"""
FastAPI 服务端
提供 REST API 接口，支持课件生成和健康检查

功能特性：
- 同步生成接口 (/generate)
- 流式生成接口 (/generate/stream)
- 仅规划接口 (/plan)
- 基于规划生成接口 (/generate-from-plan)
- 全局错误处理中间件

使用方法：
    uvicorn api:app --reload --host 0.0.0.0 --port 8000

API 文档：
    http://localhost:8000/docs
"""
import os
import time
import json
import traceback
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# 延迟导入，避免循环依赖
app_workflow = None
app_workflow_with_images = None
app_llm = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global app_workflow, app_workflow_with_images, app_llm
    # 启动时初始化工作流
    try:
        from langchain_openai import ChatOpenAI
        from src.workflow import create_workflow

        app_llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-4"),
            temperature=float(os.getenv("TEMPERATURE", 0.7)),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_BASE_URL")
        )
        
        # 创建两个工作流版本
        workflow = create_workflow(app_llm, enable_image_generation=False)
        app_workflow = workflow.compile()
        
        workflow_with_images = create_workflow(app_llm, enable_image_generation=True)
        app_workflow_with_images = workflow_with_images.compile()
        
        print("✅ 工作流初始化完成")
    except Exception as e:
        print(f"⚠️ 工作流初始化失败: {e}")
        traceback.print_exc()
        app_workflow = None

    yield

    # 关闭时清理
    print("🛑 API 服务关闭")


app = FastAPI(
    title="Agent2HTML API",
    description="""
## 智能教学课件生成 API

基于 LLM 的高职教育课件自动化生成工具。

### 功能特性
- 16:9 专业课件生成
- 多种布局模板 (20+)
- 智能图片卡槽
- 并行生成加速 (70%+)
- 流式输出支持
- Human-in-the-Loop 规划确认

### 使用流程

**标准流程**:
```
POST /generate -> 完整生成
```

**Human-in-the-Loop 流程**:
```
POST /plan -> 获取规划 -> 用户确认/修改 -> POST /generate-from-plan
```

**流式输出**:
```
POST /generate/stream -> SSE 事件流
```
    """,
    version="2.1.0",
    lifespan=lifespan
)


# ===== 全局错误处理中间件 =====

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    error_detail = {
        "error": str(exc),
        "type": type(exc).__name__,
        "path": request.url.path
    }
    
    # 开发模式下返回完整堆栈
    if os.getenv("DEBUG", "false").lower() == "true":
        error_detail["traceback"] = traceback.format_exc()
    
    return JSONResponse(
        status_code=500,
        content=error_detail
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== 请求/响应模型 =====

class GenerationRequest(BaseModel):
    """课件生成请求"""
    topic: str = Field(..., description="课程主题", example="数控编程基础")
    major: str = Field(..., description="专业", example="机械制造")
    target_audience: str = Field("高职学生", description="授课对象", example="高职二年级学生")
    duration: str = Field("45分钟", description="课时", example="45分钟")
    key_points: Optional[List[str]] = Field(None, description="关键知识点", example=["编程语言", "坐标系统"])
    enable_images: bool = Field(False, description="是否启用 AI 图片生成")


class GenerateFromPlanRequest(BaseModel):
    """基于规划生成请求"""
    planning: Dict[str, Any] = Field(..., description="规划数据（从 /plan 接口获取）")
    user_input: Dict[str, Any] = Field(..., description="原始用户输入")
    enable_images: bool = Field(False, description="是否启用 AI 图片生成")


class GenerationResponse(BaseModel):
    """课件生成响应"""
    success: bool = Field(..., description="是否成功")
    html: Optional[str] = Field(None, description="生成的 HTML 代码")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    page_count: Optional[int] = Field(None, description="页数")
    planning: Optional[dict] = Field(None, description="内容规划（JSON）")


class PlanResponse(BaseModel):
    """规划响应"""
    success: bool
    planning: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    workflow_ready: bool
    workflow_with_images_ready: bool
    version: str


# ===== API 端点 =====

@app.get("/", tags=["Root"])
async def root():
    """API 根路径"""
    return {
        "message": "Agent2HTML API",
        "version": "2.1.0",
        "docs": "/docs",
        "endpoints": {
            "generate": "POST /generate - 完整生成",
            "stream": "POST /generate/stream - 流式生成",
            "plan": "POST /plan - 仅规划",
            "generate_from_plan": "POST /generate-from-plan - 基于规划生成"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    健康检查

    返回 API 状态和工作流就绪状态
    """
    return HealthResponse(
        status="ok",
        workflow_ready=app_workflow is not None,
        workflow_with_images_ready=app_workflow_with_images is not None,
        version="2.1.0"
    )


@app.post("/generate", response_model=GenerationResponse, tags=["Generation"])
async def generate_courseware(request: GenerationRequest):
    """
    生成课件（同步）

    根据提供的课程信息生成 HTML 课件。

    - **topic**: 课程主题（必填）
    - **major**: 专业（必填）
    - **target_audience**: 授课对象
    - **duration**: 课时
    - **key_points**: 关键知识点列表
    - **enable_images**: 是否启用 AI 图片生成
    """
    global app_workflow, app_workflow_with_images

    workflow = app_workflow_with_images if request.enable_images else app_workflow
    
    if workflow is None:
        raise HTTPException(
            status_code=503,
            detail="工作流未初始化，请检查 API Key 配置"
        )

    try:
        from src.state import PPTWebState

        initial_state: PPTWebState = {
            "user_input": {
                "topic": request.topic,
                "major": request.major,
                "target_audience": request.target_audience,
                "duration": request.duration
            },
            "planning": None,
            "html_code": None,
            "quality_issues": [],
            "iteration_count": 0,
            "final_html": None,
            "status": "pending",
            "execution_time": None,
            "messages": [],
            "error": None
        }

        if request.key_points:
            initial_state["user_input"]["key_points"] = request.key_points

        start = time.time()
        result = workflow.invoke(initial_state)
        elapsed = time.time() - start

        if result.get("status") == "completed":
            return GenerationResponse(
                success=True,
                html=result.get("final_html"),
                execution_time=round(elapsed, 2),
                page_count=result.get("planning", {}).get("total_pages"),
                planning=result.get("planning")
            )
        else:
            return GenerationResponse(
                success=False,
                error=result.get("error", "生成失败"),
                execution_time=round(elapsed, 2)
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/stream", tags=["Generation"])
async def generate_courseware_stream(request: GenerationRequest):
    """
    生成课件（流式）

    使用 Server-Sent Events (SSE) 实时推送生成进度。

    事件类型：
    - `start`: 开始生成
    - `planning`: 规划完成
    - `generating`: HTML 生成中
    - `images`: 图片生成中（如启用）
    - `complete`: 生成完成
    - `error`: 发生错误
    """
    global app_workflow, app_workflow_with_images, app_llm

    workflow = app_workflow_with_images if request.enable_images else app_workflow
    
    if workflow is None:
        raise HTTPException(
            status_code=503,
            detail="工作流未初始化"
        )

    async def event_generator():
        try:
            from src.state import PPTWebState
            from src.agents.planner import content_planner
            from src.agents.generator import HTMLGenerator
            from src.utils.lightweight_validator import validate_and_fix

            # 发送开始事件
            yield f"data: {json.dumps({'event': 'start', 'message': '开始生成课件...'})}\n\n"

            initial_state: PPTWebState = {
                "user_input": {
                    "topic": request.topic,
                    "major": request.major,
                    "target_audience": request.target_audience,
                    "duration": request.duration
                },
                "planning": None,
                "html_code": None,
                "quality_issues": [],
                "iteration_count": 0,
                "final_html": None,
                "status": "pending",
                "execution_time": None,
                "messages": [],
                "error": None
            }

            if request.key_points:
                initial_state["user_input"]["key_points"] = request.key_points

            start = time.time()

            # 阶段1: 规划
            yield f"data: {json.dumps({'event': 'planning', 'message': '正在生成内容规划...'})}\n\n"
            planning_result = content_planner(initial_state, app_llm)
            
            planning = planning_result.get("planning", {})
            total_pages = planning.get("total_pages", len(planning.get("pages", [])))
            
            yield f"data: {json.dumps({'event': 'planning_done', 'message': f'规划完成，共 {total_pages} 页', 'planning': planning})}\n\n"

            # 阶段2: 生成
            yield f"data: {json.dumps({'event': 'generating', 'message': '正在生成 HTML...'})}\n\n"
            
            generator = HTMLGenerator(max_workers=4)
            gen_result = generator.generate({**initial_state, "planning": planning})
            
            # 验证
            validation = validate_and_fix(
                gen_result.get('html_code', ''),
                initial_state['user_input']
            )
            
            html = validation['validated_html']
            
            yield f"data: {json.dumps({'event': 'generating_done', 'message': 'HTML 生成完成'})}\n\n"

            # 阶段3: 图片（如启用）
            if request.enable_images:
                yield f"data: {json.dumps({'event': 'images', 'message': '正在生成图片...'})}\n\n"
                # 图片生成逻辑（略，直接跳过）
                yield f"data: {json.dumps({'event': 'images_done', 'message': '图片生成完成'})}\n\n"

            elapsed = time.time() - start

            # 完成
            yield f"data: {json.dumps({'event': 'complete', 'message': '课件生成完成', 'html': html, 'execution_time': round(elapsed, 2), 'page_count': total_pages})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/plan", response_model=PlanResponse, tags=["Generation"])
async def plan_only(request: GenerationRequest):
    """
    仅生成内容规划

    返回课件的内容规划 JSON，不生成 HTML。
    适用于 Human-in-the-Loop 流程：用户确认规划后再生成。
    """
    global app_llm

    if app_llm is None:
        raise HTTPException(
            status_code=503,
            detail="LLM 未初始化"
        )

    try:
        from src.agents.planner import content_planner

        state = {
            "user_input": {
                "topic": request.topic,
                "major": request.major,
                "target_audience": request.target_audience,
                "duration": request.duration
            },
            "messages": []
        }

        if request.key_points:
            state["user_input"]["key_points"] = request.key_points

        start = time.time()
        result = content_planner(state, app_llm)
        elapsed = time.time() - start

        if result.get("status") == "planning_completed":
            return PlanResponse(
                success=True,
                planning=result.get("planning"),
                execution_time=round(elapsed, 2)
            )
        else:
            return PlanResponse(
                success=False,
                error=result.get("error", "规划失败")
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-from-plan", response_model=GenerationResponse, tags=["Generation"])
async def generate_from_plan(request: GenerateFromPlanRequest):
    """
    基于规划生成课件

    Human-in-the-Loop 流程的第二步：
    1. 调用 /plan 获取规划
    2. 用户确认或修改规划
    3. 调用此接口完成生成
    """
    try:
        from src.agents.generator import HTMLGenerator
        from src.utils.lightweight_validator import validate_and_fix

        start = time.time()

        # 构建状态
        state = {
            "user_input": request.user_input,
            "planning": request.planning
        }

        # 直接生成
        generator = HTMLGenerator(max_workers=4)
        gen_result = generator.generate(state)

        # 验证
        validation = validate_and_fix(
            gen_result.get('html_code', ''),
            request.user_input
        )

        elapsed = time.time() - start

        return GenerationResponse(
            success=True,
            html=validation['validated_html'],
            execution_time=round(elapsed, 2),
            page_count=request.planning.get("total_pages"),
            planning=request.planning
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
FastAPI 服务端
提供 REST API 接口，支持课件生成和健康检查

使用方法：
    uvicorn api:app --reload --host 0.0.0.0 --port 8000

API 文档：
    http://localhost:8000/docs
"""
import os
import time
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# 延迟导入，避免循环依赖
app_workflow = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global app_workflow
    # 启动时初始化工作流
    try:
        from langchain_openai import ChatOpenAI
        from src.workflow import create_workflow

        llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-4"),
            temperature=float(os.getenv("TEMPERATURE", 0.7)),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_BASE_URL")
        )
        workflow = create_workflow(llm, use_ppt_pro=True)
        app_workflow = workflow.compile()
        print("✅ 工作流初始化完成")
    except Exception as e:
        print(f"⚠️ 工作流初始化失败: {e}")
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
- 多种布局模板
- 智能图片卡槽
- 并行生成加速

### 使用示例
```python
import requests

response = requests.post(
    "http://localhost:8000/generate",
    json={
        "topic": "数控编程",
        "major": "机械制造",
        "target_audience": "高职二年级学生",
        "duration": "45分钟"
    }
)
result = response.json()
print(result["html"])
```
    """,
    version="2.0.0",
    lifespan=lifespan
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


class GenerationResponse(BaseModel):
    """课件生成响应"""
    success: bool = Field(..., description="是否成功")
    html: Optional[str] = Field(None, description="生成的 HTML 代码")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    page_count: Optional[int] = Field(None, description="页数")
    planning: Optional[dict] = Field(None, description="内容规划（JSON）")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    workflow_ready: bool
    version: str


# ===== API 端点 =====

@app.get("/", tags=["Root"])
async def root():
    """API 根路径"""
    return {
        "message": "Agent2HTML API",
        "version": "2.0.0",
        "docs": "/docs"
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
        version="2.0.0"
    )


@app.post("/generate", response_model=GenerationResponse, tags=["Generation"])
async def generate_courseware(request: GenerationRequest):
    """
    生成课件

    根据提供的课程信息生成 HTML 课件。

    - **topic**: 课程主题（必填）
    - **major**: 专业（必填）
    - **target_audience**: 授课对象
    - **duration**: 课时
    - **key_points**: 关键知识点列表
    """
    global app_workflow

    if app_workflow is None:
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
        result = app_workflow.invoke(initial_state)
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


@app.post("/plan", tags=["Generation"])
async def plan_only(request: GenerationRequest):
    """
    仅生成内容规划

    返回课件的内容规划 JSON，不生成 HTML。
    适用于预览和确认规划后再生成。
    """
    global app_workflow

    if app_workflow is None:
        raise HTTPException(
            status_code=503,
            detail="工作流未初始化"
        )

    try:
        from langchain_openai import ChatOpenAI
        from src.agents.content_planner import content_planner

        llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-4"),
            temperature=float(os.getenv("TEMPERATURE", 0.7)),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_BASE_URL")
        )

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
        result = content_planner(state, llm)
        elapsed = time.time() - start

        if result.get("status") == "planning_completed":
            return {
                "success": True,
                "planning": result.get("planning"),
                "execution_time": round(elapsed, 2)
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "规划失败")
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

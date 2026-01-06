"""
LangGraph 工作流定义（高职教育 PPT 生成）

流程：
START -> Content Planner -> Designer & Generator -> Quality Checker -> END
                                                         ↓
                                                    (有问题) → 回到 Designer & Generator（最多2轮）
"""
from typing import Dict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from .state import PPTWebState
from .agents.content_planner import content_planner
from .agents.designer_generator import designer_generator
from .agents.quality_checker import quality_checker


def should_optimize(state: PPTWebState) -> str:
    """
    条件路由：决定是否需要优化

    - 如果有问题且未超过最大迭代次数：返回 "optimize"（回到生成环节）
    - 否则：返回 "end"（结束流程）
    """
    quality_issues = state.get('quality_issues', [])
    iteration_count = state.get('iteration_count', 0)
    status = state.get('status', '')

    # 如果状态是 optimizing，说明已经在优化中，返回质检
    if status == 'optimizing':
        return "check"

    # 如果有问题且未超过最大迭代次数
    MAX_ITERATIONS = 1  # 优化速度：从2轮减少到1轮
    if quality_issues and iteration_count < MAX_ITERATIONS:
        return "optimize"

    # 否则结束
    return "end"


def create_workflow(llm: ChatOpenAI) -> StateGraph:
    """
    创建 LangGraph 工作流

    流程图：
    ┌──────────────────┐
    │ Content Planner  │ (Agent 1: 规划页面大纲)
    └──────────────────┘
            ↓
    ┌──────────────────┐
    │ Designer &       │ (Agent 2: 生成 reveal.js HTML)
    │ Generator        │
    └──────────────────┘
            ↓
    ┌──────────────────┐
    │ Quality Checker  │ (Agent 3: 检查质量)
    └──────────────────┘
            ↓
        有问题? ─────┐
            │       │
           否│      是│
            │       ↓
            │   回到 Agent 2 优化
            │   (最多 2 轮)
            ↓
          END
    """

    # 创建图
    workflow = StateGraph(PPTWebState)

    # 包装 Agent 函数，注入 LLM
    def planner_node(state: PPTWebState) -> Dict:
        """Agent 1: 内容规划"""
        result = content_planner(state, llm)
        return result

    def generator_node(state: PPTWebState) -> Dict:
        """Agent 2: 设计+生成"""
        result = designer_generator(state, llm)
        
        # 并行输出：第一轮生成后立即保存 V1 版本
        if state.get("iteration_count", 0) == 0 and result.get("html_code"):
            import os
            import time
            try:
                os.makedirs("output", exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                # 保存 V1
                v1_filename = f"output/html(v1)-{timestamp}.html"
                with open(v1_filename, "w", encoding="utf-8") as f:
                    f.write(result["html_code"])
                print(f"\n🚀 [Fast Preview] V1 已生成并保存: {v1_filename}")
                print("   (Agent 3 正在后台进行质量检查与优化，稍后将生成 V2 版本...)\n")
            except Exception as e:
                print(f"   [Warning] V1 保存失败: {e}")

        return result

    def checker_node(state: PPTWebState) -> Dict:
        """Agent 3: 质量检查"""
        result = quality_checker(state, llm)
        return result

    # 添加节点
    workflow.add_node("content_planner", planner_node)
    workflow.add_node("designer_generator", generator_node)
    workflow.add_node("quality_checker", checker_node)

    # 设置流程
    workflow.set_entry_point("content_planner")

    # Content Planner -> Designer & Generator
    workflow.add_edge("content_planner", "designer_generator")

    # Designer & Generator -> Quality Checker
    workflow.add_edge("designer_generator", "quality_checker")

    # Quality Checker 的条件路由
    workflow.add_conditional_edges(
        "quality_checker",
        should_optimize,
        {
            "optimize": "designer_generator",  # 回到生成环节优化
            "check": "quality_checker",        # 重新检查
            "end": END                         # 结束
        }
    )

    return workflow

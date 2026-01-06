"""
工作流 - 智能课件生成流水线

功能特性：
1. 并行生成（提速70%）
2. 轻量级验证器（2秒完成）
3. 多模板支持（Pure CSS / PPT Pro）
4. 模块化架构
5. 统一日志系统
6. 进度追踪

支持的生成模式：
- PPT Pro: 16:9 专业模式（固定1920x1080）
- Pure CSS: 响应式纯CSS（无外部依赖）
- Traditional: 传统reveal.js模式
"""
from typing import Dict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from .state import PPTWebState
from .agents.content_planner import content_planner
from .agents.parallel_generator import parallel_designer_generator
from .agents.pure_css_generator import PureCSSGenerator
from .agents.ppt_pro_generator import PPTProGenerator
from .utils.lightweight_validator import validate_and_fix
from .utils.logger import logger, LogContext


def create_workflow(
    llm: ChatOpenAI,
    use_parallel: bool = True,
    use_pure_css: bool = True,
    use_ppt_pro: bool = False
) -> StateGraph:
    """
    创建工作流

    Args:
        llm: LLM实例
        use_parallel: 是否使用并行生成（默认True）
        use_pure_css: 是否使用纯CSS生成器（默认True，不依赖reveal.js）
        use_ppt_pro: 是否使用PPT Pro生成器（16:9专业模式，默认False）

    Returns:
        StateGraph
    """

    pure_css_gen = PureCSSGenerator(llm) if use_pure_css else None
    ppt_pro_gen = PPTProGenerator(llm) if use_ppt_pro else None

    # 创建图
    workflow = StateGraph(PPTWebState)

    def planner_node(state: PPTWebState) -> Dict:
        """
        Agent 1: 内容规划
        """
        logger.info("📋 Agent 1: Content Planner 开始...")
        return content_planner(state, llm)

    def generator_node(state: PPTWebState) -> Dict:
        """
        Agent 2: 设计+生成 + 轻量级验证
        """
        logger.info("🎨 Agent 2: Designer & Generator 开始...")

        # 生成HTML
        with LogContext("HTML 生成"):
            if use_ppt_pro and ppt_pro_gen:
                logger.info("   🎯 使用PPT Pro生成器（16:9专业模式）...")
                result = ppt_pro_gen.generate(state)
            elif use_pure_css and pure_css_gen:
                logger.info("   🎨 使用纯CSS生成器（无外部依赖）...")
                result = pure_css_gen.generate(state)
            elif use_parallel:
                logger.info("   🚀 使用并行生成策略...")
                result = parallel_designer_generator(state, llm)
            else:
                from .agents.designer_generator import designer_generator
                logger.warning("   ⚠️  使用串行生成策略...")
                result = designer_generator(state, llm)

        # 轻量级验证（替代 Agent 3）
        with LogContext("轻量级验证"):
            validation_result = validate_and_fix(
                result.get('html_code', ''),
                state['user_input']
            )

            # 显示验证结果
            if validation_result['issues_found'] > 0:
                logger.warning(f"发现 {validation_result['issues_found']} 个问题")
                for issue in validation_result['issues']:
                    logger.warning(f"   - {issue}")
                logger.info(f"应用 {len(validation_result['fixes_applied'])} 个修复")
                for fix in validation_result['fixes_applied']:
                    logger.info(f"   ✅ {fix}")
            else:
                logger.info("   ✅ 所有检查通过")

        # 使用验证后的HTML
        validated_html = validation_result['validated_html']

        return {
            **state,
            "html_code": validated_html,
            "final_html": validated_html,
            "status": "completed",
            "quality_issues": [],
            "validation_result": validation_result
        }

    # 添加节点（只保留 Agent 1 和 Agent 2）
    workflow.add_node("content_planner", planner_node)
    workflow.add_node("designer_generator", generator_node)

    # 设置流程（简化：规划 → 生成+验证 → 结束）
    workflow.set_entry_point("content_planner")
    workflow.add_edge("content_planner", "designer_generator")
    workflow.add_edge("designer_generator", END)

    return workflow

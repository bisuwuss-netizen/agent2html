"""
工作流 - 课件生成流水线

简化版：
- 无功能开关
- 直接使用最高级生成器
- 两步流程：规划 → 生成
"""
from typing import Dict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from .state import PPTWebState
from .agents.planner import content_planner
from .agents.generator import HTMLGenerator
from .utils.lightweight_validator import validate_and_fix
from .utils.logger import logger, LogContext


def create_workflow(llm: ChatOpenAI) -> StateGraph:
    """
    创建工作流
    
    Args:
        llm: LLM实例
    
    Returns:
        StateGraph
    """
    
    # 初始化生成器
    generator = HTMLGenerator(max_workers=4)
    
    # 创建图
    workflow = StateGraph(PPTWebState)
    
    def planner_node(state: PPTWebState) -> Dict:
        """Agent 1: 内容规划"""
        logger.info("📋 Agent 1: 内容规划...")
        return content_planner(state, llm)
    
    def generator_node(state: PPTWebState) -> Dict:
        """Agent 2: HTML生成 + 验证"""
        logger.info("🎨 Agent 2: HTML生成...")
        
        # 生成HTML
        with LogContext("HTML生成"):
            result = generator.generate(state)
        
        # 轻量级验证
        with LogContext("验证修复"):
            validation = validate_and_fix(
                result.get('html_code', ''),
                state['user_input']
            )
            
            if validation['issues_found'] > 0:
                logger.warning(f"发现 {validation['issues_found']} 个问题")
                for fix in validation['fixes_applied']:
                    logger.info(f"   ✅ {fix}")
            else:
                logger.info("   ✅ 验证通过")
        
        return {
            **state,
            "html_code": validation['validated_html'],
            "final_html": validation['validated_html'],
            "status": "completed",
            "quality_issues": [],
            "validation_result": validation
        }
    
    # 添加节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("generator", generator_node)
    
    # 设置流程
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "generator")
    workflow.add_edge("generator", END)
    
    return workflow

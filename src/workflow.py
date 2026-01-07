"""
工作流 - 课件生成流水线

三阶段流程：
1. 规划阶段 (Planner): 生成内容大纲
2. 生成阶段 (Generator): 生成 HTML
3. 图片阶段 (Image): 可选的图片生成/填充
"""
from typing import Dict, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from .state import PPTWebState
from .agents.planner import content_planner
from .agents.generator import HTMLGenerator
from .agents.image_generator import generate_images_agent
from .utils.lightweight_validator import validate_and_fix
from .utils.logger import logger, LogContext
from .config import config


def create_workflow(
    llm: ChatOpenAI,
    enable_image_generation: bool = False
) -> StateGraph:
    """
    创建工作流
    
    Args:
        llm: LLM实例
        enable_image_generation: 是否启用图片生成（默认关闭）
    
    Returns:
        StateGraph
    """
    
    # 初始化生成器
    generator = HTMLGenerator(max_workers=config.generation.max_workers)
    
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
            "status": "html_generated",
            "quality_issues": [],
            "validation_result": validation
        }
    
    def image_node(state: PPTWebState) -> Dict:
        """Agent 3: 图片生成（可选）"""
        logger.info("🖼️ Agent 3: 图片生成...")
        
        try:
            result = generate_images_agent(state)
            
            # 如果生成了图片，需要将图片填充到 HTML 中
            generated_images = result.get('generated_images', {})
            if generated_images:
                html = state.get('final_html', '')
                # 替换占位符为实际图片
                for page_num, image_url in generated_images.items():
                    placeholder = f'data-slot="page-{page_num}"'
                    if placeholder in html:
                        html = html.replace(
                            f'{placeholder}>',
                            f'{placeholder} style="background-image: url({image_url}); background-size: cover;">'
                        )
                
                return {
                    **state,
                    "final_html": html,
                    "generated_images": generated_images,
                    "status": "completed"
                }
            else:
                return {
                    **state,
                    "status": "completed"
                }
        except Exception as e:
            logger.error(f"图片生成失败: {e}")
            return {
                **state,
                "status": "completed",
                "error": f"图片生成失败(非致命): {str(e)}"
            }
    
    def skip_images_node(state: PPTWebState) -> Dict:
        """跳过图片生成"""
        logger.info("⏭️ 跳过图片生成")
        return {
            **state,
            "status": "completed"
        }
    
    # 添加节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("generator", generator_node)
    
    # 设置流程
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "generator")
    
    # 根据配置决定是否启用图片生成
    if enable_image_generation:
        workflow.add_node("image_generator", image_node)
        workflow.add_edge("generator", "image_generator")
        workflow.add_edge("image_generator", END)
    else:
        workflow.add_node("skip_images", skip_images_node)
        workflow.add_edge("generator", "skip_images")
        workflow.add_edge("skip_images", END)
    
    return workflow

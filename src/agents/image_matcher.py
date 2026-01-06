"""
Agent 4: Image Matcher (图片匹配 Agent)
负责：从素材库匹配图片或调用AI生成图片
"""
import os
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# 导入工具类
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.material_library import MaterialLibrary
from utils.image_generator import ImageGenerator


def image_matcher(state: Dict, llm: ChatOpenAI) -> Dict:
    """
    图片匹配 Agent

    输入: state['planning'] (包含每页的 image_description)
    输出: state['matched_images'] = {
        "page_1": {"method": "library", "path": "/path/to/image.png"},
        "page_2": {"method": "generated", "url": "https://..."}
    }
    """

    print("🖼️  Agent 4: Image Matcher - 开始匹配图片...")

    if not state.get('planning'):
        return {
            **state,
            "error": "缺少 planning 数据，无法匹配图片",
            "status": "failed"
        }

    planning = state['planning']
    user_input = state['user_input']
    major = user_input.get('major', '通用')

    # 初始化工具
    library = MaterialLibrary()
    generator = ImageGenerator(provider="dall-e")  # 可配置为 "placeholder"

    matched_images = {}
    match_summary = {
        "from_library": 0,
        "generated": 0,
        "placeholder": 0
    }

    # 遍历每一页，匹配图片
    for page in planning['pages']:
        page_num = page.get('page_num')
        image_desc = page.get('image_description', '')

        if not image_desc or image_desc == "无":
            continue  # 跳过不需要图片的页面

        print(f"\n📄 第 {page_num} 页: {image_desc}")

        # 策略1: 先从素材库搜索
        library_results = library.search_materials(
            query=image_desc,
            n_results=3,
            tags_filter=[major] if major != '通用' else None
        )

        if library_results and library_results[0]['score'] > 0.7:
            # 找到匹配度较高的素材
            best_match = library_results[0]
            matched_images[f"page_{page_num}"] = {
                "method": "library",
                "path": best_match['file_path'],
                "description": best_match['description'],
                "score": best_match['score']
            }
            match_summary["from_library"] += 1
            print(f"   ✅ 从素材库匹配: {best_match['description']} (评分: {best_match['score']:.2f})")

        else:
            # 策略2: 调用 AI 生成图片
            if os.getenv("ENABLE_IMAGE_GENERATION") == "true":
                generated = generator.generate_image(
                    prompt=f"{major}专业教学用，{image_desc}",
                    size="1024x1024",
                    quality="standard"
                )

                if generated and generated.get("url"):
                    matched_images[f"page_{page_num}"] = {
                        "method": "generated",
                        "url": generated['url'],
                        "revised_prompt": generated.get('revised_prompt'),
                        "provider": generated.get('provider')
                    }
                    match_summary["generated"] += 1
                    print(f"   🎨 AI生成图片: {generated['url'][:50]}...")

                else:
                    # 生成失败，使用占位符
                    matched_images[f"page_{page_num}"] = {
                        "method": "placeholder",
                        "description": image_desc
                    }
                    match_summary["placeholder"] += 1
                    print(f"   📦 使用占位符")

            else:
                # 策略3: 使用占位符
                matched_images[f"page_{page_num}"] = {
                    "method": "placeholder",
                    "description": image_desc
                }
                match_summary["placeholder"] += 1
                print(f"   📦 使用占位符（AI生成未启用）")

    # 打印匹配总结
    print(f"\n✅ 图片匹配完成:")
    print(f"   📚 素材库: {match_summary['from_library']} 张")
    print(f"   🎨 AI生成: {match_summary['generated']} 张")
    print(f"   📦 占位符: {match_summary['placeholder']} 张")

    return {
        **state,
        "matched_images": matched_images,
        "match_summary": match_summary,
        "status": "image_matching_completed"
    }


def enhance_image_descriptions(state: Dict, llm: ChatOpenAI) -> Dict:
    """
    增强图片描述（可选功能）

    使用 LLM 优化图片描述，使其更适合 AI 生成
    """

    if not state.get('planning'):
        return state

    planning = state['planning']

    system_prompt = """你是一位专业的 AI 绘图提示词专家。

你的任务是：将简单的图片描述优化成详细的 DALL-E 提示词。

输出要求：
1. 保留原始内容意图
2. 添加视觉细节（颜色、风格、构图）
3. 适合教学演示（清晰、专业）
4. 每个描述控制在50字以内"""

    enhanced_pages = []

    for page in planning['pages']:
        original_desc = page.get('image_description', '')

        if not original_desc or original_desc == "无":
            enhanced_pages.append(page)
            continue

        # 调用 LLM 优化描述
        user_prompt = f"""原始描述: {original_desc}

请优化成适合 AI 生成的提示词（英文或中文均可）。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        enhanced_desc = response.content.strip()

        # 更新描述
        page['image_description_enhanced'] = enhanced_desc
        enhanced_pages.append(page)

        print(f"📝 优化描述: {original_desc} → {enhanced_desc}")

    planning['pages'] = enhanced_pages

    return {
        **state,
        "planning": planning
    }


# 示例用法
if __name__ == "__main__":
    from langchain_openai import ChatOpenAI
    from dotenv import load_dotenv

    load_dotenv()

    llm = ChatOpenAI(model="deepseek-chat")

    # 模拟状态
    test_state = {
        "user_input": {
            "topic": "车床操作",
            "major": "机械制造"
        },
        "planning": {
            "course_title": "车床操作基础",
            "total_pages": 3,
            "pages": [
                {
                    "page_num": 1,
                    "type": "title",
                    "title": "车床操作基础",
                    "image_description": "无"
                },
                {
                    "page_num": 2,
                    "type": "image_text",
                    "title": "车床结构",
                    "image_description": "车床主轴结构示意图"
                },
                {
                    "page_num": 3,
                    "type": "steps",
                    "title": "操作步骤",
                    "image_description": "车床操作流程图"
                }
            ]
        }
    }

    # 执行匹配
    result = image_matcher(test_state, llm)

    print("\n匹配结果:")
    print(result.get('matched_images'))

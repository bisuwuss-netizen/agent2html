"""
Agent 1: Content Planner (内容规划 Agent)
负责：将用户需求转换成 PPT 式网页的分页大纲

增强版输出格式：
- 支持详细的 slide JSON 格式
- 支持 style JSON 配置
- 支持 assets 资源定义
"""
import json
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import config, get_style_json
from ..utils.logger import logger, LogContext
from ..utils.retry_utils import retry_with_backoff


# 幻灯片类型定义
SLIDE_TYPES = {
    'cover': '封面页',
    'objectives': '教学目标页',
    'intro': '导入页',
    'concept': '核心概念页',
    'keypoints': '要点解析页',
    'structure': '结构/组成页',
    'principle': '原理讲解页',
    'steps': '步骤说明页',
    'comparison': '对比分析页',
    'warning': '安全警告页',
    'practice': '实践练习页',
    'summary': '总结回顾页'
}

# 教学场景类型
TEACHING_SCENES = {
    'theory': '理论教学',
    'practice': '实践操作',
    'safety': '安全规范',
    'assessment': '考核评估'
}


from langchain_core.callbacks import StreamingStdOutCallbackHandler

@retry_with_backoff(max_retries=3, base_delay=2.0)
def _invoke_llm(llm: ChatOpenAI, messages: List) -> str:
    """带重试的 LLM 调用"""
    print("   Thinking...", end=" ", flush=True) # 提示用户正在生成
    response = llm.invoke(messages)
    print() # 换行
    return response.content.strip()


def content_planner(state: Dict, llm: ChatOpenAI) -> Dict:
    """
    内容规划 Agent（增强版）

    输入: state['user_input'] = {
        "topic": "机械加工-车床操作",
        "major": "机械制造",
        "target_audience": "高职二年级学生",
        "duration": "45分钟",
        "key_points": ["车床结构", "操作步骤"]  # 可选
    }

    输出: state['planning'] = {
        "deck_title": "课程标题",
        "subject": "主题",
        "knowledge_points": [...],
        "teaching_scene": "theory",
        "style": {...},
        "slides": [...]
    }
    """

    with LogContext("内容规划 Agent"):
        user_input = state['user_input']
        major = user_input.get('major', '机械制造')
        topic = user_input.get('topic', '课程主题')

        # 生成风格配置
        style_config = get_style_json(major, 'theory')

        # 智能检测：如果输入内容过长（>200字符），启用"解析模式"
        is_parser_mode = len(topic) > 200
        
        if is_parser_mode:
            logger.info("   🔄 检测到外部大纲，启用解析模式 (Parser Mode)...")
            system_prompt = _build_parser_system_prompt()
            user_prompt = _build_parser_user_prompt(topic, user_input) # topic 包含整个大纲内容
        else:
            # 正常生成模式
            system_prompt = _build_system_prompt()
            user_prompt = _build_user_prompt(user_input)

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response_text = _invoke_llm(llm, messages)
            planning = _parse_response(response_text)

            # 添加风格配置
            planning['style'] = style_config

            # 验证并补充缺失字段
            planning = _validate_and_enhance(planning, user_input)

            logger.info(f"规划完成: {planning['deck_title']}, 共 {len(planning['slides'])} 页")

            return {
                **state,
                "planning": planning,
                "status": "planning_completed",
                "messages": state.get("messages", []) + messages
            }

        except json.JSONDecodeError as e:
            error_msg = f"JSON 解析失败: {e}"
            logger.error(error_msg)
            return {
                **state,
                "error": error_msg,
                "status": "failed"
            }

        except Exception as e:
            error_msg = f"内容规划失败: {str(e)}"
            logger.error(error_msg)
            return {
                **state,
                "error": error_msg,
                "status": "failed"
            }


def _build_system_prompt() -> str:
    """构建系统 Prompt"""
    return """你是一位资深的高职教育课件设计专家。

【任务】
根据用户提供的课程信息，输出符合规范的 JSON 格式课件规划。

【输出格式要求 - 严格遵守】
输出必须是纯 JSON，不要有任何解释文字。

{
  "deck_title": "完整课程标题",
  "subject": "主题（简短）",
  "knowledge_points": ["知识点1", "知识点2", ...],
  "teaching_scene": "theory|practice|safety",
  "slides": [
    {
      "index": 1,
      "slide_type": "cover|objectives|intro|concept|keypoints|structure|principle|steps|warning|summary",
      "title": "页面标题",
      "bullets": ["要点1", "要点2", ...],
      "notes": "教师备注（可为null）",
      "interactions": [],
      "assets": [
        {
          "type": "image|diagram|chart|icon",
          "theme": "描述性主题（如：car_engine_structure）",
          "size": "16:9|4:3|1:1"
        }
      ]
    }
  ]
}

【slide_type 说明】
- cover: 封面页（课程名+授课信息）
- objectives: 教学目标页（知识/能力/素养三维目标）
- intro: 导入页（案例引入+学习目标）
- concept: 核心概念页（定义+组成+特征）
- keypoints: 要点解析页（重点+难点+总结）
- structure: 结构/组成页（部件+功能说明）
- principle: 原理讲解页（工作机制+原理图）
- steps: 步骤说明页（操作流程+注意事项）
- warning: 安全警告页（安全提示）
- summary: 总结页（知识回顾+思考题）

【assets 规范】
- 40-50% 的页面需要 assets（图片/图表）
- cover 页面：可选背景图
- intro 页面：推荐场景图（type: image, size: 16:9）
- concept/structure 页面：推荐示意图（type: diagram, size: 4:3）
- steps 页面：不需要 assets（纯文字步骤）
- warning 页面：不需要 assets（纯文字警告）
- summary 页面：不需要 assets（纯文字总结）

【bullets 规范】
- 每页 3-6 个要点
- 每个要点不超过 30 字
- 标题页可以有 3-4 个教学目标

【课程结构模板（8-12页）】
1. cover - 封面
2. objectives - 教学目标
3. intro - 导入（配图）
4. concept - 核心概念（配图）
5. keypoints - 要点解析
6. structure/principle - 结构或原理（配图）
7. steps - 操作步骤
8. warning - 安全提示（如适用）
9. summary - 总结"""


def _build_user_prompt(user_input: Dict) -> str:
    """构建用户 Prompt"""
    topic = user_input.get('topic', '课程主题')
    major = user_input.get('major', '专业')
    target_audience = user_input.get('target_audience', '高职学生')
    duration = user_input.get('duration', '45分钟')
    key_points = user_input.get('key_points', [])

    prompt = f"""请为以下课程生成 JSON 格式的课件规划：

**课程信息：**
- 主题：{topic}
- 专业：{major}
- 授课对象：{target_audience}
- 时长：{duration}
"""

    if key_points:
        prompt += f"- 必须包含的知识点：{', '.join(key_points)}\n"

    prompt += """
**要求：**
1. 按照系统 prompt 的 JSON 格式输出
2. 页数控制在 8-12 页（45分钟课程）
3. 确保课程结构完整（封面→目标→导入→正文→总结）
4. assets 只在需要图片的页面添加
5. slides 数组中每个对象必须有 index, slide_type, title, bullets 字段

请直接输出 JSON，不要有任何解释。
"""

    return prompt


def _parse_response(response_text: str) -> Dict:
    """解析 LLM 响应"""
    # 去除可能的 markdown 代码块标记
    if response_text.startswith("```json"):
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif response_text.startswith("```"):
        response_text = response_text.split("```")[1].split("```")[0].strip()

    return json.loads(response_text)


def _validate_and_enhance(planning: Dict, user_input: Dict) -> Dict:
    """验证并增强规划数据"""

    # 确保必需字段存在
    if 'deck_title' not in planning:
        planning['deck_title'] = user_input.get('topic', '课程')

    if 'subject' not in planning:
        planning['subject'] = user_input.get('topic', '课程')

    if 'knowledge_points' not in planning:
        planning['knowledge_points'] = user_input.get('key_points', [])

    if 'teaching_scene' not in planning:
        planning['teaching_scene'] = 'theory'

    if 'slides' not in planning:
        planning['slides'] = []

    # 验证每个 slide
    for i, slide in enumerate(planning['slides']):
        # 确保基本字段
        slide.setdefault('index', i + 1)
        slide.setdefault('slide_type', 'concept')
        slide.setdefault('title', f'页面 {i + 1}')
        slide.setdefault('bullets', [])
        slide.setdefault('notes', None)
        slide.setdefault('interactions', [])
        slide.setdefault('assets', [])

    # 为了兼容旧版生成器，添加 total_pages 和 pages 字段
    planning['total_pages'] = len(planning['slides'])
    planning['course_title'] = planning['deck_title']

    # 转换 slides 为旧版 pages 格式（兼容性）
    planning['pages'] = _convert_slides_to_pages(planning['slides'])

    return planning


def _convert_slides_to_pages(slides: List[Dict]) -> List[Dict]:
    """将新版 slides 格式转换为旧版 pages 格式（兼容性）"""
    pages = []

    # slide_type 到 page type 的映射
    type_mapping = {
        'cover': 'title',
        'objectives': 'intro',
        'intro': 'intro',
        'concept': 'concept',
        'keypoints': 'concept',
        'structure': 'structure',
        'principle': 'principle',
        'steps': 'steps',
        'warning': 'warning',
        'practice': 'steps',
        'summary': 'summary',
        'comparison': 'comparison',
        'gallery': 'gallery'
    }

    # slide_type 到 layout 的映射
    layout_mapping = {
        'cover': 'center',
        'objectives': 'text_with_bullets',
        'intro': 'top_image_center',
        'concept': 'left_text_right_image',
        'keypoints': 'text_with_bullets',
        'structure': 'left_text_right_image',
        'principle': 'full_text_center',
        'steps': 'numbered_steps',
        'warning': 'warning_grid',
        'practice': 'numbered_steps',
        'summary': 'summary_boxes',
        'comparison': 'comparison',
        'gallery': 'gallery_grid'
    }

    for slide in slides:
        slide_type = slide.get('slide_type', 'concept')
        assets = slide.get('assets', [])

        # 判断是否有图片
        has_image = len(assets) > 0

        page = {
            'page_num': slide.get('index', 1),
            'type': type_mapping.get(slide_type, 'concept'),
            'title': slide.get('title', ''),
            'content': slide.get('bullets', []),
            'layout': layout_mapping.get(slide_type, 'text_with_bullets'),
            'visual_emphasis': '',
            'key_points': slide.get('bullets', [])
        }

        # 添加图片描述
        if has_image:
            first_asset = assets[0]
            page['image_description'] = first_asset.get('theme', '示意图')
            page['image_size'] = 'side' if first_asset.get('size') == '4:3' else 'top'

        pages.append(page)

    return pages


def get_slide_template(slide_type: str) -> Dict:
    """
    获取幻灯片模板

    Args:
        slide_type: 幻灯片类型

    Returns:
        模板字典
    """
    templates = {
        'cover': {
            'slide_type': 'cover',
            'title': '课程标题',
            'bullets': ['授课教师：_____', '课程时间：_____', '教学场景：_____'],
            'notes': '封面信息可在前端编辑区直接改。',
            'interactions': [],
            'assets': []
        },
        'objectives': {
            'slide_type': 'objectives',
            'title': '教学目标',
            'bullets': [
                '知识目标：掌握...',
                '能力目标：能识别...',
                '素养目标：培养...'
            ],
            'notes': '可根据班级学情进一步细化。',
            'interactions': [],
            'assets': []
        },
        'intro': {
            'slide_type': 'intro',
            'title': '导入',
            'bullets': ['案例引入', '学习目标', '课程衔接'],
            'notes': None,
            'interactions': [],
            'assets': [{'type': 'image', 'theme': 'scene_intro', 'size': '16:9'}]
        },
        'concept': {
            'slide_type': 'concept',
            'title': '核心概念',
            'bullets': ['定义：...', '组成：...', '功能：...'],
            'notes': None,
            'interactions': [],
            'assets': [{'type': 'diagram', 'theme': 'concept_diagram', 'size': '4:3'}]
        },
        'summary': {
            'slide_type': 'summary',
            'title': '课程总结',
            'bullets': ['知识回顾', '重点难点', '课后思考'],
            'notes': None,
            'interactions': [],
            'assets': []
        }
    }

    return templates.get(slide_type, templates['concept'])


def _build_parser_system_prompt() -> str:
    """构建解析模式 System Prompt"""
    return """你是一个严格的课程大纲解析器和格式转换器。

【任务】
将用户提供的非结构化课程大纲文本，**严格保留原意**地转换为符合系统规范的 JSON 格式。
不要对内容进行摘要、删减或"润色"，必须忠实还原用户的教学设计。

【输出格式要求】
输出必须是纯 JSON，不要有任何解释文字。

{
  "deck_title": "解析出的课程标题",
  "subject": "主题",
  "knowledge_points": ["提取的知识点1", ...],
  "teaching_scene": "theory",
  "slides": [
    {
      "index": 1,
      "slide_type": "cover|intro|concept|structure|steps|comparison|gallery|summary",
      "title": "原大纲页面标题",
      "bullets": ["原大纲关键内容1", "原大纲关键内容2"...],
      "notes": "原大纲中的备注或视觉要求描述",
      "assets": [
        {
          "type": "image",
          "theme": "根据视觉描述提取的关键词（如：lime_kiln_fire）",
          "size": "16:9|4:3"
        }
      ]
    }
  ]
}

【slide_type 映射规则】
请根据页面内容和布局描述智能映射：
- 封面/标题页 -> cover
- 目录/导航/图片墙 -> gallery
- 对比/表格/区别 -> comparison
- 步骤/流程/三联图 -> steps
- 核心概念/左右分栏 -> concept (或 structure)
- 总结/思维导图 -> summary
- 警告/安全/挑战 -> warning
- 导入/案例 -> intro

【关键要求】
1. **Visual-First**: 如果原文描述了"视觉"、"配图"、"左图右字"，必须在 `assets` 中生成对应的图片配置。
2. **Layout Mapping**: 注意原文的布局描述（如"拼图式"->"gallery", "表格"->"comparison"）。
3. **Content Fidelity**: `bullets` 中的文字应直接提取自原文的"内容"部分，保持精炼但不要丢失核心词。
"""


def _build_parser_user_prompt(raw_text: str, user_input: Dict) -> str:
    """构建解析模式 User Prompt"""
    return f"""请解析以下课程大纲，将其转换为 JSON 格式：

【用户提供的原大纲】
{raw_text}

【补充信息】
- 专业：{user_input.get('major', '通用')}
- 对象：{user_input.get('target_audience', '学生')}

【解析要求】
1. 提取所有页面，保持及顺序一致。
2. 将"视觉"或"配图"部分的描述，提取为 `assets` 中的 `theme` 关键词（英文）和 `notes` 字段。
3. 特别注意识别表格内容，映射为 `comparison` 类型。
4. 特别注意识别图片墙或拼图，映射为 `gallery` 类型。
5. 针对'gallery'类型 slides，bullets 应包含每个图片的标题或描述。
6. 直接输出 JSON。
"""

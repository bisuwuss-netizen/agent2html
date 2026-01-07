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


def _try_parse_json_input(topic: str) -> Optional[Dict]:
    """
    尝试将输入解析为 JSON 规划数据
    
    如果输入是有效的 JSON 且包含 slides 或 pages 字段，直接返回解析后的字典。
    否则返回 None，继续正常流程。
    
    支持的 JSON 格式：
    1. 完整规划格式（包含 slides）
    2. 简化格式（包含 pages）
    """
    # 快速检查：必须以 { 开头
    topic_stripped = topic.strip()
    if not topic_stripped.startswith('{'):
        return None
    
    try:
        data = json.loads(topic_stripped)
        
        # 验证是否是规划数据（必须包含 slides 或 pages）
        if isinstance(data, dict) and ('slides' in data or 'pages' in data):
            logger.info(f"   ✅ 检测到有效 JSON 规划数据")
            return data
        
        return None
        
    except json.JSONDecodeError:
        # 不是有效 JSON，继续正常流程
        return None


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

    支持三种输入模式：
    1. 简短主题 → 正常生成模式（LLM 生成完整规划）
    2. 长文本大纲（>200字符）→ 解析模式（LLM 解析为 JSON）
    3. JSON 格式 → 直接使用模式（跳过 LLM，直接处理）

    输入: state['user_input'] = {
        "topic": "机械加工-车床操作" 或 长文本大纲 或 JSON 字符串,
        "major": "机械制造",
        "target_audience": "高职二年级学生",
        "duration": "45分钟",
        "key_points": ["车床结构", "操作步骤"]  # 可选
    }

    输出: state['planning'] = {...}
    """

    with LogContext("内容规划 Agent"):
        user_input = state['user_input']
        major = user_input.get('major', '机械制造')
        topic = user_input.get('topic', '课程主题')

        # 生成风格配置
        style_config = get_style_json(major, 'theory')

        # ========== 模式检测 ==========
        
        # 模式1: JSON 直接输入检测
        json_input = _try_parse_json_input(topic)
        if json_input:
            logger.info("   📋 检测到 JSON 输入，直接使用模式 (Direct Mode)...")
            planning = json_input
            planning['style'] = style_config
            planning = _validate_and_enhance(planning, user_input)
            
            logger.info(f"规划完成: {planning['deck_title']}, 共 {len(planning['slides'])} 页")
            
            return {
                **state,
                "planning": planning,
                "status": "planning_completed",
                "messages": []
            }
        
        # 模式2: 长文本解析模式（>200字符）
        is_parser_mode = len(topic) > 200
        
        if is_parser_mode:
            logger.info("   🔄 检测到外部大纲，启用解析模式 (Parser Mode)...")
            system_prompt = _build_parser_system_prompt()
            user_prompt = _build_parser_user_prompt(topic, user_input)
        else:
            # 模式3: 正常生成模式
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

            # 验证并补充缺失字段 (会自动移除LLM可能生成的color字段)
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
根据用户提供的课程信息，输出符合规范的**全流程 JSON 格式**课件规划。

【输出格式要求 - 严格遵守】
输出必须是纯 JSON，包含 4 个核心根与字段：

{
  "teaching_request": {
    "subject": "课程主题",
    "teaching_scene": "theory|practice|safety",
    "slide_count": 8,
    "include_cases": true,
    "teaching_goals": {
      "knowledge": "知识目标...",
      "ability": "能力目标...",
      "literacy": "素养目标..."
    }
  },
  "style_config": {
    "style_name": "theory_clean|practice_industrial|safety_warning",
    "font": {
      "title_family": "Microsoft YaHei",
      "body_family": "Microsoft YaHei"
    },
    "layout": {
      "notes_area": true
    }
  },
  "outline": {
    "deck_title": "完整课程标题",
    "subject": "主题",
    "slides": [
      {
        "index": 1,
        "slide_type": "cover|objectives|intro|concept|keypoints|structure|principle|steps|warning|summary",
        "title": "页面标题",
        "bullets": ["要点1", "要点2"],
        "notes": "教师备注",
        "assets": [
          {
            "type": "image|diagram|chart|icon",
            "theme": "英文关键词",
            "size": "16:9|4:3"
          }
        ]
      }
    ]
  },
  "deck_content": {
    "deck_title": "完整课程标题",
    "pages": [
      {
        "index": 1,
        "slide_type": "cover",
        "title": "页面标题",
        "layout": { "template": "cover" },
        "elements": [
          { "type": "text", "content": { "text": "标题", "role": "title" } },
          { "type": "text", "content": { "text": "副标题", "role": "subtitle" } }
        ],
        "speaker_notes": "备注"
      },
      {
        "index": 2,
        "slide_type": "objectives",
        "layout": { "template": "cards_3col" },
        "elements": [
          { "type": "text", "content": { "text": "教学目标", "role": "title" } },
          { "type": "bullets", "content": { "items": ["知识...", "能力...", "素养..."], "role": "body" } }
        ]
      },
      {
        "index": 3,
        "slide_type": "concept",
        "layout": { "template": "split" },
        "elements": [
          { "type": "text", "content": { "text": "标题", "role": "title" } },
          { "type": "bullets", "content": { "items": ["内容..."], "role": "body" } },
          { "type": "image", "content": { "placeholder": true, "theme": "key", "prompt": "描述" }, "style": { "role": "visual" } }
        ]
      }
    ]
  }
}

【style_config 说明】
只需要选择 style_name，不要生成 color 字段！
- theory_clean: 专业理论课(系统将根据专业自动匹配配色)
- practice_industrial: 实训操作课(强调操作和安全)
- safety_warning: 安全规范课(使用警示配色)

注意: 配色(color)由系统根据用户的"专业"字段自动匹配，不需要在 JSON 中生成！

【slide_type 与 template 映射】
- cover -> template: "cover"
- objectives -> template: "cards_3col" (三维目标)
- intro -> template: "top_image" (场景导入)
- concept -> template: "split" (左文右图)
- structure -> template: "split" (结构拆解)
- steps -> template: "timeline" (步骤)
- warning -> template: "warning" (警告)
- summary -> template: "summary" (总结)

【deck_content 生成规则】
必须为每一页生成详细的 `elements` 列表：
1. `role="title"`: 页面标题
2. `role="body"`: 核心内容 (bullets)
3. `role="visual"`: 图片/图表 (对应 outline 中的 assets)，type 设为 image/diagram
"""


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
    """验证并增强规划数据（支持 v2 全流程结构）"""

    # 1. 结构标准化 (V2 format check)
    if 'outline' in planning and 'slides' in planning['outline']:
        # V2: 将 outline.slides 映射到根目录以兼容旧代码
        planning['slides'] = planning['outline']['slides']
    elif 'slides' in planning:
        # V1: 构造 outline 包装旧版 slides
        planning['outline'] = {
            'deck_title': planning.get('deck_title', '课程'),
            'subject': planning.get('subject', '主题'),
            'slides': planning['slides']
        }

    # 2. 确保核心根节点存在
    if 'teaching_request' not in planning:
        planning['teaching_request'] = {
            'subject': user_input.get('topic', '课程主题'),
            'teaching_scene': planning.get('teaching_scene', 'theory'),
            'raw_user_input': str(user_input)
        }
    
    if 'style_config' not in planning:
        # 如果没有 style_config，使用默认
        planning['style_config'] = {
            'style_name': 'theory_clean',
            'layout': {'notes_area': True}
        }

    # 强制移除 style_config 中的 color 字段(如果存在)
    # 颜色由系统根据专业自动匹配,不应该由LLM生成
    if 'style_config' in planning and isinstance(planning['style_config'], dict):
        planning['style_config'].pop('color', None)
    
    if 'deck_content' not in planning:
        planning['deck_content'] = {'pages': []}

    # 3. 基础字段验证
    if 'slides' not in planning:
        planning['slides'] = []
        
    if 'deck_title' not in planning:
        planning['deck_title'] = user_input.get('topic', '课程')

    # 4. 验证每个 slide (Outline Level)
    for i, slide in enumerate(planning['slides']):
        # 确保基本字段
        slide.setdefault('index', i + 1)
        slide.setdefault('slide_type', 'concept')
        slide.setdefault('title', f'页面 {i + 1}')
        slide.setdefault('bullets', [])
        slide.setdefault('notes', None)
        slide.setdefault('interactions', [])
        slide.setdefault('assets', [])

    # 5. 为了兼容旧版生成器，添加 total_pages 和 pages 字段
    planning['total_pages'] = len(planning['slides'])
    planning['course_title'] = planning.get('deck_title', '课程')

    # 转换 slides 为旧版 pages 格式（兼容性）
    planning['pages'] = _convert_slides_to_pages(planning['slides'])

    # 【关键修复】同样转换 deck_content.pages 为兼容格式
    # LLM可能生成新格式(elements数组)，需要转换成旧格式(title+bullets)
    deck_pages = planning['deck_content'].get('pages', [])
    if deck_pages:
        # 如果deck_content.pages已有数据,也需要转换格式
        planning['deck_content']['pages'] = _convert_elements_to_legacy_format(deck_pages)
    else:
        # 如果为空,使用slides转换的结果
        planning['deck_content']['pages'] = planning['pages']

    return planning


def _convert_elements_to_legacy_format(pages: List[Dict]) -> List[Dict]:
    """
    将LLM生成的新格式(elements数组)转换为Generator需要的旧格式

    新格式示例:
    {
        "elements": [
            {"type": "text", "content": {"text": "标题", "role": "title"}},
            {"type": "bullets", "content": {"items": ["项1", "项2"], "role": "body"}}
        ]
    }

    旧格式示例:
    {
        "title": "标题",
        "bullets": ["项1", "项2"]
    }
    """
    converted_pages = []

    for page in pages:
        # 如果已经是旧格式(有title和bullets),直接保留
        if 'bullets' in page or 'content' in page:
            converted_pages.append(page)
            continue

        # 从elements数组中提取数据
        elements = page.get('elements', [])
        title = ''
        subtitle = ''
        bullets = []

        for elem in elements:
            elem_type = elem.get('type')
            content = elem.get('content', {})
            role = content.get('role', '')

            if elem_type == 'text':
                if role == 'title':
                    title = content.get('text', '')
                elif role == 'subtitle':
                    subtitle = content.get('text', '')
            elif elem_type == 'bullets':
                bullets = content.get('items', [])

        # 创建兼容格式的page
        converted_page = {
            'page_num': page.get('index', 1),
            'type': page.get('slide_type', 'concept'),
            'slide_type': page.get('slide_type', 'concept'),
            'title': title or page.get('title', '标题'),
            'subtitle': subtitle,
            'content': bullets,  # Generator期望的字段
            'bullets': bullets,   # 备用字段
            'layout': page.get('layout', {}).get('template') if isinstance(page.get('layout'), dict) else page.get('layout', 'split'),
            'notes': page.get('speaker_notes') or page.get('notes'),
            'assets': page.get('assets', []),
        }

        converted_pages.append(converted_page)

    return converted_pages


def _convert_slides_to_pages(slides: List[Dict]) -> List[Dict]:
    """将新版 slides 格式转换为旧版 pages 格式（增强版 - 保留更多原始数据）"""
    pages = []

    # slide_type 到 page type 的映射
    type_mapping = {
        'cover': 'cover',  # 保留 cover 不转换
        'objectives': 'objectives',
        'intro': 'intro',
        'concept': 'concept',
        'keypoints': 'keypoints',
        'structure': 'structure',
        'principle': 'principle',
        'steps': 'steps',
        'warning': 'warning',
        'practice': 'practice',
        'summary': 'summary',
        'comparison': 'comparison',
        'gallery': 'gallery'
    }

    # slide_type 到 layout 的映射
    layout_mapping = {
        'cover': 'cover',
        'objectives': 'cards_3col',
        'intro': 'top_image',
        'concept': 'split',
        'keypoints': 'cards_4col',
        'structure': 'split',
        'principle': 'process_flow',
        'steps': 'timeline',
        'warning': 'warning',
        'practice': 'steps',
        'summary': 'summary',
        'comparison': 'comparison',
        'gallery': 'image_wall_2x2'
    }

    for slide in slides:
        slide_type = slide.get('slide_type', 'concept')
        assets = slide.get('assets', [])

        # 判断是否有图片
        has_image = len(assets) > 0

        page = {
            'page_num': slide.get('index', 1),
            'type': type_mapping.get(slide_type, 'concept'),
            'slide_type': slide_type,  # 保留原始 slide_type
            'title': slide.get('title', ''),
            'content': slide.get('bullets', []),
            'layout': layout_mapping.get(slide_type, 'split'),
            'visual_emphasis': '',
            'key_points': slide.get('bullets', []),
            # 新增字段
            'notes': slide.get('notes'),  # 教师备注
            'interactions': slide.get('interactions', []),  # 交互元素
        }

        # 添加完整的 assets 信息
        if has_image:
            first_asset = assets[0]
            page['image_description'] = first_asset.get('theme', '示意图')
            page['image_size'] = 'side' if first_asset.get('size') == '4:3' else 'top'
            page['asset_type'] = first_asset.get('type', 'image')  # image/diagram/chart/icon
            page['assets'] = assets  # 保留完整 assets 列表

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
将用户提供的非结构化课程大纲文本，**严格保留原意**地转换为符合系统规范的 全流程 JSON 格式。
不要对内容进行摘要、删减或"润色"，必须忠实还原用户的教学设计。

【输出格式要求】
输出必须是纯 JSON，包含 4 个核心字段：

{
  "teaching_request": {
    "subject": "提取的主题",
    "teaching_scene": "theory",
    "slide_count": 8,
    "teaching_goals": {
      "knowledge": "提取的知识目标",
      "ability": "提取的能力目标",
      "literacy": "提取的素养目标"
    }
  },
  "style_config": {
    "style_name": "theory_clean",
    "layout": { "notes_area": true }
  },
  "outline": {
    "deck_title": "解析出的课程标题",
    "subject": "主题",
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
  },
  "deck_content": {
    "deck_title": "解析出的课程标题",
    "pages": [
      {
        "index": 1,
        "slide_type": "cover",
        "layout": { "template": "cover" },
        "elements": [
          { "type": "text", "content": { "text": "标题", "role": "title" } }
        ]
      }
    ]
  }
}

【slide_type 映射规则】
请根据页面内容和布局描述智能映射：
- 封面/标题页 -> cover
- 目录/导航/图片墙 -> gallery
- 对比/表格/区别 -> comparison
- 步骤/流程/三联图 -> steps
- 核心概念/左右分栏 -> concept (或 structure)
- Summarize/思维导图 -> summary
- 警告/安全/挑战 -> warning
- 导入/案例 -> intro

【关键要求】
1. **Visual-First**: 如果原文描述了"视觉"、"配图"、"左图右字"，必须在 `assets` 中生成对应的图片配置。
2. **deck_content.pages**: 必须为每一页生成对应的 pages 结构，elements 为空数组即可（Generator 会自动填充）。
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

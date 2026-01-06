"""
Agent 1: Content Planner (内容规划 Agent)
负责：将用户需求转换成 PPT 式网页的分页大纲
"""
import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


def content_planner(state: Dict, llm: ChatOpenAI) -> Dict:
    """
    内容规划 Agent

    输入: state['user_input'] = {
        "topic": "机械加工-车床操作",
        "major": "机械制造",
        "target_audience": "高职二年级学生",
        "duration": "45分钟",
        "key_points": ["车床结构", "操作步骤"]  # 可选
    }

    输出: state['planning'] = {
        "course_title": "车床操作基础",
        "total_pages": 8,
        "theme_suggestion": "工业蓝灰色系",
        "pages": [...]
    }
    """

    print("🎯 Agent 1: Content Planner - 开始规划内容...")

    user_input = state['user_input']

    # 构建 Prompt
    system_prompt = """你是一位资深的高职教育课件设计专家，擅长将教学内容规划成清晰、专业、结构化的 PPT 式网页课件。

【核心教学理念】
优秀的教学课件应该：
1. 结构清晰：有明确的递进层次（引入→概念→原理→应用→实践→总结）
2. 图文并茂：每页都要合理配图，辅助学生理解
3. 视觉友好：字体大、对比强、配色专业
4. 互动性强：有思考、有提问、有案例

【质量规范 - 必须严格遵守】

1. 字体规范：
   - 标题：64-72px（投影仪清晰可读）
   - 正文：32-40px（教室后排可见）
   - 列表：32px+
   - 禁止使用小于 32px 的字体

2. 配色规范（根据专业自动匹配）：
   - 机械类：蓝灰色系（#2c3e50, #34495e）专业稳重
   - 医护类：绿白色系（#27ae60, #ecf0f1）温和安全
   - 电子类：科技蓝紫（#3498db, #9b59b6）现代科技
   - 汽车类：红灰色系（#e74c3c, #34495e）动感力量
   - 严禁使用：渐变粉紫色（#f093fb, #a6c1ee）等不专业配色

3. 对比度规范：
   - 深色背景必须配浅色文字（对比度 ≥ 4.5:1）
   - 重要内容用高对比色突出

4. 页面密度规范：
   - 每页正文≤100字
   - 列表≤6个要点
   - 每个要点≤20字
   - 标题页可以有3-4个教学目标

5. 图片规范（严格控制！）：
   - **只有 40-50% 的页面需要图片**（8页课件中3-4页有图即可）
   - **有图页面（3-4页）**：
     * 标题页：课程封面场景图（可选）
     * 引入页/应用场景页：实际工作场景
     * 核心概念页：结构图/原理图（1-2页）
     * 对比页：对比示意图（如果有）
   - **无图页面（4-5页）**：
     * 定义/概念讲解页 → 纯文字 + 要点列表
     * 步骤说明页 → 编号列表 + 文字描述
     * 注意事项页 → 警告卡片 + 列表（纯文字，无图）
     * 原理解释页 → 纯文字段落
     * 总结页 → 知识回顾列表 + 思考题（纯文字，无图）
   - **图片尺寸规范**：
     * 侧边图片：max-width: 600px, max-height: 700px
     * 顶部图片：max-width: 1200px, max-height: 500px
     * 必须设置 object-fit: contain，避免变形和溢出

6. 布局多样化规范：
   - **纯文字布局**（50%页面，无图）：
     * full_text_center: 大标题 + 段落文字，居中排版
     * text_with_bullets: 标题 + 要点列表（3-6个）
     * definition_box: 定义框 + 解释文字
     * numbered_steps: 大号编号 + 步骤文字（无图）
   - **图文混合布局**（40%页面）：
     * left_text_right_image: 左60%文字 + 右40%图片（侧边小图）
     * top_image_center: 顶部图片（高度≤500px）+ 底部文字
   - **特殊布局**（10%页面，无图）：
     * two_columns_text: 左右纯文字对比
     * warning_grid: 红色警告卡片网格（纯文字）
     * summary_boxes: 网格式知识点回顾框（纯文字）

7. 结构规范（重要！）：
   - 第1页：标题页（课程名+3-4个教学目标）
   - 第2页：引入页（为什么学？工作中的应用场景）
   - 第3-7页：主体内容（递进式：概念→组成→原理→操作→注意事项）
   - 第8页：总结页（知识回顾+思考题）

你的任务是：根据用户提供的课程信息，规划出一份符合上述所有质量规范的课件大纲。

输出要求：
1. 严格按照 JSON 格式输出
2. 页面数量 8-12 页（45分钟课程）
3. 第一页必须是标题页，最后一页是总结页
4. 每页内容精炼（投影仪演示，学生要看得清）
5. 必须体现层级递进结构"""

    user_prompt = f"""请为以下课程规划 PPT 式网页课件：

**课程信息：**
- 主题：{user_input['topic']}
- 专业：{user_input['major']}
- 授课对象：{user_input['target_audience']}
- 时长：{user_input.get('duration', '45分钟')}
{f"- 必须包含的知识点：{', '.join(user_input['key_points'])}" if user_input.get('key_points') else ""}

**页面类型说明：**
- title: 标题页（课程名称+教学目标）[可选配图]
- intro: 引入页（为什么学？应用场景）[推荐配图]
- concept: 概念讲解页（定义、原理）[可选配图，优先纯文字]
- structure: 结构/组成页（部件说明）[推荐配图]
- principle: 原理讲解页（工作机制）[纯文字，不配图]
- steps: 步骤说明页（操作流程）[纯文字，不配图]
- comparison: 对比页（AB对比）[可选配图]
- warning: 警告/注意事项页（安全提示）[纯文字，不配图]
- summary: 总结页（知识回顾、思考题）[纯文字，不配图]

**布局方式说明（严格匹配页面类型）：**

🖼️ 带图布局（仅 40% 页面使用）：
- left_text_right_image: 左60%文字 + 右40%小图（适合 concept, structure）
- top_image_center: 顶部小图（≤500px）+ 底部文字（适合 intro, comparison）

📝 纯文字布局（60% 页面使用）：
- full_text_center: 大标题 + 段落居中（适合 principle, concept）
- text_with_bullets: 标题 + 要点列表（适合 concept, principle）
- numbered_steps: 大号编号 + 步骤列表（适合 steps）
- warning_grid: 红色警告卡片网格（适合 warning）
- summary_boxes: 网格式知识回顾（适合 summary）
- two_columns_text: 左右纯文字对比（适合 comparison）

**输出 JSON 格式：**
{{
  "course_title": "课程完整标题",
  "total_pages": 8,
  "theme_suggestion": "推荐配色主题（如：工业蓝灰色系、科技紫青色系、暖色橙棕色系、医护绿白色系）",
  "image_page_count": 3,  // 有图页面数量（3-4页）
  "text_only_page_count": 5,  // 纯文字页面数量（4-5页）
  "pages": [
    {{
      "page_num": 1,
      "type": "title|intro|concept|structure|principle|steps|warning|summary",
      "title": "页面标题",
      "content": "主要内容（可以是字符串、列表等）",
      "layout": "center|left_text_right_image|top_image_center|full_text_center|text_with_bullets|numbered_steps|warning_grid|summary_boxes|two_columns_text",
      "visual_emphasis": "视觉重点说明",
      "image_description": "仅当需要图片时填写（否则不要此字段或设为 null）",
      "image_size": "side|top"  // 仅当有图片时填写：side=侧边小图, top=顶部小图
    }},
    // 示例：纯文字页面
    {{
      "page_num": 3,
      "type": "concept",
      "title": "什么是车床？",
      "content": ["定义：通过工件旋转、刀具直线运动实现金属切削的机床", "特点：适合加工回转体零件", "应用：轴类、盘类零件加工"],
      "layout": "text_with_bullets",
      "visual_emphasis": "重点词汇用蓝色高亮"
      // 无 image_description 字段
    }},
    // 示例：带图页面
    {{
      "page_num": 4,
      "type": "structure",
      "title": "车床主要组成部分",
      "content": ["主轴箱：驱动工件旋转", "进给箱：控制刀具移动速度", "溜板箱：实现纵向/横向进给", "刀架：安装切削刀具"],
      "layout": "left_text_right_image",
      "visual_emphasis": "部件名称用粗体",
      "image_description": "卧式车床结构分解图，各部件用数字标注并配文字说明",
      "image_size": "side"
    }}
  ]
}}

**严格要求：**
1. content 字段：
   - 如果是列表内容（如步骤），用数组：["步骤1", "步骤2", ...]，最多6个要点
   - 如果是段落文字，用字符串，控制在100字以内

2. 布局对称性原则：
   - two_columns 布局：每栏内容数量必须相同（2对2，3对3）
   - grid 布局：总内容数必须是列数的倍数（3列就6个或9个项目）
   - left_text_right_image：左侧文字2-4个要点，右侧1张图片

3. 图片字段规范（严格控制！）：
   - **只有需要图片的页面才填写 image_description 字段**
   - **无图页面**：不要有 image_description 字段，或设为 null
   - **有图页面**（3-4页）：
     * image_description: "具体的图片内容描述"
     * image_size: "side"（侧边小图）或 "top"（顶部小图）
   - **图片描述示例**：
     * ✅ "车床主轴箱结构剖面图，标注主轴、齿轮、轴承等部件"
     * ✅ "工厂车间内，工人操作数控车床的实景照片"
     * ❌ "图片"、"配图"、"示意图"（太模糊）
   - **严禁全部页面都配图**，必须有 50% 以上的纯文字页面

4. 课程结构（必须体现递进，合理分配有图/无图）：
   - 第1页：标题页（type: title, layout: center）[可选配图]
   - 第2页：引入页（type: intro, layout: top_image_center）[有图]
   - 第3页：概念定义（type: concept, layout: text_with_bullets）[无图]
   - 第4页：组成结构（type: structure, layout: left_text_right_image）[有图]
   - 第5页：工作原理（type: principle, layout: full_text_center）[无图]
   - 第6页：操作步骤（type: steps, layout: numbered_steps）[无图]
   - 第7页：安全警告（type: warning, layout: warning_grid）[无图]
   - 第8页：总结页（type: summary, layout: summary_boxes）[无图]

   **图片分配统计**：8页中2-3页有图（25-37%），符合40-50%目标

5. 专业适配：
   - 内容符合{user_input['major']}专业特点
   - 语言符合{user_input['target_audience']}的认知水平
   - 配色遵守专业规范（机械→蓝灰，医护→绿白等）

6. 投影演示优化：
   - 每页内容精炼（字少图大）
   - 标题清晰（教室后排可见）
   - 对比度强（深色背景配浅色文字）

请直接输出 JSON，不要有其他解释。"""

    try:
        # 调用 LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        response_text = response.content.strip()

        # 提取 JSON（去除可能的 markdown 代码块标记）
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].split("```")[0].strip()

        # 解析 JSON
        planning = json.loads(response_text)

        # 验证必需字段
        required_fields = ["course_title", "total_pages", "pages"]
        for field in required_fields:
            if field not in planning:
                raise ValueError(f"缺少必需字段: {field}")

        print(f"✅ 规划完成：{planning['course_title']}，共 {planning['total_pages']} 页")
        print(f"   主题风格：{planning.get('theme_suggestion', '未指定')}")

        return {
            **state,
            "planning": planning,
            "status": "planning_completed",
            "messages": state.get("messages", []) + messages + [response]
        }

    except json.JSONDecodeError as e:
        error_msg = f"JSON 解析失败: {e}\n原始响应:\n{response_text[:500]}"
        print(f"❌ {error_msg}")
        return {
            **state,
            "error": error_msg,
            "status": "failed"
        }

    except Exception as e:
        error_msg = f"内容规划失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            **state,
            "error": error_msg,
            "status": "failed"
        }

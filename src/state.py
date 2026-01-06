"""
定义 LangGraph 的 State 结构（高职教育 PPT 生成场景）
"""
from typing import TypedDict, Dict, List, Optional
from langchain_core.messages import BaseMessage


class PPTWebState(TypedDict):
    """PPT 式网页生成的状态定义"""

    # ========== 输入 ==========
    user_input: Dict  # {
                      #   "topic": "机械加工-车床操作",
                      #   "major": "机械制造",
                      #   "target_audience": "高职二年级学生",
                      #   "duration": "45分钟",
                      #   "key_points": ["车床结构", "操作步骤", "安全规范"]  # 可选
                      # }

    # ========== Agent 1: Content Planner 输出 ==========
    planning: Optional[Dict]  # {
                              #   "course_title": "课程标题",
                              #   "total_pages": 8,
                              #   "theme_suggestion": "工业蓝灰色系",
                              #   "pages": [
                              #     {
                              #       "page_num": 1,
                              #       "type": "title",
                              #       "title": "页面标题",
                              #       "content": "主要内容",
                              #       "layout": "center",
                              #       "visual_emphasis": "视觉重点",
                              #       "image_description": "需要的图片描述"
                              #     },
                              #     ...
                              #   ]
                              # }

    # ========== Agent 2: Designer & Generator 输出 ==========
    html_code: Optional[str]  # 完整的 reveal.js HTML 代码

    # ========== Agent 3: Quality Checker 输出 ==========
    quality_issues: List[str]  # 发现的问题列表
    iteration_count: int       # 迭代次数（防止无限循环）

    # ========== 最终输出 ==========
    final_html: Optional[str]  # 通过质检的最终 HTML
    status: str                # "pending" | "planning" | "generating" | "checking" | "completed" | "failed"

    # ========== 元数据 ==========
    execution_time: Optional[float]
    messages: List[BaseMessage]
    error: Optional[str]

"""
专业配色方案（企业级标准）
去除渐变色和不专业的粉紫色，使用行业标准配色
"""

# 专业配色方案（纯色，无渐变）
PROFESSIONAL_COLOR_SCHEMES = {
    "机械": {
        "primary": "#2c3e50",           # 深蓝灰（专业稳重）
        "secondary": "#34495e",         # 中灰蓝
        "accent": "#3498db",            # 明亮蓝（强调色）
        "bg_dark": "#1a252f",           # 深蓝黑背景
        "surface": "#2c3e50",           # 卡片表面
        "text_primary": "#ecf0f1",      # 主文字（浅灰白）
        "text_secondary": "#bdc3c7",    # 次级文字
        "text_accent": "#3498db",       # 强调文字
        "warning": "#e74c3c"            # 警告红色
    },
    "医护": {
        "primary": "#27ae60",           # 医疗绿
        "secondary": "#2ecc71",         # 亮绿
        "accent": "#16a085",            # 青绿（强调）
        "bg_dark": "#1e3a28",           # 深绿背景
        "surface": "#27ae60",           # 卡片表面
        "text_primary": "#ecf0f1",      # 主文字
        "text_secondary": "#d5f4e6",    # 次级文字（浅绿）
        "text_accent": "#2ecc71",       # 强调文字
        "warning": "#e74c3c"            # 警告红色
    },
    "电子": {
        "primary": "#3498db",           # 科技蓝
        "secondary": "#9b59b6",         # 科技紫
        "accent": "#1abc9c",            # 青色（强调）
        "bg_dark": "#1e2a3a",           # 深蓝背景
        "surface": "#2c3e50",           # 卡片表面
        "text_primary": "#ecf0f1",      # 主文字
        "text_secondary": "#bdc3c7",    # 次级文字
        "text_accent": "#3498db",       # 强调文字
        "warning": "#e74c3c"            # 警告红色
    },
    "汽车": {
        "primary": "#e74c3c",           # 汽车红
        "secondary": "#c0392b",         # 深红
        "accent": "#95a5a6",            # 银灰（强调）
        "bg_dark": "#2a1e1e",           # 深红背景
        "surface": "#34495e",           # 卡片表面（深灰）
        "text_primary": "#ecf0f1",      # 主文字
        "text_secondary": "#bdc3c7",    # 次级文字
        "text_accent": "#e74c3c",       # 强调文字
        "warning": "#f39c12"            # 警告橙色
    },
    "计算机": {
        "primary": "#9b59b6",           # 科技紫
        "secondary": "#8e44ad",         # 深紫
        "accent": "#3498db",            # 蓝色（强调）
        "bg_dark": "#2a1e3a",           # 深紫背景
        "surface": "#34495e",           # 卡片表面
        "text_primary": "#ecf0f1",      # 主文字
        "text_secondary": "#bdc3c7",    # 次级文字
        "text_accent": "#9b59b6",       # 强调文字
        "warning": "#e74c3c"            # 警告红色
    },
    "default": {
        "primary": "#2c3e50",           # 默认深蓝灰
        "secondary": "#34495e",         # 中灰蓝
        "accent": "#3498db",            # 明亮蓝
        "bg_dark": "#1a252f",           # 深色背景
        "surface": "#2c3e50",           # 卡片表面
        "text_primary": "#ecf0f1",      # 主文字
        "text_secondary": "#bdc3c7",    # 次级文字
        "text_accent": "#3498db",       # 强调文字
        "warning": "#e74c3c"            # 警告红色
    }
}


def get_color_scheme(major: str) -> dict:
    """
    根据专业获取配色方案

    Args:
        major: 专业名称

    Returns:
        配色字典
    """
    # 匹配专业关键词
    keywords_mapping = {
        "机械": ["机械", "车床", "数控", "模具", "制造"],
        "医护": ["医护", "护理", "医疗", "药学", "康复"],
        "电子": ["电子", "电气", "自动化", "物联网", "通信"],
        "汽车": ["汽车", "汽修", "新能源汽车"],
        "计算机": ["计算机", "软件", "网络", "大数据", "人工智能"]
    }

    for category, keywords in keywords_mapping.items():
        for keyword in keywords:
            if keyword in major:
                return PROFESSIONAL_COLOR_SCHEMES[category]

    # 默认配色
    return PROFESSIONAL_COLOR_SCHEMES["default"]

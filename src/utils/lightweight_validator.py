"""
轻量级 HTML 验证器
不调用 LLM，使用正则和 DOM 解析快速验证和修复

预计执行时间：2-5秒
"""
import re
from typing import Dict, List

# 专业配色映射
PROFESSIONAL_COLORS = {
    '机械': {'primary': '#2c3e50', 'secondary': '#34495e', 'accent': '#7f8c8d', 'bg': '#1a252f'},
    '医护': {'primary': '#27ae60', 'secondary': '#2ecc71', 'accent': '#ecf0f1', 'bg': '#1e3a28'},
    '电子': {'primary': '#3498db', 'secondary': '#9b59b6', 'accent': '#ecf0f1', 'bg': '#1e2a3a'},
    '汽车': {'primary': '#e74c3c', 'secondary': '#c0392b', 'accent': '#ecf0f1', 'bg': '#2a1e1e'},
    '计算机': {'primary': '#9b59b6', 'secondary': '#8e44ad', 'accent': '#ecf0f1', 'bg': '#2a1e3a'},
}

# 禁用配色
FORBIDDEN_COLORS = ['#f093fb', '#a6c1ee', '#ff6fd8', 'linear-gradient']


def validate_and_fix(html_code: str, user_input: Dict) -> Dict:
    """
    验证并修复 HTML 代码

    Args:
        html_code: 待验证的 HTML 代码
        user_input: 用户输入（用于判断专业等）

    Returns:
        {
            "validated_html": 修复后的 HTML,
            "issues_found": 发现的问题数量,
            "issues": 问题列表,
            "fixes_applied": 应用的修复
        }
    """
    issues = []
    fixes = []
    fixed_html = html_code

    # ===== 规则1: 修复过小字体 =====
    small_font_pattern = r'font-size:\s*([1-2]?\d)px'
    small_fonts = re.findall(small_font_pattern, html_code)

    if small_fonts:
        def replace_small_font(match):
            size = int(match.group(1))
            if size < 32:
                return 'font-size: 32px'
            return match.group(0)

        fixed_html = re.sub(small_font_pattern, replace_small_font, fixed_html)
        issues.append(f"发现 {len(small_fonts)} 处过小字体（<32px）")
        fixes.append("已修复为 32px")

    # ===== 规则2: 修复不当配色（渐变色、粉紫色等）=====
    major = user_input.get('major', '')

    # 获取专业配色
    professional_color = None
    for key, colors in PROFESSIONAL_COLORS.items():
        if key in major:
            professional_color = colors
            break

    # 默认使用机械类配色
    if not professional_color:
        professional_color = PROFESSIONAL_COLORS['机械']

    # 替换渐变背景为纯色
    if 'linear-gradient' in html_code or 'gradient' in html_code.lower():
        fixed_html = re.sub(
            r'background:\s*linear-gradient\([^)]+\)',
            f"background: {professional_color['bg']}",
            fixed_html
        )
        issues.append("发现渐变背景")
        fixes.append(f"已替换为专业色 {professional_color['bg']}")

    # 替换禁用颜色
    for forbidden_color in FORBIDDEN_COLORS:
        if forbidden_color in html_code and forbidden_color != 'linear-gradient':
            fixed_html = fixed_html.replace(forbidden_color, professional_color['primary'])
            issues.append(f"发现不当配色 {forbidden_color}")
            fixes.append(f"已替换为专业色 {professional_color['primary']}")

    # ===== 规则3: 移除 fragment 动画 =====
    if 'fragment' in html_code:
        fixed_html = re.sub(r'\s*class="fragment[^"]*"', '', fixed_html)
        fixed_html = re.sub(r'\s*class="[^"]*fragment[^"]*"', lambda m: m.group(0).replace('fragment', ''), fixed_html)
        issues.append("发现 fragment 动画")
        fixes.append("已移除（提升可读性）")

    # ===== 规则4: 确保标题对比度 =====
    # 深色背景 → 浅色文字
    fixed_html = re.sub(
        r'(<section[^>]*style="[^"]*background:\s*#[0-3][0-9a-f]{5}[^"]*"[^>]*>.*?<h[12][^>]*)(>)',
        lambda m: m.group(1) + ' style="color: #ecf0f1;"' + m.group(2) if 'color:' not in m.group(1) else m.group(0),
        fixed_html,
        flags=re.DOTALL
    )

    # ===== 规则5: 修复标题字体大小 =====
    # h1 应该 >= 64px
    fixed_html = re.sub(
        r'(<h1[^>]*style="[^"]*font-size:\s*)([1-5]?\d)(px)',
        lambda m: m.group(1) + ('72' if int(m.group(2)) < 64 else m.group(2)) + m.group(3),
        fixed_html
    )

    # h2 应该 >= 48px
    fixed_html = re.sub(
        r'(<h2[^>]*style="[^"]*font-size:\s*)([1-4]?\d)(px)',
        lambda m: m.group(1) + ('48' if int(m.group(2)) < 48 else m.group(2)) + m.group(3),
        fixed_html
    )

    return {
        "validated_html": fixed_html,
        "issues_found": len(issues),
        "issues": issues,
        "fixes_applied": fixes,
        "execution_time": "< 2秒"
    }


def get_professional_colors(major: str) -> Dict:
    """
    根据专业获取配色方案

    Args:
        major: 专业名称

    Returns:
        配色字典
    """
    for key, colors in PROFESSIONAL_COLORS.items():
        if key in major:
            return colors

    # 默认返回机械类配色
    return PROFESSIONAL_COLORS['机械']

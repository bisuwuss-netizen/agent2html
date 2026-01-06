"""
Agent 3: Quality Checker (质量检查 Agent)
负责：检查生成的 HTML 质量，并提供优化建议
"""
import re
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


def quality_checker(state: Dict, llm: ChatOpenAI) -> Dict:
    """
    质量检查 Agent

    输入: state['html_code'] (来自 Agent 2)
    输出: state['quality_issues'] (问题列表)

    如果有问题且未超过最大迭代次数，返回优化后的 html_code
    否则，标记为 completed
    """

    print("🔍 Agent 3: Quality Checker - 开始质量检查...")

    if not state.get('html_code'):
        return {
            **state,
            "error": "缺少 html_code，无法检查质量",
            "status": "failed"
        }

    html_code = state['html_code']
    planning = state.get('planning', {})
    user_input = state['user_input']
    iteration_count = state.get('iteration_count', 0)

    issues = []

    # ========== 1. 规格检查 ==========
    print("   📏 检查规格...")

    # 检查页面数量
    page_count = html_code.count("<section")
    expected_count = planning.get('total_pages', 0)
    if expected_count > 0 and page_count != expected_count:
        issues.append(f"页面数量不对：应该 {expected_count} 页，实际 {page_count} 页")

    # 检查尺寸设置
    if "width: 1920" not in html_code and "width:1920" not in html_code:
        issues.append("未设置标准 PPT 宽度（1920px）")

    if "height: 1080" not in html_code and "height:1080" not in html_code:
        issues.append("未设置标准 PPT 高度（1080px）")

    # 检查字体大小（不应该有小于 32px 的正文）
    # 排除装饰性小字体（如 no-check class 或 14px 以下的小点）
    small_font_matches = re.finditer(r'font-size:\s*(\d+)px', html_code)
    found_sizes = set()
    for match in small_font_matches:
        size = int(match.group(1))
        # 允许 14px 左右的装饰字体，且只对 > 14 且 < 32 的字体报警
        if 14 < size < 32:
            # 尝试通过上下文判断是否是正文标签
            start_pos = match.start()
            context = html_code[max(0, start_pos-100):min(len(html_code), start_pos+100)]
            # 如果在 p, li, h1, h2 等标签内，或者是全局样式设置
            if any(tag in context.lower() for tag in ['p', 'li', 'h1', 'h2', 'span', 'td']):
                if size not in found_sizes:
                    issues.append(f"发现过小的字体：{size}px（正文及列表最小建议为 32px）")
                    found_sizes.add(size)
    
    # 特别检查是否有 12px 这种极小的装饰字体被误报过
    if "12px" in found_sizes:
        print("   ⚠️  忽略 12px 装饰性字体报警")
        issues = [i for i in issues if "12px" not in i]

    # ========== 2. reveal.js 规范检查 ==========
    print("   📦 检查 reveal.js 规范...")

    if '<div class="reveal">' not in html_code:
        issues.append("缺少 reveal.js 容器：<div class=\"reveal\">")

    if 'Reveal.initialize' not in html_code:
        issues.append("缺少 reveal.js 初始化代码")

    if 'reveal.js' not in html_code.lower():
        issues.append("未引入 reveal.js CDN")

    # ========== 3. 可访问性检查 ==========
    print("   ♿ 检查可访问性...")

    if '<img' in html_code:
        img_tags = re.findall(r'<img[^>]*>', html_code)
        missing_alt_count = 0
        for tag in img_tags:
            if 'alt=' not in tag:
                missing_alt_count += 1

        if missing_alt_count > 0:
            issues.append(f"有 {missing_alt_count} 个图片缺少 alt 属性")

    # 检查标题层级
    if '<h1' not in html_code and '<h2' not in html_code:
        issues.append("缺少标题标签（h1 或 h2）")

    # ========== 4. 教学适配性检查（使用 LLM） ==========
    print("   🎓 检查教学适配性...")

    # 只在第一次迭代时做 LLM 检查（节省成本）
    if iteration_count == 0:
        llm_check_prompt = f"""检查这个高职课件网页的教学适配性：

**课程信息：**
- 主题：{user_input.get('topic', '未知')}
- 专业：{user_input.get('major', '未知')}
- 授课对象：{user_input.get('target_audience', '未知')}

**规划的页面数：** {planning.get('total_pages', 0)}

**生成的 HTML 代码片段：**
```html
{html_code[:2000]}
...
{html_code[-1000:]}
```

请检查以下几点：

1. **配色是否符合专业特点？**
   - 机械类应该用冷色调（蓝灰）
   - 烹饪类应该用暖色调（橙棕）
   - 医护类应该用绿白色系

2. **字体和对比度是否适合课堂演示？**
   - 字体够大吗？（标题 ≥ 56px，正文 ≥ 32px）
   - 对比度够吗？（投影仪友好）

3. **页面结构是否完整？**
   - 是否有标题页、内容页、总结页？
   - 页面数量是否正确？

4. **内容是否清晰易读？**
   - 排版是否整洁？
   - 是否有明显的视觉干扰？

**输出格式：**
如果发现问题，列出具体问题（每行一个）
如果没有问题，只输出："无明显问题"

请只列出问题，不要解释或建议。"""

        try:
            llm_response = llm.invoke([HumanMessage(content=llm_check_prompt)])
            llm_result = llm_response.content.strip()

            if "无明显问题" not in llm_result and "无问题" not in llm_result:
                # 解析 LLM 返回的问题
                llm_issues = [line.strip() for line in llm_result.split('\n') if line.strip()]
                # 过滤掉解释性文字，只保留问题描述
                for issue in llm_issues:
                    if len(issue) > 10 and not issue.startswith("**"):  # 简单过滤
                        issues.append(f"LLM检查: {issue}")

        except Exception as e:
            print(f"   ⚠️  LLM 检查失败: {e}")

    # ========== 5. 决定是否需要优化 ==========
    print(f"   📊 检查完成，发现 {len(issues)} 个问题")

    if issues:
        print("   问题列表：")
        for i, issue in enumerate(issues, 1):
            print(f"      {i}. {issue}")

    MAX_ITERATIONS = 2

    if issues and iteration_count < MAX_ITERATIONS:
        print(f"   🔧 准备优化（第 {iteration_count + 1}/{MAX_ITERATIONS} 轮）...")

        # 生成优化指令
        optimization_prompt = f"""请修复以下 HTML 代码中的问题：

**发现的问题：**
{chr(10).join(f"{i+1}. {issue}" for i, issue in enumerate(issues))}

**原始 HTML 代码：**
```html
{html_code}
```

**要求：**
1. 只修复上述问题，不要改变其他部分
2. 保持 reveal.js 结构完整
3. 确保所有页面内容都在
4. 直接输出修复后的完整 HTML 代码
5. 不要有任何解释文字或 markdown 标记

请输出修复后的完整 HTML："""

        try:
            response = llm.invoke([HumanMessage(content=optimization_prompt)])
            optimized_html = response.content.strip()

            # 去除可能的 markdown 标记
            if optimized_html.startswith("```html"):
                optimized_html = optimized_html.split("```html")[1].split("```")[0].strip()
            elif optimized_html.startswith("```"):
                optimized_html = optimized_html.split("```")[1].split("```")[0].strip()

            print("   ✅ 优化完成，准备重新检查...")

            return {
                **state,
                "html_code": optimized_html,
                "quality_issues": [],  # 清空问题列表，等待下一轮检查
                "iteration_count": iteration_count + 1,
                "status": "optimizing"
            }

        except Exception as e:
            error_msg = f"优化失败: {str(e)}"
            print(f"   ❌ {error_msg}")
            # 优化失败，使用原始代码继续
            issues.append(error_msg)

    # 如果没有问题，或者已经达到最大迭代次数，标记为完成
    if not issues:
        print("   ✅ 质检通过！")
        final_status = "completed"
    else:
        print(f"   ⚠️  仍有 {len(issues)} 个问题，但已达最大迭代次数，使用当前版本")
        final_status = "completed_with_issues"

    return {
        **state,
        "quality_issues": issues,
        "final_html": html_code,
        "status": final_status
    }

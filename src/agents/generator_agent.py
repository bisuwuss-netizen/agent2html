"""
Generator Agent: 整合所有信息生成最终的HTML和CSS
"""
import re
import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..state import WebGenState


def generator_agent(state: WebGenState, llm: ChatOpenAI) -> Dict:
    """
    生成Agent - 整合plan、design、content生成完整的HTML和CSS
    """
    plan = state.get("plan", {})
    design_spec = state.get("design_spec", {})
    content_data = state.get("content_data", {})
    
    if not all([plan, design_spec, content_data]):
        return {"error": "Generator agent需要完整的plan、design和content输入"}
    
    print("🚀 [Generator] 开始生成HTML和CSS...")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是资深前端工程师。基于提供的信息生成完整的HTML和CSS代码。

要求:
1. HTML必须使用HTML5语义化标签
2. 响应式设计(移动优先)
3. CSS使用现代特性(Grid/Flexbox/CSS Variables)
4. 包含平滑的过渡和动画效果
5. 代码注释清晰
6. SEO友好
7. 无障碍支持(ARIA标签)

输出格式要求:
必须严格按照以下格式输出,用```html```和```css```包裹代码:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <!-- 完整的HTML代码 -->
</head>
<body>
    <!-- 页面内容 -->
</body>
</html>
```
```css
/* 完整的CSS代码 */
```

注意:
- 直接输出代码,不要有任何额外解释
- HTML和CSS必须分别用代码块包裹
- 确保代码可以直接运行
"""),
        ("user", """请生成网页代码:

# 规划
{plan}

# 设计规范
{design}

# 内容数据
{content}

请严格按照要求的格式输出HTML和CSS代码。""")
    ])
    
    chain = prompt | llm
    result = chain.invoke({
        "plan": json.dumps(plan, ensure_ascii=False, indent=2)[:2000],
        "design": json.dumps(design_spec, ensure_ascii=False, indent=2),
        "content": json.dumps(content_data, ensure_ascii=False, indent=2)
    })
    
    content = result.content
    
    # 提取HTML代码
    html_pattern = r'```html\s*(.*?)```'
    html_matches = re.findall(html_pattern, content, re.DOTALL)
    
    # 提取CSS代码
    css_pattern = r'```css\s*(.*?)```'
    css_matches = re.findall(css_pattern, content, re.DOTALL)
    
    if html_matches and css_matches:
        html = html_matches[0].strip()
        css = css_matches[0].strip()
        
        print("✅ [Generator] 代码生成完成")
        return {
            "html": html,
            "css": css
        }
    else:
        print("❌ [Generator] 代码提取失败")
        print(f"Debug - 原始输出:\n{content[:500]}...")
        return {
            "error": "Generator agent无法提取HTML或CSS代码",
            "raw_output": content
        }
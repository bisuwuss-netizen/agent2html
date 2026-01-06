"""
Design Agent: 生成设计规范和样式指南
"""
import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..state import WebGenState


def design_agent(state: WebGenState, llm: ChatOpenAI) -> Dict:
    """
    设计Agent - 生成配色、字体、间距等设计规范
    """
    plan = state.get("plan", {})
    
    if not plan:
        return {"error": "Design agent需要plan输入"}
    
    print("🎨 [Design] 开始设计样式方案...")
    
    # 根据风格偏好选择主题
    style_preference = plan.get("intent", {}).get("style_preference", "现代")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是UI/UX设计专家。基于规划生成精美的设计规范JSON。

输出JSON结构:
{{
  "theme": {{
    "name": "主题名称",
    "mood": "设计氛围描述"
  }},
  "colors": {{
    "primary": "#hex颜色",
    "secondary": "#hex颜色",
    "background": "#hex颜色",
    "surface": "#hex颜色",
    "text": "#hex颜色",
    "text_secondary": "#hex颜色",
    "accent": "#hex颜色",
    "success": "#hex颜色",
    "warning": "#hex颜色",
    "error": "#hex颜色"
  }},
  "typography": {{
    "heading": {{
      "family": "字体名称(使用Google Fonts)",
      "weights": [400, 600, 700]
    }},
    "body": {{
      "family": "字体名称",
      "weights": [400, 500]
    }},
    "scale": {{
      "xs": "12px",
      "sm": "14px",
      "base": "16px",
      "lg": "18px",
      "xl": "20px",
      "2xl": "24px",
      "3xl": "30px",
      "4xl": "36px",
      "5xl": "48px"
    }}
  }},
  "spacing": {{
    "unit": 8,
    "scale": {{
      "0": "0",
      "1": "8px",
      "2": "16px",
      "3": "24px",
      "4": "32px",
      "5": "40px",
      "6": "48px",
      "8": "64px",
      "10": "80px",
      "12": "96px"
    }}
  }},
  "borders": {{
    "radius": {{
      "sm": "4px",
      "md": "8px",
      "lg": "12px",
      "xl": "16px",
      "full": "9999px"
    }},
    "width": {{
      "thin": "1px",
      "medium": "2px",
      "thick": "4px"
    }}
  }},
  "shadows": {{
    "sm": "0 1px 2px rgba(0,0,0,0.05)",
    "md": "0 4px 6px rgba(0,0,0,0.1)",
    "lg": "0 10px 15px rgba(0,0,0,0.1)",
    "xl": "0 20px 25px rgba(0,0,0,0.15)"
  }},
  "animations": {{
    "duration": {{
      "fast": "150ms",
      "normal": "300ms",
      "slow": "500ms"
    }},
    "easing": {{
      "ease_in": "cubic-bezier(0.4, 0, 1, 1)",
      "ease_out": "cubic-bezier(0, 0, 0.2, 1)",
      "ease_in_out": "cubic-bezier(0.4, 0, 0.2, 1)"
    }},
    "effects": ["fade-in", "slide-up", "scale-up"]
  }},
  "components": {{
    "button": {{
      "padding": "12px 24px",
      "border_radius": "8px",
      "font_weight": "600"
    }},
    "card": {{
      "padding": "24px",
      "border_radius": "12px",
      "shadow": "md"
    }}
  }}
}}

风格参考:
- 现代科技感: 深色背景、霓虹色、渐变、动画
- 极简主义: 大量留白、单色系、简洁字体
- 复古: 暖色调、装饰性字体、纹理
- 炫酷: 高对比度、动态效果、创意布局
- 商务专业: 蓝色系、经典字体、稳重配色

当前用户风格偏好: {style}

注意:
1. 颜色必须和谐搭配
2. 字体选择Google Fonts中的免费字体
3. 确保输出完整有效的JSON
4. 不要添加注释或解释
"""),
        ("user", "规划内容:\n{plan}")
    ])
    
    chain = prompt | llm
    result = chain.invoke({
        "plan": json.dumps(plan, ensure_ascii=False, indent=2),
        "style": style_preference
    })
    
    try:
        design_spec = json.loads(result.content)
        print("✅ [Design] 设计方案完成")
        return {"design_spec": design_spec}
    except json.JSONDecodeError as e:
        print(f"❌ [Design] JSON解析失败: {e}")
        return {"error": f"Design agent JSON解析失败: {e}"}
"""
Content Agent: 生成具体的页面内容数据
"""
import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..state import WebGenState


def content_agent(state: WebGenState, llm: ChatOpenAI) -> Dict:
    """
    内容Agent - 生成页面的具体文字、图片占位符等内容
    """
    plan = state.get("plan", {})
    
    if not plan:
        return {"error": "Content agent需要plan输入"}
    
    print("📝 [Content] 开始生成内容数据...")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是内容策划专家。基于规划生成具体的页面内容JSON。

输出JSON结构:
{{
  "meta": {{
    "title": "页面标题(50字以内)",
    "description": "SEO描述(150字以内)",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "author": "作者名称"
  }},
  "sections": {{
    "hero": {{
      "heading": "主标题(吸引人的短句)",
      "subheading": "副标题(补充说明)",
      "cta": {{
        "text": "按钮文字",
        "link": "#目标区域id"
      }},
      "background_image": "hero-bg.jpg"
    }},
    "about": {{
      "heading": "关于标题",
      "content": [
        "第一段内容...",
        "第二段内容..."
      ],
      "image": "about-image.jpg"
    }},
    "features": {{
      "heading": "特性/服务标题",
      "items": [
        {{
          "title": "特性1",
          "description": "特性描述",
          "icon": "icon-name"
        }}
      ]
    }},
    "projects": {{
      "heading": "项目/作品集标题",
      "items": [
        {{
          "title": "项目名称",
          "description": "项目简介(80字左右)",
          "tags": ["标签1", "标签2"],
          "image": "project-1.jpg",
          "link": "#"
        }}
      ]
    }},
    "contact": {{
      "heading": "联系方式标题",
      "email": "example@email.com",
      "phone": "+86 138-0000-0000",
      "social_links": [
        {{"platform": "GitHub", "url": "#"}},
        {{"platform": "LinkedIn", "url": "#"}}
      ]
    }}
  }},
  "footer": {{
    "copyright": "© 2025 版权信息",
    "links": [
      {{"text": "隐私政策", "url": "#"}},
      {{"text": "使用条款", "url": "#"}}
    ]
  }}
}}

注意:
1. 根据规划中的sections生成对应内容
2. 文字要符合页面类型和风格
3. 项目/作品至少3个
4. 特性/服务至少3个
5. 图片使用占位符名称
6. 确保输出完整有效的JSON
7. 不要添加注释或解释
"""),
        ("user", "规划内容:\n{plan}")
    ])
    
    chain = prompt | llm
    result = chain.invoke({
        "plan": json.dumps(plan, ensure_ascii=False, indent=2)
    })
    
    try:
        content_data = json.loads(result.content)
        print("✅ [Content] 内容数据完成")
        return {"content_data": content_data}
    except json.JSONDecodeError as e:
        print(f"❌ [Content] JSON解析失败: {e}")
        return {"error": f"Content agent JSON解析失败: {e}"}
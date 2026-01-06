"""
Planning Agent: 合并了意图理解、内容规划、结构设计
"""
import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..state import WebGenState
from ..cache import CacheManager

# 全局缓存实例
cache_manager = CacheManager()


def planning_agent(state: WebGenState, llm: ChatOpenAI) -> Dict:
    """
    规划Agent - 一次性完成意图理解、内容规划、结构设计
    """
    user_input = state["user_input"]
    
    # 检查缓存
    cache_key = cache_manager.generate_key(user_input, "planning")
    cached_result = cache_manager.get(cache_key)
    
    if cached_result:
        print("✅ [Planning] 使用缓存结果")
        return {"plan": cached_result}
    
    print("🤔 [Planning] 开始分析需求...")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是网页规划专家。分析用户需求并输出完整的规划JSON。

输出JSON结构:
{{
  "intent": {{
    "page_type": "个人作品集/企业官网/产品页/博客/其他",
    "style_preference": "现代科技感/极简主义/复古/炫酷/商务专业/其他",
    "target_audience": "目标用户描述",
    "key_goals": ["主要目标1", "主要目标2"]
  }},
  "content": {{
    "page_title": "页面标题",
    "sections": [
      {{
        "id": "hero",
        "type": "hero-banner",
        "priority": 1,
        "description": "区域描述",
        "required_elements": ["标题", "副标题", "CTA按钮"]
      }},
      {{
        "id": "about",
        "type": "content-block",
        "priority": 2,
        "description": "个人介绍/公司介绍",
        "required_elements": ["文字内容", "可选图片"]
      }}
    ]
  }},
  "structure": {{
    "layout": "single-page/multi-page",
    "navigation": {{
      "type": "fixed-top/sticky/hidden",
      "items": ["首页", "关于", "项目", "联系"]
    }},
    "responsive": {{
      "strategy": "mobile-first",
      "breakpoints": ["mobile", "tablet", "desktop"]
    }}
  }},
  "technical_requirements": {{
    "seo_optimized": true,
    "accessible": true,
    "animations": true
  }}
}}

注意：
1. 根据用户需求合理推断内容结构
2. sections数量一般3-6个
3. 确保输出完整有效的JSON
4. 不要添加注释或解释
"""),
        ("user", "{input}")
    ])
    
    chain = prompt | llm
    result = chain.invoke({"input": user_input})
    
    try:
        plan = json.loads(result.content)
        # 保存到缓存
        cache_manager.set(cache_key, plan)
        print("✅ [Planning] 规划完成")
        return {"plan": plan}
    except json.JSONDecodeError as e:
        print(f"❌ [Planning] JSON解析失败: {e}")
        return {"error": f"Planning agent JSON解析失败: {e}"}
"""
测试新版全流程 JSON 格式输入
验证 Planner 是否能正确处理 nested structure (outline, deck_content)
"""
import os
import time
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# 使用 refined_project_data_spec.json 的内容 (去除注释)
json_input = '''
{
  "teaching_request": {
    "subject": "机械基础 齿轮传动原理",
    "knowledge_points": ["齿轮传动原理"],
    "teaching_scene": "theory",
    "slide_count": 8,
    "include_cases": true,
    "teaching_goals": {
      "knowledge": "理解齿轮传动的基本原理和核心要点",
      "ability": "能够应用齿轮传动原理分析简单应用场景",
      "literacy": "理解掌握齿轮转动的原理"
    },
    "raw_user_input": "生成一份高职机械基础‘齿轮传动原理’...",
    "source": "llm"
  },
  "style_config": {
    "style_name": "theory_clean",
    "color": {
      "primary": "#1F4E79",
      "secondary": "#F3F5F7",
      "accent": "#2E75B6",
      "text": "#111827",
      "background": "#FFFFFF",
      "warning": "#DC2626"
    },
    "font": {
      "title_family": "Microsoft YaHei",
      "body_family": "Microsoft YaHei"
    },
    "layout": {
      "notes_area": true
    }
  },
  "outline": {
    "deck_title": "机械基础 齿轮传动原理",
    "subject": "机械基础 齿轮传动原理",
    "slides": [
      {
        "index": 1,
        "slide_type": "cover",
        "title": "机械基础：齿轮传动原理",
        "bullets": ["授课人：_____", "时间：_____"],
        "notes": "封面信息可在前端编辑区直接改。",
        "assets": []
      },
      {
        "index": 2,
        "slide_type": "objectives",
        "title": "教学目标",
        "bullets": [
          "知识目标：掌握基本原理",
          "能力目标：应用分析",
          "素养目标：安全意识"
        ],
        "notes": "三维目标展示",
        "assets": []
      },
      {
         "index": 3,
         "slide_type": "intro",
         "title": "导入",
         "bullets": ["案例引入"],
         "notes": null,
         "assets": [{"type": "image", "theme": "scene_intro", "size": "16:9"}]
      }
    ]
  },
  "deck_content": {
    "deck_title": "机械基础 齿轮传动原理",
    "pages": [
      {
        "index": 1,
        "slide_type": "cover",
        "title": "机械基础：齿轮传动原理",
        "layout": {
          "template": "cover" 
        },
        "elements": [
          {
            "type": "text",
            "content": {
              "text": "机械基础：齿轮传动原理",
              "role": "title"
            },
            "style": {"role": "title"}
          },
          {
            "type": "text",
            "content": {
              "text": "授课人：_____\n时间：_____",
              "role": "subtitle"
            },
            "style": {"role": "subtitle"}
          }
        ],
        "speaker_notes": "封面信息。"
      },
      {
        "index": 2,
        "slide_type": "objectives",
        "title": "教学目标",
        "layout": {
          "template": "cards_3col"
        },
        "elements": [
           {
            "type": "text",
            "content": {"text": "教学目标", "role": "title"}
           },
           {
             "type": "bullets",
             "content": {
               "items": [
                 "知识目标：掌握基本原理",
                 "能力目标：应用分析",
                 "素养目标：安全意识"
               ],
               "role": "body"
             }
           }
        ],
        "speaker_notes": "三维目标展示"
      },
      {
        "index": 3,
        "slide_type": "intro",
        "title": "导入",
        "layout": {
          "template": "two-column"
        },
        "elements": [
          {
            "type": "text",
            "content": {"text": "导入：为什么要学？", "role": "title"}
          },
          {
            "type": "bullets",
            "content": {"items": ["案例引入..."], "role": "body"}
          },
          {
            "type": "image",
            "content": {
              "placeholder": true,
              "kind": "image",
              "theme": "scene_intro",
              "prompt": "汽车变速箱齿轮"
            },
            "style": {"role": "visual"}
          }
        ]
      }
    ]
  },
  "stage": "4.0_ready"
}
'''

async def main():
    print("=" * 60)
    print("🧪 测试新版全流程 JSON 直接输入模式 (Async)")
    print("=" * 60)
    try:
        data = json.loads(json_input)
        print("✅ JSON 格式验证通过")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 格式错误: {e}")
        return

    # 初始化LLM
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "qwen-plus"),
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL")
    )
    
    # 创建工作流
    # 注意：需要把 src 目录加入 pythonpath，或者在当前目录运行
    import sys
    sys.path.append(os.getcwd())
    
    from src.workflow import create_workflow
    from src.state import PPTWebState
    
    workflow = create_workflow(llm)
    app = workflow.compile()
    
    # 模拟用户输入
    user_input = {
        "topic": json_input,  # 直接传入 JSON 字符串
        "major": "机械制造",
        "target_audience": "高职学生",
        "duration": "45分钟"
    }
    
    initial_state = {
        "user_input": user_input,
        "planning": None,
        "html_code": None,
        "quality_issues": [],
        "messages": []
    }
    
    print("\n🚀 开始执行工作流 (Async)...\n")
    start_time = time.time()
    
    try:
        # 使用 ainvoke 异步调用
        final_state = await app.ainvoke(initial_state)
        execution_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("📊 运行结果")
        print("=" * 60)
        print(f"⏱️  耗时: {execution_time:.2f} 秒")
        
        planning = final_state.get('planning', {})
        
        # 验证关键字段是否存在
        print(f"🔍 检查全流程字段:")
        has_outline = 'outline' in planning
        has_deck = 'deck_content' in planning
        has_slides_root = 'slides' in planning # 兼容性检查
        
        print(f"  - outline 存在: {has_outline}")
        print(f"  - deck_content 存在: {has_deck}")
        print(f"  - slides (兼容) 存在: {has_slides_root}")
        
        if has_slides_root:
            print(f"  - 页数: {len(planning['slides'])}")
            
        if has_deck:
            print(f"  - 详情页数: {len(planning['deck_content']['pages'])}")
            
        # 保存结果
        html = final_state.get("final_html")
        if html:
            with open("output/new_json_test_result.html", "w") as f:
                f.write(html)
            print(f"\n✅ HTML Generated: output/new_json_test_result.html")
        else:
            print("\n❌ HTML Generation Failed")

    except Exception as e:
        print(f"\n❌ Execution Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

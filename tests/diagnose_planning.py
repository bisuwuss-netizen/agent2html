"""
诊断LLM生成的planning数据结构
"""
import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def main():
    from src.workflow import create_workflow
    from src.state import PPTWebState

    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL")
    )

    workflow = create_workflow(llm)
    app = workflow.compile()

    # 简单的topic输入(和批量测试一样)
    user_input = {
        "topic": "数控车床编程基础",
        "major": "机械制造",
        "target_audience": "高职学生",
        "duration": "30分钟"
    }

    initial_state: PPTWebState = {
        "user_input": user_input,
        "planning": None,
        "html_code": None,
        "quality_issues": [],
        "iteration_count": 0,
        "final_html": None,
        "status": "pending",
        "execution_time": None,
        "messages": [],
        "error": None
    }

    print("=" * 70)
    print("🔍 诊断 LLM 生成的 Planning 数据结构")
    print("=" * 70)
    print(f"输入主题: {user_input['topic']}")
    print(f"输入专业: {user_input['major']}")
    print("\n生成中(需要调用LLM)...\n")

    # 只运行到planning阶段
    final_state = app.invoke(initial_state, {"recursion_limit": 50})

    planning = final_state.get("planning")

    if not planning:
        print("❌ planning 为空!")
        return

    print("\n" + "=" * 70)
    print("📋 Planning 数据结构分析")
    print("=" * 70)

    # 1. 顶层字段
    print("\n【顶层字段】")
    for key in planning.keys():
        print(f"  ✓ {key}")

    # 2. slides数组
    slides = planning.get("slides", [])
    print(f"\n【slides 数组】共 {len(slides)} 个")

    # 3. 检查前3个slide的结构
    for i, slide in enumerate(slides[:3], 1):
        print(f"\n  --- Slide {i} ({slide.get('slide_type', 'unknown')}) ---")
        print(f"  title: {slide.get('title', '❌ 缺失')}")
        print(f"  bullets: {slide.get('bullets', '❌ 缺失')}")
        print(f"  content: {slide.get('content', '❌ 缺失')}")
        print(f"  所有字段: {list(slide.keys())}")

    # 4. pages数组(如果有)
    pages = planning.get("pages", [])
    if pages:
        print(f"\n【pages 数组】共 {len(pages)} 个")
        for i, page in enumerate(pages[:2], 1):
            print(f"\n  --- Page {i} ---")
            print(f"  title: {page.get('title', '❌ 缺失')}")
            print(f"  bullets: {page.get('bullets', '❌ 缺失')}")
    else:
        print(f"\n【pages 数组】不存在")

    # 5. 保存完整planning到JSON
    output_file = "output/planning_diagnosis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(planning, f, ensure_ascii=False, indent=2)

    print(f"\n\n✅ 完整planning已保存到: {output_file}")
    print("\n💡 建议: 打开该文件检查LLM生成的数据结构是否符合预期")

if __name__ == "__main__":
    main()

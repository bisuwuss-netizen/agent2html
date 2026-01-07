"""
测试LLM输出格式转换是否正确
"""
import os
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

    # 简单topic输入(触发LLM生成)
    user_input = {
        "topic": "Python基础语法",
        "major": "软件开发",
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
    print("🧪 测试 LLM 输出格式转换")
    print("=" * 70)
    print(f"输入: {user_input['topic']}")
    print("\n生成中(需要调用LLM,约1-2分钟)...\n")

    import time
    start = time.time()

    final_state = app.invoke(initial_state)

    elapsed = time.time() - start

    print("\n" + "=" * 70)
    print("📊 测试结果")
    print("=" * 70)
    print(f"⏱️  总耗时: {elapsed:.1f}秒")
    print(f"📄 状态: {final_state.get('status')}")

    planning = final_state.get('planning')
    if planning:
        print(f"📝 标题: {planning.get('deck_title', 'N/A')}")

        # 检查deck_content.pages是否有正确的格式
        deck_pages = planning.get('deck_content', {}).get('pages', [])
        if deck_pages:
            page2 = deck_pages[1] if len(deck_pages) > 1 else deck_pages[0]
            print(f"\n✅ deck_content.pages[1] 格式检查:")
            print(f"   - title: {page2.get('title', '❌ 缺失')}")
            print(f"   - content: {page2.get('content', '❌ 缺失')}")
            print(f"   - bullets: {page2.get('bullets', '❌ 缺失')}")

            has_content = page2.get('content') or page2.get('bullets')
            if has_content:
                print(f"\n   ✅ 格式转换成功! Generator可以读取到内容")
            else:
                print(f"\n   ❌ 格式转换失败! Generator读不到内容")

    # 检查生成的HTML
    html = final_state.get("final_html") or final_state.get("html_code")
    if html:
        # 检查HTML中是否有实际内容(不只是"标题")
        import re
        titles = re.findall(r'<h2[^>]*>([^<]+)</h2>', html)
        non_generic_titles = [t for t in titles if t != '标题' and t.strip()]

        print(f"\n📄 HTML内容检查:")
        print(f"   找到的标题数: {len(titles)}")
        print(f"   有效标题数: {len(non_generic_titles)}")
        if len(non_generic_titles) >= 3:
            print(f"   前3个标题: {non_generic_titles[:3]}")
            print(f"\n   ✅ HTML内容正常!")
        else:
            print(f"   ❌ HTML内容缺失,大多是'标题'占位符")

        # 保存HTML
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filepath = f"output/llm_format_test_{timestamp}.html"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n💾 HTML已保存: {filepath}")

if __name__ == "__main__":
    main()

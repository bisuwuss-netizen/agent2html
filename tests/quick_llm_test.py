"""
快速LLM测试 - 验证格式转换
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

    user_input = {
        "topic": "Python基础",
        "major": "计算机",
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

    print("🧪 快速测试LLM生成 + 格式转换")
    print("="*60)

    final_state = app.invoke(initial_state)

    html = final_state.get("final_html") or final_state.get("html_code")

    if html:
        # 保存HTML
        with open("output/quick_llm_test.html", "w", encoding="utf-8") as f:
            f.write(html)

        # 检查是否有实际内容
        import re
        h2_titles = re.findall(r'<h2[^>]*>(.*?)</h2>', html)
        h3_contents = re.findall(r'<h3[^>]*>(.*?)</h3>', html)

        print(f"\n✅ HTML生成成功")
        print(f"📄 文件大小: {len(html):,} 字节")
        print(f"\n📋 提取的H2标题 (前5个):")
        for i, title in enumerate(h2_titles[:5], 1):
            status = "✅" if title != "标题" else "❌"
            print(f"  {status} {i}. {title}")

        print(f"\n📋 提取的H3内容 (前3个):")
        for i, content in enumerate(h3_contents[:3], 1):
            print(f"  {i}. {content[:50]}...")

        if "标题" in h2_titles[:3]:
            print("\n❌ 发现'标题'占位符 - 格式转换可能失败!")
        else:
            print("\n✅ 内容填充正常 - 格式转换成功!")
    else:
        print("❌ HTML生成失败")

if __name__ == "__main__":
    main()

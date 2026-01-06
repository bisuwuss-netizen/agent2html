"""
快速测试 - 验证设计优化效果
"""
import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from src.workflow import create_workflow
from src.state import PPTWebState

load_dotenv()

def main():
    print("\n" + "="*70)
    print("🎨 测试优化后的设计效果")
    print("="*70)

    # 初始化 LLM
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "deepseek-chat"),
        temperature=float(os.getenv("TEMPERATURE", 0.7)),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL")
    )

    # 创建工作流
    workflow = create_workflow(llm)
    app = workflow.compile()

    # 测试用例：3D建模主题（使用蓝紫渐变配色）
    user_input = {
        "topic": "Python编程入门",
        "major": "计算机应用",
        "target_audience": "高职一年级学生",
        "duration": "45分钟",
        "key_points": ["变量与数据类型", "条件语句", "循环语句"]
    }

    print(f"\n📚 测试主题: {user_input['topic']}")
    print(f"🎯 专业: {user_input['major']}")

    # 初始化状态
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

    # 执行工作流
    print("\n🚀 开始生成 (异步模式)...\n")
    import threading
    start_time = time.time()

    def run_optimization(current_state):
        try:
            print(f"\n🔄 [Background] Agent 3 开始质量优化...")
            for event in app.stream(current_state):
                for node_name, node_state in event.items():
                    if node_name == "quality_checker":
                        html_v2 = node_state.get("final_html") or node_state.get("html_code")
                        if html_v2:
                            timestamp = time.strftime("%Y%m%d_%H%M%S")
                            filepath = f"output/html(v2)-{timestamp}.html"
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(html_v2)
                            print(f"\n✅ [Background] 优化版 V2 已生成: {filepath}")
        except Exception as e:
            print(f"\n❌ [Background] 错误: {e}")

    try:
        for event in app.stream(initial_state):
            for node_name, node_state in event.items():
                print(f"📍 节点: {node_name}")
                if node_name == "designer_generator":
                    # 保存 V1 (workflow.py 已经做了，但我们打印一下)
                    threading.Thread(target=run_optimization, args=(node_state,), daemon=True).start()
                    print("\n" + "="*70)
                    print(f"⏱️  V1 生成耗时: {time.time() - start_time:.2f}秒")
                    print(f"💡 V1 已就绪，V2 正在后台优化...")
                    print("="*70 + "\n")
                    
                    # 模拟主程序等待一会或退出
                    print("测试程序将等待 5 秒以确保后台线程启动，然后正常退出...")
                    time.sleep(5)
                    return

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()

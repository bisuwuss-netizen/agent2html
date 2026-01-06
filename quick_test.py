"""
快速测试脚本 - 使用默认参数测试系统
"""
import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from src.workflow import create_workflow
from src.state import PPTWebState

# 加载环境变量
load_dotenv()


def quick_test():
    """快速测试（使用默认参数）"""

    print("\n" + "="*70)
    print("🧪 快速测试模式 - 使用默认参数")
    print("="*70)

    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ 错误: 未找到 OPENAI_API_KEY")
        print("   请检查 .env 文件")
        return

    print(f"\n✅ API Key 已配置: {api_key[:10]}...")
    print(f"✅ Base URL: {os.getenv('OPENAI_BASE_URL', 'default')}")
    print(f"✅ Model: {os.getenv('MODEL_NAME', 'gpt-4')}")

    # 初始化 LLM
    try:
        llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-4"),
            temperature=float(os.getenv("TEMPERATURE", 0.7)),
            openai_api_key=api_key,
            openai_api_base=os.getenv("OPENAI_BASE_URL")
        )
        print("\n✅ LLM 初始化成功")
    except Exception as e:
        print(f"\n❌ LLM 初始化失败: {e}")
        return

    # 创建工作流
    try:
        workflow = create_workflow(llm)
        app = workflow.compile()
        print("✅ 工作流创建成功")
    except Exception as e:
        print(f"\n❌ 工作流创建失败: {e}")
        return

    # 默认测试参数
    user_input = {
        "topic": "机械加工-车床操作",
        "major": "机械制造",
        "target_audience": "高职二年级学生",
        "duration": "45分钟",
        "key_points": ["车床结构", "操作步骤", "安全规范"]
    }

    print("\n" + "="*70)
    print("📋 测试课程信息：")
    print(f"   主题：{user_input['topic']}")
    print(f"   专业：{user_input['major']}")
    print(f"   对象：{user_input['target_audience']}")
    print(f"   课时：{user_input['duration']}")
    print(f"   知识点：{', '.join(user_input['key_points'])}")
    print("="*70)

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
    print("\n🚀 开始执行工作流...\n")
    start_time = time.time()

    final_state = None

    try:
        for event in app.stream(initial_state):
            for node_name, node_state in event.items():
                print(f"\n{'='*70}")
                print(f"📍 节点: {node_name}")
                print(f"   状态: {node_state.get('status', 'unknown')}")

                # 显示规划信息
                if node_name == "content_planner" and node_state.get('planning'):
                    planning = node_state['planning']
                    print(f"   📄 课程标题: {planning.get('course_title', 'N/A')}")
                    print(f"   📊 页数: {planning.get('total_pages', 'N/A')}")

                # 显示生成信息
                if node_name == "designer_generator" and node_state.get('html_code'):
                    html_len = len(node_state['html_code'])
                    print(f"   📝 HTML 长度: {html_len} 字符")

                # 显示质检信息
                if node_name == "quality_checker":
                    issues = node_state.get('quality_issues', [])
                    print(f"   ⚠️  问题数: {len(issues)}")
                    if issues:
                        for i, issue in enumerate(issues[:3], 1):  # 只显示前3个
                            print(f"      {i}. {issue[:60]}...")

                print(f"{'='*70}")

                if node_state.get('error'):
                    print(f"❌ 错误: {node_state['error']}")
                    final_state = node_state
                    break

                final_state = node_state

        if not final_state:
            print("\n❌ 工作流执行失败")
            return

    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        return

    # 计算执行时间
    execution_time = time.time() - start_time

    # 输出结果
    print("\n" + "="*70)
    print("📊 测试结果")
    print("="*70)
    print(f"⏱️  总耗时: {execution_time:.2f} 秒")
    print(f"📄 规划页数: {final_state.get('planning', {}).get('total_pages', 'N/A')}")
    print(f"🔄 迭代次数: {final_state.get('iteration_count', 0)}")
    print(f"⚠️  最终问题数: {len(final_state.get('quality_issues', []))}")
    print(f"✅ 最终状态: {final_state.get('status', 'unknown')}")

    # 检查是否成功
    html_to_save = final_state.get("final_html") or final_state.get("html_code")

    if html_to_save:
        # 保存文件
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"test_{timestamp}.html"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_to_save)

        print(f"\n✅ 测试成功！")
        print(f"   📄 文件: {filepath}")
        print(f"   📏 大小: {len(html_to_save)} 字符")
        print(f"\n💡 用浏览器打开查看效果\n")

    else:
        print("\n❌ 测试失败：未生成 HTML")
        if final_state.get('error'):
            print(f"   错误: {final_state['error']}")


if __name__ == "__main__":
    quick_test()

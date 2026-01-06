"""
主程序入口（高职教育 PPT 式网页生成）
"""
import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from src.workflow import create_workflow
from src.state import PPTWebState

# 加载环境变量
load_dotenv()


def save_html(html_code: str, filename: str = None) -> str:
    """保存 HTML 到文件"""
    if not filename:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"html(v2)-{timestamp}.html"

    # 确保 output 目录存在
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_code)

    return filepath


def main():
    """主函数"""

    # 初始化 LLM
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4"),
        temperature=float(os.getenv("TEMPERATURE", 0.7)),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL")
    )

    # 创建工作流
    workflow = create_workflow(llm)
    app = workflow.compile()

    # 用户输入
    print("\n" + "="*70)
    print("🎓 高职教育 PPT 式网页生成器 (基于 LangGraph + reveal.js)")
    print("="*70)

    print("\n请输入课程信息：")

    # 1. 课程主题
    topic = input("📚 课程主题（如：机械加工-车床操作）: ").strip()
    if not topic:
        topic = "机械加工-车床操作"
        print(f"   使用默认主题: {topic}")

    # 2. 专业
    major = input("🎯 专业（如：机械制造）: ").strip()
    if not major:
        major = "机械制造"
        print(f"   使用默认专业: {major}")

    # 3. 授课对象
    target_audience = input("👥 授课对象（如：高职二年级学生）: ").strip()
    if not target_audience:
        target_audience = "高职二年级学生"
        print(f"   使用默认对象: {target_audience}")

    # 4. 课时
    duration = input("⏰ 课时（如：45分钟）: ").strip()
    if not duration:
        duration = "45分钟"
        print(f"   使用默认课时: {duration}")

    # 5. 关键知识点（可选）
    key_points_input = input("📌 关键知识点（用逗号分隔，可选）: ").strip()
    key_points = None
    if key_points_input:
        key_points = [kp.strip() for kp in key_points_input.split(',')]
        print(f"   知识点: {', '.join(key_points)}")

    # 构建用户输入
    user_input = {
        "topic": topic,
        "major": major,
        "target_audience": target_audience,
        "duration": duration
    }

    if key_points:
        user_input["key_points"] = key_points

    print("\n" + "="*70)
    print("📋 课程信息汇总：")
    print(f"   主题：{topic}")
    print(f"   专业：{major}")
    print(f"   对象：{target_audience}")
    print(f"   课时：{duration}")
    if key_points:
        print(f"   知识点：{', '.join(key_points)}")
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
    print("\n🚀 开始执行工作流 (并行模式)...\n")
    import threading
    
    start_time = time.time()
    v1_saved = False
    
    # 获取编译后的应用
    app = workflow.compile()

    def run_optimization(current_state):
        """后台优化线程"""
        try:
            print(f"\n🔄 [Background] Agent 3 开始质量优化...")
            # 从当前状态继续流式执行
            for event in app.stream(current_state):
                for node_name, node_state in event.items():
                    if node_name == "quality_checker":
                        # 检查是否有新生成的优化代码
                        html_v2 = node_state.get("final_html") or node_state.get("html_code")
                        if html_v2:
                            filepath_v2 = save_html(html_v2) # 默认生成 ppt_web_*.html
                            print(f"\n✅ [Background] 优化版 V2 已生成: {filepath_v2}")
            print(f"✨ [Background] 优化流程全部完成 (耗时: {time.time() - start_time:.2f}s)")
        except Exception as e:
            print(f"\n❌ [Background] 优化线程出错: {e}")

    final_state = initial_state
    try:
        # 主线程只运行到生成 V1
        for event in app.stream(initial_state):
            for node_name, node_state in event.items():
                print(f"📍 节点: {node_name} " + ("完成" if node_name != "quality_checker" else "跳过并转入后台"))
                
                if node_name == "designer_generator":
                    v1_saved = True
                    # 此时 workflow.py 已经保存了 V1
                    # 我们在这里启动后台线程进行后续优化
                    threading.Thread(target=run_optimization, args=(node_state,), daemon=True).start()
                    
                    # 打印 V1 成功的总结信息并退出主循环
                    execution_time = time.time() - start_time
                    print("\n" + "="*70)
                    print("📊 阶段 1 完成")
                    print("="*70)
                    print(f"⏱️  初次生成耗时: {execution_time:.2f} 秒")
                    print(f"📄 页面数量: {node_state.get('planning', {}).get('total_pages', 'N/A')}")
                    print(f"\n💡 V1 预览版已就绪。您现在可以打开浏览器查看。")
                    print(f"   Agent 3 正在后台进行深度优化，完成后将生成 V2 版本...")
                    print("="*70 + "\n")
                    
                    # 如果用户希望主程序在 V1 后立即“交卷”，我们可以在这里 return
                    # 或者是保持运行直到用户按 Ctrl+C，或者等待一小会
                    print("按 Enter 键退出 (后台优化将继续进行直到完成或关闭程序)...")
                    input()
                    return

    except Exception as e:
        print(f"\n❌ 主流程出错: {e}")
        return

    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        return

    # 计算执行时间
    execution_time = time.time() - start_time

    print("\n" + "="*70)
    print("📊 执行结果")
    print("="*70)
    print(f"⏱️  总耗时: {execution_time:.2f} 秒")
    print(f"📄 规划页数: {final_state.get('planning', {}).get('total_pages', 'N/A')}")
    print(f"🔄 迭代次数: {final_state.get('iteration_count', 0)}")
    print(f"⚠️  问题数量: {len(final_state.get('quality_issues', []))}")

    if final_state.get('quality_issues'):
        print("\n问题列表：")
        for i, issue in enumerate(final_state['quality_issues'], 1):
            print(f"   {i}. {issue}")

    # 检查是否有错误
    if final_state.get("error"):
        print(f"\n❌ 生成失败: {final_state['error']}")
        return

    # 保存输出
    html_to_save = final_state.get("final_html") or final_state.get("html_code")

    if html_to_save:
        try:
            filepath = save_html(html_to_save)
            print("\n✅ 文件已生成！")
            print(f"   📄 文件路径: {filepath}")
            print(f"   📏 文件大小: {len(html_to_save)} 字符")
            print(f"\n💡 使用方法:")
            print(f"   1. 用浏览器打开: {filepath}")
            print(f"   2. 按 F11 进入全屏模式")
            print(f"   3. 使用 ← → 键或空格键翻页")
            print(f"   4. 按 Esc 退出全屏\n")

        except Exception as e:
            print(f"\n❌ 保存文件失败: {e}")
    else:
        print("\n❌ 未能生成 HTML 代码")


if __name__ == "__main__":
    main()

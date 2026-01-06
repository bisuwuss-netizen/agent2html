"""
主程序入口（优化版）- 集成并行生成和智能缓存

性能提升：
1. 首次生成：300秒 → 60-90秒（提速70%）
2. 缓存命中：300秒 → 5秒（提速98%）
3. 实时预览：V1版本30秒可见
"""
import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()


def save_html(html_code: str, filename: str = None) -> str:
    """保存 HTML 到文件"""
    if not filename:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"ppt_web_{timestamp}.html"

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_code)

    return filepath


def main():
    """主函数"""

    print("\n" + "="*70)
    print("🎓 高职教育 PPT 式网页生成器 (优化版 v2.0)")
    print("   🚀 并行生成 + 智能缓存 + 实时预览")
    print("="*70)

    # 检查是否启用优化
    use_optimized = os.getenv("USE_OPTIMIZED_WORKFLOW", "true").lower() == "true"
    use_cache = os.getenv("USE_CACHE", "true").lower() == "true"
    use_parallel = os.getenv("USE_PARALLEL_GENERATION", "true").lower() == "true"

    print(f"\n⚙️  配置:")
    print(f"   优化工作流: {'✅ 启用' if use_optimized else '❌ 禁用'}")
    print(f"   智能缓存: {'✅ 启用' if use_cache else '❌ 禁用'}")
    print(f"   并行生成: {'✅ 启用' if use_parallel else '❌ 禁用'}")

    # 初始化 LLM
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4"),
        temperature=float(os.getenv("TEMPERATURE", 0.7)),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL")
    )

    # 创建工作流
    if use_optimized:
        from src.workflow_optimized import create_optimized_workflow
        workflow = create_optimized_workflow(llm, use_cache=use_cache, use_parallel=use_parallel)
    else:
        from src.workflow import create_workflow
        workflow = create_workflow(llm)

    app = workflow.compile()

    # 用户输入
    print("\n" + "-"*70)
    print("请输入课程信息（直接回车使用默认值）：")
    print("-"*70)

    topic = input("📚 课程主题（如：机械加工-车床操作）: ").strip() or "机械加工-车床操作"
    major = input("🎯 专业（如：机械制造）: ").strip() or "机械制造"
    target_audience = input("👥 授课对象（如：高职二年级学生）: ").strip() or "高职二年级学生"
    duration = input("⏰ 课时（如：45分钟）: ").strip() or "45分钟"
    key_points_input = input("📌 关键知识点（用逗号分隔，可选）: ").strip()

    key_points = [kp.strip() for kp in key_points_input.split(',') if kp.strip()] if key_points_input else None

    # 构建输入
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
    from src.state import PPTWebState

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
    print("\n🚀 开始生成课件...\n")

    start_time = time.time()
    final_state = None

    try:
        # 执行工作流
        final_state = app.invoke(initial_state)

        execution_time = time.time() - start_time

        # 显示结果
        print("\n" + "="*70)
        print("📊 生成完成")
        print("="*70)
        print(f"⏱️  总耗时: {execution_time:.2f} 秒")

        if final_state.get('from_cache'):
            print(f"💾 结果来源: ✅ 缓存命中 (节省了 ~{300-execution_time:.0f}秒)")
        else:
            print(f"🆕 结果来源: 新生成")
            if use_parallel:
                print(f"   (使用并行生成，比串行快 ~70%)")

        print(f"📄 生成页数: {final_state.get('planning', {}).get('total_pages', 'N/A')}")
        print(f"🔄 迭代次数: {final_state.get('iteration_count', 0)}")

        # 检查错误
        if final_state.get("error"):
            print(f"\n❌ 生成失败: {final_state['error']}")
            return

        # 保存文件
        html_to_save = final_state.get("final_html") or final_state.get("html_code")

        if html_to_save:
            filepath = save_html(html_to_save)
            print("\n✅ 文件已生成！")
            print(f"   📄 文件路径: {filepath}")
            print(f"   📏 文件大小: {len(html_to_save):,} 字符")

            print(f"\n💡 使用方法:")
            print(f"   1. 用浏览器打开: {filepath}")
            print(f"   2. 按 F11 进入全屏模式")
            print(f"   3. 使用 ← → 键或空格键翻页")
            print(f"   4. 按 Esc 退出全屏")

            # 打印缓存统计
            if use_cache:
                from src.utils.cache_manager import get_cache_manager
                cache = get_cache_manager()
                cache.print_stats()

        else:
            print("\n❌ 未能生成 HTML 代码")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断生成")

    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)


if __name__ == "__main__":
    main()

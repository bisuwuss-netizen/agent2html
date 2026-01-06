"""
测试新的页面生成系统
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
    print("🎓 测试新页面生成系统")
    print("="*70)

    # 初始化 LLM
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4"),
        temperature=float(os.getenv("TEMPERATURE", 0.7)),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL")
    )

    # 创建优化版工作流
    from src.workflow_optimized import create_optimized_workflow
    workflow = create_optimized_workflow(llm)
    app = workflow.compile()

    # 用户输入（硬编码测试数据）
    user_input = {
        "topic": "机械加工-车床操作",
        "major": "机械制造",
        "target_audience": "高职二年级学生",
        "duration": "45分钟"
    }

    print("\n📋 课程信息：")
    print(f"   主题：{user_input['topic']}")
    print(f"   专业：{user_input['major']}")
    print(f"   对象：{user_input['target_audience']}")
    print(f"   课时：{user_input['duration']}")
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

    try:
        # 执行优化版工作流
        final_state = app.invoke(initial_state)
        execution_time = time.time() - start_time

        # 显示结果
        print("\n" + "="*70)
        print("📊 生成完成")
        print("="*70)
        print(f"⏱️  总耗时: {execution_time:.2f} 秒")

        if final_state.get('from_cache'):
            print(f"💾 结果来源: ✅ 缓存命中")
        else:
            print(f"🆕 结果来源: 新生成")

        # 检查 planning 中的图片分配
        planning = final_state.get('planning', {})
        pages = planning.get('pages', [])
        total_pages = len(pages)
        pages_with_images = sum(1 for p in pages if p.get('image_description') and p.get('image_description') != 'null')

        print(f"📄 总页数: {total_pages}")
        print(f"🖼️  有图页面: {pages_with_images}")
        print(f"📝 纯文字页面: {total_pages - pages_with_images}")
        print(f"📊 图片占比: {pages_with_images/total_pages*100:.1f}%")

        # 保存文件
        html_to_save = final_state.get("final_html") or final_state.get("html_code")
        if html_to_save:
            filepath = save_html(html_to_save)
            print(f"\n✅ 文件已生成: {filepath}")

            # 检查生成的HTML中的图片数量
            img_count = html_to_save.count('data-image-slot=')
            print(f"🖼️  HTML中的图片插槽数量: {img_count}")

    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "="*70)


if __name__ == "__main__":
    main()

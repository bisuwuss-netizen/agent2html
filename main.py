"""
主程序入口
高职教育PPT式网页生成器 v3.0

特性：
- 19种专业布局模板
- 21套主题配色
- 热插拔图片插槽
- 智能布局选择
"""
import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def save_html(html_code: str, filename: str = None) -> str:
    """保存HTML到文件"""
    if not filename:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"ppt_{timestamp}.html"
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_code)
    
    return filepath


def main():
    """主函数"""
    
    print("\n" + "="*70)
    print("🎓 高职教育 PPT 式网页生成器 v3.0")
    print("   📐 19种布局 | 🎨 21套配色 | 🔌 热插拔图片")
    print("="*70)
    
    # 初始化LLM
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4"),
        temperature=float(os.getenv("TEMPERATURE", 0.7)),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL")
    )
    
    # 创建工作流
    from src.workflow import create_workflow
    workflow = create_workflow(llm)
    app = workflow.compile()
    
    # 用户输入
    print("\n" + "-"*70)
    print("请输入课程信息（直接回车使用默认值）：")
    print("-"*70)
    
    topic = input("📚 课程主题: ").strip() or "机械加工-车床操作"
    major = input("🎯 专业: ").strip() or "机械制造"
    target = input("👥 授课对象: ").strip() or "高职二年级学生"
    duration = input("⏰ 课时: ").strip() or "45分钟"
    
    key_points_input = input("📌 关键知识点（逗号分隔，可选）: ").strip()
    key_points = [kp.strip() for kp in key_points_input.split(',')] if key_points_input else None
    
    # 构建输入
    user_input = {
        "topic": topic,
        "major": major,
        "target_audience": target,
        "duration": duration
    }
    if key_points:
        user_input["key_points"] = key_points
    
    print("\n" + "="*70)
    print("📋 课程信息：")
    print(f"   主题：{topic}")
    print(f"   专业：{major}")
    print(f"   对象：{target}")
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
    
    # 执行
    print("\n🚀 开始生成...\n")
    start_time = time.time()
    
    try:
        final_state = app.invoke(initial_state)
        execution_time = time.time() - start_time
        
        print("\n" + "="*70)
        print("📊 生成完成")
        print("="*70)
        print(f"⏱️  耗时: {execution_time:.2f} 秒")
        print(f"📄 页数: {final_state.get('planning', {}).get('total_pages', 'N/A')}")
        
        # 保存
        html = final_state.get("final_html") or final_state.get("html_code")
        if html:
            filepath = save_html(html)
            print(f"\n✅ 已保存: {filepath}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
        return
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 使用说明
    print(f"\n💡 使用方法:")
    print(f"   1. 用浏览器打开生成的HTML文件")
    print(f"   2. 按 F 进入全屏")
    print(f"   3. 使用 ← → 或点击翻页")
    print(f"   4. 调用 window.fillImageSlot(slotId, url) 填充图片\n")
    print("="*70)


if __name__ == "__main__":
    main()

"""
测试脚本 - 运行完整生成流程
"""
import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def main():
    print("=" * 60)
    print("🧪 测试 agent2html 完整流程")
    print("=" * 60)
    
    # 初始化LLM
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4"),
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL")
    )
    
    # 创建工作流
    from src.workflow import create_workflow
    from src.state import PPTWebState
    
    workflow = create_workflow(llm)
    app = workflow.compile()
    
    # 测试输入
    user_input = {
        "topic": "森林环境指标监测",
        "major": "林业",
        "target_audience": "高职二年级学生",
        "duration": "45分钟",
        "key_points": ["森林温度监测", "湿度传感器", "数据采集方法"]
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
    
    print(f"\n📚 测试主题: {user_input['topic']}")
    print(f"🎯 专业: {user_input['major']}")
    print(f"📌 知识点: {', '.join(user_input['key_points'])}")
    print("\n🚀 开始生成...\n")
    
    start_time = time.time()
    
    try:
        final_state = app.invoke(initial_state)
        execution_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("📊 测试结果")
        print("=" * 60)
        print(f"⏱️  耗时: {execution_time:.2f} 秒")
        print(f"📄 状态: {final_state.get('status')}")
        
        if final_state.get('error'):
            print(f"❌ 错误: {final_state['error']}")
            return
        
        planning = final_state.get('planning', {})
        print(f"📝 标题: {planning.get('deck_title', 'N/A')}")
        print(f"📄 页数: {planning.get('total_pages', len(planning.get('pages', [])))}")
        
        # 保存HTML
        html = final_state.get("final_html") or final_state.get("html_code")
        if html:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = f"output/test_{timestamp}.html"
            os.makedirs("output", exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"\n✅ HTML已保存: {filepath}")
            print(f"📏 文件大小: {len(html):,} 字节")
        else:
            print("\n⚠️ 未生成HTML")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

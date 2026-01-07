"""
测试 JSON 直接输入模式
"""
import os
import time
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# 你提供的完整 JSON 数据
json_input = '''
{
  "deck_title": "齿轮传动原理：齿轮传动的基本定义和功能、齿轮传动的工作原理、传动比的概念与计算、齿轮的类型及特点、简单应用场景介绍",
  "subject": "齿轮传动原理",
  "knowledge_points": [
    "齿轮传动的基本定义和功能",
    "齿轮传动的工作原理",
    "传动比的概念与计算",
    "齿轮的类型及特点",
    "简单应用场景介绍"
  ],
  "teaching_scene": "theory",
  "slides": [
    {
      "index": 1,
      "slide_type": "cover",
      "title": "齿轮传动原理课程封面",
      "bullets": ["授课教师：_____", "课程时间：_____", "教学场景：理论教学"],
      "notes": "封面信息可在前端编辑区直接改。",
      "interactions": [],
      "assets": []
    },
    {
      "index": 2,
      "slide_type": "objectives",
      "title": "教学目标",
      "bullets": [
        "知识目标：掌握齿轮传动的定义、工作原理和传动比计算方法",
        "能力目标：能识别常见齿轮类型并分析简单应用场景",
        "素养目标：培养安全操作意识和团队协作精神"
      ],
      "notes": "可根据班级学情进一步细化。",
      "interactions": [],
      "assets": []
    },
    {
      "index": 3,
      "slide_type": "intro",
      "title": "导入：齿轮传动的实际应用",
      "bullets": [
        "以机械制造或汽车工程中的真实案例引入",
        "明确本节课学习目标：理解齿轮传动基本原理",
        "建立与后续课程如传动系统设计的联系"
      ],
      "notes": null,
      "interactions": [],
      "assets": [{"type": "image", "theme": "scene_intro", "size": "16:9"}]
    },
    {
      "index": 4,
      "slide_type": "concept",
      "title": "核心概念：齿轮传动的基本定义与功能",
      "bullets": [
        "定义：齿轮传动是通过齿轮啮合传递动力和运动的机械传动方式",
        "组成：包括齿轮、轴、轴承等核心部件",
        "功能：实现速度变换、扭矩传递和运动方向改变"
      ],
      "notes": null,
      "interactions": [],
      "assets": [{"type": "diagram", "theme": "齿轮传动定义示意图", "size": "4:3"}]
    },
    {
      "index": 5,
      "slide_type": "keypoints",
      "title": "要点解析：齿轮传动的特性",
      "bullets": [
        "高效性：传动效率高，能量损失小",
        "精确性：传动比恒定，运动控制精确",
        "可靠性：结构简单，运行稳定可靠",
        "广泛性：应用于各种机械系统"
      ],
      "notes": null,
      "interactions": [],
      "assets": []
    },
    {
      "index": 6,
      "slide_type": "summary",
      "title": "课程总结",
      "bullets": [
        "齿轮传动是机械传动的核心方式",
        "传动比决定速度与扭矩特性",
        "不同齿轮类型适用不同场景",
        "课后思考：变速箱如何实现换挡？"
      ],
      "notes": null,
      "interactions": [],
      "assets": []
    }
  ]
}
'''

def main():
    print("=" * 60)
    print("🧪 测试 JSON 直接输入模式")
    print("=" * 60)
    
    # 初始化LLM（虽然 JSON 模式不需要，但 workflow 需要）
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
    
    # 使用 JSON 作为 topic 输入
    user_input = {
        "topic": json_input,  # 直接传入 JSON 字符串
        "major": "机械制造",
        "target_audience": "高职二年级学生",
        "duration": "45分钟"
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
    
    print(f"\n📚 输入类型: JSON 规划数据")
    print(f"📄 包含 slides 数: {len(json.loads(json_input)['slides'])}")
    print("\n🚀 开始生成（应跳过 LLM 调用）...\n")
    
    start_time = time.time()
    
    try:
        final_state = app.invoke(initial_state)
        execution_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("📊 测试结果")
        print("=" * 60)
        print(f"⏱️  耗时: {execution_time:.2f} 秒（应该很快，因为跳过了 LLM）")
        print(f"📄 状态: {final_state.get('status')}")
        
        planning = final_state.get('planning', {})
        print(f"📝 标题: {planning.get('deck_title', 'N/A')}")
        print(f"🎯 主题: {planning.get('subject', 'N/A')}")
        print(f"📄 页数: {len(planning.get('pages', []))}")
        
        # 保存HTML
        html = final_state.get("final_html") or final_state.get("html_code")
        if html:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = f"output/json_test_{timestamp}.html"
            os.makedirs("output", exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"\n✅ HTML已保存: {filepath}")
            print(f"📏 文件大小: {len(html):,} 字节")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

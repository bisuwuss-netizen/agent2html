"""
批量测试脚本 - 生成6个学科类别的PPT
"""
import os
import sys
import time
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.workflow import create_workflow
from src.state import PPTWebState
from src.agents.layouts import _determine_subject_category

# 6个学科类别的测试用例
TEST_CASES = [
    {
        "major": "护理学",
        "topic": "静脉输液操作规范",
        "category": "medical"
    },
    {
        "major": "机械制造",
        "topic": "数控车床编程基础",
        "category": "engineering"
    },
    {
        "major": "视觉设计",
        "topic": "平面设计构图原则",
        "category": "arts"
    },
    {
        "major": "电子商务",
        "topic": "直播带货运营策略",
        "category": "business"
    },
    {
        "major": "园林技术",
        "topic": "城市绿化植物配置",
        "category": "nature"
    },
    {
        "major": "应用数学",
        "topic": "概率统计在工程中的应用",
        "category": "science"
    }
]


def save_html(html_code: str, category: str, topic: str) -> str:
    """保存HTML到文件，使用学科类别-主题-时间戳格式"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    # 清理主题名称，移除特殊字符
    safe_topic = topic.replace("-", "_").replace(" ", "_")[:20]
    filename = f"{category}-{safe_topic}-{timestamp}.html"
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_code)
    
    return filepath


def run_single_test(llm, app, test_case: dict) -> dict:
    """运行单个测试用例"""
    major = test_case["major"]
    topic = test_case["topic"]
    category = test_case["category"]
    
    print(f"\n{'='*60}")
    print(f"🎯 测试 [{category.upper()}] - {major}")
    print(f"   主题: {topic}")
    print('='*60)
    
    # 验证学科分类
    detected = _determine_subject_category(major)
    print(f"   检测到学科类别: {detected.value}")
    
    user_input = {
        "topic": topic,
        "major": major,
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
    
    start_time = time.time()
    
    try:
        final_state = app.invoke(initial_state)
        execution_time = time.time() - start_time
        
        html = final_state.get("final_html") or final_state.get("html_code")
        if html:
            filepath = save_html(html, category, topic)
            print(f"   ✅ 生成成功！耗时: {execution_time:.1f}s")
            print(f"   📄 保存至: {filepath}")
            return {
                "category": category,
                "major": major,
                "topic": topic,
                "filepath": filepath,
                "time": execution_time,
                "success": True
            }
        else:
            print(f"   ❌ 生成失败：无HTML输出")
            return {"category": category, "success": False, "error": "No HTML output"}
            
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return {"category": category, "success": False, "error": str(e)}


def main():
    """主函数"""
    print("\n" + "="*70)
    print("🧪 批量测试 - 6个学科类别PPT生成")
    print("="*70)
    
    # 初始化LLM
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4"),
        temperature=float(os.getenv("TEMPERATURE", 0.7)),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL")
    )
    
    # 创建工作流
    workflow = create_workflow(llm)
    app = workflow.compile()
    
    # 运行所有测试
    results = []
    total_start = time.time()
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] 开始测试...")
        result = run_single_test(llm, app, test_case)
        results.append(result)
        
        # 短暂等待，避免API限流
        if i < len(TEST_CASES):
            print("   ⏳ 等待3秒...")
            time.sleep(3)
    
    # 汇总结果
    total_time = time.time() - total_start
    success_count = sum(1 for r in results if r.get("success"))
    
    print("\n" + "="*70)
    print("📊 测试汇总")
    print("="*70)
    print(f"总测试数: {len(TEST_CASES)}")
    print(f"成功: {success_count} | 失败: {len(TEST_CASES) - success_count}")
    print(f"总耗时: {total_time:.1f}秒")
    
    print("\n生成的文件:")
    for r in results:
        if r.get("success"):
            print(f"  ✅ [{r['category']}] {r['filepath']}")
        else:
            print(f"  ❌ [{r['category']}] 失败: {r.get('error', '未知错误')}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()

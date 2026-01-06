"""
测试脚本 - 测试不同场景
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from src.workflow import create_workflow
from src.state import WebGenState
from src.utils import save_output

load_dotenv()

# 测试用例
TEST_CASES = [
    {
        "name": "个人作品集",
        "input": "创建一个前端工程师的个人作品集,包含项目展示、技能标签云、博客列表,风格要简洁现代"
    },
    {
        "name": "产品落地页",
        "input": "为一个AI写作工具生成产品落地页,要突出核心功能、用户评价、价格方案,风格要专业商务"
    },
    {
        "name": "企业官网",
        "input": "生成一个科技公司的官网首页,包含公司简介、核心业务、团队介绍、联系方式,风格要高端大气"
    }
]


def run_test(test_case: dict, llm: ChatOpenAI):
    """运行单个测试用例"""
    print(f"\n{'='*70}")
    print(f"🧪 测试: {test_case['name']}")
    print(f"{'='*70}")
    print(f"需求: {test_case['input']}\n")
    
    workflow = create_workflow(llm)
    app = workflow.compile()
    
    initial_state: WebGenState = {
        "user_input": test_case["input"],
        "plan": None,
        "design_spec": None,
        "content_data": None,
        "html": None,
        "css": None,
        "cache_key": None,
        "execution_time": None,
        "messages": [],
        "error": None
    }
    
    # 执行
    result = None
    for event in app.stream(initial_state):
        for node_name, node_state in event.items():
            if node_name == "generator":
                result = node_state
    
    if result and result.get("html") and result.get("css"):
        files = save_output(
            result["html"],
            result["css"],
            output_dir=f"./output/test_{test_case['name'].replace(' ', '_')}"
        )
        print(f"✅ 测试通过 - 文件: {files['combined_file']}")
        return True
    else:
        print(f"❌ 测试失败")
        return False


def main():
    """运行所有测试"""
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4"),
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL")
    )
    
    results = []
    for test_case in TEST_CASES:
        success = run_test(test_case, llm)
        results.append((test_case["name"], success))
    
    # 打印测试总结
    print(f"\n{'='*70}")
    print("📊 测试总结")
    print(f"{'='*70}")
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
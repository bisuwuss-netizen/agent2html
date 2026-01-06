"""
性能基准测试工具
用于测试和对比优化前后的性能
"""
import time
import json
import os
from datetime import datetime
from typing import Dict, List

# 测试用例
TEST_CASES = [
    {
        "name": "车床操作基础（8页）",
        "input": {
            "topic": "机械加工-车床操作",
            "major": "机械制造",
            "target_audience": "高职二年级学生",
            "duration": "45分钟",
            "key_points": ["车床结构", "操作步骤", "安全规范"]
        },
        "expected_pages": 8,
        "target_time": 90
    },
    {
        "name": "3D建模入门（10页）",
        "input": {
            "topic": "3D建模基础",
            "major": "3D设计",
            "target_audience": "高职一年级学生",
            "duration": "45分钟",
            "key_points": ["建模工具", "基本操作", "案例实践"]
        },
        "expected_pages": 10,
        "target_time": 110
    },
    {
        "name": "烹饪刀工（6页）",
        "input": {
            "topic": "烹饪基础刀工",
            "major": "烹饪",
            "target_audience": "高职一年级学生",
            "duration": "30分钟",
            "key_points": ["刀具选择", "切法技巧", "安全要点"]
        },
        "expected_pages": 6,
        "target_time": 70
    }
]


class PerformanceBenchmark:
    """性能基准测试类"""

    def __init__(self):
        self.results = []
        self.results_dir = "performance_results"
        os.makedirs(self.results_dir, exist_ok=True)

    def run_single_test(self, test_case: Dict) -> Dict:
        """运行单个测试用例"""
        print(f"\n{'='*60}")
        print(f"测试: {test_case['name']}")
        print(f"{'='*60}\n")

        from main import main
        from src.state import PPTWebState

        # 记录开始时间
        start_time = time.time()

        # 执行生成
        try:
            state = {
                "user_input": test_case['input'],
                "planning": None,
                "html_code": None,
                "quality_issues": [],
                "iteration_count": 0,
                "final_html": None,
                "status": "initialized",
                "messages": [],
                "error": None
            }

            # 调用工作流（模拟main.py的执行）
            from dotenv import load_dotenv
            load_dotenv()

            from langchain_openai import ChatOpenAI
            from src.workflow import create_workflow

            llm = ChatOpenAI(model="deepseek-chat", temperature=0.7)
            workflow = create_workflow(llm)
            app = workflow.compile()

            # 执行
            result = app.invoke(state)

            end_time = time.time()
            total_time = end_time - start_time

            # 检查是否成功
            success = result.get('status') == 'completed' and result.get('final_html') is not None

            # 统计token消耗（如果有）
            token_count = self._estimate_tokens(result.get('final_html', ''))

            result_data = {
                "test_name": test_case['name'],
                "success": success,
                "total_time": round(total_time, 2),
                "target_time": test_case['target_time'],
                "pages_generated": len(result.get('planning', {}).get('pages', [])) if result.get('planning') else 0,
                "expected_pages": test_case['expected_pages'],
                "token_count": token_count,
                "iteration_count": result.get('iteration_count', 0),
                "timestamp": datetime.now().isoformat()
            }

            # 打印结果
            self._print_result(result_data)

            return result_data

        except Exception as e:
            end_time = time.time()
            total_time = end_time - start_time

            result_data = {
                "test_name": test_case['name'],
                "success": False,
                "total_time": round(total_time, 2),
                "target_time": test_case['target_time'],
                "pages_generated": 0,
                "expected_pages": test_case['expected_pages'],
                "token_count": 0,
                "iteration_count": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

            print(f"❌ 测试失败: {e}")
            return result_data

    def _estimate_tokens(self, text: str) -> int:
        """估算token数量（简单估算：1 token ≈ 0.75 汉字）"""
        if not text:
            return 0
        # 英文单词数 + 中文字符数/0.75
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 0.75 + other_chars / 4)

    def _print_result(self, result: Dict):
        """打印单个测试结果"""
        print(f"\n📊 测试结果:")
        print(f"  状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
        print(f"  总耗时: {result['total_time']}秒 (目标: {result['target_time']}秒)")

        if result['total_time'] <= result['target_time']:
            print(f"  性能: ✅ 达标 ({result['target_time'] - result['total_time']:.1f}秒余量)")
        else:
            print(f"  性能: ❌ 超时 (超时 {result['total_time'] - result['target_time']:.1f}秒)")

        print(f"  生成页数: {result['pages_generated']} (预期: {result['expected_pages']})")
        print(f"  Token消耗: ~{result['token_count']}")
        print(f"  迭代次数: {result['iteration_count']}")

        if result.get('error'):
            print(f"  错误信息: {result['error']}")

    def run_all_tests(self) -> List[Dict]:
        """运行所有测试用例"""
        print("\n" + "="*60)
        print("  性能基准测试 - 开始")
        print("="*60)

        for test_case in TEST_CASES:
            result = self.run_single_test(test_case)
            self.results.append(result)

        # 保存结果
        self.save_results()

        # 打印总结
        self.print_summary()

        return self.results

    def save_results(self):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.results_dir, f"benchmark_{timestamp}.json")

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n📁 结果已保存: {filename}")

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("  测试总结")
        print("="*60)

        total_tests = len(self.results)
        success_tests = sum(1 for r in self.results if r['success'])
        total_time = sum(r['total_time'] for r in self.results)
        avg_time = total_time / total_tests if total_tests > 0 else 0

        print(f"\n总测试数: {total_tests}")
        print(f"成功: {success_tests} ({success_tests/total_tests*100:.1f}%)")
        print(f"失败: {total_tests - success_tests}")
        print(f"总耗时: {total_time:.1f}秒")
        print(f"平均耗时: {avg_time:.1f}秒")

        # 性能达标率
        on_target = sum(1 for r in self.results if r['total_time'] <= r['target_time'])
        print(f"\n性能达标: {on_target}/{total_tests} ({on_target/total_tests*100:.1f}%)")

        # 各项指标
        print(f"\n详细指标:")
        for result in self.results:
            status_icon = "✅" if result['success'] and result['total_time'] <= result['target_time'] else "❌"
            print(f"  {status_icon} {result['test_name']}: {result['total_time']}秒 / {result['target_time']}秒")

    def compare_with_baseline(self, baseline_file: str):
        """对比当前结果与基准结果"""
        if not os.path.exists(baseline_file):
            print(f"❌ 基准文件不存在: {baseline_file}")
            return

        with open(baseline_file, 'r', encoding='utf-8') as f:
            baseline = json.load(f)

        print("\n" + "="*60)
        print("  性能对比（优化后 vs 基准）")
        print("="*60)

        baseline_results = {r['test_name']: r for r in baseline['results']}

        for current in self.results:
            name = current['test_name']
            if name not in baseline_results:
                continue

            baseline_result = baseline_results[name]

            print(f"\n{name}:")
            print(f"  基准耗时: {baseline_result['total_time']}秒")
            print(f"  当前耗时: {current['total_time']}秒")

            improvement = (baseline_result['total_time'] - current['total_time']) / baseline_result['total_time'] * 100
            if improvement > 0:
                print(f"  改进: ✅ 提速 {improvement:.1f}%")
            else:
                print(f"  改进: ❌ 慢了 {abs(improvement):.1f}%")


if __name__ == "__main__":
    import sys

    benchmark = PerformanceBenchmark()

    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        # 对比模式
        if len(sys.argv) > 2:
            baseline_file = sys.argv[2]
        else:
            # 查找最新的基准文件
            import glob
            baseline_files = sorted(glob.glob("performance_results/benchmark_*.json"))
            if not baseline_files:
                print("❌ 找不到基准文件")
                sys.exit(1)
            baseline_file = baseline_files[-1]
            print(f"📊 使用基准文件: {baseline_file}")

        benchmark.run_all_tests()
        benchmark.compare_with_baseline(baseline_file)
    else:
        # 正常测试模式
        benchmark.run_all_tests()

        print("\n" + "="*60)
        print("  下次运行时可以使用 --compare 参数对比结果")
        print(f"  示例: python3 performance_benchmark.py --compare")
        print("="*60)

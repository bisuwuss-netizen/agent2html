"""
进度追踪模块
提供实时进度反馈和耗时统计
"""
import time
import sys
from typing import Optional, Callable


class ProgressTracker:
    """
    生成进度追踪器

    Example:
        progress = ProgressTracker(8, "生成页面")
        for i in range(8):
            do_work()
            progress.update(message=f"页面 {i+1} 完成")
        progress.complete()
    """

    def __init__(
        self,
        total_steps: int,
        description: str = "生成中",
        bar_width: int = 30,
        show_eta: bool = True
    ):
        """
        初始化进度追踪器

        Args:
            total_steps: 总步数
            description: 进度描述
            bar_width: 进度条宽度
            show_eta: 是否显示预计剩余时间
        """
        self.total = total_steps
        self.current = 0
        self.description = description
        self.bar_width = bar_width
        self.show_eta = show_eta
        self.start_time = time.time()
        self.step_times: list = []

    def update(self, step: int = None, message: str = None):
        """
        更新进度

        Args:
            step: 当前步数（None 则自动 +1）
            message: 状态消息
        """
        if step is not None:
            self.current = step
        else:
            self.current += 1

        # 记录步骤耗时
        self.step_times.append(time.time())

        elapsed = time.time() - self.start_time

        # 计算预计剩余时间
        if self.current > 0 and self.show_eta:
            avg_time = elapsed / self.current
            remaining = avg_time * (self.total - self.current)
            eta_str = f"剩余 {remaining:.1f}s"
        else:
            eta_str = ""

        # 进度条
        progress = self.current / self.total
        filled = int(self.bar_width * progress)
        bar = "█" * filled + "░" * (self.bar_width - filled)

        # 百分比
        percent = progress * 100

        # 输出
        status = message or self.description
        output = f"\r📊 [{bar}] {percent:5.1f}% | {self.current}/{self.total} | 已用 {elapsed:.1f}s"
        if eta_str:
            output += f" | {eta_str}"
        output += f" | {status}"

        # 清除行尾并输出
        sys.stdout.write(output + " " * 10)
        sys.stdout.flush()

        if self.current == self.total:
            sys.stdout.write("\n")
            sys.stdout.flush()

    def complete(self, message: str = "完成"):
        """标记完成"""
        self.current = self.total
        elapsed = time.time() - self.start_time
        avg_time = elapsed / self.total if self.total > 0 else 0
        sys.stdout.write(
            f"\r✅ {self.description} {message} | "
            f"总耗时 {elapsed:.2f}s | "
            f"平均 {avg_time:.2f}s/步\n"
        )
        sys.stdout.flush()

    def get_stats(self) -> dict:
        """获取统计信息"""
        elapsed = time.time() - self.start_time
        return {
            "total_steps": self.total,
            "completed_steps": self.current,
            "elapsed_time": elapsed,
            "avg_time_per_step": elapsed / self.current if self.current > 0 else 0,
            "progress_percent": (self.current / self.total * 100) if self.total > 0 else 0
        }


class ProgressContext:
    """
    进度上下文管理器

    Example:
        with ProgressContext(8, "生成页面") as progress:
            for i, page in enumerate(pages):
                generate_page(page)
                progress.update(i + 1, f"页面 {i+1}")
    """

    def __init__(self, total: int, description: str = "处理中"):
        self.tracker = ProgressTracker(total, description)

    def __enter__(self) -> ProgressTracker:
        return self.tracker

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.tracker.complete()
        else:
            elapsed = time.time() - self.tracker.start_time
            sys.stdout.write(
                f"\r❌ {self.tracker.description} 失败 | "
                f"已完成 {self.tracker.current}/{self.tracker.total} | "
                f"耗时 {elapsed:.2f}s\n"
            )
            sys.stdout.flush()
        return False

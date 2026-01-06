"""
日志模块
提供统一的日志配置和格式化
"""
import logging
import os
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str = "agent2html",
    level: str = None,
    log_file: str = None,
    enable_console: bool = True
) -> logging.Logger:
    """
    配置项目日志器

    Args:
        name: 日志器名称
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
        log_file: 日志文件路径（可选）
        enable_console: 是否启用控制台输出

    Returns:
        配置好的日志器

    Example:
        logger = setup_logger("agent2html", level="DEBUG", log_file="app.log")
        logger.info("启动应用")
    """
    level = level or os.getenv("LOG_LEVEL", "INFO")
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper()))

    # 控制台 Handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

    # 文件 Handler（可选）
    if log_file:
        os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


# 全局日志器实例
logger = setup_logger()


class LogContext:
    """
    日志上下文管理器，用于记录操作耗时

    Example:
        with LogContext("内容规划"):
            do_planning()
        # 输出: ✅ 内容规划 完成 (耗时 2.34s)
    """

    def __init__(self, operation: str, log_level: int = logging.INFO):
        self.operation = operation
        self.log_level = log_level
        self.start_time: float = 0

    def __enter__(self):
        import time
        self.start_time = time.time()
        logger.log(self.log_level, f"⏳ {self.operation} 开始...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        elapsed = time.time() - self.start_time
        if exc_type is None:
            logger.log(self.log_level, f"✅ {self.operation} 完成 (耗时 {elapsed:.2f}s)")
        else:
            logger.error(f"❌ {self.operation} 失败 (耗时 {elapsed:.2f}s): {exc_val}")
        return False

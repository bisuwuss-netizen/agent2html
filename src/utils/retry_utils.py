"""
重试工具模块
提供 LLM 调用重试机制和指数退避策略
"""
import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    指数退避重试装饰器

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟（秒）
        max_delay: 最大延迟（秒）
        exceptions: 需要重试的异常类型

    Example:
        @retry_with_backoff(max_retries=3, base_delay=2.0)
        def call_api():
            return api_client.invoke()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"第 {attempt + 1} 次尝试失败: {e}. "
                            f"{delay:.1f}秒后重试..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"达到最大重试次数 ({max_retries})")
            raise last_exception
        return wrapper
    return decorator


class LLMInvoker:
    """
    LLM 调用器，封装重试和超时逻辑
    """

    def __init__(self, llm, max_retries: int = 3, timeout: int = 120):
        """
        初始化 LLM 调用器

        Args:
            llm: LangChain LLM 实例
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
        """
        self.llm = llm
        self.max_retries = max_retries
        self.timeout = timeout

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def invoke(self, messages: list) -> Any:
        """
        调用 LLM（带重试）

        Args:
            messages: 消息列表

        Returns:
            LLM 响应
        """
        return self.llm.invoke(messages)

    def safe_invoke(self, messages: list, default: Any = None) -> Any:
        """
        安全调用 LLM（不抛出异常）

        Args:
            messages: 消息列表
            default: 失败时返回的默认值

        Returns:
            LLM 响应或默认值
        """
        try:
            return self.invoke(messages)
        except Exception as e:
            logger.error(f"LLM 调用最终失败: {e}")
            return default

"""
配置文件 - 性能优化参数
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 模型配置 - 速度优化
MODEL_CONFIG = {
    # Agent 1: Content Planner - 使用快速模型
    "content_planner": {
        "model": os.getenv("MODEL_NAME", "deepseek-chat"),
        "temperature": 0.7,
        "max_tokens": 2000,  # 只需生成JSON大纲，不需要太多token
    },

    # Agent 2: Designer & Generator - 使用快速模型
    "designer_generator": {
        "model": os.getenv("MODEL_NAME", "deepseek-chat"),
        "temperature": 0.6,
        "max_tokens": 8000,  # HTML代码较长
    },

    # Agent 3: Quality Checker - 使用快速模型
    "quality_checker": {
        "model": os.getenv("MODEL_NAME", "deepseek-chat"),
        "temperature": 0.3,  # 质检需要更严格
        "max_tokens": 3000,
    }
}

# 工作流配置
WORKFLOW_CONFIG = {
    "max_iterations": 1,  # 从2轮减少到1轮，优先速度
    "enable_quality_check": True,  # 可以关闭质检加速
}

# API配置
API_CONFIG = {
    "timeout": 60,  # API超时时间（秒）
    "retry_times": 2,  # 失败重试次数
}

"""
统一配置管理模块
集中管理所有配置项，支持环境变量和默认值
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    """LLM 配置"""
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "gpt-4"))
    temperature: float = field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0.7")))
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    timeout: int = field(default_factory=lambda: int(os.getenv("LLM_TIMEOUT", "120")))


@dataclass
class GenerationConfig:
    """生成配置"""
    use_parallel: bool = field(default_factory=lambda: os.getenv("USE_PARALLEL_GENERATION", "true").lower() == "true")
    use_pure_css: bool = field(default_factory=lambda: os.getenv("USE_PURE_CSS", "true").lower() == "true")
    use_ppt_pro: bool = field(default_factory=lambda: os.getenv("USE_PPT_PRO", "false").lower() == "true")
    max_workers: int = field(default_factory=lambda: int(os.getenv("MAX_WORKERS", "4")))
    default_page_count: int = field(default_factory=lambda: int(os.getenv("DEFAULT_PAGE_COUNT", "8")))


@dataclass
class StyleConfig:
    """样式配置"""
    # 字体规范
    min_font_size: int = 32
    h1_font_size: int = 72
    h2_font_size: int = 48
    body_font_size: int = 22
    line_height: float = 1.2

    # 分辨率
    resolution_width: int = 1920
    resolution_height: int = 1080

    # 默认字体族
    title_font_family: str = "Microsoft YaHei"
    body_font_family: str = "Microsoft YaHei"

    # 专业配色映射
    professional_colors: Dict = field(default_factory=lambda: {
        '机械': {
            'primary': '#2c3e50',
            'secondary': '#34495e',
            'accent': '#7f8c8d',
            'text': '#ecf0f1',
            'background': '#1a252f',
            'warning': '#e74c3c'
        },
        '医护': {
            'primary': '#27ae60',
            'secondary': '#2ecc71',
            'accent': '#ecf0f1',
            'text': '#ffffff',
            'background': '#1e3a28',
            'warning': '#e74c3c'
        },
        '电子': {
            'primary': '#3498db',
            'secondary': '#9b59b6',
            'accent': '#ecf0f1',
            'text': '#ffffff',
            'background': '#1e2a3a',
            'warning': '#e74c3c'
        },
        '汽车': {
            'primary': '#e74c3c',
            'secondary': '#c0392b',
            'accent': '#ecf0f1',
            'text': '#ffffff',
            'background': '#2a1e1e',
            'warning': '#f39c12'
        },
        '计算机': {
            'primary': '#9b59b6',
            'secondary': '#8e44ad',
            'accent': '#ecf0f1',
            'text': '#ffffff',
            'background': '#2a1e3a',
            'warning': '#e74c3c'
        },
    })

    # 教学场景对应的风格
    teaching_scene_styles: Dict = field(default_factory=lambda: {
        'theory': {
            'style_name': 'theory_clean',
            'density': 'comfortable',
            'image_style': 'clean_diagram',
            'icon_style': 'linear',
            'chart_preference': ['mindmap', 'flow', 'table']
        },
        'practice': {
            'style_name': 'practice_visual',
            'density': 'compact',
            'image_style': 'realistic_photo',
            'icon_style': 'filled',
            'chart_preference': ['photo', 'steps', 'comparison']
        },
        'safety': {
            'style_name': 'safety_warning',
            'density': 'spacious',
            'image_style': 'warning_icon',
            'icon_style': 'bold',
            'chart_preference': ['checklist', 'warning', 'do_dont']
        }
    })


@dataclass
class AppConfig:
    """应用总配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    style: StyleConfig = field(default_factory=StyleConfig)

    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    output_dir: str = field(default_factory=lambda: os.getenv("OUTPUT_DIR", "output"))

    def validate(self) -> List[str]:
        """
        验证配置

        Returns:
            错误列表，为空表示验证通过
        """
        errors = []
        if not self.llm.api_key:
            errors.append("缺少 OPENAI_API_KEY 环境变量")
        if self.generation.max_workers < 1:
            errors.append("MAX_WORKERS 必须 >= 1")
        if self.generation.default_page_count < 4:
            errors.append("DEFAULT_PAGE_COUNT 必须 >= 4")
        return errors

    def get_colors_for_major(self, major: str) -> Dict:
        """
        根据专业获取配色方案

        Args:
            major: 专业名称

        Returns:
            配色字典
        """
        for key, colors in self.style.professional_colors.items():
            if key in major:
                return colors
        # 默认返回机械类配色
        return self.style.professional_colors['机械']

    def get_style_for_scene(self, scene: str) -> Dict:
        """
        根据教学场景获取风格配置

        Args:
            scene: 教学场景 (theory/practice/safety)

        Returns:
            风格字典
        """
        return self.style.teaching_scene_styles.get(scene, self.style.teaching_scene_styles['theory'])


# 全局配置实例
config = AppConfig()


def get_style_json(major: str, scene: str = 'theory') -> Dict:
    """
    生成风格配置 JSON（供前端使用）

    Args:
        major: 专业名称
        scene: 教学场景

    Returns:
        完整的风格配置字典
    """
    colors = config.get_colors_for_major(major)
    scene_style = config.get_style_for_scene(scene)

    return {
        "style_name": scene_style['style_name'],
        "color": colors,
        "font": {
            "title_family": config.style.title_font_family,
            "body_family": config.style.body_font_family,
            "title_size": config.style.h1_font_size,
            "body_size": config.style.body_font_size,
            "line_height": config.style.line_height
        },
        "layout": {
            "density": scene_style['density'],
            "notes_area": True,
            "alignment": "left",
            "resolution": {
                "width": config.style.resolution_width,
                "height": config.style.resolution_height
            }
        },
        "imagery": {
            "image_style": scene_style['image_style'],
            "icon_style": scene_style['icon_style'],
            "chart_preference": scene_style['chart_preference']
        }
    }

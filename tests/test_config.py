"""
配置模块单元测试
"""
import pytest
from src.config import config, get_style_json, AppConfig


class TestConfig:
    """配置类测试"""

    def test_llm_config_defaults(self):
        """测试 LLM 配置默认值"""
        assert config.llm.temperature >= 0
        assert config.llm.max_retries >= 1

    def test_generation_config_defaults(self):
        """测试生成配置默认值"""
        assert isinstance(config.generation.use_parallel, bool)
        assert config.generation.max_workers >= 1
        assert config.generation.default_page_count >= 4

    def test_style_config_defaults(self):
        """测试样式配置默认值"""
        assert config.style.min_font_size == 32
        assert config.style.h1_font_size >= 64
        assert config.style.resolution_width == 1920
        assert config.style.resolution_height == 1080

    def test_get_colors_for_major(self):
        """测试根据专业获取配色"""
        colors = config.get_colors_for_major("机械制造")
        assert "primary" in colors
        assert "background" in colors

        colors = config.get_colors_for_major("医护护理")
        assert colors["primary"] == "#27ae60"

    def test_get_colors_for_unknown_major(self):
        """测试未知专业使用默认配色"""
        colors = config.get_colors_for_major("未知专业XYZ")
        # 应该返回机械类默认配色
        assert colors["primary"] == "#2c3e50"


class TestStyleJson:
    """风格 JSON 生成测试"""

    def test_get_style_json_structure(self):
        """测试风格 JSON 结构"""
        style = get_style_json("机械制造", "theory")

        # 验证顶层结构
        assert "style_name" in style
        assert "color" in style
        assert "font" in style
        assert "layout" in style
        assert "imagery" in style

    def test_get_style_json_color(self):
        """测试风格 JSON 配色"""
        style = get_style_json("机械制造", "theory")

        assert "primary" in style["color"]
        assert "secondary" in style["color"]
        assert "background" in style["color"]

    def test_get_style_json_font(self):
        """测试风格 JSON 字体"""
        style = get_style_json("机械制造", "theory")

        assert "title_family" in style["font"]
        assert "body_family" in style["font"]
        assert style["font"]["title_size"] >= 32

    def test_get_style_json_layout(self):
        """测试风格 JSON 布局"""
        style = get_style_json("机械制造", "theory")

        assert "density" in style["layout"]
        assert "resolution" in style["layout"]
        assert style["layout"]["resolution"]["width"] == 1920

    def test_get_style_json_imagery(self):
        """测试风格 JSON 图像风格"""
        style = get_style_json("机械制造", "theory")

        assert "image_style" in style["imagery"]
        assert "icon_style" in style["imagery"]
        assert "chart_preference" in style["imagery"]


class TestAppConfigValidation:
    """配置验证测试"""

    def test_validate_missing_api_key(self):
        """测试缺少 API Key 时的验证"""
        test_config = AppConfig()
        test_config.llm.api_key = ""

        errors = test_config.validate()
        assert len(errors) > 0
        assert any("OPENAI_API_KEY" in e for e in errors)

    def test_validate_invalid_max_workers(self):
        """测试无效的 max_workers"""
        test_config = AppConfig()
        test_config.llm.api_key = "test-key"
        test_config.generation.max_workers = 0

        errors = test_config.validate()
        assert len(errors) > 0
        assert any("MAX_WORKERS" in e for e in errors)

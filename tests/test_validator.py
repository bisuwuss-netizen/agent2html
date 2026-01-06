"""
轻量级验证器单元测试
"""
import pytest
from src.utils.lightweight_validator import validate_and_fix, get_professional_colors


class TestValidator:
    """验证器测试类"""

    def test_fixes_small_fonts(self):
        """测试修复过小字体"""
        html = '<p style="font-size: 12px;">文字</p>'
        result = validate_and_fix(html, {"major": "机械"})

        assert "font-size: 32px" in result["validated_html"]
        assert result["issues_found"] > 0

    def test_preserves_large_fonts(self):
        """测试保留正常字体"""
        html = '<p style="font-size: 48px;">文字</p>'
        result = validate_and_fix(html, {"major": "机械"})

        assert "font-size: 48px" in result["validated_html"]

    def test_replaces_gradient_colors(self):
        """测试替换渐变色"""
        html = '<div style="background: linear-gradient(135deg, #f093fb, #a6c1ee)"></div>'
        result = validate_and_fix(html, {"major": "机械"})

        assert "linear-gradient" not in result["validated_html"]
        assert result["issues_found"] > 0

    def test_replaces_forbidden_colors(self):
        """测试替换禁用颜色"""
        html = '<div style="color: #f093fb;"></div>'
        result = validate_and_fix(html, {"major": "机械"})

        assert "#f093fb" not in result["validated_html"]

    def test_removes_fragment_animations(self):
        """测试移除 fragment 动画"""
        html = '<div class="fragment fade-in">内容</div>'
        result = validate_and_fix(html, {"major": "机械"})

        assert "fragment" not in result["validated_html"]

    def test_professional_colors_for_major(self):
        """测试专业配色获取"""
        colors = get_professional_colors("机械制造")
        assert colors["primary"] == "#2c3e50"

        colors = get_professional_colors("医护专业")
        assert colors["primary"] == "#27ae60"

        colors = get_professional_colors("电子电气")
        assert colors["primary"] == "#3498db"

    def test_default_colors_for_unknown_major(self):
        """测试未知专业使用默认配色"""
        colors = get_professional_colors("未知专业")
        # 默认返回机械类配色
        assert colors["primary"] == "#2c3e50"


class TestValidatorIntegration:
    """验证器集成测试"""

    def test_full_html_validation(self):
        """测试完整 HTML 验证"""
        html = '''
        <section style="background: linear-gradient(90deg, #f093fb, #a6c1ee);">
            <h1 style="font-size: 24px;">标题</h1>
            <p style="font-size: 12px;" class="fragment">内容</p>
            <div style="color: #ff6fd8;">警告</div>
        </section>
        '''
        result = validate_and_fix(html, {"major": "机械制造"})

        # 验证所有问题都被修复
        assert "linear-gradient" not in result["validated_html"]
        assert "font-size: 32px" in result["validated_html"]
        assert "#ff6fd8" not in result["validated_html"]
        assert "fragment" not in result["validated_html"]
        assert result["issues_found"] >= 3

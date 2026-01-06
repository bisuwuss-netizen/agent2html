"""
工具模块包
"""
# 可选导入 - 部分模块依赖额外安装的包
try:
    from .image_generator import ImageGenerator
except ImportError as e:
    print(f"⚠️  ImageGenerator 未加载: {e}")
    ImageGenerator = None

try:
    from .material_library import MaterialLibrary
except ImportError as e:
    print(f"⚠️  MaterialLibrary 未加载: {e}")
    MaterialLibrary = None

__all__ = ["ImageGenerator", "MaterialLibrary"]

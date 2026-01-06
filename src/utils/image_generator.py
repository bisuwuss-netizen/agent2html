"""
图片生成模块 - 集成 DALL-E 或 Stable Diffusion
"""
import os
import base64
import requests
from typing import Optional, Dict
from openai import OpenAI


class ImageGenerator:
    """
    图片生成器 - 支持多种生成方式
    """

    def __init__(self, api_key: str = None, provider: str = "dall-e"):
        """
        初始化图片生成器

        Args:
            api_key: API密钥
            provider: 生成方式 ("dall-e", "stable-diffusion", "placeholder")
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.provider = provider
        self.client = None

        if provider == "dall-e" and self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "natural"
    ) -> Optional[Dict]:
        """
        生成图片

        Args:
            prompt: 图片描述（中文会自动翻译）
            size: 图片尺寸 ("1024x1024", "1792x1024", "1024x1792")
            quality: 质量 ("standard", "hd")
            style: 风格 ("natural", "vivid")

        Returns:
            {
                "url": "图片URL",
                "base64": "base64编码的图片数据（可选）",
                "revised_prompt": "优化后的提示词"
            }
        """
        if self.provider == "dall-e":
            return self._generate_dall_e(prompt, size, quality, style)
        elif self.provider == "stable-diffusion":
            return self._generate_stable_diffusion(prompt, size)
        else:
            # 返回占位符
            return self._generate_placeholder(prompt, size)

    def _generate_dall_e(
        self,
        prompt: str,
        size: str,
        quality: str,
        style: str
    ) -> Optional[Dict]:
        """
        使用 DALL-E 3 生成图片
        """
        try:
            # 翻译中文提示词（可选，DALL-E支持中文）
            enhanced_prompt = f"Educational illustration for vocational students: {prompt}"

            response = self.client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=size,
                quality=quality,
                style=style,
                n=1  # DALL-E 3 只能生成1张
            )

            image_data = response.data[0]

            return {
                "url": image_data.url,
                "revised_prompt": image_data.revised_prompt,
                "provider": "dall-e-3"
            }

        except Exception as e:
            print(f"❌ DALL-E 生成失败: {e}")
            return None

    def _generate_stable_diffusion(self, prompt: str, size: str) -> Optional[Dict]:
        """
        使用 Stable Diffusion API 生成图片
        （示例：使用 Stability AI API）
        """
        # TODO: 集成 Stable Diffusion API
        # 参考文档: https://platform.stability.ai/docs/api-reference
        print("⚠️  Stable Diffusion 暂未集成，返回占位符")
        return self._generate_placeholder(prompt, size)

    def _generate_placeholder(self, description: str, size: str) -> Dict:
        """
        生成占位符（不需要API调用）
        """
        width, height = size.split("x")
        return {
            "url": None,
            "html": f'''<div class="image-placeholder" style="width:{width}px; height:{height}px;">
    <div class="placeholder-content">
        <div class="placeholder-icon">🖼️</div>
        <div class="placeholder-text">图片位置预留</div>
        <div class="placeholder-desc">{description}</div>
    </div>
</div>''',
            "provider": "placeholder"
        }

    def download_image(self, url: str, save_path: str) -> bool:
        """
        下载图片到本地

        Args:
            url: 图片URL
            save_path: 保存路径

        Returns:
            是否成功
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                f.write(response.content)

            print(f"✅ 图片已保存: {save_path}")
            return True

        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return False

    def optimize_image(
        self,
        image_path: str,
        max_size: tuple = (1920, 1080),
        quality: int = 85
    ) -> bool:
        """
        优化图片（压缩、调整尺寸）

        Args:
            image_path: 图片路径
            max_size: 最大尺寸 (width, height)
            quality: JPEG质量 (1-100)

        Returns:
            是否成功
        """
        try:
            from PIL import Image

            img = Image.open(image_path)

            # 保持宽高比缩放
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # 保存（优化质量）
            if img.format == 'PNG':
                img.save(image_path, 'PNG', optimize=True)
            else:
                img.save(image_path, 'JPEG', quality=quality, optimize=True)

            print(f"✅ 图片已优化: {image_path}")
            return True

        except Exception as e:
            print(f"❌ 优化失败: {e}")
            return False


# 示例用法
if __name__ == "__main__":
    # 初始化生成器
    generator = ImageGenerator(provider="dall-e")

    # 生成图片
    result = generator.generate_image(
        prompt="车床主轴结构示意图，蓝色机械风格，专业教学用",
        size="1024x1024",
        quality="standard"
    )

    if result and result.get("url"):
        print(f"生成成功: {result['url']}")

        # 下载图片
        generator.download_image(result['url'], "output/generated_image.png")

        # 优化图片
        generator.optimize_image("output/generated_image.png")

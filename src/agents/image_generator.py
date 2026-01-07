"""
Image Generator Agent
负责：根据图片描述生成实际图片 (同步版)
"""
import os
import base64
from typing import Dict, List
from openai import OpenAI


class ImageGenerator:
    """
    图片生成器 (同步版) - 使用 DALL-E 或其他模型生成图片
    """

    def __init__(self, api_key: str = None, api_base: str = None):
        """初始化图片生成器"""
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=api_base or os.getenv("OPENAI_BASE_URL")
        )
        self.model = os.getenv("IMAGE_MODEL", "dall-e-3")

    def generate_image(self, description: str, size: str = "1024x1024") -> str:
        """
        生成单张图片 (同步)

        Args:
            description: 图片描述
            size: 图片尺寸 (1024x1024, 1792x1024, 1024x1792)

        Returns:
            base64 编码的图片数据
        """
        try:
            print(f"   🎨 正在生成图片: {description[:30]}...")

            response = self.client.images.generate(
                model=self.model,
                prompt=description,
                size=size,
                quality="standard",
                n=1,
                response_format="b64_json",
                timeout=30.0
            )

            # 获取 base64 编码的图片
            image_b64 = response.data[0].b64_json
            print(f"   ✅ 图片生成成功")

            return f"data:image/png;base64,{image_b64}"

        except Exception as e:
            print(f"   ⚠️  图片生成失败 ({type(e).__name__}): {e}")
            # 返回占位符
            return self._get_placeholder_svg(description)

    def _get_placeholder_svg(self, description: str) -> str:
        """生成 SVG 占位符"""
        # 截取前20个字
        short_desc = description[:20] + "..." if len(description) > 20 else description

        svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='800' height='600'>
            <rect width='800' height='600' fill='%23ecf0f1'/>
            <text x='50%25' y='50%25' text-anchor='middle' dy='.3em'
                  fill='%232c3e50' font-size='24' font-family='Arial'>{short_desc}</text>
        </svg>"""

        # URL encode
        import urllib.parse
        encoded_svg = urllib.parse.quote(svg)

        return f"data:image/svg+xml,{encoded_svg}"

    def generate_images_for_pages(self, pages: List[Dict]) -> Dict[int, str]:
        """
        为所有需要图片的页面生成图片 (串行)

        Args:
            pages: 页面列表

        Returns:
            {page_num: image_data_url} 的字典
        """
        results = {}

        for page in pages:
            page_num = page.get('page_num', page.get('index'))
            
            # 使用 assets 列表（新结构）或 image_description（旧结构）
            assets = page.get('assets', [])
            image_desc = page.get('image_description')
            
            # 确定是否需要生成
            target_desc = None
            size = "1024x1024"

            if assets:
                # 优先使用 assets 中的第一个图片
                for asset in assets:
                    if asset.get('type') in ['image', 'diagram']:
                        target_desc = asset.get('theme') or asset.get('prompt')
                        size_hint = asset.get('size', '1:1')
                        if size_hint == '16:9': size = "1792x1024"
                        elif size_hint == '4:3': size = "1024x1024"
                        break
            elif image_desc and image_desc != 'null':
                # 兼容旧结构
                target_desc = image_desc
                if page.get('image_size') == 'top':
                    size = "1792x1024"
            
            if target_desc:
                image_url = self.generate_image(target_desc, size)
                results[page_num] = image_url

        return results


def generate_images_agent(state: Dict, api_key: str = None, api_base: str = None) -> Dict:
    """
    图片生成 Agent

    输入: state['planning']['pages'] - 包含 image_description 的页面列表
    输出: state['generated_images'] - {page_num: image_url} 字典
    """
    print("🎨 Image Generator: 开始生成图片...")

    planning = state.get('planning', {})
    pages = planning.get('pages', [])

    # 统计需要生成的图片数量
    pages_with_images = [p for p in pages if p.get('image_description') and p.get('image_description') != 'null']
    total_images = len(pages_with_images)

    print(f"   需要生成 {total_images} 张图片")

    if total_images == 0:
        print("   ⚠️  没有需要生成的图片")
        return {
            **state,
            "generated_images": {},
            "status": "images_skipped"
        }

    # 创建生成器
    generator = ImageGenerator(api_key, api_base)

    # 生成所有图片
    try:
        images = generator.generate_images_for_pages(pages)

        print(f"✅ 图片生成完成：{len(images)}/{total_images} 张")

        return {
            **state,
            "generated_images": images,
            "status": "images_generated"
        }

    except Exception as e:
        print(f"❌ 图片生成失败: {e}")
        return {
            **state,
            "generated_images": {},
            "error": f"图片生成失败: {str(e)}",
            "status": "image_generation_failed"
        }

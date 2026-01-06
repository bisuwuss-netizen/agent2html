"""
Creative Generator - 创意页面生成器
集成图片生成 + 创意布局
"""
import json
import re
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


class CreativeGenerator:
    """
    创意生成器 - 支持图片生成和多样化布局
    """

    def __init__(self, llm: ChatOpenAI, max_workers: int = 4):
        self.llm = llm
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def generate_with_images(self, state: Dict) -> Dict:
        """
        生成带图片的完整 HTML

        工作流程：
        1. 并行生成所有页面HTML（带SVG占位符）
        2. 使用生成的图片替换占位符
        3. 合并成完整HTML
        """
        print("🎨 Creative Generator: 开始生成页面...")

        if not state.get('planning'):
            return {
                **state,
                "error": "缺少 planning 数据",
                "status": "failed"
            }

        planning = state['planning']
        user_input = state['user_input']
        pages = planning['pages']
        generated_images = state.get('generated_images', {})

        print(f"   总页数: {len(pages)}")
        print(f"   已生成图片: {len(generated_images)} 张")

        # 分批并行生成
        batches = self._split_into_batches(pages, self.max_workers)
        print(f"   每批页数: {[len(b) for b in batches]}")

        try:
            # 并行生成HTML
            html_parts = self._generate_batches_parallel(batches, planning, user_input, generated_images)

            # 合并HTML
            final_html = self._merge_html(html_parts, planning, user_input)

            print(f"✅ 创意页面生成完成！")

            return {
                **state,
                "html_code": final_html,
                "status": "html_generated"
            }

        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return {
                **state,
                "error": f"生成失败: {str(e)}",
                "status": "failed"
            }

    def _split_into_batches(self, pages: List[Dict], num_batches: int) -> List[List[Dict]]:
        """将页面分批"""
        batch_size = (len(pages) + num_batches - 1) // num_batches
        batches = []
        for i in range(0, len(pages), batch_size):
            batches.append(pages[i:i + batch_size])
        return batches

    def _generate_batches_parallel(
        self,
        batches: List[List[Dict]],
        planning: Dict,
        user_input: Dict,
        generated_images: Dict[int, str]
    ) -> List[str]:
        """并行生成所有批次"""
        futures = {}

        for batch_idx, batch in enumerate(batches):
            future = self.executor.submit(
                self._generate_batch_sync,
                batch,
                batch_idx + 1,
                planning,
                user_input,
                generated_images
            )
            futures[future] = batch_idx

        results = [None] * len(batches)

        for future in as_completed(futures):
            batch_idx = futures[future]
            try:
                html_parts = future.result()
                results[batch_idx] = html_parts
                print(f"   ✅ 批次 {batch_idx + 1} 完成 ({len(html_parts)} 页)")
            except Exception as e:
                print(f"   ❌ 批次 {batch_idx + 1} 失败: {e}")
                results[batch_idx] = []

        all_html_parts = []
        for batch_results in results:
            if batch_results:
                all_html_parts.extend(batch_results)

        return all_html_parts

    def _generate_batch_sync(
        self,
        pages: List[Dict],
        batch_num: int,
        planning: Dict,
        user_input: Dict,
        generated_images: Dict[int, str]
    ) -> List[str]:
        """同步生成一批页面"""
        print(f"   🔄 批次 {batch_num}: 开始生成 {len(pages)} 页...")

        html_parts = []

        for page in pages:
            try:
                html = self._generate_single_page_with_image(
                    page, planning, user_input, generated_images
                )
                html_parts.append(html)
            except Exception as e:
                print(f"   ⚠️  页面 {page.get('page_num')} 生成失败: {e}")
                html_parts.append(self._generate_placeholder_page(page))

        return html_parts

    def _generate_single_page_with_image(
        self,
        page: Dict,
        planning: Dict,
        user_input: Dict,
        generated_images: Dict[int, str]
    ) -> str:
        """生成单个页面（包含实际图片）"""
        from .designer_generator import get_color_scheme

        colors = get_color_scheme(user_input.get('major', ''))
        page_num = page.get('page_num')
        has_image = page.get('image_description') and page.get('image_description') != 'null'

        # 构建增强的 Prompt
        system_prompt = self._build_creative_system_prompt(colors)
        user_prompt = self._build_creative_user_prompt(page, colors, has_image, generated_images)

        # 调用 LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        html = response.content.strip()

        # 清理 markdown 标记
        if html.startswith("```html"):
            html = html.split("```html")[1].split("```")[0].strip()
        elif html.startswith("```"):
            html = html.split("```")[1].split("```")[0].strip()

        # 如果有生成的图片，替换占位符
        if has_image and page_num in generated_images:
            html = self._replace_image_placeholder(html, generated_images[page_num])

        # 清理破坏reveal.js布局的样式属性
        html = self._clean_section_styles(html)

        return html

    def _build_creative_system_prompt(self, colors: dict) -> str:
        """构建创意系统提示"""
        return f"""你是顶尖的创意网页设计师，精通视觉设计和教育课件制作。

【核心设计理念】

1. **视觉冲击力** - 打破常规，使用创意布局
   - 图片可以旋转 -3° 到 3° 的小角度
   - 使用阴影和层次感
   - 卡片式、拼贴式、网格式布局

2. **空间艺术** - 充分利用1920x1080空间
   - 错位排列
   - 不对称布局（保持视觉平衡）
   - 留白与紧凑结合

3. **色彩与字体**
   - 背景：{colors['bg_dark']}（纯色）
   - 文字：{colors['text_primary']}（高对比）
   - 强调：{colors['accent']}
   - h1: 68-72px, p/li: 36-40px

4. **创意布局类型**：

   📝 纯文字创意布局：
   - tag_cloud: 标签云（带旋转角度的标签）
   - card_grid: 创意卡片网格（3栏，轻微旋转）
   - highlight_boxes: 强调框堆叠
   - asymmetric_list: 不对称列表

   🖼️ 图文创意布局：
   - rotated_side_image: 侧边旋转图片
   - dual_images: 双图错位排列
   - collage: 拼贴风格（多图叠加）
   - polaroid_style: 拍立得风格（白边框+旋转）

5. **图片处理**：
   - 使用 transform: rotate(-3deg) 或 rotate(3deg)
   - 添加 box-shadow: 0 8px 24px rgba(0,0,0,0.4)
   - border-radius: 12px
   - 图片必须设置 max-width 和 max-height
   - 使用 object-fit: contain

6. **输出要求**：
   - 只输出 <section>...</section>
   - 所有样式内联
   - ⚠️ **重要**：<section> 标签上不要设置 width、height、min-height、max-height（reveal.js 会自动管理）
   - <section> 可以设置 background、color、position、padding、display、flex 等其他样式
   - 充分利用空间，避免过于空旷
"""

    def _build_creative_user_prompt(
        self,
        page: Dict,
        colors: dict,
        has_image: bool,
        generated_images: Dict[int, str]
    ) -> str:
        """构建创意用户提示"""
        page_num = page.get('page_num')
        layout = page.get('layout')

        # 判断是否使用实际图片
        use_real_image = has_image and page_num in generated_images
        image_note = "🎨 使用真实图片" if use_real_image else "📝 纯文字页面"

        prompt = f"""请生成以下页面的创意 HTML：

**页面信息：**
```json
{json.dumps(page, ensure_ascii=False, indent=2)}
```

**配色方案：**
- 主色：{colors['primary']}
- 背景：{colors['bg_dark']}
- 文字：{colors['text_primary']}
- 强调：{colors['accent']}

**设计要求：**
- 布局方式：{layout}
- {image_note}
- 充分利用1920x1080空间
- 图片要有轻微旋转（-3° 到 3°）
- 使用阴影和层次感

"""

        if has_image:
            if use_real_image:
                prompt += f"""
**图片处理：**
- 图片已生成，使用 {{{{IMAGE_PLACEHOLDER}}}} 作为 src
- 必须添加旋转：transform: rotate(-2deg) 或 rotate(3deg)
- 添加阴影：box-shadow: 0 8px 24px rgba(0,0,0,0.4)
- 图片描述（alt）：{page.get('image_description')}
"""
            else:
                image_size = page.get('image_size', 'side')
                max_size = "max-width:600px; max-height:700px" if image_size == 'side' else "max-width:1200px; max-height:500px"
                prompt += f"""
**SVG占位符：**
- 图片尺寸：{max_size}
- 使用SVG占位符，内容：{page.get('image_description')[:30]}...
- 必须添加 data-image-slot 属性
"""

        prompt += """

**创意要点：**
1. 打破对称，使用不规则排列
2. 图片略微旋转增加动感
3. 使用卡片、标签、框等元素
4. 充分利用空间，避免留白过多

请只输出 <section>...</section> 代码，不要解释。"""

        return prompt

    def _replace_image_placeholder(self, html: str, image_url: str) -> str:
        """替换图片占位符为实际图片"""
        # 查找所有 SVG 占位符
        pattern = r'src="data:image/svg\+xml[^"]*"'

        def replace_fn(match):
            return f'src="{image_url}"'

        html = re.sub(pattern, replace_fn, html)

        # 也尝试替换 {{IMAGE_PLACEHOLDER}}
        html = html.replace("{{IMAGE_PLACEHOLDER}}", image_url)
        html = html.replace("{IMAGE_PLACEHOLDER}", image_url)

        return html

    def _clean_section_styles(self, html: str) -> str:
        """清理section标签中破坏reveal.js布局的样式属性"""
        # 移除 width, height, min-height, max-height, min-width, max-width
        problematic_styles = [
            r'\s*width:\s*[^;]+;?',
            r'\s*height:\s*[^;]+;?',
            r'\s*min-height:\s*[^;]+;?',
            r'\s*max-height:\s*[^;]+;?',
            r'\s*min-width:\s*[^;]+;?',
            r'\s*max-width:\s*[^;]+;?'
        ]

        # 只处理<section>标签的style属性
        def clean_section_tag(match):
            section_tag = match.group(0)
            cleaned = section_tag
            for pattern in problematic_styles:
                cleaned = re.sub(pattern, '', cleaned)
            # 清理多余的分号和空格
            cleaned = re.sub(r';\s*;', ';', cleaned)
            cleaned = re.sub(r'style="\s*;', 'style="', cleaned)
            cleaned = re.sub(r';\s*"', '"', cleaned)
            return cleaned

        # 匹配<section...>标签
        html = re.sub(r'<section[^>]*>', clean_section_tag, html)

        return html

    def _generate_placeholder_page(self, page: Dict) -> str:
        """生成占位符页面"""
        return f'''<section style="display:flex; flex-direction:column; justify-content:center; align-items:center; padding:80px; background:#1a252f; color:#ecf0f1;">
  <h1 style="color:red; font-size:60px;">⚠️ 页面生成失败</h1>
  <p style="font-size:36px; margin-top:30px;">页面 {page.get('page_num')}: {page.get('title', '未知')}</p>
</section>'''

    def _merge_html(
        self,
        html_parts: List[str],
        planning: Dict,
        user_input: Dict
    ) -> str:
        """合并所有HTML片段"""
        from .designer_generator import get_color_scheme

        colors = get_color_scheme(user_input.get('major', ''))

        html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{planning.get('course_title', '课程')}</title>

  <!-- CDN -->
  <link rel="preconnect" href="https://cdnjs.cloudflare.com">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/reveal.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/theme/black.min.css">

  <style>
    #loading-screen {{
      position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
      background: {colors['bg_dark']};
      display: flex; flex-direction: column; justify-content: center; align-items: center;
      z-index: 9999; color: white; font-family: "Microsoft YaHei", sans-serif;
    }}
    #loading-screen h1 {{ font-size: 48px; animation: pulse 1.5s ease-in-out infinite; }}
    #loading-screen .spinner {{
      width: 60px; height: 60px; border: 5px solid rgba(255,255,255,0.3);
      border-top-color: white; border-radius: 50%; animation: spin 1s linear infinite; margin: 30px 0;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.6; }} }}

    /* 确保reveal.js容器正确填充 */
    html, body {{
      width: 100%;
      height: 100%;
      margin: 0;
      padding: 0;
      overflow: hidden;
    }}

    /* 强制reveal.js容器填满视口 */
    .reveal {{
      width: 100vw !important;
      height: 100vh !important;
    }}

    .reveal .slides {{
      width: 100vw !important;
      height: 100vh !important;
      transform: none !important;
    }}

    /* 自定义section样式 - 强制全屏 */
    .reveal section {{
      width: 100vw !important;
      height: 100vh !important;
      transform: none !important;
      top: 0 !important;
      left: 0 !important;
      background: {colors['bg_dark']} !important;
      color: {colors['text_primary']} !important;
      padding: 80px !important;
      box-sizing: border-box !important;
    }}

    /* 字体样式 - 使用vw单位自适应 */
    .reveal h1 {{
      font-size: 4vw !important;
      color: {colors['primary']} !important;
      margin-bottom: 40px !important;
    }}
    .reveal h2 {{
      font-size: 3vw !important;
      color: {colors['secondary']} !important;
    }}
    .reveal p, .reveal li {{
      font-size: 2vw !important;
      line-height: 1.6 !important;
    }}

    /* 创意样式 */
    .rotated-img {{ transform: rotate(-2deg); box-shadow: 0 8px 24px rgba(0,0,0,0.4); }}
    .rotated-img-r {{ transform: rotate(3deg); box-shadow: 0 8px 24px rgba(0,0,0,0.4); }}
  </style>

  <script>
    var CDNManager = {{
      cdns: [
        {{ name: 'CloudFlare', js: 'https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/reveal.min.js' }},
        {{ name: 'jsDelivr', js: 'https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.min.js' }},
        {{ name: 'BootCDN', js: 'https://cdn.bootcdn.net/ajax/libs/reveal.js/4.4.0/reveal.min.js' }}
      ],
      current: 0,
      load: function() {{
        if (this.current >= this.cdns.length) {{
          document.getElementById('loading-screen').innerHTML =
            '<h1>⚠️ 加载失败</h1><button onclick="location.reload()" style="margin-top:20px;padding:10px 30px;font-size: 32px;background:white;color:#e74c3c;border:none;border-radius:5px;cursor:pointer;">重试</button>';
          return;
        }}
        var cdn = this.cdns[this.current];
        document.getElementById('loading-status').textContent = '正在尝试 ' + cdn.name + '...';
        var s = document.createElement('script');
        s.src = cdn.js;
        s.onload = function() {{ CDNManager.init(cdn.name); }};
        s.onerror = function() {{ CDNManager.current++; CDNManager.load(); }};
        document.head.appendChild(s);
        setTimeout(function() {{ if (typeof Reveal === 'undefined') s.onerror(); }}, 8000);
      }},
      init: function(name) {{
        if (typeof Reveal !== 'undefined') {{
          Reveal.initialize({{
            width: '100%',
            height: '100%',
            margin: 0,
            minScale: 1,
            maxScale: 1,
            center: false,
            controls: true,
            progress: true,
            hash: true,
            transition: 'slide',
            disableLayout: true
          }});
          setTimeout(function() {{
            var ld = document.getElementById('loading-screen');
            ld.style.opacity = '0'; ld.style.transition = 'opacity 0.5s';
            setTimeout(function() {{ ld.style.display = 'none'; }}, 500);
          }}, 300);
        }}
      }}
    }};
    window.addEventListener('DOMContentLoaded', function() {{
      CDNManager.load();
    }});
  </script>
</head>
<body>

  <div id="loading-screen">
    <h1>正在加载课件</h1>
    <div class="spinner"></div>
    <p id="loading-status">正在连接 CDN...</p>
  </div>

  <div class="reveal">
    <div class="slides">

{''.join(html_parts)}

    </div>
  </div>

</body>
</html>'''

        return html


# 兼容接口
def creative_designer_generator(state: Dict, llm: ChatOpenAI) -> Dict:
    """创意设计+生成 Agent（带图片生成）"""
    generator = CreativeGenerator(llm, max_workers=4)
    return generator.generate_with_images(state)

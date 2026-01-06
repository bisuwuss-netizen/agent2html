"""
纯CSS生成器 - 不依赖任何外部库
使用CSS :target伪类实现页面切换
"""
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


class PureCSSGenerator:
    """纯HTML+CSS生成器"""

    def __init__(self, llm: ChatOpenAI, max_workers: int = 4):
        self.llm = llm
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def generate(self, state: Dict) -> Dict:
        """生成完整的纯CSS幻灯片"""
        print("🎨 纯CSS生成器: 开始生成...")

        planning = state.get('planning')
        user_input = state.get('user_input')

        if not planning:
            return {**state, "error": "缺少planning数据", "status": "failed"}

        pages = planning['pages']
        print(f"   总页数: {len(pages)}")

        # 并行生成所有页面
        html_parts = self._generate_pages_parallel(pages, planning, user_input)

        # 合并成完整HTML
        final_html = self._merge_html(html_parts, planning, user_input)

        print("✅ 纯CSS页面生成完成！")

        return {
            **state,
            "html_code": final_html,
            "status": "html_generated"
        }

    def _generate_pages_parallel(self, pages: List[Dict], planning: Dict, user_input: Dict) -> List[str]:
        """并行生成所有页面"""
        futures = {}

        for page in pages:
            future = self.executor.submit(
                self._generate_single_page,
                page, planning, user_input
            )
            futures[future] = page.get('page_num')

        html_parts = [''] * len(pages)
        for future in as_completed(futures):
            page_num = futures[future]
            try:
                html = future.result()
                html_parts[page_num - 1] = html
                print(f"   ✅ 页面 {page_num} 生成完成")
            except Exception as e:
                print(f"   ❌ 页面 {page_num} 生成失败: {e}")
                html_parts[page_num - 1] = self._get_error_page(page_num)

        return html_parts

    def _generate_single_page(self, page: Dict, planning: Dict, user_input: Dict) -> str:
        """生成单个页面"""
        from .designer_generator import get_color_scheme
        colors = get_color_scheme(user_input.get('major', ''))

        page_num = page.get('page_num')
        has_image = page.get('image_description') and page.get('image_description') != 'null'

        system_prompt = f"""你是专业的HTML网页设计师，精通现代CSS和视觉设计。

**任务**：为幻灯片生成单个页面的HTML代码（<section>...</section>）

**设计要求**：
1. 使用纯HTML+CSS，不使用任何JavaScript
2. 使用vw/vh单位确保响应式
3. 标题: 4-5vw, 正文: 2-2.5vw
4. 使用创意布局：卡片、网格、不对称排列
5. 添加轻微旋转效果：transform: rotate(-2deg 到 2deg)
6. 使用阴影增加层次感：box-shadow: 0 8px 24px rgba(0,0,0,0.4)
7. **风格定位**：高职教育课件，专业、清晰、易懂，适合课堂教学

**配色方案**：
- 背景：{colors['bg_dark']}
- 主色：{colors['primary']}
- 强调：{colors['accent']}
- 文字：{colors['text_primary']}

**必须遵守**：
- 只输出<section>...</section>之间的内容
- 所有样式必须内联（inline style）
- 不要使用class，直接用style属性
- section标签必须有id="page{page_num}"属性
- section必须使用：width: 100vw; height: 100vh; padding: 80px;
"""

        user_prompt = f"""生成第{page_num}页的HTML代码：

**页面信息**：
```json
{page}
```

**图片插槽要求**：
{self._get_image_instruction(has_image, page.get('image_size', 'side'))}

**布局要求**：
1. 充分利用空间，内容居中或创意排列
2. 使用卡片式布局，添加旋转和阴影
3. 只输出<section id="page{page_num}" class="slide" ...>...</section>代码
4. section标签必须有：style="width: 100vw; height: 100vh; padding: 80px;"
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        html = response.content.strip()

        # 清理markdown标记
        if html.startswith("```html"):
            html = html.split("```html")[1].split("```")[0].strip()
        elif html.startswith("```"):
            html = html.split("```")[1].split("```")[0].strip()

        return html

    def _get_image_instruction(self, has_image: bool, image_size: str = 'side') -> str:
        """生成图片插槽指令"""
        if not has_image:
            return "❌ 本页无需图片，纯文字内容即可"

        if image_size == 'top':
            return """✅ 本页需要顶部横向图片插槽：
- 使用<img>标签，设置data-image-slot="top"属性
- 尺寸：max-width: 1200px; max-height: 500px;
- 样式：border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.3);
- 位置：页面顶部或居中上方
- 初始使用SVG占位符，后续会替换为实际图片
示例：
<img data-image-slot="top" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1200' height='500'%3E%3Crect width='100%25' height='100%25' fill='%232c3e50'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23ecf0f1' font-size='24'%3E图片插槽 - 等待上传%3C/text%3E%3C/svg%3E" style="max-width: 1200px; max-height: 500px; width: 100%; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.3);" alt="图片描述">"""
        else:
            return """✅ 本页需要侧边竖向图片插槽：
- 使用<img>标签，设置data-image-slot="side"属性
- 尺寸：max-width: 500px; max-height: 600px;
- 样式：border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.3);
- 位置：页面左侧或右侧，与文字并排
- 初始使用SVG占位符，后续会替换为实际图片
示例：
<img data-image-slot="side" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='500' height='600'%3E%3Crect width='100%25' height='100%25' fill='%232c3e50'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23ecf0f1' font-size='20'%3E图片插槽%3C/text%3E%3C/svg%3E" style="max-width: 500px; max-height: 600px; width: 100%; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.3);" alt="图片描述">"""

    def _get_error_page(self, page_num: int) -> str:
        """生成错误页面"""
        return f'''<section id="page{page_num}" class="slide">
  <h1 style="color: #e74c3c; font-size: 4vw;">⚠️ 页面生成失败</h1>
  <p style="font-size: 2vw;">页面 {page_num}</p>
</section>'''

    def _merge_html(self, html_parts: List[str], planning: Dict, user_input: Dict) -> str:
        """合并所有HTML片段"""
        from .designer_generator import get_color_scheme
        colors = get_color_scheme(user_input.get('major', ''))

        total_pages = len(html_parts)
        nav_buttons = '\n    '.join([
            f'<a href="#page{i+1}" title="第{i+1}页">{i+1}</a>'
            for i in range(total_pages)
        ])

        html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{planning.get('course_title', '课程')}</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
      overflow: hidden;
      background: #000;
    }}

    /* 幻灯片容器 */
    .slides {{
      width: 100vw;
      height: 100vh;
      position: relative;
    }}

    /* 每一页的基础样式 */
    .slide {{
      width: 100vw;
      height: 100vh;
      position: absolute;
      top: 0;
      left: 0;
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.5s ease, visibility 0.5s ease;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      padding: 80px;
      background: {colors['bg_dark']};
      color: {colors['text_primary']};
    }}

    /* 显示当前页 */
    .slide:target {{
      opacity: 1;
      visibility: visible;
      z-index: 1;
    }}

    /* 默认显示第一页 */
    .slide:first-child {{
      opacity: 1;
      visibility: visible;
    }}

    /* 导航按钮 */
    .nav {{
      position: fixed;
      bottom: 40px;
      right: 40px;
      z-index: 100;
      display: flex;
      gap: 15px;
      flex-wrap: wrap;
      max-width: 600px;
      justify-content: flex-end;
    }}

    .nav a {{
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 50px;
      height: 50px;
      padding: 0 15px;
      background: rgba(52, 152, 219, 0.8);
      color: white;
      text-decoration: none;
      border-radius: 25px;
      font-size: 18px;
      transition: all 0.3s ease;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}

    .nav a:hover {{
      background: #3498db;
      transform: translateY(-3px);
      box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    }}

    /* 页码指示器 */
    .indicator {{
      position: fixed;
      top: 40px;
      right: 40px;
      z-index: 100;
      background: rgba(0,0,0,0.6);
      padding: 12px 24px;
      border-radius: 25px;
      color: white;
      font-size: 16px;
      backdrop-filter: blur(10px);
    }}

    /* 创意卡片基础样式 */
    .card {{
      background: rgba(44, 62, 80, 0.7);
      padding: 30px;
      border-radius: 12px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
      transition: transform 0.3s ease;
    }}

    .card:hover {{
      transform: scale(1.05) !important;
    }}
  </style>
</head>
<body>
  <div class="slides">
    {chr(10).join(html_parts)}
  </div>

  <!-- 导航按钮 -->
  <div class="nav">
    {nav_buttons}
  </div>

  <!-- 提示信息 -->
  <div class="indicator">
    点击右下角数字切换页面 | 共{total_pages}页
  </div>
</body>
</html>'''

        return html

"""
Agent 2+: Parallel Generator (并行生成 Agent)
实现分页并行生成，大幅提升性能
"""
import asyncio
import json
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


class ParallelGenerator:
    """
    并行生成器 - 将页面分批并行生成，大幅提升速度

    策略：
    1. 将8-12页分成4个批次（每批2-3页）
    2. 4个批次并行调用LLM
    3. 合并生成的HTML片段

    预期提速：70%（200秒 → 60秒）
    """

    def __init__(self, llm: ChatOpenAI, max_workers: int = 4):
        """
        初始化并行生成器

        Args:
            llm: LLM实例
            max_workers: 最大并行数（默认4，根据API限制调整）
        """
        self.llm = llm
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def generate_parallel(self, state: Dict) -> Dict:
        """
        并行生成所有页面

        Args:
            state: 包含planning的状态

        Returns:
            更新后的state，包含html_code
        """
        print("🚀 Parallel Generator: 开始并行生成页面...")

        if not state.get('planning'):
            return {
                **state,
                "error": "缺少 planning 数据",
                "status": "failed"
            }

        planning = state['planning']
        user_input = state['user_input']
        pages = planning['pages']
        total_pages = len(pages)

        print(f"   总页数: {total_pages}")
        print(f"   并行批次: {self.max_workers}")

        # 将页面分批
        batches = self._split_into_batches(pages, self.max_workers)
        print(f"   每批页数: {[len(b) for b in batches]}")

        # 并行生成
        try:
            html_parts = self._generate_batches_parallel(batches, planning, user_input)

            # 合并HTML
            final_html = self._merge_html(html_parts, planning, user_input)

            print(f"✅ 并行生成完成！")

            return {
                **state,
                "html_code": final_html,
                "status": "html_generated"
            }

        except Exception as e:
            print(f"❌ 并行生成失败: {e}")
            return {
                **state,
                "error": f"并行生成失败: {str(e)}",
                "status": "failed"
            }

    def _split_into_batches(self, pages: List[Dict], num_batches: int) -> List[List[Dict]]:
        """将页面分成N个批次"""
        batch_size = (len(pages) + num_batches - 1) // num_batches  # 向上取整
        batches = []

        for i in range(0, len(pages), batch_size):
            batch = pages[i:i + batch_size]
            batches.append(batch)

        return batches

    def _generate_batches_parallel(
        self,
        batches: List[List[Dict]],
        planning: Dict,
        user_input: Dict
    ) -> List[str]:
        """
        并行生成所有批次

        Returns:
            按顺序排列的HTML片段列表
        """
        futures = {}

        # 提交所有任务
        for batch_idx, batch in enumerate(batches):
            future = self.executor.submit(
                self._generate_batch_sync,
                batch,
                batch_idx + 1,
                planning,
                user_input
            )
            futures[future] = batch_idx

        # 收集结果（按顺序）
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

        # 展平结果
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
        user_input: Dict
    ) -> List[str]:
        """
        同步生成一批页面（在单独的线程中执行）

        Args:
            pages: 这批要生成的页面
            batch_num: 批次编号
            planning: 完整的规划信息
            user_input: 用户输入

        Returns:
            HTML片段列表
        """
        print(f"   🔄 批次 {batch_num}: 开始生成 {len(pages)} 页...")

        html_parts = []

        for page in pages:
            try:
                html = self._generate_single_page(page, planning, user_input)
                html_parts.append(html)
            except Exception as e:
                print(f"   ⚠️  页面 {page.get('page_num')} 生成失败: {e}")
                # 生成一个占位符
                html_parts.append(self._generate_placeholder_page(page))

        return html_parts

    def _generate_single_page(
        self,
        page: Dict,
        planning: Dict,
        user_input: Dict,
        generated_images: Dict[int, str] = None
    ) -> str:
        """
        生成单个页面的HTML

        Args:
            page: 页面信息
            planning: 规划信息（用于样式）
            user_input: 用户输入（用于配色）

        Returns:
            单个<section>的HTML代码
        """
        from .designer_generator import get_color_scheme

        # 获取配色
        colors = get_color_scheme(user_input.get('major', ''))

        # 构建Prompt（只针对这一页）
        system_prompt = f"""你是专业的 HTML 课件生成专家。

你的任务是：根据页面信息，生成**单个** <section> 标签的 HTML 代码。

【核心要求】

1. 字体规范（严格执行）：
   - h1: 64-72px（font-weight: 700）
   - h2: 48-56px（font-weight: 600）
   - p, li: 32-40px（line-height: 1.6）
   - 禁止使用小于 32px 的字体

2. 配色规范：
   - 背景：{colors['bg_dark']}（纯色，不用渐变）
   - 文字：{colors['text_primary']}（浅色，高对比度）
   - 强调：{colors['accent']}

3. 布局规范（根据 layout 字段严格执行）：

   📝 **纯文字布局**（无图片）：

   - full_text_center: 大标题 + 段落文字居中
     ```html
     <section style="display:flex; flex-direction:column; justify-content:center; align-items:center; padding:80px; background:{colors['bg_dark']}; color:{colors['text_primary']};">
       <h1 style="font-size:72px; margin-bottom:40px;">标题</h1>
       <p style="font-size:38px; max-width:1400px; line-height:1.6;">段落文字...</p>
     </section>
     ```

   - text_with_bullets: 标题 + 要点列表
     ```html
     <section style="display:flex; flex-direction:column; justify-content:center; padding:80px; background:{colors['bg_dark']}; color:{colors['text_primary']};">
       <h1 style="font-size:68px; margin-bottom:50px;">标题</h1>
       <ul style="list-style:none; padding:0;">
         <li style="font-size:36px; margin-bottom:30px;">● 要点1</li>
         <li style="font-size:36px; margin-bottom:30px;">● 要点2</li>
       </ul>
     </section>
     ```

   - numbered_steps: 大号编号 + 步骤列表
     ```html
     <section style="display:flex; flex-direction:column; justify-content:center; padding:80px; background:{colors['bg_dark']}; color:{colors['text_primary']};">
       <h1 style="font-size:68px; margin-bottom:50px;">标题</h1>
       <ol style="list-style:none; padding:0;">
         <li style="display:flex; align-items:center; margin-bottom:35px; font-size:36px;">
           <span style="display:inline-block; width:70px; height:70px; background:{colors['accent']}; color:{colors['bg_dark']}; border-radius:50%; text-align:center; line-height:70px; font-weight:700; margin-right:24px;">1</span>
           步骤1描述
         </li>
       </ol>
     </section>
     ```

   - warning_grid: 红色警告卡片网格
     ```html
     <section style="display:flex; flex-direction:column; justify-content:center; align-items:center; padding:80px; background:{colors['bg_dark']}; color:{colors['text_primary']};">
       <h1 style="font-size:68px; margin-bottom:50px;">安全注意事项</h1>
       <div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:30px; width:100%; max-width:1600px;">
         <div style="background:{colors['warning']}; padding:40px; border-radius:12px; font-size:34px; font-weight:600;">⚠️ 警告内容1</div>
         <div style="background:{colors['warning']}; padding:40px; border-radius:12px; font-size:34px; font-weight:600;">⚠️ 警告内容2</div>
       </div>
     </section>
     ```

   🖼️ **带图布局**（仅当 image_description 存在时）：

   - left_text_right_image: 左60%文字 + 右40%侧边小图
     ```html
     <section style="display:flex; padding:80px; background:{colors['bg_dark']}; color:{colors['text_primary']};">
       <div style="flex:6; padding-right:40px; display:flex; flex-direction:column; justify-content:center;">
         <h1 style="font-size:68px; margin-bottom:40px;">标题</h1>
         <ul style="list-style:none; padding:0;">
           <li style="font-size:36px; margin-bottom:25px;">● 要点</li>
         </ul>
       </div>
       <div style="flex:4; display:flex; align-items:center; justify-content:center;">
         <img src="..." alt="..." data-image-slot="..."
              style="max-width:600px; max-height:700px; width:100%; height:auto; object-fit:contain; border-radius:8px; box-shadow:0 4px 12px rgba(0,0,0,0.3);" />
       </div>
     </section>
     ```

   - top_image_center: 顶部小图 + 底部文字
     ```html
     <section style="display:flex; flex-direction:column; justify-content:center; align-items:center; padding:80px; background:{colors['bg_dark']}; color:{colors['text_primary']};">
       <img src="..." alt="..." data-image-slot="..."
            style="max-width:1200px; max-height:500px; width:80%; height:auto; object-fit:contain; border-radius:8px; margin-bottom:40px; box-shadow:0 4px 12px rgba(0,0,0,0.3);" />
       <h1 style="font-size:68px; margin-bottom:30px;">标题</h1>
       <p style="font-size:36px; max-width:1400px; line-height:1.6; text-align:center;">文字内容...</p>
     </section>
     ```

4. 图片槽位规范（严格控制）：
   - **只有当 image_description 字段存在且不为 null 时，才生成图片**
   - **图片尺寸控制**：
     * 侧边图：max-width: 600px; max-height: 700px;
     * 顶部图：max-width: 1200px; max-height: 500px;
     * 必须添加：object-fit: contain;（防止变形和溢出）
   - SVG占位符模板：
     ```html
     <img
       src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Crect width='400' height='300' fill='%23ecf0f1'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%232c3e50' font-size='18' font-family='Arial'%3E[图片描述前20字]%3C/text%3E%3C/svg%3E"
       alt="[完整的image_description]"
       data-image-slot="[完整的image_description]"
       style="max-width:600px; max-height:700px; width:100%; height:auto; object-fit:contain; border-radius:8px; box-shadow:0 4px 12px rgba(0,0,0,0.3);"
     />
     ```

5. 输出格式：
   - 只输出 <section>...</section>，不要完整HTML
   - ⚠️ **重要**：<section> 标签上不要设置 width、height、min-height、max-height（reveal.js 会自动管理）
   - <section> 可以设置 background、color、position、padding、display、flex 等其他样式
   - 确保内容在 1920x1080 范围内
   - 直接输出代码，不要解释文字
   - 如果无 image_description 字段，使用纯文字布局"""

        # 判断是否需要图片
        has_image = page.get('image_description') and page.get('image_description') != 'null'
        image_size_hint = page.get('image_size', 'side')  # side 或 top

        user_prompt = f"""请生成以下页面的HTML代码：

**页面信息：**
```json
{json.dumps(page, ensure_ascii=False, indent=2)}
```

**配色方案（专业纯色）：**
- 主色：{colors['primary']}
- 背景：{colors['bg_dark']}（纯色）
- 文字：{colors['text_primary']}
- 强调：{colors['accent']}
- 警告：{colors['warning']}

**布局与图片要求：**
- 页面类型：{page.get('type')}
- 布局方式：{page.get('layout')}
- {'🖼️ 本页需要图片：' + page.get('image_description') if has_image else '📝 本页纯文字，无图片'}
{f"- 图片尺寸：{'侧边小图（max-width:600px, max-height:700px）' if image_size_hint == 'side' else '顶部小图（max-width:1200px, max-height:500px）'}" if has_image else ''}

**严格要求：**
1. {'如果有 image_description 字段，必须生成 <img> 标签，使用 SVG 占位符' if has_image else '本页无 image_description 字段，禁止生成任何图片标签'}
2. 图片必须设置 max-width 和 max-height，并添加 object-fit: contain
3. 使用 {page.get('layout')} 布局方式
4. 字体大小：h1=68-72px, p/li=36-40px
5. 背景使用纯色 {colors['bg_dark']}，不要渐变

请只输出 <section>...</section> 代码，不要解释。"""

        # 调用LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm.invoke(messages)
        html = response.content.strip()

        # 清理可能的markdown代码块标记
        if html.startswith("```html"):
            html = html.split("```html")[1].split("```")[0].strip()
        elif html.startswith("```"):
            html = html.split("```")[1].split("```")[0].strip()

        # 清理破坏reveal.js布局的样式属性
        html = self._clean_section_styles(html)

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
        """生成占位符页面（当生成失败时）"""
        return f'''<section data-type="{page.get('type', 'placeholder')}">
  <div class="content-area center">
    <h1 style="color:red;">⚠️ 页面生成失败</h1>
    <p>页面 {page.get('page_num')}: {page.get('title', '未知')}</p>
    <p style="font-size:28px; opacity:0.7;">请重新生成</p>
  </div>
</section>'''

    def _merge_html(
        self,
        html_parts: List[str],
        planning: Dict,
        user_input: Dict
    ) -> str:
        """
        合并所有HTML片段成完整的reveal.js HTML

        Args:
            html_parts: 各页面的HTML片段
            planning: 规划信息
            user_input: 用户输入

        Returns:
            完整的HTML文件
        """
        from .designer_generator import get_color_scheme

        colors = get_color_scheme(user_input.get('major', ''))

        # 组装完整HTML
        html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{planning.get('course_title', '课程')}</title>

  <!-- CDN多重备份 -->
  <link rel="preconnect" href="https://cdnjs.cloudflare.com">
  <link rel="preconnect" href="https://cdn.jsdelivr.net">

  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/reveal.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/theme/black.min.css">

  <style>
    /* 加载屏幕 */
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
      font-size: 4.5vw !important;
      color: {colors['primary']} !important;
      margin-bottom: 40px !important;
    }}
    .reveal h2 {{
      font-size: 3.5vw !important;
      color: {colors['secondary']} !important;
    }}
    .reveal p, .reveal li {{
      font-size: 2.2vw !important;
      line-height: 1.6 !important;
    }}
    .reveal .highlight {{
      color: {colors['accent']};
      font-weight: bold;
    }}

    /* 图片占位符 */
    .image-placeholder {{
      background: {colors['surface']};
      border: 3px dashed {colors['accent']}; border-radius: 12px; color: {colors['text_primary']};
      height: 480px; display: flex; flex-direction: column;
      justify-content: center; align-items: center;
    }}
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
            '<h1>⚠️ 加载失败</h1><button onclick="location.reload()" style="margin-top:20px;padding:10px 30px;font-size:18px;background:white;color:#e74c3c;border:none;border-radius:5px;cursor:pointer;">重试</button>';
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
        console.log('✅ 成功加载:', name);
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

  <!-- 加载屏幕 -->
  <div id="loading-screen">
    <h1>正在加载课件</h1>
    <div class="spinner"></div>
    <p id="loading-status">正在连接 CDN...</p>
  </div>

  <!-- Reveal.js 容器 -->
  <div class="reveal">
    <div class="slides">

{''.join(html_parts)}

    </div>
  </div>

</body>
</html>'''

        return html


# 兼容接口：保持与原designer_generator相同的接口
def parallel_designer_generator(state: Dict, llm: ChatOpenAI) -> Dict:
    """
    并行设计+生成 Agent（兼容接口）

    这是 designer_generator 的升级版本，使用并行生成策略
    """
    generator = ParallelGenerator(llm, max_workers=4)
    return generator.generate_parallel(state)

"""
Agent 2: Designer & Generator (设计+生成 Agent)
负责：根据内容规划，生成精美的 reveal.js HTML 网页
"""
import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.utils.professional_colors import get_color_scheme as get_professional_colors


# 已弃用 - 使用 professional_colors.py 中的配色
# # COLOR_SCHEMES = {
#     "机械": {
#         "primary": "#4facfe",           # 科技蓝
#         "secondary": "#00f2fe",         # 青色
#         "accent": "#f093fb",            # 粉紫
#         "bg_dark": "#0c1929",           # 深蓝黑
#         "bg_gradient": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
#         "surface": "rgba(255, 255, 255, 0.05)",
#         "text_primary": "#ffffff",
#         "text_secondary": "#b8c5d6",
#         "text_accent": "#4facfe"
#     },
#     "3D": {
#         "primary": "#667eea",           # 蓝紫
#         "secondary": "#764ba2",         # 紫色
#         "accent": "#f093fb",            # 粉紫
#         "bg_dark": "#0f0c29",           # 深紫黑
#         "bg_gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
#         "surface": "rgba(255, 255, 255, 0.05)",
#         "text_primary": "#ffffff",
#         "text_secondary": "#b8c5d6",
#         "text_accent": "#4fc3f7"
#     },
#     "烹饪": {
#         "primary": "#ff6b6b",           # 暖红
#         "secondary": "#feca57",         # 金黄
#         "accent": "#ff9ff3",            # 粉色
#         "bg_dark": "#2d1f1f",           # 深棕
#         "bg_gradient": "linear-gradient(135deg, #cb356b 0%, #bd3f32 100%)",
#         "surface": "rgba(255, 255, 255, 0.08)",
#         "text_primary": "#ffffff",
#         "text_secondary": "#f5d6c6",
#         "text_accent": "#feca57"
#     },
#     "医护": {
#         "primary": "#00d4aa",           # 青绿
#         "secondary": "#38ef7d",         # 亮绿
#         "accent": "#4facfe",            # 蓝色
#         "bg_dark": "#0a1f1a",           # 深绿黑
#         "bg_gradient": "linear-gradient(135deg, #134e5e 0%, #71b280 100%)",
#         "surface": "rgba(255, 255, 255, 0.05)",
#         "text_primary": "#ffffff",
#         "text_secondary": "#c5e8d6",
#         "text_accent": "#00d4aa"
#     },
#     "default": {
#         "primary": "#667eea",           # 蓝紫
#         "secondary": "#764ba2",         # 紫色
#         "accent": "#f093fb",            # 粉紫
#         "bg_dark": "#0f0c29",           # 深紫黑
#         "bg_gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
#         "surface": "rgba(255, 255, 255, 0.05)",
#         "text_primary": "#ffffff",
#         "text_secondary": "#b8c5d6",
#         "text_accent": "#4fc3f7"
#     }
# }
#

def get_color_scheme(major: str) -> Dict[str, str]:
    """根据专业选择配色方案（使用新的专业配色）"""
    return get_professional_colors(major)


def designer_generator(state: Dict, llm: ChatOpenAI) -> Dict:
    """
    设计+生成 Agent

    输入: state['planning'] (来自 Agent 1)
    输出: state['html_code'] (完整的 reveal.js HTML)
    """

    print("🎨 Agent 2: Designer & Generator - 开始生成网页...")

    if not state.get('planning'):
        return {
            **state,
            "error": "缺少 planning 数据，无法生成网页",
            "status": "failed"
        }

    planning = state['planning']
    user_input = state['user_input']

    # 选择配色方案
    colors = get_color_scheme(user_input.get('major', ''))

    # 构建 Prompt
    system_prompt = f"""你是专业的 HTML 课件生成专家，精通 reveal.js 和教育课件设计。

【核心要求 - 必须严格执行】

1. 字体规范：
   - h1 标题：64-72px（font-weight: 700）
   - h2 副标题：48-56px（font-weight: 600）
   - 正文/列表：32-40px（line-height: 1.6）
   - 禁止使用小于 32px 的字体

2. 配色规范（已提供专业配色）：
   - 主色：{colors['primary']}
   - 背景：{colors['bg_dark']}
   - 文字：{colors['text_primary']}
   - 强调：{colors['accent']}
   - 警告：{colors['warning']}
   - 不使用渐变色，使用纯色

3. 图片槽位规范（非常重要！）：
   **每个需要图片的位置，必须生成带占位符的 <img> 标签**

   SVG占位图模板：
   ```html
   <img
     src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Crect width='400' height='300' fill='%23ecf0f1'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%232c3e50' font-size='18' font-family='Arial'%3E图片描述%3C/text%3E%3C/svg%3E"
     alt="图片描述"
     data-image-slot="详细的图片描述，用于后续素材库匹配"
     style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"
   />
   ```

   关键点：
   - src 使用 data URI 格式的 SVG（浅灰色背景 + 描述文字）
   - data-image-slot 属性存储完整的图片描述
   - alt 属性也包含图片描述
   - 样式：圆角、阴影、响应式

4. 布局规范：
   - left_text_right_image: 左60% + 右40%（flex布局）
   - top_image_bottom_text: 上50% + 下50%
   - two_columns: 各50%，左右对称
   - center: 居中（标题页）
   - 禁止图片在底部（除非 top_image_bottom_text）

5. 响应式规范：
   - 1920x1080 分辨率优化
   - padding: 60px 80px
   - 使用 flex 布局
   - 确保内容不溢出

6. 代码质量：
   - 完整的 HTML 结构（DOCTYPE, head, body）
   - 所有 CSS 写在 <style> 标签内
   - 包含多CDN备份加载代码
   - 直接输出 HTML，不要解释文字

你的任务是：根据课件规划，生成符合上述所有规范的完整 HTML 文件。"""

    user_prompt = f"""请根据以下课件规划，生成完整的 reveal.js HTML 文件：

**课件规划：**
```json
{json.dumps(planning, ensure_ascii=False, indent=2)}
```

**用户信息：**
- 专业：{user_input.get('major', '通用')}
- 授课对象：{user_input.get('target_audience', '学生')}

**配色方案（专业纯色配色，无渐变）：**
- 主色：{colors['primary']}
- 辅色：{colors['secondary']}
- 强调色：{colors['accent']}
- 深色背景：{colors['bg_dark']}
- 卡片表面：{colors['surface']}
- 主文字色：{colors['text_primary']}（浅色，确保可读）
- 次文字色：{colors['text_secondary']}
- 强调文字色：{colors['text_accent']}
- 警告色：{colors['warning']}

**🔴🔴🔴 核心布局与资源要求（必须严格遵守）：**

1. **CDN 企业级多重备份加载（必须严格按此实现）：**

   ```html
   <!DOCTYPE html>
   <html lang="zh">
   <head>
     <meta charset="UTF-8">
     <meta name="viewport" content="width=device-width, initial-scale=1.0">
     <title>{{课程标题}}</title>

     <!-- 预连接CDN加速DNS -->
     <link rel="preconnect" href="https://cdnjs.cloudflare.com">
     <link rel="preconnect" href="https://cdn.jsdelivr.net">
     <link rel="preconnect" href="https://cdn.bootcdn.net">

     <!-- 主CDN: CloudFlare（全球最快） -->
     <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/reveal.min.css">
     <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/theme/black.min.css">

     <style>
       /* 加载屏幕样式 */
       #loading-screen {{
         position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

       /* 页面主样式 */
       html, body {{ width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden; background: #000; }}
       {{你的自定义CSS}}
     </style>

     <script>
       // 🔥 企业级CDN管理器：4重备份自动降级
       var CDNManager = {{
         cdns: [
           {{ name: 'CloudFlare', js: 'https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/reveal.min.js' }},
           {{ name: 'jsDelivr', js: 'https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.min.js' }},
           {{ name: 'BootCDN', js: 'https://cdn.bootcdn.net/ajax/libs/reveal.js/4.4.0/reveal.min.js' }},
           {{ name: 'unpkg', js: 'https://unpkg.com/reveal.js@4.4.0/dist/reveal.js' }}
         ],
         current: 0,
         load: function() {{
           if (this.current >= this.cdns.length) {{
             document.getElementById('loading-screen').innerHTML =
               '<h1>⚠️ 加载失败</h1><p>所有CDN均无法访问</p>' +
               '<button onclick="location.reload()" style="margin-top:20px;padding:10px 30px;' +
               'font-size:18px;background:white;color:#e74c3c;border:none;border-radius:5px;cursor:pointer;">重试</button>';
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
               width: 1920, height: 1080, margin: 0.1, minScale: 0.2, maxScale: 2.0,
               center: true, controls: true, progress: true, hash: true, transition: 'slide'
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

     <div class="reveal">
       <div class="slides">
         <!-- 你的页面内容 -->
       </div>
     </div>
   </body>
   </html>
   ```

2. **CSS 居中与响应式（必须严格执行）：**
   ```css
   /* 确保reveal.js容器正确填充 */
   html, body {{
       width: 100%;
       height: 100%;
       margin: 0;
       padding: 0;
       overflow: hidden;
   }}

   /* 自定义section样式 - 不设置width/height让reveal.js控制 */
   .reveal section {{
       background: {colors['bg_dark']} !important;
       color: {colors['text_primary']} !important;
   }}
   
   .content-wrapper {{
       width: 100%;
       display: flex;
       flex-direction: column;
       justify-content: center;
       align-items: center;
   }}
   ```

3. **reveal.js 初始化（标准配置）：**
   ```javascript
   Reveal.initialize({{
       width: 1920, height: 1080,
       margin: 0.1,
       minScale: 0.2, maxScale: 2.0,
       center: true, /* 使用自带居中 */
       hash: true,
       transition: 'slide'
   }});
   ```

4. **字体规范（严格执行）：**
   - h1: 64-72px（font-weight: 700）
   - h2: 48-56px（font-weight: 600）
   - p, li: 32-40px（line-height: 1.6）
   - 禁止使用小于 32px 的字体

5. **图片槽位生成（每页有图片描述时必须添加）：**

   对于每个 image_description 字段，生成对应的 <img> 标签：

   - left_text_right_image 布局示例：
   ```html
   <div style="flex: 0 0 40%; display: flex; align-items: center;">
     <img
       src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Crect width='400' height='300' fill='%23ecf0f1'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%232c3e50' font-size='18' font-family='Arial'%3E[图片描述前20字]%3C/text%3E%3C/svg%3E"
       alt="[完整的image_description]"
       data-image-slot="[完整的image_description]"
       style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"
     />
   </div>
   ```

   - top_image_bottom_text 布局示例：
   ```html
   <img
     src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='800' height='400'%3E%3Crect width='800' height='400' fill='%23ecf0f1'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%232c3e50' font-size='20' font-family='Arial'%3E[图片描述前20字]%3C/text%3E%3C/svg%3E"
     alt="[完整的image_description]"
     data-image-slot="[完整的image_description]"
     style="width: 100%; max-height: 500px; object-fit: contain; border-radius: 8px; margin-bottom: 40px;"
   />
   ```

**输出格式：**
完整的 HTML 代码，确保：
1. 每页有 image_description 时必须生成对应的 <img> 标签占位
2. 背景使用纯色（{colors['bg_dark']}），不用渐变
3. 字体大小符合规范（≥32px）
4. 内容在 1920x1080 视口内居中，无滚动条
5. 包含 <!DOCTYPE html>，所有 CSS 写在 head style 中

现在请生成完整的 HTML 代码："""

    try:
        # 调用 LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        html_code = response.content.strip()

        # 去除可能的 markdown 代码块标记
        if html_code.startswith("```html"):
            html_code = html_code.split("```html")[1].split("```")[0].strip()
        elif html_code.startswith("```"):
            html_code = html_code.split("```")[1].split("```")[0].strip()

        # 基本验证
        if "<!DOCTYPE html>" not in html_code:
            raise ValueError("生成的代码缺少 DOCTYPE 声明")

        if '<div class="reveal">' not in html_code:
            raise ValueError("生成的代码缺少 reveal.js 容器")

        page_count = html_code.count("<section")
        expected_count = planning['total_pages']

        if page_count != expected_count:
            print(f"⚠️  页面数量不匹配：期望 {expected_count} 页，实际 {page_count} 页")

        print(f"✅ HTML 生成完成：{len(html_code)} 字符，{page_count} 页")

        return {
            **state,
            "html_code": html_code,
            "status": "generation_completed",
            "messages": state.get("messages", []) + messages + [response]
        }

    except Exception as e:
        error_msg = f"HTML 生成失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            **state,
            "error": error_msg,
            "status": "failed"
        }

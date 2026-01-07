"""
统一HTML生成器
合并所有生成器版本为单一高级实现

功能：
- 使用统一布局系统生成HTML
- 智能布局选择
- 页码指示器
- 完整内联样式
- 热插拔图片插槽
"""
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.logger import logger
from ..utils.progress import ProgressTracker
from ..config import config
from .layouts import LayoutGenerator, select_layout, _determine_subject_category

class HTMLGenerator:
    """统一HTML生成器"""
    
    def __init__(self, max_workers: int = 4):
        from .image_generator import ImageGenerator
        self.image_generator = ImageGenerator()
    
    def generate(self, state: Dict) -> Dict:
        """生成完整的HTML幻灯片"""
        logger.info("🎨 HTML Generator: 开始生成课件...")
        
        planning = state.get('planning')
        user_input = state.get('user_input')
        
        if not planning:
            logger.error("缺少 planning 数据")
            return {**state, "error": "缺少planning数据", "status": "failed"}
        
        # 1. 数据准备
        slides = planning.get('slides', [])
        deck_pages = planning.get('deck_content', {}).get('pages', [])
        source_pages = deck_pages if deck_pages else planning.get('pages', [])
        if not source_pages and slides:
             from .planner import _convert_slides_to_pages
             source_pages = _convert_slides_to_pages(slides)

        total_pages = len(source_pages)
        subject = planning.get('subject', '')
        major = user_input.get('major', '')
        
        logger.info(f"总页数: {total_pages}, 主题: {subject}, 专业: {major}")
        
        # 2. 生成图片资源
        logger.info("   🚀 正在生成图片资源...")
        assets_map = self.image_generator.generate_images_for_pages(source_pages)
        logger.info(f"   ✅ 资源准备完成，获取到 {len(assets_map)} 张图片")
        
        # 3. 页面组装
        style = planning.get('style_config', planning.get('style', {}))
        teaching_scene = planning.get('teaching_request', {}).get('teaching_scene', 'theory')
        colors = style.get('color', self._get_colors(user_input, teaching_scene))
        
        layout_gen = LayoutGenerator(colors)
        html_parts = []
        progress = ProgressTracker(total_pages, "组装页面")
        
        for i, page in enumerate(source_pages):
            try:
                page_num = page.get('page_num', i + 1)
                if page_num in assets_map:
                    page['image_url'] = assets_map[page_num]
                
                # 生成页面 HTML
                html = self._generate_page(
                    page, layout_gen, total_pages, 
                    subject=subject, major=major, # 传入 major
                    knowledge_points=planning.get('knowledge_points', [])
                )
                html_parts.append(html)
                progress.update()
            except Exception as e:
                logger.error(f"页面 {i+1} 组装失败: {e}")
                html_parts.append(self._error_page(i+1))
        
        # 4. 合并输出
        final_html = self._build_html(html_parts, planning, colors, major)
        
        logger.info("✅ HTML生成完成！")
        
        return {
            **state,
            "html_code": final_html,
            "final_html": final_html,
            "status": "completed"
        }
    
    def _get_colors(self, user_input: Dict, teaching_scene: str = 'theory') -> Dict:
        """获取配色方案"""
        major = user_input.get('major', '')
        colors = config.get_colors_for_major(major)
        if teaching_scene == 'practice':
            colors = {**colors, 'accent': '#27ae60'}
        elif teaching_scene == 'safety':
            colors = {**colors, 'accent': '#e74c3c'}
        return colors
    
    def _generate_page(
        self, page: Dict, layout_gen: LayoutGenerator, total_pages: int,
        subject: str = '', major: str = '', knowledge_points: List = None
    ) -> str:
        """生成单个页面"""
        page_type = page.get('type', page.get('slide_type', 'concept'))
        page_num = page.get('page_num', page.get('index', 1))
        
        content = {
            'title': page.get('title', '标题'),
            'subtitle': page.get('subtitle', ''),
            'bullets': page.get('content', []) or page.get('key_points', []) or page.get('bullets', []),
            'image_description': page.get('image_description', ''),
            'page_num': page_num,
            'total_pages': total_pages,
            'notes': page.get('notes') or page.get('speaker_notes'),
            'asset_type': page.get('asset_type', 'image'),
            'assets': page.get('assets', []),
            'slide_type': page_type,
            'subject': subject,
            'major': major, # 注入 major
            'knowledge_points': knowledge_points or [],
            'layout': page.get('layout', {}).get('template') if isinstance(page.get('layout'), dict) else page.get('layout'),
            'image_url': page.get('image_url')
        }
        
        if content['layout'] and content['layout'] in LayoutGenerator.AVAILABLE_LAYOUTS:
            layout_name = content['layout']
        else:
            has_image = bool(content.get('image_url') or content['image_description'])
            layout_name = select_layout(page_type, content, has_image)
        
        slide_html = layout_gen.generate(layout_name, content)
        
        if subject and page_num > 1:
            slide_html = self._add_header(slide_html, subject, layout_gen.colors)
        if content['notes']:
            slide_html = self._add_notes(slide_html, content['notes'])
            
        slide_html = self._add_page_indicator(slide_html, page_num, total_pages)
        return slide_html
    
    def _add_header(self, html: str, subject: str, colors: Dict) -> str:
        """添加页眉"""
        header = f'''
    <div class="page-header" style="position: absolute; top: 30px; left: 80px; font-size: 18pt; color: {colors.get('accent', '#7f8c8d')}; opacity: 0.7;">
        {subject}
    </div>
'''
        insert_pos = html.find('>')
        if insert_pos != -1:
            return html[:insert_pos+1] + header + html[insert_pos+1:]
        return html
    
    def _add_notes(self, html: str, notes: str) -> str:
        """添加隐藏的教师备注"""
        notes_html = f'''
    <div class="speaker-notes" style="display: none;" data-notes="{notes}">
        <!-- 教师备注：{notes} -->
    </div>
'''
        last_div = html.rfind('</div>')
        if last_div != -1:
            return html[:last_div] + notes_html + html[last_div:]
        return html
    
    def _add_page_indicator(self, html: str, page_num: int, total: int) -> str:
        """添加页码指示器"""
        indicator = f'''
    <div class="page-indicator" style="position: absolute; bottom: 40px; right: 60px; font-size: 24pt; color: rgba(255,255,255,0.6);">
        <span class="current" style="font-weight: 700; font-size: 32pt;">{str(page_num).zfill(2)}</span>
        <span class="divider" style="margin: 0 8px; opacity: 0.5;">/</span>
        <span class="total">{str(total).zfill(2)}</span>
    </div>
'''
        last_div = html.rfind('</div>')
        if last_div != -1:
            return html[:last_div] + indicator + html[last_div:]
        return html
    
    def _error_page(self, page_num: int) -> str:
        """错误页面"""
        return f'''
<div class="slide" style="background: #1a252f; display: flex; flex-direction: column; justify-content: center; align-items: center;">
    <h1 style="color: #e74c3c; font-size: 72pt;">⚠️ 页面生成失败</h1>
    <p style="font-size: 32pt; color: #95a5a6;">页面 {page_num}</p>
</div>
'''
    
    def _build_html(self, parts: List[str], planning: Dict, colors: Dict, major: str = '') -> str:
        """构建完整HTML文档"""
        title = planning.get('deck_title') or planning.get('course_title', '课程')
        slides = '\n        '.join(parts)
        
        # 确定学科类别
        category = _determine_subject_category(major).value
        styles = self._generate_styles(colors)
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
    <style>
{styles}
    </style>
</head>
<body class="subject-{category}">
    <div class="presentation-container">
        <div class="presentation">
            {slides}
        </div>
    </div>
    
    <script>
        // 响应式缩放
        function scalePresentation() {{
            const container = document.querySelector('.presentation-container');
            const presentation = document.querySelector('.presentation');
            const slideWidth = 1920;
            const slideHeight = 1080;
            
            const windowWidth = window.innerWidth;
            const windowHeight = window.innerHeight;
            
            // 计算缩放比例（取较小值以确保完整显示）
            const scaleX = windowWidth / slideWidth;
            const scaleY = windowHeight / slideHeight;
            const scale = Math.min(scaleX, scaleY, 1); // 最大不超过1
            
            presentation.style.transform = `scale(${{scale}})`;
            presentation.style.transformOrigin = 'center center';
            
            // 居中容器
            container.style.width = (slideWidth * scale) + 'px';
            container.style.height = (slideHeight * scale) + 'px';
        }}
        
        window.addEventListener('resize', scalePresentation);
        window.addEventListener('load', scalePresentation);
        
        // 幻灯片导航
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        const totalSlides = slides.length;
        
        function showSlide(n) {{
            slides.forEach((s, i) => s.style.display = i === n ? 'flex' : 'none');
            currentSlide = n;
            updateProgress();
        }}
        
        function updateProgress() {{
            const bar = document.querySelector('.progress-bar');
            if (bar) bar.style.width = ((currentSlide + 1) / totalSlides * 100) + '%';
        }}
        
        function nextSlide() {{ showSlide((currentSlide + 1) % totalSlides); }}
        function prevSlide() {{ showSlide((currentSlide - 1 + totalSlides) % totalSlides); }}
        
        document.addEventListener('keydown', e => {{
            if (e.key === 'ArrowRight' || e.key === ' ') nextSlide();
            if (e.key === 'ArrowLeft') prevSlide();
            if (e.key === 'f' || e.key === 'F') document.documentElement.requestFullscreen?.();
            if (e.key === 'Home') showSlide(0);
            if (e.key === 'End') showSlide(totalSlides - 1);
        }});
        
        document.addEventListener('click', e => {{
            if (e.clientX > window.innerWidth / 2) nextSlide();
            else prevSlide();
        }});
        
        showSlide(0);
        
        window.fillImageSlot = function(slotId, imageUrl) {{
            const slot = document.querySelector(`[data-slot-id="${{slotId}}"]`);
            if (slot) {{
                slot.style.backgroundImage = `url(${{imageUrl}})`;
                slot.style.backgroundSize = 'cover';
                slot.style.backgroundPosition = 'center';
                slot.querySelector('.slot-placeholder')?.remove();
            }}
        }};
        
        window.getSlotInfo = function() {{
            return Array.from(document.querySelectorAll('[data-slot-id]')).map(el => ({{
                id: el.dataset.slotId,
                size: el.dataset.slotSize,
                prompt: el.dataset.prompt
            }}));
        }};
        
        // 导出模式（用于截图/PDF）
        window.exportMode = function(enable = true) {{
            const presentation = document.querySelector('.presentation');
            if (enable) {{
                presentation.style.transform = 'none';
                document.querySelector('.presentation-container').style.width = '1920px';
                document.querySelector('.presentation-container').style.height = '1080px';
            }} else {{
                scalePresentation();
            }}
        }};
    </script>
</body>
</html>'''
    
    def _generate_styles(self, colors: Dict) -> str:
        """生成CSS样式 (含学科特效 + 响应式)"""
        primary = colors.get('primary', '#2c3e50')
        secondary = colors.get('secondary', '#34495e')
        accent = colors.get('accent', '#7f8c8d')
        text = colors.get('text', '#ecf0f1')
        background = colors.get('background', '#1a252f')
        warning = colors.get('warning', '#e74c3c')
        
        return f'''
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        html, body {{
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}
        
        body {{
            font-family: 'Microsoft YaHei', 'PingFang SC', -apple-system, sans-serif;
            background: #0a0a0a;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        
        /* 响应式容器 */
        .presentation-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }}
        
        /* 学科专属背景纹理 */
        body.subject-engineering .presentation {{
            background-image: 
                linear-gradient({primary}10 1px, transparent 1px),
                linear-gradient(90deg, {primary}10 1px, transparent 1px);
            background-size: 40px 40px;
        }}
        
        body.subject-medical .presentation {{
             background-image: radial-gradient({primary}15 2px, transparent 2px);
             background-size: 30px 30px;
        }}

        body.subject-arts .presentation {{
             background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJub25lIiAvPjxjaXJjbGUgY3g9IjUwIiBjeT0iNTAiIHI9IjQwIiBzdHJva2U9InJnYmEoMjAwLDIwMCwyMDAsMC4xKSIgc3Ryb2tlLXdpZHRoPSIyIiBmaWxsPSJub25lIiAvPjwvc3ZnPg==');
             background-size: 100px 100px;
        }}

        body.subject-business .presentation {{
             background-image: repeating-linear-gradient(45deg, {primary}08 0, {primary}08 1px, transparent 0, transparent 50%);
             background-size: 30px 30px;
        }}
        
        body.subject-science .presentation {{
             background-image:
                radial-gradient({primary}10 15%, transparent 16%),
                radial-gradient({secondary}10 15%, transparent 16%);
             background-size: 60px 60px;
             background-position: 0 0, 30px 30px;
        }}
        
        body.subject-nature .presentation {{
            background-image:
                linear-gradient(120deg, {secondary}15 0%, transparent 100%),
                linear-gradient(-120deg, {primary}15 0%, transparent 100%);
        }}
        
        .presentation {{
            width: 1920px;
            height: 1080px;
            position: relative;
            background-color: {background};
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            /* 初始居中对齐 */
            transform-origin: center center;
        }}
        
        .slide {{
            width: 1920px;
            height: 1080px;
            display: none;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }}
        
        /* 标题 */
        h1 {{ font-size: 72pt; font-weight: 700; line-height: 1.2; }}
        h2 {{ font-size: 54pt; font-weight: 700; line-height: 1.3; }}
        h3 {{ font-size: 42pt; font-weight: 600; line-height: 1.4; }}
        p, li {{ font-size: 28pt; line-height: 1.6; }}
        ul {{ list-style: none; }}
        
        /* 图片插槽 */
        .image-slot {{
            background: linear-gradient(135deg, {secondary}30, {primary}15);
            border: 3px dashed {primary}40;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .image-slot:hover {{
            border-color: {primary};
            transform: scale(1.02);
        }}
        
        .slot-placeholder {{
            display: flex;
            flex-direction: column;
            align-items: center;
            color: {accent};
            opacity: 0.6;
        }}
        
        .slot-placeholder i {{
            font-size: 48px;
            margin-bottom: 10px;
        }}
        
        .slot-label {{
            font-size: 16pt;
            text-align: center;
            max-width: 80%;
        }}
        
        /* 进度条 */
        .progress-bar {{
            position: fixed;
            bottom: 0;
            left: 0;
            height: 4px;
            background: linear-gradient(90deg, {primary}, {secondary});
            transition: width 0.3s ease;
            z-index: 1000;
        }}
        
        /* 打印/导出样式 */
        @media print {{
            body {{
                background: white;
            }}
            .presentation-container {{
                width: 1920px !important;
                height: 1080px !important;
            }}
            .presentation {{
                transform: none !important;
                box-shadow: none;
            }}
            .slide {{
                display: flex !important;
                page-break-after: always;
            }}
        }}
'''

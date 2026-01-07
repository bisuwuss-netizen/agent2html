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
from .layouts import LayoutGenerator, select_layout


class HTMLGenerator:
    """统一HTML生成器"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def generate(self, state: Dict) -> Dict:
        """生成完整的HTML幻灯片（增强版）"""
        logger.info("🎨 HTML Generator: 开始生成课件...")
        
        planning = state.get('planning')
        user_input = state.get('user_input')
        
        if not planning:
            logger.error("缺少 planning 数据")
            return {**state, "error": "缺少planning数据", "status": "failed"}
        
        pages = planning.get('pages', [])
        total_pages = len(pages)
        
        # 提取增强字段
        subject = planning.get('subject', '')
        knowledge_points = planning.get('knowledge_points', [])
        teaching_scene = planning.get('teaching_scene', 'theory')
        
        logger.info(f"总页数: {total_pages}, 主题: {subject}")
        
        # 获取配色（根据 teaching_scene 调整）
        style = planning.get('style', {})
        colors = style.get('color', self._get_colors(user_input, teaching_scene))
        
        # 创建布局生成器
        layout_gen = LayoutGenerator(colors)
        
        # 并行生成所有页面（传递增强数据）
        html_parts = self._generate_pages(
            pages, layout_gen, total_pages, 
            subject, knowledge_points
        )
        
        # 合并成完整HTML
        final_html = self._build_html(html_parts, planning, colors)
        
        logger.info("✅ HTML生成完成！")
        
        return {
            **state,
            "html_code": final_html,
            "final_html": final_html,
            "status": "completed"
        }
    
    def _get_colors(self, user_input: Dict, teaching_scene: str = 'theory') -> Dict:
        """获取配色方案（根据教学场景调整）"""
        major = user_input.get('major', '')
        colors = config.get_colors_for_major(major)
        
        # 根据教学场景微调配色
        if teaching_scene == 'practice':
            # 实践教学使用更活跃的配色
            colors = {**colors, 'accent': '#27ae60'}  # 绿色强调
        elif teaching_scene == 'safety':
            # 安全教学突出警告色
            colors = {**colors, 'accent': '#e74c3c'}  # 红色强调
        
        return colors
    
    def _generate_pages(
        self,
        pages: List[Dict],
        layout_gen: LayoutGenerator,
        total_pages: int,
        subject: str = '',
        knowledge_points: List = None
    ) -> List[str]:
        """并行生成所有页面（增强版）"""
        futures = {}
        progress = ProgressTracker(len(pages), "生成页面")
        
        for page in pages:
            future = self.executor.submit(
                self._generate_page,
                page, layout_gen, total_pages,
                subject, knowledge_points  # 传递增强数据
            )
            futures[future] = page.get('page_num', 1)
        
        html_parts = [''] * len(pages)
        for future in as_completed(futures):
            page_num = futures[future]
            try:
                html = future.result()
                html_parts[page_num - 1] = html
                progress.update(message=f"页面 {page_num} 完成")
            except Exception as e:
                logger.error(f"页面 {page_num} 生成失败: {e}")
                html_parts[page_num - 1] = self._error_page(page_num)
                progress.update(message=f"页面 {page_num} 失败")
        
        return html_parts
    
    def _generate_page(
        self,
        page: Dict,
        layout_gen: LayoutGenerator,
        total_pages: int,
        subject: str = '',
        knowledge_points: List = None
    ) -> str:
        """生成单个页面（增强版 - 传递更多数据）"""
        page_type = page.get('type', 'concept')
        page_num = page.get('page_num', 1)
        has_image = bool(page.get('image_description'))
        
        # 构建增强版内容数据
        content = {
            'title': page.get('title', '标题'),
            'subtitle': page.get('subtitle', ''),
            'bullets': page.get('content', []) or page.get('key_points', []),
            'image_description': page.get('image_description', ''),
            'page_num': page_num,
            'total_pages': total_pages,
            # 新增字段
            'notes': page.get('notes'),  # 教师备注
            'asset_type': page.get('asset_type', 'image'),  # image/diagram/chart/icon
            'assets': page.get('assets', []),  # 完整资源列表
            'slide_type': page.get('slide_type', page_type),  # 原始类型
            'subject': subject,  # 课程主题（用于页眉）
            'knowledge_points': knowledge_points or [],  # 知识点列表
            'layout': page.get('layout'),  # 指定的布局
        }
        
        # 如果指定了 layout，优先使用
        if content['layout'] and content['layout'] in LayoutGenerator.AVAILABLE_LAYOUTS:
            layout_name = content['layout']
        else:
            # 智能选择布局
            layout_name = select_layout(page_type, content, has_image)
        
        # 生成HTML
        slide_html = layout_gen.generate(layout_name, content)
        
        # 添加页眉（如果有 subject）
        if subject and page_num > 1:  # 封面页不加页眉
            slide_html = self._add_header(slide_html, subject, layout_gen.colors)
        
        # 添加教师备注（隐藏区域）
        if content['notes']:
            slide_html = self._add_notes(slide_html, content['notes'])
        
        # 添加页码
        slide_html = self._add_page_indicator(slide_html, page_num, total_pages)
        
        return slide_html
    
    def _add_header(self, html: str, subject: str, colors: Dict) -> str:
        """添加页眉"""
        header = f'''
    <div class="page-header" style="position: absolute; top: 30px; left: 80px; font-size: 18pt; color: {colors.get('accent', '#7f8c8d')}; opacity: 0.7;">
        {subject}
    </div>
'''
        # 在 slide div 开头后插入
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
    
    def _build_html(self, parts: List[str], planning: Dict, colors: Dict) -> str:
        """构建完整HTML文档"""
        title = planning.get('deck_title') or planning.get('course_title', '课程')
        slides = '\n        '.join(parts)
        styles = self._generate_styles(colors)
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1920, height=1080">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
    <style>
{styles}
    </style>
</head>
<body>
    <div class="presentation">
        {slides}
    </div>
    
    <script>
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
        
        // 键盘/触摸导航
        document.addEventListener('keydown', e => {{
            if (e.key === 'ArrowRight' || e.key === ' ') nextSlide();
            if (e.key === 'ArrowLeft') prevSlide();
            if (e.key === 'f' || e.key === 'F') document.documentElement.requestFullscreen?.();
        }});
        
        document.addEventListener('click', e => {{
            if (e.clientX > window.innerWidth / 2) nextSlide();
            else prevSlide();
        }});
        
        // 初始化
        showSlide(0);
        
        // 图片插槽热插拔支持
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
    </script>
</body>
</html>'''
    
    def _generate_styles(self, colors: Dict) -> str:
        """生成CSS样式"""
        primary = colors.get('primary', '#2c3e50')
        secondary = colors.get('secondary', '#34495e')
        accent = colors.get('accent', '#7f8c8d')
        text = colors.get('text', '#ecf0f1')
        background = colors.get('background', '#1a252f')
        warning = colors.get('warning', '#e74c3c')
        
        return f'''
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Microsoft YaHei', 'PingFang SC', -apple-system, sans-serif;
            background: #0a0a0a;
            overflow: hidden;
        }}
        
        .presentation {{
            width: 1920px;
            height: 1080px;
            margin: 0 auto;
            position: relative;
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
        
        /* 响应式 */
        @media screen and (max-width: 1920px) {{
            .presentation {{
                transform: scale(calc(100vw / 1920));
                transform-origin: top left;
            }}
        }}
'''

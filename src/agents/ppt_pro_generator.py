"""
PPT Pro Generator - 16:9 专业幻灯片生成器
采用固定比例容器 + 栅格化布局 + 智能图片卡槽

增强功能：
1. 支持新版 slides JSON 格式
2. 进度追踪
3. 统一日志
"""
import os
import base64
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..utils.logger import logger
from ..utils.progress import ProgressTracker
from ..config import config


class PPTProGenerator:
    """16:9 专业 PPT 生成器"""

    def __init__(self, llm: ChatOpenAI, max_workers: int = 4):
        self.llm = llm
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # 加载模板
        template_dir = os.path.join(
            os.path.dirname(__file__),
            '..', 'templates', 'ppt_pro'
        )
        self.template_path = os.path.join(template_dir, 'index_template.html')
        self.styles_path = os.path.join(template_dir, 'styles.css')

    def generate(self, state: Dict) -> Dict:
        """生成完整的 16:9 专业幻灯片"""
        logger.info("🎨 PPT Pro Generator: 开始生成 16:9 专业课件...")

        planning = state.get('planning')
        user_input = state.get('user_input')

        if not planning:
            logger.error("缺少 planning 数据")
            return {**state, "error": "缺少planning数据", "status": "failed"}

        # 兼容新旧格式
        if 'slides' in planning:
            pages = planning['pages']  # 使用转换后的 pages
        else:
            pages = planning.get('pages', [])

        logger.info(f"总页数: {len(pages)}")

        # 获取风格配置
        style = planning.get('style', {})
        colors = style.get('color', self._get_default_colors(user_input))

        # 并行生成所有页面
        html_parts = self._generate_pages_parallel(pages, planning, user_input, colors)

        # 合并成完整HTML
        final_html = self._merge_html(html_parts, planning, user_input)

        logger.info("✅ 16:9 专业课件生成完成！")

        return {
            **state,
            "html_code": final_html,
            "status": "html_generated"
        }

    def _get_default_colors(self, user_input: Dict) -> Dict:
        """获取默认配色"""
        major = user_input.get('major', '')
        return config.get_colors_for_major(major)

    def _generate_pages_parallel(
        self,
        pages: List[Dict],
        planning: Dict,
        user_input: Dict,
        colors: Dict
    ) -> List[str]:
        """并行生成所有页面"""
        futures = {}
        progress = ProgressTracker(len(pages), "生成页面")

        for page in pages:
            future = self.executor.submit(
                self._generate_single_page,
                page, planning, user_input, colors
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
                html_parts[page_num - 1] = self._get_error_page(page_num)
                progress.update(message=f"页面 {page_num} 失败")

        return html_parts

    def _generate_single_page(
        self,
        page: Dict,
        planning: Dict,
        user_input: Dict,
        colors: Dict
    ) -> str:
        """生成单个页面"""
        page_type = page.get('type', 'concept')
        has_image = bool(page.get('image_description'))

        # 根据页面类型选择布局模板
        if page_type in ['title', 'cover']:
            return self._generate_cover_page(page, colors)
        elif page_type == 'comparison':
            return self._generate_comparison_page(page, colors)
        elif page_type == 'gallery':
            return self._generate_gallery_page(page, colors)
        elif has_image:
            image_size = page.get('image_size', 'side')
            if image_size == 'top':
                return self._generate_top_image_page(page, colors)
            else:
                return self._generate_split_layout_page(page, colors)
        else:
            return self._generate_text_only_page(page, colors)


    def _generate_cover_page(self, page: Dict, colors: Dict) -> str:
        """生成封面页"""
        page_num = page.get('page_num', 1)
        title = page.get('title', '课程标题')

        # 获取内容
        content = page.get('content', [])
        if isinstance(content, list):
            content_items = content[:4]
        else:
            content_items = [str(content)]

        bullets_html = '\n'.join([f'<li>{item}</li>' for item in content_items])

        # 使用 bg-mesh 类实现高级渐变背景，不再使用内联背景色
        html = f'''
<div class="slide cover-slide bg-mesh">
    <div class="content">
        <div class="tag" style="background: linear-gradient(135deg, {colors.get('primary', '#2c3e50')}, {colors.get('secondary', '#34495e')});">高职教育课件</div>
        <h1 style="background: linear-gradient(135deg, {colors.get('primary', '#2c3e50')} 0%, {colors.get('text', '#ecf0f1')} 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{title}</h1>
        <ul class="objectives" style="color: {colors.get('text', '#ecf0f1')};">
            {bullets_html}
        </ul>
        <div class="meta" style="color: {colors.get('accent', '#7f8c8d')};">授课教师：AI Agent | 2026</div>
    </div>
    <div class="image-slot bg-slot" id="slot-page{page_num}-bg" data-prompt="教育科技背景">
        <i class="ri-image-line"></i>
        <span>封面背景素材位</span>
    </div>
</div>
'''
        return html

    def _generate_split_layout_page(self, page: Dict, colors: Dict) -> str:
        """生成左文右图布局页面"""
        page_num = page.get('page_num', 1)
        title = page.get('title', '标题')
        content = page.get('content', [])
        image_desc = page.get('image_description', '示意图')

        # 处理内容列表
        if isinstance(content, list):
            key_points = content[:4]
        else:
            key_points = [str(content)]

        key_points_html = '\n                '.join([
            f'''<li>
                    <strong>{kp}</strong>
                </li>'''
            for kp in key_points
        ])

        html = f'''
<div class="slide split-layout" style="background: {colors.get('background', '#1a252f')}; color: {colors.get('text', '#ecf0f1')};">
    <div class="text-col">
        <h2 style="color: {colors.get('primary', '#2c3e50')}; border-color: {colors.get('primary', '#2c3e50')};">{title}</h2>
        <ul class="feature-list">
            {key_points_html}
        </ul>
    </div>
    <div class="img-col">
        <div class="image-slot card-slot" id="slot-page{page_num}-chart" data-prompt="{image_desc}">
            <i class="ri-bar-chart-box-line"></i>
            <span>图表/流程图素材位</span>
        </div>
    </div>
</div>
'''
        return html

    def _generate_top_image_page(self, page: Dict, colors: Dict) -> str:
        """生成顶部图片布局页面"""
        page_num = page.get('page_num', 1)
        title = page.get('title', '标题')
        content = page.get('content', [])
        image_desc = page.get('image_description', '示意图')

        # 处理描述文字
        if isinstance(content, list):
            description = '；'.join(content[:3])
        else:
            description = str(content)

        html = f'''
<div class="slide" style="background: {colors.get('background', '#1a252f')}; color: {colors.get('text', '#ecf0f1')}; justify-content: flex-start;">
    <h2 style="color: {colors.get('primary', '#2c3e50')}; border-color: {colors.get('primary', '#2c3e50')}; margin-bottom: 50px;">{title}</h2>
    <div class="image-slot" id="slot-page{page_num}-top" data-prompt="{image_desc}"
         style="width: 100%; max-width: 1200px; height: 500px; margin-bottom: 40px;">
        <i class="ri-image-line"></i>
        <span>横向图片素材位</span>
    </div>
    <p style="font-size: 32px; text-align: center; max-width: 1000px;">{description}</p>
</div>
'''
        return html

    def _generate_text_only_page(self, page: Dict, colors: Dict) -> str:
        """生成纯文字页面（网格布局）"""
        page_num = page.get('page_num', 1)
        title = page.get('title', '标题')
        content = page.get('content', [])
        page_type = page.get('type', 'concept')

        # 确保 content 是列表
        if isinstance(content, str):
            content = [content]

        # 根据页面类型选择不同的布局
        if page_type == 'warning':
            return self._generate_warning_page(page, colors)
        elif page_type == 'steps':
            return self._generate_steps_page(page, colors)
        elif page_type == 'summary':
            return self._generate_summary_page(page, colors)

        # 默认网格布局
        grid_items = '\n            '.join([
            f'''<div class="grid-item" style="background: {colors.get('secondary', '#34495e')};">
                <div class="icon"><i class="ri-lightbulb-line" style="color: {colors.get('primary', '#2c3e50')};"></i></div>
                <p style="color: {colors.get('text', '#ecf0f1')};">{kp}</p>
            </div>'''
            for kp in content[:6]
        ])

        html = f'''
<div class="slide gallery-slide" style="background: {colors.get('background', '#1a252f')}; color: {colors.get('text', '#ecf0f1')};">
    <h2 style="color: {colors.get('primary', '#2c3e50')};">{title}</h2>
    <div class="grid-layout">
        {grid_items}
    </div>
</div>
'''
        return html

    def _generate_warning_page(self, page: Dict, colors: Dict) -> str:
        """生成警告页面"""
        title = page.get('title', '安全注意事项')
        content = page.get('content', [])

        if isinstance(content, str):
            content = [content]

        items_html = '\n            '.join([
            f'''<div class="warning-item" style="background: {colors.get('warning', '#e74c3c')}20; border-left: 4px solid {colors.get('warning', '#e74c3c')}; padding: 20px; margin: 10px 0;">
                <i class="ri-alert-line" style="color: {colors.get('warning', '#e74c3c')};"></i>
                <span style="color: {colors.get('text', '#ecf0f1')};">{item}</span>
            </div>'''
            for item in content[:6]
        ])

        return f'''
<div class="slide" style="background: {colors.get('background', '#1a252f')}; padding: 60px;">
    <h2 style="color: {colors.get('warning', '#e74c3c')}; text-align: center;">⚠️ {title}</h2>
    <div class="warning-list" style="max-width: 1200px; margin: 40px auto;">
        {items_html}
    </div>
</div>
'''

    def _generate_steps_page(self, page: Dict, colors: Dict) -> str:
        """生成步骤页面"""
        title = page.get('title', '操作步骤')
        content = page.get('content', [])

        if isinstance(content, str):
            content = [content]

        steps_html = '\n            '.join([
            f'''<div class="step-item" style="display: flex; align-items: center; margin: 20px 0;">
                <div class="step-num" style="width: 60px; height: 60px; background: {colors.get('primary', '#2c3e50')}; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: bold; color: white; margin-right: 30px;">{i+1}</div>
                <div class="step-text" style="font-size: 32px; color: {colors.get('text', '#ecf0f1')};">{step}</div>
            </div>'''
            for i, step in enumerate(content[:6])
        ])

        return f'''
<div class="slide" style="background: {colors.get('background', '#1a252f')}; padding: 60px;">
    <h2 style="color: {colors.get('primary', '#2c3e50')};">{title}</h2>
    <div class="steps-container" style="max-width: 1200px; margin: 40px auto;">
        {steps_html}
    </div>
</div>
'''

    def _generate_comparison_page(self, page: Dict, colors: Dict) -> str:
        """生成对比表格页面"""
        title = page.get('title', '对比分析')
        content = page.get('content', [])

        if isinstance(content, str):
            content = [content]

        # 解析表格行 (假设内容用 | 分隔)
        rows_html = []
        for i, row_text in enumerate(content):
            cols = row_text.split('|')
            cols = [c.strip() for c in cols if c.strip()]
            
            if not cols:
                continue

            # 第一行作为表头
            if i == 0 and len(content) > 1:
                col_tags = 'th'
            else:
                col_tags = 'td'
            
            # 生成单元格
            cells = []
            for col in cols:
                cells.append(f'<{col_tags}>{col}</{col_tags}>')
            
            rows_html.append(f'<tr>{"".join(cells)}</tr>')

        table_html = '\n'.join(rows_html)

        return f'''
<div class="slide" style="background: {colors.get('background', '#1a252f')}; padding: 60px;">
    <h2 style="color: {colors.get('primary', '#2c3e50')}; text-align: center; margin-bottom: 40px;">{title}</h2>
    <div class="comparison-container">
        <table class="compare-table">
            {table_html}
        </table>
    </div>
</div>
'''

    def _generate_gallery_page(self, page: Dict, colors: Dict) -> str:
        """生成图片墙/拼图页面"""
        title = page.get('title', '图集展示')
        content = page.get('content', [])
        
        if isinstance(content, str):
            content = [content]

        # 生成图片网格项
        # 即使没有足够的 assets，也生成占位符
        items_html = []
        for i, caption in enumerate(content[:4]): # 最多4张图
            items_html.append(f'''
            <div class="gallery-item" style="border: 2px solid {colors.get('primary', '#2c3e50')}20;">
                <div class="image-slot" style="width: 100%; height: 100%; border: none; border-radius: 0;" data-prompt="{caption}">
                   <i class="ri-image-2-line" style="font-size: 48px; opacity: 0.5;"></i>
                </div>
                <div class="gallery-caption">{caption}</div>
            </div>
            ''')
        
        return f'''
<div class="slide" style="background: {colors.get('background', '#1a252f')}; padding: 60px;">
    <h2 style="color: {colors.get('primary', '#2c3e50')}; margin-bottom: 30px;">{title}</h2>
    <div class="gallery-grid">
        {''.join(items_html)}
    </div>
</div>
'''

    def _generate_summary_page(self, page: Dict, colors: Dict) -> str:
        """生成总结页面"""
        title = page.get('title', '课程总结')
        content = page.get('content', [])

        if isinstance(content, str):
            content = [content]

        summary_html = '\n            '.join([
            f'''<div class="summary-item" style="background: {colors.get('secondary', '#34495e')}; padding: 25px 35px; border-radius: 12px; margin: 15px;">
                <i class="ri-check-double-line" style="color: {colors.get('primary', '#2c3e50')}; margin-right: 15px;"></i>
                <span style="color: {colors.get('text', '#ecf0f1')}; font-size: 28px;">{item}</span>
            </div>'''
            for item in content[:6]
        ])

        return f'''
<div class="slide" style="background: {colors.get('background', '#1a252f')}; padding: 60px;">
    <h2 style="color: {colors.get('primary', '#2c3e50')};">📋 {title}</h2>
    <div class="summary-grid" style="display: flex; flex-wrap: wrap; justify-content: center; max-width: 1400px; margin: 40px auto;">
        {summary_html}
    </div>
</div>
'''

    def _get_error_page(self, page_num: int) -> str:
        """生成错误页面"""
        return f'''
<div class="slide" style="background: #1a252f; justify-content: center; align-items: center;">
    <h1 style="color: #e74c3c; font-size: 80px;">⚠️ 页面生成失败</h1>
    <p style="font-size: 36px; color: #95a5a6;">页面 {page_num}</p>
</div>
'''

    def _merge_html(self, html_parts: List[str], planning: Dict, user_input: Dict) -> str:
        """合并所有HTML片段"""
        # 读取模板和样式
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template = f.read()

            with open(self.styles_path, 'r', encoding='utf-8') as f:
                styles = f.read()
        except FileNotFoundError as e:
            logger.error(f"模板文件不存在: {e}")
            # 使用内置模板
            return self._generate_fallback_html(html_parts, planning)

        # Base64 编码样式（内联到 HTML）
        styles_base64 = base64.b64encode(styles.encode('utf-8')).decode('utf-8')

        # 合并所有幻灯片
        slides_content = '\n        '.join(html_parts)

        # 获取标题
        course_title = planning.get('deck_title') or planning.get('course_title', '课程')

        # 填充模板
        html = template.replace('{{ course_title }}', course_title)
        html = html.replace('{{ total_pages }}', str(len(html_parts)))
        html = html.replace('{{ styles_base64 }}', styles_base64)
        html = html.replace('{{ slides_content }}', slides_content)

        return html

    def _generate_fallback_html(self, html_parts: List[str], planning: Dict) -> str:
        """生成备用 HTML（当模板不存在时）"""
        course_title = planning.get('deck_title') or planning.get('course_title', '课程')
        slides_content = '\n'.join(html_parts)

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{course_title}</title>
    <link href="https://cdn.jsdelivr.net/npm/remixicon/fonts/remixicon.css" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Microsoft YaHei', sans-serif; background: #1a252f; }}
        .slide {{ width: 1920px; height: 1080px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 80px; }}
        h1 {{ font-size: 72px; margin-bottom: 40px; }}
        h2 {{ font-size: 48px; margin-bottom: 30px; }}
        p {{ font-size: 32px; }}
        ul {{ list-style: none; }}
        li {{ font-size: 28px; margin: 15px 0; }}
        .grid-layout {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; }}
        .grid-item {{ padding: 30px; border-radius: 12px; }}
    </style>
</head>
<body>
    {slides_content}
</body>
</html>'''

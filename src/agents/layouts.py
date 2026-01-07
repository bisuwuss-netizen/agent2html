"""
统一布局模板系统
包含所有布局类型（P0、P1、P2全部实现）
支持热插拔图片插槽

核心规格（基于精品PPT分析）：
- 画布尺寸: 1920 x 1080 px (16:9)
- 安全边距: 80px
- 内容区域: 1760 x 920 px
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


# ============================================================================
# 标准插槽尺寸
# ============================================================================

class SlotSize(Enum):
    """标准插槽尺寸（基于精品PPT分析）"""
    FULL = (1920, 1080)      # 全屏背景（作为背景层，不遮挡内容）
    HERO = (1200, 600)       # 主图（顶部横图）
    HALF = (800, 700)        # 左右分栏图
    CARD_LG = (500, 400)     # 大卡片内图
    CARD_MD = (400, 300)     # 中卡片内图
    CARD_SM = (300, 200)     # 小卡片内图
    THUMB = (200, 150)       # 缩略图
    ICON = (80, 80)          # 图标

    @property
    def width(self) -> int:
        return self.value[0]
    
    @property
    def height(self) -> int:
        return self.value[1]


# ============================================================================
# 字体规范
# ============================================================================

@dataclass
class FontSpec:
    """字体规格"""
    size: int        # pt
    line_height: float
    weight: int = 400


class FontScale:
    """字体梯度（基于精品PPT分析）"""
    TITLE_XL = FontSpec(72, 1.2, 700)    # 封面主标题
    TITLE_LG = FontSpec(54, 1.3, 700)    # 页面标题
    TITLE_MD = FontSpec(42, 1.4, 600)    # 二级标题
    BODY_LG = FontSpec(32, 1.6, 400)     # 大号正文
    BODY_MD = FontSpec(24, 1.6, 400)     # 标准正文
    BODY_SM = FontSpec(18, 1.5, 400)     # 注释文字
    CAPTION = FontSpec(14, 1.4, 400)     # 图注


# ============================================================================
# 布局生成器 - 全部布局类型
# ============================================================================

class LayoutGenerator:
    """布局HTML生成器 - 包含所有P0/P1/P2布局"""
    
    # 所有可用布局
    AVAILABLE_LAYOUTS = [
        # P0 - 必须实现
        'cover', 'timeline', 'cards_3col', 'cards_4col', 
        'image_wall_2x2', 'image_wall_2x3',
        # P1 - 建议实现  
        'quote', 'stats', 'process_flow', 'before_after',
        # P2 - 可选实现
        'masonry', 'circular', 'pyramid',
        # 基础布局
        'split', 'top_image', 'steps', 'warning', 'summary', 'comparison'
    ]
    
    def __init__(self, colors: Dict):
        self.colors = colors
    
    def generate(self, layout_name: str, content: Dict) -> str:
        """根据布局名称生成HTML"""
        generator_map = {
            # P0 基础布局
            "cover": self._gen_cover,
            "timeline": self._gen_timeline,
            "cards_3col": self._gen_cards_3col,
            "cards_4col": self._gen_cards_4col,
            "image_wall_2x2": self._gen_image_wall_2x2,
            "image_wall_2x3": self._gen_image_wall_2x3,
            # P1 增强布局
            "quote": self._gen_quote,
            "stats": self._gen_stats,
            "process_flow": self._gen_process_flow,
            "before_after": self._gen_before_after,
            # P2 高级布局
            "masonry": self._gen_masonry,
            "circular": self._gen_circular,
            "pyramid": self._gen_pyramid,
            # 基础布局
            "split": self._gen_split,
            "top_image": self._gen_top_image,
            "steps": self._gen_steps,
            "warning": self._gen_warning,
            "summary": self._gen_summary,
            "comparison": self._gen_comparison,
        }
        
        generator = generator_map.get(layout_name, self._gen_default)
        return generator(content)
    
    def _create_slot(self, slot_id: str, size: SlotSize, prompt: str, 
                     extra_style: str = "", is_background: bool = False,
                     asset_type: str = "image") -> str:
        """
        创建热插拔图片插槽
        
        Args:
            slot_id: 插槽唯一标识，用于后续图片匹配
            size: 插槽尺寸
            prompt: 图片描述/提示词
            extra_style: 额外CSS样式
            is_background: 是否为背景插槽（z-index: 0）
            asset_type: 资源类型（image/diagram/chart/icon）
        """
        z_index = "z-index: 0;" if is_background else "z-index: 1;"
        position = "position: absolute; top: 0; left: 0;" if is_background else ""
        
        # 根据资源类型选择图标
        icon_map = {
            'image': 'ri-image-add-line',
            'diagram': 'ri-flow-chart',
            'chart': 'ri-bar-chart-box-line',
            'icon': 'ri-shape-line',
        }
        icon = icon_map.get(asset_type, 'ri-image-add-line')
        
        # 类型标签
        type_label = {
            'image': '图片',
            'diagram': '示意图',
            'chart': '图表',
            'icon': '图标',
        }.get(asset_type, '素材')
        
        return f'''<div class="image-slot" 
     data-slot-id="{slot_id}" 
     data-slot-size="{size.name}" 
     data-prompt="{prompt}"
     data-asset-type="{asset_type}"
     style="width: {size.width}px; height: {size.height}px; {z_index} {position} {extra_style}">
    <div class="slot-placeholder">
        <i class="{icon}"></i>
        <span class="slot-label">{prompt[:30]}...</span>
        <span class="slot-type" style="font-size: 12pt; opacity: 0.5; margin-top: 5px;">[{type_label}]</span>
    </div>
</div>'''
    
    # ========================================================================
    # P0 - 必须实现的布局
    # ========================================================================
    
    def _gen_cover(self, content: Dict) -> str:
        """封面页 - 使用CSS渐变背景，无遮挡"""
        title = content.get('title', '课程标题')
        subtitle = content.get('subtitle', '')
        bullets = content.get('bullets', [])
        page_num = content.get('page_num', 1)
        
        bullets_html = '\n'.join([f'<li>{b}</li>' for b in bullets[:4]])
        
        # 封面不使用插槽，直接使用渐变背景
        # 如果需要背景图，通过 fillImageSlot 动态添加
        return f'''
<div class="slide slide-cover" 
     data-slot-id="p{page_num}-bg" 
     data-slot-size="FULL" 
     data-prompt="教育科技封面背景"
     style="background: linear-gradient(135deg, {self.colors['background']} 0%, {self.colors['secondary']}40 50%, {self.colors['primary']}30 100%); position: relative; background-size: cover; background-position: center;">
    <div class="cover-content" style="position: relative; z-index: 10; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; padding: 80px;">
        <div class="tag" style="background: {self.colors['primary']}; padding: 12px 30px; border-radius: 30px; font-size: 20pt; color: white; margin-bottom: 40px;">高职教育课件</div>
        <h1 style="font-size: 72pt; color: {self.colors['text']}; margin-bottom: 30px; text-shadow: 0 4px 20px rgba(0,0,0,0.3);">{title}</h1>
        {f'<p class="subtitle" style="font-size: 32pt; color: {self.colors["accent"]}; margin-bottom: 40px;">{subtitle}</p>' if subtitle else ''}
        <ul class="objectives" style="list-style: none; text-align: left; color: {self.colors['text']};">
            {bullets_html}
        </ul>
        <div class="meta" style="color: {self.colors['accent']}; margin-top: 60px; font-size: 22pt;">授课教师：AI Agent | 2026</div>
    </div>
</div>
'''
    
    def _gen_timeline(self, content: Dict) -> str:
        """时间轴布局"""
        title = content.get('title', '流程步骤')
        items = content.get('bullets', [])[:5]
        page_num = content.get('page_num', 1)
        
        items_html = ''
        for i, item in enumerate(items, 1):
            items_html += f'''
            <div class="timeline-item" style="display: flex; align-items: flex-start; margin: 25px 0; position: relative;">
                <div class="timeline-marker" style="min-width: 70px; height: 70px; background: {self.colors['primary']}; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 28pt; font-weight: bold; color: white; z-index: 2;">
                    {i}
                </div>
                <div class="timeline-content" style="flex: 1; margin-left: 30px; background: {self.colors['secondary']}30; border-left: 4px solid {self.colors['primary']}; padding: 25px 35px; border-radius: 0 12px 12px 0;">
                    <p style="color: {self.colors['text']}; font-size: 26pt; margin: 0;">{item}</p>
                </div>
            </div>
'''
        
        return f'''
<div class="slide slide-timeline" style="background: {self.colors['background']}; padding: 80px;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; margin-bottom: 50px; border-left: 6px solid {self.colors['primary']}; padding-left: 25px;">{title}</h2>
    <div class="timeline-container" style="position: relative; max-width: 1400px;">
        <div class="timeline-line" style="position: absolute; left: 35px; top: 35px; bottom: 35px; width: 4px; background: {self.colors['primary']}30;"></div>
        {items_html}
    </div>
</div>
'''
    
    def _gen_cards_3col(self, content: Dict) -> str:
        """三栏卡片布局"""
        title = content.get('title', '核心要点')
        items = content.get('bullets', [])[:3]
        page_num = content.get('page_num', 1)
        icons = ['ri-lightbulb-line', 'ri-settings-3-line', 'ri-shield-check-line']
        
        cards_html = ''
        for i, item in enumerate(items):
            slot = self._create_slot(f"p{page_num}-card{i+1}", SlotSize.CARD_MD, item[:20])
            cards_html += f'''
            <div class="card" style="background: {self.colors['secondary']}20; border: 2px solid {self.colors['primary']}20; border-radius: 20px; padding: 40px; text-align: center;">
                <div class="card-icon" style="color: {self.colors['primary']}; font-size: 48px; margin-bottom: 20px;">
                    <i class="{icons[i % len(icons)]}"></i>
                </div>
                {slot}
                <h3 style="color: {self.colors['text']}; font-size: 28pt; margin-top: 25px;">{item}</h3>
            </div>
'''
        
        return f'''
<div class="slide slide-cards-3col" style="background: {self.colors['background']}; padding: 80px;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; text-align: center; margin-bottom: 50px;">{title}</h2>
    <div class="cards-container" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; max-width: 1600px; margin: 0 auto;">
        {cards_html}
    </div>
</div>
'''
    
    def _gen_cards_4col(self, content: Dict) -> str:
        """四栏卡片布局"""
        title = content.get('title', '特点特性')
        items = content.get('bullets', [])[:4]
        icons = ['ri-star-line', 'ri-heart-line', 'ri-rocket-line', 'ri-medal-line']
        
        cards_html = ''
        for i, item in enumerate(items):
            cards_html += f'''
            <div class="card-mini" style="background: {self.colors['secondary']}15; padding: 35px 25px; border-radius: 16px; text-align: center;">
                <div class="icon-circle" style="background: linear-gradient(135deg, {self.colors['primary']}, {self.colors['secondary']}); width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 25px;">
                    <i class="{icons[i % len(icons)]}" style="font-size: 36px; color: white;"></i>
                </div>
                <p style="color: {self.colors['text']}; font-size: 22pt;">{item}</p>
            </div>
'''
        
        return f'''
<div class="slide slide-cards-4col" style="background: {self.colors['background']}; padding: 80px;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; text-align: center; margin-bottom: 50px;">{title}</h2>
    <div class="cards-container" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 30px; max-width: 1700px; margin: 0 auto;">
        {cards_html}
    </div>
</div>
'''
    
    def _gen_image_wall_2x2(self, content: Dict) -> str:
        """图片墙 2x2"""
        title = content.get('title', '图片展示')
        captions = content.get('bullets', [])[:4]
        page_num = content.get('page_num', 1)
        
        # 补齐4个标题
        while len(captions) < 4:
            captions.append(f"图片{len(captions)+1}")
        
        items_html = ''
        for i, cap in enumerate(captions):
            slot = self._create_slot(f"p{page_num}-wall{i+1}", SlotSize.CARD_LG, cap)
            items_html += f'''
            <div class="wall-item" style="text-align: center;">
                {slot}
                <p style="color: {self.colors['text']}; font-size: 20pt; margin-top: 15px;">{cap}</p>
            </div>
'''
        
        return f'''
<div class="slide slide-image-wall" style="background: {self.colors['background']}; padding: 80px;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; margin-bottom: 40px;">{title}</h2>
    <div class="wall-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 40px; max-width: 1200px; margin: 0 auto;">
        {items_html}
    </div>
</div>
'''
    
    def _gen_image_wall_2x3(self, content: Dict) -> str:
        """图片墙 2x3"""
        title = content.get('title', '案例展示')
        captions = content.get('bullets', [])[:6]
        page_num = content.get('page_num', 1)
        
        while len(captions) < 6:
            captions.append(f"案例{len(captions)+1}")
        
        items_html = ''
        for i, cap in enumerate(captions):
            slot = self._create_slot(f"p{page_num}-wall{i+1}", SlotSize.CARD_SM, cap)
            items_html += f'''
            <div class="wall-item" style="text-align: center;">
                {slot}
                <p style="color: {self.colors['text']}; font-size: 16pt; margin-top: 10px;">{cap}</p>
            </div>
'''
        
        return f'''
<div class="slide slide-image-wall-6" style="background: {self.colors['background']}; padding: 60px;">
    <h2 style="color: {self.colors['primary']}; font-size: 48pt; margin-bottom: 30px;">{title}</h2>
    <div class="wall-grid-6" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 25px; max-width: 1400px; margin: 0 auto;">
        {items_html}
    </div>
</div>
'''
    
    # ========================================================================
    # P1 - 建议实现的布局
    # ========================================================================
    
    def _gen_quote(self, content: Dict) -> str:
        """引用金句布局"""
        quote = content.get('title', '引用内容')
        author = content.get('subtitle', '')
        
        return f'''
<div class="slide slide-quote" style="background: linear-gradient(135deg, {self.colors['background']} 0%, {self.colors['primary']}15 100%); display: flex; align-items: center; justify-content: center;">
    <div class="quote-container" style="max-width: 1400px; text-align: center; padding: 60px;">
        <div class="quote-mark" style="font-size: 150pt; color: {self.colors['primary']}30; font-family: Georgia, serif; line-height: 0.6;">"</div>
        <blockquote style="font-size: 42pt; color: {self.colors['text']}; line-height: 1.6; margin: 30px 0; font-style: italic;">
            {quote}
        </blockquote>
        {f'<cite style="font-size: 28pt; color: {self.colors["accent"]}; display: block; margin-top: 40px;">— {author}</cite>' if author else ''}
    </div>
</div>
'''
    
    def _gen_stats(self, content: Dict) -> str:
        """数据展示布局"""
        title = content.get('title', '数据亮点')
        items = content.get('bullets', [])[:4]
        
        stats_html = ''
        for item in items:
            # 解析 "数字：描述" 格式
            if '：' in item or ':' in item:
                parts = item.replace('：', ':').split(':')
                num, desc = parts[0].strip(), parts[1].strip() if len(parts) > 1 else ''
            else:
                num, desc = item, ''
            
            stats_html += f'''
            <div class="stat-item" style="text-align: center; padding: 40px;">
                <div class="stat-num" style="font-size: 72pt; font-weight: 700; color: {self.colors['primary']}; background: linear-gradient(135deg, {self.colors['primary']}, {self.colors['secondary']}); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{num}</div>
                <div class="stat-desc" style="font-size: 24pt; color: {self.colors['text']}; margin-top: 15px;">{desc}</div>
            </div>
'''
        
        cols = min(len(items), 4) if items else 1
        return f'''
<div class="slide slide-stats" style="background: {self.colors['background']}; padding: 80px; display: flex; flex-direction: column; justify-content: center;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; text-align: center; margin-bottom: 60px;">{title}</h2>
    <div class="stats-grid" style="display: grid; grid-template-columns: repeat({cols}, 1fr); gap: 40px; max-width: 1600px; margin: 0 auto;">
        {stats_html}
    </div>
</div>
'''
    
    def _gen_process_flow(self, content: Dict) -> str:
        """流程图布局 - 横向箭头连接"""
        title = content.get('title', '流程步骤')
        steps = content.get('bullets', [])[:5]
        
        steps_html = ''
        for i, step in enumerate(steps):
            arrow = f'<div class="arrow" style="color: {self.colors["primary"]}; font-size: 48px;">→</div>' if i < len(steps) - 1 else ''
            steps_html += f'''
            <div class="flow-step" style="display: flex; align-items: center;">
                <div class="step-box" style="background: linear-gradient(135deg, {self.colors['primary']}20, {self.colors['secondary']}20); border: 2px solid {self.colors['primary']}; border-radius: 16px; padding: 30px 40px; min-width: 200px; text-align: center;">
                    <div class="step-num" style="font-size: 24pt; color: {self.colors['primary']}; font-weight: 700; margin-bottom: 10px;">Step {i+1}</div>
                    <div class="step-text" style="font-size: 22pt; color: {self.colors['text']};">{step}</div>
                </div>
                {arrow}
            </div>
'''
        
        return f'''
<div class="slide slide-process" style="background: {self.colors['background']}; padding: 80px;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; text-align: center; margin-bottom: 60px;">{title}</h2>
    <div class="process-container" style="display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 20px;">
        {steps_html}
    </div>
</div>
'''
    
    def _gen_before_after(self, content: Dict) -> str:
        """对比前后布局"""
        title = content.get('title', '对比分析')
        items = content.get('bullets', [])
        page_num = content.get('page_num', 1)
        
        # 分成两组
        half = len(items) // 2
        before_items = items[:half] if half > 0 else items[:2]
        after_items = items[half:] if half > 0 else items[2:4]
        
        before_html = '\n'.join([f'<li style="margin: 15px 0; font-size: 24pt; color: {self.colors["text"]};">{i}</li>' for i in before_items])
        after_html = '\n'.join([f'<li style="margin: 15px 0; font-size: 24pt; color: {self.colors["text"]};">{i}</li>' for i in after_items])
        
        before_slot = self._create_slot(f"p{page_num}-before", SlotSize.CARD_MD, "改进前状态")
        after_slot = self._create_slot(f"p{page_num}-after", SlotSize.CARD_MD, "改进后状态")
        
        return f'''
<div class="slide slide-before-after" style="background: {self.colors['background']}; padding: 80px;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; text-align: center; margin-bottom: 50px;">{title}</h2>
    <div class="comparison-container" style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 40px; max-width: 1600px; margin: 0 auto; align-items: start;">
        <div class="before-section" style="background: {self.colors['warning']}15; border: 2px solid {self.colors['warning']}; border-radius: 20px; padding: 40px;">
            <h3 style="color: {self.colors['warning']}; font-size: 36pt; text-align: center; margin-bottom: 30px;">❌ Before</h3>
            {before_slot}
            <ul style="list-style: none; padding: 0; margin-top: 25px;">{before_html}</ul>
        </div>
        <div class="arrow" style="font-size: 72pt; color: {self.colors['primary']}; align-self: center;">→</div>
        <div class="after-section" style="background: {self.colors['primary']}15; border: 2px solid {self.colors['primary']}; border-radius: 20px; padding: 40px;">
            <h3 style="color: {self.colors['primary']}; font-size: 36pt; text-align: center; margin-bottom: 30px;">✅ After</h3>
            {after_slot}
            <ul style="list-style: none; padding: 0; margin-top: 25px;">{after_html}</ul>
        </div>
    </div>
</div>
'''
    
    # ========================================================================
    # P2 - 高级布局
    # ========================================================================
    
    def _gen_masonry(self, content: Dict) -> str:
        """瀑布流布局"""
        title = content.get('title', '瀑布流展示')
        items = content.get('bullets', [])[:6]
        page_num = content.get('page_num', 1)
        
        # 不同大小的卡片
        sizes = [SlotSize.CARD_LG, SlotSize.CARD_MD, SlotSize.CARD_SM, 
                 SlotSize.CARD_MD, SlotSize.CARD_LG, SlotSize.CARD_SM]
        spans = ['span 2', 'span 1', 'span 1', 'span 1', 'span 2', 'span 1']
        
        items_html = ''
        for i, item in enumerate(items):
            slot = self._create_slot(f"p{page_num}-mas{i+1}", sizes[i % len(sizes)], item[:20])
            items_html += f'''
            <div class="masonry-item" style="grid-row: {spans[i % len(spans)]}; background: {self.colors['secondary']}15; border-radius: 16px; padding: 20px; overflow: hidden;">
                {slot}
                <p style="color: {self.colors['text']}; font-size: 18pt; margin-top: 15px; text-align: center;">{item}</p>
            </div>
'''
        
        return f'''
<div class="slide slide-masonry" style="background: {self.colors['background']}; padding: 60px;">
    <h2 style="color: {self.colors['primary']}; font-size: 48pt; margin-bottom: 30px;">{title}</h2>
    <div class="masonry-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); grid-auto-rows: 180px; gap: 20px; max-width: 1500px; margin: 0 auto;">
        {items_html}
    </div>
</div>
'''
    
    def _gen_circular(self, content: Dict) -> str:
        """环形图解布局"""
        title = content.get('title', '核心概念')
        items = content.get('bullets', [])[:6]
        center_text = content.get('subtitle', '核心')
        
        # 计算圆形位置
        import math
        radius = 280
        center_x, center_y = 480, 400
        
        items_html = ''
        for i, item in enumerate(items):
            angle = (i * 360 / len(items)) - 90  # 从顶部开始
            rad = math.radians(angle)
            x = center_x + radius * math.cos(rad) - 80
            y = center_y + radius * math.sin(rad) - 40
            
            items_html += f'''
            <div class="circle-item" style="position: absolute; left: {x}px; top: {y}px; width: 160px; height: 80px; background: {self.colors['secondary']}30; border: 2px solid {self.colors['primary']}; border-radius: 12px; display: flex; align-items: center; justify-content: center; text-align: center;">
                <span style="color: {self.colors['text']}; font-size: 18pt;">{item}</span>
            </div>
'''
        
        return f'''
<div class="slide slide-circular" style="background: {self.colors['background']}; padding: 80px;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; margin-bottom: 40px;">{title}</h2>
    <div class="circular-container" style="position: relative; width: 960px; height: 800px; margin: 0 auto;">
        <div class="center-circle" style="position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: 200px; height: 200px; background: linear-gradient(135deg, {self.colors['primary']}, {self.colors['secondary']}); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
            <span style="color: white; font-size: 32pt; font-weight: 700;">{center_text}</span>
        </div>
        {items_html}
    </div>
</div>
'''
    
    def _gen_pyramid(self, content: Dict) -> str:
        """金字塔布局"""
        title = content.get('title', '层次结构')
        items = content.get('bullets', [])[:4]
        
        # 从上到下，宽度递增
        widths = ['40%', '55%', '70%', '85%']
        
        layers_html = ''
        for i, item in enumerate(items):
            w = widths[i] if i < len(widths) else '90%'
            layers_html += f'''
            <div class="pyramid-layer" style="width: {w}; background: linear-gradient(135deg, {self.colors['primary']}{hex(255 - i*40)[2:]}, {self.colors['secondary']}{hex(255 - i*40)[2:]}); padding: 25px 40px; margin: 5px auto; border-radius: 8px; text-align: center;">
                <span style="color: white; font-size: 24pt; font-weight: 600;">{item}</span>
            </div>
'''
        
        return f'''
<div class="slide slide-pyramid" style="background: {self.colors['background']}; padding: 80px;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; text-align: center; margin-bottom: 50px;">{title}</h2>
    <div class="pyramid-container" style="max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column;">
        {layers_html}
    </div>
</div>
'''
    
    # ========================================================================
    # 基础布局
    # ========================================================================
    
    def _gen_split(self, content: Dict) -> str:
        """左右分栏布局"""
        title = content.get('title', '标题')
        bullets = content.get('bullets', [])
        image_desc = content.get('image_description', '示意图')
        page_num = content.get('page_num', 1)
        
        bullets_html = '\n'.join([
            f'<li style="margin: 18px 0; font-size: 26pt; color: {self.colors["text"]};"><strong>{b}</strong></li>'
            for b in bullets[:5]
        ])
        
        slot = self._create_slot(f"p{page_num}-main", SlotSize.HALF, image_desc)
        
        return f'''
<div class="slide slide-split" style="background: {self.colors['background']}; display: flex; padding: 80px; gap: 60px;">
    <div class="text-col" style="flex: 1;">
        <h2 style="color: {self.colors['primary']}; font-size: 54pt; border-left: 6px solid {self.colors['primary']}; padding-left: 25px; margin-bottom: 40px;">{title}</h2>
        <ul style="list-style: none; padding: 0;">
            {bullets_html}
        </ul>
    </div>
    <div class="image-col" style="flex: 1; display: flex; align-items: center; justify-content: center;">
        {slot}
    </div>
</div>
'''
    
    def _gen_top_image(self, content: Dict) -> str:
        """顶部大图布局"""
        title = content.get('title', '标题')
        bullets = content.get('bullets', [])
        image_desc = content.get('image_description', '场景图')
        page_num = content.get('page_num', 1)
        
        desc_text = '；'.join(bullets[:3]) if bullets else ''
        slot = self._create_slot(f"p{page_num}-hero", SlotSize.HERO, image_desc)
        
        return f'''
<div class="slide slide-top-image" style="background: {self.colors['background']}; padding: 80px; display: flex; flex-direction: column; align-items: center;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; margin-bottom: 40px;">{title}</h2>
    {slot}
    <p style="font-size: 28pt; color: {self.colors['text']}; text-align: center; max-width: 1200px; margin-top: 40px;">{desc_text}</p>
</div>
'''
    
    def _gen_steps(self, content: Dict) -> str:
        """步骤布局"""
        title = content.get('title', '操作步骤')
        steps = content.get('bullets', [])[:6]
        
        steps_html = ''
        for i, step in enumerate(steps, 1):
            steps_html += f'''
            <div class="step-item" style="display: flex; align-items: flex-start; margin: 25px 0;">
                <div class="step-num" style="min-width: 70px; height: 70px; background: {self.colors['primary']}; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 32pt; font-weight: bold; color: white; margin-right: 30px;">{i}</div>
                <div class="step-text" style="flex: 1; font-size: 28pt; color: {self.colors['text']}; padding-top: 15px;">{step}</div>
            </div>
'''
        
        return f'''
<div class="slide slide-steps" style="background: {self.colors['background']}; padding: 80px;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; margin-bottom: 50px;">{title}</h2>
    <div class="steps-container" style="max-width: 1400px;">
        {steps_html}
    </div>
</div>
'''
    
    def _gen_warning(self, content: Dict) -> str:
        """安全警告布局"""
        title = content.get('title', '安全注意事项')
        items = content.get('bullets', [])[:6]
        
        items_html = ''
        for item in items:
            items_html += f'''
            <div class="warning-item" style="background: {self.colors['warning']}15; border-left: 5px solid {self.colors['warning']}; padding: 25px 30px; margin: 15px 0; border-radius: 0 12px 12px 0; display: flex; align-items: center;">
                <i class="ri-alert-line" style="color: {self.colors['warning']}; font-size: 28pt; margin-right: 20px;"></i>
                <span style="color: {self.colors['text']}; font-size: 26pt;">{item}</span>
            </div>
'''
        
        return f'''
<div class="slide slide-warning" style="background: {self.colors['background']}; padding: 80px;">
    <h2 style="color: {self.colors['warning']}; font-size: 54pt; text-align: center; margin-bottom: 50px;">
        <i class="ri-error-warning-line" style="margin-right: 20px;"></i>{title}
    </h2>
    <div class="warning-list" style="max-width: 1200px; margin: 0 auto;">
        {items_html}
    </div>
</div>
'''
    
    def _gen_summary(self, content: Dict) -> str:
        """总结回顾布局"""
        title = content.get('title', '课程总结')
        points = content.get('bullets', [])[:6]
        
        points_html = ''
        for point in points:
            points_html += f'''
            <div class="summary-point" style="background: {self.colors['secondary']}20; padding: 25px 35px; border-radius: 12px; margin: 12px; display: inline-flex; align-items: center;">
                <i class="ri-check-double-line" style="color: {self.colors['primary']}; font-size: 28pt; margin-right: 15px;"></i>
                <span style="color: {self.colors['text']}; font-size: 26pt;">{point}</span>
            </div>
'''
        
        return f'''
<div class="slide slide-summary" style="background: {self.colors['background']}; padding: 80px;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; text-align: center; margin-bottom: 50px;">
        <i class="ri-bookmark-line" style="margin-right: 15px;"></i>{title}
    </h2>
    <div class="summary-grid" style="display: flex; flex-wrap: wrap; justify-content: center; max-width: 1500px; margin: 0 auto;">
        {points_html}
    </div>
</div>
'''
    
    def _gen_comparison(self, content: Dict) -> str:
        """表格对比布局"""
        title = content.get('title', '对比分析')
        items = content.get('bullets', [])
        
        rows_html = ''
        for i, row_text in enumerate(items):
            cols = [c.strip() for c in row_text.replace('|', '｜').split('｜') if c.strip()]
            if not cols:
                continue
            
            tag = 'th' if i == 0 else 'td'
            bg = f'{self.colors["primary"]}20' if i == 0 else 'transparent'
            cells = ''.join([f'<{tag} style="padding: 20px 25px; border: 1px solid {self.colors["primary"]}30;">{c}</{tag}>' for c in cols])
            rows_html += f'<tr style="background: {bg};">{cells}</tr>\n'
        
        return f'''
<div class="slide slide-comparison" style="background: {self.colors['background']}; padding: 80px;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; text-align: center; margin-bottom: 50px;">{title}</h2>
    <div class="table-container" style="max-width: 1500px; margin: 0 auto; overflow: auto;">
        <table style="width: 100%; border-collapse: collapse; color: {self.colors['text']}; font-size: 24pt;">
            {rows_html}
        </table>
    </div>
</div>
'''
    
    def _gen_default(self, content: Dict) -> str:
        """默认布局"""
        title = content.get('title', '页面标题')
        bullets = content.get('bullets', [])
        
        bullets_html = '\n'.join([
            f'<li style="margin: 18px 0; font-size: 28pt; color: {self.colors["text"]};">{b}</li>'
            for b in bullets[:6]
        ])
        
        return f'''
<div class="slide slide-default" style="background: {self.colors['background']}; padding: 80px;">
    <h2 style="color: {self.colors['primary']}; font-size: 54pt; border-left: 6px solid {self.colors['primary']}; padding-left: 25px; margin-bottom: 50px;">{title}</h2>
    <ul style="list-style: none; padding: 0; max-width: 1400px;">
        {bullets_html}
    </ul>
</div>
'''


# ============================================================================
# 智能布局选择器
# ============================================================================

def select_layout(slide_type: str, content: Dict, has_image: bool = False) -> str:
    """
    根据内容智能选择最佳布局
    
    Args:
        slide_type: 幻灯片类型
        content: 内容数据
        has_image: 是否有图片
    
    Returns:
        布局名称
    """
    bullets = content.get('bullets', []) or content.get('content', [])
    count = len(bullets) if isinstance(bullets, list) else 1
    
    # 类型到布局的映射
    type_map = {
        'cover': 'cover',
        'title': 'cover',
        'objectives': 'cards_3col' if count == 3 else 'cards_4col',
        'intro': 'quote' if count <= 2 else 'top_image',
        'concept': 'split' if has_image else 'cards_3col',
        'keypoints': 'cards_4col' if count == 4 else 'cards_3col',
        'structure': 'circular' if count >= 4 else 'split',
        'principle': 'process_flow' if count >= 3 else 'split',
        'steps': 'timeline' if count <= 5 else 'steps',
        'warning': 'warning',
        'practice': 'before_after' if count >= 4 else 'steps',
        'summary': 'pyramid' if count == 4 else 'summary',
        'comparison': 'comparison',
        'gallery': 'image_wall_2x2' if count <= 4 else 'image_wall_2x3',
        'stats': 'stats',
    }
    
    return type_map.get(slide_type, 'split' if has_image else 'cards_3col')


def get_all_layouts() -> list:
    """获取所有可用布局名称"""
    return LayoutGenerator.AVAILABLE_LAYOUTS.copy()

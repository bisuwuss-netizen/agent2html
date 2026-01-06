"""
创意布局模板
提供多种有设计感的页面布局样式
"""

# 创意布局 CSS 样式
CREATIVE_STYLES = """
/* 图片旋转效果 */
.rotated-image-left {
    transform: rotate(-3deg);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}

.rotated-image-right {
    transform: rotate(3deg);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}

/* 拼贴风格 */
.collage-container {
    position: relative;
    width: 100%;
    height: 100%;
}

.collage-image {
    position: absolute;
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
    transition: transform 0.3s ease;
}

.collage-image:hover {
    transform: scale(1.05);
    z-index: 10;
}

/* 卡片网格 */
.card-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 30px;
    padding: 40px;
}

.creative-card {
    background: rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 30px;
    border: 2px solid rgba(255,255,255,0.1);
    transition: all 0.3s ease;
}

.creative-card:hover {
    transform: translateY(-10px);
    border-color: rgba(255,255,255,0.3);
    box-shadow: 0 12px 32px rgba(0,0,0,0.3);
}

/* 不规则网格 */
.masonry-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    grid-auto-rows: minmax(100px, auto);
    gap: 30px;
}

.masonry-item:nth-child(1) {
    grid-row: span 2;
}

.masonry-item:nth-child(3) {
    grid-row: span 2;
}

/* 标签样式 */
.tag-badge {
    display: inline-block;
    padding: 8px 20px;
    background: rgba(255,255,255,0.1);
    border-radius: 20px;
    font-size: 28px;
    margin: 5px;
    border: 2px solid rgba(255,255,255,0.2);
}

/* 强调框 */
.highlight-box {
    background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
    border-left: 5px solid;
    padding: 30px;
    border-radius: 8px;
    margin: 20px 0;
}
"""


def get_creative_layout_template(layout_type: str, colors: dict, has_image: bool = False) -> str:
    """
    获取创意布局模板

    Args:
        layout_type: 布局类型
        colors: 配色方案
        has_image: 是否包含图片

    Returns:
        HTML 模板字符串
    """

    templates = {
        # 拼贴风格 - 多图错位排列
        "collage_style": f"""
<section style="padding:80px; background:{colors['bg_dark']}; color:{colors['text_primary']}; position:relative; overflow:hidden;">
    <div style="position:relative; z-index:2;">
        <h1 style="font-size:72px; margin-bottom:40px; font-weight:700;">{{{{title}}}}</h1>
        <div style="max-width:800px;">
            {{{{content}}}}
        </div>
    </div>

    <!-- 拼贴图片区 -->
    <div style="position:absolute; right:80px; top:50%; transform:translateY(-50%); width:500px; height:600px;">
        <!-- 图片1 - 左上，轻微左旋 -->
        <img src="{{{{image1}}}}" alt="{{{{alt1}}}}" data-image-slot="{{{{slot1}}}}"
             style="position:absolute; top:0; left:0; width:300px; height:auto; object-fit:contain;
                    transform:rotate(-5deg); border-radius:12px; box-shadow:0 8px 24px rgba(0,0,0,0.4); z-index:1;" />

        <!-- 图片2 - 右下，轻微右旋 -->
        <img src="{{{{image2}}}}" alt="{{{{alt2}}}}" data-image-slot="{{{{slot2}}}}"
             style="position:absolute; bottom:0; right:0; width:280px; height:auto; object-fit:contain;
                    transform:rotate(3deg); border-radius:12px; box-shadow:0 8px 24px rgba(0,0,0,0.4); z-index:2;" />
    </div>
</section>
        """,

        # 卡片网格 - 三栏布局
        "card_grid_3col": f"""
<section style="padding:80px; background:{colors['bg_dark']}; color:{colors['text_primary']};">
    <h1 style="font-size:72px; margin-bottom:60px; text-align:center; font-weight:700;">{{{{title}}}}</h1>

    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:35px;">
        {{{{cards}}}}
    </div>
</section>
        """,

        # 左侧大图 + 右侧卡片堆叠
        "left_image_right_cards": f"""
<section style="display:flex; padding:80px; background:{colors['bg_dark']}; color:{colors['text_primary']}; gap:50px;">
    <!-- 左侧大图 -->
    <div style="flex:1; position:relative;">
        <img src="{{{{main_image}}}}" alt="{{{{main_alt}}}}" data-image-slot="{{{{main_slot}}}}"
             style="width:100%; height:auto; max-height:800px; object-fit:contain;
                    border-radius:16px; transform:rotate(-2deg);
                    box-shadow:0 12px 40px rgba(0,0,0,0.5);" />
    </div>

    <!-- 右侧内容 -->
    <div style="flex:1; display:flex; flex-direction:column; justify-content:center;">
        <h1 style="font-size:68px; margin-bottom:40px; font-weight:700;">{{{{title}}}}</h1>
        {{{{content}}}}
    </div>
</section>
        """,

        # 顶部双图 + 底部文字
        "top_dual_images": f"""
<section style="padding:80px; background:{colors['bg_dark']}; color:{colors['text_primary']};">
    <h1 style="font-size:72px; margin-bottom:50px; text-align:center; font-weight:700;">{{{{title}}}}</h1>

    <!-- 双图并排 -->
    <div style="display:flex; gap:40px; margin-bottom:50px; justify-content:center;">
        <img src="{{{{image1}}}}" alt="{{{{alt1}}}}" data-image-slot="{{{{slot1}}}}"
             style="width:45%; max-height:450px; object-fit:contain;
                    border-radius:12px; transform:rotate(-2deg);
                    box-shadow:0 8px 24px rgba(0,0,0,0.4);" />

        <img src="{{{{image2}}}}" alt="{{{{alt2}}}}" data-image-slot="{{{{slot2}}}}"
             style="width:45%; max-height:450px; object-fit:contain;
                    border-radius:12px; transform:rotate(2deg);
                    box-shadow:0 8px 24px rgba(0,0,0,0.4);" />
    </div>

    <!-- 底部内容 -->
    <div style="max-width:1400px; margin:0 auto;">
        {{{{content}}}}
    </div>
</section>
        """,

        # 标签云样式
        "tag_cloud": f"""
<section style="padding:80px; background:{colors['bg_dark']}; color:{colors['text_primary']}; display:flex; flex-direction:column; justify-content:center;">
    <h1 style="font-size:72px; margin-bottom:60px; text-align:center; font-weight:700;">{{{{title}}}}</h1>

    <div style="text-align:center; max-width:1400px; margin:0 auto;">
        {{{{tags}}}}
    </div>
</section>
        """,

        # 不规则网格
        "masonry_grid": f"""
<section style="padding:80px; background:{colors['bg_dark']}; color:{colors['text_primary']};">
    <h1 style="font-size:72px; margin-bottom:50px; font-weight:700;">{{{{title}}}}</h1>

    <div style="display:grid; grid-template-columns:repeat(2, 1fr); grid-auto-rows:minmax(100px, auto); gap:30px;">
        {{{{items}}}}
    </div>
</section>
        """
    }

    return templates.get(layout_type, "")


def create_creative_card(title: str, content: str, icon: str, colors: dict, rotate: int = 0) -> str:
    """创建创意卡片"""
    return f"""
<div style="background:rgba(255,255,255,0.05); border-radius:16px; padding:35px;
            border:2px solid rgba(255,255,255,0.1); transform:rotate({rotate}deg);
            transition:all 0.3s ease;">
    <div style="font-size:48px; margin-bottom:20px;">{icon}</div>
    <h3 style="font-size:38px; margin-bottom:20px; color:{colors['accent']}; font-weight:600;">{title}</h3>
    <p style="font-size:32px; line-height:1.6; color:{colors['text_secondary']};">{content}</p>
</div>
    """


def create_highlight_box(content: str, colors: dict, border_color: str = None) -> str:
    """创建强调框"""
    border = border_color or colors['accent']
    return f"""
<div style="background:linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
            border-left:5px solid {border}; padding:35px; border-radius:8px; margin:25px 0;">
    <p style="font-size:36px; line-height:1.6;">{content}</p>
</div>
    """

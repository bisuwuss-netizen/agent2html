# Agent 2 增强指南

## 需要修改的内容

### 1. 导入新的配色方案

在 `src/agents/designer_generator.py` 开头添加：

```python
from src.utils.professional_colors import get_color_scheme
```

### 2. 替换 COLOR_SCHEMES

删除现有的 `COLOR_SCHEMES` 字典（第12-66行），改为使用：

```python
# 在 designer_generator 函数中
colors = get_color_scheme(user_input['major'])
```

### 3. 增强 System Prompt - 添加图片槽位规范

在 system_prompt 中添加：

```python
system_prompt = """你是专业的 HTML 课件生成专家。

【核心要求】

1. 字体规范（严格执行）：
   - h1 标题：64-72px
   - h2 副标题：48-56px
   - 正文/列表：32-40px
   - 禁止使用小于 32px 的字体

2. 配色规范：
   - 使用提供的专业配色（无渐变）
   - 深色背景 + 浅色文字（对比度 ≥ 4.5:1）
   - 强调内容使用 accent 颜色

3. 图片槽位规范（重要！）：
   **每个需要图片的位置，必须生成 <img> 标签占位**

   示例（left_text_right_image布局）：
   ```html
   <section>
     <div style="display: flex; width: 100%; gap: 40px;">
       <!-- 左侧文字 60% -->
       <div style="flex: 0 0 60%;">
         <h2>车床主要组成部分</h2>
         <ul>
           <li>主轴箱：驱动工件旋转</li>
           <li>进给箱：控制刀具移动速度</li>
         </ul>
       </div>

       <!-- 右侧图片 40% -->
       <div style="flex: 0 0 40%; display: flex; align-items: center;">
         <img
           src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Crect width='400' height='300' fill='%23ecf0f1'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%232c3e50' font-size='20' font-family='Arial'%3E车床结构示意图%3C/text%3E%3C/svg%3E"
           alt="车床结构示意图"
           data-image-slot="车床主轴、进给箱、溜板箱结构剖面图，工业蓝灰色调"
           style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"
         />
       </div>
     </div>
   </section>
   ```

   **关键点**：
   - src 使用 SVG 占位图（浅灰色背景 + 图片描述文字）
   - data-image-slot 属性存储图片描述（后续用于素材库匹配）
   - alt 属性也包含图片描述
   - 尺寸合理（left_text_right_image: 400-500px宽）

4. 布局规范：
   - left_text_right_image: 左60% + 右40%
   - top_image_bottom_text: 上50% + 下50%
   - two_columns: 各50%，左右对称
   - 禁止图片在底部（除非 top_image_bottom_text）

5. 响应式规范：
   - 1920x1080 分辨率优化
   - 使用 flex 布局
   - padding: 60px 80px（确保内容不溢出）

6. CDN 加载：
   - 必须包含多CDN备份代码
   - 加载屏幕友好提示
"""
```

### 4. 更新 User Prompt

添加当前页面的图片描述信息：

```python
user_prompt = f"""
请为第 {page['page_num']} 页生成 HTML 代码片段。

**页面信息：**
- 标题：{page['title']}
- 类型：{page['type']}
- 布局：{page['layout']}
- 内容：{json.dumps(page['content'], ensure_ascii=False)}
- 图片描述：{page.get('image_description', '无')}  # ← 新增

**配色方案（专业配色）：**
- 主色：{colors['primary']}
- 背景：{colors['bg_dark']}
- 文字：{colors['text_primary']}

**图片槽位要求：**
{f"本页需要图片槽位：{page.get('image_description', '无')}" if page.get('image_description') else ""}
{f"布局位置：{page['layout']}" if 'image' in page['layout'] else ""}

{generate_image_slot_example(page['layout'], page.get('image_description'))}

请生成符合上述规范的 HTML 代码片段（只需 <section> 部分）。
"""
```

### 5. 添加图片槽位生成辅助函数

```python
def generate_image_slot_example(layout: str, description: str) -> str:
    """
    根据布局生成图片槽位示例

    Args:
        layout: 布局方式
        description: 图片描述

    Returns:
        HTML示例代码
    """
    if not description or 'image' not in layout:
        return ""

    # SVG占位图模板
    svg_template = f"""data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='{{width}}' height='{{height}}'%3E%3Crect width='{{width}}' height='{{height}}' fill='%23ecf0f1'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%232c3e50' font-size='18' font-family='Arial'%3E{description[:20]}...%3C/text%3E%3C/svg%3E"""

    if layout == "left_text_right_image":
        return f"""
**图片槽位示例（右侧40%）：**
```html
<img
  src="{svg_template.format(width=400, height=300)}"
  alt="{description}"
  data-image-slot="{description}"
  style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);"
/>
```
"""
    elif layout == "top_image_bottom_text":
        return f"""
**图片槽位示例（上方50%）：**
```html
<img
  src="{svg_template.format(width=800, height=400)}"
  alt="{description}"
  data-image-slot="{description}"
  style="width: 100%; max-height: 500px; object-fit: contain; border-radius: 8px;"
/>
```
"""
    else:
        return ""
```

## SVG占位图说明

使用 data URI 格式的 SVG 作为占位图有以下优点：

1. **无需外部文件**：直接嵌入HTML
2. **清晰标识**：显示图片描述，方便识别
3. **轻量级**：几百字节
4. **后续替换方便**：通过 data-image-slot 属性定位

## 后续素材库集成

当素材库功能实现后，可以通过以下方式替换占位图：

```python
# 伪代码
for img_tag in html.find_all('img'):
    description = img_tag['data-image-slot']
    real_image_url = material_library.search(description)
    if real_image_url:
        img_tag['src'] = real_image_url
```

## 完整修改步骤

1. ✅ 创建 `src/utils/professional_colors.py`
2. ⏳ 修改 `src/agents/designer_generator.py`：
   - 导入新配色
   - 删除旧 COLOR_SCHEMES
   - 增强 system_prompt（图片槽位规范）
   - 更新 user_prompt（包含图片描述）
   - 添加 generate_image_slot_example 函数
3. ⏳ 同样修改 `src/agents/parallel_generator.py`
4. ⏳ 测试生成的HTML是否包含图片槽位

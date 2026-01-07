# 3.5 模块五：网页版幻灯片页面设计与素材描述生成

## 3.5.1 网页版幻灯片设计要点

### 标准化尺寸与规格
采用 **16:9 标准宽屏比例**（1920×1080 像素），确保与主流投影设备和显示器适配，页面边距统一为 80px，保证内容不贴边，视觉舒适。

### 统一布局系统
系统内置 **19 种专业教学布局**，覆盖高职教学全场景：

| 布局类别 | 布局类型 | 适用场景 |
|---------|---------|---------|
| 封面类 | cover（封面）| 课程标题页、章节首页 |
| 目标类 | cards_3col（三栏卡片）、cards_4col（四栏卡片）| 教学目标展示（知识/能力/素养） |
| 内容类 | split（左右分栏）、top_image（上图下文）| 知识点讲解、概念阐述 |
| 流程类 | timeline（时间轴）、steps（步骤流程）、process_flow（流程图）| 实训步骤、操作流程 |
| 对比类 | comparison（对比表格）、before_after（前后对比）| 概念对比、优缺点分析 |
| 数据类 | stats（数据统计）、pyramid（金字塔）、circular（环形图）| 数据展示、层级关系 |
| 特殊类 | warning（警告框）、quote（引用）、summary（总结）| 安全提示、重点强调 |
| 图片类 | image_wall_2x2（2×2图墙）、image_wall_2x3（2×3图墙）、masonry（瀑布流）| 案例展示、设备图片 |

### 智能布局选择
系统根据页面类型（slide_type）和内容特征自动选择最佳布局：
- **封面页（cover）**：自动应用全屏渐变背景 + 居中标题布局
- **教学目标页（objectives）**：根据目标数量选择 3 栏或 4 栏卡片
- **知识点讲解页（concept）**：有图片时选择左右分栏，无图片时选择卡片
- **步骤说明页（steps）**：要点≤5 时选择时间轴，>5 时选择编号步骤
- **安全警告页（warning）**：自动应用红色醒目警告框样式

### 风格一致性渲染
基于风格配置文件（21 套专业配色主题），通过 CSS 内联样式实现页面色彩、字体、版式的统一渲染：
- **配色体系**：主色（primary）、辅色（secondary）、强调色（accent）、背景色、文本色、警告色
- **字体规范**：标题 72pt/54pt/42pt 三级，正文 28pt/24pt 两级
- **学科适配**：工科（蓝灰）、医护（蓝绿）、IT（紫蓝）、农林（绿色）、商科（橙金）、艺术（渐变）

### 响应式适配
采用 CSS 变换（transform: scale）实现响应式缩放，保证在不同屏幕尺寸（电脑、平板、投影仪）上都能清晰预览，布局不变形。

### 交互功能集成
- **键盘导航**：方向键/空格键翻页，F 键全屏
- **鼠标/触摸导航**：点击屏幕左半部分上一页，右半部分下一页
- **页码指示器**：右下角显示当前页/总页数（如 02/10）
- **页眉显示**：非封面页左上角显示课程主题（subject）
- **进度条**：底部显示课程进度（可选）

### 教师备注区域
每个页面可包含隐藏的教师备注区域（speaker-notes），AI 根据页面内容自动生成教学提示（如"此处可补充实例讲解""强调安全操作要点"），便于教师备课参考。

## 3.5.2 素材描述生成规则

针对各页面的素材需求，生成精准、详细的素材描述（用于后续素材库匹配或 AI 图像生成），包含以下维度：

### 素材类型（asset_type）
| 类型 | 英文标识 | 用途说明 |
|-----|---------|---------|
| 图片 | image | 实景照片、案例图片、场景配图 |
| 示意图 | diagram | 原理图、结构图、流程示意 |
| 图表 | chart | 数据图表、统计图、关系图 |
| 图标 | icon | 操作图标、警示标识、装饰图标 |

### 素材主题（theme）
与知识点教学内容精准匹配，采用"知识点关键词+素材用途"的命名规则：
- **机械专业**：gear_transmission_structure（齿轮传动结构图）、lathe_operation_steps（车床操作步骤图）
- **护理专业**：iv_infusion_procedure（静脉输液流程图）、sterile_operation_warning（无菌操作警示图）
- **电子专业**：diode_characteristics_diagram（二极管特性曲线图）、circuit_board_layout（电路板布局图）
- **林业专业**：forest_monitoring_sensors（森林监测传感器）、tree_species_identification（树种识别图鉴）

### 标准尺寸规格（slot_size）
系统定义 **8 种标准插槽尺寸**，确保素材比例统一：

| 尺寸名称 | 像素尺寸 | 适用场景 |
|---------|---------|---------|
| FULL | 1920×1080 | 全屏背景图 |
| HERO | 1600×900 | 大幅主视觉图 |
| HALF | 800×600 | 左右分栏图片 |
| CARD_LG | 500×400 | 大卡片配图 |
| CARD_MD | 400×300 | 中等卡片配图 |
| CARD_SM | 300×200 | 小卡片配图 |
| THUMB | 200×150 | 缩略图、图墙单元 |
| ICON | 80×80 | 图标、标识 |

### 风格要求
- **理论课素材**：清晰的知识点示意图、简洁线描图、专业配色
- **实训课素材**：高清实拍图、步骤分解图、标注操作关键点
- **安全警告素材**：醒目红色/黄色、带警示图标和说明文字
- **色彩匹配**：素材主色调需与课件配色体系协调

### 附加属性
- **data-slot-id**：唯一插槽标识（如 p3-main），用于后续素材填充
- **data-prompt**：素材描述提示词，用于 AI 图像生成或素材库检索
- **data-asset-type**：素材类型标识，用于显示对应占位符图标

## 3.5.3 输出结果

### HTML 文件结构
生成完整的网页版幻灯片 HTML 文件，包含以下组成部分：

```
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1920, height=1080">
    <title>【课程标题】</title>
    <link href="remixicon.css" rel="stylesheet"> <!-- 图标库 -->
    <style>
        /* 统一 CSS 样式：布局、配色、字体、动画 */
    </style>
</head>
<body>
    <div class="presentation">
        <!-- 各幻灯片页面 -->
        <div class="slide slide-cover">...</div>
        <div class="slide slide-split">...</div>
        ...
    </div>
    <script>
        /* 导航交互、图片插槽热插拔 API */
    </script>
</body>
</html>
```

### 素材描述清单（JSON）
同时输出各页面素材需求的结构化清单：

```
{
  "assets": [
    {
      "slot_id": "p1-bg",
      "page_num": 1,
      "asset_type": "image",
      "theme": "vocational_education_cover_background",
      "size": "FULL",
      "prompt": "高职教育科技感背景，深蓝色渐变，带轻微几何图案"
    },
    {
      "slot_id": "p3-main",
      "page_num": 3,
      "asset_type": "diagram",
      "theme": "gear_transmission_structure",
      "size": "HALF",
      "prompt": "齿轮传动原理示意图，包含主动轮和从动轮，标注传动方向"
    }
  ]
}
```

### 热插拔素材接口
HTML 文件内置 JavaScript API，支持后续动态填充素材：

```
// 获取所有插槽信息
window.getSlotInfo()
// 返回: [{id: "p1-bg", size: "FULL", prompt: "..."}, ...]

// 填充单个插槽
window.fillImageSlot("p3-main", "https://example.com/gear.png")
// 插槽背景图自动替换为指定图片 URL
```

### 输出文件规格
| 项目 | 规格 |
|-----|------|
| 文件格式 | HTML5（UTF-8 编码）|
| 幻灯片尺寸 | 1920×1080 像素（16:9）|
| 文件大小 | 约 20-40 KB（不含外部素材）|
| 生成耗时 | 约 1-2 秒（纯 HTML 生成）|
| 浏览器兼容 | Chrome、Firefox、Safari、Edge |

### 预览与编辑
- 支持在浏览器中直接打开预览
- 支持全屏演示模式（F 键）
- 支持教师在线调整内容后重新导出
- 素材插槽支持拖拽替换（前端编辑模式）

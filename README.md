# Agent2HTML - 智能教学课件生成系统

> 基于 LLM 的高职教育课件自动化生成工具

## 🎯 项目简介

Agent2HTML 是一个智能课件生成系统，能够根据课程主题自动规划内容、设计布局、生成专业的 HTML 课件。支持多种输出模式，特别针对高职教育场景优化。

### 核心特性

- **16:9 专业模式 (PPT Pro)**: 固定 1920x1080 分辨率，符合视频合成标准
- **纯 CSS 模式**: 无外部依赖，完全自包含
- **智能图片卡槽**: data-prompt 属性预留 AI 图片生成接口
- **并行生成**: 多页面异步生成，提速 70%
- **轻量级验证**: 自动检查和修复质量问题

### v2.0 新特性 (New!) 🚀

1. **美学升级 (Aesthetic Upgrade)**
   - 全新 Glassmorphism (毛玻璃) UI 设计
   - Mesh Gradients 动态背景
   - 基于 Animate.css 的流畅入场动画
   - 优化排版与 Google Fonts 集成

2. **外部大纲集成 (External Plan Integration)**
   - **Parser Mode**: 智能解析外部详细大纲（支持 Gamma/ChatGPT 生成内容）
   - **New Layouts**: 新增 `comparison` (表格) 和 `gallery` (图片墙) 布局
   - **Visual Fidelity**: 完美还原外部大纲的视觉描述

3. **API 服务化**
   - FastAPI 接口支持 (`/generate`, `/plan`)
   - 生产级结构化日志与配置管理

## 📦 快速开始

### 安装依赖

```bash
# 使用项目内的 conda 环境
conda env create -f environment.yml -p ./.conda

# 或手动安装
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件:

```bash
# LLM 配置
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4
TEMPERATURE=0.7

# 生成模式配置
USE_PPT_PRO=true              # 启用 16:9 专业模式
USE_PURE_CSS=false            # 禁用纯 CSS 模式
USE_PARALLEL_GENERATION=true  # 启用并行生成
```

### 运行

```bash
# 方法 1: 使用快速启动脚本
./quick_start.sh

# 方法 2: 运行测试
python test_ppt_pro.py

# 方法 3: 运行主程序（交互式）
python main.py
```

## 🏗️ 项目架构

### 核心模块

```
agent2html/
├── main.py                   # 主程序入口
├── src/
│   ├── workflow.py           # 工作流定义
│   ├── state.py              # 状态管理
│   ├── agents/               # Agent 模块
│   │   ├── content_planner.py       # Agent 1: 内容规划
│   │   ├── ppt_pro_generator.py     # PPT Pro 生成器
│   │   ├── pure_css_generator.py    # 纯 CSS 生成器
│   │   ├── parallel_generator.py    # 并行生成器
│   │   └── designer_generator.py    # 传统生成器
│   ├── templates/ppt_pro/    # PPT Pro 模板
│   │   ├── index_template.html
│   │   └── styles.css
│   └── utils/                # 工具函数
│       └── lightweight_validator.py
├── output/                   # 生成的 HTML 文件
└── test_ppt_pro.py          # 测试脚本
```

### 工作流程

```
用户输入 → Agent 1 (内容规划) → Agent 2 (设计+生成) → 验证器 → HTML 输出
```

## 🎨 生成模式

### 1. PPT Pro 模式 (推荐)

**特点**:
- 固定 1920x1080 分辨率（16:9 黄金比例）
- 4 种专业布局模板
- 智能图片卡槽系统
- Base64 内联 CSS
- 键盘翻页 + PDF 导出

**使用场景**: 视频课程制作、专业演示

**启用方式**:
```bash
export USE_PPT_PRO=true
python test_ppt_pro.py
```

**布局模板**:
1. **封面页**: 左 60% 文字 + 右 40% 背景斜切
2. **左文右图**: CSS Grid 1:1 分栏 + 图表卡槽
3. **顶部大图**: 1200x500 横向图 + 底部说明
4. **网格展示**: 3 列网格 + 卡槽说明

### 2. 纯 CSS 模式

**特点**:
- 无外部依赖
- CSS `:target` 伪类实现翻页
- 响应式设计（vw/vh 单位）
- 创意布局（卡片、旋转、阴影）

**使用场景**: 离线使用、网页演示

**启用方式**:
```bash
export USE_PURE_CSS=true
export USE_PPT_PRO=false
python main.py
```

### 3. 传统模式

**特点**:
- 基于 reveal.js
- 丰富的动画效果
- 完整的演示功能

**使用场景**: 互动演示、在线分享

## 🔧 智能图片卡槽

生成的 HTML 包含智能图片卡槽，方便后续填充:

```html
<div class="image-slot" 
     id="slot-page2-chart" 
     data-prompt="现代机械工厂中，工人在数控系统前编写程序的实景照片">
    <i class="ri-image-line"></i>
    <span>图表/流程图素材位</span>
</div>
```

### 后端替换示例

```python
from bs4 import BeautifulSoup

html = open('output.html').read()
soup = BeautifulSoup(html, 'html.parser')

# 根据 data-prompt 自动填充图片
for slot in soup.find_all(attrs={'data-prompt': True}):
    prompt = slot['data-prompt']
    image_url = generate_image_from_sd(prompt)  # 调用 Stable Diffusion
    slot['style'] = f"background-image: url({image_url}); background-size: cover;"
    slot.clear()  # 清空占位符

with open('output_filled.html', 'w') as f:
    f.write(str(soup))
```

### JavaScript 动态填充

```javascript
// 已内置在模板中
fillImageSlot('slot-page2-chart', 'https://example.com/chart.png');
```

## 📊 性能指标

| 指标 | 数值 |
|------|------|
| 生成时间 | ~33秒（8页） |
| 并行加速 | 70% 提升 |
| 文件大小 | ~50KB |
| 图片卡槽 | 3-4个/8页 |

## 🎓 使用示例

### 示例 1: 生成数控编程课件

```bash
# 运行测试脚本
python test_ppt_pro.py

# 输出: output/ppt_pro_20260106_140342.html
# 页数: 8 页
# 图片卡槽: 3 个
# 耗时: 33.45 秒
```

### 示例 2: 自定义课程

```bash
# 运行主程序
python main.py

# 输入课程信息:
# - 主题: 焊接技术基础
# - 专业: 机械制造
# - 对象: 高职一年级学生
# - 课时: 90分钟
```

## 🔮 扩展功能

### Playwright 自动截图

将 HTML 导出为图片序列:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    page.goto('file:///path/to/output.html')

    slides = page.locator('.slide').all()
    for i, slide in enumerate(slides):
        slide.screenshot(path=f'slide_{i+1}.png')
```

### PDF 导出

1. 浏览器打开生成的 HTML
2. 按 `Cmd+P` (Mac) 或 `Ctrl+P` (Windows)
3. 选择"保存为 PDF"
4. 勾选"背景图形"
5. 布局选择"横向"

## 🛠️ 技术栈

- **LLM**: OpenAI API (gpt-4)
- **工作流**: LangGraph
- **模板引擎**: Jinja2
- **并发**: ThreadPoolExecutor
- **前端**: HTML + CSS + JavaScript
- **图标**: Remix Icon

## 📝 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `USE_PPT_PRO` | 启用 PPT Pro 模式 | `false` |
| `USE_PURE_CSS` | 启用纯 CSS 模式 | `true` |
| `USE_PARALLEL_GENERATION` | 启用并行生成 | `true` |
| `MODEL_NAME` | LLM 模型名称 | `gpt-4` |
| `TEMPERATURE` | 生成温度 | `0.7` |

### 布局优先级

```
PPT Pro > Pure CSS > Traditional
```

当 `USE_PPT_PRO=true` 时，其他模式自动禁用。

## 🎯 适用场景

### 1. 视频课程制作

- 使用 PPT Pro 模式生成 1080P 幻灯片
- Playwright 截图导出图片序列
- 导入 OpenShot 进行视频合成

### 2. 在线教学

- 使用纯 CSS 模式生成轻量级课件
- 部署到 Web 服务器
- 学生浏览器直接访问

### 3. 课堂演示

- 使用传统模式生成交互式课件
- 支持动画和特效
- 全屏演示

## 📖 简历素材

> **智能教学课件生成系统（2026.01）**
> 
> - 设计并实现了 **16:9 专业课件生成器**，采用固定 1920x1080 分辨率容器，支持自动缩放和 PDF 导出
> - 创新性引入 **智能图片卡槽机制**（data-prompt 属性），为后续 AI 图片生成预留接口，提升扩展性
> - 采用 **Jinja2 模板引擎 + Base64 内联 CSS**，生成完全自包含的单文件 HTML，便于分发和集成
> - 实现 **4 种专业布局模板**（封面/左文右图/顶部大图/网格），满足不同教学场景需求
> - 通过**并行生成策略**（ThreadPoolExecutor），将 8 页课件生成时间从 ~90 秒优化至 ~33 秒（**提速 70%**）
> - 输出符合 **OpenShot 视频合成标准**（1080P 分辨率），可直接用于视频课程制作

## 🔧 常见问题

### Q: 如何调整字体大小？

修改 `src/templates/ppt_pro/styles.css` 中的字体尺寸。

### Q: 如何添加新的布局模板？

在 `src/agents/ppt_pro_generator.py` 中添加新的 `_generate_xxx_page()` 方法。

### Q: 生成失败怎么办？

1. 检查 `.env` 文件配置
2. 确认 API Key 有效
3. 查看终端错误信息
4. 尝试降低 `TEMPERATURE` 参数

### Q: 如何批量生成？

编写循环脚本，修改 `user_input` 参数即可:

```python
topics = ["数控编程", "焊接技术", "钳工基础"]
for topic in topics:
    user_input = {"topic": topic, ...}
    result = app.invoke(initial_state)
    save_html(result['final_html'], f"{topic}.html")
```

## 📄 License

MIT License

## 🙏 致谢

- OpenAI for GPT-4 API
- LangChain/LangGraph for workflow framework
- Remix Icon for beautiful icons

---

**项目地址**: [GitHub](https://github.com/yourusername/agent2html)

**作者**: Your Name

**联系方式**: your.email@example.com

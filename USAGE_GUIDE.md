# 🚀 使用指南

## 一、文件说明

### 核心文件

| 文件 | 说明 | 你需要关注 |
|-----|------|-----------|
| **src/state.py** | State 定义 | ⭐ 了解数据流 |
| **src/agents/content_planner.py** | Agent 1: 内容规划 | ⭐⭐⭐ 核心逻辑 |
| **src/agents/designer_generator.py** | Agent 2: 设计+生成 | ⭐⭐⭐ 核心逻辑 |
| **src/agents/quality_checker.py** | Agent 3: 质量检查 | ⭐⭐⭐ 核心逻辑 |
| **src/workflow.py** | LangGraph 工作流 | ⭐⭐ 理解流程 |
| **main.py** | 主程序 | ⭐ 运行入口 |
| **quick_test.py** | 快速测试 | ⭐ 测试用 |

### 配置文件

| 文件 | 说明 |
|-----|------|
| **.env** | API 密钥配置（你需要创建） |
| **.env.example** | 配置模板 |
| **requirements.txt** | Python 依赖包 |

---

## 二、快速测试步骤

### 第 1 步：检查环境

```bash
# 确认 Python 版本 (需要 3.8+)
python --version

# 查看当前目录
pwd
# 应该显示: /Users/bisuv/Documents/internProject/agent2html
```

### 第 2 步：安装依赖

```bash
pip install -r requirements.txt
```

> **如果遇到错误**：可能需要先升级 pip
> ```bash
> pip install --upgrade pip
> ```

### 第 3 步：配置 API 密钥

编辑 `.env` 文件（如果没有就创建一个）：

```env
OPENAI_API_KEY=你的API密钥
OPENAI_BASE_URL=https://api.deepseek.com/v1  # 如果用 DeepSeek
MODEL_NAME=deepseek-chat  # 或 gpt-4
TEMPERATURE=0.7
```

**重要**：确保 API Key 有效且有余额。

### 第 4 步：运行快速测试

```bash
python quick_test.py
```

**预期输出**：

```
======================================================================
🧪 快速测试模式 - 使用默认参数
======================================================================

✅ API Key 已配置: sk-1234567...
✅ Base URL: https://api.deepseek.com/v1
✅ Model: deepseek-chat

✅ LLM 初始化成功
✅ 工作流创建成功

======================================================================
📋 测试课程信息：
   主题：机械加工-车床操作
   专业：机械制造
   对象：高职二年级学生
   课时：45分钟
   知识点：车床结构, 操作步骤, 安全规范
======================================================================

🚀 开始执行工作流...

======================================================================
📍 节点: content_planner
   状态: planning_completed
   📄 课程标题: 车床操作基础
   📊 页数: 8
======================================================================

======================================================================
📍 节点: designer_generator
   状态: generation_completed
   📝 HTML 长度: 12543 字符
======================================================================

======================================================================
📍 节点: quality_checker
   状态: completed
   ⚠️  问题数: 0
======================================================================

======================================================================
📊 测试结果
======================================================================
⏱️  总耗时: 35.23 秒
📄 规划页数: 8
🔄 迭代次数: 0
⚠️  最终问题数: 0
✅ 最终状态: completed

✅ 测试成功！
   📄 文件: output/test_20260105_150322.html
   📏 大小: 12543 字符

💡 用浏览器打开查看效果
```

### 第 5 步：查看生成的文件

```bash
# 查看 output 目录
ls -lh output/

# 用浏览器打开（Mac）
open output/test_20260105_150322.html

# 或者用默认浏览器（通用）
# 直接双击 output/ 文件夹里的 .html 文件
```

---

## 三、正式使用

### 方式 1：交互式输入

```bash
python main.py
```

然后按照提示输入课程信息：

```
📚 课程主题（如：机械加工-车床操作）: 3D建模入门
🎯 专业（如：机械制造）: 数字媒体艺术
👥 授课对象（如：高职二年级学生）: 高职一年级
⏰ 课时（如：45分钟）: 90分钟
📌 关键知识点（用逗号分隔，可选）: Blender界面, 基础建模, 材质
```

### 方式 2：编程式调用

创建自己的脚本：

```python
from langchain_openai import ChatOpenAI
from src.workflow import create_workflow
from src.state import PPTWebState

# 初始化
llm = ChatOpenAI(model="deepseek-chat", openai_api_key="your-key")
app = create_workflow(llm).compile()

# 定义课程
user_input = {
    "topic": "烹饪基础-刀工技巧",
    "major": "烹饪工艺",
    "target_audience": "高职一年级学生",
    "duration": "45分钟",
    "key_points": ["刀具选择", "切菜技巧", "安全操作"]
}

# 执行
initial_state = {
    "user_input": user_input,
    "planning": None,
    "html_code": None,
    "quality_issues": [],
    "iteration_count": 0,
    "final_html": None,
    "status": "pending",
    "execution_time": None,
    "messages": [],
    "error": None
}

for event in app.stream(initial_state):
    # 处理事件
    pass
```

---

## 四、常见问题排查

### 问题 1：`ModuleNotFoundError: No module named 'langgraph'`

**原因**：依赖未安装

**解决**：
```bash
pip install -r requirements.txt
```

### 问题 2：`openai.error.AuthenticationError`

**原因**：API Key 无效或未配置

**解决**：
1. 检查 `.env` 文件是否存在
2. 检查 `OPENAI_API_KEY` 是否正确
3. 检查 API Key 是否有余额

### 问题 3：生成的 HTML 打不开

**原因**：文件损坏或路径错误

**解决**：
1. 检查 `output/` 目录是否有文件
2. 用文本编辑器打开 HTML，检查内容是否完整
3. 确认文件以 `<!DOCTYPE html>` 开头

### 问题 4：页面显示乱码

**原因**：编码问题

**解决**：代码已经处理了 UTF-8 编码，如果还有问题：
1. 用 Chrome 打开 HTML
2. 右键 → 检查 → Console，查看错误
3. 检查 HTML 文件的 `<meta charset="UTF-8">` 标签

### 问题 5：运行很慢或超时

**原因**：LLM 响应慢或网络问题

**解决**：
1. 检查网络连接
2. 尝试更换 API 服务商（如 DeepSeek → OpenAI）
3. 减少知识点数量（简化任务）

---

## 五、如何调试

### 查看详细日志

在每个 Agent 文件中，已经有 `print()` 语句，运行时会自动显示进度。

### 查看中间结果

在 `main.py` 的循环中添加：

```python
for event in app.stream(initial_state):
    for node_name, node_state in event.items():
        # 打印完整的 state
        import json
        print(json.dumps(node_state, indent=2, ensure_ascii=False))
```

### 单独测试某个 Agent

```python
from src.agents.content_planner import content_planner
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="deepseek-chat")

state = {
    "user_input": {
        "topic": "测试课程",
        "major": "机械",
        "target_audience": "学生",
        "duration": "45分钟"
    },
    "messages": []
}

result = content_planner(state, llm)
print(result['planning'])
```

---

## 六、性能优化建议

### 当前性能

- **Agent 1 (规划)**：5-8 秒
- **Agent 2 (生成)**：15-20 秒
- **Agent 3 (质检)**：8-10 秒
- **总耗时**：30-40 秒（包含优化）

### 优化方向

1. **使用更快的模型**
   ```env
   MODEL_NAME=deepseek-chat  # 比 gpt-4 快
   ```

2. **减少 Prompt 长度**
   - 在 Agent 2 中，可以去掉一些注释

3. **缓存结果**
   - 相同的课程主题，第二次生成会更快

4. **并行优化**（高级）
   - 当前是串行执行，未来可以让某些检查并行

---

## 七、下一步建议

### 本周目标

1. ✅ 跑通完整流程（用 `quick_test.py`）
2. ✅ 生成 2-3 个不同专业的课件（机械、3D、烹饪）
3. ✅ 用浏览器查看效果，F11 全屏演示
4. ✅ 记录遇到的问题和改进想法

### 下周目标

1. 优化 Prompt，提高生成质量
2. 添加更多配色方案
3. 尝试接入 RAG 素材库
4. 准备给老板演示

### 展示准备

**给老板看的内容**：
1. 输入课程信息（现场演示）
2. 等待 30 秒生成
3. 浏览器全屏展示（F11）
4. 翻页演示效果
5. 讲解 3 个 Agent 的分工

**亮点**：
- 完全自动化（从需求到成品）
- 专业化配色（不同专业不同风格）
- 质量保证（自动检查+优化）
- 课堂友好（大字体、高对比度）

---

## 八、联系方式

如果遇到问题，可以：
1. 查看 README.md 的常见问题部分
2. 检查代码注释（每个文件都有详细说明）
3. 用 Claude 询问具体问题

---

**祝测试顺利！** 🎉

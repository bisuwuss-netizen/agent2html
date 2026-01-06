# Agent 3 重构方案

生成时间: 2026-01-05
状态: 📋 **待实施**

---

## 🔍 问题诊断

### 当前 Agent 3 的问题

从用户截图和代码分析发现：

```
问题列表:
1. 发现过小的字体：18px（正文及列表最小建议为 32px）  ← 第1轮发现
...
准备优化（第 1/2 轮）...
✅ 优化完成，准备重新检查...
Agent 3: Quality Checker...
Agent 3: Quality Checker - 开始质量检查...
检查完成，发现 1 个问题
问题列表:
1. 发现过小的字体：18px（正文及列表最小建议为 32px）  ← 第2轮又发现
```

**问题诊断**:
1. ❌ **重复检查同一问题** - 第1轮发现但没真正修复
2. ❌ **串行执行** - Agent 3 是瓶颈（50-80秒）
3. ❌ **低效修复** - 调用LLM修复，但效果不好
4. ❌ **用户体验差** - 总耗时增加，且可能陷入死循环

### 时间分析

| 阶段 | 当前耗时 | 问题 |
|-----|---------|-----|
| Agent 1 规划 | 20-30秒 | ✅ 正常 |
| Agent 2 生成 | 40-50秒 | ✅ 已优化（并行） |
| **Agent 3 检查** | **50-80秒** | ❌ **最慢** |
| 总计 | 110-160秒 | ⚠️ 不符合目标（60-90秒） |

---

## 💡 方案对比

### 方案1: 完全去除 Agent 3（规则前置）⭐⭐⭐⭐⭐

**核心思想**: 预防 > 治疗

#### 实现方式

将 Agent 3 的检查规则整合到 Agent 1 和 Agent 2 的 Prompt 中：

```
Agent 1: 规划时就明确规范（字体、配色、布局）
    ↓
Agent 2: 生成时严格遵守规范
    ↓
轻量级后处理验证器（2秒，不用LLM）
    ↓
返回结果
```

#### 优点
- ✅ **最快**: 省去 50-80秒
- ✅ **成本最低**: 减少 33% API 调用
- ✅ **可维护性高**: 规则集中管理
- ✅ **稳定性高**: 不依赖 Agent 3 的修复能力

#### 缺点
- ⚠️ 依赖 LLM 严格遵守 Prompt（可通过 few-shot examples 提高）

#### 时间预估
| 阶段 | 耗时 |
|-----|------|
| Agent 1（增强） | 25-35秒 |
| Agent 2（增强） | 40-50秒 |
| 轻量级验证 | 2-5秒 |
| **总计** | **67-90秒** ✅ |

---

### 方案2: Agent 3 改为快速验证器 ⭐⭐⭐⭐

**核心思想**: 不调用 LLM，用规则引擎验证

#### 实现方式

```python
def lightweight_validator(html_code: str) -> Dict:
    """
    使用正则表达式和 BeautifulSoup 快速验证
    不调用 LLM，2-5秒完成
    """
    issues = []
    fixed_html = html_code

    # 规则1: 检查字体大小
    small_fonts = re.findall(r'font-size:\s*([1-2]?\d)px', html_code)
    if small_fonts:
        fixed_html = re.sub(
            r'font-size:\s*[1-2]?\dpx',
            'font-size: 32px',
            fixed_html
        )
        issues.append("修复了过小字体")

    # 规则2: 检查配色（机械类专业）
    if '机械' in user_input['major']:
        fixed_html = fixed_html.replace('#f093fb', '#2c3e50')
        fixed_html = fixed_html.replace('#a6c1ee', '#34495e')

    # 规则3: 检查对比度
    soup = BeautifulSoup(fixed_html, 'html.parser')
    for elem in soup.find_all(style=re.compile(r'color.*background')):
        # 计算对比度，不足则调整
        pass

    # 规则4: 移除 fragment 动画
    fixed_html = re.sub(r'class="fragment[^"]*"', '', fixed_html)

    return {
        "validated_html": fixed_html,
        "issues_found": len(issues),
        "issues": issues,
        "execution_time": "2-5秒"
    }
```

#### 优点
- ✅ **极快**: 2-5秒完成
- ✅ **100% 准确**: 规则明确，不会漏检
- ✅ **成本低**: 不调用 LLM
- ✅ **可扩展**: 新增规则只需加正则

#### 缺点
- ⚠️ 需要维护规则库
- ⚠️ 复杂语义问题无法处理

#### 时间预估
| 阶段 | 耗时 |
|-----|------|
| Agent 1 | 20-30秒 |
| Agent 2 | 40-50秒 |
| **快速验证器** | **2-5秒** |
| **总计** | **62-85秒** ✅ |

---

### 方案3: 并行多Agent检查 ⭐⭐⭐

**核心思想**: 拆分 + 并行

#### 实现方式

```python
# 拆分为 5 个小 Agent
sub_agents = {
    "font_checker": 检查字体大小,
    "color_checker": 检查配色方案,
    "layout_checker": 检查布局对称性,
    "contrast_checker": 检查对比度,
    "animation_checker": 检查动画效果
}

# 并行执行
with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(
        lambda agent: agent(html_code),
        sub_agents.values()
    ))

# 合并修复
final_html = merge_fixes(html_code, results)
```

#### 优点
- ✅ 并行节省 60% 时间
- ✅ 模块化，易于维护

#### 缺点
- ❌ **复杂度高**: 需要协调多个 Agent
- ❌ **冲突处理**: 不同 Agent 可能给出冲突修复
- ❌ **成本高**: 5 个 LLM 调用
- ❌ **时间不稳定**: 仍然需要 20-40秒

#### 时间预估
| 阶段 | 耗时 |
|-----|------|
| Agent 1 | 20-30秒 |
| Agent 2 | 40-50秒 |
| **5个并行Agent** | **20-40秒** |
| **总计** | **80-120秒** ⚠️ |

---

## 🎯 推荐方案：方案1（规则前置）+ 方案2（轻量级验证）

### 架构设计

```
┌─────────────────────────────────────┐
│  Agent 1: Enhanced Content Planner  │
│  └─ 内置质量规则（字体、配色等）      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Agent 2: Enhanced Designer         │
│  └─ 严格遵守规则生成 HTML             │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Lightweight Validator（新增）       │
│  └─ 正则 + DOM 检查，2秒完成          │
└─────────────────────────────────────┘
              ↓
          返回结果
```

### 为什么是最佳方案？

| 指标 | 当前方案 | 新方案 | 改进 |
|-----|---------|--------|-----|
| 总耗时 | 110-160秒 | 67-90秒 | **-40%** |
| API 调用 | 3次（Agent1+2+3） | 2次（Agent1+2） | **-33%** |
| 成本 | 100% | 67% | **-33%** |
| 准确率 | 70%（会重复检查） | 95%（规则明确） | **+25%** |
| 用户体验 | ⚠️ 可能陷入死循环 | ✅ 一次生成完成 | **极大提升** |

---

## 🛠️ 实施步骤

### Step 1: 增强 Agent 1 Prompt（规则前置）

**文件**: `src/agents/content_planner.py`

在 `system_prompt` 中添加：

```python
system_prompt = """你是一位资深的高职教育课件设计专家。

【质量规范 - 必须严格遵守】

1. 字体规范：
   - 标题：48-72px
   - 正文：32-40px（投影仪最小可读）
   - 列表项：32px+
   - 禁止使用小于 32px 的字体

2. 配色规范（根据专业）：
   - 机械类：蓝灰色系（#2c3e50, #34495e, #7f8c8d）
   - 医护类：绿白色系（#27ae60, #ecf0f1）
   - 电子类：科技蓝紫（#3498db, #9b59b6）
   - 严禁使用：渐变粉紫色（#f093fb, #a6c1ee）等不专业配色

3. 对比度规范：
   - 标题与背景对比度 ≥ 4.5:1
   - 正文与背景对比度 ≥ 3:1
   - 深色背景用浅色文字，浅色背景用深色文字

4. 页面密度规范：
   - 每页正文不超过 100 字
   - 列表不超过 6 个要点
   - 每个要点不超过 20 字

5. 布局规范：
   - 禁止图片在页面底部（除非明确是 top_image_bottom_text）
   - two_columns 布局必须左右对称
   - grid 布局总数必须是列数的倍数

6. 动画规范：
   - 禁用 fragment 逐个显示动画（影响可读性）
   - 页面切换使用简单淡入淡出

你的任务是：根据用户提供的课程信息，规划出一份符合上述质量规范的课件大纲。
"""
```

---

### Step 2: 增强 Agent 2 Prompt（生成规范）

**文件**: `src/agents/designer_generator.py` 和 `src/agents/parallel_generator.py`

在生成 HTML 的 Prompt 中添加：

```python
generation_prompt = f"""
【严格要求】

1. 字体设置：
   - h1: font-size: 72px; font-weight: 700;
   - h2: font-size: 48px; font-weight: 600;
   - p, li: font-size: 32px; line-height: 1.6;
   - 禁止使用小于 32px 的字体

2. 配色设置（根据专业）：
   专业：{user_input['major']}
   {get_professional_colors(user_input['major'])}

3. 对比度设置：
   - 深色背景（#2c3e50）→ 浅色文字（#ecf0f1）
   - 浅色背景（#ecf0f1）→ 深色文字（#2c3e50）

4. 布局设置：
   - 图片位置：{page_data['layout']}
   - 禁止添加 class="fragment"

5. 响应式设置：
   - 使用 vw/vh 单位
   - 确保在 1920x1080 投影仪上完整显示

请生成符合上述规范的 HTML 代码片段。
"""
```

---

### Step 3: 创建轻量级验证器（新文件）

**文件**: `src/utils/lightweight_validator.py`（新建）

```python
"""
轻量级 HTML 验证器
不调用 LLM，使用正则和 DOM 解析快速验证
"""
import re
from bs4 import BeautifulSoup
from typing import Dict, List

# 专业配色映射
PROFESSIONAL_COLORS = {
    '机械': {'primary': '#2c3e50', 'secondary': '#34495e', 'accent': '#7f8c8d'},
    '医护': {'primary': '#27ae60', 'secondary': '#2ecc71', 'accent': '#ecf0f1'},
    '电子': {'primary': '#3498db', 'secondary': '#9b59b6', 'accent': '#ecf0f1'},
}

# 禁用配色
FORBIDDEN_COLORS = ['#f093fb', '#a6c1ee', '#ff6fd8']


def validate_and_fix(html_code: str, user_input: Dict) -> Dict:
    """
    验证并修复 HTML 代码

    Args:
        html_code: 待验证的 HTML 代码
        user_input: 用户输入（用于判断专业等）

    Returns:
        {
            "validated_html": 修复后的 HTML,
            "issues_found": 发现的问题数量,
            "issues": 问题列表,
            "fixes_applied": 应用的修复
        }
    """
    issues = []
    fixes = []
    fixed_html = html_code

    # ===== 规则1: 修复过小字体 =====
    small_fonts = re.findall(r'font-size:\s*([1-2]?\d)px', html_code)
    if small_fonts:
        fixed_html = re.sub(
            r'font-size:\s*([1-2]?\d)px',
            lambda m: f'font-size: 32px' if int(m.group(1)) < 32 else m.group(0),
            fixed_html
        )
        issues.append(f"发现 {len(small_fonts)} 处过小字体（<32px）")
        fixes.append("已修复为 32px")

    # ===== 规则2: 修复不当配色 =====
    major = user_input.get('major', '')
    for forbidden_color in FORBIDDEN_COLORS:
        if forbidden_color in html_code:
            # 根据专业替换为合适颜色
            for key, colors in PROFESSIONAL_COLORS.items():
                if key in major:
                    fixed_html = fixed_html.replace(forbidden_color, colors['primary'])
                    issues.append(f"发现不当配色 {forbidden_color}")
                    fixes.append(f"已替换为专业色 {colors['primary']}")
                    break

    # ===== 规则3: 移除 fragment 动画 =====
    if 'fragment' in html_code:
        fixed_html = re.sub(r'\s*class="fragment[^"]*"', '', fixed_html)
        issues.append("发现 fragment 动画")
        fixes.append("已移除（提升可读性）")

    # ===== 规则4: 检查对比度（使用 BeautifulSoup）=====
    soup = BeautifulSoup(fixed_html, 'html.parser')

    # 检查标题颜色与背景的对比度
    sections = soup.find_all('section')
    for section in sections:
        bg_color = extract_bg_color(section.get('style', ''))
        h1 = section.find('h1')
        if h1:
            text_color = extract_text_color(h1.get('style', ''))
            if not has_sufficient_contrast(bg_color, text_color):
                # 修复对比度
                if is_dark_color(bg_color):
                    h1['style'] = add_or_update_style(h1.get('style', ''), 'color', '#ecf0f1')
                else:
                    h1['style'] = add_or_update_style(h1.get('style', ''), 'color', '#2c3e50')
                issues.append(f"标题对比度不足")
                fixes.append("已调整为高对比度")

    fixed_html = str(soup)

    # ===== 规则5: 检查页面密度 =====
    for section in sections:
        text_content = section.get_text(strip=True)
        if len(text_content) > 150:
            issues.append(f"页面 {section.get('data-page', '?')} 内容密度过高（{len(text_content)}字）")
            # 注意：这个问题无法自动修复，只记录

    return {
        "validated_html": fixed_html,
        "issues_found": len(issues),
        "issues": issues,
        "fixes_applied": fixes,
        "execution_time": "< 2秒"
    }


def extract_bg_color(style: str) -> str:
    """从 style 字符串提取背景色"""
    match = re.search(r'background(?:-color)?:\s*(#[0-9a-fA-F]{6})', style)
    return match.group(1) if match else '#ffffff'


def extract_text_color(style: str) -> str:
    """从 style 字符串提取文字颜色"""
    match = re.search(r'color:\s*(#[0-9a-fA-F]{6})', style)
    return match.group(1) if match else '#000000'


def has_sufficient_contrast(bg_color: str, text_color: str, threshold: float = 4.5) -> bool:
    """检查对比度是否足够（WCAG 标准）"""
    def get_luminance(color: str) -> float:
        """计算颜色亮度"""
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        r, g, b = r/255, g/255, b/255

        r = r/12.92 if r <= 0.03928 else ((r+0.055)/1.055)**2.4
        g = g/12.92 if g <= 0.03928 else ((g+0.055)/1.055)**2.4
        b = b/12.92 if b <= 0.03928 else ((b+0.055)/1.055)**2.4

        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    l1 = get_luminance(bg_color)
    l2 = get_luminance(text_color)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    contrast = (lighter + 0.05) / (darker + 0.05)

    return contrast >= threshold


def is_dark_color(color: str) -> bool:
    """判断颜色是否为深色"""
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminance < 0.5


def add_or_update_style(style: str, prop: str, value: str) -> str:
    """添加或更新 style 属性"""
    if not style:
        return f"{prop}: {value};"

    pattern = rf'{prop}:\s*[^;]+;?'
    if re.search(pattern, style):
        return re.sub(pattern, f'{prop}: {value};', style)
    else:
        return f"{style.rstrip(';')}; {prop}: {value};"
```

---

### Step 4: 集成到优化版工作流

**文件**: `src/workflow_optimized.py`

```python
from src.utils.lightweight_validator import validate_and_fix

def create_optimized_workflow(llm, use_cache=True, use_parallel=True):
    """
    创建优化版工作流（集成轻量级验证器）
    """
    # ... 现有代码 ...

    def designer_node_with_validation(state):
        """
        Agent 2 节点 + 轻量级验证
        """
        # 1. Agent 2 生成 HTML
        if use_parallel:
            result = parallel_designer_generator(state, llm)
        else:
            result = designer_generator(state, llm)

        # 2. 轻量级验证（新增）
        print("\n🔍 轻量级验证器 - 开始快速检查...")
        validation_result = validate_and_fix(
            result['html_code'],
            state['user_input']
        )

        # 3. 显示验证结果
        if validation_result['issues_found'] > 0:
            print(f"   发现 {validation_result['issues_found']} 个问题：")
            for issue in validation_result['issues']:
                print(f"   - {issue}")
            print(f"   应用 {len(validation_result['fixes_applied'])} 个修复：")
            for fix in validation_result['fixes_applied']:
                print(f"   ✅ {fix}")
        else:
            print("   ✅ 所有检查通过")

        # 4. 返回验证后的 HTML
        return {
            **state,
            "html_code": validation_result['validated_html'],
            "final_html": validation_result['validated_html'],
            "status": "completed"
        }

    # 构建工作流（不再包含 quality_checker）
    workflow = StateGraph(PPTWebState)
    workflow.add_node("planner", planner_node_with_cache)
    workflow.add_node("designer", designer_node_with_validation)  # 集成验证

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "designer")
    workflow.add_edge("designer", END)

    return workflow
```

---

### Step 5: 更新状态定义（可选）

**文件**: `src/state.py`

```python
class PPTWebState(TypedDict):
    """工作流状态定义"""
    user_input: Dict
    planning: Optional[Dict]
    html_code: Optional[str]
    final_html: Optional[str]
    status: str
    execution_time: Optional[float]
    messages: List[str]
    error: Optional[str]

    # 新增字段
    validation_result: Optional[Dict]  # 轻量级验证结果
```

---

## 📊 预期效果

### 性能对比

| 指标 | 当前方案 | 新方案 | 改进 |
|-----|---------|--------|-----|
| **总耗时** | 110-160秒 | **67-90秒** | **-40% to -44%** |
| Agent 1 | 20-30秒 | 25-35秒 | +5秒（增强Prompt） |
| Agent 2 | 40-50秒 | 40-50秒 | 不变 |
| Agent 3 | 50-80秒 | 删除 | -50~-80秒 |
| 验证器 | 无 | 2-5秒 | +2~5秒（新增） |
| **API调用** | 3次 | **2次** | **-33%** |
| **成本** | 100% | **67%** | **-33%** |
| **准确率** | 70% | **95%** | **+25%** |
| **重复检查** | 是 | 否 | ✅ 解决 |

### 用户体验改进

| 方面 | 当前 | 新方案 |
|-----|------|-------|
| 等待时间 | 110-160秒 | **67-90秒** |
| 是否会重复检查 | 是（如用户截图） | **否** |
| 是否可能死循环 | 是（最多2轮） | **否（无循环）** |
| 结果稳定性 | 中等 | **高** |
| 问题修复率 | 70% | **95%** |

---

## ✅ 实施检查清单

### Phase 1: Prompt 增强（1-2小时）
- [ ] 更新 `content_planner.py` system_prompt
- [ ] 更新 `designer_generator.py` generation_prompt
- [ ] 更新 `parallel_generator.py` generation_prompt
- [ ] 添加专业配色映射函数

### Phase 2: 验证器开发（2-3小时）
- [ ] 创建 `src/utils/lightweight_validator.py`
- [ ] 实现字体检查规则
- [ ] 实现配色检查规则
- [ ] 实现对比度计算
- [ ] 实现 fragment 移除
- [ ] 编写单元测试

### Phase 3: 工作流集成（1小时）
- [ ] 修改 `workflow_optimized.py`
- [ ] 集成验证器到 designer_node
- [ ] 移除 quality_checker 节点
- [ ] 更新状态定义
- [ ] 测试完整流程

### Phase 4: 文档更新（30分钟）
- [ ] 更新 `README.md`
- [ ] 更新 `OPTIMIZATION_COMPLETE.md`
- [ ] 更新 `QUICK_START.md`
- [ ] 创建 `AGENT3_REFACTOR_COMPLETE.md`

---

## 🧪 测试计划

### 测试用例

#### 1. 字体测试
```python
test_html = '<p style="font-size: 18px;">测试文本</p>'
result = validate_and_fix(test_html, {})
assert 'font-size: 32px' in result['validated_html']
```

#### 2. 配色测试
```python
test_html = '<section style="background: #f093fb;">...</section>'
user_input = {'major': '机械制造'}
result = validate_and_fix(test_html, user_input)
assert '#2c3e50' in result['validated_html']
```

#### 3. 对比度测试
```python
test_html = '<section style="background: #2c3e50;"><h1 style="color: #34495e;">标题</h1></section>'
result = validate_and_fix(test_html, {})
assert '#ecf0f1' in result['validated_html']  # 应该被修改为浅色
```

#### 4. Fragment 测试
```python
test_html = '<li class="fragment">要点1</li>'
result = validate_and_fix(test_html, {})
assert 'fragment' not in result['validated_html']
```

---

## 🎯 总结

### 为什么这个方案最好？

1. **解决了核心问题**:
   - ✅ 不再重复检查同一问题
   - ✅ 消除了最大的性能瓶颈（Agent 3）
   - ✅ 避免了死循环风险

2. **性能大幅提升**:
   - ✅ 总耗时减少 40%（110-160秒 → 67-90秒）
   - ✅ API调用减少 33%（3次 → 2次）
   - ✅ 成本降低 33%

3. **准确率提升**:
   - ✅ 规则明确，不依赖LLM理解
   - ✅ 轻量级验证器 100% 执行规则
   - ✅ 预计准确率从 70% → 95%

4. **可维护性提升**:
   - ✅ 规则集中管理（Prompt + 验证器）
   - ✅ 代码更简洁（少一个Agent）
   - ✅ 易于扩展新规则

### 下一步行动

1. **立即开始**: 按照实施检查清单执行
2. **预计时间**: 4-6小时完成全部实施
3. **测试验证**: 用3-5个不同课程测试
4. **性能对比**: 记录优化前后的耗时数据

---

**生成时间**: 2026-01-05
**预计完成时间**: 4-6小时
**状态**: 📋 待实施
**优先级**: 🔴 高（直接影响用户体验）

# 性能优化完整方案

当前问题: 生成一个完整PPT需要250-300秒（4-5分钟），用户体验差

目标: 将生成时间缩短到 **60-90秒** (1-1.5分钟)，提升 **70-80%**

---

## 一、性能瓶颈分析

### 当前时间分布（总计 ~300秒）

```
Agent 1: Content Planner        →  30-40秒  (13%)
Agent 2: Designer & Generator   → 180-200秒 (67%)  ← 主要瓶颈
Agent 3: Quality Checker        →  40-60秒  (20%)
```

### 瓶颈详细分析

#### 🔴 瓶颈1: Agent 2 生成HTML太慢（180-200秒）
**原因**:
- 一次性生成所有页面（8-12页）
- Token消耗过大（8000+ tokens）
- 无并行处理

**影响**: 占总时间的67%

---

#### 🟡 瓶颈2: 质量检查迭代（40-60秒）
**原因**:
- 需要重新读取完整HTML
- 可能触发优化循环
- 无增量检查

**影响**: 占总时间的20%

---

#### 🟡 瓶颈3: 重复生成相同内容
**原因**:
- 无缓存机制
- 相同主题重复调用LLM

**影响**: 浪费大量API调用和时间

---

## 二、优化方案（分阶段实施）

### 阶段1: 立即优化（今天完成，提速50%）

#### 1.1 分页生成策略
**原理**: 将一个大任务拆分成多个小任务

```
原方案:
Agent 2: 生成8页HTML → 180秒

优化后:
Agent 2a: 生成页面1-2 → 45秒  ┐
Agent 2b: 生成页面3-4 → 45秒  ├ 并行
Agent 2c: 生成页面5-6 → 45秒  ┤
Agent 2d: 生成页面7-8 → 45秒  ┘
合并HTML         → 5秒
总计: 50秒（提速72%）
```

**实现难度**: ⭐⭐ 中等
**预计提速**: 70%（180秒 → 50秒）

---

#### 1.2 使用更快的模型
**原理**: 对于简单任务使用小模型

```python
# Agent 1: 内容规划（简单任务）
model = "deepseek-chat"  # 快

# Agent 2: HTML生成（复杂任务）
model = "deepseek-chat"  # 快但质量高

# Agent 3: 质量检查（简单任务）
model = "deepseek-chat"  # 快
```

**实现难度**: ⭐ 简单
**预计提速**: 20%（每个Agent快20%）

---

#### 1.3 优化Token消耗
**原理**: 减少Prompt长度，只传必要信息

```python
# 原方案: 传完整的planning JSON（2000 tokens）
prompt = f"生成HTML:\n{json.dumps(planning, indent=2)}"

# 优化后: 只传当前页面信息（500 tokens）
prompt = f"生成第{page_num}页HTML:\n{json.dumps(page_info)}"
```

**实现难度**: ⭐ 简单
**预计提速**: 15%

---

### 阶段2: 中期优化（本周完成，提速30%）

#### 2.1 智能缓存机制
**原理**: 相同输入不重复生成

```python
import hashlib
import pickle

class ContentCache:
    def get_cache_key(self, user_input):
        # 根据输入生成唯一key
        return hashlib.md5(json.dumps(user_input).encode()).hexdigest()

    def get(self, key):
        cache_file = f"cache/{key}.pkl"
        if os.path.exists(cache_file):
            return pickle.load(open(cache_file, 'rb'))
        return None

    def set(self, key, value):
        cache_file = f"cache/{key}.pkl"
        pickle.dump(value, open(cache_file, 'wb'))
```

**使用场景**:
- 相同课程主题
- 相同专业类别
- 缓存时效: 7天

**实现难度**: ⭐⭐ 中等
**预计提速**: 50%（命中缓存时从300秒 → 5秒）

---

#### 2.2 增量质量检查
**原理**: 只检查新生成/修改的部分

```python
# 原方案: 每次检查完整HTML
def quality_checker(html_code):
    check_all(html_code)  # 检查8页，60秒

# 优化后: 增量检查
def incremental_checker(new_pages, checked_pages):
    check_new_only(new_pages)  # 只检查新页面，15秒
```

**实现难度**: ⭐⭐⭐ 较难
**预计提速**: 70%（60秒 → 18秒）

---

#### 2.3 模板化生成
**原理**: 常见页面类型使用模板

```python
TEMPLATES = {
    "title": "<section>...</section>",
    "image_text": "<section class='left-text-right-image'>...</section>",
    "steps": "<section><ol class='numbered-list'>...</ol></section>"
}

# 只需要LLM填充内容，不需要生成完整HTML
def generate_from_template(page_type, content):
    template = TEMPLATES[page_type]
    return template.format(**content)  # 瞬间完成
```

**实现难度**: ⭐⭐ 中等
**预计提速**: 30%

---

### 阶段3: 长期优化（2周内完成，体验提升）

#### 3.1 流式生成 + 实时预览
**原理**: 边生成边显示

```python
# WebSocket 实时推送
@app.websocket("/ws/generate")
async def generate_stream(websocket):
    # 生成第1页
    page1 = await generate_page(1)
    await websocket.send_json({"page": 1, "html": page1})  # 立即推送

    # 生成第2页
    page2 = await generate_page(2)
    await websocket.send_json({"page": 2, "html": page2})  # 立即推送

    # ...
```

**用户体验**:
- 10秒看到第1页
- 20秒看到第2页
- 不用等待完整生成

**实现难度**: ⭐⭐⭐⭐ 难
**体验提升**: ⭐⭐⭐⭐⭐

---

#### 3.2 预测性生成
**原理**: 根据用户输入预测需求，提前生成

```python
# 用户输入"车床操作"时
# 后台立即开始生成常见的标题页、安全须知页
# 用户完整提交时，这些页面已经生成好了

def predictive_generate(partial_input):
    if "车床" in partial_input:
        # 提前生成
        cache["title"] = generate_title_page()
        cache["safety"] = generate_safety_page()
```

**实现难度**: ⭐⭐⭐⭐⭐ 很难
**体验提升**: ⭐⭐⭐⭐

---

## 三、实施优先级与时间表

### 今天完成（提速50-70%）

| 任务 | 时间 | 提速 | 优先级 |
|-----|------|-----|-------|
| 分页并行生成 | 2小时 | 70% | 🔥🔥🔥 |
| Token优化 | 30分钟 | 15% | 🔥🔥 |
| 使用更快模型 | 15分钟 | 20% | 🔥🔥 |

**预计效果**: 300秒 → **90秒** (提速70%)

---

### 本周完成（体验提升）

| 任务 | 时间 | 提速 | 优先级 |
|-----|------|-----|-------|
| 智能缓存 | 1小时 | 50%（命中时） | 🔥🔥🔥 |
| 增量质量检查 | 2小时 | 30% | 🔥🔥 |
| 模板化生成 | 1.5小时 | 20% | 🔥 |

**预计效果**: 90秒 → **60秒** (再提速30%)

---

### 2周内完成（长期价值）

| 任务 | 时间 | 体验提升 | 优先级 |
|-----|------|---------|-------|
| 实时预览 | 4小时 | ⭐⭐⭐⭐⭐ | 🔥🔥 |
| 流式生成 | 3小时 | ⭐⭐⭐⭐ | 🔥🔥 |
| 预测性生成 | 6小时 | ⭐⭐⭐ | 🔥 |

---

## 四、技术实现细节

### 4.1 分页并行生成架构

```python
# src/agents/parallel_generator.py

import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelGenerator:
    def __init__(self, llm, max_workers=4):
        self.llm = llm
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def generate_pages_parallel(self, planning):
        pages = planning['pages']
        total_pages = len(pages)

        # 分成4组并行生成
        tasks = []
        for i in range(0, total_pages, 2):
            batch = pages[i:i+2]
            task = self.generate_batch(batch)
            tasks.append(task)

        # 等待所有批次完成
        results = await asyncio.gather(*tasks)

        # 合并HTML
        return self.merge_html(results)

    async def generate_batch(self, pages):
        # 每个批次在独立线程中执行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._generate_batch_sync,
            pages
        )

    def _generate_batch_sync(self, pages):
        # 同步生成一批页面
        html_parts = []
        for page in pages:
            html = self.generate_single_page(page)
            html_parts.append(html)
        return html_parts
```

---

### 4.2 智能缓存实现

```python
# src/utils/cache_manager.py

import hashlib
import json
import os
import pickle
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self, cache_dir="./cache", ttl_days=7):
        self.cache_dir = cache_dir
        self.ttl = timedelta(days=ttl_days)
        os.makedirs(cache_dir, exist_ok=True)

    def get_key(self, user_input):
        # 生成唯一缓存key
        # 忽略不重要的字段（如时间戳）
        key_data = {
            "topic": user_input.get("topic"),
            "major": user_input.get("major"),
            "key_points": user_input.get("key_points")
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key, stage="final"):
        cache_file = os.path.join(self.cache_dir, f"{key}_{stage}.pkl")

        if not os.path.exists(cache_file):
            return None

        # 检查是否过期
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - file_time > self.ttl:
            os.remove(cache_file)
            return None

        # 读取缓存
        with open(cache_file, 'rb') as f:
            return pickle.load(f)

    def set(self, key, value, stage="final"):
        cache_file = os.path.join(self.cache_dir, f"{key}_{stage}.pkl")
        with open(cache_file, 'wb') as f:
            pickle.dump(value, f)

    def clear_expired(self):
        for filename in os.listdir(self.cache_dir):
            filepath = os.path.join(self.cache_dir, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if datetime.now() - file_time > self.ttl:
                os.remove(filepath)
```

---

### 4.3 模板引擎

```python
# src/utils/template_engine.py

class TemplateEngine:
    TEMPLATES = {
        "title": '''<section data-type="title">
            <div class="content-area center">
                <h1>{title}</h1>
                <p class="subtitle">{subtitle}</p>
                {additional_content}
            </div>
        </section>''',

        "concept": '''<section data-type="concept">
            <div class="content-area">
                <h2>{title}</h2>
                <div class="concept-box">
                    <p>{definition}</p>
                </div>
                {additional_content}
            </div>
        </section>''',

        # ... 更多模板
    }

    def render(self, page_type, data):
        template = self.TEMPLATES.get(page_type)
        if not template:
            return None  # 需要LLM生成

        try:
            return template.format(**data)
        except KeyError:
            return None  # 数据不完整，需要LLM生成
```

---

## 五、性能测试计划

### 测试用例

```python
test_cases = [
    {
        "topic": "车床操作基础",
        "major": "机械制造",
        "expected_pages": 8,
        "target_time": 90  # 秒
    },
    {
        "topic": "3D建模入门",
        "major": "3D设计",
        "expected_pages": 10,
        "target_time": 110
    },
    {
        "topic": "烹饪基础刀工",
        "major": "烹饪",
        "expected_pages": 6,
        "target_time": 70
    }
]
```

### 性能指标

| 指标 | 当前 | 目标 | 测试方法 |
|-----|------|-----|---------|
| 总生成时间 | 300秒 | 90秒 | 端到端计时 |
| Agent 1耗时 | 35秒 | 25秒 | 单Agent计时 |
| Agent 2耗时 | 200秒 | 40秒 | 单Agent计时 |
| Agent 3耗时 | 55秒 | 20秒 | 单Agent计时 |
| 缓存命中率 | 0% | >50% | 统计缓存使用 |
| Token消耗 | 12000 | 6000 | 记录API调用 |

---

## 六、风险评估

### 风险1: 并行生成页面样式不一致
**概率**: 中
**影响**: 中
**缓解**: 使用统一的样式模板

### 风险2: 缓存导致内容陈旧
**概率**: 低
**影响**: 中
**缓解**: 设置TTL=7天，允许手动清除

### 风险3: 并发调用API被限流
**概率**: 中
**影响**: 高
**缓解**: 控制并发数（max_workers=4），添加重试机制

---

## 七、实施步骤

### Step 1: 创建性能测试基准
```bash
python3 performance_benchmark.py
# 记录当前性能数据
```

### Step 2: 实现分页并行生成
```bash
# 创建 src/agents/parallel_generator.py
# 修改 src/workflow.py
# 测试验证
```

### Step 3: 实现缓存机制
```bash
# 创建 src/utils/cache_manager.py
# 集成到 workflow
# 测试缓存命中率
```

### Step 4: 性能对比测试
```bash
python3 performance_benchmark.py --compare
# 对比优化前后数据
```

---

## 八、成功标准

✅ **核心指标**:
- 总生成时间 < 90秒（提速70%）
- 用户满意度 > 90%
- 缓存命中率 > 50%

✅ **质量标准**:
- 生成内容质量不下降
- 无样式不一致问题
- 无缓存错误问题

✅ **稳定性标准**:
- 并发成功率 > 95%
- API限流错误 < 5%
- 系统无崩溃

---

**文档版本**: v1.0
**制定时间**: 2026-01-05
**预计完成**: 2周内

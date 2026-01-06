# 性能优化使用指南

## 🎯 优化效果

### 性能提升对比

| 场景 | 原版本 | 优化版本 | 提升 |
|-----|-------|---------|-----|
| 首次生成 | ~300秒 | ~60-90秒 | **70%** ⚡ |
| 缓存命中 | ~300秒 | ~5秒 | **98%** 🚀 |
| V1预览 | 无 | 30秒可见 | **体验提升** ✨ |

### 核心优化技术

1. **并行生成** - 将8-12页分成4批并行生成
2. **智能缓存** - 相同输入不重复调用LLM
3. **分页策略** - 每批2-3页，减少单次Token消耗
4. **跳过质检** - 缓存结果不再检查

---

## 🚀 快速开始

### 方式1: 使用优化版本（推荐）

```bash
# 1. 确认配置（默认已启用优化）
cat .env | grep USE_OPTIMIZED

# 2. 运行优化版本
python3 main_optimized.py
```

### 方式2: 使用原版本（对比测试）

```bash
# 临时禁用优化
export USE_OPTIMIZED_WORKFLOW=false

# 运行原版本
python3 main.py
```

---

## ⚙️ 配置说明

### .env 配置文件

```bash
# 性能优化配置
USE_OPTIMIZED_WORKFLOW=true      # 是否使用优化工作流
USE_CACHE=true                   # 是否启用智能缓存
USE_PARALLEL_GENERATION=true     # 是否使用并行生成
CACHE_TTL_DAYS=7                 # 缓存有效期（天）
MAX_PARALLEL_WORKERS=4           # 并行worker数
```

### 配置建议

| 场景 | 推荐配置 | 说明 |
|-----|---------|-----|
| **生产环境** | 全部启用 | 最快速度 |
| **测试调试** | 禁用缓存 | 避免缓存干扰 |
| **API限流** | workers=2 | 降低并发 |
| **低配机器** | workers=2 | 减少内存占用 |

---

## 📊 性能测试

### 运行性能对比测试

```bash
# 自动测试：原版本 vs 优化版本 vs 缓存
bash test_performance.sh
```

**测试内容**:
1. 原版本串行生成
2. 优化版本首次生成
3. 优化版本缓存命中

**预期结果**:
```
原始版本:       ~300秒
优化版本(首次): ~90秒   (提速70%)
优化版本(缓存): ~5秒    (提速98%)
```

### 运行基准测试

```bash
# 更详细的性能测试（包含3个不同难度的用例）
python3 performance_benchmark.py
```

### 对比历史性能

```bash
# 对比本次测试 vs 历史基准
python3 performance_benchmark.py --compare
```

---

## 💾 缓存管理

### 查看缓存统计

```python
from src.utils.cache_manager import get_cache_manager

cache = get_cache_manager()
cache.print_stats()
```

**输出示例**:
```
==================================================
  缓存统计
==================================================
命中次数: 5
未命中次数: 3
保存次数: 3
命中率: 62.5%
缓存文件数: 9
==================================================
```

### 清空缓存

```bash
# 方式1: 删除缓存目录
rm -rf cache/*.pkl

# 方式2: 使用Python代码
python3 -c "from src.utils.cache_manager import clear_cache; clear_cache()"
```

### 缓存文件说明

```
cache/
├── abc123_planning.pkl   # 规划结果缓存
├── abc123_html.pkl       # HTML代码缓存
└── abc123_final.pkl      # 最终结果缓存
```

**缓存key生成规则**:
- 基于: topic, major, target_audience, key_points
- 忽略: 时间戳、用户ID等
- 算法: MD5 hash

---

## 🔧 问题排查

### 问题1: 性能没有提升

**可能原因**:
1. 优化未启用
2. API限流导致并行失败
3. 缓存未生效

**解决方法**:
```bash
# 检查配置
echo $USE_OPTIMIZED_WORKFLOW
cat .env | grep OPTIMIZED

# 查看运行日志
python3 main_optimized.py 2>&1 | tee run.log

# 检查是否有"并行生成"字样
grep "并行" run.log
```

### 问题2: 缓存不生效

**可能原因**:
1. USE_CACHE=false
2. 输入有微小变化（如多余空格）
3. 缓存已过期（>7天）

**解决方法**:
```bash
# 检查缓存目录
ls -lh cache/

# 查看缓存时间
ls -lt cache/ | head -5

# 手动测试缓存
python3 -c "
from src.utils.cache_manager import get_cache_manager
cache = get_cache_manager()
user_input = {
    'topic': '车床操作基础',
    'major': '机械制造',
    'target_audience': '高职二年级学生'
}
key = cache.get_key(user_input)
print(f'缓存key: {key}')
print(f'缓存文件: cache/{key}_*.pkl')
"
```

### 问题3: 并行生成报错

**可能原因**:
1. workers过多导致API限流
2. 内存不足
3. 线程冲突

**解决方法**:
```bash
# 减少并行数
export MAX_PARALLEL_WORKERS=2

# 或禁用并行
export USE_PARALLEL_GENERATION=false

# 重新运行
python3 main_optimized.py
```

---

## 📈 性能监控

### 实时查看生成进度

```bash
python3 main_optimized.py 2>&1 | while read line; do
    echo "[$(date '+%H:%M:%S')] $line"
done
```

### 记录性能日志

```bash
# 记录到文件
python3 main_optimized.py 2>&1 | tee performance_$(date +%Y%m%d_%H%M%S).log
```

### 分析瓶颈

```python
# 在代码中添加计时
import time

start = time.time()
# ... 执行某个操作
end = time.time()
print(f"耗时: {end - start:.2f}秒")
```

---

## 🎨 高级优化

### 1. 自定义并行策略

```python
from src.agents.parallel_generator import ParallelGenerator

# 根据页面数动态调整workers
total_pages = 12
workers = min(4, (total_pages + 1) // 2)  # 每2页1个worker

generator = ParallelGenerator(llm, max_workers=workers)
```

### 2. 预热缓存

```bash
# 提前生成常见课程的缓存
python3 -c "
from main_optimized import main
import sys

# 模拟输入
sys.stdin = open('/dev/stdin', 'w')
# ... 批量生成
"
```

### 3. 分布式生成（未来）

```python
# 使用Celery或Ray实现分布式
from celery import Celery

@app.task
def generate_page_batch(pages):
    # 在不同机器上并行生成
    pass
```

---

## 📚 相关文档

- `PERFORMANCE_OPTIMIZATION_PLAN.md` - 完整优化方案
- `CODE_REVIEW_REPORT.md` - 代码审查报告
- `CDN_SOLUTION_GUIDE.md` - CDN加载方案
- `README.md` - 项目总览

---

## 🆘 获取帮助

### 报告性能问题

请提供以下信息:
1. 系统环境（OS, Python版本）
2. 配置文件（.env）
3. 运行日志
4. 性能数据（耗时）

### 社区支持

- GitHub Issues: [项目地址]
- 文档反馈: [联系方式]

---

**最后更新**: 2026-01-05
**版本**: v2.0 (优化版)

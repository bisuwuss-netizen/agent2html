#!/bin/bash

# 性能对比测试脚本
# 对比原始版本 vs 优化版本的性能

echo "=========================================="
echo "  性能对比测试"
echo "=========================================="
echo ""

# 测试配置
TEST_TOPIC="车床操作基础"
TEST_MAJOR="机械制造"

# 1. 清空缓存（确保公平对比）
echo "📝 步骤1: 清空缓存..."
rm -rf cache/*.pkl 2>/dev/null
echo "   ✅ 缓存已清空"
echo ""

# 2. 测试原始版本
echo "=========================================="
echo "  测试 1: 原始版本（串行 + 无缓存）"
echo "=========================================="
echo ""

# 临时禁用优化
export USE_OPTIMIZED_WORKFLOW=false

echo "开始测试..."
start_time=$(date +%s)

# 运行原始版本（模拟输入）
echo -e "$TEST_TOPIC\n$TEST_MAJOR\n高职二年级学生\n45分钟\n车床结构,操作步骤\n" | python3 main.py > /tmp/test_original.log 2>&1

end_time=$(date +%s)
original_time=$((end_time - start_time))

echo "✅ 原始版本测试完成"
echo "   耗时: ${original_time}秒"
echo ""

# 3. 清空缓存
echo "📝 清空缓存（准备测试优化版本）..."
rm -rf cache/*.pkl 2>/dev/null
echo ""

# 4. 测试优化版本（首次生成）
echo "=========================================="
echo "  测试 2: 优化版本 - 首次生成（并行 + 无缓存）"
echo "=========================================="
echo ""

# 启用优化
export USE_OPTIMIZED_WORKFLOW=true
export USE_CACHE=true
export USE_PARALLEL_GENERATION=true

echo "开始测试..."
start_time=$(date +%s)

# 运行优化版本
echo -e "$TEST_TOPIC\n$TEST_MAJOR\n高职二年级学生\n45分钟\n车床结构,操作步骤\n" | python3 main_optimized.py > /tmp/test_optimized.log 2>&1

end_time=$(date +%s)
optimized_time=$((end_time - start_time))

echo "✅ 优化版本测试完成"
echo "   耗时: ${optimized_time}秒"
echo ""

# 5. 测试缓存命中
echo "=========================================="
echo "  测试 3: 优化版本 - 缓存命中"
echo "=========================================="
echo ""

echo "开始测试..."
start_time=$(date +%s)

# 再次运行（缓存命中）
echo -e "$TEST_TOPIC\n$TEST_MAJOR\n高职二年级学生\n45分钟\n车床结构,操作步骤\n" | python3 main_optimized.py > /tmp/test_cached.log 2>&1

end_time=$(date +%s)
cached_time=$((end_time - start_time))

echo "✅ 缓存测试完成"
echo "   耗时: ${cached_time}秒"
echo ""

# 6. 计算提升
echo "=========================================="
echo "  性能对比结果"
echo "=========================================="
echo ""

echo "📊 耗时对比:"
echo "   原始版本:       ${original_time}秒"
echo "   优化版本(首次): ${optimized_time}秒"
echo "   优化版本(缓存): ${cached_time}秒"
echo ""

if [ $original_time -gt 0 ]; then
    improvement=$((100 - (optimized_time * 100 / original_time)))
    cache_improvement=$((100 - (cached_time * 100 / original_time)))

    echo "🚀 性能提升:"
    echo "   首次生成: 提速 ${improvement}%"
    echo "   缓存命中: 提速 ${cache_improvement}%"
fi

echo ""
echo "=========================================="
echo "  详细日志"
echo "=========================================="
echo ""
echo "查看详细日志:"
echo "  原始版本: cat /tmp/test_original.log"
echo "  优化版本: cat /tmp/test_optimized.log"
echo "  缓存测试: cat /tmp/test_cached.log"
echo ""

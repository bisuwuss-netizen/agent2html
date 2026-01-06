#!/bin/bash

# 快速测试 CDN 加载方案
# 使用方法: bash quick_test_cdn.sh

echo "=========================================="
echo "  Reveal.js CDN 加载方案快速测试"
echo "=========================================="
echo ""

# 1. 生成测试页面
echo "📝 步骤1: 生成测试页面..."
python3 test_cdn_loading.py
echo ""

# 2. 查找最新生成的测试文件
TEST_FILE=$(ls -t output/test_cdn_*.html | head -1)

if [ -z "$TEST_FILE" ]; then
    echo "❌ 错误: 未找到测试文件"
    exit 1
fi

echo "✅ 测试文件: $TEST_FILE"
echo ""

# 3. 在浏览器中打开
echo "🌐 步骤2: 在浏览器中打开测试页面..."

# 根据操作系统选择浏览器
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$TEST_FILE"
    echo "✅ 已在默认浏览器中打开"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "$TEST_FILE"
    echo "✅ 已在默认浏览器中打开"
else
    echo "⚠️  请手动打开文件: file://$(pwd)/$TEST_FILE"
fi

echo ""
echo "=========================================="
echo "  测试检查清单"
echo "=========================================="
echo ""
echo "请在浏览器中验证以下项目:"
echo ""
echo "✓ [ ] 加载屏幕是否显示（紫色渐变背景）"
echo "✓ [ ] 加载动画是否正常（旋转的圆圈）"
echo "✓ [ ] 是否在 2-10 秒内加载完成"
echo "✓ [ ] 第一页是否显示 '✅ CDN 加载测试成功'"
echo "✓ [ ] 显示的使用 CDN 名称是否正确"
echo "✓ [ ] 按方向键（→）能否切换到下一页"
echo "✓ [ ] 总共有 4 页幻灯片"
echo ""
echo "=========================================="
echo "  调试指南"
echo "=========================================="
echo ""
echo "如果页面无法加载，请按 F12 打开开发者工具，检查:"
echo ""
echo "1. Console 标签页:"
echo "   - 查找 '[CDN Manager]' 开头的日志"
echo "   - 确认是否有 '✅ 成功加载' 的消息"
echo "   - 查看是否有网络错误"
echo ""
echo "2. Network 标签页:"
echo "   - 刷新页面（Cmd+R / Ctrl+R）"
echo "   - 查找 'reveal.min.js' 的请求"
echo "   - 检查状态码是否为 200"
echo "   - 查看是哪个 CDN 成功响应"
echo ""
echo "3. 如果所有 CDN 都失败:"
echo "   - 检查网络连接"
echo "   - 尝试关闭 VPN/代理"
echo "   - 考虑使用本地化方案（见 CDN_SOLUTION_GUIDE.md）"
echo ""
echo "=========================================="
echo "  完成测试后"
echo "=========================================="
echo ""
echo "如果测试通过，可以运行主程序:"
echo ""
echo "  python3 main.py"
echo ""
echo "生成的正式 HTML 文件将使用相同的 CDN 加载策略。"
echo ""

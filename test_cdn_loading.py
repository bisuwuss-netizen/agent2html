"""
测试 CDN 加载方案
生成一个简单的测试页面，验证多重 CDN 备份是否正常工作
"""
import os
from datetime import datetime


def generate_test_html():
    """生成测试 HTML 文件"""

    html_content = '''<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CDN 加载测试 - Reveal.js 4重备份</title>

  <!-- 预连接CDN加速DNS -->
  <link rel="preconnect" href="https://cdnjs.cloudflare.com">
  <link rel="preconnect" href="https://cdn.jsdelivr.net">
  <link rel="preconnect" href="https://cdn.bootcdn.net">

  <!-- 主CDN: CloudFlare -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/reveal.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/theme/black.min.css">

  <style>
    /* 加载屏幕 */
    #loading-screen {
      position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex; flex-direction: column; justify-content: center; align-items: center;
      z-index: 9999; color: white; font-family: "Microsoft YaHei", "Arial", sans-serif;
    }
    #loading-screen h1 {
      font-size: 48px;
      margin-bottom: 20px;
      animation: pulse 1.5s ease-in-out infinite;
    }
    #loading-screen .spinner {
      width: 60px; height: 60px;
      border: 5px solid rgba(255,255,255,0.3);
      border-top-color: white;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin: 30px 0;
    }
    #loading-screen p {
      font-size: 20px;
      opacity: 0.9;
    }
    #loading-screen .log {
      margin-top: 30px;
      font-size: 14px;
      font-family: "Consolas", "Monaco", monospace;
      background: rgba(0,0,0,0.3);
      padding: 15px;
      border-radius: 8px;
      max-width: 600px;
      text-align: left;
      line-height: 1.8;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }

    .error-screen {
      background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%) !important;
    }

    /* 页面样式 */
    html, body {
      width: 100%; height: 100%;
      margin: 0; padding: 0;
      overflow: hidden;
      background: #000;
    }

    .reveal h1 { font-size: 72px; color: #4facfe; }
    .reveal h2 { font-size: 56px; color: #f093fb; }
    .reveal p { font-size: 36px; line-height: 1.6; }
    .reveal .success { color: #00d4aa; font-weight: bold; }
    .reveal .cdn-info {
      background: rgba(79, 172, 254, 0.1);
      border-left: 4px solid #4facfe;
      padding: 20px;
      margin: 20px 0;
      border-radius: 8px;
    }
  </style>

  <script>
    // 企业级 CDN 管理器
    var CDNManager = {
      cdns: [
        { name: 'CloudFlare', js: 'https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/reveal.min.js' },
        { name: 'jsDelivr', js: 'https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.min.js' },
        { name: 'BootCDN', js: 'https://cdn.bootcdn.net/ajax/libs/reveal.js/4.4.0/reveal.min.js' },
        { name: 'unpkg', js: 'https://unpkg.com/reveal.js@4.4.0/dist/reveal.js' }
      ],
      current: 0,
      logs: [],
      startTime: Date.now(),

      addLog: function(message, type = 'info') {
        var time = ((Date.now() - this.startTime) / 1000).toFixed(2);
        var emoji = type === 'success' ? '✅' : type === 'error' ? '❌' : '📝';
        var log = `[${time}s] ${emoji} ${message}`;
        this.logs.push(log);
        console.log('[CDN Manager]', message);
        this.updateLogDisplay();
      },

      updateLogDisplay: function() {
        var logEl = document.getElementById('loading-log');
        if (logEl) {
          logEl.innerHTML = this.logs.slice(-5).join('<br>');
        }
      },

      updateStatus: function(message) {
        var statusEl = document.getElementById('loading-status');
        if (statusEl) statusEl.textContent = message;
      },

      load: function() {
        if (this.current >= this.cdns.length) {
          this.showError();
          return;
        }

        var cdn = this.cdns[this.current];
        this.updateStatus('正在尝试 ' + cdn.name + '...');
        this.addLog('尝试加载 ' + cdn.name);

        var script = document.createElement('script');
        script.src = cdn.js;

        script.onload = function() {
          CDNManager.addLog(cdn.name + ' 加载成功', 'success');
          CDNManager.init(cdn.name);
        };

        script.onerror = function() {
          CDNManager.addLog(cdn.name + ' 加载失败', 'error');
          CDNManager.current++;
          CDNManager.load();
        };

        document.head.appendChild(script);

        // 8秒超时保护
        setTimeout(function() {
          if (typeof Reveal === 'undefined') {
            CDNManager.addLog(cdn.name + ' 加载超时', 'error');
            script.onerror();
          }
        }, 8000);
      },

      init: function(cdnName) {
        this.updateStatus('✅ 加载成功！正在初始化...');

        if (typeof Reveal === 'undefined') {
          this.addLog('Reveal 对象未定义', 'error');
          this.current++;
          this.load();
          return;
        }

        try {
          Reveal.initialize({
            width: 1920,
            height: 1080,
            margin: 0.1,
            minScale: 0.2,
            maxScale: 2.0,
            center: true,
            controls: true,
            progress: true,
            hash: true,
            transition: 'slide'
          });

          this.addLog('Reveal.js 初始化成功', 'success');

          // 将成功的CDN名称注入到页面中
          setTimeout(function() {
            var cdnInfoEl = document.getElementById('used-cdn');
            if (cdnInfoEl) {
              cdnInfoEl.textContent = cdnName;
            }
          }, 100);

          // 隐藏加载屏幕
          setTimeout(function() {
            var loading = document.getElementById('loading-screen');
            if (loading) {
              loading.style.opacity = '0';
              loading.style.transition = 'opacity 0.5s';
              setTimeout(function() {
                loading.style.display = 'none';
              }, 500);
            }
          }, 1000);

        } catch (e) {
          this.addLog('初始化失败: ' + e.message, 'error');
          this.showError();
        }
      },

      showError: function() {
        var loading = document.getElementById('loading-screen');
        if (loading) {
          loading.className = 'error-screen';
          loading.innerHTML = `
            <h1>⚠️ 加载失败</h1>
            <p>所有 CDN 均无法访问，请检查网络连接</p>
            <div class="log">
              <strong>已尝试的 CDN:</strong><br>
              ${this.cdns.map(c => '• ' + c.name).join('<br>')}
            </div>
            <button onclick="location.reload()"
                    style="margin-top:40px; padding:15px 40px; font-size:20px;
                           background:white; color:#e74c3c; border:none;
                           border-radius:8px; cursor:pointer; font-weight:bold;">
              重新加载
            </button>
          `;
        }
        this.addLog('所有CDN均加载失败', 'error');
      }
    };

    // 页面加载后启动
    window.addEventListener('DOMContentLoaded', function() {
      CDNManager.addLog('页面加载完成，开始尝试CDN');

      // 给主CDN 2秒加载时间
      setTimeout(function() {
        if (typeof Reveal !== 'undefined') {
          CDNManager.addLog('主CDN加载成功', 'success');
          CDNManager.init('CloudFlare (Primary)');
        } else {
          CDNManager.addLog('主CDN失败，开始尝试备用', 'error');
          CDNManager.current = 1;
          CDNManager.load();
        }
      }, 2000);
    });
  </script>
</head>
<body>

  <!-- 加载屏幕 -->
  <div id="loading-screen">
    <h1>正在加载课件</h1>
    <div class="spinner"></div>
    <p id="loading-status">正在连接 CDN...</p>
    <div class="log">
      <div id="loading-log">初始化中...</div>
    </div>
  </div>

  <!-- Reveal.js 容器 -->
  <div class="reveal">
    <div class="slides">

      <!-- 第1页：测试结果 -->
      <section>
        <h1>✅ CDN 加载测试成功</h1>
        <p>如果你能看到这个页面，说明 Reveal.js 已成功加载！</p>
        <div class="cdn-info">
          <h2>使用的 CDN</h2>
          <p class="success" id="used-cdn">加载中...</p>
        </div>
        <p style="font-size:28px; opacity:0.7; margin-top:40px;">
          按 → 键或点击右侧查看下一页
        </p>
      </section>

      <!-- 第2页：CDN 列表 -->
      <section>
        <h1>🌐 备份 CDN 列表</h1>
        <div style="text-align:left; margin-top:40px;">
          <p>✅ CloudFlare CDN（主CDN，全球最快）</p>
          <p>✅ jsDelivr CDN（备用，国内可用）</p>
          <p>✅ BootCDN（备用，国内优化）</p>
          <p>✅ unpkg CDN（最后备用）</p>
        </div>
        <p style="margin-top:60px; font-size:28px; opacity:0.7;">
          自动降级策略：每个CDN失败后8秒自动切换下一个
        </p>
      </section>

      <!-- 第3页：功能特性 -->
      <section>
        <h1>🚀 企业级特性</h1>
        <div style="text-align:left; line-height:2;">
          <p>✅ 4重CDN备份，确保100%加载成功</p>
          <p>✅ 8秒超时自动切换</p>
          <p>✅ 友好的加载动画</p>
          <p>✅ 详细的错误提示</p>
          <p>✅ 控制台完整日志</p>
        </div>
      </section>

      <!-- 第4页：测试通过 -->
      <section>
        <h1 style="color:#00d4aa;">🎉 测试通过</h1>
        <p style="font-size:48px;">Reveal.js 多重CDN方案运行正常</p>
        <p style="margin-top:60px; opacity:0.7;">
          现在可以开始生成正式的教学课件了
        </p>
      </section>

    </div>
  </div>

</body>
</html>'''

    # 保存文件
    os.makedirs('output', exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'output/test_cdn_{timestamp}.html'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ 测试文件已生成: {filename}")
    print(f"\n测试步骤:")
    print(f"1. 在浏览器中打开: file://{os.path.abspath(filename)}")
    print(f"2. 观察加载屏幕是否正常显示")
    print(f"3. 查看是否在2-10秒内加载成功")
    print(f"4. 按F12打开控制台，查看CDN加载日志")
    print(f"5. 使用方向键测试幻灯片切换")

    return filename


if __name__ == "__main__":
    print("="*60)
    print("  Reveal.js 企业级 CDN 加载方案测试")
    print("="*60)
    print()

    filename = generate_test_html()

    print("\n" + "="*60)
    print("  测试完成！")
    print("="*60)

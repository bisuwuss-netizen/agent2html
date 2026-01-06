"""
企业级 CDN 加载方案 - 多备份源 + 自动降级
"""

def generate_reveal_js_loader() -> str:
    """
    生成企业级的 reveal.js 加载代码

    策略：
    1. 优先使用 cloudflare CDN（全球稳定）
    2. 失败后自动切换到 jsDelivr（国内可用）
    3. 再失败切换到 BootCDN（国内优化）
    4. 最后使用 unpkg（备用）
    5. 全部失败则显示友好错误提示

    Returns:
        完整的 HTML <head> 部分代码
    """

    return '''<!-- ============ Reveal.js CDN 多重备份加载方案 ============ -->
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{TITLE}}</title>

  <!-- 预连接CDN，加速DNS解析 -->
  <link rel="preconnect" href="https://cdnjs.cloudflare.com">
  <link rel="preconnect" href="https://cdn.jsdelivr.net">
  <link rel="preconnect" href="https://cdn.bootcdn.net">

  <!-- 方案1: CloudFlare CDN（优先，全球最快） -->
  <link id="reveal-css-1" rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/reveal.min.css"
        onerror="this.onerror=null; this.disabled=true; loadBackupCSS();">
  <link id="theme-css-1" rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/theme/black.min.css"
        onerror="this.onerror=null; this.disabled=true;">

  <style id="custom-styles">
    /* 加载中提示 */
    #loading-screen {
      position: fixed;
      top: 0; left: 0;
      width: 100vw; height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      z-index: 9999;
      color: white;
      font-family: "Microsoft YaHei", sans-serif;
    }

    #loading-screen h1 {
      font-size: 48px;
      margin-bottom: 20px;
      animation: pulse 1.5s ease-in-out infinite;
    }

    #loading-screen p {
      font-size: 24px;
      opacity: 0.8;
    }

    #loading-screen .spinner {
      width: 60px;
      height: 60px;
      border: 5px solid rgba(255,255,255,0.3);
      border-top-color: white;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin: 30px 0;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.6; }
    }

    /* 错误提示 */
    .error-screen {
      background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%) !important;
    }

    .error-screen h1::before {
      content: "⚠️ ";
    }

    /* 页面主体样式 */
    html, body {
      width: 100%;
      height: 100%;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background: #000;
    }

    .reveal .slides {
      text-align: left;
    }

    .reveal .slides section {
      width: 1920px;
      height: 1080px;
      padding: 80px;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    /* 文字大小确保可读性 */
    .reveal h1 { font-size: 80px; }
    .reveal h2 { font-size: 60px; }
    .reveal p, .reveal li { font-size: 40px; line-height: 1.6; }

    {{CUSTOM_STYLES}}
  </style>

  <script>
    // 企业级 CDN 加载管理器
    var CDNManager = {
      cdnList: [
        {
          name: 'CloudFlare',
          css: 'https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/reveal.min.css',
          theme: 'https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/theme/black.min.css',
          js: 'https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.4.0/reveal.min.js'
        },
        {
          name: 'jsDelivr',
          css: 'https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.min.css',
          theme: 'https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/theme/black.min.css',
          js: 'https://cdn.jsdelivr.net/npm/reveal.js@4.4.0/dist/reveal.min.js'
        },
        {
          name: 'BootCDN',
          css: 'https://cdn.bootcdn.net/ajax/libs/reveal.js/4.4.0/reveal.min.css',
          theme: 'https://cdn.bootcdn.net/ajax/libs/reveal.js/4.4.0/theme/black.min.css',
          js: 'https://cdn.bootcdn.net/ajax/libs/reveal.js/4.4.0/reveal.min.js'
        },
        {
          name: 'unpkg',
          css: 'https://unpkg.com/reveal.js@4.4.0/dist/reveal.css',
          theme: 'https://unpkg.com/reveal.js@4.4.0/dist/theme/black.css',
          js: 'https://unpkg.com/reveal.js@4.4.0/dist/reveal.js'
        }
      ],
      currentIndex: 0,
      maxRetries: 4,

      updateStatus: function(message) {
        var statusEl = document.getElementById('loading-status');
        if (statusEl) statusEl.textContent = message;
        console.log('[CDN Manager]', message);
      },

      loadNextCDN: function() {
        if (this.currentIndex >= this.maxRetries) {
          this.showError();
          return;
        }

        var cdn = this.cdnList[this.currentIndex];
        this.updateStatus('正在尝试加载 ' + cdn.name + ' CDN...');

        // 加载 CSS（可选，失败不影响）
        if (this.currentIndex > 0) {  // 第一个已经在 HTML 中加载了
          this.loadCSS(cdn.css);
          this.loadCSS(cdn.theme);
        }

        // 加载 JS（关键）
        this.loadScript(cdn.js, function() {
          CDNManager.onSuccess(cdn.name);
        }, function() {
          CDNManager.currentIndex++;
          CDNManager.loadNextCDN();
        });
      },

      loadScript: function(url, onSuccess, onError) {
        var script = document.createElement('script');
        script.src = url;
        script.onload = onSuccess;
        script.onerror = onError;
        script.timeout = 10000;  // 10秒超时
        document.head.appendChild(script);

        // 超时保护
        setTimeout(function() {
          if (typeof Reveal === 'undefined') {
            script.onerror();
          }
        }, 10000);
      },

      loadCSS: function(url) {
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = url;
        link.onerror = function() {
          console.warn('[CDN Manager] CSS 加载失败（不影响功能）:', url);
        };
        document.head.appendChild(link);
      },

      onSuccess: function(cdnName) {
        this.updateStatus('✅ ' + cdnName + ' 加载成功！正在初始化...');
        console.log('[CDN Manager] 成功使用:', cdnName);

        // 初始化 reveal.js
        setTimeout(function() {
          if (typeof Reveal !== 'undefined') {
            CDNManager.initReveal();
          } else {
            console.error('[CDN Manager] Reveal 对象未定义');
            CDNManager.currentIndex++;
            CDNManager.loadNextCDN();
          }
        }, 100);
      },

      initReveal: function() {
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
            transition: 'slide',
            transitionSpeed: 'default',
            backgroundTransition: 'fade'
          });

          this.updateStatus('✅ 初始化完成！');

          // 隐藏加载屏幕
          setTimeout(function() {
            var loading = document.getElementById('loading-screen');
            if (loading) {
              loading.style.opacity = '0';
              loading.style.transition = 'opacity 0.5s';
              setTimeout(function() { loading.style.display = 'none'; }, 500);
            }
          }, 500);

          console.log('[CDN Manager] Reveal.js 初始化成功！');
        } catch (e) {
          console.error('[CDN Manager] 初始化失败:', e);
          this.showError();
        }
      },

      showError: function() {
        var loading = document.getElementById('loading-screen');
        if (loading) {
          loading.className = 'error-screen';
          loading.innerHTML = `
            <h1>加载失败</h1>
            <p>无法加载 Reveal.js 库，请检查网络连接</p>
            <p style="font-size:18px; margin-top:40px; opacity:0.7;">
              已尝试的CDN: CloudFlare, jsDelivr, BootCDN, unpkg<br>
              建议：检查网络连接或联系管理员
            </p>
            <button onclick="location.reload()"
                    style="margin-top:40px; padding:15px 40px; font-size:20px;
                           background:white; color:#e74c3c; border:none;
                           border-radius:8px; cursor:pointer;">
              重新加载
            </button>
          `;
        }
        console.error('[CDN Manager] 所有CDN均加载失败');
      }
    };

    // 页面加载完成后开始尝试加载
    window.addEventListener('DOMContentLoaded', function() {
      // 检查第一个CDN是否已加载
      setTimeout(function() {
        if (typeof Reveal !== 'undefined') {
          CDNManager.onSuccess('CloudFlare (Primary)');
        } else {
          console.warn('[CDN Manager] 主CDN失败，开始尝试备用CDN');
          CDNManager.currentIndex = 1;  // 跳过第一个（已尝试）
          CDNManager.loadNextCDN();
        }
      }, 3000);  // 给主CDN 3秒加载时间
    });
  </script>
</head>'''


def generate_loading_screen() -> str:
    """生成加载屏幕HTML"""
    return '''<!-- 加载屏幕 -->
<div id="loading-screen">
  <h1>正在加载课件</h1>
  <div class="spinner"></div>
  <p id="loading-status">正在连接 CDN...</p>
</div>'''


# 使用示例
if __name__ == "__main__":
    print("=== 企业级 Reveal.js 加载方案 ===")
    print("\n功能特性:")
    print("✅ 4个CDN备份源自动切换")
    print("✅ 10秒超时自动重试")
    print("✅ 友好的加载动画")
    print("✅ 详细的错误提示")
    print("✅ 控制台调试日志")
    print("\n使用方法: 在 designer_generator.py 中调用 generate_reveal_js_loader()")

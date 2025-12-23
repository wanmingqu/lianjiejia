#!/usr/bin/env python3
"""
启动简单的HTTP服务器用于测试前端页面
"""

import http.server
import socketserver
import webbrowser
import os
import threading
import time

def start_test_server():
    """启动测试服务器"""
    PORT = 8080
    web_dir = '/workspace/web'
    
    # 切换到web目录
    os.chdir(web_dir)
    
    # 创建服务器
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    
    print(f"🚀 测试服务器已启动")
    print(f"📍 地址: http://localhost:{PORT}/test-feedback-learning.html")
    print(f"📂 服务目录: {web_dir}")
    print("🔗 点击链接或复制到浏览器中打开")
    print("⚠️  按 Ctrl+C 停止服务器")
    
    # 延迟2秒后自动打开浏览器
    def open_browser():
        time.sleep(2)
        webbrowser.open(f'http://localhost:{PORT}/test-feedback-learning.html')
    
    # 在后台线程中打开浏览器
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        httpd.shutdown()

if __name__ == "__main__":
    start_test_server()
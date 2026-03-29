#!/usr/bin/env python3
"""
三省六部看板 Web 服务器 - 带数据代理和 API

用法：
  python3 web_server_proxy.py [端口]

默认端口：7850
"""

import http.server
import socketserver
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse
import subprocess
import urllib.request
import urllib.parse

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 7850

# 数据文件路径
TASKS_FILE = Path("/root/.openclaw/workspace-taizi/data/tasks.json")

# API 服务端口
API_PORT = 7851

# 添加软链接（如果不存在）
WEB_DATA_DIR = Path(__file__).parent / "web" / "data"
WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
WEB_DATA_LINK = WEB_DATA_DIR / "tasks.json"
if not WEB_DATA_LINK.exists():
    try:
        import os
        os.symlink(TASKS_FILE, WEB_DATA_LINK)
        print(f"✅ 创建数据链接：{WEB_DATA_LINK} -> {TASKS_FILE}")
    except FileExistsError:
        pass

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        web_dir = Path(__file__).parent / "web"
        super().__init__(*args, directory=str(web_dir), **kwargs)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        # 特殊处理 /api/tasks.json 请求
        if parsed.path == '/api/tasks.json' or parsed.path == '/tasks.json':
            if TASKS_FILE.exists():
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(TASKS_FILE, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "数据文件不存在"}).encode())
        
        # 代理 /api/system/status 请求
        elif parsed.path.startswith('/api/system/status'):
            self.proxy_api_request(f'http://localhost:{API_PORT}/api/system/status')
        
        # 代理 /api/agents/list 请求
        elif parsed.path.startswith('/api/agents/list'):
            self.proxy_api_request(f'http://localhost:{API_PORT}/api/agents/list')
        
        # 代理 /api/sessions/stats 请求
        elif parsed.path.startswith('/api/sessions/stats'):
            self.proxy_api_request(f'http://localhost:{API_PORT}/api/sessions/stats')
        
        # 重定向根路径到 index.html
        elif parsed.path == '/':
            self.send_response(302)
            self.send_header('Location', '/index.html')
            self.end_headers()
        
        else:
            super().do_GET()
    
    def proxy_api_request(self, target_url):
        """代理 API 请求到 system_status.py"""
        try:
            response = urllib.request.urlopen(target_url, timeout=10)
            data = response.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        print(f"🏛️  三省六部看板运行中...")
        print(f"📊 访问地址：http://localhost:{PORT}")
        print(f"📁 Web 目录：{Path(__file__).parent / 'web'}")
        print(f"📁 数据文件：{TASKS_FILE}")
        print(f"🔌 API 代理端口：{API_PORT}")
        print(f"按 Ctrl+C 停止服务")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 服务已停止")

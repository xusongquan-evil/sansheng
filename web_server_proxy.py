#!/usr/bin/env python3
"""
三省六部看板 Web 服务器 - 带数据代理

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

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 7850

# 数据文件路径
TASKS_FILE = Path("/root/.openclaw/workspace-taizi/data/tasks.json")

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
        
        # 重定向根路径到 index.html
        elif parsed.path == '/':
            self.send_response(302)
            self.send_header('Location', '/index.html')
            self.end_headers()
        
        else:
            super().do_GET()

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        print(f"🏛️  三省六部看板运行中...")
        print(f"📊 访问地址：http://localhost:{PORT}")
        print(f"📁 Web 目录：{Path(__file__).parent / 'web'}")
        print(f"📁 数据文件：{TASKS_FILE}")
        print(f"按 Ctrl+C 停止服务")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 服务已停止")

#!/usr/bin/env python3
"""
三省六部看板 Web 服务器

用法：
  python3 web_server.py [端口]

默认端口：8080
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "workspace-taizi" / "data"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # 设置 web 目录为根目录
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def do_GET(self):
        # 特殊处理 /data/tasks.json 请求
        if self.path.startswith('/data/tasks.json'):
            tasks_file = DATA_DIR / "tasks.json"
            if tasks_file.exists():
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(tasks_file, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            super().do_GET()

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🏛️  三省六部看板运行中...")
        print(f"📊 访问地址：http://localhost:{PORT}")
        print(f"📁 数据目录：{DATA_DIR}")
        print(f"按 Ctrl+C 停止服务")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 服务已停止")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三省六部 - 系统状态 API

提供 Agent 状态、会话统计、系统监控等数据

API 端点:
- GET /api/system/status - 系统整体状态
- GET /api/agents/list - Agent 列表
- GET /api/sessions/stats - 会话统计
"""

import json
import os
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# 配置
WORKSPACE = "/root/.openclaw/workspace"
DATA_DIR = "/root/.openclaw/workspace-taizi/data"
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")


def get_system_status():
    """获取系统整体状态"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "summary": {}
    }
    
    # 检查看板服务
    try:
        import urllib.request
        start = datetime.now()
        response = urllib.request.urlopen("http://10.1.0.9:7850", timeout=5)
        elapsed = (datetime.now() - start).total_seconds() * 1000
        status["services"]["kanban"] = {
            "status": "running",
            "response_time_ms": round(elapsed, 2),
            "url": "http://10.1.0.9:7850"
        }
    except Exception as e:
        status["services"]["kanban"] = {
            "status": "unreachable",
            "error": str(e)
        }
    
    # 检查 OpenClaw Gateway
    try:
        result = subprocess.run(
            ["openclaw", "gateway", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        status["services"]["gateway"] = {
            "status": "running" if "running" in result.stdout.lower() else "stopped",
            "details": result.stdout.strip()[:200]
        }
    except Exception as e:
        status["services"]["gateway"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # 任务统计
    try:
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        
        status["summary"]["tasks"] = {
            "total": len(tasks),
            "done": sum(1 for t in tasks if t.get("state") == "Done"),
            "in_progress": sum(1 for t in tasks if t.get("state") not in ["Done", "Cancelled"]),
            "cancelled": sum(1 for t in tasks if t.get("state") == "Cancelled")
        }
    except Exception as e:
        status["summary"]["tasks"] = {"error": str(e)}
    
    return status


def get_agents_list():
    """获取 Agent 列表"""
    agents = []
    
    try:
        # 使用 openclaw CLI 获取会话列表
        result = subprocess.run(
            ["openclaw", "sessions", "list", "--limit", "50"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # 尝试解析 JSON 输出
            try:
                data = json.loads(result.stdout)
                sessions = data.get("sessions", [])
                
                for session in sessions:
                    agent_info = {
                        "key": session.get("key", "unknown"),
                        "kind": session.get("kind", "unknown"),
                        "status": session.get("status", "unknown"),
                        "model": session.get("model", "unknown"),
                        "totalTokens": session.get("totalTokens", 0),
                        "contextTokens": session.get("contextTokens", 0),
                        "updatedAt": session.get("updatedAt"),
                        "label": session.get("label") or session.get("displayName", ""),
                        "isMain": session.get("kind") == "other" and "telegram" in session.get("channel", "")
                    }
                    agents.append(agent_info)
            except json.JSONDecodeError:
                # 如果输出不是 JSON，返回原始输出
                agents = [{"raw": result.stdout}]
        else:
            agents = [{"error": result.stderr}]
            
    except Exception as e:
        agents = [{"error": str(e)}]
    
    return {"agents": agents, "count": len(agents)}


def get_sessions_stats():
    """获取会话统计"""
    stats = {
        "timestamp": datetime.now().isoformat(),
        "summary": {},
        "by_status": {},
        "by_kind": {},
        "recent": []
    }
    
    try:
        result = subprocess.run(
            ["openclaw", "sessions", "list", "--limit", "100"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            sessions = data.get("sessions", [])
            
            # 按状态统计
            status_count = {}
            for s in sessions:
                status = s.get("status", "unknown")
                status_count[status] = status_count.get(status, 0) + 1
            stats["by_status"] = status_count
            
            # 按类型统计
            kind_count = {}
            for s in sessions:
                kind = s.get("kind", "unknown")
                kind_count[kind] = kind_count.get(kind, 0) + 1
            stats["by_kind"] = kind_count
            
            # 摘要
            stats["summary"] = {
                "total": len(sessions),
                "running": status_count.get("running", 0),
                "done": status_count.get("done", 0),
                "timeout": status_count.get("timeout", 0),
                "aborted": status_count.get("aborted", 0)
            }
            
            # 最近 10 个会话
            stats["recent"] = [
                {
                    "label": s.get("label") or s.get("displayName", "")[:50],
                    "status": s.get("status"),
                    "model": s.get("model"),
                    "totalTokens": s.get("totalTokens", 0)
                }
                for s in sessions[:10]
            ]
            
    except Exception as e:
        stats["error"] = str(e)
    
    return stats


class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        # 路由
        if path == "/api/system/status":
            data = get_system_status()
        elif path == "/api/agents/list":
            data = get_agents_list()
        elif path == "/api/sessions/stats":
            data = get_sessions_stats()
        else:
            self.send_response(404)
            self.end_headers()
            return
        
        # 返回 JSON
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode())
    
    def log_message(self, format, *args):
        # 沉默日志
        pass


def main():
    port = 7851  # 使用 7851 端口作为 API 服务
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    print(f"🚀 三省六部系统状态 API 运行在 http://0.0.0.0:{port}")
    print(f"   - GET /api/system/status")
    print(f"   - GET /api/agents/list")
    print(f"   - GET /api/sessions/stats")
    server.serve_forever()


if __name__ == "__main__":
    main()

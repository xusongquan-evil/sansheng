#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三省六部 - 服务监控能力

监控服务状态，支持：
- 系统服务（systemd）
- HTTP 端点
- 进程状态

使用示例：
    python3 monitor.py check --service sansheng-web.service
    python3 monitor.py check --url http://10.1.0.9:7850
    python3 monitor.py check --pid 12345
"""

import subprocess
import sys
import json
import argparse
from datetime import datetime


def check_systemd_service(service_name: str) -> dict:
    """检查 systemd 服务状态"""
    result = {
        "name": service_name,
        "type": "systemd",
        "status": "unknown",
        "active": False,
        "message": ""
    }
    
    try:
        # 检查服务状态
        proc = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if proc.stdout.strip() == "active":
            result["status"] = "running"
            result["active"] = True
            result["message"] = f"服务 {service_name} 运行正常"
        else:
            result["status"] = proc.stdout.strip()
            result["active"] = False
            result["message"] = f"服务 {service_name} 状态：{proc.stdout.strip()}"
            
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["message"] = f"检查服务 {service_name} 超时"
    except FileNotFoundError:
        result["status"] = "error"
        result["message"] = "systemctl 命令不存在"
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
    
    return result


def check_http_endpoint(url: str) -> dict:
    """检查 HTTP 端点可用性"""
    result = {
        "name": url,
        "type": "http",
        "status": "unknown",
        "active": False,
        "status_code": None,
        "response_time_ms": None,
        "message": ""
    }
    
    try:
        import urllib.request
        import time
        
        start = time.time()
        response = urllib.request.urlopen(url, timeout=10)
        elapsed = (time.time() - start) * 1000
        
        result["status"] = "running"
        result["active"] = True
        result["status_code"] = response.status
        result["response_time_ms"] = round(elapsed, 2)
        result["message"] = f"HTTP {response.status}, 响应时间 {elapsed:.0f}ms"
        
    except urllib.error.HTTPError as e:
        result["status"] = "error"
        result["status_code"] = e.code
        result["message"] = f"HTTP 错误：{e.code}"
    except urllib.error.URLError as e:
        result["status"] = "unreachable"
        result["message"] = f"无法访问：{str(e.reason)}"
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
    
    return result


def check_process_pid(pid: int) -> dict:
    """检查进程是否存在"""
    result = {
        "name": f"PID {pid}",
        "type": "process",
        "status": "unknown",
        "active": False,
        "message": ""
    }
    
    try:
        import os
        # 检查进程是否存在
        os.kill(pid, 0)
        result["status"] = "running"
        result["active"] = True
        result["message"] = f"进程 {pid} 运行中"
        
    except ProcessLookupError:
        result["status"] = "not_found"
        result["active"] = False
        result["message"] = f"进程 {pid} 不存在"
    except PermissionError:
        # 进程存在但无权限发送信号
        result["status"] = "running"
        result["active"] = True
        result["message"] = f"进程 {pid} 运行中（无权限详情）"
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
    
    return result


def run_all_checks(config_path: str = None) -> dict:
    """执行所有健康检查"""
    # 默认检查列表
    checks = [
        {"type": "systemd", "name": "sansheng-web.service"},
        {"type": "http", "name": "http://10.1.0.9:7850"},
        {"type": "systemd", "name": "openclaw-gateway.service"},
    ]
    
    results = []
    all_healthy = True
    
    for check in checks:
        if check["type"] == "systemd":
            result = check_systemd_service(check["name"])
        elif check["type"] == "http":
            result = check_http_endpoint(check["name"])
        elif check["type"] == "process":
            result = check_process_pid(int(check["name"]))
        else:
            continue
        
        results.append(result)
        if not result["active"]:
            all_healthy = False
    
    return {
        "timestamp": datetime.now().isoformat(),
        "healthy": all_healthy,
        "checks": results
    }


def main():
    parser = argparse.ArgumentParser(description="三省六部服务监控")
    parser.add_argument("action", choices=["check", "all"], help="操作类型")
    parser.add_argument("--service", help="systemd 服务名称")
    parser.add_argument("--url", help="HTTP 端点 URL")
    parser.add_argument("--pid", type=int, help="进程 PID")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    
    args = parser.parse_args()
    
    if args.action == "all":
        result = run_all_checks()
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n{'='*50}")
            print(f"三省六部健康检查 - {result['timestamp']}")
            print(f"总体状态：{'✅ 健康' if result['healthy'] else '❌ 异常'}")
            print(f"{'='*50}\n")
            for check in result["checks"]:
                status_icon = "✅" if check["active"] else "❌"
                print(f"{status_icon} [{check['type']}] {check['name']}")
                print(f"   状态：{check['status']}")
                print(f"   {check['message']}\n")
        return
    
    result = None
    if args.service:
        result = check_systemd_service(args.service)
    elif args.url:
        result = check_http_endpoint(args.url)
    elif args.pid:
        result = check_process_pid(args.pid)
    else:
        parser.print_help()
        sys.exit(1)
    
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        status_icon = "✅" if result["active"] else "❌"
        print(f"\n{status_icon} [{result['type']}] {result['name']}")
        print(f"   状态：{result['status']}")
        print(f"   {result['message']}\n")


if __name__ == "__main__":
    main()

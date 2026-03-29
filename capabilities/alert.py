#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三省六部 - 告警通知能力

通过 Telegram Bot 发送告警通知

使用示例：
    python3 alert.py send --message "服务宕机！"
    python3 alert.py test  # 发送测试告警

配置：
    在 ~/.openclaw/workspace/sansheng/config.yaml 中配置 Telegram Bot Token 和 Chat ID
    或通过环境变量 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID 设置
"""

import subprocess
import sys
import json
import argparse
import os
from datetime import datetime


def get_telegram_config() -> tuple:
    """获取 Telegram 配置"""
    # 优先从环境变量读取
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if token and chat_id:
        return token, chat_id
    
    # 尝试从 config.yaml 读取（简化版，实际应该用 yaml 库）
    config_path = os.path.expanduser("~/.openclaw/workspace/sansheng/config.yaml")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 简单解析（生产环境应该用 proper YAML parser）
                if "telegram:" in content:
                    # TODO: 实现 YAML 解析
                    pass
        except Exception:
            pass
    
    return None, None


def send_telegram_message(message: str, bot_token: str, chat_id: str) -> dict:
    """发送 Telegram 消息"""
    result = {
        "success": False,
        "message": "",
        "timestamp": datetime.now().isoformat()
    }
    
    if not bot_token or not chat_id:
        result["message"] = "❌ 未配置 Telegram Bot Token 或 Chat ID"
        return result
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    try:
        import urllib.request
        import urllib.parse
        
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }).encode()
        
        req = urllib.request.Request(url, data=data, method='POST')
        response = urllib.request.urlopen(req, timeout=10)
        response_data = json.loads(response.read().decode())
        
        if response_data.get("ok"):
            result["success"] = True
            result["message"] = "✅ 告警已发送"
        else:
            result["message"] = f"❌ Telegram API 错误：{response_data.get('description', 'Unknown error')}"
            
    except urllib.error.URLError as e:
        result["message"] = f"❌ 网络错误：{str(e.reason)}"
    except Exception as e:
        result["message"] = f"❌ 发送失败：{str(e)}"
    
    return result


def send_alert(message: str, level: str = "warning") -> dict:
    """发送告警（自动获取配置）"""
    bot_token, chat_id = get_telegram_config()
    
    # 构建告警消息
    emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨", "error": "❌"}
    icon = emoji.get(level, "⚠️")
    
    formatted_message = f"""{icon} *三省六部告警*

{message}

时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return send_telegram_message(formatted_message, bot_token, chat_id)


def test_alert() -> dict:
    """发送测试告警"""
    return send_alert(
        "这是一条测试告警消息\n\n如果您收到此消息，说明告警系统工作正常。",
        level="info"
    )


def main():
    parser = argparse.ArgumentParser(description="三省六部告警通知")
    parser.add_argument("action", choices=["send", "test", "check"], help="操作类型")
    parser.add_argument("--message", "-m", help="告警消息内容")
    parser.add_argument("--level", "-l", choices=["info", "warning", "error", "critical"], default="warning", help="告警级别")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    
    args = parser.parse_args()
    
    result = None
    
    if args.action == "test":
        result = test_alert()
    elif args.action == "send":
        if not args.message:
            parser.error("--message 是必需的")
        result = send_alert(args.message, args.level)
    elif args.action == "check":
        token, chat_id = get_telegram_config()
        result = {
            "configured": bool(token and chat_id),
            "token_exists": bool(token),
            "chat_id_exists": bool(chat_id),
            "message": "✅ 配置完整" if (token and chat_id) else "❌ 未配置 Telegram Bot Token 或 Chat ID"
        }
    
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        status_icon = "✅" if result.get("success", result.get("configured", False)) else "❌"
        print(f"\n{status_icon} {result.get('message', '操作完成')}\n")


if __name__ == "__main__":
    main()

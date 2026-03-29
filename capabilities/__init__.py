# 三省六部 - 扩展能力模块
# 最后更新：2026-03-29

"""
三省六部系统扩展能力注册

能力列表：
- monitor: 服务监控
- alert: 告警通知
- healthcheck: 健康检查（TODO）
- github_sync: GitHub 同步（TODO）
"""

__version__ = "1.0.0"

CAPABILITIES = {
    "monitor": {
        "name": "服务监控",
        "description": "监控系统服务、HTTP 端点、进程状态",
        "script": "monitor.py",
        "enabled": True
    },
    "alert": {
        "name": "告警通知",
        "description": "通过 Telegram 发送告警消息",
        "script": "alert.py",
        "enabled": True
    }
}


def list_capabilities():
    """列出所有可用能力"""
    print("\n三省六部扩展能力\n")
    print(f"{'能力':<15} {'状态':<8} 描述")
    print("-" * 60)
    for key, cap in CAPABILITIES.items():
        status = "✅" if cap["enabled"] else "❌"
        print(f"{key:<15} {status:<8} {cap['description']}")
    print()


if __name__ == "__main__":
    list_capabilities()

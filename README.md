# 三省六部 · 多 Agent 协作系统

基于 OpenClaw 的多 Agent 协作框架，模拟古代三省六部制的决策流程。

## 🏛️ 系统架构

```
皇上 (用户)
  ↓
太子 (分拣) → 中书省 (规划) → 门下省 (审议) → 尚书省 (派发) → 执行部 (六部合并)
```

### 核心特性

- **状态机流转**：9 个状态，严格单向递进
- **门下省审议**：所有方案必须经过审议，支持封驳/准奏
- **权限控制**：每个 Agent 只能调用指定的下一个环节
- **完整日志**：flow_log + progress_log + JSONL，全程可追溯

## 📊 可视化看板

项目包含一个实时任务看板，可以查看所有任务的流转状态。

### 启动看板

```bash
cd sansheng
python3 web_server.py 8080
```

然后访问：http://localhost:8080

### 功能

- 📊 实时任务列表（每 30 秒自动刷新）
- 🎯 状态筛选（全部/进行中/已完成）
- 🔍 任务搜索
- 📈 进度条展示
- 📜 完整流转记录
- 📦 产出物查看

---

### 前置条件

- OpenClaw 2026.3.x 或更高版本
- Python 3.8+
- Node.js 18+

### 安装

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/sansheng.git
cd sansheng

# 复制 Agent SOUL 文件到 OpenClaw
cp agents/*.md ~/.openclaw/workspace-<agent-name>/SOUL.md

# 复制 CLI 工具
cp scripts/task_update.py ~/.openclaw/workspace-<agent-name>/scripts/
```

### 配置 Agent

编辑 `~/.openclaw/openclaw.json`，注册 5 个 Agent：

```bash
openclaw agents add taizi --agent-dir ~/.openclaw/agents/taizi --workspace ~/.openclaw/workspace-taizi --non-interactive
openclaw agents add zhongshu --agent-dir ~/.openclaw/agents/zhongshu --workspace ~/.openclaw/workspace-zhongshu --non-interactive
openclaw agents add menxia --agent-dir ~/.openclaw/agents/menxia --workspace ~/.openclaw/workspace-menxia --non-interactive
openclaw agents add shangshu --agent-dir ~/.openclaw/agents/shangshu --workspace ~/.openclaw/workspace-shangshu --non-interactive
openclaw agents add executor --agent-dir ~/.openclaw/agents/executor --workspace ~/.openclaw/workspace-executor --non-interactive
```

### 重启 Gateway

```bash
openclaw gateway restart
```

## 📖 使用流程

### 1. 下旨

通过你配置的渠道（Telegram/Signal 等）给**太子 Agent**发消息：

```
帮我创建一个用户登录系统，需要邮箱注册和密码登录功能
```

### 2. 自动流转

系统会自动执行完整流程：

1. **太子**：判断为旨意 → 创建任务 → 转中书省
2. **中书省**：起草方案 → 提交门下省审议
3. **门下省**：审议方案 → 准奏/封驳
4. **尚书省**：派发执行部 → 汇总结果
5. **执行部**：实际执行任务
6. **太子**：回奏皇上

### 3. 查看任务状态

```bash
cd ~/.openclaw/workspace-taizi
python3 scripts/task_update.py state TASK-xxx Menxia "提交审议"
cat data/tasks.json | python3 -m json.tool
```

## 🛠️ CLI 工具

### 命令参考

```bash
# 创建任务
python3 scripts/task_update.py create TASK-20260328-001 "任务标题" Zhongshu 中书省

# 更新状态
python3 scripts/task_update.py state TASK-xxx Menxia "提交审议"

# 记录流转
python3 scripts/task_update.py flow TASK-xxx "中书省" "门下省" "提交方案审议"

# 汇报进展
python3 scripts/task_update.py progress TASK-xxx "正在起草方案" "分析🔄|起草|审议"

# 完成任务
python3 scripts/task_update.py done TASK-xxx "/path/to/output" "任务完成摘要"
```

## 📋 状态机

```
Pending → Taizi → Zhongshu → Menxia → Assigned → Doing → Review → Done
                              ↑          ↓
                              └─ 封驳 (最多 2 轮) ─┘
```

| 状态 | 含义 | 负责 Agent |
|------|------|-----------|
| Pending | 待处理旨意 | - |
| Taizi | 太子分拣中 | taizi |
| Zhongshu | 中书省规划中 | zhongshu |
| Menxia | 门下省审议中 | menxia |
| Assigned | 尚书省派发中 | shangshu |
| Doing | 执行部执行中 | executor |
| Review | 尚书省汇总中 | shangshu |
| Done | 已完成 | - |
| Cancelled | 已取消 | - |

## 📚 文档

- [DESIGN.md](docs/DESIGN.md) - 系统设计文档
- [DEPLOY.md](docs/DEPLOY.md) - 详细部署指南
- [agents/](agents/) - 各 Agent 的 SOUL.md 配置

## 🎯 示例任务

参考 [examples/](examples/) 目录中的示例任务。

## 🔧 扩展

### Phase 1（当前）
- ✅ 5 个 Agent + 状态机 + CLI 工具
- ✅ 基础审议流程

### Phase 2（计划）
- [ ] React 看板（任务列表 + 详情 + 活动流）
- [ ] 自动派发机制（状态变更→自动通知下一环节）

### Phase 3（计划）
- [ ] 六部分解（工/兵/户/礼/刑/吏）
- [ ] 调度器（自动重试 + 升级 + 回滚）

## 🤝 贡献

欢迎提 Issue 和 PR！

## 📄 开源协议

MIT License - 详见 [LICENSE](LICENSE)

## 🙏 致谢

灵感来源于中国古代三省六部制，参考了 [edict](https://github.com/cft0808/edict) 项目的核心设计理念。

---

**Built with OpenClaw** 🦞

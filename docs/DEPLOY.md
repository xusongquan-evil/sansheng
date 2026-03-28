# 三省六部系统 · 部署指南

## 一、文件结构

已创建的文件：

```
/root/.openclaw/workspace/sansheng/
├── DESIGN.md                 # 系统设计文档
├── DEPLOY.md                 # 本文件：部署指南
├── SOUL/
│   ├── taizi.md             # 太子·分拣
│   ├── zhongshu.md          # 中书省·规划
│   ├── menxia.md            # 门下省·审议
│   ├── shangshu.md          # 尚书省·派发
│   └── executor.md          # 执行部·六部合并
├── scripts/
│   └── task_update.py       # CLI 工具
└── data/
    └── tasks.json           # 任务数据（运行时生成）
```

## 二、部署步骤

### Step 1：创建 Agent

在 OpenClaw 中注册 5 个 Agent：

```bash
# 太子
openclaw agents add taizi

# 中书省
openclaw agents add zhongshu

# 门下省
openclaw agents add menxia

# 尚书省
openclaw agents add shangshu

# 执行部
openclaw agents add executor
```

### Step 2：配置 SOUL.md

将 SOUL 文件复制到各 Agent workspace：

```bash
# 太子
cp /root/.openclaw/workspace/sansheng/SOUL/taizi.md ~/.openclaw/agents/taizi/SOUL.md

# 中书省
cp /root/.openclaw/workspace/sansheng/SOUL/zhongshu.md ~/.openclaw/agents/zhongshu/SOUL.md

# 门下省
cp /root/.openclaw/workspace/sansheng/SOUL/menxia.md ~/.openclaw/agents/menxia/SOUL.md

# 尚书省
cp /root/.openclaw/workspace/sansheng/SOUL/shangshu.md ~/.openclaw/agents/shangshu/SOUL.md

# 执行部
cp /root/.openclaw/workspace/sansheng/SOUL/executor.md ~/.openclaw/agents/executor/SOUL.md
```

### Step 3：配置权限矩阵

编辑 `~/.openclaw/config/openclaw.json`（或 `openclaw agents edit`），设置 `allowAgents`：

```json
{
  "agents": [
    {
      "id": "taizi",
      "label": "太子",
      "allowAgents": ["zhongshu"]
    },
    {
      "id": "zhongshu",
      "label": "中书省",
      "allowAgents": ["menxia"]
    },
    {
      "id": "menxia",
      "label": "门下省",
      "allowAgents": ["zhongshu", "shangshu"]
    },
    {
      "id": "shangshu",
      "label": "尚书省",
      "allowAgents": ["executor"]
    },
    {
      "id": "executor",
      "label": "执行部",
      "allowAgents": []
    }
  ]
}
```

### Step 4：同步 API Key

确保所有 Agent 都有 API Key 配置：

```bash
# 如果 main agent 已配置 API Key，可以复制到其他 Agent
# 或者逐个配置
openclaw agents edit taizi
# 设置 API Key

# 重复以上步骤配置其他 Agent
```

### Step 5：测试 CLI 工具

```bash
cd /root/.openclaw/workspace/sansheng

# 测试创建任务
python3 scripts/task_update.py create TASK-20260328-001 "测试任务" Zhongshu 中书省

# 查看任务数据
cat data/tasks.json

# 测试状态更新
python3 scripts/task_update.py state TASK-20260328-001 Menxia "提交审议"

# 测试流转记录
python3 scripts/task_update.py flow TASK-20260328-001 "中书省" "门下省" "测试流转"

# 测试进展汇报
python3 scripts/task_update.py progress TASK-20260328-001 "正在处理" "步骤 1🔄|步骤 2"
```

### Step 6：重启 Gateway

```bash
openclaw gateway restart
```

等待 ~5 秒让配置生效。

## 三、使用流程

### 下旨

给太子发消息（通过你配置的渠道，如 Telegram/Signal）：

```
帮我创建一个用户登录系统，需要邮箱注册和密码登录功能
```

### 自动流转

系统会自动执行：

1. **太子**：判断为旨意 → 创建任务 `TASK-xxx` → 转中书省
2. **中书省**：起草方案 → 提交门下省审议
3. **门下省**：审议方案 → 准奏/封驳
4. **尚书省**：派发执行部 → 汇总结果
5. **执行部**：实际执行任务
6. **太子**：回奏皇上

### 查看任务状态

```bash
# 查看所有任务
cat /root/.openclaw/workspace/sansheng/data/tasks.json | python3 -m json.tool

# 或者写个简单的查看脚本
python3 -c "
import json
tasks = json.load(open('/root/.openclaw/workspace/sansheng/data/tasks.json'))
for t in tasks:
    print(f\"{t['id']}: {t['title'][:30]} | {t['state']}\")
"
```

## 四、故障排查

### 问题：Agent 不响应

1. 检查 Gateway 状态：`openclaw gateway status`
2. 检查 Agent 是否在线：`openclaw agents list`
3. 检查 API Key 是否配置正确

### 问题：状态转移失败

1. 检查状态转移是否合法（参考 `task_update.py` 中的 `VALID_TRANSITIONS`）
2. 查看 CLI 输出中的错误信息

### 问题：权限不足

1. 检查 `openclaw.json` 中的 `allowAgents` 配置
2. 确认 Agent ID 拼写正确

## 五、下一步扩展

### Phase 2：实时看板
- 创建 React/Vue 前端
- 展示任务列表、详情、活动流
- 支持状态修改、任务干预

### Phase 3：自动派发
- 状态变更时自动通知下一环节 Agent
- 使用 `sessions_send` 或消息队列

### Phase 4：六部分离
- 将执行部分解为 6 个独立 Agent
- 工部（开发）、兵部（部署）、户部（数据）等
- 尚书省负责协调多个部门

---

**部署完成后，就可以开始使用了！** 🎉

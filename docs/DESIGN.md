# 三省六部系统 · 设计方案

## 一、系统架构

```
皇上 (用户)
  ↓
太子 (分拣) → 中书省 (规划) → 门下省 (审议) → 尚书省 (派发) → 执行部 (六部合并)
```

## 二、Agent 配置

| Agent | ID | 职责 | 权限 (allowAgents) |
|-------|-----|------|-------------------|
| 太子 | taizi | 消息分拣、需求整理、创建任务 | ["zhongshu"] |
| 中书省 | zhongshu | 接旨、规划方案、拆解任务 | ["menxia"] |
| 门下省 | menxia | 审议方案、封驳/准奏 | ["zhongshu", "shangshu"] |
| 尚书省 | shangshu | 派发任务、协调执行、汇总结果 | ["executor"] |
| 执行部 | executor | 实际执行（合并六部职能） | [] |

## 三、任务状态机

### 状态流转

```
Pending → Taizi → Zhongshu → Menxia → Assigned → Doing → Review → Done
                              ↑          ↓
                              └─ 封驳 (最多 2 轮，第 3 轮强制准奏) ─┘
```

### 状态定义

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

## 四、任务数据结构

```json
{
  "id": "TASK-20260328-001",
  "title": "任务标题",
  "state": "Pending",
  "org": "太子",
  "priority": "normal",
  "reviewRound": 0,
  "flow_log": [
    {
      "at": "2026-03-28T10:00:00Z",
      "from": "皇上",
      "to": "太子",
      "remark": "下旨：创建登录注册系统"
    }
  ],
  "progress_log": [
    {
      "at": "2026-03-28T10:05:00Z",
      "agent": "taizi",
      "text": "正在分析消息类型",
      "todos": ["分析消息🔄|创建任务|转交中书省"]
    }
  ],
  "todos": [],
  "output": "",
  "createdAt": "2026-03-28T10:00:00Z",
  "updatedAt": "2026-03-28T10:05:00Z"
}
```

## 五、CLI 工具命令

```bash
# 创建任务
python3 scripts/task_update.py create TASK-20260328-001 "任务标题" Zhongshu 中书省

# 更新状态
python3 scripts/task_update.py state TASK-20260328-001 Menxia "提交审议"

# 记录流转
python3 scripts/task_update.py flow TASK-20260328-001 "中书省" "门下省" "提交方案审议"

# 汇报进展
python3 scripts/task_update.py progress TASK-20260328-001 "正在起草方案" "分析需求🔄|起草方案|提交审议"

# 完成任务
python3 scripts/task_update.py done TASK-20260328-001 "/path/to/output" "任务完成摘要"
```

## 六、部署步骤

1. **创建 Agent Workspace**
   ```bash
   # 为每个 Agent 创建独立 workspace
   mkdir -p ~/.openclaw/agents/{taizi,zhongshu,menxia,shangshu,executor}
   ```

2. **写入 SOUL.md**
   - 将 `sansheng/SOUL/*.md` 复制到各 Agent workspace

3. **配置 openclaw.json**
   - 注册 5 个 Agent
   - 设置 allowAgents 权限矩阵

4. **初始化任务数据**
   ```bash
   mkdir -p sansheng/data
   echo '[]' > sansheng/data/tasks.json
   ```

5. **测试流程**
   - 下一个简单任务
   - 验证状态流转
   - 验证权限控制

## 七、核心规则

### 门下省审议规则
- 所有中书省方案必须经过门下省审议
- 门下省可以封驳（打回重改）或准奏（放行）
- 最多 2 轮封驳，第 3 轮必须准奏（可附改进建议）

### 状态流转规则
- 状态只能单向递进（Pending→Taizi→...→Done）
- 唯一例外：Menxia 可以封驳回 Zhongshu
- Done/Cancelled 是终态，不可修改

### 权限控制规则
- Agent 只能调用 allowAgents 中定义的 Agent
- 越权调用被系统拒绝
- 执行部不能调用其他 Agent（只能执行）

## 八、扩展计划

### Phase 1（当前）
- 5 个 Agent + 状态机 + CLI 工具
- 基础审议流程

### Phase 2
- React 看板（任务列表 + 详情 + 活动流）
- 自动派发机制（状态变更→自动通知下一环节 Agent）

### Phase 3
- 六部拆分（工/兵/户/礼/刑/吏）
- 调度器（自动重试 + 升级 + 回滚）

---

**版本**: v0.1  
**日期**: 2026-03-28  
**状态**: 设计中

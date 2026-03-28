#!/usr/bin/env python3
"""
三省六部任务更新工具

用法:
  # 新建任务
  python3 task_update.py create TASK-20260328-001 "任务标题" Zhongshu 中书省

  # 更新状态
  python3 task_update.py state TASK-20260328-001 Menxia "提交审议"

  # 记录流转
  python3 task_update.py flow TASK-20260328-001 "中书省" "门下省" "提交方案审议"

  # 汇报进展
  python3 task_update.py progress TASK-20260328-001 "正在起草方案" "分析🔄|起草|审议"

  # 完成任务
  python3 task_update.py done TASK-20260328-001 "/path/to/output" "任务完成摘要"
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# 数据文件路径
BASE_DIR = Path(__file__).parent.parent
TASKS_FILE = BASE_DIR / "data" / "tasks.json"

# 状态 - 部门映射
STATE_ORG_MAP = {
    'Taizi': '太子',
    'Zhongshu': '中书省',
    'Menxia': '门下省',
    'Assigned': '尚书省',
    'Doing': '执行部',
    'Review': '尚书省',
    'Done': '完成',
    'Blocked': '阻塞',
}

# 状态转移规则（合法的后继状态）
VALID_TRANSITIONS = {
    'Pending': {'Taizi', 'Cancelled'},
    'Taizi': {'Zhongshu', 'Cancelled'},
    'Zhongshu': {'Menxia', 'Cancelled'},
    'Menxia': {'Assigned', 'Zhongshu', 'Cancelled'},  # 封驳回中书
    'Assigned': {'Doing', 'Blocked', 'Cancelled'},
    'Doing': {'Review', 'Blocked', 'Cancelled'},
    'Review': {'Done', 'Menxia', 'Doing', 'Cancelled'},  # 可打回重审
    'Blocked': {'Doing', 'Assigned', 'Review', 'Cancelled'},
    'Done': set(),  # 终态
    'Cancelled': set(),  # 终态
}


def load_tasks():
    """加载任务列表"""
    if not TASKS_FILE.exists():
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return []
    
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_tasks(tasks):
    """保存任务列表"""
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def now_iso():
    """返回 ISO 格式当前时间"""
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def find_task(tasks, task_id):
    """查找任务"""
    return next((t for t in tasks if t.get('id') == task_id), None)


def cmd_create(task_id, title, state, org, official=None):
    """创建任务"""
    tasks = load_tasks()
    
    # 检查是否已存在
    if find_task(tasks, task_id):
        print(f'⚠️  任务 {task_id} 已存在')
        return
    
    actual_org = STATE_ORG_MAP.get(state, org)
    
    task = {
        'id': task_id,
        'title': title,
        'state': state,
        'org': actual_org,
        'official': official or '',
        'priority': 'normal',
        'reviewRound': 0,
        'flow_log': [{
            'at': now_iso(),
            'from': '皇上',
            'to': actual_org,
            'remark': f'下旨：{title}'
        }],
        'progress_log': [],
        'todos': [],
        'output': '',
        'createdAt': now_iso(),
        'updatedAt': now_iso()
    }
    
    tasks.insert(0, task)
    save_tasks(tasks)
    print(f'✅ 创建任务 {task_id} | {title[:30]} | state={state}')


def cmd_state(task_id, new_state, now_text=None):
    """更新任务状态"""
    tasks = load_tasks()
    task = find_task(tasks, task_id)
    
    if not task:
        print(f'❌ 任务 {task_id} 不存在')
        return
    
    old_state = task['state']
    
    # 检查状态转移合法性
    allowed = VALID_TRANSITIONS.get(old_state)
    if allowed is not None and new_state not in allowed:
        print(f'❌ 非法状态转换：{old_state} → {new_state}')
        print(f'   允许的状态：{allowed}')
        return
    
    # 更新状态
    task['state'] = new_state
    if new_state in STATE_ORG_MAP:
        task['org'] = STATE_ORG_MAP[new_state]
    if now_text:
        task['now'] = now_text
    task['updatedAt'] = now_iso()
    
    save_tasks(tasks)
    print(f'✅ {task_id} 状态更新：{old_state} → {new_state}')


def cmd_flow(task_id, from_dept, to_dept, remark):
    """记录流转"""
    tasks = load_tasks()
    task = find_task(tasks, task_id)
    
    if not task:
        print(f'❌ 任务 {task_id} 不存在')
        return
    
    flow_entry = {
        'at': now_iso(),
        'from': from_dept,
        'to': to_dept,
        'remark': remark
    }
    
    task.setdefault('flow_log', []).append(flow_entry)
    task['org'] = to_dept
    task['updatedAt'] = now_iso()
    
    save_tasks(tasks)
    print(f'✅ {task_id} 流转记录：{from_dept} → {to_dept}')


def cmd_progress(task_id, now_text, todos_pipe=''):
    """汇报进展"""
    tasks = load_tasks()
    task = find_task(tasks, task_id)
    
    if not task:
        print(f'❌ 任务 {task_id} 不存在')
        return
    
    # 解析 todos
    parsed_todos = []
    if todos_pipe:
        for i, item in enumerate(todos_pipe.split('|'), 1):
            item = item.strip()
            if not item:
                continue
            if item.endswith('✅'):
                status = 'completed'
                title = item[:-1].strip()
            elif item.endswith('🔄'):
                status = 'in-progress'
                title = item[:-1].strip()
            else:
                status = 'not-started'
                title = item
            parsed_todos.append({'id': str(i), 'title': title, 'status': status})
    
    # 更新进展
    task['now'] = now_text
    if parsed_todos:
        task['todos'] = parsed_todos
    
    progress_entry = {
        'at': now_iso(),
        'text': now_text,
        'todos': parsed_todos if parsed_todos else task.get('todos', [])
    }
    
    task.setdefault('progress_log', []).append(progress_entry)
    task['updatedAt'] = now_iso()
    
    save_tasks(tasks)
    
    done_cnt = sum(1 for td in task.get('todos', []) if td.get('status') == 'completed')
    total_cnt = len(task.get('todos', []))
    print(f'📡 {task_id} 进展：{now_text[:40]}... [{done_cnt}/{total_cnt}]')


def cmd_done(task_id, output='', summary=''):
    """完成任务"""
    tasks = load_tasks()
    task = find_task(tasks, task_id)
    
    if not task:
        print(f'❌ 任务 {task_id} 不存在')
        return
    
    task['state'] = 'Done'
    task['org'] = '完成'
    task['output'] = output
    task['now'] = summary or '任务已完成'
    
    # 添加完成流转记录
    task.setdefault('flow_log', []).append({
        'at': now_iso(),
        'from': task.get('org', '执行部'),
        'to': '皇上',
        'remark': f'✅ 完成：{summary or "任务已完成"}'
    })
    
    task['updatedAt'] = now_iso()
    
    save_tasks(tasks)
    print(f'✅ {task_id} 已完成')


def print_help():
    """打印帮助"""
    print(__doc__)


if __name__ == '__main__':
    args = sys.argv[1:]
    
    if not args:
        print_help()
        sys.exit(0)
    
    cmd = args[0]
    
    if cmd == 'create':
        if len(args) < 5:
            print('❌ create 命令需要至少 4 个参数：TASK_ID TITLE STATE ORG')
            sys.exit(1)
        cmd_create(args[1], args[2], args[3], args[4], args[5] if len(args) > 5 else None)
    
    elif cmd == 'state':
        if len(args) < 3:
            print('❌ state 命令需要至少 2 个参数：TASK_ID NEW_STATE')
            sys.exit(1)
        cmd_state(args[1], args[2], args[3] if len(args) > 3 else None)
    
    elif cmd == 'flow':
        if len(args) < 5:
            print('❌ flow 命令需要至少 4 个参数：TASK_ID FROM TO REMARK')
            sys.exit(1)
        cmd_flow(args[1], args[2], args[3], args[4])
    
    elif cmd == 'progress':
        if len(args) < 3:
            print('❌ progress 命令需要至少 2 个参数：TASK_ID NOW_TEXT')
            sys.exit(1)
        cmd_progress(args[1], args[2], args[3] if len(args) > 3 else '')
    
    elif cmd == 'done':
        if len(args) < 2:
            print('❌ done 命令需要至少 1 个参数：TASK_ID')
            sys.exit(1)
        cmd_done(args[1], args[2] if len(args) > 2 else '', args[3] if len(args) > 3 else '')
    
    else:
        print(f'❌ 未知命令：{cmd}')
        print_help()
        sys.exit(1)

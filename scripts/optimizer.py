#!/usr/bin/env python3
"""
吏部 · Agent优化器 v2.0
======================

监控Agent权重，执行优化或替换。

用法:
  python3 optimizer.py --status     # 查看所有Agent权重
  python3 optimizer.py --review    # 审查所有Agent
  python3 optimizer.py --optimize <agent_id>  # 优化指定Agent
"""

import json
import pathlib
import subprocess
import sys
import argparse
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional

# ── 配置 ──────────────────────────────────────────────────────────────────

EDICT_HOME = '/home/administrator/edict'
STUDIO_HOME = '/home/administrator/studio'
WEIGHT_FILE = '/tmp/agent_weights.json'
AUDIT_FILE = '/tmp/optimizer_audit.log'

# ── Agent权重数据 ────────────────────────────────────────────────────────

@dataclass
class AgentWeight:
    agent_id: str
    department: str
    weight: int
    status: str  # normal, warning, danger, eliminated
    total_tasks: int
    rejected_tasks: int
    last_review: str
    last_rejection_reason: str
    version: int

def load_weights() -> dict:
    """加载Agent权重数据"""
    if pathlib.Path(WEIGHT_FILE).exists():
        with open(WEIGHT_FILE) as f:
            data = json.load(f)
            return {k: AgentWeight(**v) for k, v in data.items()}
    
    # 初始化默认权重
    default_weights = {
        'taizi': AgentWeight('taizi', '太子', 8, 'normal', 0, 0, '', '', 1),
        'zhongshu': AgentWeight('zhongshu', '中书省', 8, 'normal', 0, 0, '', '', 1),
        'menxia': AgentWeight('menxia', '门下省', 8, 'normal', 0, 0, '', '', 1),
        'shangshu': AgentWeight('shangshu', '尚书省', 8, 'normal', 0, 0, '', '', 1),
        'gongbu': AgentWeight('gongbu', '工部', 8, 'normal', 0, 0, '', '', 1),
        'libu': AgentWeight('libu', '礼部', 8, 'normal', 0, 0, '', '', 1),
        'hubu': AgentWeight('hubu', '户部', 8, 'normal', 0, 0, '', '', 1),
        'xingbu': AgentWeight('xingbu', '刑部', 8, 'normal', 0, 0, '', '', 1),
        'bingbu': AgentWeight('bingbu', '兵部', 8, 'normal', 0, 0, '', '', 1),
        'jiandu': AgentWeight('jiandu', '监察院', 10, 'normal', 0, 0, '', '', 1),
    }
    save_weights(default_weights)
    return default_weights

def save_weights(weights: dict):
    """保存Agent权重数据"""
    with open(WEIGHT_FILE, 'w') as f:
        json.dump({k: asdict(v) for k, v in weights.items()}, f, indent=2)

# ── 权重扣减 ──────────────────────────────────────────────────────────────

def decrease_weight(agent_id: str, reason: str, points: int = 1):
    """扣减Agent权重"""
    weights = load_weights()
    
    if agent_id not in weights:
        print(f'❓ 未知Agent: {agent_id}')
        return
    
    agent = weights[agent_id]
    old_weight = agent.weight
    agent.weight = max(0, agent.weight - points)
    agent.total_tasks += 1
    agent.rejected_tasks += 1
    agent.last_review = datetime.utcnow().isoformat() + 'Z'
    agent.last_rejection_reason = reason
    
    # 更新状态
    if agent.weight <= 1:
        agent.status = 'eliminated'
    elif agent.weight <= 3:
        agent.status = 'danger'
    elif agent.weight <= 5:
        agent.status = 'warning'
    else:
        agent.status = 'normal'
    
    save_weights(weights)
    
    print(f'\n📉 权重扣减: {agent_id}')
    print(f'   部门: {agent.department}')
    print(f'   扣减: {old_weight} → {agent.weight} (-{points})')
    print(f'   原因: {reason}')
    print(f'   状态: {agent.status}')
    
    # 记录日志
    log_audit(agent_id, 'decrease', old_weight, agent.weight, reason)
    
    # 如果是danger或eliminated，执行优化/替换
    if agent.status in ['danger', 'eliminated']:
        trigger_optimization(agent_id)

def increase_weight(agent_id: str, reason: str, points: int = 1):
    """增加Agent权重"""
    weights = load_weights()
    
    if agent_id not in weights:
        print(f'❓ 未知Agent: {agent_id}')
        return
    
    agent = weights[agent_id]
    old_weight = agent.weight
    agent.weight = min(10, agent.weight + points)
    agent.total_tasks += 1
    
    if agent.weight >= 6:
        agent.status = 'normal'
    
    save_weights(weights)
    
    print(f'\n📈 权重增加: {agent_id}')
    print(f'   部门: {agent.department}')
    print(f'   增加: {old_weight} → {agent.weight} (+{points})')
    print(f'   原因: {reason}')
    
    log_audit(agent_id, 'increase', old_weight, agent.weight, reason)

# ── 优化/替换 ────────────────────────────────────────────────────────────

def trigger_optimization(agent_id: str):
    """触发优化流程"""
    weights = load_weights()
    agent = weights.get(agent_id)
    
    if not agent:
        return
    
    print(f'\n⚠️ 触发优化: {agent_id} (权重: {agent.weight})')
    
    if agent.status == 'eliminated':
        print(f'🔴 执行Agent替换: {agent_id}')
        replace_agent(agent_id)
    elif agent.status == 'danger':
        print(f'🟠 执行深度优化: {agent_id}')
        optimize_agent(agent_id)

def optimize_agent(agent_id: str):
    """深度优化Agent"""
    weights = load_weights()
    agent = weights[agent_id]
    
    # 记录优化
    print(f'   正在分析 {agent_id} 的问题...')
    
    # 重置为降级权重
    agent.weight = 5
    agent.status = 'warning'
    agent.version += 1
    
    save_weights(weights)
    
    print(f'   优化完成: {agent_id} v{agent.version}')
    print(f'   新权重: 5 (降级观察)')
    print(f'   建议: 吏部将密切关注此Agent后续表现')
    
    log_audit(agent_id, 'optimized', 0, 5, '深度优化')

def replace_agent(agent_id: str):
    """替换Agent"""
    weights = load_weights()
    agent = weights[agent_id]
    
    print(f'   ⚰️ Agent {agent_id} 已被淘汰')
    print(f'   📋 历史记录:')
    print(f'      总任务: {agent.total_tasks}')
    print(f'      被拒绝: {agent.rejected_tasks}')
    print(f'      最后原因: {agent.last_rejection_reason}')
    
    # 创建新版Agent
    new_id = f'{agent_id}_v{agent.version + 1}'
    weights[new_id] = AgentWeight(
        agent_id=new_id,
        department=agent.department,
        weight=8,  # 新Agent从8开始
        status='normal',
        total_tasks=0,
        rejected_tasks=0,
        last_review='',
        last_rejection_reason='',
        version=1
    )
    
    # 标记旧Agent为eliminated
    agent.status = 'eliminated'
    
    save_weights(weights)
    
    print(f'   ✅ 新Agent已创建: {new_id} (权重: 8)')
    print(f'   📢 通知皇上确认替换')
    
    log_audit(agent_id, 'replaced', agent.weight, 8, f'替换为{new_id}')

# ── 日志 ──────────────────────────────────────────────────────────────────

def log_audit(agent_id: str, action: str, old_val: int, new_val: int, reason: str):
    """记录优化审计"""
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'agent_id': agent_id,
        'action': action,
        'old_value': old_val,
        'new_value': new_val,
        'reason': reason
    }
    
    with open(AUDIT_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

# ── CLI入口 ──────────────────────────────────────────────────────────────

def show_status():
    """显示所有Agent权重"""
    weights = load_weights()
    
    print('\n🏛️ 吏部 · Agent权重状态\n')
    print('=' * 80)
    
    for agent_id, agent in weights.items():
        status_icon = {
            'normal': '🟢',
            'warning': '🟡',
            'danger': '🔴',
            'eliminated': '⚰️'
        }.get(agent.status, '❓')
        
        rejection_rate = '0%'
        if agent.total_tasks > 0:
            rate = agent.rejected_tasks / agent.total_tasks * 100
            rejection_rate = f'{rate:.0f}%'
        
        print(f'{status_icon} {agent_id:15} | 权重: {agent.weight:2} | {agent.department:6} | '
              f'拒绝率: {rejection_rate:4} | v{agent.version}')
        
        if agent.rejected_tasks > 0:
            print(f'                     最后拒绝: {agent.last_rejection_reason[:50]}')
    
    print('=' * 80)
    print('\n权重等级:')
    print('  8-10: 🟢 正常  6-7: 🟡 合格  4-5: 🟠 警示  2-3: 🔴 危险  0-1: ⚰️ 淘汰')
    print()

def main():
    parser = argparse.ArgumentParser(description='吏部 · Agent优化器')
    parser.add_argument('--status', action='store_true', help='查看所有Agent权重')
    parser.add_argument('--review', action='store_true', help='审查所有Agent')
    parser.add_argument('--optimize', help='优化指定Agent')
    parser.add_argument('--decrease', help='扣减权重: --decrease <agent_id> --reason <原因>')
    parser.add_argument('--increase', help='增加权重: --increase <agent_id> --reason <原因>')
    parser.add_argument('--reason', help='原因')
    parser.add_argument('--points', type=int, default=1, help='扣减/增加点数')
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    elif args.review:
        weights = load_weights()
        print('\n🏛️ 吏部 · Agent审查报告\n')
        danger_count = sum(1 for a in weights.values() if a.status in ['danger', 'eliminated'])
        warning_count = sum(1 for a in weights.values() if a.status == 'warning')
        normal_count = sum(1 for a in weights.values() if a.status == 'normal')
        
        print(f'  正常: {normal_count}')
        print(f'  警示: {warning_count}')
        print(f'  危险: {danger_count}')
        
        if danger_count > 0:
            print('\n⚠️ 需要立即处理的Agent:')
            for agent_id, agent in weights.items():
                if agent.status in ['danger', 'eliminated']:
                    print(f'  🔴 {agent_id} (权重{agent.weight}): {agent.last_rejection_reason}')
        else:
            print('\n✅ 所有Agent状态正常')
    elif args.decrease:
        if not args.reason:
            print('❌ 需要提供 --reason')
            return
        decrease_weight(args.decrease, args.reason, args.points)
    elif args.increase:
        if not args.reason:
            print('❌ 需要提供 --reason')
            return
        increase_weight(args.increase, args.reason, args.points)
    else:
        show_status()

if __name__ == '__main__':
    main()

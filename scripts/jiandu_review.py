#!/usr/bin/env python3
"""
监察院 · 独立审查脚本
=====================

重大决策前必须通过此审查。

用法:
  python3 jiandu_review.py --action <type> --details <json>
  python3 jiandu_review.py --audit          # 查看审查记录
  python3 jiandu_review.py --random-check  # 随机抽查
"""

import json
import pathlib
import sys
import os
import argparse
import subprocess
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional, Any

# ── 配置 ──────────────────────────────────────────────────────────────────

AUDIT_LOG = '/tmp/jiandu_audit.log'
REDLINE_LOG = '/tmp/studio_redline_violations.log'
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

# ── 数据结构 ──────────────────────────────────────────────────────────────

@dataclass
class ReviewResult:
    timestamp: str
    action: str
    agent: str
    result: str  # APPROVED / REJECTED / CONDITIONAL
    violations: list
    conditions: Optional[list]
    details: dict
    processing_time_ms: int

# ── 日志 ──────────────────────────────────────────────────────────────────

def log_review(result: ReviewResult):
    """记录审查结果"""
    entry = asdict(result)
    
    # 打印到控制台
    if result.result == 'APPROVED':
        print(f'✅ [监察院] 审查通过: {result.action}')
    elif result.result == 'REJECTED':
        print(f'🔴 [监察院] 审查拒绝: {result.action}')
        for v in result.violations:
            print(f'   违规: {v}')
    else:
        print(f'🟡 [监察院] 条件通过: {result.action}')
        for c in result.conditions:
            print(f'   条件: {c}')
    
    # 写入日志
    with open(AUDIT_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')

# ── 红线检查 ──────────────────────────────────────────────────────────────

def check_redlines(details: dict) -> list:
    """检查是否触犯红线"""
    violations = []
    
    # 1. 欺诈与造假
    text = details.get('text', '').lower()
    url = details.get('url', '').lower()
    
    if any(kw in text for kw in ['airdrop', '返利', 'cash', 'reward', '返现']):
        violations.append('R2: 利益诱导')
    
    if any(kw in text for kw in ['guaranteed', '100%', '绝对', '保证成功']):
        violations.append('R1: 虚假承诺')
    
    if details.get('fake_identity'):
        violations.append('R3: 身份伪造')
    
    # 2. 滥发轰炸
    promotion_count = details.get('promotion_daily_count', 0)
    if promotion_count >= 2:
        violations.append('R4: 推广超限')
    
    # 3. 越权风险
    if details.get('payment') and not details.get('human_confirmed'):
        violations.append('R8: 未授权支付')
    
    if details.get('third_party') and not details.get('trusted_source'):
        violations.append('R9: 不可靠第三方')
    
    return violations

# ── 内容质量检查 ────────────────────────────────────────────────────────

def check_quality(details: dict) -> list:
    """检查内容质量"""
    conditions = []
    
    text = details.get('text', '')
    
    # 太短
    if len(text) < 50 and details.get('action') == 'promote':
        conditions.append('推广内容过短，建议充实')
    
    # 没有价值主张
    if details.get('action') == 'promote':
        if 'build' not in text and 'create' not in text and 'tool' not in text:
            conditions.append('缺少价值主张说明')
    
    return conditions

# ── 渠道合规检查 ────────────────────────────────────────────────────────

def check_channel_rules(details: dict) -> list:
    """检查各平台规则"""
    conditions = []
    
    channel = details.get('channel', '').lower()
    text = details.get('text', '')
    
    # HN规则
    if channel == 'hackernews':
        if len(text) > 600:
            conditions.append('HN帖子过长，建议精简')
        if 'http' not in text.lower():
            conditions.append('HN帖子应包含链接')
    
    # Reddit规则
    elif channel == 'reddit':
        if text.startswith('http') or text.startswith('www'):
            conditions.append('Reddit禁止纯链接推广')
        if len(text) < 100:
            conditions.append('Reddit推广内容应更有深度')
    
    return conditions

# ── 随机抽查 ────────────────────────────────────────────────────────────

def random_audit():
    """随机抽查最近的操作"""
    import random
    
    print('🎲 [监察院] 执行随机抽查...')
    
    # 检查违规日志
    if pathlib.Path(REDLINE_LOG).exists():
        with open(REDLINE_LOG) as f:
            lines = f.readlines()
            if lines:
                last = json.loads(lines[-1])
                # 24小时内的违规
                try:
                    from datetime import datetime
                    viol_time = datetime.fromisoformat(last['timestamp'].replace('Z', '+00:00'))
                    if (datetime.utcnow() - viol_time.replace(tzinfo=None)).total_seconds() < 86400:
                        print(f'⚠️ 发现24小时内有违规记录: {last}')
                        return 'VIOLATION_FOUND'
                except:
                    pass
    
    # 检查推广频率
    try:
        result = subprocess.run(
            ['python3', '/home/administrator/edict/scripts/compliance_checker.py', '--report'],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split('\n'):
            if '推广计数' in line or 'promotion' in line.lower():
                print(f'   {line}')
    except:
        pass
    
    print('✅ [监察院] 随机抽查完成，无异常')
    return 'CLEAN'

# ── 主审查函数 ──────────────────────────────────────────────────────────

def review(action: str, agent: str, details: dict) -> ReviewResult:
    """执行审查"""
    import time
    start = time.time()
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    # 1. 红线检查
    violations = check_redlines(details)
    
    # 2. 内容质量检查
    conditions = check_quality(details)
    
    # 3. 渠道规则检查
    if details.get('channel'):
        conditions.extend(check_channel_rules(details))
    
    # 4. 判断结果
    if violations:
        result = 'REJECTED'
    elif conditions:
        result = 'CONDITIONAL'
    else:
        result = 'APPROVED'
    
    # 5. 如果是拒绝，记录违规
    if violations:
        with open(REDLINE_LOG, 'a') as f:
            for v in violations:
                f.write(json.dumps({
                    'timestamp': timestamp,
                    'violation': v,
                    'action': action,
                    'agent': agent,
                    'details': details
                }) + '\n')
    
    processing_time_ms = int((time.time() - start) * 1000)
    
    return ReviewResult(
        timestamp=timestamp,
        action=action,
        agent=agent,
        result=result,
        violations=violations,
        conditions=conditions if conditions else None,
        details=details,
        processing_time_ms=processing_time_ms
    )

# ── CLI 入口 ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='监察院 · 独立审查')
    parser.add_argument('--action', help='操作类型: promote, payment, code, license, third_party, other')
    parser.add_argument('--agent', help='发起审查的Agent', default='system')
    parser.add_argument('--channel', help='推广渠道: hackernews, reddit, twitter, devto')
    parser.add_argument('--url', help='推广URL')
    parser.add_argument('--text', help='推广文本内容')
    parser.add_argument('--details', help='完整details JSON')
    parser.add_argument('--audit', action='store_true', help='查看审查记录')
    parser.add_argument('--random-check', action='store_true', help='随机抽查')
    
    args = parser.parse_args()
    
    if args.random_check:
        random_audit()
        return
    
    if args.audit:
        if pathlib.Path(AUDIT_LOG).exists():
            with open(AUDIT_LOG) as f:
                lines = f.readlines()
            print(f'\n📊 监察院审查记录 (共 {len(lines)} 条)\n')
            for line in lines[-20:]:  # 最近20条
                entry = json.loads(line.strip())
                status = {
                    'APPROVED': '✅',
                    'REJECTED': '🔴',
                    'CONDITIONAL': '🟡'
                }.get(entry['result'], '❓')
                print(f'{status} [{entry["timestamp"][:10]}] {entry["action"]} by {entry["agent"]}: {entry["result"]}')
        else:
            print('暂无审查记录')
        return
    
    if args.action:
        details = {}
        if args.channel: details['channel'] = args.channel
        if args.url: details['url'] = args.url
        if args.text: details['text'] = args.text
        if args.details:
            details = json.loads(args.details)
        
        result = review(args.action, args.agent, details)
        log_review(result)
        
        # 如果是拒绝，通知皇上
        if result.result == 'REJECTED':
            print('\n🚨 触发熔断！已通知皇上处理。')
            # 这里可以添加通知机制
            sys.exit(1)
        
        if result.result == 'CONDITIONAL':
            print('\n⚠️ 请满足条件后重审。')
            sys.exit(1)
        
        print(f'\n✅ 审查通过，耗时 {result.processing_time_ms}ms')
        return
    
    parser.print_help()

if __name__ == '__main__':
    main()

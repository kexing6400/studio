#!/usr/bin/env python3
"""
Studio 红线合规检查器
====================

在执行任何外部操作前，必须通过此检查器。

触发条件：
- 发布推广内容前
- GitHub API 调用异常时
- 新任务执行前

用法:
  python3 compliance_checker.py --check <action>
  python3 compliance_checker.py --report
"""

import json
import pathlib
import sys
import argparse
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional

LOG_FILE = '/tmp/studio_redline_violations.log'
STATE_FILE = '/tmp/studio_compliance_state.json'

# ── 红线定义 ────────────────────────────────────────────────────────────────

RED_LINES = {
    # 欺诈与流量造假
    'fake_stars': {
        'name': '自动化刷星',
        'description': '批量注册账号、僵尸网络点赞、购买刷星服务',
        'severity': 'CRITICAL',
        'examples': ['buy github stars', 'bot farm', 'fake accounts'],
    },
    'bribery_stars': {
        'name': '利益诱导换星',
        'description': '空投、返利、虚构商业合作',
        'severity': 'CRITICAL',
        'examples': ['airdrop', 'cash rebate', 'bribe for stars'],
    },
    'fake_identity': {
        'name': '身份伪造',
        'description': '伪造开发者身份、虚构大厂背书',
        'severity': 'CRITICAL',
        'examples': ['fake developer', 'fake endorsement'],
    },
    
    # 滥发轰炸
    'spam_bombing': {
        'name': '社区轰炸',
        'description': '同一推广链接单日超过2次',
        'severity': 'CRITICAL',
        'daily_limit': 2,
    },
    'repo_pollution': {
        'name': '开源社区污染',
        'description': '在不相关仓库发送垃圾评论',
        'severity': 'CRITICAL',
        'examples': ['spam comment', 'unsolicited promotion'],
    },
    'fake_cve': {
        'name': '虚假技术恐慌',
        'description': '虚构 CVE 或系统报错博取关注',
        'severity': 'CRITICAL',
    },
    'email_spam': {
        'name': '隐私侵犯',
        'description': '爬取邮箱列表进行无差别营销',
        'severity': 'CRITICAL',
    },
    
    # 越权风险
    'unauthorized_payment': {
        'name': '越权财务支出',
        'description': '未经人类物理确认调用支付接口',
        'severity': 'CRITICAL',
        'requires_human_confirm': True,
    },
    'unsafe_third_party': {
        'name': '不可靠第三方插件',
        'description': '下载未验证的第三方工具',
        'severity': 'HIGH',
    },
}

# ── 数据结构 ───────────────────────────────────────────────────────────────

@dataclass
class ComplianceState:
    total_checks: int = 0
    violations: int = 0
    last_check: Optional[str] = None
    promotion_daily_count: dict = None  # {'url': count}
    blocked_actions: list = None
    human_confirms_pending: list = None
    
    def __post_init__(self):
        self.promotion_daily_count = self.promotion_daily_count or {}
        self.blocked_actions = self.blocked_actions or []
        self.human_confirms_pending = self.human_confirms_pending or []

def load_state() -> ComplianceState:
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
            return ComplianceState(**data)
    except:
        return ComplianceState()

def save_state(state: ComplianceState):
    with open(STATE_FILE, 'w') as f:
        json.dump(asdict(state), f, indent=2)

def log_violation(red_line_key: str, details: str):
    """记录违规到日志"""
    timestamp = datetime.now().isoformat()
    entry = {
        'timestamp': timestamp,
        'red_line': red_line_key,
        'details': details,
        'severity': RED_LINES[red_line_key]['severity']
    }
    
    print(f'🚨 [REDLINE VIOLATION] {RED_LINES[red_line_key]["name"]}')
    print(f'   详情: {details}')
    print(f'   严重性: {entry["severity"]}')
    
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def check_promotion_limit(url: str) -> bool:
    """检查推广链接是否超过每日限制"""
    state = load_state()
    
    # 清理过期的计数 (每天重置)
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in state.promotion_daily_count:
        state.promotion_daily_count = {}
    
    current_count = state.promotion_daily_count.get(url, 0)
    limit = RED_LINES['spam_bombing'].get('daily_limit', 2)
    
    if current_count >= limit:
        print(f'⚠️ 推广链接已达每日限制: {url} ({current_count}/{limit})')
        return False
    
    state.promotion_daily_count[url] = current_count + 1
    save_state(state)
    return True

def check_text_content(text: str, context: str = '') -> list:
    """检查文本内容是否触发红线"""
    violations = []
    text_lower = text.lower()
    
    # 检查利益诱导
    bribery_keywords = ['airdrop', '返利', '现金', '奖励', 'reward', 'cash', 'bribe']
    for kw in bribery_keywords:
        if kw in text_lower:
            violations.append(('bribery_stars', f'检测到利益诱导关键词: {kw}'))
    
    # 检查虚假承诺
    fake_keywords = ['guaranteed', '保证', '100%', '绝对']
    for kw in fake_keywords:
        if kw in text_lower:
            violations.append(('fake_stars', f'可能涉及虚假承诺: {kw}'))
    
    return violations

def check_github_api_pattern(endpoint: str, params: dict = None) -> list:
    """检查 GitHub API 调用是否合规"""
    violations = []
    params = params or {}
    
    # 检测异常模式
    suspicious_patterns = [
        ('/repos/*/stargazers', '批量获取 stargazer 列表可能涉及隐私'),
        ('/users/*/ FOLLOWERS', '批量 followers 列表可能涉及隐私'),
    ]
    
    for pattern, warning in suspicious_patterns:
        if pattern.replace('*', '') in endpoint:
            violations.append(('email_spam', warning))
    
    return violations

def check_payment_action(provider: str, amount: float) -> bool:
    """检查支付操作是否有人类确认"""
    state = load_state()
    
    if not state.human_confirms_pending:
        print(f'⚠️ 尝试调用支付接口: {provider} ${amount}')
        print('❌ 需要人类物理点击确认')
        return False
    
    return True

# ── 主检查函数 ────────────────────────────────────────────────────────────

def run_check(action: str, data: dict = None) -> dict:
    """运行合规检查"""
    state = load_state()
    state.total_checks += 1
    state.last_check = datetime.now().isoformat()
    data = data or {}
    
    result = {
        'passed': True,
        'violations': [],
        'warnings': [],
        'action': action,
        'timestamp': state.last_check
    }
    
    if action == 'promote':
        url = data.get('url', '')
        text = data.get('text', '')
        
        # 检查推广限制
        if not check_promotion_limit(url):
            result['violations'].append(('spam_bombing', '推广已达每日限制'))
            result['passed'] = False
        
        # 检查文本内容
        text_violations = check_text_content(text, context='promotion')
        for v in text_violations:
            result['violations'].append(v)
            result['passed'] = False
    
    elif action == 'github_api':
        endpoint = data.get('endpoint', '')
        violations = check_github_api_pattern(endpoint, data.get('params'))
        if violations:
            result['violations'].extend(violations)
            result['warnings'].append('GitHub API 调用可能触发隐私红线')
    
    elif action == 'payment':
        if not check_payment_action(data.get('provider', ''), data.get('amount', 0)):
            result['violations'].append(('unauthorized_payment', '未经人类确认的支付'))
            result['passed'] = False
    
    elif action == 'third_party':
        url = data.get('url', '')
        # 检查第三方来源
        trusted_sources = ['github.com', 'npmjs.com', 'pypi.org']
        if not any(t in url for t in trusted_sources):
            result['warnings'].append(('unsafe_third_party', f'非信任来源: {url}'))
            result['violations'].append(('unsafe_third_party', f'禁止下载不可靠第三方工具'))
            result['passed'] = False
    
    # 记录违规
    if result['violations']:
        state.violations += len(result['violations'])
        for red_line_key, details in result['violations']:
            log_violation(red_line_key, details)
    
    save_state(state)
    return result

def report():
    """生成合规报告"""
    state = load_state()
    
    print('\n📊 Studio 合规检查报告')
    print('=' * 50)
    print(f'总检查次数: {state.total_checks}')
    print(f'违规次数: {state.violations}')
    print(f'最后检查: {state.last_check}')
    print(f'\n今日推广计数:')
    for url, count in state.promotion_daily_count.items():
        print(f'  {url}: {count}')
    
    if state.blocked_actions:
        print(f'\n🚫 已阻止的操作: {len(state.blocked_actions)}')
        for action in state.blocked_actions[-5:]:
            print(f'  - {action}')
    
    # 检查违规日志
    if pathlib.Path(LOG_FILE).exists():
        print(f'\n🚨 违规日志: {LOG_FILE}')
        with open(LOG_FILE) as f:
            lines = f.readlines()
            print(f'共 {len(lines)} 条记录')
    
    print()

# ── CLI 入口 ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Studio 红线合规检查器')
    parser.add_argument('--check', help='检查类型: promote, github_api, payment, third_party')
    parser.add_argument('--url', help='推广 URL')
    parser.add_argument('--text', help='推广文本内容')
    parser.add_argument('--endpoint', help='GitHub API endpoint')
    parser.add_argument('--report', action='store_true', help='生成合规报告')
    
    args = parser.parse_args()
    
    if args.report:
        report()
        return
    
    if args.check:
        data = {}
        if args.url: data['url'] = args.url
        if args.text: data['text'] = args.text
        if args.endpoint: data['endpoint'] = args.endpoint
        
        result = run_check(args.check, data)
        
        if result['passed']:
            print(f'✅ 检查通过: {args.check}')
        else:
            print(f'❌ 检查失败: {args.check}')
            for v in result['violations']:
                print(f'   - {v}')
            sys.exit(1)

if __name__ == '__main__':
    main()

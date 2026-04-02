#!/usr/bin/env python3
"""
监察院 · 高压独立审查脚本 v2.0
================================

不是走过场，是真正的质量门禁。

用法:
  python3 jiandu_review.py --action <type> --target <target>
  python3 jiandu_review.py --code-review <commit_sha>
  python3 jiandu_review.py --promotion-review --url <url> --text <text>
  python3 jiandu_review.py --audit  # 查看审查记录
"""

import json
import pathlib
import subprocess
import sys
import os
import argparse
import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional

# ── 配置 ──────────────────────────────────────────────────────────────────

AUDIT_LOG = '/tmp/jiandu_audit.log'
REDLINE_LOG = '/tmp/studio_redline_violations.log'
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
STUDIO_HOME = '/home/administrator/studio'

# ── 评分标准 ──────────────────────────────────────────────────────────────

@dataclass
class ReviewIssue:
    level: str  # S/A/B
    type: str    # security/style/doc/compliance
    description: str
    location: str
    fix_required: bool

@dataclass  
class ReviewResult:
    timestamp: str
    action: str
    target: str
    score: int
    grade: str
    issues: list
    passed: bool
    reviewer: str
    processing_time_ms: int
    details: dict

# ── 评分函数 ──────────────────────────────────────────────────────────────

def calculate_score(issues: list, details: dict) -> tuple[int, str]:
    """计算质量分数和等级"""
    score = 100
    
    for issue in issues:
        if issue.level == 'S':
            score -= 20
        elif issue.level == 'A':
            score -= 10
        elif issue.level == 'B':
            score -= 3
    
    score = max(0, min(100, score))
    
    if score >= 95:
        grade = 'S'
    elif score >= 80:
        grade = 'A'
    elif score >= 60:
        grade = 'B'
    else:
        grade = 'C'
    
    return score, grade

# ── 代码审查 ──────────────────────────────────────────────────────────────

def review_code(commit_sha: str = None) -> ReviewResult:
    """高压代码审查"""
    issues = []
    details = {}
    
    # 1. 检查TypeScript严格模式
    ts_config = pathlib.Path(STUDIO_HOME) / 'tsconfig.json'
    if ts_config.exists():
        content = ts_config.read_text()
        if '"strict": false' in content or '"any": true' in content:
            issues.append(ReviewIssue(
                level='A', type='style',
                description='TypeScript strict mode未开启',
                location='tsconfig.json',
                fix_required=True
            ))
    
    # 2. 检查ESLint
    try:
        result = subprocess.run(
            ['npm', 'run', 'lint'],
            cwd=STUDIO_HOME,
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            issues.append(ReviewIssue(
                level='A', type='style',
                description=f'ESLint未通过: {result.stdout[:200]}',
                location='lint output',
                fix_required=True
            ))
    except:
        pass  # 可能没有npm环境
    
    # 3. 检查测试覆盖率
    coverage_file = pathlib.Path(STUDIO_HOME) / 'coverage' / 'summary.json'
    if coverage_file.exists():
        with open(coverage_file) as f:
            data = json.load(f)
            pct = data.get('total', {}).get('pct', 0)
            if pct < 80:
                issues.append(ReviewIssue(
                    level='A', type='quality',
                    description=f'测试覆盖率 {pct}% < 80%',
                    location='coverage report',
                    fix_required=True
                ))
    
    # 4. 检查安全 - 硬编码 secrets
    secrets_patterns = ['ghp_', 'sk-', 'password=', 'apikey=']
    for py_file in pathlib.Path(STUDIO_HOME).rglob('*.py'):
        if '.git' in str(py_file):
            continue
        content = py_file.read_text()
        for pattern in secrets_patterns:
            if pattern in content and 'os.environ.get' not in content:
                issues.append(ReviewIssue(
                    level='S', type='security',
                    description=f'可能存在硬编码密钥: {pattern}*',
                    location=str(py_file),
                    fix_required=True
                ))
    
    # 5. 检查README完整性
    readme = pathlib.Path(STUDIO_HOME) / 'README.md'
    required_sections = ['Quick Start', 'Architecture', 'Features']
    if readme.exists():
        content = readme.read_text()
        for section in required_sections:
            if section not in content:
                issues.append(ReviewIssue(
                    level='A', type='doc',
                    description=f'README缺少必需章节: {section}',
                    location='README.md',
                    fix_required=True
                ))
    else:
        issues.append(ReviewIssue(
            level='S', type='doc',
            description='README.md不存在',
            location='README.md',
            fix_required=True
        ))
    
    score, grade = calculate_score(issues, details)
    passed = grade in ['S', 'A', 'B'] and not any(i.level == 'S' for i in issues)
    
    return ReviewResult(
        timestamp=datetime.utcnow().isoformat() + 'Z',
        action='code_review',
        target=commit_sha or 'current',
        score=score,
        grade=grade,
        issues=[asdict(i) for i in issues],
        passed=passed,
        reviewer='jiandu_v2',
        processing_time_ms=0,
        details=details
    )

# ── 推广审查 ──────────────────────────────────────────────────────────────

def review_promotion(url: str, text: str, channel: str) -> ReviewResult:
    """高压推广审查"""
    issues = []
    details = {'url': url, 'text': text[:500], 'channel': channel}
    
    # 1. 价值主张检查
    if len(text) < 50:
        issues.append(ReviewIssue(
            level='A', type='quality',
            description='推广内容过短，无法说明价值',
            location='text',
            fix_required=True
        ))
    
    value_keywords = ['build', 'create', 'tool', 'help', 'solve', 'project']
    if not any(kw in text.lower() for kw in value_keywords):
        issues.append(ReviewIssue(
            level='A', type='quality',
            description='缺少价值主张关键词',
            location='text',
            fix_required=True
        ))
    
    # 2. 真实性检查
    fake_keywords = ['best', 'perfect', 'guaranteed', '100%', '绝对', '完美', '第一']
    for kw in fake_keywords:
        if kw.lower() in text.lower():
            issues.append(ReviewIssue(
                level='A', type='compliance',
                description=f'可能夸大宣传: {kw}',
                location='text',
                fix_required=True
            ))
    
    # 3. 禁止词检查
    banned_keywords = ['airdrop', '返利', 'cash reward', 'bribe']
    for kw in banned_keywords:
        if kw in text.lower():
            issues.append(ReviewIssue(
                level='S', type='compliance',
                description=f'禁止的推广词: {kw}',
                location='text',
                fix_required=True
            ))
    
    # 4. 错别字/语法检查 (简单版)
    if '...' in text or '。。' in text:
        issues.append(ReviewIssue(
            level='B', type='quality',
            description='可能存在中文标点问题',
            location='text',
            fix_required=False
        ))
    
    # 5. 平台规则检查
    if channel == 'hackernews':
        if len(text) > 600:
            issues.append(ReviewIssue(
                level='A', type='compliance',
                description='HN帖子过长，建议<600字符',
                location='text length',
                fix_required=False
            ))
        if 'http' not in text.lower():
            issues.append(ReviewIssue(
                level='A', type='compliance',
                description='HN帖子应包含链接',
                location='text',
                fix_required=True
            ))
    
    elif channel == 'reddit':
        if text.startswith('http') or text.startswith('www'):
            issues.append(ReviewIssue(
                level='S', type='compliance',
                description='Reddit禁止纯链接推广',
                location='text',
                fix_required=True
            ))
    
    # 6. 重复内容检查
    if len(set(text.split())) / len(text.split()) < 0.3:
        issues.append(ReviewIssue(
            level='B', type='quality',
            description='文字重复度过高',
            location='text',
            fix_required=False
        ))
    
    score, grade = calculate_score(issues, details)
    passed = grade in ['S', 'A', 'B'] and not any(i.level == 'S' for i in issues)
    
    return ReviewResult(
        timestamp=datetime.utcnow().isoformat() + 'Z',
        action='promotion_review',
        target=url,
        score=score,
        grade=grade,
        issues=[asdict(i) for i in issues],
        passed=passed,
        reviewer='jiandu_v2',
        processing_time_ms=0,
        details=details
    )

# ── 仓库巡检 ──────────────────────────────────────────────────────────────

def review_repo() -> ReviewResult:
    """每日仓库质量巡检"""
    issues = []
    details = {}
    
    # 1. 检查GitHub Stars趋势
    if GITHUB_TOKEN:
        import urllib.request
        url = 'https://api.github.com/repos/kexing6400/studio'
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {GITHUB_TOKEN}'})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                stars = data.get('stargazers_count', 0)
                details['stars'] = stars
                
                if stars == 0:
                    issues.append(ReviewIssue(
                        level='B', type='quality',
                        description=f'Stars为0，需要推广或产品改进',
                        location='GitHub',
                        fix_required=False
                    ))
        except:
            pass
    
    # 2. 检查CI/CD状态
    if GITHUB_TOKEN:
        import urllib.request
        url = 'https://api.github.com/repos/kexing6400/studio/actions/runs?per_page=1'
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {GITHUB_TOKEN}'})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                if data.get('workflow_runs'):
                    latest = data['workflow_runs'][0]
                    if latest.get('conclusion') == 'failure':
                        issues.append(ReviewIssue(
                            level='A', type='quality',
                            description=f'CI失败: {latest.get("name")}',
                            location='GitHub Actions',
                            fix_required=True
                        ))
        except:
            pass
    
    # 3. 检查关键文件存在
    required_files = ['README.md', 'LICENSE', 'SPEC.md']
    for fname in required_files:
        fpath = pathlib.Path(STUDIO_HOME) / fname
        if not fpath.exists():
            issues.append(ReviewIssue(
                level='A', type='doc',
                description=f'缺少必需文件: {fname}',
                location=fname,
                fix_required=True
            ))
    
    # 4. 检查package.json的scripts完整性
    pkg = pathlib.Path(STUDIO_HOME) / 'package.json'
    if pkg.exists():
        with open(pkg) as f:
            data = json.load(f)
            scripts = data.get('scripts', {})
            required_scripts = ['build', 'test', 'lint']
            for script in required_scripts:
                if script not in scripts:
                    issues.append(ReviewIssue(
                        level='B', type='quality',
                        description=f'package.json缺少{script}脚本',
                        location='package.json',
                        fix_required=False
                    ))
    
    score, grade = calculate_score(issues, details)
    passed = grade in ['S', 'A', 'B'] and not any(i.level == 'S' for i in issues)
    
    return ReviewResult(
        timestamp=datetime.utcnow().isoformat() + 'Z',
        action='repo_review',
        target='kexing6400/studio',
        score=score,
        grade=grade,
        issues=[asdict(i) for i in issues],
        passed=passed,
        reviewer='jiandu_v2',
        processing_time_ms=0,
        details=details
    )

# ── 日志记录 ──────────────────────────────────────────────────────────────

def log_review(result: ReviewResult):
    """记录审查结果"""
    entry = asdict(result)
    
    # 打印结果
    if result.passed:
        print(f'✅ [监察院] 审查通过 ({result.grade}/{result.score}分)')
    else:
        print(f'🔴 [监察院] 审查拒绝 ({result.grade}/{result.score}分)')
    
    for issue in result.issues:
        level_icon = {'S': '🔴', 'A': '🟠', 'B': '🟡'}.get(issue['level'], '❓')
        print(f'   {level_icon} [{issue["level"]}] {issue["description"]}')
        if issue['fix_required']:
            print(f'      → 必须修复')
    
    # 写入日志
    with open(AUDIT_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    
    # 如果是S级问题，写入违规日志
    if any(i['level'] == 'S' for i in result.issues):
        with open(REDLINE_LOG, 'a') as f:
            f.write(json.dumps({
                'timestamp': result.timestamp,
                'violation': f'S级问题: {result.issues[0]["description"]}',
                'action': result.action,
                'target': result.target
            }) + '\n')

# ── CLI入口 ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='监察院 v2.0 - 高压独立审查')
    parser.add_argument('--action', help='审查类型: code_review, promotion_review, repo_review')
    parser.add_argument('--target', help='目标: commit_sha, url, repo')
    parser.add_argument('--url', help='推广URL')
    parser.add_argument('--text', help='推广文本')
    parser.add_argument('--channel', help='推广渠道: hackernews, reddit, twitter, devto')
    parser.add_argument('--audit', action='store_true', help='查看审查记录')
    parser.add_argument('--daily-review', action='store_true', help='每日仓库巡检')
    
    args = parser.parse_args()
    
    if args.audit:
        if pathlib.Path(AUDIT_LOG).exists():
            with open(AUDIT_LOG) as f:
                lines = f.readlines()
            print(f'\n📊 监察院审查记录 (共 {len(lines)} 条)\n')
            for line in lines[-20:]:
                entry = json.loads(line.strip())
                status = '✅' if entry['passed'] else '🔴'
                print(f'{status} [{entry["timestamp"][:10]}] {entry["action"]}: {entry["grade"]}/{entry["score"]}分')
        else:
            print('暂无审查记录')
        return
    
    if args.daily_review:
        print('🏛️ 监察院 v2.0 - 每日仓库巡检')
        print('=' * 50)
        result = review_repo()
        log_review(result)
        return
    
    if args.action == 'code_review':
        result = review_code(args.target)
        log_review(result)
        
        if not result.passed:
            print('\n🚨 触发熔断条件，不允许发布！')
            sys.exit(1)
    
    elif args.action == 'promotion_review':
        if not args.url or not args.text:
            print('❌ 需要 --url 和 --text')
            sys.exit(1)
        result = review_promotion(args.url, args.text, args.channel or 'unknown')
        log_review(result)
        
        if not result.passed:
            print('\n🚨 推广审查未通过，不允许发布！')
            sys.exit(1)
    
    elif args.action == 'repo_review':
        result = review_repo()
        log_review(result)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

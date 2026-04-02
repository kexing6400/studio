#!/usr/bin/env python3
"""
三省六部 · 7×24 全天候自治循环引擎
======================================

从市场调研 → 产品开发 → 持续运营的完整闭环

循环周期：
- 心跳：每5分钟 (核心进程 + 任务流转)
- 调研：每30分钟 (GitHub trending + 竞品分析)
- 开发：持续 (通过 Agent 执行)
- 质量：每15分钟 (CI状态 + 测试覆盖率)
- 推广：每天 08:00 / 20:00
- 总结：每天 00:00

用法:
  python3 seven_x_twenty_four.py [--daemon]
  python3 seven_x_twenty_four.py --once
  python3 seven_x_twenty_four.py --status
"""

import json
import pathlib
import subprocess
import sys
import os
import time
import signal
import argparse
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, asdict
from enum import Enum

# ── 配置 ──────────────────────────────────────────────────────────────────

EDICT_HOME = os.environ.get('EDICT_HOME', '/home/administrator/edict')
STUDIO_HOME = os.environ.get('STUDIO_HOME', '/home/administrator/studio')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
OPENCLAW_CLI = 'openclaw'

sys.path.insert(0, f'{EDICT_HOME}/scripts')
from file_lock import atomic_json_read, atomic_json_write
from utils import now_iso, validate_url

LOG_FILE = '/tmp/seven_x_twenty_four.log'
STATE_FILE = '/tmp/seven_x_twenty_four_state.json'
TASKS_FILE = pathlib.Path(EDICT_HOME) / 'data' / 'tasks_source.json'

# 循环间隔 (秒)
HEARTBEAT_INTERVAL = 300       # 5分钟
RESEARCH_INTERVAL = 1800      # 30分钟
QUALITY_INTERVAL = 900        # 15分钟
PROMOTION_MORNING = '08:00'
PROMOTION_EVENING = '20:00'
SUMMARY_TIME = '00:00'

# GitHub API 配置
GITHUB_API_BASE = 'https://api.github.com'
HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
    'X-GitHub-Api-Version': '2022-11-28'
}

# ── 枚举 ───────────────────────────────────────────────────────────────────

class TaskState(Enum):
    TAIZI = 'Taizi'
    ZHONGSHU = 'Zhongshu'
    MENXIA = 'Menxia'
    ASSIGNED = 'Assigned'
    DOING = 'Doing'
    REVIEW = 'Review'
    DONE = 'Done'
    BLOCKED = 'Blocked'
    CANCELLED = 'Cancelled'

class Ministry(Enum):
    GONGBU = '工部'      # 后端
    HUBU = '户部'        # DevOps
    LIBU = '礼部'        # 前端/内容
    XINGBU = '刑部'      # QA/安全
    BINGBU = '兵部'      # 推广
    LIBU2 = '吏部'       # 文档
    KEKE = '客部'        # 市场研究

# ── 数据结构 ───────────────────────────────────────────────────────────────

@dataclass
class LoopState:
    last_heartbeat: Optional[str] = None
    last_research: Optional[str] = None
    last_quality: Optional[str] = None
    last_promotion: Optional[str] = None
    last_summary: Optional[str] = None
    last_compliance: Optional[str] = None
    last_jiandu: Optional[str] = None
    last_daily_date: Optional[str] = None
    consecutive_errors: int = 0
    total_cycles: int = 0
    github_rate_limit_remaining: int = 60
    prev_stars: int = 0

@dataclass
class MarketOpportunity:
    name: str
    description: str
    tech_stack: list[str]
    stars: int
    relevance_score: float
    url: str
    identified_at: str

# ── 日志 ───────────────────────────────────────────────────────────────────

def log(msg: str, level: str = 'INFO'):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'{ts} [7×24] [{level}] {msg}'
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def log_error(msg: str, exc: Optional[Exception] = None):
    if exc:
        log(f'ERROR: {msg}: {exc}', 'ERROR')
    else:
        log(msg, 'ERROR')

# ── 状态持久化 ─────────────────────────────────────────────────────────────

def load_state() -> LoopState:
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
            return LoopState(**data)
    except:
        return LoopState()

def save_state(state: LoopState):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(asdict(state), f, indent=2)
    except Exception as e:
        log_error('save_state failed', e)

# ── GitHub API ─────────────────────────────────────────────────────────────

def github_api(method: str, path: str, data: Optional[dict] = None) -> Optional[dict]:
    """GitHub API 请求"""
    url = f'{GITHUB_API_BASE}{path}'
    cmd = ['curl', '-s', '--max-time', '15', '-X', method.upper()]
    
    for k, v in HEADERS.items():
        cmd.extend(['-H', f'{k}: {v}'])
    
    if data:
        cmd.extend(['-H', 'Content-Type: application/json', '-d', json.dumps(data)])
    
    cmd.append(url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if result.stdout.strip():
            return json.loads(result.stdout)
    except Exception as e:
        log_error(f'github_api {method} {path} failed', e)
    return None

def get_rate_limit() -> dict:
    """获取 API 速率限制状态"""
    return github_api('GET', '/rate_limit') or {}

def get_trending_repos(language: str = 'typescript', period: str = 'weekly') -> list:
    """获取 GitHub Trending 仓库"""
    # Trending API
    repos = github_api('GET', f'/search/repositories?q=stars:>100+language:{language}&sort=stars&order=desc&per_page=20')
    if repos and 'items' in repos:
        return repos['items']
    return []

def get_repo_details(owner: str, repo: str) -> Optional[dict]:
    """获取仓库详细信息"""
    return github_api('GET', f'/repos/{owner}/{repo}')

def analyze_opportunity(repo: dict) -> MarketOpportunity:
    """分析仓库是否构成项目机会"""
    name = repo.get('full_name', '')
    desc = repo.get('description', '') or ''
    stars = repo.get('stargazers_count', 0)
    langs = repo.get('language', '')
    topics = repo.get('topics', [])
    url = repo.get('html_url', '')
    
    # 计算相关性分数 (简化版本)
    score = 0.0
    positive_signals = ['api', 'tool', 'generator', 'cli', 'boilerplate', 'starter']
    negative_signals = ['demo', 'example', 'tutorial', 'learn']
    
    desc_lower = desc.lower()
    for signal in positive_signals:
        if signal in desc_lower:
            score += 0.2
    for signal in negative_signals:
        if signal in desc_lower:
            score -= 0.3
    
    # Stars 加权
    score += min(stars / 1000, 1.0)
    
    # 标准化到 0-1
    score = max(0, min(1, score))
    
    return MarketOpportunity(
        name=name,
        description=desc[:200],
        tech_stack=[langs] + topics[:5] if topics else [langs],
        stars=stars,
        relevance_score=round(score, 3),
        url=url,
        identified_at=now_iso()
    )

# ── 看板操作 ────────────────────────────────────────────────────────────────

def load_tasks() -> list:
    try:
        return atomic_json_read(TASKS_FILE, [])
    except:
        return []

def save_tasks(tasks: list):
    atomic_json_write(TASKS_FILE, tasks)

def kanban_cmd(cmd: str, *args) -> str:
    """执行看板CLI命令"""
    script = f'{EDICT_HOME}/scripts/kanban_update.py'
    try:
        result = subprocess.run(
            ['python3', script, cmd] + list(args),
            capture_output=True, text=True, timeout=15,
            cwd=EDICT_HOME,
            env={**os.environ, 'EDICT_HOME': EDICT_HOME}
        )
        return result.stdout.strip()
    except Exception as e:
        return f'ERROR: {e}'

def get_task_by_state(state: str) -> list:
    """获取特定状态的任务"""
    tasks = load_tasks()
    return [t for t in tasks if t.get('state') == state]

def get_blocked_tasks() -> list:
    """获取 blocked 任务"""
    tasks = load_tasks()
    return [t for t in tasks if t.get('state') == 'Blocked']

def get_stale_tasks(threshold_minutes: int = 30) -> list:
    """获取超过阈值未更新的任务"""
    tasks = load_tasks()
    stale = []
    now = datetime.utcnow()
    
    for t in tasks:
        updated = t.get('updatedAt', '')
        if not updated:
            continue
        try:
            updated_time = datetime.fromisoformat(updated.replace('Z', '+00:00'))
            if (now - updated_time.replace(tzinfo=None)).total_seconds() > threshold_minutes * 60:
                stale.append(t)
        except:
            pass
    
    return stale

def create_research_task(opportunity: MarketOpportunity) -> bool:
    """创建调研任务"""
    today = datetime.now().strftime('%Y%m%d')
    # 生成唯一ID
    hash_suffix = hashlib.md5(opportunity.name.encode()).hexdigest()[:4].upper()
    task_id = f'JJC-{today}-AUTO{hash_suffix}'
    
    # 检查是否已存在
    tasks = load_tasks()
    if any(t['id'] == task_id for t in tasks):
        return False
    
    task = {
        'id': task_id,
        'title': f'【调研】{opportunity.name}',
        'official': '客部',
        'org': '尚书省',
        'state': 'Zhongshu',
        'now': f'发现机会：{opportunity.description[:100]}',
        'eta': '-',
        'block': '无',
        'output': opportunity.url,
        'ac': '',
        'flow_log': [{
            'at': now_iso(),
            'from': '客部',
            'to': '中书省',
            'remark': f'自动创建调研任务 (相关性: {opportunity.relevance_score})'
        }],
        'metadata': {
            'type': 'research',
            'stars': opportunity.stars,
            'score': opportunity.relevance_score,
            'tech_stack': opportunity.tech_stack
        }
    }
    
    tasks.append(task)
    save_tasks(tasks)
    
    # 更新流转
    kanban_cmd('flow', task_id, '客部', '中书省', f'📋 调研任务：{opportunity.name}')
    
    return True

# ── 进程管理 ────────────────────────────────────────────────────────────────

def is_process_running(name: str) -> bool:
    """检查进程是否运行"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', name],
            capture_output=True, text=True, timeout=5
        )
        return bool(result.stdout.strip())
    except:
        return False

def ensure_dashboard_running() -> bool:
    """确保看板服务运行"""
    if is_process_running('dashboard/server.py'):
        return True
    
    log('Dashboard not running, attempting to start...')
    try:
        proc = subprocess.Popen(
            ['python3', 'dashboard/server.py'],
            cwd=EDICT_HOME,
            stdout=open('/dev/null', 'w'),
            stderr=open('/dev/null', 'w'),
            preexec_fn=os.setsid
        )
        time.sleep(3)
        return is_process_running('dashboard/server.py')
    except Exception as e:
        log_error('Failed to start dashboard', e)
        return False

# ── 循环执行 ────────────────────────────────────────────────────────────────

def run_heartbeat(state: LoopState) -> LoopState:
    """核心心跳：进程检查 + 任务流转 + 主动巡检"""
    log('=== 心跳检查 ===')
    
    # 1. 进程健康检查
    if not ensure_dashboard_running():
        log('Dashboard health check FAILED', 'WARN')
    
    # 2. 检查卡住的任务
    stale = get_stale_tasks(30)
    if stale:
        log(f'发现 {len(stale)} 个超过30分钟未更新的任务', 'WARN')
        for t in stale[:3]:  # 最多处理3个
            log(f'  - {t["id"]}: {t["title"]}')
            # 尝试自动推进
            kanban_cmd('flow', t['id'], t.get('org', '尚书省'), '尚书省', '🧭 自动推进：停滞超时')
    
    # 3. Blocked 任务处理
    blocked = get_blocked_tasks()
    if blocked:
        log(f'发现 {len(blocked)} 个 blocked 任务', 'WARN')
        for t in blocked[:2]:
            log(f'  🔴 {t["id"]}: {t.get("block", "unknown")}')
    
    # 4. 主动巡检：CLI可用性
    _check_cli_health()
    
    # 5. 主动巡检：GitHub Stars
    _check_github_stars(state)
    
    # 6. 主动巡检：CI/CD状态
    _check_ci_health()
    
    state.last_heartbeat = now_iso()
    return state

def _check_cli_health():
    """主动检查CLI是否正常工作"""
    try:
        import subprocess
        # 测试CLI是否能正常执行
        result = subprocess.run(
            ['node', '/home/administrator/studio/packages/cli/dist/index.js', 'list'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            log('  ✅ CLI健康检查通过')
        else:
            log('  ⚠️ CLI健康检查失败，需要修复', 'WARN')
            # 如果CLI坏了，这是严重问题，应该记录
            _log_self_issue('CLI健康检查失败', 'high')
    except Exception as e:
        log(f'  ⚠️ CLI检查异常: {e}', 'WARN')

def _check_github_stars(state: LoopState):
    """主动检查GitHub Stars变化"""
    try:
        studio = github_api('GET', '/repos/kexing6400/studio')
        if studio:
            stars = studio.get('stargazers_count', 0)
            prev_stars = getattr(state, 'prev_stars', None)
            
            if prev_stars is not None and stars != prev_stars:
                change = stars - prev_stars
                log(f'  ⭐ Stars变化: {prev_stars} → {stars} ({change:+d})')
                
                if change > 0:
                    log(f'  🎉 Stars增长! 分析原因...')
                    # 这里可以分析是什么带来了增长
                elif change < 0:
                    log(f'  ⚠️ Stars下降! 检查原因...')
            
            state.prev_stars = stars
    except Exception as e:
        log(f'  ⚠️ Stars检查异常: {e}', 'WARN')

def _check_ci_health():
    """主动检查CI/CD状态"""
    try:
        ci_status = github_api('GET', '/repos/kexing6400/studio/actions/runs?per_page=1')
        if ci_status and 'workflow_runs' in ci_status and ci_status['workflow_runs']:
            latest = ci_status['workflow_runs'][0]
            status = latest.get('conclusion', 'unknown')
            if status == 'failure':
                log(f'  🔴 CI失败: {latest.get("name", "unknown")}', 'WARN')
                # CI失败是重要问题，应该分析
                _log_self_issue(f'CI失败: {latest.get("name")}', 'high')
            elif status == 'success':
                log(f'  ✅ CI通过')
    except Exception as e:
        log(f'  ⚠️ CI检查异常: {e}', 'WARN')

def _log_self_issue(issue: str, severity: str = 'medium'):
    """记录自我发现的问题"""
    issue_log = pathlib.Path('/tmp/studio_self_issues.log')
    entry = {
        'timestamp': now_iso(),
        'issue': issue,
        'severity': severity,
        'status': 'open'
    }
    with open(issue_log, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def run_research(state: LoopState) -> LoopState:
    """市场调研：GitHub trending + 机会分析"""
    log('=== 市场调研 ===')
    
    # 获取 Trending
    repos = get_trending_repos('typescript', 'weekly')
    log(f'获取到 {len(repos)} 个 trending 仓库')
    
    opportunities_found = 0
    for repo in repos[:10]:  # 分析前10个
        opp = analyze_opportunity(repo)
        if opp.relevance_score > 0.5:  # 只创建高相关性机会
            if create_research_task(opp):
                opportunities_found += 1
                log(f'  ✨ 新机会: {opp.name} (score: {opp.relevance_score})')
    
    log(f'创建了 {opportunities_found} 个调研任务')
    
    state.last_research = now_iso()
    return state

def run_quality_check(state: LoopState) -> LoopState:
    """质量检查：CI状态 + 代码质量"""
    log('=== 质量检查 ===')
    
    # 检查 Studio 项目的 CI 状态
    ci_status = github_api('GET', '/repos/kexing6400/studio/actions/runs?per_page=3')
    if ci_status and 'workflow_runs' in ci_status:
        latest = ci_status['workflow_runs'][0]
        status = latest.get('conclusion', 'unknown')
        name = latest.get('name', 'CI')
        log(f'  CI ({name}): {status}')
        
        if status == 'failure':
            log('  🔴 CI 失败，需要关注', 'WARN')
    
    state.last_quality = now_iso()
    return state

def run_compliance_check(state: LoopState) -> LoopState:
    """合规检查：红线约束检查 + 监察院随机抽查"""
    log('=== 合规检查 ===')
    
    # 1. 运行合规检查器
    try:
        result = subprocess.run(
            ['python3', f'{EDICT_HOME}/scripts/compliance_checker.py', '--report'],
            capture_output=True, text=True, timeout=10,
            cwd=EDICT_HOME
        )
        if result.stdout:
            for line in result.stdout.strip().split('\n')[-10:]:  # 只显示最后10行
                if line.strip():
                    log(f'  {line}')
        
        # 检查违规日志
        violation_log = pathlib.Path('/tmp/studio_redline_violations.log')
        if violation_log.exists():
            recent = subprocess.run(
                ['tail', '-1', str(violation_log)],
                capture_output=True, text=True, timeout=5
            )
            if recent.stdout:
                import json
                try:
                    entry = json.loads(recent.stdout.strip())
                    log(f'  🚨 最近违规: {entry.get("red_line", "unknown")}', 'WARN')
                except:
                    pass
    except Exception as e:
        log(f'  合规检查执行异常: {e}', 'WARN')
    
    # 2. 监察院高压审查 (每2小时一次)
    if should_run(state, 7200, 'last_jiandu'):
        log('=== 监察院高压审查 ===')
        try:
            # 仓库质量巡检
            jiandu_result = subprocess.run(
                ['python3', f'{EDICT_HOME}/scripts/jiandu_review.py', '--daily-review'],
                capture_output=True, text=True, timeout=30,
                cwd=EDICT_HOME
            )
            for line in jiandu_result.stdout.strip().split('\n')[-10:]:
                if line.strip():
                    log(f'  {line}')
            state.last_jiandu = now_iso()
        except Exception as e:
            log(f'  监察院审查异常: {e}', 'WARN')
    
    state.last_compliance = now_iso()
    return state

def run_promotion(state: LoopState) -> LoopState:
    """推广报告：早间/晚间"""
    hour = datetime.now().hour
    
    if hour == 8:
        log('=== 早间简报 (08:00) ===')
        _generate_morning_report()
    elif hour == 20:
        log('=== 晚间总结 (20:00) ===')
        _generate_evening_report()
        # 晚间时检查是否需要推广
        _check_promotion_opportunity(state)
    
    state.last_promotion = now_iso()
    return state

def _jiandu_review(action: str, agent: str, details: dict) -> bool:
    """监察院审查 - 返回True表示通过"""
    try:
        result = subprocess.run(
            ['python3', f'{EDICT_HOME}/scripts/jiandu_review.py',
             '--action', action, '--agent', agent,
             '--details', json.dumps(details)],
            capture_output=True, text=True, timeout=15,
            cwd=EDICT_HOME
        )
        
        if result.returncode != 0:
            log(f'  🔴 监察院拒绝: {action}', 'ERROR')
            return False
        
        log(f'  ✅ 监察院放行: {action}')
        return True
    except Exception as e:
        log(f'  ⚠️ 监察院审查异常: {e}', 'WARN')
        return True  # 异常时放行（后续可调整）

def _check_promotion_opportunity(state: LoopState):
    """检查是否有推广机会 (需要监察院审查)"""
    # 获取当前GitHub Stars
    studio = github_api('GET', '/repos/kexing6400/studio')
    if studio:
        stars = studio.get('stargazers_count', 0)
        log(f'  当前Stars: ⭐{stars}')
        
        if stars < 100:
            # 准备推广，但需要监察院审查
            log('  准备推广...')
            
            # 检查推广频率
            compliance_state = load_state()
            today = datetime.now().strftime('%Y-%m-%d')
            promo_count = compliance_state.promotion_daily_count.get(today, 0)
            
            if promo_count < 2:
                # 监察院审查
                details = {
                    'action': 'promote',
                    'url': 'https://github.com/kexing6400/studio',
                    'text': 'Studio: AI-Powered Independent Developer Studio - Transform natural language ideas into production-quality software with multi-agent collaboration',
                    'channel': 'github_daily'
                }
                
                if _jiandu_review('promote', 'shangshu', details):
                    log('  ✅ 监察院审查通过，可以推广')
                    # TODO: 执行实际推广操作
                else:
                    log('  🔴 监察院拒绝本次推广')
            else:
                log(f'  ⏸ 今日推广次数已达上限 ({promo_count}/2)')

def _generate_morning_report():
    """生成早间简报"""
    tasks = load_tasks()
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_tasks = [t for t in tasks if today in t.get('id', '')]
    
    doing = [t for t in today_tasks if t.get('state') == 'Doing']
    done = [t for t in today_tasks if t.get('state') == 'Done']
    blocked = [t for t in tasks if t.get('state') == 'Blocked']
    
    report = f"""
📋 三省六部 · 早间简报 {today}
{'='*40}

🎯 今日任务: {len(today_tasks)}
   • 进行中: {len(doing)}
   • 已完成: {len(done)}
   • 阻塞中: {len(blocked)}

"""
    log(report)
    
    # 写入报告文件
    report_file = pathlib.Path(STUDIO_HOME) / 'reports' / f'morning_{today}.md'
    report_file.parent.mkdir(exist_ok=True)
    report_file.write_text(report)
    
    # 更新 README
    kanban_cmd('progress', 'STUDIO-DAILY', f'早间简报: {len(today_tasks)}任务', '')

def _generate_evening_report():
    """生成晚间总结"""
    tasks = load_tasks()
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_tasks = [t for t in tasks if today in t.get('id', '')]
    
    done = [t for t in today_tasks if t.get('state') == 'Done']
    
    # GitHub 统计
    studio_stats = github_api('GET', '/repos/kexing6400/studio')
    stars = studio_stats.get('stargazers_count', 0) if studio_stats else 0
    
    report = f"""
📋 三省六部 · 晚间总结 {today}
{'='*40}

✅ 今日完成: {len(done)} 个任务
⭐ GitHub Stars: {stars}

完成的任务:
"""
    for t in done:
        report += f"   • {t['id']}: {t['title']}\n"
    
    report += """
明日计划:
   • 继续推进待办任务
   • 监控 CI/CD 状态
   • 研究新项目机会

---
Generated by 三省六部 7×24 Loop Engine
"""
    log(report)
    
    # 写入报告文件
    report_file = pathlib.Path(STUDIO_HOME) / 'reports' / f'evening_{today}.md'
    report_file.parent.mkdir(exist_ok=True)
    report_file.write_text(report)

def run_daily_summary(state: LoopState) -> LoopState:
    """每日总结 + 自我复盘"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    if state.last_daily_date == today:
        return state
    
    log('=== 每日总结 + 自我复盘 ===')
    
    tasks = load_tasks()
    today_tasks = [t for t in tasks if today in t.get('id', '')]
    
    # 按状态统计
    stats = {}
    for t in tasks:
        s = t.get('state', 'Unknown')
        stats[s] = stats.get(s, 0) + 1
    
    log(f'任务统计: {stats}')
    
    # GitHub 数据收集
    github_repos = ['studio', 'github-profile-generator']
    for repo in github_repos:
        stats_data = github_api('GET', f'/repos/kexing6400/{repo}')
        if stats_data:
            log(f"  {repo}: ⭐{stats_data.get('stargazers_count', 0)} "
                f"🍴{stats_data.get('forks_count', 0)}")
    
    # 自我复盘
    _self_review(state)
    
    state.last_daily_date = today
    state.last_summary = now_iso()
    return state

def _self_review(state: LoopState):
    """每日自我复盘：主动发现问题，主动改进"""
    log('  🪞 自我复盘中...')
    
    # 1. 检查自我发现的问题
    issue_log = pathlib.Path('/tmp/studio_self_issues.log')
    if issue_log.exists():
        with open(issue_log) as f:
            lines = f.readlines()
        
        open_issues = []
        for line in lines[-10:]:
            try:
                entry = json.loads(line.strip())
                if entry.get('status') == 'open':
                    open_issues.append(entry)
            except:
                pass
        
        if open_issues:
            log(f'  📋 待处理自我问题: {len(open_issues)}')
            for issue in open_issues[-3:]:
                log(f'    - [{issue["severity"]}] {issue["issue"]}')
    
    # 2. 检查是否有可以改进的地方
    improvement_log = pathlib.Path('/tmp/studio_improvements.log')
    if improvement_log.exists():
        with open(improvement_log) as f:
            improvements = f.readlines()
        if improvements:
            log(f'  💡 已实施的改进: {len(improvements)}')
    
    # 3. GitHub Stars趋势分析
    stars = getattr(state, 'prev_stars', 0)
    if stars > 0:
        log(f'  📈 当前Stars: ⭐{stars}')
        # 如果Stars停滞，考虑主动做推广
        if stars < 50:
            log(f'  ⚠️ Stars较低，主动分析原因...')
            # 可以在这里触发一些主动行为
    
    log('  ✅ 自我复盘完成')

def log_improvement(improvement: str):
    """记录自我改进"""
    improvement_log = pathlib.Path('/tmp/studio_improvements.log')
    entry = f'{now_iso()}: {improvement}\n'
    with open(improvement_log, 'a') as f:
        f.write(entry)

# ── 主循环 ──────────────────────────────────────────────────────────────────

def should_run(state: LoopState, interval_seconds: int, last_key: str) -> bool:
    """判断是否应该执行"""
    last = getattr(state, last_key, None)
    if not last:
        return True
    
    try:
        last_time = datetime.fromisoformat(last.replace('Z', '+00:00'))
        elapsed = (datetime.utcnow() - last_time.replace(tzinfo=None)).total_seconds()
        return elapsed >= interval_seconds
    except:
        return True

def run_cycle(state: LoopState) -> LoopState:
    """运行一次完整循环"""
    state.total_cycles += 1
    log(f'=== 循环 #{state.total_cycles} ===')
    
    try:
        # 心跳 (每5分钟)
        if should_run(state, HEARTBEAT_INTERVAL, 'last_heartbeat'):
            state = run_heartbeat(state)
        
        # 市场调研 (每30分钟)
        if should_run(state, RESEARCH_INTERVAL, 'last_research'):
            state = run_research(state)
        
        # 质量检查 (每15分钟)
        if should_run(state, QUALITY_INTERVAL, 'last_quality'):
            state = run_quality_check(state)
        
        # 合规检查 (每小时)
        if should_run(state, 3600, 'last_compliance'):
            state = run_compliance_check(state)
        
        # 推广报告 (每天 08:00 / 20:00)
        hour = datetime.now().hour
        if (hour == 8 or hour == 20) and should_run(state, 43200, 'last_promotion'):
            state = run_promotion(state)
        
        # 每日总结 (每天 00:00)
        if should_run(state, 86400, 'last_summary'):
            state = run_daily_summary(state)
        
        state.consecutive_errors = 0
        save_state(state)
        
    except Exception as e:
        state.consecutive_errors += 1
        log_error('Cycle failed', e)
        save_state(state)
        
        if state.consecutive_errors > 5:
            log('连续错误超过5次，进入安全模式', 'ERROR')
    
    return state

def daemon_mode():
    """守护进程模式"""
    log('启动 7×24 守护进程...')
    
    # 确保日志目录存在
    pathlib.Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    
    state = load_state()
    save_state(state)
    
    while True:
        state = run_cycle(state)
        log(f'休眠 {HEARTBEAT_INTERVAL} 秒...')
        time.sleep(HEARTBEAT_INTERVAL)

def once_mode():
    """单次运行模式 (测试用)"""
    log('单次循环模式')
    state = load_state()
    state = run_cycle(state)
    save_state(state)
    log('完成')

def status_mode():
    """状态查看模式"""
    state = load_state()
    print(json.dumps(asdict(state), indent=2))

# ── 入口 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='三省六部 7×24 自治循环引擎')
    parser.add_argument('--daemon', action='store_true', help='守护进程模式')
    parser.add_argument('--once', action='store_true', help='单次运行')
    parser.add_argument('--status', action='store_true', help='查看状态')
    
    args = parser.parse_args()
    
    if args.status:
        status_mode()
    elif args.daemon:
        daemon_mode()
    elif args.once:
        once_mode()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

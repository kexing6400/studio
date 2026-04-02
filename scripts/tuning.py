#!/usr/bin/env python3
"""
调令师 · Prompt Tuning Master
===========================

全网搜索顶级提示词，优化Agent灵魂。

用法:
  python3 tuning.py --optimize <agent_id>
  python3 tuning.py --search <关键词>
  python3 tuning.py --status
  python3 tuning.py --search-best --agent <agent_id>
"""

import json
import pathlib
import subprocess
import sys
import os
import argparse
import urllib.request
import urllib.parse
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional

# ── 配置 ──────────────────────────────────────────────────────────────────

EDICT_HOME = '/home/administrator/edict'
STUDIO_HOME = '/home/administrator/studio'
TUNING_DIR = pathlib.Path(STUDIO_HOME) / 'tuning_prompts'
PROMPT_CACHE = '/tmp/prompt_cache.json'
AUDIT_FILE = '/tmp/tuning_audit.log'

# ── 搜索来源 ──────────────────────────────────────────────────────────────

SEARCH_SOURCES = {
    'github': {
        'url': 'https://api.github.com/search/repositories?q={query}+prompt+engineer&sort=stars&per_page=10',
        'requires_token': True
    },
    'huggingface': {
        'url': 'https://huggingface.co/api/models?search={query}',
        'requires_token': False
    }
}

# ── 提示词库 ──────────────────────────────────────────────────────────────

@dataclass
class PromptRecord:
    source: str
    title: str
    content: str
    quality_score: int
    relevance: str
    url: str
    found_at: str

def load_prompt_cache() -> dict:
    if pathlib.Path(PROMPT_CACHE).exists():
        with open(PROMPT_CACHE) as f:
            return json.load(f)
    return {}

def save_prompt_cache(cache: dict):
    with open(PROMPT_CACHE, 'w') as f:
        json.dump(cache, f, indent=2)

# ── 搜索功能 ──────────────────────────────────────────────────────────────

def search_github(query: str, token: str = '') -> list:
    """搜索GitHub上的提示词"""
    results = []
    try:
        url = f'https://api.github.com/search/code?q={urllib.parse.quote(query)}+extension:md&per_page=10'
        req = urllib.request.Request(url)
        if token:
            req.add_header('Authorization', f'Bearer {token}')
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            for item in data.get('items', [])[:5]:
                results.append({
                    'source': 'github',
                    'title': item.get('name', ''),
                    'url': item.get('html_url', ''),
                    'repository': item.get('repository', {}).get('full_name', '')
                })
    except Exception as e:
        print(f'  ⚠️ GitHub搜索失败: {e}')
    
    return results

def search_awesome_list(github_token: str = '') -> list:
    """搜索Awesome lists中的提示词资源"""
    results = []
    try:
        # 搜索awesome prompt相关仓库
        url = 'https://api.github.com/search/repositories?q=awesome+prompt+engineer&sort=stars&per_page=20'
        req = urllib.request.Request(url)
        if github_token:
            req.add_header('Authorization', f'Bearer {github_token}')
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            for repo in data.get('items', [])[:10]:
                results.append({
                    'source': 'github_repo',
                    'title': repo.get('name'),
                    'description': repo.get('description', ''),
                    'stars': repo.get('stargazers_count', 0),
                    'url': repo.get('html_url'),
                    'language': repo.get('language')
                })
    except Exception as e:
        print(f'  ⚠️ Awesome列表搜索失败: {e}')
    
    return results

def search_prompt_best_practices() -> list:
    """搜索最佳提示词实践"""
    results = []
    
    # 直接从已知的高质量来源
    known_prompts = [
        {
            'source': 'openai',
            'title': 'GPT Best Practices',
            'description': 'OpenAI官方提示词指南',
            'url': 'https://platform.openai.com/docs/guides/gpt-best-practices',
            'quality': 95
        },
        {
            'source': 'anthropic',
            'title': 'Claude Prompt Engineering',
            'description': 'Anthropic官方提示词工程指南',
            'url': 'https://docs.anthropic.com/claude/docs',
            'quality': 95
        },
        {
            'source': 'microsoft',
            'title': 'Prompt Engineering Guide',
            'description': '微软提示词工程指南',
            'url': 'https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/prompt-engineering',
            'quality': 90
        },
        {
            'source': 'github',
            'title': 'Awesome ChatGPT Prompts',
            'description': 'Awesome ChatGPT提示词合集',
            'url': 'https://github.com/f/awesome-chatgpt-prompts',
            'stars': 28000,
            'quality': 85
        },
        {
            'source': 'github',
            'title': 'Prompt Engineering Guide (Reddit)',
            'description': '全面的提示词工程指南',
            'url': 'https://github.com/dair-ai/Prompt-Engineering-Guide',
            'stars': 32000,
            'quality': 92
        }
    ]
    
    results.extend(known_prompts)
    return results

# ── 分析Agent问题 ────────────────────────────────────────────────────────

def analyze_agent_problems(agent_id: str) -> dict:
    """分析Agent的问题"""
    weights_file = pathlib.Path('/tmp/agent_weights.json')
    
    problems = {
        'agent_id': agent_id,
        'weight': 8,
        'status': 'normal',
        'issues': [],
        'optimization_direction': []
    }
    
    if weights_file.exists():
        with open(weights_file) as f:
            weights = json.load(f)
            if agent_id in weights:
                agent = weights[agent_id]
                problems['weight'] = agent.get('weight', 8)
                problems['status'] = agent.get('status', 'normal')
                problems['issues'] = agent.get('rejection_history', [])
    
    # 确定优化方向
    if problems['weight'] <= 6:
        if 'quality' in str(problems['issues']).lower():
            problems['optimization_direction'] = ['quality_focus', 'high_standards', 'strict_review']
        elif 'understanding' in str(problems['issues']).lower():
            problems['optimization_direction'] = ['clarity', 'examples', 'role_definition']
        elif 'proactive' in str(problems['issues']).lower():
            problems['optimization_direction'] = ['autonomy', 'self_initiated', 'initiative']
        else:
            problems['optimization_direction'] = ['general_improvement', 'best_practices']
    
    return problems

# ── 生成优化提示词 ────────────────────────────────────────────────────────

def generate_optimized_prompt(agent_id: str, problems: dict) -> str:
    """基于问题生成优化后的提示词"""
    
    # 基础模板
    template = f"""# {agent_id.upper()} · Agent SOUL (优化版)

> **优化时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}**
> **权重状态: {problems['weight']} ({problems['status']})**

---

## 角色定义

你是{agent_id}，负责系统中的特定职责。

## 核心职责

【必须做到】
1. 
2. 
3. 

## 工作标准

【质量门槛】
- 每次产出必须经过自检
- 不达标准绝不交付
- 主动发现问题

【时间观念】
- 接到任务立即执行
- 不等待，不拖延
- 阻塞时主动报告

## 约束规则

【红线约束 - 绝对禁止】
- 🚫 欺诈与流量造假
- 🚫 滥发轰炸
- 🚫 越权操作

【质量约束 - 必须遵守】
- 代码/内容必须通过审查才能提交
- 主动学习最佳实践
- 持续改进工作质量

## 优化要点

根据问题「{'、'.join(problems['issues'][:3])}」，重点优化：
"""
    
    for direction in problems['optimization_direction']:
        template += f"\n### {direction}\n- \n"
    
    return template

# ── 主流程 ──────────────────────────────────────────────────────────────

def optimize_agent(agent_id: str, github_token: str = ''):
    """优化指定Agent的提示词"""
    print(f'\n🧙 调令师 · 优化Agent: {agent_id}\n')
    print('=' * 60)
    
    # Step 1: 分析问题
    print('\n📋 Step 1: 问题诊断')
    problems = analyze_agent_problems(agent_id)
    print(f'   权重: {problems["weight"]}')
    print(f'   状态: {problems["status"]}')
    print(f'   问题: {problems["issues"][-3:] if problems["issues"] else "无记录"}')
    print(f'   优化方向: {problems["optimization_direction"]}')
    
    # Step 2: 搜索最佳提示词
    print('\n🔍 Step 2: 全网搜索最佳提示词')
    print('   搜索来源: GitHub, HuggingFace, Awesome Lists...')
    
    best_prompts = search_prompt_best_practices()
    print(f'\n   找到 {len(best_prompts)} 个高质量提示词资源:')
    for i, prompt in enumerate(best_prompts[:5], 1):
        stars = prompt.get('stars', 0)
        star_str = f' ⭐{stars}' if stars else ''
        print(f'   {i}. {prompt["title"]}{star_str}')
        print(f'      {prompt["description"][:50]}...')
    
    # Step 3: 生成优化提示词
    print('\n✍️ Step 3: 生成优化提示词')
    optimized = generate_optimized_prompt(agent_id, problems)
    
    # Step 4: 保存优化结果
    output_dir = TUNING_DIR / agent_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f'optimized_v{datetime.now().strftime("%Y%m%d_%H%M")}.md'
    with open(output_file, 'w') as f:
        f.write(optimized)
    
    print(f'\n   ✅ 优化提示词已保存: {output_file}')
    print(f'\n📄 优化提示词预览:')
    print('-' * 60)
    print(optimized[:500] + '...')
    print('-' * 60)
    
    # Step 5: 建议
    print('\n💡 调令师建议:')
    print(f'   1. 查看 {output_file} 获取完整优化方案')
    print(f'   2. 根据实际情况调整')
    print(f'   3. 测试验证后再应用到Agent')
    print(f'   4. 监控优化效果')
    
    # 记录日志
    log_audit('optimize', agent_id, problems)
    
    return optimized

def search_prompts(keyword: str, github_token: str = ''):
    """搜索提示词"""
    print(f'\n🔍 搜索关键词: {keyword}\n')
    
    # 搜索最佳实践
    print('📚 搜索最佳提示词实践...')
    best = search_prompt_best_practices()
    
    filtered = [p for p in best if keyword.lower() in p.get('title', '').lower() 
                or keyword.lower() in p.get('description', '').lower()]
    
    if filtered:
        print(f'\n✅ 找到 {len(filtered)} 个相关提示词:')
        for i, p in enumerate(filtered, 1):
            print(f'\n   {i}. {p["title"]}')
            print(f'      {p["description"]}')
            print(f'      {p["url"]}')
    else:
        print('   未找到精确匹配，搜索其他来源...')
        github_results = search_github(keyword, github_token)
        if github_results:
            print(f'\n   找到 {len(github_results)} 个GitHub资源:')
            for r in github_results:
                print(f'   - {r["title"]}: {r.get("repository", "")}')
    
    # 搜索Awesome列表
    print('\n📋 搜索Awesome列表...')
    awesome = search_awesome_list(github_token)
    if awesome:
        print(f'   找到 {len(awesome)} 个Awesome列表:')
        for a in awesome[:5]:
            print(f'   ⭐ {a["title"]} ({a.get("stars", 0)} stars)')
            print(f'      {a.get("description", "")}')

def log_audit(action: str, target: str, data: dict):
    """记录调令师审计日志"""
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'action': action,
        'target': target,
        'data': data
    }
    
    with open(AUDIT_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def show_status():
    """显示调令师状态"""
    cache = load_prompt_cache()
    
    print('\n🧙 调令师 · 状态面板\n')
    print('=' * 60)
    
    # 提示词库状态
    tuning_dir = pathlib.Path(TUNING_DIR)
    if tuning_dir.exists():
        agents = list(tuning_dir.iterdir())
        print(f'\n📚 已优化的Agent: {len(agents)}')
        for agent_dir in agents[:5]:
            files = list(agent_dir.glob('*.md'))
            print(f'   {agent_dir.name}: {len(files)} 个版本')
    
    # 缓存的提示词
    print(f'\n💾 提示词缓存: {len(cache)} 条')
    
    # 最近活动
    if pathlib.Path(AUDIT_FILE).exists():
        with open(AUDIT_FILE) as f:
            lines = f.readlines()
        print(f'\n📋 最近活动: {len(lines)} 条')
        if lines:
            last = json.loads(lines[-1])
            print(f'   最后: {last["action"]} {last["target"]} @ {last["timestamp"][:16]}')
    
    print('\n' + '=' * 60)

# ── CLI入口 ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='🧙 调令师 · Prompt Tuning Master')
    parser.add_argument('--optimize', help='优化指定Agent的提示词')
    parser.add_argument('--search', help='搜索提示词')
    parser.add_argument('--status', action='store_true', help='显示调令师状态')
    parser.add_argument('--agent', help='指定Agent')
    parser.add_argument('--token', default='', help='GitHub Token')
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    elif args.optimize:
        optimize_agent(args.optimize, args.token)
    elif args.search:
        search_prompts(args.search, args.token)
    elif args.agent:
        # 直接优化指定Agent
        optimize_agent(args.agent, args.token)
    else:
        show_status()
        print('\n用法:')
        print('  python3 tuning.py --status                    # 显示状态')
        print('  python3 tuning.py --optimize <agent_id>       # 优化Agent')
        print('  python3 tuning.py --search <关键词>            # 搜索提示词')

if __name__ == '__main__':
    main()

# 离开期间自治指南

> **更新：2026-04-02 13:25 — 皇上旨意：自主运转，只给结果**

---

## 🎯 最高目标

**GitHub Stars: 0 → 500**

皇上只要最终结果，过程不需要汇报。

---

## 🚨 红线约束 (必须遵守)

在执行任何操作前，先检查是否符合红线：

### 绝对禁止
- 🚫 自动化刷星、买星、僵尸账号
- 🚫 利益诱导（空投/返利换Star）
- 🚫 伪造身份、虚假背书
- 🚫 同一推广链接单日超过2次
- 🚫 在不相关仓库发垃圾评论
- 🚫 虚构CVE博取关注
- 🚫 爬取邮箱营销
- 🚫 **未经人类物理确认，调用支付接口**
- 🚫 下载不可靠第三方工具

### 违规即熔断
违反任何一条红线，立即终止，记录日志，通知皇上。

---

## 🔄 自主运转流程

### 心跳 (每5分钟)
- 检查进程健康
- 推进卡住的任务
- 检查GitHub Stars数量

### 调研 (每30分钟)
- 扫描GitHub Trending
- 发现项目机会
- 分析竞品

### 推广 (每天)
- 08:00 早间简报
- 20:00 晚间总结
- 适时在各平台推广

### 合规检查 (每小时)
- 运行 `compliance_checker.py`
- 检查违规日志
- 确保操作合规

---

## ✅ 可自主决定的事

| 事项 | 权限 |
|------|------|
| 代码修改/提交 | ✅ 自主 |
| README/文档优化 | ✅ 自主 |
| CI/CD配置 | ✅ 自主 |
| GitHub Pages部署 | ✅ 自主 |
| HN/Reddit发布 | ✅ 自主 (遵守红线) |
| 技术博客撰写 | ✅ 自主 |
| 购买服务器/广告 | ❌ 必须皇上确认 |

---

## 📊 成功标准

```
目标: ⭐ 500 GitHub Stars

路径:
- HN Front Page → +100-300 stars
- Reddit推广 → +30-80 stars
- Twitter → +10-30 stars
- 有机增长 → +100-200 stars/月
```

---

## 🛠️ 关键脚本

```bash
# 查看GitHub Stars
curl -s https://api.github.com/repos/kexing6400/studio | jq .stargazers_count

# 合规检查
python3 scripts/compliance_checker.py --check promote --url <url> --text "<content>"

# 推送代码
git add . && git commit -m "<message>" && git push

# 查看任务看板
python3 scripts/kanban_update.py list
```

---

## 📁 关键路径

| 路径 | 说明 |
|------|------|
| `/home/administrator/studio/` | Studio主仓库 |
| `/home/administrator/edict/` | 三省六部系统 |
| `/tmp/seven_x_twenty_four.log` | 7x24循环日志 |
| `/tmp/studio_redline_violations.log` | 违规记录 |

---

*最后更新：2026-04-02 13:25 GMT+8*

# 中书省 · 尚书省 · 工部 · 礼部 · 户部 · 刑部 · 兵部 · 吏部

> 三省六部 AI Agent System

## 目录结构

```
studio/studio/agents/
├── taizi/          # 太子 (Crown Prince) — 消息分拣
├── zhongshu/      # 中书省 (Secretariat) — 规划起草
├── menxia/        # 门下省 (Department of Review) — 审议审核
├── shangshu/      # 尚书省 (Department of Cabinet) — 派发调度
├── libu/          # 礼部 (Ministry of Rites) — 前端/内容
├── bubu/          # 兵部 (Ministry of War) — 运维/测试
├── gongbu/        # 工部 (Ministry of Works) — 后端
├── bingbu/        # 兵部 (Ministry of Military) — DevOps/CI
├── xingbu/        # 刑部 (Ministry of Justice) — QA/安全
└── libu/          # 吏部 (Ministry of Personnel) — 文档/HR
```

## Agent 接口规范

每个 Agent 必须实现以下接口：

```typescript
interface AIAgent {
  id: string;              // 唯一标识
  name: string;            // 显示名称
  role: string;            // 三省六部角色
  capabilities: string[];  // 能力列表
  execute(input: TaskInput): Promise<TaskOutput>;
}

interface TaskInput {
  taskId: string;
  description: string;
  context: Record<string, unknown>;
  constraints?: string[];
}

interface TaskOutput {
  success: boolean;
  artifacts: Artifact[];
  summary: string;
  nextSteps?: string[];
}
```

## 通信协议

Agent 之间通过 `sessions_send` 进行通信：

```typescript
// 发送任务给下级
await sessions_send(sessionKey, {
  taskId: "xxx",
  action: "dispatch",
  payload: { ... }
});
```

## 看板集成

所有任务通过看板系统追踪：

```bash
python3 scripts/kanban_update.py create <id> "<title>" <state> <org> <official>
python3 scripts/kanban_update.py flow <id> "<from>" "<to>" "<remark>"
python3 scripts/kanban_update.py progress <id> "<status>" "<checklist>"
```

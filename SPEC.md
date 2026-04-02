# Studio — AI-Powered Independent Developer Studio

> Your AI development team. From idea to production — with professional quality.

## Vision

Studio is an AI-native development studio that transforms natural language ideas into 
production-quality software. Unlike "AI code generators" that produce demo-quality code,
Studio operates at the level of a senior architect: every output is production-ready,
properly structured, and follows industry best practices.

**Target Users:** 
- Indie hackers validating side project ideas
- Developers who want a "senior architect on demand"
- Startups needing rapid prototyping without sacrificing quality

## Core Principles

1. **Production First** — Never output demo code. Everything is deployable.
2. **Opinionated** — Strong conventions. TypeScript, strict mode, proper error handling.
3. **Full Stack** — Not just code generation. Includes architecture, CI/CD, docs, deployment.
4. **Transparent** — User sees the reasoning and can override any decision.

## System Architecture

```
User (Natural Language)
         │
┌────────▼────────┐
│   三省六部       │  ← Decision Making
│  · 太子(Triage) │
│  · 中书省(Plan) │
│  · 门下省(Review)│
│  · 尚书省(Dispatch)│
└────────┬────────┘
         │
┌────────▼────────┐
│   六部 (Execute) │  ← Implementation
│  · 工部(Backend) │
│  · 户部(DevOps)  │
│  · 礼部(Frontend)│
│  · 刑部(QA)      │
│  · 兵部(Infra)   │
│  · 吏部(Human)   │
└─────────────────┘
```

## Output Standards

Every generated project MUST include:

### Backend
- [ ] TypeScript strict mode with ESLint + Prettier
- [ ] Express/Fastify or FastAPI (Python) with OpenAPI spec
- [ ] Database: PostgreSQL + Prisma/Drizzle ORM + migrations
- [ ] Authentication: JWT or session-based with refresh tokens
- [ ] Rate limiting, CORS, helmet security headers
- [ ] Comprehensive error handling with logging (structured JSON logs)
- [ ] Health check endpoint, graceful shutdown
- [ ] Unit tests with Jest/Vitest (≥80% coverage)
- [ ] Docker + docker-compose for local dev

### Frontend
- [ ] React 18+ or Next.js 14+ App Router
- [ ] TypeScript strict mode
- [ ] Tailwind CSS or CSS Modules (component library optional)
- [ ] React Query / SWR for data fetching
- [ ] Form validation with Zod
- [ ] Responsive design, accessibility (WCAG 2.1 AA)
- [ ] E2E tests with Playwright

### DevOps
- [ ] GitHub Actions CI/CD pipeline
- [ ] Dockerfile multi-stage build (dev, build, prod)
- [ ] Environment variable management (.env.example)
- [ ] Database migration scripts
- [ ] Health checks, monitoring-ready (Prometheus metrics endpoint)

### Documentation
- [ ] README.md: Quick start, architecture, deployment guide
- [ ] API documentation (auto-generated from OpenAPI)
- [ ] CONTRIBUTING.md
- [ ] CHANGELOG.md with semantic versioning

## Workflow

1. **User Input** → "Build a SaaS for task management with team features"
2. **需求解析 (中书省)** → Generate SPEC.md with architecture decisions
3. **评审 (门下省)** → Review for security, scalability, feasibility
4. **执行 (六部)** → Generate code in parallel (backend, frontend, infra)
5. **汇总 (尚书省)** → Assemble, verify, deploy

## Technical Stack

- **Runtime:** Node.js 20 LTS, Python 3.12+
- **Language:** TypeScript (strict), Python (type-annotated)
- **Framework:** Express/Fastify, FastAPI
- **ORM:** Prisma (TypeScript), SQLAlchemy/Alembic (Python)
- **Frontend:** Next.js 14, Tailwind CSS, Radix UI
- **Database:** PostgreSQL 15, Redis (cache/sessions)
- **Container:** Docker, docker-compose
- **CI/CD:** GitHub Actions
- **Infra:** Vercel (frontend), Railway/Render (backend)

## Quality Gates

Before any code is considered "done":
1. ✅ TypeScript compiles without errors (strict mode)
2. ✅ ESLint passes with no warnings
3. ✅ All unit tests pass
4. ✅ Docker builds successfully
5. ✅ App runs with `docker-compose up`
6. ✅ Health check returns 200
7. ✅ No hardcoded secrets (detected by CI)

## Competitive Positioning

| Other Tools | Studio |
|-------------|--------|
| Demo code | Production code |
| Single file | Full project structure |
| No tests | ≥80% coverage |
| No CI/CD | Full GitHub Actions |
| Hardcoded secrets | Secret scanning |
| No docs | Complete documentation |

## License

Proprietary — This is the source code for the Studio system itself.
Generated projects are owned by their creators under their chosen license.

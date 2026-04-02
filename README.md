# Studio — AI-Powered Independent Developer Studio

> Your AI development team. From idea to production — with professional quality.

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-blue.svg)](./LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-Strict-blue)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-20 LTS-green)](https://nodejs.org/)

## Overview

Studio is an AI-native development studio built on the 三省六部 (Three Departments and Six Ministries) architecture. It transforms natural language ideas into production-quality software through autonomous multi-agent collaboration.

### What Makes Studio Different

| Aspect | Typical AI Code Tools | Studio |
|--------|----------------------|--------|
| Code Quality | Demo/Prototype | Production-ready |
| Project Structure | Single files | Full monorepo |
| Testing | None or minimal | ≥80% coverage |
| DevOps | Manual | Full CI/CD |
| Security | Often overlooked | Secret scanning + hardening |

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          User Input                            │
│                   (Natural Language Brief)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     三省六部 Orchestration                       │
│                                                                 │
│   ┌─────────┐                                                   │
│   │  太子    │  Triage — Analyze intent, classify task type     │
│   └────┬────┘                                                   │
│   ┌────▼────┐                                                   │
│   │ 中书省   │  Plan — Architecture design, PRD generation      │
│   └────┬────┘                                                   │
│   ┌────▼────┐                                                   │
│   │ 门下省   │  Review — Security, scalability, risk audit      │
│   └────┬────┘                                                   │
│   ┌────▼────┐                                                   │
│   │ 尚书省   │  Dispatch — Task allocation, progress tracking   │
│   └────┬────┘                                                   │
│   ┌────▼────┐                                                   │
│   │ 六部    │  Execute — Parallel implementation                │
│   │ 工部    │    Backend (Express/FastAPI)                      │
│   │ 户部    │    Database design + DevOps                       │
│   │ 礼部    │    Frontend (Next.js/React)                       │
│   │ 刑部    │    Testing + QA                                   │
│   │ 兵部    │    Infrastructure + CI/CD                         │
│   │ 吏部    │    Documentation + Human review                    │
│   └─────────┘                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Production Output                            │
│  • SPEC.md (architecture document)                              │
│  • Full-stack application code                                  │
│  • Docker + docker-compose                                     │
│  • GitHub Actions CI/CD                                        │
│  • Complete documentation                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Node.js 20 LTS
- Python 3.12+
- Docker + docker-compose
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/kexing6400/studio.git
cd studio

# Install dependencies
npm install

# Start the dashboard
npm run dashboard
```

### Dashboard

The dashboard provides a web UI for monitoring and controlling the 三省六部 system:

```bash
cd dashboard
npm install
npm run dev
```

Access at `http://localhost:7891`

## Project Structure

```
studio/
├── SPEC.md                    # This specification
├── README.md                  # Project documentation
│
├── studio/                    # Core AI orchestration
│   ├── agents/                # Agent definitions
│   │   ├── taizi/            # Crown Prince (triage)
│   │   ├── zhongshu/         # Secretariat (planning)
│   │   ├── menxia/           # Department of门下 (review)
│   │   ├── shangshu/         # Department of尚书 (dispatch)
│   │   └── libu/             # Ministry of礼 (frontend)
│   │       └── ...
│   ├── scripts/              # Execution scripts
│   └── lib/                   # Shared utilities
│
├── dashboard/                 # Web dashboard
│   ├── app/                   # Next.js app
│   ├── components/           # React components
│   └── dist/                  # Built static assets
│
└── projects/                 # Generated projects (gitignored)
```

## Output Standards

Every project generated by Studio meets these standards:

### Backend
- ✅ TypeScript strict mode (no `any` escape hatches)
- ✅ ESLint + Prettier enforcement
- ✅ REST API with OpenAPI 3.1 spec
- ✅ PostgreSQL + Prisma ORM with migrations
- ✅ JWT authentication with refresh tokens
- ✅ Rate limiting, CORS, security headers
- ✅ Structured JSON logging
- ✅ Graceful shutdown
- ✅ ≥80% test coverage

### Frontend
- ✅ Next.js 14 App Router
- ✅ TypeScript strict mode
- ✅ Tailwind CSS
- ✅ React Query for server state
- ✅ Zod for runtime validation
- ✅ Accessibility: WCAG 2.1 AA
- ✅ Playwright E2E tests

### DevOps
- ✅ GitHub Actions CI/CD
- ✅ Multi-stage Dockerfile
- ✅ docker-compose for local dev
- ✅ Environment validation
- ✅ Secret scanning in CI

## Generated Project Template

When Studio creates a new project, it produces:

```
project-name/
├── SPEC.md                    # Architecture & design decisions
├── README.md                  # Quick start guide
├── CONTRIBUTING.md            # Contribution guidelines
├── CHANGELOG.md               # Version history
│
├── packages/
│   ├── backend/               # Express/Fastify API
│   │   ├── src/
│   │   │   ├── routes/
│   │   │   ├── middleware/
│   │   │   ├── services/
│   │   │   └── types/
│   │   ├── tests/
│   │   ├── prisma/
│   │   │   └── migrations/
│   │   ├── Dockerfile
│   │   └── package.json
│   │
│   └── frontend/              # Next.js application
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   └── lib/
│       ├── tests/
│       └── package.json
│
├── docker-compose.yml         # Full stack local dev
├── .env.example               # Environment template
├── .eslintrc.js               # Linting config
├── turbo.json                 # Monorepo config
└── package.json               # Workspace root
```

## License

Proprietary — Studio system source code.

Generated projects are owned by their creators under licenses of their choosing.

---

*Built with 三省六部 — Where AI meets production quality.*

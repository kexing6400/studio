# @studio/cli

> Create production-ready TypeScript projects in seconds.

```
$ npm install -g @studio/cli
$ studio new my-api --template api
$ cd my-api && npm install && npm run dev
```

## Features

- 🎯 **Production Ready** — Not demo code. Tests, CI/CD, Docker all included.
- ⚡ **Fast** — `studio new <name>` and you're ready to code.
- 📦 **Templates** — API, Fullstack, CLI — all with TypeScript strict mode.
- 🔒 **Secure** — Security headers, rate limiting, JWT auth built-in.

## Templates

| Template | Description |
|----------|-------------|
| `api` | Express.js REST API with Prisma + PostgreSQL |
| `fullstack` | Next.js 14 + Express API |
| `cli` | Node.js CLI tool with Commander |

## Quick Start

```bash
# Install
npm install -g @studio/cli

# Create a new API project
studio new my-api --template api

# Create a new CLI project
studio new my-tool --template cli

# List available templates
studio list
```

## What You Get

Every project comes with:

- ✅ TypeScript strict mode (no `any`)
- ✅ ESLint + Prettier
- ✅ Vitest with ≥80% coverage
- ✅ GitHub Actions CI/CD
- ✅ Docker + docker-compose
- ✅ Health check endpoint
- ✅ Graceful shutdown
- ✅ Structured logging

## Examples

```bash
# Create an API project
studio new task-api --template api
cd task-api
npm install
docker-compose up -d postgres
npm run dev

# Create a CLI tool
studio new my-cli --template cli
cd my-cli
npm install
npm run build
npm link
my-cli hello
```

## Why Studio?

| Other Tools | Studio |
|-------------|--------|
| Demo code | Production code |
| No tests | ≥80% coverage |
| No CI/CD | Full GitHub Actions |
| Reinvent everything | Best practices built-in |

## License

MIT

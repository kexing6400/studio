# {{PROJECT_NAME}}

Production-ready REST API built with Studio.

## Quick Start

```bash
npm install
npm run dev
```

## What You Get

- ✅ TypeScript strict mode
- ✅ Express.js with middleware
- ✅ Prisma ORM (PostgreSQL)
- ✅ JWT authentication
- ✅ Zod validation
- ✅ Structured logging (Winston)
- ✅ Error handling
- ✅ Rate limiting
- ✅ Security headers (Helmet)
- ✅ Vitest tests
- ✅ ESLint + Prettier
- ✅ Docker + docker-compose

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /api/auth/register | Register |
| POST | /api/auth/login | Login |

## Environment

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/db
JWT_SECRET=your-secret
PORT=3000
```

## Scripts

```bash
npm run dev      # Development
npm run build    # Production build
npm run test     # Run tests
npm run lint     # Lint code
```

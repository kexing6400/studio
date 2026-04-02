# Contributing to Studio

Thank you for your interest in contributing to Studio!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/kexing6400/studio.git
cd studio

# Install dependencies
npm install

# Start the dashboard
npm run dashboard
```

## Project Structure

```
studio/
├── studio/              # Core AI orchestration
│   ├── agents/          # Agent definitions (三省六部)
│   ├── scripts/         # Execution scripts
│   └── lib/             # Shared utilities
├── dashboard/           # Web dashboard (Next.js)
└── projects/           # Generated projects (gitignored)
```

## Adding a New Agent

1. Create a new directory under `studio/agents/`
2. Implement the `AIAgent` interface
3. Register in `agents.json`
4. Add tests

## Code Standards

- TypeScript strict mode (no `any`)
- ESLint + Prettier enforcement
- Unit tests with ≥80% coverage
- Semantic commit messages

## Commit Message Format

```
<type>(<scope>): <subject>

Types:
  ✨ feat     - New feature
  🐛 fix      - Bug fix
  📝 docs     - Documentation
  💄 style    - Formatting
  ♻️ refactor - Code refactoring
  ✅ test     - Adding tests
  🔧 chore    - Maintenance
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `npm run lint && npm test`
5. Submit a pull request

## License

By contributing, you agree that your contributions will be licensed under the
Studio Proprietary License.

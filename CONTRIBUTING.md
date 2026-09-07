# Contributing to NEXUS

Thanks for contributing to NEXUS.

## Ways to Contribute

- Report bugs with reproducible steps.
- Suggest features with market/use-case context.
- Improve indicators, scoring, and forecasting methods.
- Expand docs, media, tutorials, and examples.
- Add tests and improve reliability.

## Local Setup

1. Install Node.js 18+.
2. Install dependencies:

```bash
npm install
```

3. Start app:

```bash
npm start
```

4. Open:
- http://127.0.0.1:8080

## Branch & PR Workflow

1. Fork repository.
2. Create feature branch:

```bash
git checkout -b feat/short-description
```

3. Commit small, focused changes.
4. Add/update docs and screenshots where needed.
5. Open Pull Request using template.

## Coding Standards

- Keep functions small and composable.
- Keep API responses backward-compatible when possible.
- Add concise comments only for non-obvious logic.
- Prefer deterministic behavior and fail-safe fallbacks.
- Keep frontend responsive for desktop/mobile.

## Testing Checklist

- API health endpoint returns ok=true.
- Multi-market endpoints return records for defaults.
- Decision response includes technical/fundamental/quant fields.
- UI loads with no console errors.
- README examples remain valid.

## Commit Message Examples

- feat: add macro regime feature to fundamental score
- fix: prevent timeout cascade in market data fanout
- docs: add indicator formulas and API examples

## Community

- Be respectful in all discussions.
- Review other contributors' work constructively.
- Propose improvements with data/evidence.

# AI development instructions

## Purpose and current phase

Build a minimal CI/CD teaching template: FastAPI, pytest, Playwright Python, and one HTML calculator page. See [README.md](README.md) for current status and [docs/spec.md](docs/spec.md) for requirements. Implementation is authorized. Follow the issue backlog through a verified running demo; update status and evidence as each issue is completed.

## Read before changing behavior

- Read the issue and its linked requirements, then relevant architecture, testing, and CI/CD sections.
- Treat the specification as the intended contract. If a request changes it, update the spec and acceptance criteria alongside the work.
- Preserve requirement IDs. Add new IDs instead of renumbering existing requirements.
- Keep unresolved deployment host, architecture, and registry choices explicit. Inspect safely where possible; ask only for decisions that cannot be inferred or verified.
- Do not claim planned files, commands, tests, releases, or deployments already exist.

## Implementation boundaries

- Keep all frontend HTML, CSS, and JavaScript in one file. No frontend framework, bundler, CDN, database, login system, or unrelated infrastructure.
- Keep arithmetic separate from HTTP. Test Python logic with pytest, API integration with TestClient, and the real container/browser flow with Playwright.
- Use the shared command interface in [CONTRIBUTING.md](CONTRIBUTING.md).
- Build once per supported native architecture, browser-test each artifact, and publish those saved artifacts as a multi-platform index. Do not rebuild silently after testing.
- The practical assessment requires sanitized deployment configuration in this repository under deploy/. Keep certificate stores and credentials private. Preserve the optional local Compose override on every application lifecycle operation.
- Keep development on `8080`, production on `8090`, and E2E containers isolated from both.
- Configure updater access explicitly; update only the separate QA and production release services. Never imply a read-only Docker socket mount removes Docker control privileges.
- Do not add a Sites or other hosting deployment to this Docker-based project.

## Work and review discipline

- Work in small issue-linked changes. Follow [CONTRIBUTING.md](CONTRIBUTING.md) for branches, atomic commits, and PR evidence.
- Read existing work and preserve unrelated edits. Do not force-push, rewrite history, or hide failed demo commits.
- Keep code, tests, and corresponding specification changes coherent. Avoid unrelated refactors and redundant tests that merely repeat the implementation.
- Run checks appropriate to the change and record results honestly. A successful image push is not proof of deployment.
- Never print secrets or commit credentials, `.env` files, browser artifacts, or private local configuration. Refer to `DOCKER_API_KEY` by name only.
- Do not enable branch protections until the intended required checks exist and have run; document proposed policy first.
- Complete work already authorized by the user without adding redundant approval steps. This file does not require a separate approval for routine edits, commits, issues, or publishing already authorized in the conversation.

## Definition of done

The issue's acceptance criteria are met, required checks passed, the spec reflects final behavior, and the PR/issue contains evidence. For deployment work, include the workflow, digest, and observed running commit. For documentation-only work, link and consistency checks suffice; do not manufacture runtime test results.

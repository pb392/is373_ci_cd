# Contributing

This repository teaches development history as well as deployment. Prefer small, understandable changes with evidence over a large all-at-once implementation.

## Specification-driven workflow

1. Pick an open issue from the [implementation plan](docs/implementation-plan.md). Check its dependencies.
2. Read its linked specification sections and requirement IDs.
3. If behavior must change, update the specification and issue before or with the implementation. Explain the decision in the PR.
4. Create a branch such as `feat/3-calculation-api` or `fix/12-zero-validation`.
5. Implement one coherent piece and run the relevant checks.
6. Make focused commits that reference the issue.
7. Open a PR with acceptance evidence, scope, and any untested limitations.
8. Merge when the issue's acceptance criteria are satisfied and required checks pass. A deployment issue also needs evidence from the running host.

The initial documentation bootstrap goes directly to the empty repository's `main` branch so the specifications and issue forms can be reviewed on GitHub. Subsequent implementation should use branches and PRs. For the Xenoshin assessment, verify QA first and merge its pull request into `main` only after the `verify` checks and public QA deployment pass. This describes the project promotion procedure, not a claim that GitHub branch protection is enabled.

## Atomic commits

An atomic commit represents one coherent, reviewable change. A behavior change and its necessary tests usually belong together. Do not split a change just to increase the commit count, and do not combine unrelated fixes.

Suggested style:

```text
docs: specify calculator request and response contract (#1)
feat: add calculation API and validation tests (#3)
test: exercise calculator in Chromium (#4)
ci: publish verified container images (#6)
```

Use `Refs #N` while an issue is in progress and `Closes #N` in the completing PR. Preserve useful atomic commits using GitHub's merge-commit option; avoid squashing the whole implementation into one commit for this teaching repository. Review staged files before committing. Do not commit secrets, build output, local environment files, browser artifacts, or unrelated changes.

## Command interface

These commands are implemented. Start with `make setup` and `make browsers` when running tests locally.

| Command | Contract |
| --- | --- |
| `make dev` | Start only the source-mounted dev service on `8080`; no published image required |
| `make test-unit` | Run only pure Python unit tests |
| `make test-integration` | Run only in-process API integration tests |
| `make build` | Build a release image with commit and build metadata; no publication |
| `make test-e2e` | Test the already-built image in an isolated container; collect failures and clean up |
| `make deploy` | Start only published production and WUD; honor pause state and local override |
| `make verify-production` | Compare selected image ID with the actual container and health commit |
| `make up` | Start dev, published prod, and WUD after bootstrap |
| `make down` | Stop this project's Compose services without deleting unrelated resources |
| `make rollback RELEASE=<sha-tag-or-digest>` | Pause updater and redeploy only prod to a known-good release |
| `make resume-updates` | Restore the production channel and resume updates deliberately |

Prerequisites and setup are in the README. `IMAGE` selects the locally built/tested image; `E2E_PORT` changes the isolated browser-test port. Future framework adaptations keep this interface and replace its internals. Use these Make targets to preserve `.state/release.env` and the updater pause marker during rollback.

## Validation and evidence

- Documentation: review consistency, relative links, requirement references, and applicable YAML syntax; run `git diff --check`.
- Python logic/API: run the affected unit and integration tests.
- HTML/JavaScript: run browser checks against the production image.
- Docker/CI/updater: verify the actual image, runner, or host behavior as appropriate.
- Every PR: state exact checks run and material checks not run. Never label planned validation as passed.

Deliberate failure demonstrations belong on clearly named demo branches and should be documented. Do not leave a known broken release on `main` outside an explicitly coordinated failure demonstration.

## Platform and hosting changes

Keep the required `verify` check name. CI must test each supported platform before publishing its artifact. Use the companion-owned override described in [hosting](docs/hosting.md) instead of installing another Traefik here. Local `compose.override.yaml` is ignored and loaded by every lifecycle command.

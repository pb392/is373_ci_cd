# Product specification

Status: version 1 contract plus the complementary-hosting extension. Requirement IDs are stable references for issues, tests, and pull requests. Proposed defaults below may be changed through a documented specification update.

## Goal and scope

Teach a complete, repeatable CI/CD process using an application small enough to understand at a glance. Demonstrate three test levels, a failed release gate, automatic image deployment, release identification, and a manual rollback.

Version 1 includes a FastAPI application, one HTML file, pytest, Playwright, Docker Compose, GitHub Actions, Docker Hub, and WUD. It excludes databases, authentication, calculation history, advanced mathematics, Kubernetes, zero-downtime releases, and automatic rollback. This is a teaching deployment, not a hardened public service.

## Calculator behavior

### CALC-01 — Four operations

The page provides labeled inputs **First number** and **Second number**, an **Operation** selector, and a **Calculate** submit button. Operations are `add`, `subtract`, `multiply`, and `divide`, displayed as `+`, `−`, `×`, and `÷`. Enter submits the form.

Acceptance examples:

| First | Operation | Second | Result |
| --- | --- | --- | --- |
| 2 | add | 3 | 5 |
| -4 | subtract | 2 | -6 |
| 6 | multiply | 7 | 42 |
| 9 | divide | 2 | 4.5 |

### CALC-02 — Browser and API comparison

One submission calculates locally in JavaScript and sends the same operands and operation to `POST /api/calculate`. Show labeled **Browser result** and **API result**, followed by **Results match** or **Results differ**. Do not claim a match before the API responds. A disagreement must be visible rather than silently replacing one result with the other.

Disable submission while a request is pending, clear stale comparison state on a new submission, and always restore the button after completion or failure. If the user edits an input during the request, discard the stale response or make clear which submitted operands it belongs to. A request times out after five seconds; there are no automatic retries in v1.

### CALC-03 — Input and error contract

Operands must be finite numbers with absolute value at most `1,000,000`. Negative and fractional numbers are allowed. Empty strings must not silently become zero. Division by positive or negative zero is rejected. A non-finite calculated result is rejected. JavaScript and Python apply the same rules.

The API requires JSON numbers, rejecting booleans, numeric strings, missing fields, extra fields, and unknown operations with `422`. Division by zero and a non-finite result return `400` with a stable application error code. The UI rejects locally detectable errors before making the calculation request and renders messages as text.

### CALC-04 — Numeric comparison and display

Use ordinary JavaScript numbers and Python floating-point arithmetic; exact decimal arithmetic is outside scope. Two finite results match when:

```text
abs(browser - api) <= max(1e-9, 1e-9 * max(abs(browser), abs(api)))
```

Compare numeric values before formatting. Display up to ten significant digits, strip insignificant trailing fractional zeros, normalize negative zero to `0`, and allow scientific notation. The API returns the unformatted finite numeric result. `0.1 + 0.2` must display a sensible value and report a match. Shared acceptance examples define the contract; duplicating a small calculation function across languages is intentional for this lesson.

### UI-01 — One accessible HTML file

Serve one shared HTML file at `/` and `/calculator`, containing all page markup, CSS, and JavaScript. The server selects the visible view before delivery; the test homepage works without JavaScript. Use standard browser APIs, with no CDN or frontend build step. Associate labels with controls, use keyboard-accessible inputs, and announce results/errors with a live region. Status must use words, not color alone. The page must remain usable on a narrow viewport.

### OPS-01 — Release identity

Display environment (`development`, `production`, or `test`), commit, and UTC build time. Production embeds a full commit SHA and build timestamp in its image; the UI may abbreviate the SHA. Development may use `local` and an unavailable build timestamp. Local uncommitted changes are not a production release.

### OPS-02 — Health and API status

`GET /health` returns `200` and identifies the running release. On initial page load, the UI checks health and displays **API available** or **API unavailable**. A subsequent calculation response can update that status. Health is a lightweight application readiness check, not evidence that every feature works.

On a network failure, timeout, or non-JSON server error, retain any valid browser result and show an understandable API error without a false comparison result. Never display a Python traceback or secret in the UI.

## HTTP contract

| Route | Success | Error |
| --- | --- | --- |
| `GET /` | `200`, HTML test homepage | Normal server error handling |
| `GET /calculator` | `200`, HTML calculator | Normal server error handling |
| `POST /api/calculate` | `200`, JSON result | `422` invalid request; `400` arithmetic error |
| `GET /health` | `200`, JSON health and release identity | Connection failure/non-200 means not ready |

Request:

```json
{"a": 6, "b": 7, "operation": "multiply"}
```

Successful response:

```json
{"result": 42}
```

Arithmetic error:

```json
{"detail": {"code": "division_by_zero", "message": "Cannot divide by zero."}}
```

The other arithmetic code is `non_finite_result`. For `422`, retain FastAPI's validation error structure; tests check status and relevant field locations, not library-specific message wording. The UI translates validation failures into concise guidance.

Health response (illustrative values):

```json
{
  "status": "ok",
  "environment": "production",
  "commit": "full-git-commit-sha",
  "built_at": "2026-09-17T18:00:00Z"
}
```

## Delivery requirements

- **DEL-01:** Development on host port `8080` reloads mounted source; production on `8090` runs only a published image, without a source mount or reload.
- **DEL-02:** Unit, integration, image build, and browser checks all pass before a release is published. Pull requests never publish or deploy.
- **DEL-03:** Only successful `main` releases update `:prod`; retain a unique `:sha-<full-commit>` tag for release identification.
- **DEL-04:** WUD monitors only the production application, detects changes to the digest behind `:prod`, and recreates production without restarting development.
- **DEL-05:** The repository documents bootstrap, failed-release behavior, deployment verification, rollback with updates paused, and later resumption.
- **DEL-06:** Failed browser tests leave a downloadable trace and screenshot in GitHub Actions.
- **DEV-01:** Changes trace to issues and specification IDs, with focused commits and recorded validation.
- **DEV-02:** Commands expose stable development/test/build interfaces so another framework can reuse the delivery pattern.

See [testing](testing.md) for coverage, [CI/CD](ci-cd.md) for delivery details, and [implementation plan](implementation-plan.md) for completion gates.

## Complementary hosting extension (issue #28)

- **DEL-07:** Native AMD64 and ARM64 artifacts each pass unit, integration, and real-browser tests before either can enter the multi-platform production index. Publication loads tested artifacts without rebuilding.
- **DEL-08:** A stable `verify` check gates both native jobs. Only current-main pushes can publish; PRs/manual runs cannot.
- **OPS-03:** All Compose lifecycle operations load an optional local override. Production-only deployment does not build/start development, and rollback preserves the hosting network and labels through that override.
- **OPS-04:** Persisted release selections override inherited `PROD_IMAGE`; verification compares actual container image identity and the expected health commit/environment.
- **DOC-01:** The hosting companion owns DNS, TLS, firewall, proxy, and its routing overlay; this repository owns the app and delivery. Cross-links describe the handoff without duplicating either source of truth.

Acceptance: both native PR checks pass; rendered Compose retains overrides and loopback ports; regression tests cover conflicting release selection; a production publication records both platform digests and the index. A new public deployment/rollback rehearsal must be recorded separately before claiming it occurred.

## Xenoshin test homepage

- **UI-02:** `/` shows xenoshin.com, “The test website is working.”, and “This page loaded successfully.” without requiring JavaScript. It contains no visible calculator or release details and fits a narrow mobile viewport.
- **UI-03:** The existing calculator remains available at `/calculator`; its calculation, health, and release identity contracts remain unchanged.

Publishing a Docker image does not demonstrate that xenoshin.com is serving it. Server access, routing, and public HTTPS verification remain a separate hosting step.

# Testing strategy

Status: implemented and verified locally, in GitHub Actions, and against the published production image. Current counts: 22 unit, 16 integration, and 7 Chromium tests. See [recorded evidence](evidence.md). The suite should be small enough that most feedback time comes from runner setup, image builds, and deployment polling rather than test execution.

## Test layers

| Layer | Boundary | Tools | What a failure teaches |
| --- | --- | --- | --- |
| Unit | Pure Python calculation function | pytest | Arithmetic/domain behavior is wrong |
| Integration | Request parsing → validation → route → calculation → JSON response | pytest, FastAPI TestClient, HTTPX | Components disagree on the API contract |
| E2E | Chromium → real HTTP → built production container → rendered UI | pytest-playwright | The user-facing flow is broken |

Integration tests execute the real application in-process without a network server. They do not substitute for container startup or browser tests. pytest unit tests cover Python; JavaScript behavior is exercised by Playwright, not claimed as Python unit coverage.

## Minimal coverage matrix

Use parameterization to keep tests readable. Avoid broad browser matrices and arbitrary coverage-percentage gates in version 1.

| Requirements | Coverage |
| --- | --- |
| CALC-01 | Unit cases for four operations, negative and fractional operands |
| CALC-03 | Unit rejection of zero divisor, out-of-range/non-finite operands and non-finite result |
| CALC-04 | Unit numeric examples and browser decimal comparison |
| CALC-02 | One browser success scenario: `6 × 7`, both results `42`, match status |
| CALC-03, HTTP contract | Integration: valid request returns numeric result; invalid/missing/extra fields, strings, booleans, unknown operation, and out-of-range operands return `422` |
| CALC-03, HTTP contract | Integration: division by zero and overflowing finite-input division return `400` with specified codes |
| CALC-03, UI-01 | Browser: empty input and zero divisor produce guidance without a false match |
| CALC-04 | Browser: `0.1 + 0.2` reports a match and readable result |
| OPS-01, OPS-02 | Integration and container smoke check: health status and expected release metadata |
| OPS-02 | Browser: deliberately block the calculation request; local result survives and API failure appears |
| DEL-01–DEL-05 | Container/deployment checks and the recorded demo, not redundant unit tests of YAML |
| DEL-06 | Deliberately fail a browser assertion and confirm uploaded trace/screenshot |

The homepage checks cover its HTTP routes, visibility without JavaScript, and narrow-screen layout. The calculator suite includes success, empty/zero-divisor input, decimal, network failure, mismatch, and narrow-screen keyboard scenarios. Keep one Chromium worker, no automatic retries initially, and no fixed sleeps. Wait for readiness with a bounded health-check loop, then use Playwright's condition-based assertions.

## Commands and evidence

Test commands (run `make setup` and `make browsers` first):

```sh
make test-unit
make test-integration
make build
make test-e2e
```

`make test-e2e` starts an isolated instance of the already-built release image, waits up to 30 seconds for `/health`, runs browser tests, and cleans up even after failure. It must not accidentally test the development server on `8080` or replace the user's production container on `8090`. Use a configurable isolated port, default `18090`, and pass the base URL to the tests. The artifact tested must be the artifact later published.

Startup failure is also a cleanup case: if the port is occupied, Docker can create a container before reporting the error. The runner removes its unique container name, saves startup diagnostics, and leaves no stale tested-image record. This scenario is tracked and reproduced in [#20](https://github.com/kaw393939/is373_ci_cd/issues/20).

Record test counts and durations separately for unit, integration, build, and browser steps. Retain browser traces/screenshots on failure and application container logs for startup failures. Upload evidence even when the test step fails; keep artifacts seven days for this demo. Never include credentials in logs or artifacts.

## Speed targets

Initial goals, not benchmark claims: unit and integration execution together under ten seconds; browser execution under thirty seconds after the server and browser are ready. Measure cold and cached workflow times and push-to-visible-deployment time on the selected host. Do not promise a total duration before observing the runner, registry, architecture, and polling costs.

Cache Python downloads and Docker build layers. Keep browser tooling outside the release image. Prefer one job with named steps to avoid repeated runner setup. Add parallel jobs only if measured time justifies the complexity.

## Useful failure demonstrations

1. Change multiplication to addition in Python: unit failure stops the pipeline.
2. Change the response key from `result` to `answer`: integration failure stops the pipeline.
3. Disconnect the Calculate button handler: E2E failure produces a trace.

Introduce one fault at a time. Use a disposable demonstration branch/PR; no publishing occurs there. Restore changes afterward. A controlled failing `main` commit is optional for explicitly demonstrating the publication gate; do it only as an intentional demo, and revert with a new commit rather than rewriting history.

## References

- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Playwright pytest integration](https://playwright.dev/python/docs/test-runners)
- [Playwright trace viewer](https://playwright.dev/python/docs/trace-viewer-intro)

Publication guard unit cases also reject PR/manual contexts, stale main commits, mismatched image IDs, and mismatched release identities. The pinned upstream TestClient currently emits two deprecation warnings; these do not fail the tests.

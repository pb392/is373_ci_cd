# Hosting handoff: two complementary repositories

For this student’s deployed QA/production setup, use the [repository README](../README.md) and the tracked [deployment configuration](../deploy/). The companion workflow below is retained as template background.

## Ownership

| This repository: is373_ci_cd | Companion: 373_hosting |
|---|---|
| Calculator and HTTP contract | Ubuntu, Docker installation, DNS, firewall |
| Dockerfile and dependency lock | Traefik and certificate persistence |
| Unit/API/browser tests | Public routing overlay and HTTPS verification |
| Tested image publication | Public deployment lesson and server recovery |
| App deployment, updater, rollback | Infrastructure lifecycle independent of app releases |

The app works locally without Traefik. The host works with Apache welcome pages without this app. Integration adds one application to an existing shared proxy network; it does not start a second proxy or replace the welcome pages.

## Stable contract

- Published image: `pb392/is373_ci_cd:prod`, with multi-platform `sha-<full-commit>` rollback references after the new pipeline's first release.
- HTTP container port: `8000`.
- Readiness/release endpoint: `GET /health`, returning status, production environment, full commit, and build time.
- Host port `8090` remains loopback-only for local operational checks; public users connect through Traefik on 443.
- Service name `prod` is the integration target. Development and WUD are not public routes.
- The app's lifecycle wrapper loads ignored `compose.override.yaml` after `compose.yaml` for every operation, including rollback/resume.
- A host-generated `.env` supplies `APP_HOST` and `TRAEFIK_NETWORK` to that overlay. DNS/TLS settings remain in the hosting repo.

## Deploy through the companion

Follow [the complete integration lesson](https://github.com/kaw393939/373_hosting/blob/main/book/10-application-delivery.md) and use its [routing overlay](https://github.com/kaw393939/373_hosting/tree/main/examples/integrations/calculator). Copy that overlay into the app checkout as `compose.override.yaml`, set the host/network values locally, then run `make deploy` on the server. Docker access is required; the hosting lesson uses sudo for deployment commands.

No `make setup`, browser install, or local application build is needed for a production-only deployment. It pulls the tested registry image. `make up` intentionally also starts source-mounted development; use it for the local classroom demonstration.

Public deployments must verify the expected commit over HTTPS, not just loopback. The hosting repo owns that external check. Keep the updater dashboard on `127.0.0.1:8091`; an SSH tunnel can provide administrative access when needed. Its Docker socket gives it substantial host control.

## Image selection and rollback

Persisted `.state/release.env` wins over shell `PROD_IMAGE`, which otherwise wins over `.env` and the Compose default. This prevents an old exported variable from overriding a deliberate rollback. Resume deliberately selects the `prod` channel. Keep `.state` across routine operations.

`make verify-production` checks that the container's actual image ID equals the selected local image, then verifies the health commit and production environment. When you select a registry digest, Docker resolves the host's platform image; that platform image ID must match the container. Publication records retain both the multi-platform index and child digests.

An ARM64-only historical tag cannot restore an AMD64 host. Select a known-good compatible release; do not assume every old tag has both architectures. A single-container update briefly interrupts service. No zero-downtime or automatic health-based rollback is promised.

## Extensibility without duplication

The optional override mechanism is generic: another host can supply an external network, labels, or approved resource limits. It does not require this app to know the proxy's certificate configuration. Replacing FastAPI with another framework changes the app image and tests while retaining the deployment contract where practical.

The dev/QA/manual-promotion proposal in issue #27 is a separate unadopted design. This integration preserves the current passing-main-to-prod teaching model rather than introducing three release environments implicitly.

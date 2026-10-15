# Xenoshin — secure QA and production deployment

**[Production: xenoshin.com](https://xenoshin.com)** · **[QA: qa.xenoshin.com](https://qa.xenoshin.com)**

[Public GitHub repository](https://github.com/pb392/is373_ci_cd) · [Docker Hub images](https://hub.docker.com/r/pb392/is373_ci_cd)

A minimal containerized test website on my DigitalOcean Droplet. The homepage shows the release message, environment, and running commit; the original calculator remains at `/calculator`.

## Promotion rule

1. Push a change to `qa`. GitHub Actions runs unit, API integration, and Chromium browser tests on native AMD64 and ARM64 runners. It builds each platform once, tests that exact image, and publishes the saved artifacts to `pb392/is373_ci_cd:qa` only after all checks pass.
2. The server's WUD updater observes the QA image digest and replaces only the QA container. The workflow waits for `https://qa.xenoshin.com/health` to report the expected commit and `qa` environment. QA changes do not change production.
3. Review QA, then merge a pull request from `qa` into `main`. The same checks publish `:prod`; the updater replaces only production. The workflow verifies the expected production commit over HTTPS and captures both pages.

Pull requests and manual workflow runs test but never publish. A failed test or build prevents publication. Registry credentials use the GitHub Actions secret `DOCKER_API_REP`; no server private key is needed by Actions. Source changes are promoted by merge; each branch commit has its own tested immutable image tag.

## Test Evidence

The [QA bootstrap workflow](https://github.com/pb392/is373_ci_cd/actions/runs/38776465642) passed both native platform checks, published the QA image, and verified its public HTTPS release. The QA service was started once using the non-root account; subsequent releases use the automatic updater.

[SSH verification](docs/assessment/ssh-verification.txt) records successful key login as `webadmin`, effective disabled root/password authentication, and rejected root and password-only connections. No private credentials are included.

The visible Version 3 change is being demonstrated through QA and then production. The final workflow links, before/after screenshots, and deployed identities will be recorded after that real promotion completes.

## Deployment configuration

- [Application services](compose.yaml): separate QA and production containers on loopback ports 8092 and 8090. The local development service uses 8080.
- [HTTPS proxy](deploy/traefik.compose.yaml) and [routing overlay](deploy/routes.yaml): only QA and production have public HTTPS routes. HTTP redirects to HTTPS and certificates renew automatically.
- [Public domain settings](deploy/site.env.example): copy to the server checkout as `.env`; copy the routing overlay as `compose.override.yaml`.
- [SSH policy](deploy/ssh-hardening.conf): install only after verifying non-root key access. Disables root and password/keyboard-interactive SSH.
- [Limited administration command](deploy/xenoshin-admin): installed root-owned and executable; `webadmin` may use sudo for only the enumerated operations. No unrestricted passwordless sudo was added.

The site runs on the owner's DigitalOcean server at `104.248.180.176`. Application checkout: `/opt/is373_ci_cd`; proxy: `/opt/xenoshin-hosting`. SSH administration uses `webadmin@104.248.180.176`. Private SSH keys, certificates, tokens, and updater passwords are never committed.

The QA and production services follow separate image channels and have no shared source-code mounts. The updater dashboard stays on loopback port 8091 with authentication; it is not publicly routed. Its Docker access is privileged. Pause/resume operations stop/start the common updater, affecting automatic updates for both environments; a production rollback recreates production only.

## Run and test locally

```sh
git clone https://github.com/pb392/is373_ci_cd.git
cd is373_ci_cd
make setup
make browsers
make test-unit
make test-integration
make build
make test-e2e
make dev
```

Development: http://localhost:8080. Calculator: http://localhost:8080/calculator.

For initial server bootstrap, configure the external `hosting-web` network/proxy and routing overlay, then use `make deploy` and `make deploy-qa` after the corresponding images exist. Subsequent branch releases update automatically. Docker starts on boot; the services use restart policies.

## Historical template documentation

This project builds on the course calculator template. Older records in `docs/evidence.md`, `docs/qa.md`, and `docs/integration-evidence.md` refer to the original author's demonstration and are not this student's submission evidence. Use this README's Test Evidence section for the Xenoshin deployment.

[Specification](docs/spec.md) · [Testing](docs/testing.md) · [CI/CD details](docs/ci-cd.md) · [Contributing](CONTRIBUTING.md)

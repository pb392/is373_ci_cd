# CI/CD specification

The original ARM64 demo is recorded in [evidence](evidence.md). The current pipeline extends it to native AMD64 and ARM64 delivery; see [integration evidence](integration-evidence.md) for validation status.

## Pipeline contract

1. Two native jobs (`ubuntu-24.04` for AMD64 and `ubuntu-24.04-arm` for ARM64) install locked dependencies and run unit/integration tests.
2. Each builds one release image with the exact Git commit and build timestamp, then runs Chromium E2E against that image on isolated port 18090.
3. Each exports that image with `docker save` and records its image ID, architecture, OS, and tested commit. The image archive is not rebuilt in publication.
4. The stable required check `verify` fails unless both jobs succeeded. Existing branch protection continues to require this name.
5. Only a successful push to current `main` authenticates to Docker Hub. The publisher loads both archives, compares them with their test evidence and embedded release labels, and checks that main has not advanced.
6. It pushes immutable-by-convention platform tags, creates one multi-platform commit index from their registry digests, rechecks main, and copies that index to `prod`.

PRs and manual dispatch can verify but never publish. A PR run does not receive publishing credentials. Test/image artifacts are scoped to the current workflow run. Release image archives expire after two days; test and publication evidence after seven. Do not use `pull_request_target` to execute untrusted contributor code with secrets.

## Tags and identity

| Reference | Meaning |
|---|---|
| `sha-<full-commit>-amd64` | Exact native AMD64 image tested for that commit |
| `sha-<full-commit>-arm64` | Exact native ARM64 image tested for that commit |
| `sha-<full-commit>` | Multi-platform index containing both tested images |
| `prod` | Moving channel pointing at the latest promoted index |
| `@sha256:...` | Immutable registry content identity (index or platform manifest) |

All references use repository `pb392/is373_ci_cd`. Docker selects the appropriate platform from an index. The image ID used by the runtime is the local platform image's identity; it is not necessarily the registry index digest. Publication evidence records child manifests and the index so the distinction can be taught explicitly.

Tags are protected by project convention, not registry immutability. The publisher refuses a rerun if any commit tag already exists, including a partially uploaded platform release. Publish a new commit after diagnosing an interrupted release. Do not overwrite old evidence or silently rebuild for the same tag.

Workflow concurrency serializes production releases without cancelling an in-progress push. A stale-main check runs before upload and again immediately before moving `prod`. Partial uploads may leave unused commit tags; a failed pre-promotion step leaves the existing production channel unchanged. A new main commit can still arrive immediately after the final check; the serialized newer run will follow. This is not a transaction across GitHub and Docker Hub.

## Credentials and architecture

The publisher uses the existing `DOCKER_API_REP` Actions secret. Keep it out of Git and logs. The pinned Python and WUD image indexes include both supported architectures. Local `make build` targets the Docker daemon's architecture unless `BUILD_PLATFORM` selects a supported override.

The original demo tags are ARM64-only. New indexes support both architectures; do not promise AMD64 rollback to a historical tag without inspecting its manifest. The single-platform E2E images are tested natively, not merely built with emulation.

## Host-side deployment

WUD polls the digest behind `prod`, filters candidates to that tag, and updates only the opted-in production container. Development, WUD itself, and unrelated hosting services are not opted in. The Docker trigger preserves the application's runtime configuration; confirm its network and Traefik labels during the public-update exercise.

`make deploy` pulls the selected published image, starts production without development, checks its actual image/health identity, and starts WUD unless a pause marker exists. `make up` additionally builds/starts development. Every lifecycle command includes an optional local `compose.override.yaml`.

WUD polls outward, so there is no server SSH credential in GitHub Actions. Private registry deployments need separate read credentials for host pulls and updater checks. A GitHub publishing secret does not configure the host automatically.

## Recovery

`make rollback RELEASE=sha-<full-commit>` or `RELEASE=sha256:<digest>` pauses WUD, persists the selected reference, pulls and recreates only production, and verifies the actual container image ID plus `/health` release identity. It leaves updates paused. Persisted release state overrides inherited shell `PROD_IMAGE`.

`make resume-updates` restores `prod`, verifies it, starts WUD, and clears the pause marker. Resuming while `prod` still points to a bad release deploys that release again. Bare Compose commands bypass the wrapper's release-state loading; use the Make interface.

A failed build/test cannot publish. An unhealthy replacement is a failed deployment even if publication succeeded; the operator performs rollback. A single production container has a brief interruption during recreation. Automatic health-based rollback and high availability remain out of scope.

## Completion evidence

For a release: record workflow URL, commit, index digest, child digests, and both native E2E results. For a deployment: additionally record the actual container image, updater event, and observed health commit. Public integration also requires trusted HTTPS and the expected public `/health` commit. Publication alone never proves deployment.

References: [native multi-platform builds](https://docs.docker.com/build/ci/github-actions/multi-platform/), [manifest creation](https://docs.docker.com/reference/cli/docker/buildx/imagetools/create/), [WUD watchers](https://getwud.app/docs/configuration/watchers/), and [hosting handoff](hosting.md).

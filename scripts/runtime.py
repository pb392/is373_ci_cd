"""Small Docker operations shared by local development and CI."""

import base64
import datetime
import json
import os
from pathlib import Path
import subprocess
import re
import secrets
import sys
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".state"
ARTIFACTS = ROOT / "artifacts"
IMAGE = os.getenv("IMAGE", "is373-ci-cd:local")
REPOSITORY = "pb392/is373_ci_cd"


def run(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, check=True, text=True, **kwargs)


def output(args):
    try:
        return run(args, capture_output=True).stdout.strip()
    except subprocess.CalledProcessError as error:
        print(error.stderr or str(error), file=sys.stderr)
        raise


def compose(*args, capture_output=False):
    cmd = ["docker", "compose"]
    for path in (ROOT / ".env", STATE / "release.env"):
        if path.exists():
            cmd += ["--env-file", str(path)]
    cmd += ["-f", str(ROOT / "compose.yaml")]
    override = ROOT / "compose.override.yaml"
    if override.exists():
        cmd += ["-f", str(override)]
    environment = os.environ.copy()
    # A persisted rollback/resume selection must beat an inherited shell value.
    selected = STATE / "release.env"
    if selected.exists():
        values = dict(line.split("=", 1) for line in selected.read_text().splitlines()
                      if line and not line.startswith("#"))
        environment["PROD_IMAGE"] = values["PROD_IMAGE"]
    return run(cmd + list(args), env=environment, capture_output=capture_output)


def wait_for_health(url, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                data = json.load(response)
            if data.get("status") == "ok":
                return data
        except (OSError, ValueError):
            pass
        time.sleep(0.25)
    raise RuntimeError(f"Application not ready after {timeout}s: {url}")


def build():
    commit = output(["git", "rev-parse", "HEAD"])
    if output(["git", "status", "--porcelain"]):
        commit += "-dirty"
    built_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    target = os.getenv("BUILD_PLATFORM")
    if not target:
        architecture = output(["docker", "info", "--format", "{{.Architecture}}"])
        architecture = {"aarch64": "arm64", "x86_64": "amd64"}.get(architecture, architecture)
        target = "linux/" + architecture
    if target not in ("linux/amd64", "linux/arm64"):
        raise ValueError("BUILD_PLATFORM must be linux/amd64 or linux/arm64")
    run(["docker", "buildx", "build", "--load", "--platform", target,
         "--build-arg", f"COMMIT_SHA={commit}", "--build-arg", f"BUILT_AT={built_at}",
         "--tag", IMAGE, "."])


def test_e2e():
    STATE.mkdir(exist_ok=True)
    ARTIFACTS.mkdir(exist_ok=True)
    record = STATE / "tested-image.json"
    record.unlink(missing_ok=True)
    image = json.loads(output(["docker", "image", "inspect", IMAGE]))[0]
    image_id = image["Id"]
    expected_commit = image["Config"]["Labels"]["org.opencontainers.image.revision"]
    port = int(os.getenv("E2E_PORT", "18090"))
    name = "is373-e2e-" + uuid.uuid4().hex[:10]
    container_id = None
    startup_error = ""
    try:
        container_id = output(["docker", "run", "-d", "--name", name,
                               "-p", f"127.0.0.1:{port}:8000", "-e", "APP_ENV=test", image_id])
        health = wait_for_health(f"http://127.0.0.1:{port}/health")
        if health["commit"] != expected_commit:
            raise RuntimeError("Health release identity does not match the built image")
        run(["make", "test-browser", f"BASE_URL=http://127.0.0.1:{port}"], timeout=180)
        record.write_text(json.dumps({"image_id": image_id, "commit": expected_commit,
                                      "architecture": image["Architecture"], "os": image["Os"],
                                      "health": health}, indent=2))
        print(f"Verified image {image_id} at commit {expected_commit}", flush=True)
    except subprocess.CalledProcessError as error:
        startup_error = (error.stdout or "") + (error.stderr or "")
        raise
    finally:
        # Docker may create the named container before failing to bind the port.
        target = container_id or name
        exists = subprocess.run(["docker", "container", "inspect", target], capture_output=True).returncode == 0
        logs = subprocess.run(["docker", "logs", target], capture_output=True, text=True) if exists else None
        (ARTIFACTS / "container.log").write_text(startup_error + (logs.stdout + logs.stderr if logs else ""))
        if exists:
            subprocess.run(["docker", "rm", "-f", target], check=True, stdout=subprocess.DEVNULL)


def initialize_updater():
    STATE.mkdir(exist_ok=True)
    credentials = STATE / "wud.env"
    if not credentials.exists():
        with os.fdopen(os.open(credentials, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as handle:
            handle.write("WUD_AUTH_ADMIN_USER=admin\nWUD_AUTH_ADMIN_PASSWORD=" + secrets.token_urlsafe(24) + "\n")
    print("WUD dashboard: http://localhost:8091 (credentials in ignored .state/wud.env)")


def pause_updates():
    STATE.mkdir(exist_ok=True)
    (STATE / "updates-paused").touch()
    compose("stop", "wud")
    print("Automatic updates are paused. Use make resume-updates deliberately.")


def select_release(reference):
    STATE.mkdir(exist_ok=True)
    temp = STATE / "release.env.tmp"
    temp.write_text(f"PROD_IMAGE={reference}\n")
    temp.replace(STATE / "release.env")


def verify_production(reference):
    image = json.loads(output(["docker", "image", "inspect", reference]))[0]
    container_id = compose("ps", "-q", "prod", capture_output=True).stdout.strip()
    if not container_id:
        raise RuntimeError("Production container is not running")
    running = output(["docker", "inspect", container_id, "--format", "{{.Image}}"])
    if running != image["Id"]:
        raise RuntimeError("Production container is not running the selected image ID")
    expected = image["Config"]["Labels"]["org.opencontainers.image.revision"]
    health = wait_for_health("http://127.0.0.1:8090/health")
    if health["commit"] != expected or health["environment"] != "production":
        raise RuntimeError("Production health does not identify the selected release")
    print(json.dumps(health, indent=2))


def production_reference():
    # Render privately: the full model may contain updater credentials.
    model = json.loads(compose("config", "--format", "json", capture_output=True).stdout)
    return model["services"]["prod"]["image"]


def deploy(include_dev=False):
    initialize_updater()
    compose("pull", "prod")
    if include_dev:
        compose("up", "-d", "--build", "dev", "prod")
    else:
        compose("up", "-d", "--no-deps", "prod")
    verify_production(production_reference())
    if not (STATE / "updates-paused").exists():
        compose("up", "-d", "wud")


def rollback():
    release = os.getenv("RELEASE", "")
    if re.fullmatch(r"sha-[0-9a-f]{40}", release):
        reference = f"{REPOSITORY}:{release}"
    elif re.fullmatch(r"sha256:[0-9a-f]{64}", release):
        reference = f"{REPOSITORY}@{release}"
    else:
        raise SystemExit("Use RELEASE=sha-<full-commit> or RELEASE=sha256:<digest>")
    pause_updates()
    run(["docker", "pull", reference])
    select_release(reference)
    compose("up", "-d", "--no-deps", "prod")
    verify_production(reference)


def resume_updates():
    initialize_updater()
    pause_updates()
    reference = f"{REPOSITORY}:prod"
    run(["docker", "pull", reference])
    select_release(reference)
    compose("up", "-d", "--no-deps", "prod")
    verify_production(reference)
    compose("up", "-d", "wud")
    (STATE / "updates-paused").unlink(missing_ok=True)
    print("Production channel restored; automatic updates resumed.")


def check_updates():
    if (STATE / "updates-paused").exists():
        raise SystemExit("Updates are paused. Use make resume-updates only when the prod channel is safe.")
    credentials = dict(line.split("=", 1) for line in (STATE / "wud.env").read_text().splitlines())
    auth = base64.b64encode((credentials["WUD_AUTH_ADMIN_USER"] + ":" + credentials["WUD_AUTH_ADMIN_PASSWORD"]).encode()).decode()
    request = urllib.request.Request("http://127.0.0.1:8091/api/containers/watch", data=b"", headers={"Authorization": "Basic " + auth}, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        response.read()
    print("Registry check requested. Watch production health or WUD logs for the update.")


def main():
    command = sys.argv[1]
    if command == "build":
        build()
    elif command == "test-e2e":
        test_e2e()
    elif command == "dev":
        compose("up", "-d", "--build", "dev")
    elif command == "up":
        deploy(include_dev=True)
    elif command == "deploy":
        deploy()
    elif command == "verify-production":
        verify_production(production_reference())
    elif command == "down":
        compose("down")
    elif command == "rollback":
        rollback()
    elif command == "pause-updates":
        pause_updates()
    elif command == "resume-updates":
        resume_updates()
    elif command == "check-updates":
        check_updates()
    elif command == "status":
        compose("ps")
        print("Updates:", "paused" if (STATE / "updates-paused").exists() else "enabled")
        print(json.dumps(wait_for_health("http://127.0.0.1:8090/health"), indent=2))
    else:
        raise SystemExit(f"Unknown command: {command}")


if __name__ == "__main__":
    main()

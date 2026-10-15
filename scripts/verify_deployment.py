"""Confirm the automatic updater deployed the expected release over trusted HTTPS."""
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request


def matches(health, commit, environment):
    return (health.get("status") == "ok" and health.get("commit") == commit
            and health.get("environment") == environment)


def main():
    url = os.environ["DEPLOY_URL"].rstrip("/")
    commit = os.environ["EXPECTED_COMMIT"]
    environment = os.environ["DEPLOY_ENV"]
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url + "/health", timeout=10) as response:
                if response.url != url + "/health":
                    raise ValueError("Unexpected health redirect")
                health = json.load(response)
            if matches(health, commit, environment):
                with urllib.request.urlopen(url + "/", timeout=10) as response:
                    if response.status != 200:
                        raise ValueError("Homepage unavailable")
                Path("artifacts").mkdir(exist_ok=True)
                record = {"url": url, "health": health, "https_verified": True}
                Path("artifacts/deployment.json").write_text(json.dumps(record, indent=2))
                print(json.dumps(record, indent=2))
                with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
                    summary.write(f"\n## Verified automatic deployment\n\n{url} runs `{commit}` in `{environment}` over trusted HTTPS.\n")
                return
            print("Waiting for the selected environment to update", flush=True)
        except (OSError, ValueError) as error:
            print(f"Waiting for public readiness: {type(error).__name__}", flush=True)
        time.sleep(10)
    raise SystemExit("Expected release was not observed; deployment is not verified")


if __name__ == "__main__":
    main()

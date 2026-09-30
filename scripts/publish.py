"""Publish two native-tested artifacts, then promote their multi-platform index."""

import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request

REPOSITORY = "pb392/is373_ci_cd"
ARCHITECTURES = ("amd64", "arm64")


def output(args):
    return subprocess.check_output(args, text=True).strip()


def validate_release(event, ref, commit, main_head, tested, image_id):
    if event != "push" or ref != "refs/heads/main":
        raise ValueError("Publication requires a main push, never a PR or manual run")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("A full commit SHA is required")
    if commit != main_head:
        raise ValueError("Refusing to promote a stale main commit")
    if tested.get("commit") != commit or tested.get("image_id") != image_id:
        raise ValueError("The publish image must be the exact E2E-tested release")


def tag_exists(repository, tag):
    try:
        with urllib.request.urlopen(f"https://hub.docker.com/v2/repositories/{repository}/tags/{tag}/", timeout=20):
            return True
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False
        raise  # A network/auth failure is not evidence that a tag is absent.


def validate_artifact(architecture, tested, image, commit):
    if architecture not in ARCHITECTURES:
        raise ValueError("Unexpected release architecture")
    if tested.get("architecture") != architecture or tested.get("os") != "linux":
        raise ValueError("Test evidence has the wrong platform")
    if image.get("Architecture") != architecture or image.get("Os") != "linux":
        raise ValueError("Loaded image has the wrong platform")
    if image.get("Id") != tested.get("image_id") or tested.get("commit") != commit:
        raise ValueError("Loaded artifact is not the tested commit/image")
    if image.get("Config", {}).get("Labels", {}).get("org.opencontainers.image.revision") != commit:
        raise ValueError("Image release label does not match the commit")


def main():
    commit = os.environ["GITHUB_SHA"]
    github_repo = os.environ["GITHUB_REPOSITORY"]
    artifacts = Path(os.getenv("RELEASE_DIR", "release-images"))
    releases = {}
    # Validate all artifacts before pushing any tags. docker load does not rebuild.
    for architecture in ARCHITECTURES:
        folder = artifacts / ("release-" + architecture)
        tested = json.loads((folder / "tested-image.json").read_text())
        subprocess.run(["docker", "load", "-i", str(folder / "image.tar")], check=True)
        image = json.loads(output(["docker", "image", "inspect", tested["image_id"]]))[0]
        validate_artifact(architecture, tested, image, commit)
        releases[architecture] = tested

    def check_current():
        head = output(["gh", "api", f"repos/{github_repo}/git/ref/heads/main", "--jq", ".object.sha"])
        for tested in releases.values():
            validate_release(os.environ["GITHUB_EVENT_NAME"], os.environ["GITHUB_REF"],
                             commit, head, tested, tested["image_id"])

    check_current()
    commit_tag = f"sha-{commit}"
    tags = [commit_tag] + [f"{commit_tag}-{arch}" for arch in ARCHITECTURES]
    if any(tag_exists(REPOSITORY, tag) for tag in tags):
        raise SystemExit("A commit tag already exists. Refusing a full or partial release overwrite; use a new commit.")

    sources = []
    for architecture, tested in releases.items():
        reference = f"{REPOSITORY}:{commit_tag}-{architecture}"
        subprocess.run(["docker", "tag", tested["image_id"], reference], check=True)
        subprocess.run(["docker", "push", reference], check=True)
        details = json.loads(output(["docker", "image", "inspect", reference]))[0]
        digest = next(d for d in details["RepoDigests"] if d.startswith(REPOSITORY + "@"))
        sources.append(digest)
        tested["digest"] = digest

    Path("artifacts").mkdir(exist_ok=True)
    metadata = Path("artifacts/index.json")
    version = f"{REPOSITORY}:{commit_tag}"
    subprocess.run(["docker", "buildx", "imagetools", "create", "--tag", version,
                    "--metadata-file", str(metadata), *sources], check=True)
    digest = json.loads(metadata.read_text())["containerimage.descriptor"]["digest"]
    reference = f"{REPOSITORY}@{digest}"
    # No rebuild: prod becomes a copy of the immutable, two-platform index.
    check_current()
    channel = f"{REPOSITORY}:prod"
    subprocess.run(["docker", "buildx", "imagetools", "create", "--tag", channel, reference], check=True)
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
        summary.write(f"## Published multi-platform release\n\n- Commit: `{commit}`\n- Version: `{version}`\n- Channel: `{channel}`\n- Index: `{reference}`\n\nBoth native artifacts passed E2E before publication. Verify the running `/health` commit separately.\n")
    Path("artifacts/release.json").write_text(json.dumps(
        {"commit": commit, "version": version, "digest": reference, "platforms": releases}, indent=2))


if __name__ == "__main__":
    main()

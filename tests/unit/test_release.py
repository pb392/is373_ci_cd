import pytest

from scripts.publish import validate_artifact, validate_release

SHA = "a" * 40
IMAGE_ID = "sha256:" + "b" * 64


@pytest.mark.parametrize("ref", ["refs/heads/main", "refs/heads/qa"])
def test_current_tested_branch_artifact_can_publish(ref):
    validate_release("push", ref, SHA, SHA, {"commit": SHA, "image_id": IMAGE_ID}, IMAGE_ID)


@pytest.mark.parametrize("event,ref,commit,head,tested", [
    ("push", "refs/heads/feature", SHA, SHA, {"commit": SHA, "image_id": IMAGE_ID}),
    ("push", "refs/heads/qa", SHA, "c" * 40, {"commit": SHA, "image_id": IMAGE_ID}),
    ("pull_request", "refs/pull/1/merge", SHA, SHA, {"commit": SHA, "image_id": IMAGE_ID}),
    ("workflow_dispatch", "refs/heads/main", SHA, SHA, {"commit": SHA, "image_id": IMAGE_ID}),
    ("push", "refs/heads/main", SHA, "c" * 40, {"commit": SHA, "image_id": IMAGE_ID}),
    ("push", "refs/heads/main", SHA, SHA, {"commit": SHA, "image_id": "different-build"}),
    ("push", "refs/heads/main", SHA, SHA, {"commit": "different-commit", "image_id": IMAGE_ID}),
    ("push", "refs/heads/main", "local", "local", {"commit": "local", "image_id": IMAGE_ID}),
])
def test_unsafe_release_is_refused(event, ref, commit, head, tested):
    with pytest.raises(ValueError):
        validate_release(event, ref, commit, head, tested, IMAGE_ID)


@pytest.mark.parametrize('arch', ['amd64', 'arm64'])
def test_native_artifact_matches_evidence(arch):
    tested = {'architecture': arch, 'os': 'linux', 'image_id': IMAGE_ID, 'commit': SHA}
    image = {'Architecture': arch, 'Os': 'linux', 'Id': IMAGE_ID,
             'Config': {'Labels': {'org.opencontainers.image.revision': SHA}}}
    validate_artifact(arch, tested, image, SHA)


@pytest.mark.parametrize('field,value', [('Architecture', 'arm64'), ('Os', 'windows'), ('Id', 'rebuilt')])
def test_wrong_or_rebuilt_artifact_is_rejected(field, value):
    tested = {'architecture': 'amd64', 'os': 'linux', 'image_id': IMAGE_ID, 'commit': SHA}
    image = {'Architecture': 'amd64', 'Os': 'linux', 'Id': IMAGE_ID,
             'Config': {'Labels': {'org.opencontainers.image.revision': SHA}}}
    image[field] = value
    with pytest.raises(ValueError):
        validate_artifact('amd64', tested, image, SHA)

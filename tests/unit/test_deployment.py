from scripts.verify_deployment import matches


def test_deployment_requires_expected_commit_environment_and_health():
    assert matches({"status": "ok", "commit": "abc", "environment": "qa"}, "abc", "qa")
    assert not matches({"status": "ok", "commit": "old", "environment": "qa"}, "abc", "qa")
    assert not matches({"status": "ok", "commit": "abc", "environment": "production"}, "abc", "qa")
    assert not matches({"status": "error", "commit": "abc", "environment": "qa"}, "abc", "qa")

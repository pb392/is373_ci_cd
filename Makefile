.PHONY: setup browsers test-unit test-integration test-browser build test-e2e dev up deploy verify-production down rollback pause-updates resume-updates check-updates status

UV := sh scripts/uv.sh

setup:
	$(UV) sync --frozen

browsers:
	$(UV) run --frozen playwright install chromium

test-unit:
	$(UV) run --frozen pytest tests/unit -q

test-integration:
	$(UV) run --frozen pytest tests/integration -q

BASE_URL ?= http://127.0.0.1:18090
test-browser:
	$(UV) run --frozen pytest tests/e2e -q --base-url=$(BASE_URL) --browser chromium --tracing retain-on-failure --screenshot only-on-failure --output artifacts/playwright

export RELEASE
build test-e2e dev up deploy deploy-qa verify-production down rollback pause-updates resume-updates check-updates status:
	python3 scripts/runtime.py $@

FROM python:3.13.15-slim-bookworm@sha256:ed86c82274b3c69b52fb5820f358f0bd7df0b603332063cb5c6e32bd220c3e6e AS dependencies
WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.15
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --python /usr/local/bin/python

FROM python:3.13.15-slim-bookworm@sha256:ed86c82274b3c69b52fb5820f358f0bd7df0b603332063cb5c6e32bd220c3e6e AS runtime
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=production
RUN useradd --uid 10001 --create-home appuser
COPY --from=dependencies /app/.venv /app/.venv
COPY app ./app
ARG COMMIT_SHA=local
ARG BUILT_AT=unavailable
RUN COMMIT_SHA="$COMMIT_SHA" BUILT_AT="$BUILT_AT" python -c 'import json,os; from pathlib import Path; Path("app/release.json").write_text(json.dumps({"commit":os.environ["COMMIT_SHA"],"built_at":os.environ["BUILT_AT"]}))'
LABEL org.opencontainers.image.source="https://github.com/pb392/is373_ci_cd" org.opencontainers.image.revision="$COMMIT_SHA" org.opencontainers.image.created="$BUILT_AT"
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=6 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

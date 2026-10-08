"""HTTP contracts and release identity for the demo."""

import json
import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.calculator import LIMIT, CalculationError, Operation, calculate

app = FastAPI(title="CI/CD Calculator", version="0.1.0")
Operand = Annotated[float, Field(strict=True, ge=-LIMIT, le=LIMIT, allow_inf_nan=False)]


@app.get("/", include_in_schema=False)
def homepage():
    return render_page("home")


@app.get("/calculator", include_in_schema=False)
def calculator_page():
    return render_page("calculator")


def render_page(page):
    html = Path(__file__).with_name("index.html").read_text()
    return HTMLResponse(html.replace("__PAGE__", page), headers={"Cache-Control": "no-store"})


@app.exception_handler(RequestValidationError)
async def validation_error(_request, error):
    # Untrusted inputs such as NaN cannot be serialized back into strict JSON.
    # Keep the normal validation shape without echoing input or exception context.
    return JSONResponse(status_code=422, content={"detail": [
        {key: item[key] for key in ("type", "loc", "msg")}
        for item in error.errors()
    ]})


class CalculationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    a: Operand
    b: Operand
    operation: Operation


class CalculationResponse(BaseModel):
    result: float


@app.post("/api/calculate", response_model=CalculationResponse)
def calculate_route(request: CalculationRequest):
    try:
        return {"result": calculate(request.a, request.b, request.operation)}
    except CalculationError as error:
        raise HTTPException(
            status_code=400, detail={"code": error.code, "message": str(error)}
        ) from error


@app.get("/health")
def health():
    release_file = Path(__file__).with_name("release.json")
    release = json.loads(release_file.read_text()) if release_file.exists() else {
        "commit": os.getenv("APP_COMMIT", "local"),
        "built_at": os.getenv("APP_BUILT_AT", "unavailable"),
    }
    return {
        "status": "ok",
        "environment": os.getenv("APP_ENV", "development"),
        **release,
    }

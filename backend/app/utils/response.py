# app/utils/response.py
from typing import Any, List
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

def _to_list(data: Any) -> List[Any]:
    if data is None:
        return []
    if isinstance(data, (list, tuple)):
        return list(data)
    return [data]

def success(message: str = "OK", data: Any = None, status_code: int = 200) -> JSONResponse:
    payload = _to_list(data)
    return JSONResponse(
        status_code=status_code,
        content={
            "code": status_code,
            "messages": message,
            "data": jsonable_encoder(payload, by_alias=True),
        },
    )

def error(message: str = "Error", status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": status_code, "messages": message},
    )

def setup_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers with unified JSON shape."""

    @app.exception_handler(HTTPException)
    async def http_exc_handler(request: Request, exc: HTTPException):
        msg = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        return error(message=msg, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exc_handler(request: Request, exc: RequestValidationError):
        parts = []
        for e in exc.errors():
            loc = ".".join(str(p) for p in e.get("loc", []))
            msg = e.get("msg", "Validation error")
            typ = e.get("type")
            ctx = e.get("ctx") or {}

            if typ in {"string_too_short", "too_short"} and ctx.get("min_length") == 1:
                field = loc.split(".")[-1]
                msg = f"{field} is required"

            parts.append(f"{loc}: {msg}")

        return error(message="; ".join(parts), status_code=422)

    @app.exception_handler(Exception)
    async def unhandled_exc_handler(request: Request, exc: Exception):
        return error(message="Internal Server Error", status_code=500)

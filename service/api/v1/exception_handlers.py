"""
Exception handlers for the FastAPI application.

## Traceability
Feature: F001-F009 — All features
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from core.exceptions import AppException


def register_exception_handlers(app):
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

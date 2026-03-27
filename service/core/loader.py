"""
FastAPI application factory.

## Traceability
Feature: F001-F009 — All features
"""
from fastapi import FastAPI
from api.v1.include_router import include_routers
from api.v1.exception_handlers import register_exception_handlers

app = FastAPI(title="Product Engineer Bot — Backend API", version="0.1.0")
include_routers(app)
register_exception_handlers(app)

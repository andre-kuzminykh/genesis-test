"""
FastAPI application factory.

## Traceability
Feature: F001-F009 — All features
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.v1.include_router import include_routers
from api.v1.exception_handlers import register_exception_handlers
from core.database import db_connect
from model.base_model import Base
import model  # noqa: F401 — register all models for create_all


@asynccontextmanager
async def lifespan(application: FastAPI):
    db_connect.init()
    async with db_connect.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Product Engineer Bot — Backend API",
    version="0.1.0",
    lifespan=lifespan,
)
include_routers(app)
register_exception_handlers(app)

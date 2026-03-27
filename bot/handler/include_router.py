"""Register all feature routers with the root dispatcher.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

from aiogram import Dispatcher

from handler.v1.user.start_widget import router as start_router
from handler.v1.user.chat.gpt_chat_widget import router as gpt_chat_router
from handler.v1.user.chat.gpt_generate_widget import router as gpt_generate_router
from handler.v1.user.product.F001.product_list_widget import router as product_list_router
from handler.v1.user.product.F001.product_create_widget import router as product_create_router
from handler.v1.user.product.F001.product_detail_widget import router as product_detail_router
from handler.v1.user.feature.F002.feature_list_widget import router as feature_list_router
from handler.v1.user.story.F004.story_list_widget import router as story_list_router
from handler.v1.user.health.F009.health_widget import router as health_router


def include_routers(dp: Dispatcher) -> None:
    """Attach every feature router to the dispatcher."""
    dp.include_routers(
        start_router,
        gpt_chat_router,
        gpt_generate_router,
        product_list_router,
        product_create_router,
        product_detail_router,
        feature_list_router,
        story_list_router,
        health_router,
    )

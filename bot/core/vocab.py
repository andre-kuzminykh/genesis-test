"""UI texts, button labels, and command descriptions.

## Traceability
Product: Telegram Product Engineer Bot
"""

# ── Commands ──────────────────────────────────────────────
COMMANDS = {
    "start": "Start the bot",
    "products": "List all products",
    "features": "List features for a product",
    "stories": "List user stories",
    "health": "Check backend health",
}

# ── Button labels ─────────────────────────────────────────
BTN_CREATE = "Create"
BTN_BACK = "Back"
BTN_APPROVE = "Approve"
BTN_DETAIL = "Detail"
BTN_DELETE = "Delete"
BTN_REFRESH = "Refresh"

# ── Message templates ─────────────────────────────────────
MSG_WELCOME = "Welcome to the Product Engineer Bot! Use /products to get started."
MSG_PRODUCT_LIST_HEADER = "Products:"
MSG_PRODUCT_CREATED = "Product <b>{name}</b> created successfully."
MSG_PRODUCT_DETAIL = (
    "<b>{name}</b>\n"
    "Status: {status}\n"
    "Description: {description}"
)
MSG_FEATURE_LIST_HEADER = "Features for product <b>{product_name}</b>:"
MSG_STORY_LIST_HEADER = "User Stories:"
MSG_HEALTH_OK = "Backend is healthy."
MSG_HEALTH_FAIL = "Backend is unreachable."
MSG_ERROR = "Something went wrong. Please try again."
MSG_NOT_FOUND = "Entity not found."
MSG_ENTER_PRODUCT_NAME = "Enter the product name:"
MSG_ENTER_PRODUCT_DESCRIPTION = "Enter the product description:"
MSG_EMPTY_LIST = "No items found."

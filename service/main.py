"""
Entry point for the backend service.

## Traceability
Product: Telegram Product Engineer Bot
"""
import uvicorn


def main():
    uvicorn.run(
        "core.loader:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()

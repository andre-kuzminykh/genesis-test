"""
Application exceptions.

## Traceability
Feature: F001-F009 — All features
"""


class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):
    def __init__(self, entity: str, entity_id: str):
        super().__init__(f"{entity} with id '{entity_id}' not found", status_code=404)


class ValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class ConflictError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)

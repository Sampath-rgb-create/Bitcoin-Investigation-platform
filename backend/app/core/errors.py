from typing import Any, Dict, Optional


class PlatformException(Exception):
    """Base exception class for Bitcoin Investigation Platform."""
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class SchemaValidationError(PlatformException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="DATA_SCHEMA_INVALID",
            message=message,
            status_code=400,
            details=details,
        )


class AuthenticationError(PlatformException):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(
            code="AUTH_INVALID",
            message=message,
            status_code=401,
        )


class PermissionDeniedError(PlatformException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=403,
        )


class EntityNotFoundError(PlatformException):
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            code=f"{entity_type.upper()}_NOT_FOUND",
            message=f"{entity_type.capitalize()} '{entity_id}' was not found.",
            status_code=404,
            details={"entity_type": entity_type, "entity_id": entity_id},
        )


class ConflictError(PlatformException):
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=code,
            message=message,
            status_code=409,
            details=details,
        )


class OfflineConstraintViolationError(PlatformException):
    def __init__(self, message: str = "External network call attempted while OFFLINE_MODE is true"):
        super().__init__(
            code="OFFLINE_VIOLATION",
            message=message,
            status_code=503,
        )

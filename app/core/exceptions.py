import logging
from typing import Any, Dict

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class GestionePalchiException(Exception):
    """Base exception for Gestione Palchi application"""

    def __init__(
        self, message: str, status_code: int = 500, details: Dict[str, Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(GestionePalchiException):
    """Raised when validation fails"""

    def __init__(self, message: str, field: str = None):
        details = {"field": field} if field else {}
        super().__init__(message, 422, details)


class NotFoundException(GestionePalchiException):
    """Raised when a resource is not found"""

    def __init__(
        self, message: str, resource_type: str = None, resource_id: str = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, 404, details)


class BusinessLogicException(GestionePalchiException):
    """Raised when business logic rules are violated"""

    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, 400, details)


class ConflictException(GestionePalchiException):
    """Raised when there's a conflict in data"""

    def __init__(self, message: str, conflicting_field: str = None):
        details = {"conflicting_field": conflicting_field} if conflicting_field else {}
        super().__init__(message, 409, details)


class AuthenticationException(GestionePalchiException):
    """Raised when authentication fails"""

    def __init__(self, message: str = "❌ Autenticazione fallita"):
        super().__init__(message, 401)


class AuthorizationException(GestionePalchiException):
    """Raised when authorization fails"""

    def __init__(self, message: str = "🚫 Permessi insufficienti"):
        super().__init__(message, 403)


# Legacy aliases for backward compatibility
ValidationError = ValidationException
NotFoundError = NotFoundException
ConflictError = ConflictException


async def gestione_palchi_exception_handler(
    request: Request, exc: GestionePalchiException
):
    logger.error(f"❌ Errore dell'applicazione: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "type": "application_error", **exc.details},
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.error(f"🗃️ Errore di integrità del database: {str(exc)}")
    return JSONResponse(
        status_code=409,
        content={
            "detail": "Violazione dei vincoli di integrità dei dati",
            "type": "database_error",
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"🚨 Errore inaspettato: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Errore interno del server", "type": "server_error"},
    )

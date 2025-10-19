"""
Custom exceptions for CatAlert application
"""
from typing import Any, Dict, Optional


class CatAlertException(Exception):
    """Base exception for CatAlert application"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "CATALERT_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(CatAlertException):
    """Validation error exception"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class NotFoundError(CatAlertException):
    """Resource not found exception"""
    
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with id {resource_id} not found",
            error_code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "resource_id": resource_id}
        )


class AuthenticationError(CatAlertException):
    """Authentication error exception"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401
        )


class AuthorizationError(CatAlertException):
    """Authorization error exception"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403
        )


class AIAgentError(CatAlertException):
    """AI Agent related error exception"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AI_AGENT_ERROR",
            status_code=500,
            details=details
        )


class ExternalServiceError(CatAlertException):
    """External service error exception"""
    
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"External service {service} error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details=details
        )

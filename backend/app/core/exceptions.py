"""Custom exceptions for the application"""

class BaseAppException(Exception):
    """Base exception for all application exceptions"""
    pass

class AuthenticationError(BaseAppException):
    """Raised when authentication fails"""
    pass

class AuthorizationError(BaseAppException):
    """Raised when user lacks required permissions"""
    pass

class ValidationError(BaseAppException):
    """Raised when validation fails"""
    pass

class NotFoundError(BaseAppException):
    """Raised when a resource is not found"""
    pass

class ConflictError(BaseAppException):
    """Raised when there's a conflict (e.g., duplicate entry)"""
    pass

class ExternalServiceError(BaseAppException):
    """Raised when an external service fails"""
    pass

class AIProviderError(ExternalServiceError):
    """Raised when AI provider (OpenAI, etc.) returns an error"""
    pass

class InsufficientCreditsError(BaseAppException):
    """Raised when there are insufficient credits for an operation"""
    pass

class CreditLimitExceededError(BaseAppException):
    """Raised when a credit limit (department, daily, etc.) would be exceeded"""
    pass

class PaymentError(BaseAppException):
    """Raised when payment processing fails"""
    pass

class SubscriptionError(BaseAppException):
    """Raised when subscription operations fail"""
    pass
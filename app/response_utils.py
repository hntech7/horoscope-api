from fastapi import Response, status
from typing import Any, Optional
from .schemas import StandardResponse

def create_success_response(
    response: Response,
    data: Any = None,
    message: str = "Operation successful",
    status_code: int = status.HTTP_200_OK
) -> StandardResponse:
    """
    Create a success response with proper HTTP status code
    
    Args:
        response: FastAPI Response object
        data: Response data
        message: Success message
        status_code: HTTP status code (200 for existing resources, 201 for created resources)
    
    Returns:
        StandardResponse with success=True
    """
    response.status_code = status_code
    return StandardResponse.success_response(data=data, message=message)

def create_error_response(
    response: Response,
    message: str,
    error: Optional[str] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> StandardResponse:
    """
    Create an error response with proper HTTP status code
    
    Args:
        response: FastAPI Response object
        message: Error message
        error: Detailed error information
        status_code: HTTP status code (400, 401, 403, 404, 422, 500, etc.)
    
    Returns:
        StandardResponse with success=False
    """
    response.status_code = status_code
    return StandardResponse.error_response(message=message, error=error)

def get_success_status_code(is_created: bool = False) -> int:
    """
    Get appropriate success status code
    
    Args:
        is_created: True if resource was created, False if existing resource was returned/updated
    
    Returns:
        201 for created resources, 200 for existing resources
    """
    return status.HTTP_201_CREATED if is_created else status.HTTP_200_OK

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .schemas import StandardResponse
import logging

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standardized response format"""
    
    # Determine if this is a success or error based on status code
    is_success = 200 <= exc.status_code < 300
    
    if is_success:
        response = StandardResponse.success_response(
            message=exc.detail or "Operation successful"
        )
    else:
        response = StandardResponse.error_response(
            message=exc.detail or "An error occurred",
            error=f"HTTP {exc.status_code}"
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with standardized response format"""
    
    # Extract validation error details
    error_details = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_details.append(f"{field}: {message}")
    
    error_message = "; ".join(error_details)
    
    response = StandardResponse.error_response(
        message="Validation error",
        error=error_message
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump()
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with standardized response format"""
    
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    response = StandardResponse.error_response(
        message="Internal server error",
        error="An unexpected error occurred"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump()
    )

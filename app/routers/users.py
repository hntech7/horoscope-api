from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List
from ..schemas import UserResponse, UserUpdate, UserCreate, StandardResponse
from ..crud import get_user, update_user, delete_user, create_user
from ..auth import get_current_user
from ..models import User
from ..response_utils import create_success_response, create_error_response

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/profile", response_model=StandardResponse[UserResponse])
async def get_user_profile(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile"""
    user_response = UserResponse.from_orm(current_user)
    return create_success_response(
        response,
        data=user_response,
        message="User profile retrieved successfully"
    )

@router.put("/profile", response_model=StandardResponse[UserResponse])
async def update_user_profile(
    user_update: UserUpdate,
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Update current user's profile"""
    try:
        updated_user = await update_user(current_user.user_id, user_update)
        if not updated_user:
            return create_error_response(
                response,
                "User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        user_response = UserResponse.from_orm(updated_user)
        return create_success_response(
            response,
            data=user_response,
            message="User profile updated successfully"
        )
    except ValueError as e:
        return create_error_response(
            response,
            str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return create_error_response(
            response,
            "Failed to update user profile",
            error=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.delete("/profile", response_model=StandardResponse[dict])
async def delete_user_profile(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Delete current user's profile"""
    try:
        success = await delete_user(current_user.user_id)
        if not success:
            return create_error_response(
                response,
                "User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return create_success_response(
            response,
            data={"deleted": True},
            message="User profile deleted successfully"
        )
    except Exception as e:
        return create_error_response(
            response,
            "Failed to delete user profile",
            error=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/{user_id}", response_model=StandardResponse[UserResponse])
async def get_user_by_id(
    user_id: str,
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Get user by ID (only accessible by the user themselves)"""
    try:
        if current_user.user_id != user_id:
            return create_error_response(
                response,
                "Access denied",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        user = await get_user(user_id)
        if not user:
            return create_error_response(
                response,
                "User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        user_response = UserResponse.from_orm(user)
        return create_success_response(
            response,
            data=user_response,
            message="User retrieved successfully"
        )
    except Exception as e:
        return create_error_response(
            response,
            "Failed to retrieve user",
            error=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

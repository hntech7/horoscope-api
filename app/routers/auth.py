from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from ..schemas import (
    TokenResponse, UserResponse, SocialLoginRequest, UserCreate,
    RefreshTokenRequest, RefreshTokenResponse, LogoutResponse, StandardResponse
)
from ..auth import (
    create_access_token, get_current_user, generate_user_id,
    create_refresh_token_record, verify_refresh_token, revoke_refresh_token,
    revoke_all_user_refresh_tokens, blacklist_token
)
from ..crud import get_user_by_provider_id, create_user, get_user_by_email
from ..models import User
from ..response_utils import create_success_response, create_error_response, get_success_status_code

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/social-login", response_model=StandardResponse[TokenResponse])
async def social_login(
    login_data: SocialLoginRequest,
    response: Response
):
    """Social login with Google or Apple - checks database only"""
    
    # Validate provider
    if login_data.provider not in ['google', 'apple']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider. Must be 'google' or 'apple'"
        )
    
    # Check if user exists by provider ID
    existing_user = await get_user_by_provider_id(
        login_data.provider, 
        login_data.provider_id
    )
    
    if existing_user:
        # User exists, return token with 200 status
        access_token = create_access_token(data={"sub": existing_user.user_id})
        refresh_token = await create_refresh_token_record(existing_user.user_id)
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(existing_user)
        )
        return create_success_response(
            response,
            data=token_response,
            message="Login successful",
            status_code=status.HTTP_200_OK
        )
    
    # Check if user exists by email (in case they registered with email before)
    if login_data.email:
        existing_user_by_email = await get_user_by_email(login_data.email)
        if existing_user_by_email:
            # Update existing user with social provider info (only if not empty)
            
            # Only update fields that have values and don't overwrite existing data with empty values
            if login_data.provider and not existing_user_by_email.provider:
                existing_user_by_email.provider = login_data.provider
            if login_data.provider_id and not existing_user_by_email.provider_id:
                existing_user_by_email.provider_id = login_data.provider_id
            if login_data.profile_image and not existing_user_by_email.profile_image:
                existing_user_by_email.profile_image = login_data.profile_image
            if login_data.name and not existing_user_by_email.name:
                existing_user_by_email.name = login_data.name
            
            existing_user_by_email.updated_at = datetime.utcnow()
            await existing_user_by_email.save()
            
            access_token = create_access_token(data={"sub": existing_user_by_email.user_id})
            refresh_token = await create_refresh_token_record(existing_user_by_email.user_id)
            token_response = TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                user=UserResponse.model_validate(existing_user_by_email)
            )
            return create_success_response(
                response,
                data=token_response,
                message="Login successful",
                status_code=status.HTTP_200_OK
            )
    
    # Create new user
    new_user_data = UserCreate(
        user_id=generate_user_id(),
        name=login_data.name,
        email=login_data.email,
        language=login_data.language,
        profile_image=login_data.profile_image,
        provider=login_data.provider,
        provider_id=login_data.provider_id
    )
    
    new_user = await create_user(new_user_data)
    
    # Create access token and refresh token
    access_token = create_access_token(data={"sub": new_user.user_id})
    refresh_token = await create_refresh_token_record(new_user.user_id)
    
    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )
    
    return create_success_response(
        response,
        data=token_response,
        message="User created and logged in successfully",
        status_code=status.HTTP_201_CREATED
    )


@router.post("/refresh", response_model=StandardResponse[RefreshTokenResponse])
async def refresh_access_token(refresh_data: RefreshTokenRequest, response: Response):
    """Refresh access token using refresh token"""
    
    # Verify refresh token
    refresh_token_record = await verify_refresh_token(refresh_data.refresh_token)
    if not refresh_token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user
    user = await User.find_one(User.user_id == refresh_token_record.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Revoke old refresh token
    await revoke_refresh_token(refresh_data.refresh_token)
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user.user_id})
    new_refresh_token = await create_refresh_token_record(user.user_id)
    
    refresh_response = RefreshTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )
    
    return create_success_response(
        response,
        data=refresh_response,
        message="Token refreshed successfully"
    )


@router.post("/logout", response_model=StandardResponse[LogoutResponse])
async def logout(
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user)
):
    """Logout user by blacklisting current token and revoking all refresh tokens"""
    
    # Blacklist the current access token
    access_token = credentials.credentials
    await blacklist_token(access_token, current_user.user_id)
    
    # Revoke all refresh tokens for the user
    await revoke_all_user_refresh_tokens(current_user.user_id)
    
    logout_response = LogoutResponse(message="Successfully logged out")
    return create_success_response(
        response,
        data=logout_response,
        message="Successfully logged out"
    )


@router.post("/logout-all", response_model=StandardResponse[LogoutResponse])
async def logout_all_devices(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Logout user from all devices by revoking all refresh tokens"""
    
    # Revoke all refresh tokens for the user
    await revoke_all_user_refresh_tokens(current_user.user_id)
    
    logout_response = LogoutResponse(message="Successfully logged out from all devices")
    return create_success_response(
        response,
        data=logout_response,
        message="Successfully logged out from all devices"
    )


@router.get("/me", response_model=StandardResponse[UserResponse])
async def get_current_user_info(
    response: Response,
    current_user = Depends(get_current_user)
):
    """Get current user information"""
    user_response = UserResponse.model_validate(current_user)
    return create_success_response(
        response,
        data=user_response,
        message="User information retrieved successfully"
    )

from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List, Optional
from datetime import datetime
from ..models import User, UserCredits, CreditTransaction, FeatureType, FEATURE_COSTS
from ..schemas import (
    CreditBalanceResponse, 
    FeatureUsageRequest, 
    CreditTransactionResponse, 
    CreditTransactionListResponse,
    AddCreditsRequest,
    StandardResponse
)
from ..auth import get_current_user
from ..response_utils import create_success_response, create_error_response

router = APIRouter(prefix="/credits", tags=["credits"])

async def get_or_create_user_credits(user_id: str) -> UserCredits:
    """Get user credits or create if doesn't exist"""
    user_credits = await UserCredits.find_one(UserCredits.user_id == user_id)
    if not user_credits:
        user_credits = UserCredits(user_id=user_id)
        await user_credits.save()
    return user_credits

@router.get("/balance", response_model=StandardResponse[CreditBalanceResponse])
async def get_credit_balance(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Get current user's credit balance"""
    try:
        user_credits = await get_or_create_user_credits(current_user.user_id)
        
        balance_response = CreditBalanceResponse(
            balance=user_credits.balance,
            total_earned=user_credits.total_earned,
            total_spent=user_credits.total_spent,
            updated_at=user_credits.updated_at
        )
        
        return create_success_response(
            response,
            data=balance_response,
            message="Credit balance retrieved successfully"
        )
    except Exception as e:
        return create_error_response(
            response,
            "Failed to retrieve credit balance",
            error=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.post("/use-feature", response_model=StandardResponse[dict])
async def use_feature(
    request: FeatureUsageRequest,
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Deduct credits for using a feature"""
    try:
        # Validate feature type
        try:
            feature_type = FeatureType(request.feature_type)
        except ValueError:
            return create_error_response(
                response,
                f"Invalid feature type: {request.feature_type}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Get credit cost for the feature
        credit_cost = FEATURE_COSTS[feature_type]
        
        # Get user credits
        user_credits = await get_or_create_user_credits(current_user.user_id)
        
        # Check if user has enough credits
        if user_credits.balance < credit_cost:
            return create_error_response(
                response,
                f"Insufficient credits. Required: {credit_cost}, Available: {user_credits.balance}",
                status_code=status.HTTP_402_PAYMENT_REQUIRED
            )
        
        # Deduct credits
        balance_before = user_credits.balance
        user_credits.balance -= credit_cost
        user_credits.total_spent += credit_cost
        user_credits.updated_at = datetime.utcnow()
        await user_credits.save()
        
        # Create transaction record
        transaction = CreditTransaction(
            user_id=current_user.user_id,
            transaction_type="debit",
            amount=credit_cost,
            feature_type=feature_type,
            description=f"Used {feature_type.value} feature",
            balance_before=balance_before,
            balance_after=user_credits.balance
        )
        await transaction.save()
        
        feature_usage_data = {
            "credits_deducted": credit_cost,
            "remaining_balance": user_credits.balance,
            "feature_type": feature_type.value
        }
        
        return create_success_response(
            response,
            data=feature_usage_data,
            message=f"Successfully used {feature_type.value} feature"
        )
        
    except Exception as e:
        return create_error_response(
            response,
            "Failed to process feature usage",
            error=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.post("/add", response_model=StandardResponse[dict])
async def add_credits(
    request: AddCreditsRequest,
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Add credits to user account (purchase or ad watch)"""
    try:
        if request.amount <= 0:
            return create_error_response(
                response,
                "Credit amount must be positive",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate credit type
        if request.credit_type not in ["purchase", "ad_watch"]:
            return create_error_response(
                response,
                "Credit type must be 'purchase' or 'ad_watch'",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user credits
        user_credits = await get_or_create_user_credits(current_user.user_id)
        
        # Add credits
        balance_before = user_credits.balance
        user_credits.balance += request.amount
        user_credits.total_earned += request.amount
        user_credits.updated_at = datetime.utcnow()
        await user_credits.save()
        
        # Set description based on credit type if not provided
        description = request.description
        if not description:
            description = f"Credits earned by {'watching ads' if request.credit_type == 'ad_watch' else 'purchase'}"
        
        # Create transaction record
        transaction = CreditTransaction(
            user_id=current_user.user_id,
            transaction_type="credit",
            amount=request.amount,
            credit_type=request.credit_type,
            description=description,
            balance_before=balance_before,
            balance_after=user_credits.balance
        )
        await transaction.save()
        
        credits_data = {
            "credits_added": request.amount,
            "credit_type": request.credit_type,
            "new_balance": user_credits.balance
        }
        
        return create_success_response(
            response,
            data=credits_data,
            message="Credits added successfully"
        )
        
    except Exception as e:
        return create_error_response(
            response,
            "Failed to add credits",
            error=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/transactions", response_model=StandardResponse[CreditTransactionListResponse])
async def get_credit_transactions(
    response: Response,
    skip: int = 0,
    limit: int = 20,
    transaction_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get user's credit transaction history"""
    try:
        # Build query
        query = CreditTransaction.user_id == current_user.user_id
        if transaction_type:
            if transaction_type not in ["credit", "debit"]:
                return create_error_response(
                    response,
                    "Transaction type must be 'credit' or 'debit'",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            query = query & (CreditTransaction.transaction_type == transaction_type)
        
        # Get transactions with pagination
        transactions = await CreditTransaction.find(query).sort(
            -CreditTransaction.created_at
        ).skip(skip).limit(limit).to_list()
        
        # Get total count
        total = await CreditTransaction.find(query).count()
        
        # Convert to response format
        transaction_responses = [
            CreditTransactionResponse(
                id=transaction.id,
                transaction_type=transaction.transaction_type,
                amount=transaction.amount,
                feature_type=transaction.feature_type.value if transaction.feature_type else None,
                credit_type=transaction.credit_type,
                description=transaction.description,
                balance_before=transaction.balance_before,
                balance_after=transaction.balance_after,
                created_at=transaction.created_at
            )
            for transaction in transactions
        ]
        
        transactions_list = CreditTransactionListResponse(
            transactions=transaction_responses,
            total=total
        )
        
        return create_success_response(
            response,
            data=transactions_list,
            message="Credit transactions retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            response,
            "Failed to retrieve transactions",
            error=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.post("/purchase", response_model=StandardResponse[dict])
async def purchase_credits(
    amount: int,
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Add credits via purchase"""
    request = AddCreditsRequest(
        amount=amount,
        credit_type="purchase",
        description=f"Purchased {amount} credits"
    )
    return await add_credits(request, response, current_user)

@router.post("/watch-ad", response_model=StandardResponse[dict])
async def watch_ad_credits(
    amount: int,  # Default 5 credits for watching an ad
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Add credits by watching ads"""
    request = AddCreditsRequest(
        amount=amount,
        credit_type="ad_watch",
        description=f"Earned {amount} credits by watching ads"
    )
    return await add_credits(request, response, current_user)

@router.get("/feature-costs", response_model=StandardResponse[dict])
async def get_feature_costs(response: Response):
    """Get the credit costs for all features"""
    feature_costs_data = {
        "feature_costs": {
            feature.value: cost for feature, cost in FEATURE_COSTS.items()
        }
    }
    
    return create_success_response(
        response,
        data=feature_costs_data,
        message="Feature costs retrieved successfully"
    )

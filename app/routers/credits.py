from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from ..models import User, UserCredits, CreditTransaction, FeatureType, FEATURE_COSTS
from ..schemas import (
    CreditBalanceResponse, 
    FeatureUsageRequest, 
    CreditTransactionResponse, 
    CreditTransactionListResponse,
    AddCreditsRequest
)
from ..auth import get_current_user

router = APIRouter(prefix="/credits", tags=["credits"])

async def get_or_create_user_credits(user_id: str) -> UserCredits:
    """Get user credits or create if doesn't exist"""
    user_credits = await UserCredits.find_one(UserCredits.user_id == user_id)
    if not user_credits:
        user_credits = UserCredits(user_id=user_id)
        await user_credits.save()
    return user_credits

@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(current_user: User = Depends(get_current_user)):
    """Get current user's credit balance"""
    try:
        user_credits = await get_or_create_user_credits(current_user.user_id)
        
        return CreditBalanceResponse(
            balance=user_credits.balance,
            total_earned=user_credits.total_earned,
            total_spent=user_credits.total_spent,
            updated_at=user_credits.updated_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve credit balance: {str(e)}"
        )

@router.post("/use-feature")
async def use_feature(
    request: FeatureUsageRequest,
    current_user: User = Depends(get_current_user)
):
    """Deduct credits for using a feature"""
    try:
        # Validate feature type
        try:
            feature_type = FeatureType(request.feature_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid feature type: {request.feature_type}"
            )
        
        # Get credit cost for the feature
        credit_cost = FEATURE_COSTS[feature_type]
        
        # Get user credits
        user_credits = await get_or_create_user_credits(current_user.user_id)
        
        # Check if user has enough credits
        if user_credits.balance < credit_cost:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Required: {credit_cost}, Available: {user_credits.balance}"
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
        
        return {
            "message": f"Successfully used {feature_type.value} feature",
            "credits_deducted": credit_cost,
            "remaining_balance": user_credits.balance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process feature usage: {str(e)}"
        )

@router.post("/add")
async def add_credits(
    request: AddCreditsRequest,
    current_user: User = Depends(get_current_user)
):
    """Add credits to user account (purchase or ad watch)"""
    try:
        if request.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credit amount must be positive"
            )
        
        # Validate credit type
        if request.credit_type not in ["purchase", "ad_watch"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credit type must be 'purchase' or 'ad_watch'"
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
        
        return {
            "message": "Credits added successfully",
            "credits_added": request.amount,
            "credit_type": request.credit_type,
            "new_balance": user_credits.balance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add credits: {str(e)}"
        )

@router.get("/transactions", response_model=CreditTransactionListResponse)
async def get_credit_transactions(
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
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transaction type must be 'credit' or 'debit'"
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
        
        return CreditTransactionListResponse(
            transactions=transaction_responses,
            total=total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transactions: {str(e)}"
        )

@router.post("/purchase")
async def purchase_credits(
    amount: int,
    current_user: User = Depends(get_current_user)
):
    """Add credits via purchase"""
    request = AddCreditsRequest(
        amount=amount,
        credit_type="purchase",
        description=f"Purchased {amount} credits"
    )
    return await add_credits(request, current_user)

@router.post("/watch-ad")
async def watch_ad_credits(
    amount: int = 5,  # Default 5 credits for watching an ad
    current_user: User = Depends(get_current_user)
):
    """Add credits by watching ads"""
    request = AddCreditsRequest(
        amount=amount,
        credit_type="ad_watch",
        description=f"Earned {amount} credits by watching ads"
    )
    return await add_credits(request, current_user)

@router.get("/feature-costs")
async def get_feature_costs():
    """Get the credit costs for all features"""
    return {
        "feature_costs": {
            feature.value: cost for feature, cost in FEATURE_COSTS.items()
        }
    }

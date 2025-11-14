from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from beanie import PydanticObjectId
from ..models import User, Conversation, Chat, UserCredits, CreditTransaction, FeatureType, FEATURE_COSTS
from ..schemas import ConversationRequest, ConversationResponse, ConversationListResponse, ChatResponse
from ..auth import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])

async def get_or_create_user_credits(user_id: str) -> UserCredits:
    """Get user credits or create if doesn't exist"""
    user_credits = await UserCredits.find_one(UserCredits.user_id == user_id)
    if not user_credits:
        user_credits = UserCredits(user_id=user_id)
        await user_credits.save()
    return user_credits

async def deduct_credits_for_chat(user_id: str) -> dict:
    """Deduct credits for chat feature usage"""
    feature_type = FeatureType.CHAT
    credit_cost = FEATURE_COSTS[feature_type]
    
    # Get user credits
    user_credits = await get_or_create_user_credits(user_id)
    
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
        user_id=user_id,
        transaction_type="debit",
        amount=credit_cost,
        feature_type=feature_type,
        description=f"Used {feature_type.value} feature",
        balance_before=balance_before,
        balance_after=user_credits.balance
    )
    await transaction.save()
    
    return {
        "credits_deducted": credit_cost,
        "remaining_balance": user_credits.balance
    }

@router.post("/", response_model=ConversationResponse)
async def create_or_update_conversation(
    request: ConversationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new conversation or add a chat to an existing conversation
    """
    try:
        # Deduct credits for chat usage
        credit_info = await deduct_credits_for_chat(current_user.user_id)
        
        # Create new chat entry
        new_chat = Chat(
            query=request.query,
            answer=request.answer,
            timestamp=datetime.utcnow()
        )
        
        if request.conversationId:
            # Update existing conversation
            try:
                conversation_id = PydanticObjectId(request.conversationId)
                conversation = await Conversation.find_one(
                    Conversation.id == conversation_id,
                    Conversation.user_id == current_user.user_id
                )
                
                if not conversation:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Conversation not found"
                    )
                
                # Add new chat to existing conversation
                conversation.chats.append(new_chat)
                conversation.updated_at = datetime.utcnow()
                await conversation.save()
                
            except Exception as e:
                if "not a valid ObjectId" in str(e):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid conversation ID format"
                    )
                raise e
        else:
            # Create new conversation
            conversation = Conversation(
                user_id=current_user.user_id,
                chats=[new_chat],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await conversation.save()
        
        # Convert to response format
        chat_responses = [
            ChatResponse(
                query=chat.query,
                answer=chat.answer,
                timestamp=chat.timestamp
            )
            for chat in conversation.chats
        ]
        
        return ConversationResponse(
            id=conversation.id,
            userId=conversation.user_id,
            chats=chat_responses,
            createdAt=conversation.created_at,
            updatedAt=conversation.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create/update conversation: {str(e)}"
        )

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific conversation by ID
    """
    try:
        conversation_obj_id = PydanticObjectId(conversation_id)
        conversation = await Conversation.find_one(
            Conversation.id == conversation_obj_id,
            Conversation.user_id == current_user.user_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Convert to response format
        chat_responses = [
            ChatResponse(
                query=chat.query,
                answer=chat.answer,
                timestamp=chat.timestamp
            )
            for chat in conversation.chats
        ]
        
        return ConversationResponse(
            id=conversation.id,
            userId=conversation.user_id,
            chats=chat_responses,
            createdAt=conversation.created_at,
            updatedAt=conversation.updated_at
        )
        
    except Exception as e:
        if "not a valid ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation ID format"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )

@router.get("/", response_model=ConversationListResponse)
async def get_user_conversations(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Get all conversations for the current user with pagination
    """
    try:
        # Get conversations with pagination, sorted by most recent first
        conversations = await Conversation.find(
            Conversation.user_id == current_user.user_id
        ).sort(-Conversation.created_at).skip(skip).limit(limit).to_list()
        
        # Get total count
        total = await Conversation.find(
            Conversation.user_id == current_user.user_id
        ).count()
        
        # Convert to response format
        conversation_responses = []
        for conversation in conversations:
            chat_responses = [
                ChatResponse(
                    query=chat.query,
                    answer=chat.answer,
                    timestamp=chat.timestamp
                )
                for chat in conversation.chats
            ]
            
            conversation_responses.append(ConversationResponse(
                id=conversation.id,
                userId=conversation.user_id,
                chats=chat_responses,
                createdAt=conversation.created_at,
                updatedAt=conversation.updated_at
            ))
        
        return ConversationListResponse(
            conversations=conversation_responses,
            total=total
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversations: {str(e)}"
        )

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific conversation
    """
    try:
        conversation_obj_id = PydanticObjectId(conversation_id)
        conversation = await Conversation.find_one(
            Conversation.id == conversation_obj_id,
            Conversation.user_id == current_user.user_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        await conversation.delete()
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        if "not a valid ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation ID format"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )

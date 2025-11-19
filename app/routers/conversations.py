from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List, Optional
from datetime import datetime
from beanie import PydanticObjectId
from ..models import User, Conversation, Chat
from ..schemas import ConversationRequest, ConversationResponse, ConversationListResponse, ChatResponse, StandardResponse
from ..auth import get_current_user
from ..response_utils import create_success_response, create_error_response, get_success_status_code

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=StandardResponse[ConversationResponse])
async def create_or_update_conversation(
    request: ConversationRequest,
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new conversation or add a chat to an existing conversation
    """
    try:
        # Create new chat entry
        new_chat = Chat(
            query=request.query,
            answer=request.answer,
            timestamp=datetime.utcnow()
        )
        
        is_new_conversation = False
        
        if request.conversationId:
            # Update existing conversation
            try:
                conversation_id = PydanticObjectId(request.conversationId)
                conversation = await Conversation.find_one(
                    Conversation.id == conversation_id,
                    Conversation.user_id == current_user.user_id
                )
                
                if not conversation:
                    return create_error_response(
                        response,
                        "Conversation not found",
                        status_code=status.HTTP_404_NOT_FOUND
                    )
                
                # Add new chat to existing conversation
                conversation.chats.append(new_chat)
                conversation.updated_at = datetime.utcnow()
                await conversation.save()
                
            except Exception as e:
                if "not a valid ObjectId" in str(e):
                    return create_error_response(
                        response,
                        "Invalid conversation ID format",
                        status_code=status.HTTP_400_BAD_REQUEST
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
            is_new_conversation = True
        
        # Convert to response format
        chat_responses = [
            ChatResponse(
                query=chat.query,
                answer=chat.answer,
                timestamp=chat.timestamp
            )
            for chat in conversation.chats
        ]
        
        conversation_response = ConversationResponse(
            id=conversation.id,
            userId=conversation.user_id,
            chats=chat_responses,
            createdAt=conversation.created_at,
            updatedAt=conversation.updated_at
        )
        
        return create_success_response(
            response,
            data=conversation_response,
            message="Conversation created successfully" if is_new_conversation else "Chat added to conversation successfully",
            status_code=get_success_status_code(is_new_conversation)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response(
            response,
            "Failed to create/update conversation",
            error=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/{conversation_id}", response_model=StandardResponse[ConversationResponse])
async def get_conversation(
    conversation_id: str,
    response: Response,
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
            return create_error_response(
                response,
                "Conversation not found",
                status_code=status.HTTP_404_NOT_FOUND
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
        
        conversation_response = ConversationResponse(
            id=conversation.id,
            userId=conversation.user_id,
            chats=chat_responses,
            createdAt=conversation.created_at,
            updatedAt=conversation.updated_at
        )
        
        return create_success_response(
            response,
            data=conversation_response,
            message="Conversation retrieved successfully"
        )
        
    except Exception as e:
        if "not a valid ObjectId" in str(e):
            return create_error_response(
                response,
                "Invalid conversation ID format",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return create_error_response(
            response,
            "Failed to retrieve conversation",
            error=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/", response_model=StandardResponse[ConversationListResponse])
async def get_user_conversations(
    skip: int = 0,
    limit: int = 10,
    response: Response = None,
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
        
        conversations_list = ConversationListResponse(
            conversations=conversation_responses,
            total=total
        )
        
        return create_success_response(
            response,
            data=conversations_list,
            message="Conversations retrieved successfully"
        )
        
    except Exception as e:
        return create_error_response(
            response,
            "Failed to retrieve conversations",
            error=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.delete("/{conversation_id}", response_model=StandardResponse[dict])
async def delete_conversation(
    conversation_id: str,
    response: Response,
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
            return create_error_response(
                response,
                "Conversation not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        await conversation.delete()
        
        return create_success_response(
            response,
            data={"deleted": True},
            message="Conversation deleted successfully"
        )
        
    except Exception as e:
        if "not a valid ObjectId" in str(e):
            return create_error_response(
                response,
                "Invalid conversation ID format",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return create_error_response(
            response,
            "Failed to delete conversation",
            error=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

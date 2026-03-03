from __future__ import annotations

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class Location(BaseModel):
    """Location information for context-aware responses (only zip and country)"""
    zip: Optional[str] = Field(None, description="ZIP or postal code")
    country: Optional[str] = Field("US", description="Country code")


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    session_id: str = Field(..., description="Unique session identifier for conversation context")
    message: str = Field(..., description="User's question or message", min_length=1)
    location: Optional[Location] = Field(None, description="Location context for accurate guidance")
    user_type: Optional[str] = Field(None, description="User type (Architect or Structure Engineer)")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="Chatbot's response")
    session_id: str = Field(..., description="Session identifier")


class SessionHistory(BaseModel):
    """Model for session history"""
    session_id: str = Field(..., description="Session identifier")
    history: List[Dict[str, Any]] = Field(..., description="Conversation history")


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Specific error code")


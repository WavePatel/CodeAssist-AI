from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI

from . import config, schemas

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI's API"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.settings.openai_api_key)
        self.model = config.settings.openai_model
    
    def _build_system_prompt(self, location: Optional[schemas.Location] = None) -> str:
        """Build the system prompt for the chatbot"""
        location_context = ""
        if location:
            location_parts = []
            if location.zip:
                location_parts.append(location.zip)
            if location.country and location.country != "US":
                location_parts.append(location.country)
            if location_parts:
                location_context = f" The user is located in: {', '.join(location_parts)}."
        
        return f"""You are a professional home design and building code consultant chatbot. You provide accurate, helpful guidance on:

- Home design and renovation projects
- Building codes and regulations
- Construction best practices
- Permits and zoning requirements
- Safety considerations
- Material recommendations
- Cost estimates and budgeting

{location_context}

Guidelines:
1. Always provide practical, actionable advice
2. Emphasize safety and code compliance
3. Suggest consulting local authorities for specific regulations
4. Be clear about when professional help is needed
5. Provide step-by-step guidance when appropriate
6. Use plain English, avoid overly technical jargon
7. If you don't know something specific, say so and suggest where to find the information

Respond in a helpful, professional tone. Keep responses concise but comprehensive."""
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format conversation history for OpenAI API"""
        formatted_history = []
        
        for message in history:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            # Add location context to user messages if available
            if role == "user" and "location" in message and message["location"]:
                location = message["location"]
                if isinstance(location, dict):
                    location_parts = []
                    if location.get("zip"):
                        location_parts.append(location["zip"])
                    if location.get("country") and location["country"] != "US":
                        location_parts.append(location["country"])
                    if location_parts:
                        content = f"[Location: {', '.join(location_parts)}] {content}"
            
            formatted_history.append({
                "role": role,
                "content": content
            })
        
        return formatted_history
    
    async def generate_response(
        self, 
        conversation_history: List[Dict[str, Any]], 
        location: Optional[schemas.Location] = None
    ) -> str:
        """
        Generate a response using OpenAI's API
        """
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(location)
            
            # Format conversation history
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self._format_conversation_history(conversation_history))
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            if not response.choices or not response.choices[0].message:
                raise Exception("No response generated from OpenAI")
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test the connection to OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return response.choices is not None
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {str(e)}")
            return False


from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

import google.generativeai as genai

from . import config, schemas

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Google's Gemini API"""
    
    def __init__(self):
        # decide between demo and real mode based on key
        if config.settings.gemini_api_key == "demo_key_placeholder":
            self.model = None
            self.demo_mode = True
        else:
            genai.configure(api_key=config.settings.gemini_api_key)
            # allow model override via environment variable
            model_name = config.settings.gemini_model
            try:
                self.model = genai.GenerativeModel(model_name)
            except Exception as e:
                # if the model cannot be instantiated, log a clear warning
                logger.error(f"Failed to initialize Gemini model '{model_name}': {e}")
                # fall back into demo mode so the service still starts
                self.model = None
                self.demo_mode = True
                return

            self.demo_mode = False
    
    def _build_system_prompt(self, location: Optional[schemas.Location] = None, user_type: Optional[str] = None) -> str:
        """Build the system prompt for the chatbot, including user type"""
        location_context = ""
        if location:
            location_parts = []
            if location.zip:
                location_parts.append(location.zip)
            if location.country and location.country != "US":
                location_parts.append(location.country)
            if location_parts:
                location_context = f" The user is located in: {', '.join(location_parts)}."

        user_type_context = ""
        if user_type:
            user_type_context = f" The user is a {user_type}."

        return f"""You are a professional home design and building code consultant chatbot. You provide accurate, helpful guidance on:

- Home design and renovation projects
- Building codes and regulations
- Construction best practices
- Permits and zoning requirements
- Safety considerations
- Material recommendations
- Cost estimates and budgeting

{location_context}{user_type_context}

Guidelines:
1. Always provide practical, actionable advice
2. Emphasize safety and code compliance
3. Suggest consulting local authorities for specific regulations
4. Be clear about when professional help is needed
5. Provide step-by-step guidance when appropriate
6. Use plain English, avoid overly technical jargon
7. If you don't know something specific, say so and suggest where to find the information

CRITICAL: Your response MUST be under 500 words. Provide ONLY the most essential information. Use bullet points and be extremely concise. Stop at 500 words maximum.

**Formatting requirements:**
- **Return your answer in Markdown**. Use headings, bullet points ("-" or "*"), and numbered lists where appropriate.
- Keep paragraphs short; separate them with a blank line.
- Do not include any extraneous preamble such as "Sure," "Here is what you requested," or other conversational fluff.

Respond in a helpful, professional tone. Keep responses concise but comprehensive."""
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for Gemini API"""
        formatted_messages = []
        
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
            
            if role == "user":
                formatted_messages.append(f"User: {content}")
            elif role == "assistant":
                formatted_messages.append(f"Assistant: {content}")
        
        return "\n".join(formatted_messages)
    
    async def generate_response(
        self, 
        conversation_history: List[Dict[str, Any]], 
        location: Optional[schemas.Location] = None
    ) -> str:
        """
        Generate a response using Gemini's API
        """
        try:
            # Demo mode responses
            if self.demo_mode:
                return self._get_demo_response(conversation_history, location)
            
            # Get user_type from latest user message
            user_type = None
            for msg in reversed(conversation_history):
                if msg.get("role") == "user" and msg.get("user_type"):
                    user_type = msg["user_type"]
                    break
            # Build system prompt
            system_prompt = self._build_system_prompt(location, user_type)
            
            # Format conversation history
            conversation_text = self._format_conversation_history(conversation_history)
            
            # Create the full prompt with strict word limit
            full_prompt = f"{system_prompt}\n\nConversation History:\n{conversation_text}\n\nAssistant: Remember, your response MUST be under 500 words. Be extremely concise."
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            if not response.text:
                raise Exception("No response generated from Gemini")
            
            # Limit response to 500 words - more aggressive approach
            response_text = response.text.strip()
            words = response_text.split()
            
            print(f"Original response: {len(words)} words")
            
            if len(words) > 500:
                # Take first 500 words and add ellipsis
                response_text = ' '.join(words[:500]) + "..."
                print(f"Response truncated from {len(words)} to 500 words")
            
            # Final word count check
            final_words = response_text.split()
            print(f"Final response: {len(final_words)} words")
            
            # post-process formatting for readability
            response_text = self._postprocess_response(response_text)
            return response_text
            
        except Exception as e:
            # Log the original exception
            logger.error(f"Error generating Gemini response: {str(e)}")
            msg = str(e)
            lowered = msg.lower()
            # model not found errors are common when the default changes
            if "404" in msg and "models/" in msg:
                raise Exception(
                    f"Configured Gemini model '{config.settings.gemini_model}' not found or unsupported. "
                    "Update GEMINI_MODEL in your .env or use a valid model name. "
                    "Call ListModels to see available options."
                )
            # Detect common API key/authentication issues and give user-friendly guidance
            if "401" in msg or "api key" in lowered or "unauthorized" in lowered:
                raise Exception("Gemini API key invalid or unauthorized. Please verify your GEMINI_API_KEY in your environment.")
            # Otherwise propagate general failure
            raise Exception(f"Failed to generate response: {msg}")
    
    def _get_demo_response(self, conversation_history: List[Dict[str, Any]], location: Optional[schemas.Location] = None) -> str:
        """Generate demo responses when API key is not available"""
        last_message = conversation_history[-1].get("content", "").lower()
        
        # Handle location from conversation history if not passed directly
        if not location and conversation_history:
            location_data = conversation_history[-1].get("location")
            if location_data and isinstance(location_data, dict):
                location = schemas.Location(**location_data)
        
        demo_responses = {
            "hello": "Hello! I'm your home design assistant. I can help with construction, permits, and design questions. To get real AI responses, please add your Gemini API key.",
            "help": "I can help with home design, building codes, permits, and construction questions. For full functionality, please set up your Gemini API key.",
            "permit": "For permits, you'll need to check with your local building department. Requirements vary by location. I can provide general guidance, but always verify with local authorities.",
            "construction": "Construction projects require careful planning. Consider safety, permits, materials, and local codes. For specific projects, consult with licensed contractors.",
            "design": "Home design involves layout, materials, lighting, and functionality. Consider your needs, budget, and local building codes.",
            "cost": "Costs vary greatly by project type, location, and materials. Get multiple quotes from licensed contractors for accurate estimates.",
            "code": "Building codes ensure safety and compliance. They vary by location and project type. Always check with your local building department."
        }
        
        for keyword, response in demo_responses.items():
            if keyword in last_message:
                return response
        
        return "I'm here to help with home design and construction questions! For full AI-powered responses, please add your Gemini API key to the .env file. In demo mode, I can provide general guidance on permits, construction, and design topics."
    
    async def test_connection(self) -> bool:
        """Test the connection to Gemini API"""
        try:
            response = self.model.generate_content("Hello")
            return response.text is not None
        except Exception as e:
            logger.error(f"Gemini connection test failed: {str(e)}")
            return False

    def _postprocess_response(self, text: str) -> str:
        """Clean up and normalize the model response for better formatting"""
        import re

        # collapse multiple spaces
        cleaned = re.sub(r"[ \t]+", " ", text).strip()

        lines = cleaned.splitlines()
        formatted_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                # preserve blank lines
                formatted_lines.append("")
                continue

            # normalize bullets starting with '*' to '-' for consistency
            if stripped.startswith("*"):
                formatted_lines.append("- " + stripped.lstrip("*").strip())
            else:
                formatted_lines.append(stripped)

        return "\n".join(formatted_lines)


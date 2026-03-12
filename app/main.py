from __future__ import annotations

import logging
from typing import Dict, Any

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
except ModuleNotFoundError as e:
    missing = getattr(e, 'name', str(e))
    raise RuntimeError(
        f"Missing required package '{missing}'. Install dependencies with: python -m pip install -r requirements.txt"
    ) from e

from . import config, schemas, context, gemini_client

# Configure logging
logging.basicConfig(level=getattr(logging, config.settings.log_level.upper()))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Home Design & Building Code Chatbot",
    description="Professional, location-aware chatbot for home design, construction, and building code questions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize context manager
context_manager = context.ContextManager()

# Initialize Gemini client
gemini_client_instance = gemini_client.GeminiClient()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse('static/index.html')


@app.get("/about")
async def read_about():
    """Serve the About Us page"""
    return FileResponse('static/about.html')


@app.get("/careers")
async def read_careers():
    """Serve the Careers page"""
    return FileResponse('static/careers.html')


@app.get("/contact")
async def read_contact():
    """Serve the Contact Us page"""
    return FileResponse('static/contact.html')


@app.get("/all-rights")
async def read_all_rights():
    """Serve the all rights page"""
    return FileResponse('static/all-rights.html')


@app.get("/cookies-policy")
async def read_cookies_policy():
    """Serve the cookies policy page"""
    return FileResponse('static/cookies-policy.html')


@app.get("/privacy-statements")
async def read_privacy_statements():
    """Serve the privacy statements page"""
    return FileResponse('static/privacy-statements.html')


@app.get("/terms-of-use")
async def read_terms_of_use():
    """Serve the terms of use page"""
    return FileResponse('static/terms-of-use.html')

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    gemini_status = None
    if not gemini_client_instance.demo_mode:
        try:
            gemini_status = await gemini_client_instance.test_connection()
        except Exception:
            gemini_status = False
    return {
        "status": "healthy",
        "message": "Chatbot API is running",
        "gemini_ok": gemini_status,
        "demo_mode": gemini_client_instance.demo_mode,
    }


@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(request: schemas.ChatRequest):
    """
    Main chat endpoint for home design and building code questions
    """
    try:
        # Get conversation context
        conversation_history = context_manager.get_context(request.session_id)
        
        # Add the new message to context
        conversation_history.append({
            "role": "user",
            "content": request.message,
            "location": request.location.dict() if request.location else None,
            "user_type": request.user_type
        })
        
        # Generate response using Gemini
        response = await gemini_client_instance.generate_response(
            conversation_history=conversation_history,
            location=request.location
        )
        
        # Add assistant response to context
        conversation_history.append({
            "role": "assistant", 
            "content": response
        })
        
        # Convert any Location objects to dicts before saving
        for message in conversation_history:
            if "location" in message and message["location"] is not None:
                if hasattr(message["location"], 'dict'):
                    message["location"] = message["location"].dict()
        
        # Save updated context
        context_manager.save_context(request.session_id, conversation_history)
        
        return schemas.ChatResponse(
            response=response,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session"""
    try:
        history = context_manager.get_context(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving session history: {str(e)}")


@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history for a session"""
    try:
        context_manager.clear_context(session_id)
        return {"message": f"Session {session_id} cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


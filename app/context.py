from __future__ import annotations

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages conversation context and session storage"""
    
    def __init__(self, storage_dir: str = "sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self._memory_cache: Dict[str, List[Dict[str, Any]]] = {}
    
    def get_context(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation context for a session
        Returns empty list if no context exists
        """
        try:
            # Check memory cache first
            if session_id in self._memory_cache:
                return self._memory_cache[session_id].copy()
            
            # Load from file
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    context_data = json.load(f)
                    self._memory_cache[session_id] = context_data
                    return context_data.copy()
            
            # Return empty context for new session
            return []
            
        except Exception as e:
            logger.error(f"Error loading context for session {session_id}: {str(e)}")
            return []
    
    def save_context(self, session_id: str, context: List[Dict[str, Any]]) -> None:
        """
        Save conversation context for a session
        """
        try:
            # Update memory cache
            self._memory_cache[session_id] = context.copy()
            
            # Save to file
            session_file = self.storage_dir / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(context, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving context for session {session_id}: {str(e)}")
            raise
    
    def clear_context(self, session_id: str) -> None:
        """
        Clear conversation context for a session
        """
        try:
            # Remove from memory cache
            if session_id in self._memory_cache:
                del self._memory_cache[session_id]
            
            # Remove file
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                
        except Exception as e:
            logger.error(f"Error clearing context for session {session_id}: {str(e)}")
            raise
    
    def get_all_sessions(self) -> List[str]:
        """
        Get list of all active session IDs
        """
        try:
            session_files = list(self.storage_dir.glob("*.json"))
            return [f.stem for f in session_files]
        except Exception as e:
            logger.error(f"Error getting session list: {str(e)}")
            return []
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old session files
        Returns number of sessions cleaned up
        """
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0
        
        try:
            for session_file in self.storage_dir.glob("*.json"):
                if current_time - session_file.stat().st_mtime > max_age_seconds:
                    session_id = session_file.stem
                    self.clear_context(session_id)
                    cleaned_count += 1
                    
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")
            
        return cleaned_count


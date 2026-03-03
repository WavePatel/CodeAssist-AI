from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "info")

    @staticmethod
    def from_env() -> "Settings":
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            # For demo purposes, use a placeholder key
            print("WARNING: GEMINI_API_KEY not found. Using demo mode.")
            api_key = "demo_key_placeholder"
        return Settings(gemini_api_key=api_key)


settings = Settings.from_env()



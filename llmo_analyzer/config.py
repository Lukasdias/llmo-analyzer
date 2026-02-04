"""
LLMO Analyzer - Configuration Module
Manages environment variables and application settings.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env and .env.local files
# .env.local takes precedence (common pattern for local secrets)
load_dotenv()
load_dotenv(".env.local", override=True)


class Config:
    """Application configuration with environment variable support."""
    
    # Groq API Settings
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Content Settings
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "10000"))
    MAX_TOKENS_FOR_AI: int = 4000  # Maximum tokens to send to Groq
    
    # Scoring Weights (must sum to 1.0)
    WEIGHT_READABILITY: float = 0.25
    WEIGHT_STRUCTURE: float = 0.25
    WEIGHT_TECHNICAL: float = 0.20
    WEIGHT_AI_ENTITY: float = 0.10
    WEIGHT_AI_EXTRACTABILITY: float = 0.10
    WEIGHT_AI_CITATION: float = 0.10
    
    # Readability Thresholds
    READABILITY_EXCELLENT: float = 60.0  # Flesch Reading Ease
    READABILITY_GOOD: float = 50.0
    READABILITY_FAIR: float = 30.0
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not cls.GROQ_API_KEY or cls.GROQ_API_KEY == "your_groq_api_key_here":
            errors.append("GROQ_API_KEY is not set. Please set it in your environment or .env file.")
        
        total_weight = (
            cls.WEIGHT_READABILITY + cls.WEIGHT_STRUCTURE + cls.WEIGHT_TECHNICAL +
            cls.WEIGHT_AI_ENTITY + cls.WEIGHT_AI_EXTRACTABILITY + cls.WEIGHT_AI_CITATION
        )
        if abs(total_weight - 1.0) > 0.001:
            errors.append(f"Scoring weights must sum to 1.0, current sum: {total_weight}")
        
        return errors
    
    @classmethod
    def is_valid(cls) -> bool:
        """Check if configuration is valid."""
        return len(cls.validate()) == 0

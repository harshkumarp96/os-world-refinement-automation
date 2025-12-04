"""
Configuration settings for the LangChain Screenshot Validator
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables - use override to ensure .env values are used
load_dotenv(override=True)

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    max_tokens: int = int(os.getenv("MAX_TOKENS", "4096"))
    temperature: float = float(os.getenv("TEMPERATURE", "0"))
    
    # Directory paths
    project_root: Path = Path(__file__).parent.parent
    input_data_dir: Path = project_root / os.getenv("INPUT_DATA_DIR", "Input Data")
    # Legacy paths for backward compatibility
    input_json_dir: Path = project_root / os.getenv("INPUT_JSON_DIR", "Input Data/Json")
    screenshots_dir: Path = project_root / os.getenv("SCREENSHOTS_DIR", "Input Data/Screenshots")
    output_dir: Path = project_root / os.getenv("OUTPUT_DIR", "output")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()

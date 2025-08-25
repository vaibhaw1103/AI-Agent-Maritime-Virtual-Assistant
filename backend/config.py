"""
Production-ready configuration for Maritime Assistant
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://maritime_user:maritime_pass@localhost:5432/maritime_assistant_db")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "maritime-assistant-secret-key-2025-production")
    
    # AI Providers (priority order)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
    
    # Azure Services
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    # Weather APIs
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    NOAA_API_KEY = os.getenv("NOAA_API_KEY")
    
    # Production Settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    @property
    def ai_provider(self):
        """Determine which AI provider to use based on available keys"""
        if self.GROQ_API_KEY:
            return "groq"
        elif self.OPENAI_API_KEY:
            return "openai"
        elif self.HUGGINGFACE_API_KEY:
            return "huggingface"
        elif self.OPENROUTER_API_KEY:
            return "openrouter"
        elif self.TOGETHER_API_KEY:
            return "together"
        elif self.AZURE_OPENAI_KEY and self.AZURE_OPENAI_ENDPOINT:
            return "azure"
        else:
            return "mock"
    
    @property
    def weather_provider(self):
        """Determine weather data source"""
        if self.OPENWEATHER_API_KEY:
            return "openweather"
        elif self.NOAA_API_KEY:
            return "noaa"
        else:
            return "mock"

config = Config()

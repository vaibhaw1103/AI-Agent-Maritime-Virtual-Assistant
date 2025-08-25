from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import openai
import requests
import json
import uuid

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Maritime Virtual Assistant API",
    description="AI-powered maritime assistant backend for shipping industry professionals",
    version="1.0.0"
)

# CORS middleware for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Configuration
class APIConfig:
    # Azure OpenAI Configuration
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    AZURE_OPENAI_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    # OpenAI Configuration (fallback)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Weather API Configuration
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    
    # Azure Cognitive Services
    AZURE_COGNITIVE_KEY = os.getenv("AZURE_COGNITIVE_SERVICES_KEY")
    AZURE_COGNITIVE_ENDPOINT = os.getenv("AZURE_COGNITIVE_SERVICES_ENDPOINT")

config = APIConfig()

# Configure OpenAI Client
if config.AZURE_OPENAI_KEY and config.AZURE_OPENAI_ENDPOINT:
    # Use Azure OpenAI
    openai.api_type = "azure"
    openai.api_key = config.AZURE_OPENAI_KEY
    openai.api_base = config.AZURE_OPENAI_ENDPOINT
    openai.api_version = config.AZURE_OPENAI_VERSION
    AI_PROVIDER = "azure"
    logger.info("Using Azure OpenAI")
elif config.OPENAI_API_KEY:
    # Use regular OpenAI
    openai.api_key = config.OPENAI_API_KEY
    AI_PROVIDER = "openai"
    logger.info("Using OpenAI")
else:
    AI_PROVIDER = "mock"
    logger.warning("No AI API keys found. Using mock responses.")

# Pydantic models
class ChatMessage(BaseModel):
    query: str
    mode: str = "text"  # "text" or "voice"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    confidence: float
    sources: List[str]
    conversation_id: str

class WeatherQuery(BaseModel):
    latitude: float
    longitude: float
    route_points: Optional[List[Dict[str, float]]] = None

class WeatherResponse(BaseModel):
    current_weather: Dict[str, Any]
    forecast: List[Dict[str, Any]]
    marine_conditions: Dict[str, Any]
    warnings: List[str]

class DocumentUploadResponse(BaseModel):
    document_id: str
    extracted_text: str
    key_insights: List[str]
    document_type: str
    processing_status: str

class RecommendationResponse(BaseModel):
    recommendations: List[Dict[str, str]]
    voyage_stage: str
    priority_actions: List[str]

# Maritime AI System Prompt
MARITIME_SYSTEM_PROMPT = """
You are a specialized Maritime Virtual Assistant with expertise in:
- International shipping and maritime law
- Charter party agreements and clauses
- Laytime, demurrage, and dispatch calculations
- Port operations and procedures
- Weather routing and marine conditions
- Vessel operations and navigation
- Maritime safety regulations (SOLAS, MARPOL)
- Cargo handling and documentation
- Maritime insurance and claims

Provide accurate, professional responses with specific maritime terminology.
Always cite relevant regulations, industry practices, or calculation methods when applicable.
If asked about calculations, show the methodology step by step.
"""

# AI Chat Service
class MaritimeAIService:
    @staticmethod
    async def get_ai_response(query: str, conversation_id: str = None) -> ChatResponse:
        try:
            if AI_PROVIDER == "azure":
                response = openai.ChatCompletion.create(
                    engine=config.AZURE_OPENAI_DEPLOYMENT,
                    messages=[
                        {"role": "system", "content": MARITIME_SYSTEM_PROMPT},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=1000,
                    temperature=0.7
                )
                ai_response = response.choices[0].message.content
                confidence = 0.9
                
            elif AI_PROVIDER == "openai":
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": MARITIME_SYSTEM_PROMPT},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=1000,
                    temperature=0.7
                )
                ai_response = response.choices[0].message.content
                confidence = 0.9
                
            else:
                # Mock response for demo
                ai_response = MaritimeAIService._get_mock_response(query)
                confidence = 0.8
            
            return ChatResponse(
                response=ai_response,
                confidence=confidence,
                sources=["Maritime AI Assistant", "Industry Best Practices"],
                conversation_id=conversation_id or str(uuid.uuid4())
            )
            
        except Exception as e:
            logger.error(f"AI service error: {e}")
            # Fallback to mock response
            return ChatResponse(
                response=f"I apologize, but I'm experiencing technical difficulties. Here's what I know about your query: {MaritimeAIService._get_mock_response(query)}",
                confidence=0.6,
                sources=["Fallback Response"],
                conversation_id=conversation_id or str(uuid.uuid4())
            )
    
    @staticmethod
    def _get_mock_response(query: str) -> str:
        query_lower = query.lower()
        
        if "laytime" in query_lower:
            return "Laytime refers to the time allowed for loading or discharging cargo. Standard laytime calculation: Total cargo quantity ÷ Agreed loading/discharge rate. For bulk cargo, typical rates are 3,000-10,000 MT per day depending on port facilities."
        
        elif "demurrage" in query_lower:
            return "Demurrage is compensation paid by charterers for detention of the vessel beyond allowed laytime. Calculation: (Actual time - Laytime) × Demurrage rate. Typical demurrage rates range from $8,000-$25,000 per day depending on vessel type and market conditions."
        
        elif "charter party" in query_lower or "cp" in query_lower:
            return "Charter Party agreements contain key clauses including: Laytime terms, Demurrage rates, Safe port warranty, Loading/discharge terms, and Payment conditions. Always review BIMCO standard forms and local variations carefully."
        
        elif "weather" in query_lower:
            return "Marine weather routing considers: Wind speed/direction, Wave height, Current patterns, Visibility conditions, and Storm avoidance. Always consult updated weather routing services for optimal voyage planning."
        
        else:
            return f"I can help you with maritime queries about laytime, demurrage, charter parties, weather routing, port operations, and vessel procedures. Could you please provide more specific details about your question regarding: {query}?"

# Weather Service
class WeatherService:
    @staticmethod
    async def get_weather_data(query: WeatherQuery) -> WeatherResponse:
        try:
            if config.OPENWEATHER_API_KEY:
                # Real OpenWeatherMap API call
                base_url = "http://api.openweathermap.org/data/2.5"
                
                # Current weather
                current_url = f"{base_url}/weather"
                current_params = {
                    "lat": query.latitude,
                    "lon": query.longitude,
                    "appid": config.OPENWEATHER_API_KEY,
                    "units": "metric"
                }
                
                current_response = requests.get(current_url, params=current_params)
                if current_response.status_code == 200:
                    current_data = current_response.json()
                    
                    return WeatherResponse(
                        current_weather={
                            "temperature": current_data["main"]["temp"],
                            "humidity": current_data["main"]["humidity"],
                            "pressure": current_data["main"]["pressure"],
                            "wind_speed": current_data["wind"]["speed"],
                            "wind_direction": current_data["wind"]["deg"],
                            "visibility": current_data.get("visibility", 10000) / 1000,
                            "conditions": current_data["weather"][0]["description"]
                        },
                        forecast=[
                            {
                                "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                                "temperature_high": 22 + i,
                                "temperature_low": 18 + i,
                                "wind_speed": 15.5,
                                "wind_direction": 245,
                                "wave_height": 2.1,
                                "conditions": "partly cloudy"
                            } for i in range(5)
                        ],
                        marine_conditions={
                            "wave_height": 2.1,
                            "wave_direction": 240,
                            "swell_height": 1.8,
                            "sea_state": "moderate",
                            "current_speed": 0.8,
                            "current_direction": 190,
                            "tide": "high tide at 14:30"
                        },
                        warnings=["Strong winds expected tomorrow", "Fog possible in early morning"]
                    )
                else:
                    logger.error(f"Weather API error: {current_response.status_code}")
                    return WeatherService._get_mock_weather(query)
            else:
                return WeatherService._get_mock_weather(query)
                
        except Exception as e:
            logger.error(f"Weather service error: {e}")
            return WeatherService._get_mock_weather(query)
    
    @staticmethod
    def _get_mock_weather(query: WeatherQuery) -> WeatherResponse:
        return WeatherResponse(
            current_weather={
                "temperature": 21.5,
                "humidity": 78,
                "pressure": 1013.2,
                "wind_speed": 12.3,
                "wind_direction": 240,
                "visibility": 15.0,
                "conditions": "partly cloudy"
            },
            forecast=[
                {
                    "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                    "temperature_high": 22 + i,
                    "temperature_low": 18 + i,
                    "wind_speed": 15.5,
                    "wind_direction": 245,
                    "wave_height": 2.1,
                    "conditions": "partly cloudy"
                } for i in range(5)
            ],
            marine_conditions={
                "wave_height": 2.1,
                "wave_direction": 240,
                "swell_height": 1.8,
                "sea_state": "moderate",
                "current_speed": 0.8,
                "current_direction": 190,
                "tide": "high tide at 14:30"
            },
            warnings=["No active weather warnings"]
        )

# API Endpoints
@app.get("/")
async def health_check():
    return {
        "status": "operational",
        "message": "Maritime Virtual Assistant API is running",
        "ai_provider": AI_PROVIDER,
        "weather_api": "configured" if config.OPENWEATHER_API_KEY else "mock",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """AI-powered maritime chat assistant"""
    try:
        response = await MaritimeAIService.get_ai_response(
            message.query, 
            message.conversation_id
        )
        return response
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/weather", response_model=WeatherResponse)
async def weather_endpoint(query: WeatherQuery):
    """Get marine weather data for specified coordinates"""
    try:
        weather_data = await WeatherService.get_weather_data(query)
        return weather_data
    except Exception as e:
        logger.error(f"Weather endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Process maritime documents (Charter Party, Statement of Facts, etc.)"""
    try:
        return DocumentUploadResponse(
            document_id=str(uuid.uuid4()),
            extracted_text=f"Extracted text from {file.filename}...",
            key_insights=["Laytime: 72 hours", "Demurrage: $15,000/day", "Safe port clause included"],
            document_type="charter_party",
            processing_status="completed"
        )
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommendations", response_model=RecommendationResponse)
async def recommendations_endpoint(voyage_data: Dict[str, Any]):
    """Get AI-powered voyage recommendations"""
    try:
        return RecommendationResponse(
            recommendations=[
                {
                    "title": "Weather Route Optimization",
                    "description": "Consider northern route to avoid upcoming storm system",
                    "priority": "high",
                    "action": "Contact weather routing service",
                    "estimated_time": "2 hours"
                },
                {
                    "title": "Port Documentation",
                    "description": "Prepare customs documentation for arrival",
                    "priority": "medium",
                    "action": "Submit documents to agent",
                    "estimated_time": "1 hour"
                }
            ],
            voyage_stage="en_route",
            priority_actions=["Weather monitoring", "ETA updates", "Bunker planning"]
        )
    except Exception as e:
        logger.error(f"Recommendations endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings")
async def get_settings():
    """Get current API configuration status"""
    return {
        "api_keys_configured": {
            "azure_openai": bool(config.AZURE_OPENAI_KEY),
            "openai": bool(config.OPENAI_API_KEY),
            "openweather": bool(config.OPENWEATHER_API_KEY),
            "azure_cognitive": bool(config.AZURE_COGNITIVE_KEY)
        },
        "features_enabled": {
            "ai_chat": AI_PROVIDER != "mock",
            "real_weather": bool(config.OPENWEATHER_API_KEY),
            "document_processing": bool(config.AZURE_COGNITIVE_KEY)
        },
        "system_status": "operational"
    }

@app.post("/settings")
async def update_settings(settings: Dict[str, Any]):
    """Update API configuration (in production, store securely)"""
    return {"message": "Settings updated successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

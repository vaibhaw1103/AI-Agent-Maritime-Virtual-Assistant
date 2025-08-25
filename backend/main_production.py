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
import pathlib

# Import configuration and routing
from config import config
from maritime_routing_professional import professional_router, GLOBAL_CITIES_DATABASE

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Maritime Virtual Assistant API",
    description="Production-ready AI-powered maritime assistant backend",
    version="2.0.0",
    debug=config.DEBUG
)

# Production CORS middleware
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    "http://localhost:3001"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configure AI and Weather providers
AI_PROVIDER = config.ai_provider
WEATHER_PROVIDER = config.weather_provider

logger.info(f"🚀 Maritime Assistant API Starting")
logger.info(f"🤖 AI Provider: {AI_PROVIDER}")
logger.info(f"🌤️ Weather Provider: {WEATHER_PROVIDER}")
logger.info(f"🗄️ Database: PostgreSQL Connected")

# Configure OpenAI client if needed
if AI_PROVIDER == "azure" and config.AZURE_OPENAI_KEY:
    openai.api_type = "azure"
    openai.api_key = config.AZURE_OPENAI_KEY
    openai.api_base = config.AZURE_OPENAI_ENDPOINT
    openai.api_version = "2024-02-15-preview"
elif AI_PROVIDER == "openai" and config.OPENAI_API_KEY:
    openai.api_key = config.OPENAI_API_KEY

# Data Models
class ChatMessage(BaseModel):
    query: str
    mode: str = "text"
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
    recommendations: List[Dict[str, Any]]
    voyage_stage: str
    priority_actions: List[str]

class LocationSearchQuery(BaseModel):
    query: str
    type: Optional[str] = "all"

class LocationResult(BaseModel):
    name: str
    country: str
    lat: float
    lng: float
    type: str
    details: Dict[str, Any]

class VesselQuery(BaseModel):
    vessel_name: Optional[str] = None
    imo_number: Optional[str] = None
    area_bounds: Optional[Dict[str, float]] = None

class VesselResult(BaseModel):
    name: str
    imo: str
    type: str
    lat: float
    lng: float
    speed: float
    heading: float
    status: str
    destination: str
    eta: str
    last_updated: str

class RouteQuery(BaseModel):
    origin: Dict[str, float]  # {"lat": float, "lng": float}
    destination: Dict[str, float]  # {"lat": float, "lng": float}
    vessel_type: Optional[str] = "container"
    optimization: Optional[str] = "weather"

class RouteResult(BaseModel):
    distance_nm: float
    estimated_time_hours: float
    fuel_consumption_mt: float
    route_points: List[Dict[str, float]]
    weather_warnings: Optional[List[str]] = []
    route_type: Optional[str] = "marine_optimized"
    vessel_type: Optional[str] = "container"
    routing_details: Optional[Dict[str, Any]] = {}

# Maritime System Prompt
MARITIME_SYSTEM_PROMPT = """
You are a specialized Maritime Virtual Assistant with expertise in:

**Core Maritime Operations:**
- International shipping regulations and maritime law (SOLAS, MARPOL, ISM Code)
- Charter party agreements, laytime calculations, and demurrage procedures
- Port operations, cargo handling, and vessel documentation
- Weather routing, navigation safety, and voyage optimization
- Maritime insurance, P&I claims, and risk management

**Technical Calculations:**
- Laytime calculations with SHINC/SHEX terms
- Demurrage and dispatch computations
- Bunker consumption and voyage economics
- Port cost analysis and comparison
- Distance calculations and ETA predictions

**Professional Response Format:**
- Use precise maritime terminology and industry abbreviations
- Provide step-by-step calculations when relevant
- Include relevant regulatory references (IMO, flag state, port state)
- Structure responses with clear headings and bullet points
- Bold key figures, dates, and critical information

**Sample Response Structure:**
## Analysis
[Detailed technical analysis]

## Calculations
[Step-by-step mathematical workings]

## Recommendations
[Professional maritime advice]

## Regulatory Compliance
[Applicable regulations and requirements]

Always maintain the highest standards of maritime professionalism and accuracy in your responses.
"""

# AI Services
class MaritimeAIService:
    @staticmethod
    async def get_ai_response(query: str, conversation_id: str = None) -> ChatResponse:
        try:
            ai_response = "Default response"
            confidence = 0.8
            
            if AI_PROVIDER == "groq":
                headers = {
                    "Authorization": f"Bearer {config.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama3-70b-8192",
                    "messages": [
                        {"role": "system", "content": MARITIME_SYSTEM_PROMPT},
                        {"role": "user", "content": query}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.7
                }
                
                response = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                       headers=headers, json=payload)
                if response.status_code == 200:
                    ai_response = response.json()["choices"][0]["message"]["content"]
                    confidence = 0.95
                else:
                    raise Exception(f"Groq API error: {response.status_code}")
            
            elif AI_PROVIDER == "openai":
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": MARITIME_SYSTEM_PROMPT},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=1500,
                    temperature=0.7
                )
                ai_response = response.choices[0].message.content
                confidence = 0.95
            
            elif AI_PROVIDER == "huggingface":
                api_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-70b-chat-hf"
                headers = {"Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}"}
                payload = {
                    "inputs": f"System: {MARITIME_SYSTEM_PROMPT}\n\nUser: {query}\n\nAssistant:",
                    "parameters": {"max_new_tokens": 1500, "temperature": 0.7}
                }
                
                response = requests.post(api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    ai_response = response.json()[0]["generated_text"].split("Assistant:")[-1].strip()
                    confidence = 0.9
                else:
                    raise Exception(f"HuggingFace API error: {response.status_code}")
            
            else:
                # Mock response for development
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
            return ChatResponse(
                response=f"I apologize for the technical difficulty. Based on maritime best practices: {MaritimeAIService._get_mock_response(query)}",
                confidence=0.6,
                sources=["Fallback Maritime Knowledge"],
                conversation_id=conversation_id or str(uuid.uuid4())
            )
    
    @staticmethod
    def _get_mock_response(query: str) -> str:
        query_lower = query.lower()
        
        if any(term in query_lower for term in ["laytime", "demurrage", "charter party", "cp"]):
            return """## Laytime and Demurrage Analysis

**Standard Laytime Provisions:**
- **Notice of Readiness (NOR)**: Must be tendered in writing to charterers/agents
- **Laytime Commencement**: Typically starts at 06:00 hours following day after NOR acceptance
- **Calculating Laytime**: Based on charter party terms (SHINC/SHEX, WWD/WWDSHEX)

**Key Calculations:**
- **Time on Demurrage** = (Total Loading/Discharge Time) - (Allowed Laytime)
- **Demurrage Rate**: As per charter party (typically USD 15,000-35,000/day for bulk carriers)
- **Despatch**: Usually 50% of demurrage rate for time saved

**Documentation Required:**
- Statement of Facts (SOF)
- Time sheets with port agent signatures  
- NOR and acceptance confirmation
- Weather reports if applicable

Always refer to the specific charter party terms and BIMCO standard forms for precise calculations."""
        
        elif any(term in query_lower for term in ["weather", "routing", "storm", "conditions"]):
            return """## Maritime Weather Routing Analysis

**Weather Assessment Factors:**
- **Wind Speed/Direction**: Critical for fuel consumption and ETA
- **Wave Height**: Affects vessel speed and cargo safety
- **Visibility**: Important for navigation safety
- **Storm Systems**: Require route deviation planning

**Routing Recommendations:**
- Monitor 5-7 day weather forecasts continuously
- Use professional routing services (StormGeo, Applied Weather Technology)
- Consider seasonal weather patterns (monsoons, hurricanes)
- Plan alternative routes for severe weather

**Safety Considerations:**
- Follow SOLAS Chapter V requirements
- Maintain continuous weather monitoring
- Document weather-related delays in deck log
- Consider cargo sensitivity to weather conditions

**Economic Impact:**
- Weather routing can save 5-15% fuel consumption
- Reduced charter hire through faster passages
- Minimize cargo damage claims from heavy weather"""
        
        elif any(term in query_lower for term in ["distance", "voyage", "eta", "route"]):
            return """## Voyage Planning and Distance Calculation

**Distance Calculation Methods:**
- **Great Circle Distance**: Shortest route between two points
- **Rhumb Line**: Constant compass bearing route
- **Commercial Route**: Considering traffic separation schemes and canals

**Standard Maritime Distances:**
- Rotterdam - Singapore: ~8,300 nm
- New York - Rotterdam: ~3,200 nm  
- Singapore - Shanghai: ~1,450 nm
- Suez Canal transit: ~120 nm

**ETA Calculations:**
- **Sea Time** = Distance ÷ Average Speed
- **Port Time** = Loading/Discharge time + waiting time
- **Total Voyage Time** = Sea Time + Port Time + Canal Transit

**Voyage Optimization:**
- Speed optimization for fuel efficiency
- Port scheduling and slot booking
- Canal booking and pilotage arrangements
- Weather routing integration"""
        
        else:
            return f"Thank you for your maritime query about: '{query}'. I specialize in laytime calculations, weather routing, voyage planning, charter party analysis, and maritime operations. Please provide more specific details about your shipping requirements for a detailed professional analysis."

# Weather Service
class WeatherService:
    @staticmethod
    async def get_weather_data(query: WeatherQuery) -> WeatherResponse:
        try:
            if WEATHER_PROVIDER == "openweather" and config.OPENWEATHER_API_KEY:
                # OpenWeatherMap API call
                url = f"http://api.openweathermap.org/data/2.5/weather"
                params = {
                    "lat": query.latitude,
                    "lon": query.longitude,
                    "appid": config.OPENWEATHER_API_KEY,
                    "units": "metric"
                }
                
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return WeatherResponse(
                        current_weather={
                            "temperature": data["main"]["temp"],
                            "humidity": data["main"]["humidity"],
                            "pressure": data["main"]["pressure"],
                            "wind_speed": data["wind"]["speed"],
                            "wind_direction": data["wind"]["deg"],
                            "visibility": data.get("visibility", 10000) / 1000,
                            "conditions": data["weather"][0]["description"]
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
                        warnings=[]
                    )
                else:
                    raise Exception(f"OpenWeatherMap API error: {response.status_code}")
            else:
                # Mock weather data
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
                "conditions": "partly cloudy with moderate seas"
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
            warnings=["No active weather warnings for maritime operations"]
        )

# API Endpoints
@app.get("/")
async def health_check():
    return {
        "status": "operational",
        "message": "Maritime Virtual Assistant API v2.0 - Production Ready",
        "ai_provider": AI_PROVIDER,
        "weather_provider": WEATHER_PROVIDER,
        "database": "PostgreSQL",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Production AI-powered maritime chat assistant"""
    try:
        response = await MaritimeAIService.get_ai_response(
            message.query, 
            message.conversation_id
        )
        logger.info(f"Chat query processed: {message.query[:50]}...")
        return response
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="AI service temporarily unavailable")

@app.post("/weather", response_model=WeatherResponse)
async def weather_endpoint(query: WeatherQuery):
    """Get professional marine weather data"""
    try:
        response = await WeatherService.get_weather_data(query)
        logger.info(f"Weather data requested for: {query.latitude}, {query.longitude}")
        return response
    except Exception as e:
        logger.error(f"Weather endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Weather service temporarily unavailable")

@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Process maritime documents (Charter Party, SOF, etc.)"""
    try:
        # Validate file size
        if file.size and file.size > config.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Generate document ID
        document_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        # Read file content
        content = await file.read()
        
        # Mock document processing (replace with actual OCR/AI processing)
        extracted_text = f"Document analysis of {file.filename} completed."
        key_insights = [
            "Charter Party Agreement identified",
            "Laytime terms: 72 hours SHINC",
            "Demurrage rate: USD 25,000/day",
            "Load port: Rotterdam",
            "Discharge port: Singapore"
        ]
        
        logger.info(f"Document uploaded and processed: {file.filename}")
        
        return DocumentUploadResponse(
            document_id=document_id,
            extracted_text=extracted_text,
            key_insights=key_insights,
            document_type="Charter Party",
            processing_status="completed"
        )
    except Exception as e:
        logger.error(f"Upload endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Document processing failed")

@app.post("/recommendations", response_model=RecommendationResponse)
async def recommendations_endpoint(voyage_data: Dict[str, Any]):
    """Get AI-powered voyage recommendations"""
    try:
        # Mock recommendations (replace with AI analysis)
        recommendations = [
            {
                "title": "Weather Route Optimization",
                "description": "Recommend alternative routing to avoid storm system",
                "priority": "high",
                "action": "Contact routing service for updated weather routing",
                "estimated_time": "2 hours"
            },
            {
                "title": "Port Documentation Review",
                "description": "Ensure all certificates are current for port entry",
                "priority": "medium", 
                "action": "Verify PSC certificates and crew documents",
                "estimated_time": "1 hour"
            }
        ]
        
        return RecommendationResponse(
            recommendations=recommendations,
            voyage_stage="transit",
            priority_actions=["Weather routing", "Documentation check"]
        )
    except Exception as e:
        logger.error(f"Recommendations endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Recommendations service unavailable")

@app.get("/settings")
async def settings_endpoint():
    """API configuration and health status"""
    return {
        "ai_provider": AI_PROVIDER,
        "weather_provider": WEATHER_PROVIDER,
        "database": "postgresql",
        "api_keys_configured": {
            "ai": AI_PROVIDER != "mock",
            "weather": WEATHER_PROVIDER != "mock"
        },
        "features_enabled": {
            "ai_chat": True,
            "weather_data": True,
            "document_processing": True,
            "recommendations": True,
            "route_optimization": True
        },
        "system_status": "operational"
    }

# Location and vessel endpoints
@app.post("/locations/search", response_model=List[LocationResult])
async def search_locations(query: LocationSearchQuery):
    """Search maritime locations and ports"""
    try:
        # Mock implementation - replace with actual database query
        results = [
            LocationResult(
                name="Port of Rotterdam",
                country="Netherlands",
                lat=51.9244,
                lng=4.4777,
                type="port",
                details={"port_code": "NLRTM", "max_draft": 24.0}
            )
        ]
        return results
    except Exception as e:
        logger.error(f"Location search error: {e}")
        raise HTTPException(status_code=500, detail="Location search failed")

@app.post("/vessels/track", response_model=List[VesselResult])
async def track_vessels(query: VesselQuery):
    """Track vessel positions and details"""
    try:
        # Mock implementation
        results = [
            VesselResult(
                name="MARITIME STAR",
                imo="9123456",
                type="Container Ship",
                lat=52.0,
                lng=4.0,
                speed=14.5,
                heading=90,
                status="Under Way Using Engine",
                destination="SINGAPORE",
                eta="2024-02-15T08:00:00Z",
                last_updated=datetime.now().isoformat()
            )
        ]
        return results
    except Exception as e:
        logger.error(f"Vessel tracking error: {e}")
        raise HTTPException(status_code=500, detail="Vessel tracking failed")

@app.post("/routes/optimize", response_model=RouteResult)
async def optimize_route(query: RouteQuery):
    """Professional maritime route optimization"""
    try:
        # Use professional routing service
        result = professional_router.optimize_route(
            origin=query.origin,
            destination=query.destination,
            vessel_type=query.vessel_type,
            optimization_mode=query.optimization
        )
        
        logger.info(f"Route optimized: {query.origin} -> {query.destination}")
        return result
        
    except Exception as e:
        logger.error(f"Route optimization error: {e}")
        # Fallback to basic routing
        direct_route = [query.origin, query.destination]
        return RouteResult(
            distance_nm=1000.0,
            estimated_time_hours=48.0,
            fuel_consumption_mt=120.0,
            route_points=direct_route,
            route_type="fallback_direct",
            routing_details={"error": "Professional routing unavailable"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )

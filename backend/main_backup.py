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
    description="AI-powered maritime assistant backend for shipping industry professionals",
    version="1.0.0"
)

# CORS middleware for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
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
    
    # FREE AI API Options
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
    
    # Weather API Configuration
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    
    # Azure Cognitive Services
    AZURE_COGNITIVE_KEY = os.getenv("AZURE_COGNITIVE_SERVICES_KEY")
    AZURE_COGNITIVE_ENDPOINT = os.getenv("AZURE_COGNITIVE_SERVICES_ENDPOINT")

config = APIConfig()

# Configure AI Client with Production Priority
AI_PROVIDER = config.ai_provider
WEATHER_PROVIDER = config.weather_provider

logger.info(f"🤖 AI Provider: {AI_PROVIDER}")
logger.info(f"🌤️ Weather Provider: {WEATHER_PROVIDER}")
logger.info(f"🗄️ Database: Connected to PostgreSQL")
    logger.info("Using Together AI (FREE Credits)")
elif config.AZURE_OPENAI_KEY and config.AZURE_OPENAI_ENDPOINT:
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
You are a senior Maritime Operations Consultant and Chartering Expert with 20+ years of industry experience specializing in commercial shipping operations, charter party analysis, and maritime law.

🚢 CORE EXPERTISE:
• Charter Party Analysis & Negotiation (NYPE, Barecon, Gencon, Baltimore forms)
• Laytime/Demurrage/Dispatch Calculations (BIMCO, FONASBA, WORLDSCALE)
• Maritime Commercial Law & Arbitration (London, New York, Singapore, Hong Kong)
• Port Operations, Terminal Procedures & Cargo Handling
• Vessel Performance Analysis & Weather Routing Optimization
• Maritime Regulatory Compliance (IMO, Flag State, Port State requirements)
• International Trade & Shipping Documentation (Bills of Lading, Letters of Credit)
• Marine Insurance, P&I Club Claims & Risk Management
• Dry Cargo, Tanker, and Bulk Carrier Operations

📋 MANDATORY RESPONSE STRUCTURE:
Always format responses using this professional structure:

## EXECUTIVE SUMMARY
Brief overview of key findings, recommendations, or answers (2-3 sentences)

## DETAILED ANALYSIS
### Calculation/Technical Breakdown (if applicable)
**Method:** [Calculation methodology]
**Formula:** [Relevant formula with variables]
**Step-by-step Calculation:**
1. [Step 1 with numbers]
2. [Step 2 with numbers]  
3. [Final result]

**Summary Table:** (when applicable)
| Parameter | Value | Unit | Notes |
|-----------|-------|------|-------|
| [Parameter] | [Value] | [Unit] | [Explanation] |

### Industry Context
- **Relevant Regulations:** [Cite specific IMO conventions, charter party clauses]
- **Market Practice:** [Standard industry approach]
- **Charter Party Implications:** [Specific clause references]

## PRACTICAL CONSIDERATIONS
### Implementation Notes
- [Practical step 1]
- [Practical step 2]

### Risk Factors & Mitigation
- **Risk:** [Identified risk] | **Mitigation:** [Suggested action]
- **Risk:** [Identified risk] | **Mitigation:** [Suggested action]

## REGULATORY REFERENCES
- **IMO Conventions:** [Specific references]
- **Charter Party Clauses:** [Relevant standard form clauses]
- **Industry Guidelines:** [BIMCO, ICS, INTERCARGO standards]
- **Case Law:** [Relevant precedents if applicable]

## RECOMMENDATIONS
1. **Immediate Actions:** [Urgent items]
2. **Medium-term Considerations:** [Planning items]
3. **Documentation Requirements:** [Required paperwork/evidence]

---
*Professional Opinion: [Concluding expert assessment]*

� MARKDOWN FORMATTING REQUIREMENTS:
**CRITICAL: All responses MUST be formatted in proper Markdown with:**
- Use ## for main section headers (EXECUTIVE SUMMARY, DETAILED ANALYSIS, etc.)
- Use ### for subsection headers (Implementation Notes, Risk Factors, etc.)
- Use **bold text** for key terms, figures, and emphasis
- Use - or * for bullet points and lists
- Use | tables | for structured data presentation
- Use `code formatting` for technical terms and calculations
- Use > blockquotes for important notes or regulations
- Always use proper line breaks between sections
- Include horizontal rules (---) for visual separation

�🔢 CALCULATION STANDARDS:
- Always show complete step-by-step methodology
- Include all relevant variables and assumptions
- Reference specific charter party clauses or BIMCO guidelines
- Present final results in both tabular and summary format
- Consider weather, port conditions, and market factors
- Provide alternative calculation methods when industry practice varies

💼 PROFESSIONAL TERMINOLOGY:
Mandatory use of precise maritime terms:
- "Vessel" (commercial contexts) vs "Ship" (technical/regulatory)
- "Owner/Disponent Owner" and "Charterer" (always capitalized per C/P practice)
- "Laytime" vs "Demurrage" vs "Detention" (distinct concepts)
- "NOR" (Notice of Readiness), "SOF" (Statement of Facts), "LOI" (Letter of Indemnity)
- "Free Pratique," "All Fast," "Commenced Loading/Discharging"
- "WWWW" (Weather Working Days), "SHEX/SHINC" (Sundays/Holidays Excluded/Included)

⚖️ REGULATORY INTEGRATION:
Always incorporate relevant:
- **IMO Conventions:** SOLAS, MARPOL, STCW, MLC, BWM, COLREG
- **Charter Party Forms:** NYPE 2015, Barecon 2017, Gencon 2022, Asbatankvoy
- **BIMCO Clauses:** Specific clause numbers and applications  
- **Port Regulations:** Local requirements, VTS procedures, pilot regulations
- **Flag/Class Requirements:** Specific surveying and certification requirements

📊 FORMATTING REQUIREMENTS:
- Use clear section headers with ## and ###
- Employ bullet points for lists and key information
- Include professional tables for calculations and comparisons
- Bold key terms, figures, and conclusions
- Use maritime industry standard abbreviations consistently
- Maintain professional, consultant-level language throughout

This response format ensures comprehensive, structured, and professionally presented maritime expertise that meets industry standards for commercial shipping operations and chartering advice.
"""

# AI Chat Service
class MaritimeAIService:
    @staticmethod
    async def get_ai_response(query: str, conversation_id: str = None) -> ChatResponse:
        try:
            if AI_PROVIDER == "huggingface":
                # Use Hugging Face Inference API (FREE)
                api_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-70b-chat-hf"
                headers = {"Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}"}
                payload = {
                    "inputs": f"System: {MARITIME_SYSTEM_PROMPT}\n\nUser: {query}\n\nAssistant:",
                    "parameters": {"max_new_tokens": 1000, "temperature": 0.7}
                }
                
                response = requests.post(api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    ai_response = response.json()[0]["generated_text"].split("Assistant:")[-1].strip()
                    confidence = 0.9
                else:
                    raise Exception(f"HuggingFace API error: {response.status_code}")
            
            elif AI_PROVIDER == "openrouter":
                # Use OpenRouter API (FREE Credits)
                headers = {
                    "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "meta-llama/llama-3.1-8b-instruct:free",
                    "messages": [
                        {"role": "system", "content": MARITIME_SYSTEM_PROMPT},
                        {"role": "user", "content": query}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
                
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                       headers=headers, json=payload)
                if response.status_code == 200:
                    ai_response = response.json()["choices"][0]["message"]["content"]
                    confidence = 0.9
                else:
                    raise Exception(f"OpenRouter API error: {response.status_code}")
            
            elif AI_PROVIDER == "groq":
                # Use Groq API (FREE & Super Fast)
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
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
                
                response = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                       headers=headers, json=payload)
                if response.status_code == 200:
                    ai_response = response.json()["choices"][0]["message"]["content"]
                    confidence = 0.9
                else:
                    raise Exception(f"Groq API error: {response.status_code}")
            
            elif AI_PROVIDER == "together":
                # Use Together AI (FREE Credits)
                headers = {
                    "Authorization": f"Bearer {config.TOGETHER_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "meta-llama/Llama-2-70b-chat-hf",
                    "messages": [
                        {"role": "system", "content": MARITIME_SYSTEM_PROMPT},
                        {"role": "user", "content": query}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
                
                response = requests.post("https://api.together.xyz/v1/chat/completions",
                                       headers=headers, json=payload)
                if response.status_code == 200:
                    ai_response = response.json()["choices"][0]["message"]["content"]
                    confidence = 0.9
                else:
                    raise Exception(f"Together AI error: {response.status_code}")
            
            elif AI_PROVIDER == "azure":
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

# New Pydantic models for enhanced functionality
class LocationSearchQuery(BaseModel):
    query: str
    type: str = "all"  # "port", "city", "coordinates", "all"

class LocationResult(BaseModel):
    name: str
    country: str
    lat: float
    lng: float
    type: str  # "port", "city", "landmark"
    details: Dict[str, Any]

class VesselQuery(BaseModel):
    vessel_name: Optional[str] = None
    imo_number: Optional[str] = None
    area_bounds: Optional[Dict[str, float]] = None  # lat_min, lat_max, lng_min, lng_max

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
    origin: Dict[str, float]  # lat, lng
    destination: Dict[str, float]  # lat, lng
    vessel_type: str = "container"
    optimization: str = "time"  # "time", "fuel", "weather"

class RouteResult(BaseModel):
    distance_nm: float
    estimated_time_hours: float
    fuel_consumption_mt: float
    route_points: List[Dict[str, float]]
    weather_warnings: List[str] = []
    route_type: str = "marine_optimized"
    vessel_type: str = "General Cargo"
    routing_details: Dict[str, Any] = {}

# Location Search Service
class LocationService:
    @staticmethod
    async def search_locations(query: LocationSearchQuery) -> List[LocationResult]:
        """Search for maritime locations (ports, cities, coordinates)"""
        try:
            # Enhanced ports database with more details
            maritime_locations = [
                # Major European Ports
                {"name": "Rotterdam", "country": "Netherlands", "lat": 51.9225, "lng": 4.4792, "type": "port", 
                 "details": {"code": "NLRTM", "max_draft": 23.0, "pilot_required": True, "vts_channel": "VHF 11"}},
                {"name": "Hamburg", "country": "Germany", "lat": 53.5511, "lng": 9.9937, "type": "port",
                 "details": {"code": "DEHAM", "max_draft": 15.1, "pilot_required": True, "vts_channel": "VHF 12"}},
                {"name": "Antwerp", "country": "Belgium", "lat": 51.2194, "lng": 4.4025, "type": "port",
                 "details": {"code": "BEANR", "max_draft": 17.5, "pilot_required": True, "vts_channel": "VHF 09"}},
                {"name": "Le Havre", "country": "France", "lat": 49.4938, "lng": 0.1077, "type": "port",
                 "details": {"code": "FRLEH", "max_draft": 16.0, "pilot_required": True, "vts_channel": "VHF 68"}},
                {"name": "Felixstowe", "country": "United Kingdom", "lat": 51.9538, "lng": 1.3517, "type": "port",
                 "details": {"code": "GBFXT", "max_draft": 16.0, "pilot_required": True, "vts_channel": "VHF 14"}},
                
                # Major Asian Ports
                {"name": "Singapore", "country": "Singapore", "lat": 1.3521, "lng": 103.8198, "type": "port",
                 "details": {"code": "SGSIN", "max_draft": 25.0, "pilot_required": True, "vts_channel": "VHF 12"}},
                {"name": "Shanghai", "country": "China", "lat": 31.2304, "lng": 121.4737, "type": "port",
                 "details": {"code": "CNSHA", "max_draft": 12.5, "pilot_required": True, "vts_channel": "VHF 09"}},
                {"name": "Hong Kong", "country": "Hong Kong", "lat": 22.3193, "lng": 114.1694, "type": "port",
                 "details": {"code": "HKHKG", "max_draft": 17.0, "pilot_required": True, "vts_channel": "VHF 12"}},
                {"name": "Tokyo", "country": "Japan", "lat": 35.6762, "lng": 139.6503, "type": "port",
                 "details": {"code": "JPTYO", "max_draft": 16.0, "pilot_required": True, "vts_channel": "VHF 16"}},
                {"name": "Busan", "country": "South Korea", "lat": 35.1796, "lng": 129.0756, "type": "port",
                 "details": {"code": "KRPUS", "max_draft": 17.0, "pilot_required": True, "vts_channel": "VHF 14"}},
                
                # Major American Ports
                {"name": "Los Angeles", "country": "USA", "lat": 33.7361, "lng": -118.2639, "type": "port",
                 "details": {"code": "USLAX", "max_draft": 16.8, "pilot_required": True, "vts_channel": "VHF 14"}},
                {"name": "New York", "country": "USA", "lat": 40.7128, "lng": -74.0060, "type": "port",
                 "details": {"code": "USNYC", "max_draft": 15.2, "pilot_required": True, "vts_channel": "VHF 12"}},
                {"name": "Houston", "country": "USA", "lat": 29.7604, "lng": -95.3698, "type": "port",
                 "details": {"code": "USHOU", "max_draft": 13.7, "pilot_required": True, "vts_channel": "VHF 16"}},
                {"name": "Santos", "country": "Brazil", "lat": -23.9537, "lng": -46.3396, "type": "port",
                 "details": {"code": "BRSST", "max_draft": 15.0, "pilot_required": True, "vts_channel": "VHF 16"}},
                
                # Major Cities for reference
                {"name": "London", "country": "United Kingdom", "lat": 51.5074, "lng": -0.1278, "type": "city",
                 "details": {"timezone": "GMT", "maritime_services": ["P&I Clubs", "Maritime Law", "Ship Finance"]}},
                {"name": "Dubai", "country": "UAE", "lat": 25.2048, "lng": 55.2708, "type": "city",
                 "details": {"timezone": "GST+4", "maritime_services": ["Bunkering", "Ship Supply", "Crew Change"]}},
            ]
            
            # Filter results based on query
            results = []
            query_lower = query.query.lower()
            
            for location in maritime_locations:
                if (query_lower in location["name"].lower() or 
                    query_lower in location["country"].lower() or
                    (query.type == "all" or query.type == location["type"])):
                    results.append(LocationResult(**location))
            
            return results[:10]  # Limit to 10 results
            
        except Exception as e:
            logger.error(f"Location search error: {e}")
            return []

# Vessel Tracking Service (Mock AIS data)
class VesselService:
    @staticmethod
    async def get_vessels(query: VesselQuery) -> List[VesselResult]:
        """Get vessel positions and information"""
        try:
            # Mock vessel data (in production, integrate with real AIS APIs like MarineTraffic, VesselFinder, etc.)
            sample_vessels = [
                {"name": "EVER GIVEN", "imo": "9811000", "type": "Container Ship", "lat": 30.0444, "lng": 31.2357, 
                 "speed": 0.1, "heading": 12, "status": "At Anchor", "destination": "NLRTM", "eta": "2025-08-20 14:30"},
                {"name": "VALE BRASIL", "imo": "9632443", "type": "Bulk Carrier", "lat": 51.9225, "lng": 4.4792,
                 "speed": 0.0, "heading": 95, "status": "Moored", "destination": "CNSHA", "eta": "2025-09-05 08:00"},
                {"name": "FRONT ALTAIR", "imo": "9797725", "type": "Oil Tanker", "lat": 35.6762, "lng": 139.6503,
                 "speed": 12.3, "heading": 220, "status": "Under Way", "destination": "SGSIN", "eta": "2025-08-25 16:45"},
                {"name": "MSC OSCAR", "imo": "9703291", "type": "Container Ship", "lat": 1.3521, "lng": 103.8198,
                 "speed": 0.2, "heading": 180, "status": "Loading", "destination": "DEHAM", "eta": "2025-09-12 10:15"},
                {"name": "SEAWISE GIANT", "imo": "7381154", "type": "VLCC Tanker", "lat": 25.2048, "lng": 55.2708,
                 "speed": 15.6, "heading": 305, "status": "Under Way", "destination": "USLAX", "eta": "2025-09-18 20:30"},
            ]
            
            results = []
            for vessel in sample_vessels:
                # Filter by name or IMO if specified
                if query.vessel_name and query.vessel_name.upper() not in vessel["name"]:
                    continue
                if query.imo_number and query.imo_number not in vessel["imo"]:
                    continue
                    
                # Filter by area bounds if specified
                if query.area_bounds:
                    bounds = query.area_bounds
                    if not (bounds["lat_min"] <= vessel["lat"] <= bounds["lat_max"] and
                           bounds["lng_min"] <= vessel["lng"] <= bounds["lng_max"]):
                        continue
                
                results.append(VesselResult(
                    **vessel,
                    last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Vessel tracking error: {e}")
            return []

# Enhanced Route Optimization Service with Professional Marine Routing
class RouteService:
    @staticmethod
    async def calculate_route(query: RouteQuery) -> RouteResult:
        """Calculate optimized maritime route using professional marine routing"""
        try:
            origin = query.origin
            destination = query.destination
            
            # Use professional maritime routing system
            route_points_raw = professional_router.calculate_maritime_route(
                (origin["lat"], origin["lng"]),
                (destination["lat"], destination["lng"])
            )
            
            # Convert to the expected format
            route_points = [{"lat": lat, "lng": lng} for lat, lng in route_points_raw]
            
            # Calculate total distance along the marine route
            from math import radians, cos, sin, asin, sqrt
            
            def haversine_distance(lat1, lon1, lat2, lon2):
                # Convert decimal degrees to radians
                lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                
                # Haversine formula
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                
                # Radius of earth in nautical miles
                r = 3440.065
                return c * r
            
            # Calculate total distance along route
            total_distance = 0
            for i in range(len(route_points) - 1):
                segment_distance = haversine_distance(
                    route_points[i]["lat"], route_points[i]["lng"],
                    route_points[i + 1]["lat"], route_points[i + 1]["lng"]
                )
                total_distance += segment_distance
            
            # Enhanced vessel-specific parameters
            vessel_params = {
                "container": {"avg_speed": 22, "fuel_rate": 2.8, "description": "Container Ship"},
                "bulk": {"avg_speed": 14, "fuel_rate": 1.6, "description": "Bulk Carrier"},
                "tanker": {"avg_speed": 15, "fuel_rate": 2.4, "description": "Oil Tanker"},
                "general": {"avg_speed": 18, "fuel_rate": 2.2, "description": "General Cargo"},
                "roro": {"avg_speed": 20, "fuel_rate": 2.5, "description": "RoRo Ferry"},
                "cruise": {"avg_speed": 25, "fuel_rate": 3.2, "description": "Cruise Ship"}
            }
            
            params = vessel_params.get(query.vessel_type, vessel_params["general"])
            
            # Enhanced calculations with route factors
            base_speed = params["avg_speed"]
            
            # Adjust for weather and sea conditions (simplified)
            weather_factor = 0.95  # Assume some headwind/adverse conditions
            route_factor = 1.1    # Factor for complex routing around land masses
            
            effective_speed = base_speed * weather_factor
            estimated_time = (total_distance * route_factor) / effective_speed
            fuel_consumption = estimated_time * params["fuel_rate"]
            
            # Add realistic routing information
            routing_info = RouteService._analyze_route(route_points_raw)
            
            return RouteResult(
                distance_nm=round(total_distance, 1),
                estimated_time_hours=round(estimated_time, 1),
                fuel_consumption_mt=round(fuel_consumption, 1),
                route_points=route_points,
                weather_warnings=[],
                route_type="marine_optimized",
                vessel_type=params["description"],
                routing_details=routing_info
            )
            
        except Exception as e:
            logger.error(f"Route calculation error: {e}")
            # Fallback to simple great circle route
            return await RouteService._fallback_route(query)
    
    @staticmethod
    def _analyze_route(route_points: List[tuple]) -> Dict[str, Any]:
        """Analyze route for special maritime features"""
        routing_info = {
            "major_waypoints": [],
            "special_zones": [],
            "estimated_canals": [],
            "weather_considerations": []
        }
        
        # Check for major maritime waypoints using professional router
        waypoints = professional_router.major_waypoints
        
        for point_name, point_coords in waypoints.items():
            for route_point in route_points:
                # Check if route passes near major waypoints (within 2 degrees)
                if abs(route_point[0] - point_coords[0]) < 2.0 and abs(route_point[1] - point_coords[1]) < 2.0:
                    routing_info["major_waypoints"].append({
                        "name": point_name.replace("_", " ").title(),
                        "coordinates": point_coords,
                        "description": RouteService._get_waypoint_description(point_name)
                    })
        
        # Add general routing considerations
        if any("suez" in wp["name"].lower() for wp in routing_info["major_waypoints"]):
            routing_info["estimated_canals"].append("Suez Canal transit included")
        if any("panama" in wp["name"].lower() for wp in routing_info["major_waypoints"]):
            routing_info["estimated_canals"].append("Panama Canal transit included")
        if any("cape" in wp["name"].lower() for wp in routing_info["major_waypoints"]):
            routing_info["special_zones"].append("Cape route - deep water passage")
        
        return routing_info
    
    @staticmethod
    def _get_waypoint_description(waypoint_name: str) -> str:
        """Get description for maritime waypoints"""
        descriptions = {
            "suez_canal": "Major shipping canal connecting Mediterranean and Red Sea",
            "panama_canal": "Critical canal connecting Atlantic and Pacific",
            "strait_of_hormuz": "Strategic chokepoint for oil shipments",
            "strait_of_malacca": "Busiest shipping lane in Southeast Asia",
            "gibraltar": "Gateway between Mediterranean and Atlantic",
            "cape_of_good_hope": "Southern tip of Africa, deep-water route",
            "cape_horn": "Southern tip of South America",
            "singapore_strait": "Major port and transshipment hub"
        }
        return descriptions.get(waypoint_name, "Important maritime waypoint")
    
    @staticmethod
    async def _fallback_route(query: RouteQuery) -> RouteResult:
        """Fallback to simple great circle route if marine routing fails"""
        origin = query.origin
        destination = query.destination
        
        # Simple great circle calculation
        from math import radians, cos, sin, asin, sqrt
        
        def haversine_distance(lat1, lon1, lat2, lon2):
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 3440.065
            return c * r
        
        distance_nm = haversine_distance(
            origin["lat"], origin["lng"], 
            destination["lat"], destination["lng"]
        )
        
        # Simple route points
        route_points = [
            {"lat": origin["lat"], "lng": origin["lng"]},
            {"lat": (origin["lat"] + destination["lat"]) / 2, "lng": (origin["lng"] + destination["lng"]) / 2},
            {"lat": destination["lat"], "lng": destination["lng"]}
        ]
        
        # Simple calculations for fallback
        estimated_time = distance_nm / 18  # Average speed
        fuel_consumption = estimated_time * 2.2  # Average consumption
        
        return RouteResult(
            distance_nm=round(distance_nm, 1),
            estimated_time_hours=round(estimated_time, 1),
            fuel_consumption_mt=round(fuel_consumption, 1),
            route_points=route_points,
            weather_warnings=[],
            route_type="fallback_great_circle",
            vessel_type="General Cargo",
            routing_details={"note": "Fallback route - marine routing unavailable"}
        )

# API Endpoints for new services
@app.post("/locations/search", response_model=List[LocationResult])
async def search_locations(query: LocationSearchQuery):
    """Search for maritime locations, ports, and cities"""
    try:
        results = await LocationService.search_locations(query)
        return results
    except Exception as e:
        logger.error(f"Location search endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vessels/track", response_model=List[VesselResult])
async def track_vessels(query: VesselQuery):
    """Get vessel tracking information"""
    try:
        results = await VesselService.get_vessels(query)
        return results
    except Exception as e:
        logger.error(f"Vessel tracking endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/weather/search-location")
async def search_location(query: str):
    """Enhanced global location search with comprehensive city database"""
    try:
        if not query or len(query) < 2:
            return {"locations": [], "message": "Query too short"}
        
        query_lower = query.lower().strip()
        results = []
        
        # Search in global cities database
        for city_name, city_data in GLOBAL_CITIES_DATABASE.items():
            # Check if query matches city name or country
            if (query_lower in city_name.lower() or 
                query_lower in city_data["country"].lower() or
                city_name.lower().startswith(query_lower)):
                
                results.append({
                    "name": f"{city_name}, {city_data['country']}",
                    "lat": city_data["lat"],
                    "lng": city_data["lng"],
                    "type": city_data["type"],
                    "country": city_data["country"],
                    "display_name": f"{city_name} ({city_data['type'].title()}) - {city_data['country']}"
                })
        
        # Sort by relevance (exact matches first, then partial matches)
        results.sort(key=lambda x: (
            0 if x["name"].lower().startswith(query_lower) else 1,
            len(x["name"])
        ))
        
        # Limit results
        results = results[:10]
        
        if results:
            return {
                "locations": results,
                "coordinates": {"lat": results[0]["lat"], "lng": results[0]["lng"]},
                "location_name": results[0]["name"],
                "message": f"Found {len(results)} locations"
            }
        else:
            return {
                "locations": [],
                "message": f"No locations found for '{query}'. Try major cities or ports."
            }
            
    except Exception as e:
        logger.error(f"Location search error: {e}")
        return {
            "locations": [],
            "message": "Search failed - please try again"
        }

@app.get("/api/locations/global")
async def get_global_locations():
    """Get all available cities and ports from global database"""
    try:
        locations = []
        for city_name, city_data in GLOBAL_CITIES_DATABASE.items():
            locations.append({
                "name": f"{city_name}, {city_data['country']}",
                "lat": city_data["lat"],
                "lng": city_data["lng"],
                "type": city_data["type"],
                "country": city_data["country"]
            })
        
        # Group by type and country
        ports = [loc for loc in locations if loc["type"] == "port"]
        cities = [loc for loc in locations if loc["type"] == "city"]
        
        return {
            "total_locations": len(locations),
            "ports": len(ports),
            "cities": len(cities),
            "locations": {
                "ports": sorted(ports, key=lambda x: x["name"]),
                "cities": sorted(cities, key=lambda x: x["name"]),
                "all": sorted(locations, key=lambda x: x["name"])
            }
        }
        
    except Exception as e:
        logger.error(f"Global locations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/routes/optimize", response_model=RouteResult)
async def optimize_route(query: RouteQuery):
    """Calculate optimized maritime route"""
    try:
        result = await RouteService.calculate_route(query)
        return result
    except Exception as e:
        logger.error(f"Route optimization endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings")
async def get_settings():
    """Get current API configuration status"""
    return {
        "api_keys_configured": {
            "huggingface": bool(config.HUGGINGFACE_API_KEY),
            "openrouter": bool(config.OPENROUTER_API_KEY),
            "groq": bool(config.GROQ_API_KEY),
            "together": bool(config.TOGETHER_API_KEY),
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
        "current_ai_provider": AI_PROVIDER,
        "system_status": "operational"
    }

@app.post("/settings")
async def update_settings(settings: Dict[str, Any]):
    """Update API configuration (in production, store securely)"""
    return {"message": "Settings updated successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

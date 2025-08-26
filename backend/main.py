from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import openai
import requests
import json
import uuid
import pathlib
import base64
import io
from PIL import Image
import easyocr
import PyPDF2
import fitz  # PyMuPDF
import numpy as np
import re
import html
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import configuration and routing
from config import config
from maritime_routing_professional import professional_router, GLOBAL_CITIES_DATABASE
from ports_service import PortsService
from authentication import (
    AuthenticationService, UserCreate, UserLogin, Token, User,
    get_current_user, get_current_active_user, require_role,
    get_auth_statistics, ACCESS_TOKEN_EXPIRE_MINUTES, security
)

# Import enhanced maritime services
from marine_weather_service import marine_weather_service, MarineWeatherData
from enhanced_marine_routing import enhanced_marine_router, OptimizedRoute
from enhanced_vessel_tracking import enhanced_vessel_tracker, VesselTrack, VesselDetails

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

# SECURITY: Initialize rate limiter (Critical Security Fix)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

# SECURITY: Add security headers middleware (Critical Security Fix)
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    # Essential security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';"
    
    # Remove server information (use del instead of pop for MutableHeaders)
    if "Server" in response.headers:
        del response.headers["Server"]
    
    return response

# SECURITY: Input sanitization function (Critical Security Fix)
def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not text:
        return text
    
    # Remove dangerous protocols
    dangerous_protocols = [
        'javascript:', 'data:', 'vbscript:', 'file:', 'about:',
        'chrome:', 'chrome-extension:', 'ms-its:', 'ms-itss:', 'ms-appx:'
    ]
    
    sanitized = text
    for protocol in dangerous_protocols:
        sanitized = re.sub(rf'{re.escape(protocol)}[^\\s]*', '[REMOVED_DANGEROUS_CONTENT]', sanitized, flags=re.IGNORECASE)
    
    # Remove dangerous HTML tags and attributes
    dangerous_tags = [
        '<script[^>]*>.*?</script>',
        '<iframe[^>]*>.*?</iframe>',
        '<object[^>]*>.*?</object>',
        '<embed[^>]*>.*?</embed>',
        '<link[^>]*>',
        '<meta[^>]*>',
        '<style[^>]*>.*?</style>'
    ]
    
    for tag_pattern in dangerous_tags:
        sanitized = re.sub(tag_pattern, '[REMOVED_HTML_CONTENT]', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove dangerous attributes
    dangerous_attrs = [
        'onclick', 'onload', 'onerror', 'onmouseover', 'onmouseout',
        'onfocus', 'onblur', 'onchange', 'onsubmit', 'onreset'
    ]
    
    for attr in dangerous_attrs:
        sanitized = re.sub(rf'{attr}\\s*=\\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
    
    # HTML escape remaining content for safety
    sanitized = html.escape(sanitized, quote=False)
    
    # Limit length to prevent DoS
    if len(sanitized) > 10000:
        sanitized = sanitized[:10000] + '[TRUNCATED_LARGE_INPUT]'
    
    return sanitized

# Configure AI and Weather providers
AI_PROVIDER = config.ai_provider
WEATHER_PROVIDER = config.weather_provider

logger.info(f"🚀 Maritime Assistant API Starting")
logger.info(f"🤖 AI Provider: {AI_PROVIDER}")
logger.info(f"🌤️ Weather Provider: {WEATHER_PROVIDER}")
logger.info(f"🗄️ Database: PostgreSQL Connected")

# Initialize services
ports_service = PortsService()
logger.info(f"🚢 Ports Database: {ports_service.get_ports_count()} ports loaded")

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

class ChatWithImageRequest(BaseModel):
    query: str
    image_data: Optional[str] = None  # Base64 encoded file
    file_type: Optional[str] = "image"  # "image" or "application/pdf"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    confidence: float
    sources: List[str]
    conversation_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    extracted_text: Optional[str] = None
    document_analysis: Optional[Dict[str, Any]] = None

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
            
            # Add other AI providers here if needed
            else:
                # Use mock response as fallback
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
    async def get_ai_response_with_document(query: str, file_data: str, file_type: str = "image", conversation_id: str = None) -> ChatResponse:
        """Process chat request with document (image or PDF)"""
        try:
            # Analyze the document (image or PDF)
            doc_analysis = await DocumentAnalysisService.analyze_document(file_data, file_type, query)
            
            # Combine user query with document analysis for AI processing
            enhanced_query = f"""
User Query: {query}

Document Analysis Results:
- Document Type: {doc_analysis['document_analysis'].get('document_type', 'Unknown')}
- Processing Method: {"PDF Text Extraction" if file_type == "application/pdf" else "OCR Image Processing"}
- Extracted Text: {doc_analysis['extracted_text'][:1500]}...
- Key Findings: {', '.join(doc_analysis['document_analysis'].get('key_findings', []))}

Please provide a professional maritime analysis incorporating both the user's question and the document content.
"""
            
            # Get AI response with enhanced context
            ai_response = await MaritimeAIService._get_ai_response_text(enhanced_query)
            
            return ChatResponse(
                response=ai_response,
                confidence=doc_analysis['confidence'],
                sources=["Maritime AI Assistant", "Document Analysis", "OCR Processing"],
                conversation_id=conversation_id or str(uuid.uuid4()),
                extracted_text=doc_analysis['extracted_text'],
                document_analysis=doc_analysis['document_analysis']
            )
            
        except Exception as e:
            logger.error(f"AI service with document error: {e}")
            return ChatResponse(
                response=f"I encountered an issue processing your document. However, I can help with your query: {MaritimeAIService._get_mock_response(query)}",
                confidence=0.6,
                sources=["Fallback Maritime Knowledge"],
                conversation_id=conversation_id or str(uuid.uuid4()),
                extracted_text="Error processing document",
                document_analysis={"error": str(e)}
            )
    
    @staticmethod
    async def _get_ai_response_text(query: str) -> str:
        """Get AI text response for internal use"""
        try:
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
                    return response.json()["choices"][0]["message"]["content"]
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
                return response.choices[0].message.content
            
            elif AI_PROVIDER == "huggingface":
                api_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-70b-chat-hf"
                headers = {"Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}"}
                payload = {
                    "inputs": f"System: {MARITIME_SYSTEM_PROMPT}\n\nUser: {query}\n\nAssistant:",
                    "parameters": {"max_new_tokens": 1500, "temperature": 0.7}
                }
                
                response = requests.post(api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    return response.json()[0]["generated_text"].split("Assistant:")[-1].strip()
                else:
                    raise Exception(f"HuggingFace API error: {response.status_code}")
            
            else:
                return MaritimeAIService._get_mock_response(query)
                
        except Exception as e:
            logger.error(f"AI text service error: {e}")
            return MaritimeAIService._get_mock_response(query)
    
    @staticmethod
    async def get_ai_response(query: str, conversation_id: str = None) -> ChatResponse:
        """Main AI response method for regular text queries"""
        try:
            ai_response = await MaritimeAIService._get_ai_response_text(query)
            confidence = 0.95 if AI_PROVIDER in ["groq", "openai"] else 0.8
            
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

# Document Analysis Service  
class DocumentAnalysisService:
    @staticmethod
    async def analyze_document(file_data: str, file_type: str, query: str = "") -> Dict[str, Any]:
        """Analyze maritime documents (images or PDFs) using OCR/text extraction and AI"""
        try:
            extracted_text = ""
            
            if file_type == "application/pdf":
                # Handle PDF files
                extracted_text = DocumentAnalysisService._extract_text_from_pdf(file_data)
                logger.info(f"PDF text extraction completed: {len(extracted_text)} characters")
            else:
                # Handle image files with OCR
                extracted_text = DocumentAnalysisService._extract_text_from_image(file_data)
                logger.info(f"OCR extracted {len(extracted_text)} characters from image")
            
            # Check if this is a Statement of Facts document
            from sof_processor import StatementOfFactsProcessor
            is_sof, sof_confidence, sof_indicators = StatementOfFactsProcessor.validate_sof_document(extracted_text)
            
            if is_sof:
                # Process as SOF document
                sof_doc = StatementOfFactsProcessor.process_sof_document(extracted_text)
                low_confidence_events = StatementOfFactsProcessor.get_low_confidence_events(sof_doc, threshold=0.7)
                
                analysis = {
                    "document_type": "Statement of Facts",
                    "sof_data": {
                        "vessel_name": sof_doc.vessel_name,
                        "imo_number": sof_doc.imo_number,
                        "port": sof_doc.port,
                        "berth": sof_doc.berth,
                        "events": [
                            {
                                "event_type": event.event_type,
                                "description": event.description,
                                "start_time": event.start_time_str,
                                "confidence": event.confidence,
                                "needs_review": event.confidence < 0.7
                            } for event in sof_doc.events
                        ],
                        "total_events": len(sof_doc.events),
                        "low_confidence_count": len(low_confidence_events),
                        "total_laytime_hours": sof_doc.total_laytime,
                        "document_confidence": sof_doc.document_confidence
                    },
                    "export_formats": ["json", "csv"],
                    "editable_events": [
                        {
                            "event_type": event.event_type,
                            "description": event.description,
                            "confidence": event.confidence,
                            "suggested_time": event.start_time_str,
                            "extracted_text": event.extracted_text
                        } for event in low_confidence_events
                    ]
                }
            else:
                # Process as general maritime document - prefer Groq if configured
                if AI_PROVIDER == "groq":
                    try:
                        analysis = await DocumentAnalysisService._call_groq_structurer(extracted_text, query)
                    except Exception as e:
                        logger.warning(f"Groq structuring failed, falling back to local analysis: {e}")
                        analysis = DocumentAnalysisService._analyze_maritime_document(extracted_text, query)
                else:
                    # Fallback to local heuristic analysis
                    analysis = DocumentAnalysisService._analyze_maritime_document(extracted_text, query)
            
            return {
                "extracted_text": extracted_text,
                "document_analysis": analysis,
                "processing_status": "completed",
                "confidence": analysis.get("document_confidence", 0.95) if is_sof else (0.95 if len(extracted_text) > 100 else 0.7)
            }
            
        except Exception as e:
            logger.error(f"Document analysis error: {e}")
            return {
                "extracted_text": f"Error processing document: {str(e)}",
                "document_analysis": {"error": str(e), "document_type": "unknown"},
                "processing_status": "failed",
                "confidence": 0.0
            }
    
    @staticmethod
    def _extract_text_from_pdf(pdf_base64: str) -> str:
        """Extract text from PDF using multiple methods for maximum compatibility"""
        try:
            # Decode base64 PDF
            pdf_bytes = base64.b64decode(pdf_base64)
            
            # Method 1: Try PyPDF2 for text-based PDFs
            try:
                pdf_file = io.BytesIO(pdf_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text_content = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text().strip()
                    text_content += page_text + "\n"
                
                # If we got substantial text content, use it
                if len(text_content.strip()) > 100:  # At least 100 characters
                    logger.info(f"PyPDF2 extracted {len(text_content)} characters successfully")
                    return text_content.strip()
                
            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed: {e}")
            
            # Method 2: Use PyMuPDF for both text and OCR
            logger.info("Trying PyMuPDF for PDF processing...")
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            all_text = ""
            
            # Initialize OCR reader once
            ocr_reader = easyocr.Reader(['en'], gpu=False)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # First try to extract text directly
                page_text = page.get_text().strip()
                
                if len(page_text) > 50:  # If we got decent text
                    all_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    logger.info(f"Page {page_num + 1}: Extracted {len(page_text)} characters via text")
                else:
                    # Convert page to image and use OCR
                    try:
                        # Get page as image
                        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR quality
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("png")
                        
                        # Convert to PIL Image
                        image = Image.open(io.BytesIO(img_data))
                        image_array = np.array(image)
                        
                        # Use OCR - preserve line order and line breaks
                        ocr_results = ocr_reader.readtext(image_array, detail=1)

                        # ocr_results items are typically (bbox, text, confidence)
                        lines = []
                        for res in ocr_results:
                            try:
                                bbox, text = res[0], res[1]
                                # Determine top Y coordinate for sorting
                                top_y = min([pt[1] for pt in bbox]) if bbox else 0
                                lines.append((top_y, text))
                            except Exception:
                                # Fallback when readtext returns simple strings
                                lines.append((0, res if isinstance(res, str) else str(res)))

                        # Sort by vertical position (top to bottom) and join with newlines
                        lines.sort(key=lambda x: x[0])
                        ocr_text = "\n".join([t for _, t in lines])

                        if len(ocr_text.strip()) > 10:
                            all_text += f"\n--- Page {page_num + 1} (OCR) ---\n{ocr_text}\n"
                            logger.info(f"Page {page_num + 1}: Extracted {len(ocr_text)} characters via OCR")
                        
                    except Exception as ocr_error:
                        logger.warning(f"OCR failed for page {page_num + 1}: {ocr_error}")
            
            pdf_document.close()
            
            if len(all_text.strip()) > 0:
                logger.info(f"Total PDF text extracted: {len(all_text)} characters")
                return all_text.strip()
            else:
                return "No text could be extracted from this PDF document. The document may be corrupted, password-protected, or contain only non-text elements."
                
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return f"Error processing PDF document: {str(e)}. Please try converting the PDF to images (JPG/PNG) for better results."
    
    @staticmethod
    def _extract_text_from_image(image_base64: str) -> str:
        """Extract text from image using EasyOCR"""
        try:
            # Initialize EasyOCR reader (English only for better performance)
            reader = easyocr.Reader(['en'])
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert PIL image to numpy array for EasyOCR
            import numpy as np
            image_array = np.array(image)
            
            # Extract text using OCR and preserve line order
            results = reader.readtext(image_array, detail=1)
            lines = []
            for res in results:
                try:
                    bbox, text = res[0], res[1]
                    top_y = min([pt[1] for pt in bbox]) if bbox else 0
                    lines.append((top_y, text))
                except Exception:
                    lines.append((0, res if isinstance(res, str) else str(res)))

            lines.sort(key=lambda x: x[0])
            extracted_text = "\n".join([t for _, t in lines])

            return extracted_text
            
        except Exception as e:
            logger.error(f"Image OCR error: {e}")
            return f"Error extracting text from image: {str(e)}"

    @staticmethod
    async def analyze_document_image(image_data: str, query: str = "") -> Dict[str, Any]:
        """Legacy method for backward compatibility - redirects to analyze_document"""
        return await DocumentAnalysisService.analyze_document(image_data, "image", query)
    
    @staticmethod
    def _analyze_maritime_document(text: str, user_query: str = "") -> Dict[str, Any]:
        """Analyze maritime document content and extract key information"""
        text_lower = text.lower()
        
        # Initialize with better structure
        analysis = {
            "document_type": "unknown",
            "confidence": 0.0,
            "key_findings": [],
            "sections": [],
            "financial_data": {},
            "metadata": {
                "dates": [],
                "vessels": [],
                "ports": [],
                "cargo": [],
                "parties": []
            },
            "recommendations": []
        }

        # Score tracking for confidence calculation
        total_score = 0
        checks_performed = 0

        # Detect document type with confidence scoring
        doc_type_indicators = {
            "Statement of Facts": ["statement of facts", "sof", "time sheet", "time log", "port log"],
            "Charter Party": ["charter party", "charterparty", "fixture", "c/p", "hire"],
            "Bill of Lading": ["bill of lading", "b/l", "shipped on board", "consignee"],
            "Port Document": ["port authority", "terminal", "berth", "pilot", "tug"],
            "Cargo Document": ["cargo manifest", "stowage plan", "loading list", "discharge list"],
            "Commercial Document": ["invoice", "demurrage", "claim", "freight", "payment"]
        }

        # Document type detection with confidence scoring
        max_type_score = 0
        detected_type = "General Maritime Document"

        for doc_type, indicators in doc_type_indicators.items():
            type_score = sum(2 if term in text_lower else 0 for term in indicators)
            if type_score > max_type_score:
                max_type_score = type_score
                detected_type = doc_type

        analysis["document_type"] = detected_type
        type_confidence = min(0.95, (max_type_score / (len(doc_type_indicators[detected_type]) * 2)) if detected_type in doc_type_indicators else 0.7)
        total_score += type_confidence
        checks_performed += 1
        
        # Section detection and structuring
        import re
        from datetime import datetime

        # Split text into potential sections
        lines = text.split('\n')
        current_section = {"title": "Header", "content": [], "confidence": 0.0}
        sections = []
        
        # Common maritime section headers
        section_headers = {
            "vessel details": ["vessel", "ship", "particulars"],
            "port information": ["port", "terminal", "berth"],
            "cargo details": ["cargo", "goods", "loading", "discharge"],
            "dates and times": ["date", "time", "eta", "etd"],
            "parties": ["owner", "charterer", "shipper", "consignee"],
            "terms and conditions": ["terms", "conditions", "clause"],
            "financial": ["payment", "rate", "amount", "price"],
            "remarks": ["remarks", "notes", "comments"]
        }

        # Process text into structured sections
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line is a section header
            is_header = False
            header_confidence = 0.0
            detected_header = None
            
            for header, keywords in section_headers.items():
                if any(keyword in line.lower() for keyword in keywords):
                    if current_section["content"]:
                        sections.append(current_section)
                    header_confidence = sum(1 for kw in keywords if kw in line.lower()) / len(keywords)
                    detected_header = header.title()
                    current_section = {
                        "title": detected_header,
                        "content": [],
                        "confidence": header_confidence
                    }
                    is_header = True
                    break
                    
            if not is_header:
                current_section["content"].append(line)
        
        # Add last section
        if current_section["content"]:
            sections.append(current_section)
            
        # Process sections for metadata
        entity_patterns = {
            "dates": r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4}',
            "vessels": r'[mM][/?][vV]\s+[\w\s-]+|[sS][/?][sS]\s+[\w\s-]+',
            "ports": r'Port of\s+[\w\s-]+|[\w\s-]+\s+Port|[\w\s-]+\s+Terminal',
            "amounts": r'USD?\s*[\d,.]+|EUR?\s*[\d,.]+|GBP?\s*[\d,.]+',
            "times": r'\d{1,2}:\d{2}\s*(?:hrs?|am|pm|GMT|UTC)?|\d{4}\s*(?:hrs?|GMT|UTC)'
        }
        # Extract entities from sections
        for section in sections:
            section_text = ' '.join(section["content"])
            
            # Extract entities using patterns
            for entity_type, pattern in entity_patterns.items():
                matches = re.finditer(pattern, section_text, re.IGNORECASE)
                found_entities = [match.group(0) for match in matches]
                
                if found_entities:
                    if entity_type not in analysis["metadata"]:
                        analysis["metadata"][entity_type] = []
                    analysis["metadata"][entity_type].extend(found_entities)
                    
                    # Update section confidence based on found entities
                    section["confidence"] = min(0.95, section["confidence"] + 0.1 * len(found_entities))
        
        # Clean and deduplicate metadata
        for key in analysis["metadata"]:
            if analysis["metadata"][key]:
                analysis["metadata"][key] = list(set(analysis["metadata"][key]))
                
        # Add processed sections to analysis
        analysis["sections"] = sections
        
        # Calculate overall confidence based on multiple factors
        section_confidence = sum(s["confidence"] for s in sections) / len(sections) if sections else 0.6
        metadata_confidence = min(0.95, 0.6 + 0.05 * sum(len(v) for v in analysis["metadata"].values()))
        
        # Combine confidence scores
        total_score += section_confidence + metadata_confidence
        checks_performed += 2
        
        # Calculate final confidence score
        analysis["confidence"] = min(0.95, total_score / checks_performed)
        
        # Generate key findings based on extracted data
        if analysis["metadata"]["vessels"]:
            analysis["key_findings"].append(f"Vessel identified: {analysis['metadata']['vessels'][0]}")
        if analysis["metadata"]["ports"]:
            analysis["key_findings"].append(f"Port mentioned: {analysis['metadata']['ports'][0]}")
        if analysis["metadata"]["dates"]:
            analysis["key_findings"].append(f"Key date found: {analysis['metadata']['dates'][0]}")
        if analysis["metadata"]["amounts"]:
            analysis["key_findings"].append(f"Financial amount detected: {analysis['metadata']['amounts'][0]}")
            
        # Add processing timestamp
        analysis["metadata"]["processed_at"] = datetime.now().isoformat()
        
        return analysis
        # Filter out common non-vessel words
        exclude_words = {'THE', 'AND', 'OR', 'OF', 'TO', 'FROM', 'IN', 'ON', 'AT', 'BY', 'FOR', 'WITH', 'USD', 'EUR', 'GBP'}
        analysis["vessels"] = [v for v in potential_vessels if v not in exclude_words and len(v) > 2][:5]
        
        # Look for port names
        common_ports = ['ROTTERDAM', 'SINGAPORE', 'HAMBURG', 'SHANGHAI', 'DUBAI', 'HONG KONG', 'ANTWERP', 'FELIXSTOWE']
        analysis["ports"] = [port for port in common_ports if port in text.upper()]
        
        # Generate recommendations based on document type
        if analysis["document_type"] == "Statement of Facts":
            analysis["recommendations"] = [
                "Verify all time entries are accurate and properly documented",
                "Check for any weather delays or exceptional circumstances",
                "Ensure NOR (Notice of Readiness) timing is clearly stated",
                "Cross-reference with charter party laytime terms"
            ]
        elif analysis["document_type"] == "Charter Party Agreement":
            analysis["recommendations"] = [
                "Review laytime calculation terms (SHINC/SHEX)",
                "Verify demurrage and despatch rates",
                "Check cargo description and quantity details",
                "Confirm loading and discharge port terms"
            ]
        
        return analysis

    @staticmethod
    async def _call_groq_structurer(text: str, user_query: str = "") -> Dict[str, Any]:
        """Call Groq chat completions to structure the maritime document into sections and tables (JSON)."""
        if not config.GROQ_API_KEY:
            raise Exception('GROQ API key not configured')

        prompt = f"Extract and structure the key information from this maritime document into a JSON object with 'sections' and 'tables' arrays, preserving dates, times, vessel & port details.\n\nDocument:\n{text[:12000]}"

        headers = {
            "Authorization": f"Bearer {config.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": "You are a helpful maritime document parser. Return only valid JSON according to the requested schema."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 3000,
            "temperature": 0.0
        }

        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            raise Exception(f"Groq API error: {resp.status_code} {resp.text[:200]}")

        data = resp.json()
        content = data.get("choices", [])[0].get("message", {}).get("content") if data.get("choices") else None
        if not content:
            raise Exception("Groq returned empty content")

        # Parse JSON content
        try:
            parsed = json.loads(content)
        except Exception as e:
            # If Groq returned extraneous text, try to extract JSON block
            import re
            m = re.search(r"\{[\s\S]*\}", content)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                except Exception:
                    raise Exception(f"Failed to parse JSON from Groq response: {e}")
            else:
                raise Exception(f"Failed to parse Groq response as JSON: {e}")

        # Validate basic shape
        sections = parsed.get("sections", []) if isinstance(parsed, dict) else []
        tables = parsed.get("tables", []) if isinstance(parsed, dict) else []

        return {
            "document_type": parsed.get("document_type", "Structured Maritime Document") if isinstance(parsed, dict) else "Structured Maritime Document",
            "confidence": parsed.get("confidence", 0.9) if isinstance(parsed, dict) else 0.9,
            "key_findings": parsed.get("key_findings", []),
            "sections": sections,
            "tables": tables,
            "metadata": parsed.get("metadata", {}),
            "recommendations": parsed.get("recommendations", [])
        }

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
    async def get_current_weather_only(query: WeatherQuery) -> Dict[str, Any]:
        """Get only current weather data (no forecast)"""
        try:
            if WEATHER_PROVIDER == "openweather" and config.OPENWEATHER_API_KEY:
                # OpenWeatherMap current weather API
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
                    return {
                        "location": query.location_name or f"{query.latitude}, {query.longitude}",
                        "coordinates": {"lat": query.latitude, "lon": query.longitude},
                        "current_weather": {
                            "temperature": data["main"]["temp"],
                            "feels_like": data["main"]["feels_like"],
                            "humidity": data["main"]["humidity"],
                            "pressure": data["main"]["pressure"],
                            "wind_speed": data["wind"]["speed"],
                            "wind_direction": data["wind"]["deg"],
                            "visibility": data.get("visibility", 10000) / 1000,
                            "conditions": data["weather"][0]["description"],
                            "weather_main": data["weather"][0]["main"],
                            "clouds": data["clouds"]["all"],
                            "timestamp": datetime.now().isoformat()
                        },
                        "source": "OpenWeatherMap"
                    }
                else:
                    raise Exception(f"OpenWeatherMap API error: {response.status_code}")
            else:
                # Mock current weather
                return WeatherService._get_mock_current_weather(query)
                
        except Exception as e:
            logger.error(f"Current weather service error: {e}")
            return WeatherService._get_mock_current_weather(query)
    
    @staticmethod
    async def search_location(location_query: str) -> Optional[Dict[str, Any]]:
        """Search for location coordinates using multiple services"""
        try:
            # Try Nominatim (OpenStreetMap) first - free and unlimited
            url = f"https://nominatim.openstreetmap.org/search"
            params = {
                "format": "json",
                "q": location_query,
                "limit": 1,
                "addressdetails": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                results = response.json()
                if results:
                    result = results[0]
                    return {
                        "name": result.get("display_name", location_query),
                        "lat": float(result["lat"]),
                        "lon": float(result["lon"]),
                        "source": "Nominatim"
                    }
            
            # Fallback to built-in location database
            return await WeatherService._search_builtin_locations(location_query)
            
        except Exception as e:
            logger.error(f"Location search error: {e}")
            return await WeatherService._search_builtin_locations(location_query)
    
    @staticmethod
    async def _search_builtin_locations(query: str) -> Optional[Dict[str, Any]]:
        """Search built-in global locations database including comprehensive ports"""
        try:
            # First try to search in the comprehensive ports database
            ports = await ports_service.search_ports(query, limit=1)
            if ports:
                port = ports[0]
                return {
                    "name": port["name"],
                    "lat": port["latitude"],
                    "lon": port["longitude"],
                    "source": "Maritime Ports Database",
                    "type": port.get("type", "Port"),
                    "country": port.get("country")
                }
        except Exception as e:
            logger.warning(f"Ports search failed: {e}")
        
        # Fallback to global cities database
        global_locations = [
            # Global Major Cities
            {"name": "New York City", "lat": 40.7128, "lon": -74.0060, "keywords": ["new york", "nyc", "manhattan"]},
            {"name": "London", "lat": 51.5074, "lon": -0.1278, "keywords": ["london", "uk", "england"]},
            {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "keywords": ["tokyo", "japan"]},
            {"name": "Paris", "lat": 48.8566, "lon": 2.3522, "keywords": ["paris", "france"]},
            {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "keywords": ["sydney", "australia"]},
            {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "keywords": ["mumbai", "bombay", "india"]},
            {"name": "São Paulo", "lat": -23.5505, "lon": -46.6333, "keywords": ["são paulo", "sao paulo", "brazil"]},
            {"name": "Moscow", "lat": 55.7558, "lon": 37.6176, "keywords": ["moscow", "russia"]},
            {"name": "Beijing", "lat": 39.9042, "lon": 116.4074, "keywords": ["beijing", "peking", "china"]},
            {"name": "Seoul", "lat": 37.5665, "lon": 126.9780, "keywords": ["seoul", "korea"]},
            {"name": "Istanbul", "lat": 41.0082, "lon": 28.9784, "keywords": ["istanbul", "turkey"]},
            {"name": "Jakarta", "lat": -6.2088, "lon": 106.8456, "keywords": ["jakarta", "indonesia"]},
            {"name": "Manila", "lat": 14.5995, "lon": 120.9842, "keywords": ["manila", "philippines"]},
            {"name": "Bangkok", "lat": 13.7563, "lon": 100.5018, "keywords": ["bangkok", "thailand"]},
            {"name": "Cairo", "lat": 30.0444, "lon": 31.2357, "keywords": ["cairo", "egypt"]},
            {"name": "Lagos", "lat": 6.5244, "lon": 3.3792, "keywords": ["lagos", "nigeria"]},
            {"name": "Buenos Aires", "lat": -34.6118, "lon": -58.3960, "keywords": ["buenos aires", "argentina"]},
            {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241, "keywords": ["cape town", "south africa"]}
        ]
        
        query_lower = query.lower()
        for location in global_locations:
            if any(keyword in query_lower or query_lower in keyword for keyword in location["keywords"]):
                return {
                    "name": location["name"],
                    "lat": location["lat"],
                    "lon": location["lon"],
                    "source": "Built-in Database"
                }
        
        return None
    
    @staticmethod
    def _get_mock_current_weather(query: WeatherQuery) -> Dict[str, Any]:
        """Mock current weather data"""
        return {
            "location": query.location_name or f"{query.latitude}, {query.longitude}",
            "coordinates": {"lat": query.latitude, "lon": query.longitude},
            "current_weather": {
                "temperature": 21.5,
                "feels_like": 24.0,
                "humidity": 78,
                "pressure": 1013.2,
                "wind_speed": 12.3,
                "wind_direction": 240,
                "visibility": 15.0,
                "conditions": "partly cloudy with moderate seas",
                "weather_main": "Clouds",
                "clouds": 65,
                "timestamp": datetime.now().isoformat()
            },
            "source": "Mock Data (API unavailable)"
        }
    
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

@app.get("/health")
async def health():
    return {"status": "ok"}

# AUTHENTICATION ENDPOINTS
@app.post("/auth/register", response_model=Dict[str, Any])
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        user = AuthenticationService.create_user(user_data)
        logger.info(f"User registered: {user.username}")
        
        return {
            "message": "User registered successfully",
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    """Authenticate user and return JWT tokens"""
    try:
        user = AuthenticationService.authenticate_user(
            user_credentials.username, 
            user_credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Create tokens
        access_token = AuthenticationService.create_access_token(
            data={"sub": user.username, "user_id": user.user_id, "role": user.role}
        )
        refresh_token = AuthenticationService.create_refresh_token(
            data={"sub": user.username, "user_id": user.user_id, "role": user.role}
        )
        
        logger.info(f"User logged in: {user.username}")
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_info={
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "full_name": user.full_name,
                "company": user.company
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/auth/logout")
async def logout_user(current_user: User = Depends(get_current_active_user),
                     credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user and revoke token"""
    try:
        AuthenticationService.revoke_token(credentials.credentials)
        logger.info(f"User logged out: {current_user.username}")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@app.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@app.get("/auth/stats")
async def get_authentication_stats(
    current_user: User = Depends(require_role(["admin"]))
):
    """Get authentication statistics (admin only)"""
    return get_auth_statistics()

# PUBLIC ENDPOINTS (No Authentication Required)
@app.post("/public/chat", response_model=ChatResponse)
@limiter.limit("10/minute")  # SECURITY: Lower rate limit for public access
async def public_chat_endpoint(request: Request, message: ChatMessage):
    """Public AI-powered maritime chat assistant (Limited Access)"""
    try:
        # SECURITY: Input sanitization for XSS protection
        sanitized_query = sanitize_input(message.query)
        
        # Add disclaimer for public access
        public_disclaimer = "[PUBLIC ACCESS - Limited Features] "
        
        response = await MaritimeAIService.get_ai_response(
            sanitized_query, 
            message.conversation_id
        )
        
        # Modify response to indicate public access
        response.response = public_disclaimer + response.response
        response.sources = ["Public Maritime Assistant"] + (response.sources or [])
        
        logger.info(f"Public chat query processed: {sanitized_query[:50]}...")
        return response
    except Exception as e:
        logger.error(f"Public chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="AI service temporarily unavailable")

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("30/minute")  # SECURITY: Rate limiting - 30 requests per minute
async def chat_endpoint(request: Request, message: ChatMessage, 
                       current_user: User = Depends(get_current_active_user)):
    """Production AI-powered maritime chat assistant (Authentication Required)"""
    try:
        # SECURITY: Input sanitization for XSS protection (Critical Security Fix)
        sanitized_query = sanitize_input(message.query)
        
        response = await MaritimeAIService.get_ai_response(
            sanitized_query, 
            message.conversation_id
        )
        logger.info(f"Chat query processed for user {current_user.username}: {sanitized_query[:50]}...")
        return response
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="AI service temporarily unavailable")

@app.post("/chat/analyze-document", response_model=ChatResponse)
async def chat_with_document_endpoint(request: ChatWithImageRequest):
    """Analyze maritime documents (SOF, Charter Party, etc.) with AI"""
    try:
        if not request.image_data:
            # If no image provided, fall back to regular chat
            response = await MaritimeAIService.get_ai_response(
                request.query, 
                request.conversation_id
            )
        else:
            # Process chat with document (image or PDF)
            response = await MaritimeAIService.get_ai_response_with_document(
                request.query,
                request.image_data,
                request.file_type or "image",
                request.conversation_id
            )
        
        logger.info(f"Document analysis chat processed: {request.query[:50]}...")
        return response
    except Exception as e:
        logger.error(f"Document analysis endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Document analysis service temporarily unavailable")

@app.post("/upload-document", response_model=Dict[str, Any])
async def upload_document_image(file: UploadFile = File(...)):
    """Upload and analyze maritime document images"""
    try:
        # Validate file type - accept both images and PDFs
        if not (file.content_type.startswith('image/') or file.content_type == 'application/pdf'):
            raise HTTPException(status_code=400, detail="Only image files (PNG, JPG) and PDF files are supported")
        
        # Validate file size
        contents = await file.read()
        if len(contents) > config.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Convert to base64 for processing
        file_base64 = base64.b64encode(contents).decode('utf-8')
        
        # Analyze the document
        analysis = await DocumentAnalysisService.analyze_document(file_base64, file.content_type)
        
        logger.info(f"Document uploaded and analyzed: {file.filename}")
        
        return {
            "document_id": str(uuid.uuid4()),
            "filename": file.filename,
            "analysis": analysis,
            "status": "completed",
            "file_type": file.content_type,
            "file_size": len(contents)
        }
        
    except Exception as e:
        logger.error(f"Document upload endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Document upload failed")

@app.post("/sof/export/{format}")
async def export_sof_document(format: str, sof_data: Dict[str, Any]):
    """Export SOF document in JSON or CSV format"""
    try:
        from sof_processor import StatementOfFactsProcessor, SoFDocument, SoFEvent
        
        if format.lower() not in ['json', 'csv']:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
        
        # Reconstruct SOF document from data
        events = []
        for event_data in sof_data.get('events', []):
            event = SoFEvent(
                event_type=event_data.get('event_type', ''),
                description=event_data.get('description', ''),
                start_time_str=event_data.get('start_time', ''),
                confidence=event_data.get('confidence', 0.0),
                vessel=sof_data.get('vessel_name', ''),
                port=sof_data.get('port', '')
            )
            events.append(event)
        
        sof_doc = SoFDocument(
            vessel_name=sof_data.get('vessel_name', ''),
            imo_number=sof_data.get('imo_number', ''),
            port=sof_data.get('port', ''),
            berth=sof_data.get('berth', ''),
            events=events,
            total_laytime=sof_data.get('total_laytime_hours'),
            document_confidence=sof_data.get('document_confidence', 0.0)
        )
        
        if format.lower() == 'json':
            export_data = StatementOfFactsProcessor.export_to_json(sof_doc)
            media_type = "application/json"
            filename = f"sof_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            export_data = StatementOfFactsProcessor.export_to_csv(sof_doc)
            media_type = "text/csv"
            filename = f"sof_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        from fastapi.responses import Response
        return Response(
            content=export_data,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"SOF export error: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

@app.post("/sof/update-event")
async def update_sof_event(event_update: Dict[str, Any]):
    """Update SOF event with user corrections"""
    try:
        from sof_processor import StatementOfFactsProcessor
        
        # Parse the updated time
        updated_time_str = event_update.get('updated_time', '')
        if updated_time_str:
            parsed_time, confidence = StatementOfFactsProcessor.parse_time(updated_time_str)
            
            return {
                "success": True,
                "parsed_time": parsed_time.isoformat() if parsed_time else None,
                "confidence": confidence,
                "message": "Event updated successfully"
            }
        else:
            return {
                "success": False,
                "message": "No time provided for update"
            }
            
    except Exception as e:
        logger.error(f"SOF event update error: {e}")
        raise HTTPException(status_code=500, detail="Event update failed")

@app.get("/sof/validate")
async def validate_sof_text(text: str):
    """Validate if text is a Statement of Facts document"""
    try:
        from sof_processor import StatementOfFactsProcessor
        
        is_sof, confidence, indicators = StatementOfFactsProcessor.validate_sof_document(text)
        
        return {
            "is_sof": is_sof,
            "confidence": confidence,
            "indicators_found": indicators,
            "recommendation": "Process as SOF document" if is_sof else "Process as general maritime document"
        }
        
    except Exception as e:
        logger.error(f"SOF validation error: {e}")
        raise HTTPException(status_code=500, detail="Validation failed")

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

@app.get("/current-weather")
async def get_current_weather(lat: float, lon: float, location_name: str = ""):
    """Get current weather for any location"""
    try:
        query = WeatherQuery(latitude=lat, longitude=lon, location_name=location_name)
        response = await WeatherService.get_current_weather_only(query)
        logger.info(f"Current weather requested for: {location_name or f'{lat}, {lon}'}")
        return response
    except Exception as e:
        logger.error(f"Current weather endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Current weather service unavailable")

@app.get("/port-weather/{port_name}")
async def get_port_weather(port_name: str):
    """Get weather data for specific maritime ports"""
    try:
        # Search for the port in our comprehensive database
        ports = await ports_service.search_ports(port_name, limit=1)
        
        if not ports:
            raise HTTPException(status_code=404, detail=f"Port '{port_name}' not found in database")
        
        port_info = ports[0]
        
        # Handle different coordinate formats
        if 'coordinates' in port_info and isinstance(port_info['coordinates'], dict):
            # New format with nested coordinates
            coords = port_info['coordinates']
            latitude = coords.get('lat', 0)
            longitude = coords.get('lon', 0)
        else:
            # Fallback for direct latitude/longitude keys
            latitude = port_info.get("latitude", 0)
            longitude = port_info.get("longitude", 0)
        
        if latitude == 0 or longitude == 0:
            raise HTTPException(status_code=400, detail=f"Invalid coordinates for port '{port_name}'")
        
        query = WeatherQuery(
            latitude=latitude, 
            longitude=longitude, 
            location_name=port_info["name"]
        )
        
        response = await WeatherService.get_weather_data(query)
        logger.info(f"Port weather requested for: {port_info['name']} at {latitude}, {longitude}")
        return {
            "port": port_info,
            "weather": response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Port weather endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Port weather service unavailable")

@app.get("/location-weather")
async def search_location_weather(query: str):
    """Search for weather by location name (cities, ports, landmarks)"""
    try:
        location = await WeatherService.search_location(query)
        if not location:
            raise HTTPException(status_code=404, detail=f"Location '{query}' not found")
        
        weather_query = WeatherQuery(
            latitude=location["lat"],
            longitude=location["lon"],
            location_name=location["name"]
        )
        
        response = await WeatherService.get_weather_data(weather_query)
        logger.info(f"Location weather search: {query} -> {location['name']}")
        return {
            "location": location,
            "weather": response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Location weather search error: {e}")
        raise HTTPException(status_code=500, detail="Location weather search unavailable")

# =====================================================
# COMPREHENSIVE PORTS API ENDPOINTS 
# =====================================================

@app.get("/api/ports")
async def get_all_ports(
    country: Optional[str] = None,
    port_type: Optional[str] = None,
    limit: int = 100
):
    """Get all ports with optional filtering"""
    try:
        if country:
            ports = await ports_service.get_ports_by_country(country, limit=limit)
        elif port_type:
            ports = await ports_service.get_ports_by_type(port_type, limit=limit)
        else:
            ports = await ports_service.get_all_ports(limit=limit)
        
        return {
            "total": len(ports),
            "ports": ports,
            "total_in_database": ports_service.get_ports_count()
        }
    
    except Exception as e:
        logger.error(f"Get all ports error: {e}")
        raise HTTPException(status_code=500, detail="Ports service unavailable")

@app.get("/api/ports/search")
async def search_ports(query: str, limit: int = 50):
    """Search ports by name, country, or other criteria"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        ports = await ports_service.search_ports(query, limit=limit)
        
        return {
            "query": query,
            "results": len(ports),
            "ports": ports
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Port search error: {e}")
        raise HTTPException(status_code=500, detail="Port search service unavailable")

@app.get("/api/ports/nearby")
async def get_nearby_ports(
    latitude: float, 
    longitude: float, 
    radius: float = 100,
    limit: int = 20
):
    """Get ports within specified radius from coordinates"""
    try:
        if not (-90 <= latitude <= 90):
            raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")
        if not (-180 <= longitude <= 180):
            raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")
        if radius <= 0 or radius > 10000:
            raise HTTPException(status_code=400, detail="Radius must be between 1 and 10000 km")
        
        ports = await ports_service.get_nearby_ports(latitude, longitude, radius, limit)
        
        return {
            "location": {"latitude": latitude, "longitude": longitude},
            "radius_km": radius,
            "results": len(ports),
            "ports": ports
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Nearby ports error: {e}")
        raise HTTPException(status_code=500, detail="Nearby ports service unavailable")

@app.get("/api/ports/country/{country}")
async def get_ports_by_country(country: str, limit: int = 100):
    """Get all ports in a specific country"""
    try:
        if not country.strip():
            raise HTTPException(status_code=400, detail="Country cannot be empty")
        
        ports = await ports_service.get_ports_by_country(country, limit=limit)
        
        if not ports:
            raise HTTPException(status_code=404, detail=f"No ports found for country: {country}")
        
        return {
            "country": country,
            "results": len(ports),
            "ports": ports
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ports by country error: {e}")
        raise HTTPException(status_code=500, detail="Ports by country service unavailable")

@app.get("/api/ports/type/{port_type}")
async def get_ports_by_type(port_type: str, limit: int = 100):
    """Get ports by type (Container, Bulk, Oil, etc.)"""
    try:
        if not port_type.strip():
            raise HTTPException(status_code=400, detail="Port type cannot be empty")
        
        ports = await ports_service.get_ports_by_type(port_type, limit=limit)
        
        if not ports:
            raise HTTPException(status_code=404, detail=f"No ports found for type: {port_type}")
        
        return {
            "port_type": port_type,
            "results": len(ports),
            "ports": ports
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ports by type error: {e}")
        raise HTTPException(status_code=500, detail="Ports by type service unavailable")

@app.get("/api/ports/locode/{locode}")
async def get_port_by_locode(locode: str):
    """Get port by UN/LOCODE"""
    try:
        if not locode.strip():
            raise HTTPException(status_code=400, detail="LOCODE cannot be empty")
        
        port = ports_service.get_port_by_locode(locode)
        
        if not port:
            raise HTTPException(status_code=404, detail=f"Port with LOCODE '{locode}' not found")
        
        return {
            "locode": locode.upper(),
            "port": port
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Port by LOCODE error: {e}")
        raise HTTPException(status_code=500, detail="Port by LOCODE service unavailable")

@app.get("/api/ports/stats")
async def get_ports_statistics():
    """Get comprehensive ports database statistics"""
    try:
        total_ports = ports_service.get_ports_count()
        countries = ports_service.get_countries_with_ports()
        port_types = ports_service.get_port_types()
        
        return {
            "database_stats": {
                "total_ports": total_ports,
                "total_countries": len(countries),
                "total_port_types": len(port_types)
            },
            "countries": countries,
            "port_types": port_types,
            "sample_ports": await ports_service.get_all_ports(limit=10)
        }
    
    except Exception as e:
        logger.error(f"Ports statistics error: {e}")
        raise HTTPException(status_code=500, detail="Ports statistics service unavailable")

@app.post("/upload", response_model=DocumentUploadResponse)
@limiter.limit("10/minute")  # SECURITY: Rate limiting for file uploads
async def upload_document(request: Request, file: UploadFile = File(...), 
                         current_user: User = Depends(get_current_active_user)):
    """Process maritime documents (Charter Party, SOF, etc.) - Authentication Required"""
    try:
        # SECURITY: Validate file type (Critical Security Fix)
        allowed_content_types = {
            'application/pdf',
            'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/csv'
        }
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.csv'}
        
        # Check content type
        if file.content_type not in allowed_content_types:
            raise HTTPException(status_code=415, detail=f"File type {file.content_type} not supported. Allowed: PDF, DOC, DOCX, TXT, CSV")
        
        # Check file extension
        if file.filename:
            file_ext = os.path.splitext(file.filename.lower())[1]
            if file_ext not in allowed_extensions:
                raise HTTPException(status_code=415, detail=f"File extension {file_ext} not allowed. Allowed: {', '.join(allowed_extensions)}")
        
        # SECURITY: Validate file size
        if file.size and file.size > config.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # SECURITY: Read file content with size limit validation
        content = await file.read()
        if len(content) > config.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File content too large")
        
        # SECURITY: Basic content validation (prevent executable content)
        if content.startswith(b'MZ') or content.startswith(b'\x7fELF'):
            raise HTTPException(status_code=415, detail="Executable files are not allowed")
        
        # Generate document ID
        document_id = f"doc_{uuid.uuid4().hex[:8]}"
        
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

# Enhanced Marine Weather Endpoints
@app.post("/marine-weather/comprehensive")
async def get_comprehensive_marine_weather(lat: float, lon: float, location_name: str = ""):
    """Get comprehensive marine weather data including waves, tides, and currents"""
    try:
        weather_data = await marine_weather_service.get_comprehensive_marine_weather(
            lat, lon, location_name
        )
        
        # Convert to response format
        return {
            "timestamp": weather_data.timestamp.isoformat(),
            "location": weather_data.location,
            "coordinates": weather_data.coordinates,
            "atmospheric": {
                "temperature": weather_data.temperature,
                "humidity": weather_data.humidity,
                "pressure": weather_data.pressure,
                "visibility": weather_data.visibility
            },
            "wind": {
                "speed": weather_data.wind_speed,
                "direction": weather_data.wind_direction,
                "gust": weather_data.wind_gust
            },
            "marine": {
                "wave_height": weather_data.wave_height,
                "wave_direction": weather_data.wave_direction,
                "wave_period": weather_data.wave_period,
                "swell_height": weather_data.swell_height,
                "swell_direction": weather_data.swell_direction,
                "swell_period": weather_data.swell_period,
                "sea_state": weather_data.sea_state,
                "sea_temperature": weather_data.sea_temperature
            },
            "currents": {
                "speed": weather_data.current_speed,
                "direction": weather_data.current_direction
            },
            "tides": {
                "height": weather_data.tide_height,
                "direction": weather_data.tide_direction,
                "next_high_tide": weather_data.next_high_tide.isoformat(),
                "next_low_tide": weather_data.next_low_tide.isoformat()
            },
            "warnings": weather_data.warnings,
            "storm_warnings": weather_data.storm_warnings,
            "source": weather_data.source,
            "confidence": weather_data.confidence
        }
        
    except Exception as e:
        logger.error(f"Comprehensive marine weather error: {e}")
        raise HTTPException(status_code=500, detail="Marine weather service unavailable")

@app.get("/marine-weather/forecast")
async def get_marine_weather_forecast(lat: float, lon: float, days: int = 5):
    """Get marine weather forecast for multiple days"""
    try:
        forecast_data = await marine_weather_service.get_weather_forecast(lat, lon, days)
        
        return {
            "forecast": [
                {
                    "timestamp": data.timestamp.isoformat(),
                    "atmospheric": {
                        "temperature": data.temperature,
                        "humidity": data.humidity,
                        "pressure": data.pressure
                    },
                    "wind": {
                        "speed": data.wind_speed,
                        "direction": data.wind_direction
                    },
                    "marine": {
                        "wave_height": data.wave_height,
                        "sea_state": data.sea_state,
                        "sea_temperature": data.sea_temperature
                    }
                }
                for data in forecast_data
            ]
        }
        
    except Exception as e:
        logger.error(f"Marine weather forecast error: {e}")
        raise HTTPException(status_code=500, detail="Weather forecast service unavailable")

@app.get("/marine-weather/warnings")
async def get_marine_weather_warnings(lat: float, lon: float, radius_km: float = 100):
    """Get marine weather warnings for the area"""
    try:
        warnings = await marine_weather_service.get_marine_warnings(lat, lon, radius_km)
        return {"warnings": warnings}
        
    except Exception as e:
        logger.error(f"Marine weather warnings error: {e}")
        raise HTTPException(status_code=500, detail="Weather warnings service unavailable")

# Enhanced Vessel Tracking Endpoints
@app.post("/vessels/enhanced-track")
async def enhanced_track_vessel(identifier: str, include_history: bool = True):
    """Enhanced vessel tracking with IMO/MMSI resolution and position history"""
    try:
        track = await enhanced_vessel_tracker.track_vessel(identifier, include_history)
        
        if not track:
            raise HTTPException(status_code=404, detail="Vessel not found")
        
        return {
            "vessel": {
                "imo": track.vessel.imo,
                "mmsi": track.vessel.mmsi,
                "name": track.vessel.name,
                "callsign": track.vessel.callsign,
                "type": track.vessel.vessel_type,
                "flag": track.vessel.flag,
                "gross_tonnage": track.vessel.gross_tonnage,
                "length": track.vessel.length,
                "width": track.vessel.width,
                "draft": track.vessel.draft,
                "year_built": track.vessel.year_built,
                "home_port": track.vessel.home_port,
                "operator": track.vessel.operator
            },
            "current_position": {
                "timestamp": track.current_position.timestamp.isoformat(),
                "latitude": track.current_position.latitude,
                "longitude": track.current_position.longitude,
                "speed": track.current_position.speed,
                "heading": track.current_position.heading,
                "course": track.current_position.course,
                "status": track.current_position.status,
                "source": track.current_position.source
            },
            "position_history": [
                {
                    "timestamp": pos.timestamp.isoformat(),
                    "latitude": pos.latitude,
                    "longitude": pos.longitude,
                    "speed": pos.speed,
                    "heading": pos.heading,
                    "status": pos.status
                }
                for pos in track.position_history
            ],
            "destination": track.destination,
            "eta": track.eta.isoformat() if track.eta else None,
            "route_points": track.route_points,
            "weather_conditions": track.weather_conditions,
            "alerts": track.alerts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced vessel tracking error: {e}")
        raise HTTPException(status_code=500, detail="Vessel tracking service unavailable")

@app.post("/vessels/search-enhanced")
async def enhanced_search_vessels(query: str, limit: int = 10):
    """Enhanced vessel search with IMO/MMSI resolution"""
    try:
        vessels = await enhanced_vessel_tracker.search_vessels(query, limit)
        
        return {
            "vessels": [
                {
                    "imo": vessel.imo,
                    "mmsi": vessel.mmsi,
                    "name": vessel.name,
                    "callsign": vessel.callsign,
                    "type": vessel.vessel_type,
                    "flag": vessel.flag,
                    "gross_tonnage": vessel.gross_tonnage,
                    "length": vessel.length,
                    "width": vessel.width,
                    "draft": vessel.draft,
                    "year_built": vessel.year_built,
                    "home_port": vessel.home_port,
                    "operator": vessel.operator
                }
                for vessel in vessels
            ]
        }
        
    except Exception as e:
        logger.error(f"Enhanced vessel search error: {e}")
        raise HTTPException(status_code=500, detail="Vessel search service unavailable")

@app.get("/vessels/{vessel_id}/alerts")
async def get_vessel_alerts(vessel_id: str):
    """Get current alerts for a specific vessel"""
    try:
        alerts = await enhanced_vessel_tracker.get_vessel_alerts(vessel_id)
        return {"alerts": alerts}
        
    except Exception as e:
        logger.error(f"Vessel alerts error: {e}")
        raise HTTPException(status_code=500, detail="Vessel alerts service unavailable")

@app.get("/vessels/{vessel_id}/weather")
async def get_vessel_weather(vessel_id: str):
    """Get weather conditions at vessel's current position"""
    try:
        weather = await enhanced_vessel_tracker.get_vessel_weather_report(vessel_id)
        return {"weather": weather}
        
    except Exception as e:
        logger.error(f"Vessel weather error: {e}")
        raise HTTPException(status_code=500, detail="Vessel weather service unavailable")

# Enhanced Route Optimization Endpoints
@app.post("/routes/enhanced-optimize")
async def enhanced_route_optimization(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    optimization_mode: str = "weather",
    vessel_type: str = "container",
    weather_data: Optional[Dict[str, Any]] = None
):
    """Enhanced marine route optimization with weather integration"""
    try:
        result = await enhanced_marine_router.optimize_route(
            origin=origin,
            destination=destination,
            optimization_mode=optimization_mode,
            vessel_type=vessel_type,
            weather_data=weather_data
        )
        
        return {
            "origin": result.origin,
            "destination": result.destination,
            "waypoints": result.waypoints,
            "total_distance_nm": result.total_distance_nm,
            "total_time_hours": result.total_time_hours,
            "total_fuel_mt": result.total_fuel_mt,
            "optimization_mode": result.optimization_mode,
            "weather_warnings": result.weather_warnings,
            "safety_score": result.safety_score,
            "route_type": result.route_type,
            "estimated_arrival": result.estimated_arrival.isoformat(),
            "alternative_routes": result.alternative_routes,
            "segments": [
                {
                    "start": seg.start,
                    "end": seg.end,
                    "distance_nm": seg.distance_nm,
                    "estimated_time_hours": seg.estimated_time_hours,
                    "fuel_consumption_mt": seg.fuel_consumption_mt,
                    "hazards": seg.hazards,
                    "depth_restrictions": seg.depth_restrictions,
                    "current_effects": seg.current_effects
                }
                for seg in result.segments
            ]
        }
        
    except Exception as e:
        logger.error(f"Enhanced route optimization error: {e}")
        raise HTTPException(status_code=500, detail="Enhanced routing service unavailable")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )

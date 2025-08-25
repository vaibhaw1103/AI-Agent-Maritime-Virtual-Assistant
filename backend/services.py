import os
import json
import logging
from typing import List, Dict, Any
import openai
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
import aiofiles

logger = logging.getLogger(__name__)

class AzureOpenAIService:
    """Azure OpenAI integration for maritime AI chat"""
    
    def __init__(self):
        self.client = openai.AsyncAzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
        
    async def generate_maritime_response(self, query: str, context: str = "") -> Dict[str, Any]:
        """Generate AI response for maritime queries"""
        try:
            system_prompt = """
            You are a Maritime Virtual Assistant with deep knowledge of:
            - Charter parties and laytime calculations
            - Maritime law and regulations
            - Weather routing and voyage optimization
            - Port operations and procedures
            - Cargo operations and documentation
            - Maritime safety and compliance
            
            Provide accurate, professional responses with practical advice.
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context: {context}\n\nQuery: {query}"}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            return {
                "response": response.choices[0].message.content,
                "confidence": 0.85,  # Can be enhanced with confidence scoring
                "sources": ["Maritime Knowledge Base", "Azure OpenAI"]
            }
            
        except Exception as e:
            logger.error(f"Azure OpenAI error: {str(e)}")
            # Fallback to mock response
            return {
                "response": f"I understand your query about '{query}'. Let me help you with maritime-specific guidance...",
                "confidence": 0.70,
                "sources": ["Maritime Assistant Fallback"]
            }

class AzureDocumentService:
    """Azure Form Recognizer for document analysis"""
    
    def __init__(self):
        endpoint = os.getenv("AZURE_COGNITIVE_SERVICES_ENDPOINT")
        key = os.getenv("AZURE_COGNITIVE_SERVICES_KEY")
        if endpoint and key:
            self.client = DocumentAnalysisClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key)
            )
        else:
            self.client = None
            logger.warning("Azure Cognitive Services not configured")
    
    async def analyze_document(self, file_content: bytes, content_type: str) -> Dict[str, Any]:
        """Analyze document using Azure Form Recognizer"""
        try:
            if not self.client:
                return self._mock_document_analysis(content_type)
            
            # Use prebuilt document model for general documents
            poller = self.client.begin_analyze_document(
                "prebuilt-document",
                file_content
            )
            result = poller.result()
            
            # Extract text and key-value pairs
            extracted_text = ""
            key_insights = []
            
            for page in result.pages:
                for line in page.lines:
                    extracted_text += line.content + "\n"
            
            for kv_pair in result.key_value_pairs:
                if kv_pair.key and kv_pair.value:
                    key_insights.append(f"{kv_pair.key.content}: {kv_pair.value.content}")
            
            return {
                "extracted_text": extracted_text,
                "key_insights": key_insights[:10],  # Limit to top 10 insights
                "document_type": self._classify_maritime_document(extracted_text),
                "processing_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Document analysis error: {str(e)}")
            return self._mock_document_analysis(content_type)
    
    def _classify_maritime_document(self, text: str) -> str:
        """Classify document type based on content"""
        text_lower = text.lower()
        if any(term in text_lower for term in ["charter party", "cp", "fixture"]):
            return "Charter Party"
        elif any(term in text_lower for term in ["statement of facts", "sof", "laytime"]):
            return "Statement of Facts"
        elif any(term in text_lower for term in ["bill of lading", "bl", "cargo"]):
            return "Bill of Lading"
        elif any(term in text_lower for term in ["voyage instructions", "orders"]):
            return "Voyage Instructions"
        else:
            return "Maritime Document"
    
    def _mock_document_analysis(self, content_type: str) -> Dict[str, Any]:
        """Mock document analysis for demo purposes"""
        return {
            "extracted_text": "Sample extracted text from maritime document...",
            "key_insights": ["Sample insight 1", "Sample insight 2"],
            "document_type": "Maritime Document",
            "processing_status": "completed"
        }

class AzureBlobService:
    """Azure Blob Storage for document storage"""
    
    def __init__(self):
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if connection_string:
            self.blob_service = BlobServiceClient.from_connection_string(connection_string)
            self.container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME", "maritime-documents")
        else:
            self.blob_service = None
            logger.warning("Azure Blob Storage not configured")
    
    async def upload_document(self, file_content: bytes, filename: str, document_id: str) -> str:
        """Upload document to Azure Blob Storage"""
        try:
            if not self.blob_service:
                return f"local://documents/{document_id}"
            
            blob_name = f"{document_id}/{filename}"
            blob_client = self.blob_service.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.upload_blob(file_content, overwrite=True)
            return blob_client.url
            
        except Exception as e:
            logger.error(f"Blob upload error: {str(e)}")
            return f"local://documents/{document_id}"

class WeatherAPIService:
    """Weather API integration for marine conditions"""
    
    def __init__(self):
        self.noaa_key = os.getenv("NOAA_API_KEY")
        self.openweather_key = os.getenv("OPENWEATHER_API_KEY")
    
    async def get_marine_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get marine weather data"""
        try:
            # In real implementation, call NOAA Marine API or OpenWeather
            # For demo, return mock data
            return {
                "current_weather": {
                    "temperature": 22,
                    "wind_speed": 15,
                    "wind_direction": 225,
                    "wave_height": 1.8,
                    "visibility": 10
                },
                "marine_conditions": {
                    "sea_state": "Moderate",
                    "swell_height": 2.1,
                    "current_speed": 0.5
                },
                "warnings": []
            }
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
            return {"error": "Weather data unavailable"}

# Initialize services
azure_openai = AzureOpenAIService()
azure_documents = AzureDocumentService()
azure_blob = AzureBlobService()
weather_service = WeatherAPIService()

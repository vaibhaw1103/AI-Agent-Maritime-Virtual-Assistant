# Maritime Virtual Assistant Backend

This is the FastAPI backend for the Maritime Virtual Assistant, designed for hackathon development with full Azure integration support.

## 🚢 Features

- **AI Chat Agent**: Maritime domain-specific Q&A using Azure OpenAI
- **Document Processing**: PDF/Word analysis with Azure Cognitive Services  
- **Weather Integration**: Marine weather data from NOAA/OpenWeather APIs
- **Recommendations Engine**: AI-powered voyage optimization suggestions
- **Authentication**: JWT-based security with Azure AD support
- **Database**: SQLAlchemy with PostgreSQL/MySQL support
- **File Storage**: Azure Blob Storage integration
- **Caching**: Redis for high-performance data retrieval

## 🛠 Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: SQLAlchemy ORM with PostgreSQL/MySQL
- **AI/ML**: Azure OpenAI, Azure Cognitive Services
- **Storage**: Azure Blob Storage
- **Cache**: Redis
- **Deployment**: Docker + Azure App Service ready

## 📋 Prerequisites

- Python 3.11+
- Redis server
- Azure account (for production features)
- API keys for weather services

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone and navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# For hackathon demo, you can start without Azure keys
```

### 3. Database Setup

```bash
# Create database tables
python -c "from database import create_tables; create_tables()"
```

### 4. Run Development Server

```bash
# Start the API server
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --port 8000
```

The API will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

## 📡 API Endpoints

### Core Endpoints

- `GET /` - Health check and API info
- `POST /chat` - AI maritime assistant chat
- `POST /upload` - Document upload and analysis  
- `POST /weather` - Weather and marine conditions
- `POST /recommendations` - Voyage recommendations
- `GET /settings` - API configuration status

### Example Usage

#### Chat with AI Assistant
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is standard laytime for bulk cargo loading?",
    "mode": "text"
  }'
```

#### Upload Document
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@charter_party.pdf"
```

#### Get Weather Data
```bash
curl -X POST "http://localhost:8000/weather" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 51.9244,
    "longitude": 4.4777
  }'
```

## 🔧 Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/maritime_db

# Redis
REDIS_URL=redis://localhost:6379

# Azure Services
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_COGNITIVE_SERVICES_KEY=your_key
AZURE_STORAGE_CONNECTION_STRING=your_connection

# Weather APIs
NOAA_API_KEY=your_noaa_key
OPENWEATHER_API_KEY=your_openweather_key
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build Docker image
docker build -t maritime-assistant-backend .

# Run container
docker run -d \
  --name maritime-backend \
  -p 8000:8000 \
  --env-file .env \
  maritime-assistant-backend
```

### Docker Compose (with Redis)

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - redis
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

## ☁️ Azure Deployment

### Azure App Service

```bash
# Login to Azure
az login

# Create resource group
az group create --name maritime-assistant-rg --location eastus

# Create App Service plan
az appservice plan create \
  --name maritime-plan \
  --resource-group maritime-assistant-rg \
  --sku B1 --is-linux

# Create web app
az webapp create \
  --name maritime-assistant-api \
  --resource-group maritime-assistant-rg \
  --plan maritime-plan \
  --runtime "PYTHON|3.11"

# Deploy code
az webapp deploy \
  --name maritime-assistant-api \
  --resource-group maritime-assistant-rg \
  --src-path .
```

## 🔍 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Manual Testing
- Use the interactive API docs at `/docs`
- Import the Postman collection from `tests/postman_collection.json`
- Test endpoints with sample maritime data

## 🎯 Hackathon Demo Features

### Pre-loaded Sample Data
- Maritime port database
- Sample charter party clauses  
- Mock weather data
- Standard laytime calculations

### Mock Services
- Fallback responses when APIs are unavailable
- Sample document processing results
- Realistic maritime scenarios

### Quick Demo Scenarios
1. **Laytime Query**: "Calculate laytime for 48 hours SHINC"
2. **Weather Check**: Upload coordinates for Rotterdam
3. **Document Upload**: Process sample charter party PDF
4. **Voyage Planning**: Get recommendations for loading stage

## 🚨 Production Considerations

### Security
- Enable HTTPS in production
- Use Azure Key Vault for secrets
- Implement rate limiting
- Add comprehensive logging

### Performance  
- Configure Redis caching
- Use connection pooling
- Implement async database queries
- Add monitoring and metrics

### Scalability
- Use Azure Container Instances
- Configure auto-scaling
- Implement load balancing
- Add health checks

## 📚 Maritime Domain Knowledge

### Supported Queries
- **Laytime & Demurrage**: Calculations, terms, disputes
- **Charter Parties**: Clause interpretation, obligations
- **Weather Routing**: Optimal routes, safety considerations  
- **Port Operations**: Procedures, documentation, berth planning
- **Cargo Operations**: Loading/discharge, documentation
- **Maritime Law**: Regulations, compliance, best practices

### Document Types
- Charter Party agreements
- Statement of Facts (SoF)
- Bills of Lading
- Voyage Instructions
- Port documentation
- Weather routing reports

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🆘 Support

For hackathon support and questions:
- Check the `/docs` endpoint for API documentation
- Review sample requests in `tests/` directory
- Use mock data for quick testing
- All endpoints return meaningful sample data

---

**Built for Maritime Industry Hackathon** 🏆

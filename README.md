# 🌊 AquaIntel - AI-Powered Maritime Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15.2.4-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-red.svg)](https://fastapi.tiangolo.com/)

AquaIntel is a comprehensive AI-powered platform designed specifically for the maritime industry. It combines advanced document processing, weather forecasting, route optimization, and intelligent chat assistance to help shipping professionals, port operators, and voyage planners streamline their operations.

## 🚀 Features

### 📄 Document Intelligence
- **SOF Processing**: Automated Statement of Facts document analysis and structuring
- **Charter Party Analysis**: AI-powered contract document processing
- **Bill of Lading Processing**: Intelligent cargo document handling
- **OCR & Text Extraction**: Advanced optical character recognition for scanned documents
- **Document Classification**: Automatic categorization of maritime documents

### 🌤️ Weather & Navigation
- **Marine Weather Dashboard**: Real-time weather data and forecasts
- **Port Weather Information**: Detailed weather conditions for specific ports
- **Route Optimization**: AI-powered maritime routing with weather considerations
- **Vessel Tracking**: Enhanced vessel monitoring and tracking capabilities

### 🗺️ Port Management
- **Comprehensive Port Database**: Global port information and details
- **Port Search & Filtering**: Advanced search capabilities with multiple criteria
- **Port Weather Integration**: Weather data integrated with port information
- **Port Recommendations**: AI-driven port selection suggestions

### 💬 AI Assistant
- **Maritime Chat Assistant**: Specialized AI chatbot for maritime queries
- **Context-Aware Responses**: Intelligent responses based on maritime domain knowledge
- **Document Integration**: Chat assistant with access to processed documents
- **Multi-Provider AI**: Support for Groq, OpenAI, and OpenRouter

### 🔐 Security & Authentication
- **JWT Authentication**: Secure user authentication system
- **Role-Based Access Control**: Different permission levels for users
- **Rate Limiting**: API protection against abuse
- **Input Sanitization**: XSS and injection attack prevention

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 15.2.4 (React 19)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI
- **Maps**: MapLibre GL, Leaflet
- **State Management**: Zustand
- **Forms**: React Hook Form + Zod

### Backend
- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.10+
- **Database**: PostgreSQL (production), SQLite (development)
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT with Python-Jose
- **AI/ML**: OpenAI, Groq, OpenRouter, spaCy, Transformers
- **Document Processing**: PyMuPDF, EasyOCR, Azure Form Recognizer

### Infrastructure
- **Containerization**: Docker support
- **CI/CD**: GitHub Actions
- **Environment**: Environment variable management
- **Logging**: Structured logging with Python logging

## 📋 Prerequisites

- **Node.js**: 18+ (LTS recommended)
- **Python**: 3.10+
- **PostgreSQL**: 12+ (for production)
- **Package Manager**: npm, yarn, or pnpm

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/aquaintel.git
cd aquaintel
```

### 2. Frontend Setup

```bash
# Install dependencies
npm install
# or
pnpm install
# or
yarn install

# Start development server
npm run dev
# or
pnpm dev
# or
yarn dev
```

The frontend will be available at `http://localhost:3000`

### 3. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`

### 4. Environment Configuration

Create `.env` files in both root and backend directories:

**Root `.env`:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=AquaIntel
```

**Backend `.env`:**
```env
# Database
DATABASE_URL=sqlite:///./ports.db
# For production: DATABASE_URL=postgresql://user:password@localhost:5432/aquaintel

# AI Providers (at least one required)
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# Security
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Azure Services (optional)
AZURE_STORAGE_CONNECTION_STRING=your_azure_storage_connection_string
AZURE_FORM_RECOGNIZER_ENDPOINT=your_azure_form_recognizer_endpoint
AZURE_FORM_RECOGNIZER_KEY=your_azure_form_recognizer_key

# Weather APIs (optional)
METEO_MATICS_API_KEY=your_meteo_matics_api_key
STORMGLASS_API_KEY=your_stormglass_api_key
```

### 5. Database Setup

For development (SQLite):
```bash
# The database will be created automatically on first run
```

For production (PostgreSQL):
```bash
# Run the PostgreSQL setup script
python setup_postgres.py

# Run migrations
alembic upgrade head
```

## 📁 Project Structure

```
aquaintel/
├── app/                    # Next.js app directory
│   ├── api/               # API routes
│   ├── auth/              # Authentication pages
│   ├── chat/              # Chat interface
│   ├── documents/         # Document management
│   ├── ports/             # Port information
│   ├── weather/           # Weather dashboard
│   └── recommendations/   # AI recommendations
├── backend/               # FastAPI backend
│   ├── services/          # Business logic services
│   ├── migrations/        # Database migrations
│   └── main.py           # FastAPI application entry point
├── components/            # Reusable React components
│   └── ui/               # UI component library
├── lib/                   # Utility libraries
├── public/               # Static assets
├── styles/               # Global styles
└── types/                # TypeScript type definitions
```

## 🔧 Development

### Running Tests

```bash
# Frontend tests
npm test

# Backend tests
cd backend
pytest
```

### Code Quality

```bash
# Frontend linting
npm run lint

# Backend formatting
cd backend
black .
isort .
```

### Building for Production

```bash
# Frontend build
npm run build

# Backend (FastAPI is production-ready)
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 📚 API Documentation

Once the backend is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow the existing code style and conventions
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/aquaintel/issues)
- **Documentation**: Check the [Wiki](https://github.com/yourusername/aquaintel/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/aquaintel/discussions)

## 🙏 Acknowledgments

- [Next.js](https://nextjs.org/) for the frontend framework
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Tailwind CSS](https://tailwindcss.com/) for styling
- [Radix UI](https://www.radix-ui.com/) for accessible components
- [MapLibre GL](https://maplibre.org/) for mapping capabilities

## 📊 Project Status

- ✅ Core functionality implemented
- ✅ Document processing working
- ✅ Weather integration active
- ✅ Port database populated
- ✅ Authentication system secure
- 🔄 Continuous improvements
- 🔄 Additional AI features

---

**Made with ❤️ for the maritime industry**

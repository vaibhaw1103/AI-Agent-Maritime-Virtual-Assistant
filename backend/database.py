from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# PostgreSQL connection with fallback to SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://maritime_user:maritime_pass@localhost:5432/maritime_assistant_db")

# Configure engine with PostgreSQL optimizations
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300
    )
else:
    # SQLite fallback for development
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, unique=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    document_type = Column(String)
    extracted_text = Column(Text)
    key_insights = Column(Text)  # JSON string
    processing_status = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

class ChatConversation(Base):
    __tablename__ = "chat_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    messages = relationship("ChatMessage", back_populates="conversation")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("chat_conversations.conversation_id"))
    query = Column(Text)
    response = Column(Text)
    confidence = Column(Float)
    sources = Column(Text)  # JSON string
    mode = Column(String)  # "text" or "voice"
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("ChatConversation", back_populates="messages")

class WeatherData(Base):
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    weather_data = Column(Text)  # JSON string
    requested_at = Column(DateTime, default=datetime.utcnow)

class VoyageRecommendation(Base):
    __tablename__ = "voyage_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    voyage_id = Column(String)
    stage = Column(String)
    recommendations = Column(Text)  # JSON string
    priority_actions = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

class APISettings(Base):
    __tablename__ = "api_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String, unique=True, index=True)
    setting_value = Column(Text)
    is_encrypted = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

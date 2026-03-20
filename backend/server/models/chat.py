from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MessageHistory(BaseModel):
    role: str
    text: str

class DocumentInfo(BaseModel):
    id: str
    title: str
    file_type: str  # "pdf", "image", "text"
    download_url: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[MessageHistory]] = None

class ChatResponse(BaseModel):
    source: str  # "database" or "gemini"
    answer: str
    category: Optional[str] = None
    documents: Optional[List[DocumentInfo]] = None

class FAQCreate(BaseModel):
    question: str
    answer: str
    category: str
    keywords: List[str]
    document_ids: Optional[List[str]] = None

class FAQInDB(FAQCreate):
    id: str = Field(alias="_id")
    created_at: datetime
    
class FAQResponse(BaseModel):
    id: str
    question: str
    answer: str
    category: str
    keywords: List[str]
    created_at: datetime
    document_ids: Optional[List[str]] = None

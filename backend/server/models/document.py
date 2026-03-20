from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DocumentResponse(BaseModel):
    id: str
    title: str
    file_type: str
    file_path: str
    branch: Optional[str] = None
    semester: Optional[int] = None
    subject: Optional[str] = None
    year: Optional[int] = None
    uploaded_at: datetime

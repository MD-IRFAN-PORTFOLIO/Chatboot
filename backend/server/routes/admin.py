from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import List, Optional
from pydantic import BaseModel
from bson import ObjectId
import os

from server.database import (
    admin_collection, faq_collection, documents_collection,
    users_collection, prompts_collection, api_keys_collection,
    feedback_collection, activity_logs_collection, chat_history_collection
)
from server.models.admin import AdminCreate, AdminInDB, Token
from server.models.admin_extended import UserProfile, PromptConfig, APIKeyConfig, ActivityLog, DashboardStats
from server.models.chat import FAQCreate, FAQResponse
from server.models.document import DocumentResponse
from server.utils.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from server.middleware.auth import get_current_admin
from server.utils.file_extract import extract_text_from_pdf, extract_text_from_txt, extract_text_from_image

router = APIRouter(prefix="/admin", tags=["Admin"])

class TimetableEntry(BaseModel):
    day: str
    time: str
    subject: str
    branch: str
    semester: int
    room: Optional[str] = ""
    professor: Optional[str] = ""

class FacultyEntry(BaseModel):
    name: str
    qualification: str
    designation: str
    department: str
    about: str
    photo_url: str

@router.post("/register", response_model=Token, description="One-time endpoint to register first admin. You'd normally protect this.")
async def register_admin(admin_data: AdminCreate):
    existing_admin = await admin_collection.find_one({"username": admin_data.username})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    hashed_password = get_password_hash(admin_data.password)
    admin_in_db = AdminInDB(username=admin_data.username, hashed_password=hashed_password)
    
    await admin_collection.insert_one(admin_in_db.model_dump())
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login_admin(form_data: OAuth2PasswordRequestForm = Depends()):
    admin = await admin_collection.find_one({"username": form_data.username})
    if not admin or not verify_password(form_data.password, admin["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/add-faq", response_model=FAQResponse)
async def add_faq(faq_data: FAQCreate, current_admin=Depends(get_current_admin)):
    import datetime
    faq_dict = faq_data.model_dump()
    faq_dict["created_at"] = datetime.datetime.utcnow()
    # Ensure keywords are stored in lowercase for easier matching
    faq_dict["keywords"] = [kw.lower() for kw in faq_dict["keywords"]]
    
    result = await faq_collection.insert_one(faq_dict)
    faq_dict["id"] = str(result.inserted_id)
    return faq_dict

@router.get("/all-faq", response_model=List[FAQResponse])
async def get_all_faq(current_admin=Depends(get_current_admin)):
    faqs = []
    cursor = faq_collection.find({})
    async for document in cursor:
        document["id"] = str(document["_id"])
        faqs.append(document)
    return faqs

@router.delete("/delete-faq/{id}")
async def delete_faq(id: str, current_admin=Depends(get_current_admin)):
    result = await faq_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return {"message": "FAQ deleted successfully"}

# --- Timetable Management ---

@router.get("/timetables")
async def get_timetables():
    from server.database import timetable_collection
    cursor = timetable_collection.find({})
    items = await cursor.to_list(length=100)
    for item in items:
        item["id"] = str(item["_id"])
        del item["_id"]
    return items

@router.post("/timetables")
async def add_timetable(entry: TimetableEntry):
    from server.database import timetable_collection
    result = await timetable_collection.insert_one(entry.model_dump())
    return {"message": "Timetable entry added", "id": str(result.inserted_id)}

@router.delete("/timetables/{id}")
async def delete_timetable(id: str):
    from server.database import timetable_collection
    await timetable_collection.delete_one({"_id": ObjectId(id)})
    return {"message": "Entry removed successfully"}

# --- Faculty Management ---

@router.get("/all-faculty")
async def get_all_faculty(current_admin=Depends(get_current_admin)):
    from server.database import faculty_collection
    faculty = []
    cursor = faculty_collection.find({})
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        faculty.append(doc)
    return faculty

@router.post("/add-faculty")
async def add_faculty(
    name: str = Form(...),
    qualification: str = Form(...),
    designation: str = Form(...),
    department: str = Form(...),
    about: str = Form(...),
    file: UploadFile = File(...),
    current_admin=Depends(get_current_admin)
):
    from server.database import faculty_collection
    import os
    import shutil
    import uuid

    # Save Uploaded Photo
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = f"static/uploads/faculty/{filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    photo_url = f"/static/uploads/faculty/{filename}"

    faculty_dict = {
        "name": name,
        "qualification": qualification,
        "designation": designation,
        "department": department,
        "about": about,
        "photo_url": photo_url
    }

    result = await faculty_collection.insert_one(faculty_dict)
    faculty_dict["id"] = str(result.inserted_id)
    return faculty_dict

@router.delete("/delete-faculty/{id}")
async def delete_faculty(id: str, current_admin=Depends(get_current_admin)):
    from server.database import faculty_collection
    import os

    # Optional: Delete file too
    target = await faculty_collection.find_one({"_id": ObjectId(id)})
    if target and target.get("photo_url"):
        try:
            rel_path = target["photo_url"].lstrip("/")
            if os.path.exists(rel_path):
                os.remove(rel_path)
        except: pass

    await faculty_collection.delete_one({"_id": ObjectId(id)})
    return {"message": "Faculty member removed successfully"}

@router.post("/link-document-to-faq/{faq_id}/{document_id}")
async def link_document_to_faq(faq_id: str, document_id: str, current_admin=Depends(get_current_admin)):
    """Link a document (PDF, Image) to an FAQ"""
    try:
        # Verify FAQ exists
        faq = await faq_collection.find_one({"_id": ObjectId(faq_id)})
        if not faq:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        # Verify document exists
        doc = await documents_collection.find_one({"_id": ObjectId(document_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update FAQ with document_id
        if "document_ids" not in faq:
            faq["document_ids"] = []
        
        if document_id not in faq.get("document_ids", []):
            await faq_collection.update_one(
                {"_id": ObjectId(faq_id)},
                {"$push": {"document_ids": document_id}}
            )
        
        return {"message": "Document linked to FAQ successfully", "faq_id": faq_id, "document_id": document_id}
    except Exception as e:
        print(f"Error linking document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-document", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    branch: Optional[str] = Form(None),
    semester: Optional[int] = Form(None),
    subject: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    current_admin=Depends(get_current_admin)
):
    import datetime
    import os
    
    # Save file
    UPLOAD_DIR = "server/uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    contents = await file.read()
    
    with open(file_path, "wb") as f:
        f.write(contents)
        
    extracted_text = ""
    file_type = file.content_type
    
    # Extract based on file type
    if file_type == "application/pdf":
        extracted_text = extract_text_from_pdf(contents)
        doc_type = "pdf"
    elif file_type == "text/plain":
        extracted_text = extract_text_from_txt(contents)
        doc_type = "text"
    elif file_type and file_type.startswith("image/"):
        extracted_text = extract_text_from_image(contents)
        doc_type = "image"
    else:
        doc_type = "unknown"
        
    doc_data = {
        "title": file.filename,
        "file_type": doc_type,
        "file_path": file_path,
        "extracted_text": extracted_text,
        "branch": branch,
        "semester": semester,
        "subject": subject,
        "year": year,
        "uploaded_at": datetime.datetime.utcnow()
    }
    
    result = await documents_collection.insert_one(doc_data)
    doc_data["id"] = str(result.inserted_id)
    
    return doc_data
    
@router.get("/all-documents", response_model=List[DocumentResponse])
async def get_all_documents(current_admin=Depends(get_current_admin)):
    docs = []
    cursor = documents_collection.find({})
    async for document in cursor:
        document["id"] = str(document["_id"])
        docs.append(document)
    return docs

@router.delete("/delete-document/{id}")
async def delete_document(id: str, current_admin=Depends(get_current_admin)):
    try:
        # Get document first to find file path
        doc = await documents_collection.find_one({"_id": ObjectId(id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Remove file from disk
        file_path = doc.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
                
        # Delete from DB
        await documents_collection.delete_one({"_id": ObjectId(id)})
        
        # Also remove references in FAQs
        await faq_collection.update_many(
            {"document_ids": id},
            {"$pull": {"document_ids": id}}
        )
        
        return {"message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# EXTENDED ADMIN MODULES
# ==========================================

@router.get("/dashboard-stats", response_model=DashboardStats)
async def get_dashboard_stats(current_admin=Depends(get_current_admin)):
    import datetime
    
    # 1. Total & Active Users
    total_users = await users_collection.count_documents({})
    active_users = await users_collection.count_documents({"status": "active"})
    
    # 2. Total Conversations
    # Example logic assuming chat_history exists per thread
    total_conversations = await chat_history_collection.count_documents({})
    
    # 3. API Requests Today (Mock logic, would query api_keys_collection)
    today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    api_key_data = await api_keys_collection.find_one({"status": "active"})
    api_requests_today = api_key_data["requests_today"] if api_key_data else 0
    
    return DashboardStats(
        total_users=total_users,
        active_users=active_users,
        total_conversations=total_conversations,
        api_requests_today=api_requests_today,
        error_rate=0.01, # placeholder
        daily_conversations=[{"date": "2026-03-15", "count": 12}, {"date": "2026-03-16", "count": 25}],
        user_growth=[{"date": "2026-03-15", "count": 2}, {"date": "2026-03-16", "count": 5}]
    )

@router.get("/users")
async def get_users(current_admin=Depends(get_current_admin)):
    users = []
    cursor = users_collection.find({}).sort("signup_date", -1).limit(50)
    async for d in cursor:
        d["id"] = str(d["_id"])
        del d["_id"]
        users.append(d)
    return users

@router.delete("/users/{user_id}")
async def block_user(user_id: str, current_admin=Depends(get_current_admin)):
    await users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": "blocked"}})
    await activity_logs_collection.insert_one({"admin_id": current_admin.get("username", "admin"), "action": "blocked_user", "details": user_id})
    return {"status": "success"}

@router.get("/prompts")
async def get_prompt_config(current_admin=Depends(get_current_admin)):
    prompt = await prompts_collection.find_one({})
    if prompt:
        prompt["id"] = str(prompt["_id"])
        del prompt["_id"]
        return prompt
    # Fallback default
    return {"system_prompt": "You are a helpful assistant.", "temperature": 0.7, "response_length": 1000, "creativity_level": "Balanced"}

@router.post("/prompts")
async def update_prompt_config(config: PromptConfig, current_admin=Depends(get_current_admin)):
    import datetime
    config_dict = config.model_dump(exclude={"id"})
    config_dict["updated_at"] = datetime.datetime.utcnow()
    
    await prompts_collection.delete_many({}) # Keep only one active config
    result = await prompts_collection.insert_one(config_dict)
    
    await activity_logs_collection.insert_one({"admin_id": current_admin.get("username", "admin"), "action": "updated_prompts"})
    return {"status": "success", "id": str(result.inserted_id)}

@router.get("/api-keys")
async def get_api_keys(current_admin=Depends(get_current_admin)):
    keys = []
    cursor = api_keys_collection.find({})
    async for k in cursor:
        k["id"] = str(k["_id"])
        del k["_id"]
        # obscure key for frontend
        k["api_key"] = k["api_key"][:4] + "*" * (len(k["api_key"]) - 8) + k["api_key"][-4:] if len(k["api_key"]) > 8 else "***"
        keys.append(k)
    return keys

@router.get("/activity-logs")
async def get_activity_logs(current_admin=Depends(get_current_admin)):
    logs = []
    cursor = activity_logs_collection.find({}).sort("timestamp", -1).limit(100)
    async for l in cursor:
        l["id"] = str(l["_id"])
        del l["_id"]
        logs.append(l)
    return logs


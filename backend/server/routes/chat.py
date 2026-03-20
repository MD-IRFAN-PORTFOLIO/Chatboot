from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Optional
import re
import json
import os
import base64

from server.database import faq_collection, documents_collection
from server.models.chat import ChatRequest, ChatResponse, DocumentInfo
from server.gemini_service import get_gemini_response, stream_gemini_response
from bson import ObjectId

router = APIRouter(tags=["Chat"])

@router.post("/chat")
async def chat_endpoint(
    message: str = Form(...),
    history: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    branch: Optional[str] = Form(None),
    semester: Optional[str] = Form(None)
):
    user_message = message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    image_data = None
    mime_type = None
    
    if file:
        mime_type = file.content_type
        # Only process if it's an image
        if mime_type.startswith("image/"):
            file_content = await file.read()
            image_data = base64.b64encode(file_content).decode("utf-8")
            
    # Parse history if provided as JSON string
    parsed_history = []
    if history:
        try:
            parsed_history = json.loads(history)
        except:
            pass
        
    # 0. Question Paper Flow Handler
    async def handle_qp_flow():
        # Identify Question Paper intent
        is_qp_intent = any(kw in user_message.lower() for kw in ["question paper", "qp", "previous year paper", "exam paper"])
        
        # Identify last assistant message from history
        last_assistant_msg = ""
        if parsed_history:
            for entry in reversed(parsed_history):
                # Gemini history can be {"role": "model", "parts": [{"text": "..."}]} or similar
                # Our frontend sends it as {"role": "model", "text": "..."} or "content"
                role = entry.get("role")
                if role == "model" or role == "assistant":
                    content = ""
                    if "parts" in entry:
                        content = entry.get("parts", [{}])[0].get("text", "")
                    elif "text" in entry:
                        content = entry.get("text", "")
                    else:
                        content = entry.get("content", "")
                    last_assistant_msg = content
                    break

        # FETCH AVAILABLE DATA for this student's branch/semester
        # This helps us identify subjects mentioned in messages
        student_branch = branch
        student_sem = int(semester) if semester and semester.isdigit() else None
        
        db_query = {}
        if student_branch: db_query["branch"] = student_branch
        if student_sem: db_query["semester"] = student_sem
        
        all_docs = await documents_collection.find(db_query).to_list(length=200)
        subjects_in_db = list(set([d.get("subject") for d in all_docs if d.get("subject")]))
        
        mentioned_subject = next((s for s in subjects_in_db if s.lower() in user_message.lower()), None)

        # STATE 1: Initial Request (or no subject known yet)
        if is_qp_intent:
            if not mentioned_subject and "which subject" not in last_assistant_msg.lower() and "available question papers" not in last_assistant_msg.lower():
                return "Which subject question paper do you want?"

        # STATE 2: Subject Provided -> Show Years
        if mentioned_subject or ("which subject" in last_assistant_msg.lower() and not is_qp_intent):
            # If we don't have a mentioned_subject from THIS message, take the whole message as subject
            # unless the user was just asking for QP generally
            subject = mentioned_subject or user_message.strip()
            
            # Find papers for this subject
            qp_query = {"subject": {"$regex": f"^{re.escape(subject)}$", "$options": "i"}}
            if student_branch: qp_query["branch"] = student_branch
            if student_sem: qp_query["semester"] = student_sem
            
            matches = await documents_collection.find(qp_query).to_list(length=50)
            if not matches:
                # If they just typed a random word after "Which subject...", and it's not in DB
                if "which subject" in last_assistant_msg.lower():
                    return f"Sorry, no question papers found for '{subject}'. Please check the subject name."
                return None # Fallback to Gemini if it doesn't look like a direct subject answer
                
            years = sorted(list(set([str(d.get("year")) for d in matches if d.get("year")])), reverse=True)
            if not years:
                # Try to extract year from title if not in field (e.g. QP_CSE_2024.pdf)
                extracted_years = []
                for d in matches:
                    match = re.search(r'(20\d{2})', d.get('title', ''))
                    if match: extracted_years.append(match.group(1))
                years = sorted(list(set(extracted_years)), reverse=True)

            if not years:
                return f"Question papers found for {subject}, but no specific years are registered in the neural matrix. Please check again later."
                
            return f"Available question papers for **{subject}** are:\n" + "\n".join([f"- {y}" for y in years]) + "\n\n**Please select a year.**"

        # STATE 3: Year Selected -> Provide Download Link
        if "please select a year" in last_assistant_msg.lower():
            year_match = re.search(r'(20\d{2})', user_message)
            if not year_match:
                return "Please provide a valid year (e.g., 2024) to retrieve the paper."
            
            target_year = int(year_match.group(1))
            
            # Extract subject from the bot's previous message
            # "Available question papers for **DSA** are..."
            subj_match = re.search(r'for \*\*(.*?)\*\* are', last_assistant_msg)
            prev_subject = subj_match.group(1) if subj_match else None
            
            if prev_subject:
                final_query = {"subject": {"$regex": f"^{re.escape(prev_subject)}$", "$options": "i"}, "year": target_year}
                if student_branch: final_query["branch"] = student_branch
                if student_sem: final_query["semester"] = student_sem
                
                doc = await documents_collection.find_one(final_query)
                if doc:
                    download_url = f"http://127.0.0.1:8000/chat/download/{str(doc['_id'])}"
                    return f"### {doc['title']}\nHere is the question paper for **{prev_subject}** ({target_year}):\n\n{download_url}"
                else:
                    return f"Sorry, I couldn't find the {target_year} paper for {prev_subject} in the database."

        return None

    # Try QP Flow first
    qp_response = await handle_qp_flow()
    if qp_response:
        async def stream_qp():
            # Send in one or two chunks to simulate typing
            yield f"data: {json.dumps({'text': qp_response})}\n\n"
        return StreamingResponse(stream_qp(), media_type="text/event-stream")

    # 1. RAG Search (Search FAQs and Knowledge Nodes)
    # Include words with 3 or more characters (acronyms like ECE, CSE, HOD are important)
    search_terms = [word for word in user_message.split() if len(word) >= 3]
    context_parts = []
    matched_docs_metadata = [] # To show download links if found
    
    if search_terms:
        # Construct a regex that matches any of the important terms
        regex_pattern = "|".join([re.escape(term) for term in search_terms])
        
        # A. Search FAQ collection
        try:
            faq_cursor = faq_collection.find({
                "$or": [
                    {"question": {"$regex": regex_pattern, "$options": "i"}},
                    {"keywords": {"$regex": regex_pattern, "$options": "i"}}
                ]
            })
            faqs = await faq_cursor.to_list(length=3)
            for f in faqs:
                context_parts.append(f"PREVIOUS FAQ:\nQ: {f['question']}\nA: {f['answer']}")
                # If FAQ has linked documents, add them to metadata for download
                if "document_ids" in f and f["document_ids"]:
                    for d_id in f["document_ids"]:
                        d = await documents_collection.find_one({"_id": ObjectId(d_id)})
                        if d:
                            matched_docs_metadata.append(DocumentInfo(
                                id=str(d["_id"]),
                                title=d["title"],
                                file_type=d["file_type"],
                                download_url=f"/chat/download/{str(d['_id'])}"
                            ))
        except Exception as e:
            print(f"FAQ search error: {e}")

        # B. Search Faculty Collection
        try:
            from server.database import faculty_collection
            fac_cursor = faculty_collection.find({
                "$or": [
                    {"name": {"$regex": regex_pattern, "$options": "i"}},
                    {"designation": {"$regex": regex_pattern, "$options": "i"}},
                    {"department": {"$regex": regex_pattern, "$options": "i"}},
                    {"about": {"$regex": regex_pattern, "$options": "i"}},
                    {"qualification": {"$regex": regex_pattern, "$options": "i"}}
                ]
            })
            async for fac in fac_cursor:
                # Format exactly as the AI should output to the user
                fac_context = f"FACULTY PROFILE CARD DATA: Name: {fac['name']} | Qual: {fac['qualification']} | Desig: {fac['designation']} | Dept: {fac['department']} | About: {fac['about']} | Photo: {fac['photo_url']}\n"
                context_parts.append(fac_context)
        except Exception as e:
            print(f"Faculty search error: {e}")

        # C. Search Knowledge Nodes (Documents)
        try:
            doc_cursor = documents_collection.find({"extracted_text": {"$regex": regex_pattern, "$options": "i"}})
            docs = await doc_cursor.to_list(length=2)
            for d in docs:
                download_url = f"http://127.0.0.1:8000/chat/download/{str(d['_id'])}"
                context_parts.append(f"KNOWLEDGE NODE ({d['title']}):\n{d['extracted_text'][:2000]}\nDOWNLOAD LINK: {download_url}")
        except Exception as e:
            print(f"Document search error: {e}")

    # 3. Search Timetable Collection (Manual Entries - Highest Priority)
    is_schedule_query = any(word in user_message.lower() for word in ["timetable", "schedule", "class", "timing", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"])
    if is_schedule_query:
        from server.database import timetable_collection
        
        # A. Extract Day
        day_query = next((day for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"] if day.lower() in user_message.lower()), None)
        
        # B. Extract Branch (Fallback)
        branch_query = next((b for b in ["CSE", "CIVIL", "ECE"] if b.lower() in user_message.lower()), None)
        
        # C. Extract Semester (Fallback - look for numbers 1-6 near 'sem')
        sem_match = re.search(r'([1-6])(?:st|nd|rd|th)?\s*(?:sem|semester)', user_message.lower())
        sem_query = int(sem_match.group(1)) if sem_match else None
        
        # Build Search Filter
        tt_search = {}
        if day_query: tt_search["day"] = day_query
        
        # Priority 1: Use explicitly provided branch/sem from Form (Session)
        # Priority 2: Use extracted branch/sem from text
        final_branch = branch if branch else branch_query
        final_sem = int(semester) if semester else sem_query
        
        if final_branch: tt_search["branch"] = final_branch
        if final_sem: tt_search["semester"] = final_sem
        
        tt_cursor = timetable_collection.find(tt_search)
        tt_entries = await tt_cursor.to_list(length=20)
        
        if tt_entries:
            tt_context = "MANUAL TIMETABLE ENTRIES (VERIFIED):\n"
            for entry in tt_entries:
                tt_context += f"- {entry.get('day')}: {entry.get('time')} | {entry.get('subject')} | Branch: {entry.get('branch')} | Sem: {entry.get('semester')} | Room: {entry.get('room')} | Prof: {entry.get('professor')}\n"
            context_parts.append(tt_context)
            # If we found a specific match, we can tell Gemini to prioritize this
            if branch_query and sem_query:
                context_parts.append(f"NOTE: The user is specifically asking for the {branch_query} {sem_query} semester schedule.")
            elif branch_query:
                context_parts.append(f"NOTE: The user is asking for the {branch_query} schedule.")

    # Process context
    context = "\n\n---\n\n".join(context_parts) if context_parts else None
    
    # Add a system instruction to Gemini about the context
    if context:
        system_instruction = (
            "You are Aura AI, a professional college assistant. Use the provided context to answer. "
            "CRITICAL: If the context contains 'FACULTY PROFILE CARD DATA', you MUST respond ONLY with the faculty card format: "
            "DATABASE_FACULTY_CARD: [Name] | [Qual] | [Desig] | [Dept] | [About] | [Photo]. "
            "DO NOT add any conversational text before or after the card if a faculty match is found. "
            "If the context contains a timetable, format it into a Markdown Table or neat list. "
            "If a document is relevant, provide its download link."
        )
        user_message_with_instruction = f"[SYSTEM INSTRUCTION: {system_instruction}]\n\nUSER QUESTION: {user_message}"
    else:
        user_message_with_instruction = user_message

    # 2. Always stream from Gemini API with context
    return StreamingResponse(
        stream_gemini_response(user_message_with_instruction, parsed_history, image_data, mime_type, context),
        media_type="text/event-stream"
    )

@router.get("/chat/download/{document_id}")
async def download_document(document_id: str):
    """Download a document by its ID"""
    try:
        doc = await documents_collection.find_one({"_id": ObjectId(document_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = doc["file_path"]
        
        # Verify file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on server")
        
        # Return file with appropriate headers for download
        return FileResponse(
            path=file_path,
            filename=doc["title"],
            media_type='application/octet-stream'
        )
    except Exception as e:
        print(f"Download error: {e}")
        raise HTTPException(status_code=500, detail="Error downloading file")

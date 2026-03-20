import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

async def main():
    load_dotenv('.env')
    client = AsyncIOMotorClient(os.getenv('MONGODB_URL') or 'mongodb://localhost:27017')
    db = client[os.getenv('DATABASE_NAME') or 'chatbot_db']
    # Correct collection names
    docs_col = db['documents_collection']
    faqs_col = db['faq_collection']
    
    docs = await docs_col.find().to_list(length=20)
    for d in docs:
        print(f"ID: {str(d['_id'])} | Title: {d['title']} | Path: {d['file_path']}")
    
    faqs = await faqs_col.find().to_list(length=20)
    for f in faqs:
        print(f"FAQ ID: {str(f['_id'])} | Docs: {f.get('document_ids', [])}")

if __name__ == "__main__":
    asyncio.run(main())

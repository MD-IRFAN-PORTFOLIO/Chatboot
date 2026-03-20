import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def count_docs():
    url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DATABASE_NAME", "chatbot_db")
    client = AsyncIOMotorClient(url)
    db = client[db_name]
    for c in ["faqs", "faq_collection", "documents", "documents_collection", "admin_collection", "timetable_collection"]:
        count = await db[c].count_documents({})
        print(f"COUNT {c}: {count}")

if __name__ == "__main__":
    asyncio.run(count_docs())

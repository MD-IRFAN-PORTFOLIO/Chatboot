import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "chatbot_db")

async def diag_faculty():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    faculty_collection = db.get_collection("faculty")
    
    print("--- Faculty Collection ---")
    cursor = faculty_collection.find({})
    async for doc in cursor:
        print(doc)

if __name__ == "__main__":
    asyncio.run(diag_faculty())

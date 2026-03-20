import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "chatbot_db")

client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=2000)
database = client[DATABASE_NAME]

# Collections
faq_collection = database.get_collection("faq_collection")
documents_collection = database.get_collection("documents_collection")
admin_collection = database.get_collection("admin_collection")

# New Extended Architecture Collections
users_collection = database.get_collection("users")
prompts_collection = database.get_collection("prompts")
api_keys_collection = database.get_collection("api_keys")
feedback_collection = database.get_collection("feedback")
activity_logs_collection = database.get_collection("activity_logs")
chat_history_collection = database.get_collection("chat_history")
timetable_collection = database.get_collection("timetable_collection")
faculty_collection = database.get_collection("faculty")

# Create indexes for search optimization
async def init_db():
    try:
        # Index on keywords for faster array searching
        await faq_collection.create_index("keywords")
        # Example: text index on question to allow text search if needed
        await faq_collection.create_index([("question", "text")])
        print("Database connected and indexes created.")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}. Falling back to Gemini only mode.")

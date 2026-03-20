import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys

async def test():
    try:
        client = AsyncIOMotorClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000)
        await client.admin.command('ping')
        print('SUCCESS: MongoDB is running and reachable on localhost:27017')
        sys.exit(0)
    except Exception as e:
        print(f'ERROR: Could not connect to MongoDB - {e}')
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(test())

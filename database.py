from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any, List

class Database:
    def __init__(self, mongodb_uri: str):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.mongodb_uri = mongodb_uri

    async def connect(self):
        """Connect to MongoDB Atlas"""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_uri)
            self.db = self.client.discord_bot
            # Test connection
            await self.client.admin.command('ping')
            print("Successfully connected to MongoDB!")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")

    # Example methods for future use
    async def save_user_data(self, user_id: int, data: Dict[str, Any]):
        """Save user data to database"""
        collection = self.db.users
        await collection.update_one(
            {"user_id": user_id},
            {"$set": data},
            upsert=True
        )

    async def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data from database"""
        collection = self.db.users
        return await collection.find_one({"user_id": user_id})

    async def save_guild_data(self, guild_id: int, data: Dict[str, Any]):
        """Save guild data to database"""
        collection = self.db.guilds
        await collection.update_one(
            {"guild_id": guild_id},
            {"$set": data},
            upsert=True
        )

    async def get_guild_data(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get guild data from database"""
        collection = self.db.guilds
        return await collection.find_one({"guild_id": guild_id})

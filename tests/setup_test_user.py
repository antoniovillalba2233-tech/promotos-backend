"""Seed a test user + session for PayPal integration tests."""
import asyncio
import os
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    user_doc = {
        "user_id": "user_paypaltest01",
        "email": "test@paypal.com",
        "name": "Test",
        "picture": None,
        "is_premium": False,
        "created_at": datetime.now(timezone.utc),
    }
    session_doc = {
        "session_token": "test_paypal_token_123",
        "user_id": "user_paypaltest01",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=1),
        "created_at": datetime.now(timezone.utc),
    }

    await db.users.update_one(
        {"user_id": user_doc["user_id"]}, {"$set": user_doc}, upsert=True
    )
    await db.user_sessions.delete_many({"session_token": session_doc["session_token"]})
    await db.user_sessions.insert_one(session_doc)
    print("Seed OK: user_paypaltest01 / token test_paypal_token_123")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())

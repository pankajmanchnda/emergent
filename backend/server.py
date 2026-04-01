from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class NewsItemCreate(BaseModel):
    title: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    tags: List[str] = []
    item_type: str = "rss"  # "youtube" or "rss"

class NewsItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    url: str
    source: str
    published_at: datetime
    summary: Optional[str] = None
    tags: List[str] = []
    item_type: str = "rss"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RefreshResponse(BaseModel):
    success: bool
    message: str
    new_items: int
    total_fetched: int

class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str


# News routes
@api_router.post("/news", response_model=NewsItem)
async def create_news_item(input: NewsItemCreate):
    """Create a new news item"""
    news_dict = input.model_dump()
    
    if news_dict.get('published_at') is None:
        news_dict['published_at'] = datetime.now(timezone.utc)
    
    news_obj = NewsItem(**news_dict)
    
    doc = news_obj.model_dump()
    doc['published_at'] = doc['published_at'].isoformat()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.news_items.insert_one(doc)
    return news_obj


@api_router.get("/news", response_model=List[NewsItem])
async def get_news_items(tag: Optional[str] = None):
    """Get all news items, optionally filtered by tag, sorted newest first"""
    query = {}
    if tag and tag.lower() != 'all':
        query = {"tags": {"$regex": f"^{tag}$", "$options": "i"}}
    
    news_items = await db.news_items.find(query, {"_id": 0}).sort("published_at", -1).to_list(1000)
    
    for item in news_items:
        if isinstance(item.get('published_at'), str):
            item['published_at'] = datetime.fromisoformat(item['published_at'])
        if isinstance(item.get('created_at'), str):
            item['created_at'] = datetime.fromisoformat(item['created_at'])
    
    return news_items


@api_router.delete("/news/{news_id}")
async def delete_news_item(news_id: str):
    """Delete a news item by ID"""
    result = await db.news_items.delete_one({"id": news_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="News item not found")
    return {"message": "News item deleted"}


@api_router.post("/news/refresh", response_model=RefreshResponse)
async def refresh_youtube_news():
    """Fetch latest Iran war news from YouTube channels"""
    try:
        from youtube_service import fetch_all_iran_news
        
        # Fetch new videos
        videos = await fetch_all_iran_news()
        
        if not videos:
            return RefreshResponse(
                success=True,
                message="No new Iran war videos found in the last 24 hours",
                new_items=0,
                total_fetched=0
            )
        
        # Check for duplicates and insert new items
        new_count = 0
        for video in videos:
            # Check if URL already exists
            existing = await db.news_items.find_one({"url": video['url']})
            if not existing:
                news_obj = NewsItem(
                    title=video['title'],
                    url=video['url'],
                    source=video['source'],
                    published_at=datetime.fromisoformat(video['published_at'].replace('Z', '+00:00')),
                    summary=video.get('summary', ''),
                    tags=video.get('tags', ['Iran']),
                    item_type='youtube'
                )
                
                doc = news_obj.model_dump()
                doc['published_at'] = doc['published_at'].isoformat()
                doc['created_at'] = doc['created_at'].isoformat()
                
                await db.news_items.insert_one(doc)
                new_count += 1
        
        return RefreshResponse(
            success=True,
            message=f"Successfully fetched {len(videos)} videos, added {new_count} new items",
            new_items=new_count,
            total_fetched=len(videos)
        )
        
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Root route
@api_router.get("/")
async def root():
    return {"message": "Iran War Monitor API"}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    await db.status_checks.insert_one(doc)
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

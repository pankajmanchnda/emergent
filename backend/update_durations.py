"""
Script to update existing YouTube items with duration
"""
import asyncio
import os
import re
from motor.motor_asyncio import AsyncIOMotorClient
from googleapiclient.discovery import build
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

def parse_duration(duration_str: str) -> str:
    """Convert ISO 8601 duration to human readable format"""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return "0:00"
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

async def update_durations():
    # Connect to MongoDB
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # Get YouTube API
    youtube = build('youtube', 'v3', developerKey=os.environ['YOUTUBE_API_KEY'], cache_discovery=False)
    
    # Find all YouTube items without duration
    items = await db.news_items.find({
        "item_type": "youtube",
        "$or": [
            {"duration": None},
            {"duration": {"$exists": False}},
            {"duration": ""}
        ]
    }).to_list(1000)
    
    print(f"Found {len(items)} items to update")
    
    # Extract video IDs from URLs
    video_ids = []
    item_map = {}
    for item in items:
        url = item['url']
        if 'watch?v=' in url:
            vid_id = url.split('watch?v=')[1].split('&')[0]
            video_ids.append(vid_id)
            item_map[vid_id] = item['id']
    
    print(f"Extracted {len(video_ids)} video IDs")
    
    # Fetch durations in batches of 50
    updated = 0
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        
        response = youtube.videos().list(
            id=','.join(batch),
            part='contentDetails'
        ).execute()
        
        for video in response.get('items', []):
            vid_id = video['id']
            duration_iso = video['contentDetails'].get('duration', 'PT0S')
            duration = parse_duration(duration_iso)
            
            # Update in database
            item_id = item_map.get(vid_id)
            if item_id:
                await db.news_items.update_one(
                    {"id": item_id},
                    {"$set": {"duration": duration}}
                )
                updated += 1
                print(f"Updated {vid_id} with duration {duration}")
    
    print(f"Updated {updated} items with durations")
    client.close()

if __name__ == "__main__":
    asyncio.run(update_durations())

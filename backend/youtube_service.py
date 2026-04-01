"""
YouTube News Fetcher Service
Fetches latest Iran war related videos from specified YouTube channels
"""
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from emergentintegrations.llm.chat import LlmChat, UserMessage
import logging
import re

logger = logging.getLogger(__name__)

# YouTube channel mappings (handle -> channel ID)
CHANNEL_HANDLES = {
    "FoxNews": "UCXIJgqnII2ZOINSWNOGFThA",
    "abcnews": "UCBi2mrWuNuyYy4gbM6fU18Q",
    "ThinkSchool": "UCvHnbCaTpXvLXSw8Oy6bkAA",
    "THECHANAKYADIALOGUESHINDI": "UCqRPk7BdTCNXpnzNl0L0K2w",
    "ThinkSchool_Hindi": "UCrG2Z0ushe_xG-adCDXSe7Q",
    "Firstpost": "UClLTa71UCXguBxiSZ5o7-EA",
    "aljazeeraenglish": "UCNye-wNBqNL5ZzHSJj3l8Bg",
    "WION": "UC_gUM8rL-Lrg6O3adPW9K1g",
    "SkyNewsAustralia": "UC-4K_bfuNmkqQcIgKtCBG0Q"
}

# Iran war related keywords for filtering
IRAN_KEYWORDS = [
    "iran", "iranian", "tehran", "persian gulf", "strait of hormuz",
    "irgc", "revolutionary guard", "khamenei", "rouhani", "raisi",
    "nuclear", "uranium", "enrichment", "iaea", "sanctions",
    "middle east", "israel iran", "us iran", "war iran", "attack iran",
    "drone iran", "missile iran", "hezbollah", "proxy", "houthi",
    "red sea", "gulf war", "iran strike", "iran conflict"
]


def get_youtube_service():
    """Initialize YouTube API service"""
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY not found in environment")
    return build('youtube', 'v3', developerKey=api_key, cache_discovery=False)


def is_iran_related(title: str, description: str) -> bool:
    """Check if video is related to Iran war/conflict"""
    text = f"{title} {description}".lower()
    return any(keyword in text for keyword in IRAN_KEYWORDS)


async def fetch_channel_videos(channel_id: str, channel_name: str, max_results: int = 10) -> List[Dict]:
    """Fetch latest videos from a YouTube channel"""
    try:
        youtube = get_youtube_service()
        
        # Calculate date 24 hours ago
        published_after = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        
        # Search for recent videos from channel
        search_response = youtube.search().list(
            channelId=channel_id,
            part='snippet',
            order='date',
            type='video',
            publishedAfter=published_after,
            maxResults=max_results
        ).execute()
        
        videos = []
        for item in search_response.get('items', []):
            snippet = item['snippet']
            video_id = item['id']['videoId']
            
            video_data = {
                'video_id': video_id,
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'channel_name': channel_name,
                'channel_title': snippet['channelTitle'],
                'published_at': snippet['publishedAt'],
                'thumbnail': snippet['thumbnails'].get('high', {}).get('url', ''),
                'url': f"https://www.youtube.com/watch?v={video_id}"
            }
            videos.append(video_data)
        
        return videos
        
    except HttpError as e:
        logger.error(f"YouTube API error for channel {channel_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching videos from {channel_name}: {e}")
        return []


async def filter_iran_videos(videos: List[Dict]) -> List[Dict]:
    """Filter videos to only include Iran war related content"""
    filtered = []
    for video in videos:
        if is_iran_related(video['title'], video['description']):
            filtered.append(video)
    return filtered


async def summarize_video_with_ai(video: Dict) -> Optional[Dict]:
    """Use AI to summarize video content and extract tags"""
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            logger.error("EMERGENT_LLM_KEY not found")
            return None
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"video-summary-{video['video_id']}",
            system_message="""You are a news analyst specializing in Iran and Middle East conflicts. 
            Analyze YouTube video titles and descriptions to extract key information.
            Be concise and factual. Focus on credibility - flag any sensationalist or unverified claims."""
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""Analyze this YouTube video about Iran/Middle East news:

Title: {video['title']}
Channel: {video['channel_title']}
Description: {video['description'][:500]}

Provide a JSON response with:
1. "summary": A 1-2 sentence factual summary (max 150 chars)
2. "tags": Array of relevant tags from: ["Iran", "War", "Nuclear", "Diplomacy", "Israel", "US", "Sanctions", "Military"]
3. "credibility": "high", "medium", or "low" based on source and content
4. "is_relevant": true if genuinely about Iran conflict, false if clickbait/unrelated

Respond ONLY with valid JSON, no other text."""

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        import json
        # Clean response - extract JSON if wrapped in markdown
        response_text = response.strip()
        if response_text.startswith('```'):
            response_text = re.sub(r'^```json?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)
        
        result = json.loads(response_text)
        
        if not result.get('is_relevant', True):
            return None
        
        if result.get('credibility') == 'low':
            return None
            
        return {
            'summary': result.get('summary', ''),
            'tags': result.get('tags', ['Iran']),
            'credibility': result.get('credibility', 'medium')
        }
        
    except Exception as e:
        logger.error(f"AI summarization error: {e}")
        # Fallback - return basic data
        return {
            'summary': video['description'][:150] if video['description'] else '',
            'tags': ['Iran'],
            'credibility': 'medium'
        }


async def fetch_all_iran_news() -> List[Dict]:
    """Fetch and process Iran war news from all configured channels"""
    all_videos = []
    
    for handle, channel_id in CHANNEL_HANDLES.items():
        logger.info(f"Fetching videos from {handle}...")
        videos = await fetch_channel_videos(channel_id, handle)
        all_videos.extend(videos)
    
    # Filter for Iran-related content
    iran_videos = await filter_iran_videos(all_videos)
    logger.info(f"Found {len(iran_videos)} Iran-related videos out of {len(all_videos)} total")
    
    # Process each video with AI
    processed_videos = []
    for video in iran_videos:
        ai_result = await summarize_video_with_ai(video)
        if ai_result:
            processed_videos.append({
                'title': video['title'],
                'url': video['url'],
                'source': video['channel_title'],
                'published_at': video['published_at'],
                'summary': ai_result['summary'],
                'tags': ai_result['tags'],
                'item_type': 'youtube',
                'thumbnail': video['thumbnail'],
                'credibility': ai_result['credibility']
            })
    
    logger.info(f"Processed {len(processed_videos)} credible videos")
    return processed_videos

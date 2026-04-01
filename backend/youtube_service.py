"""
YouTube News Fetcher Service
Fetches latest Iran war related videos from specified YouTube channels
Uses playlistItems API instead of search to avoid API restrictions
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

# YouTube channel mappings (handle -> uploads playlist ID)
# Uploads playlist ID is "UU" + channel_id[2:]
CHANNEL_INFO = {
    "Fox News": {"channel_id": "UCXIJgqnII2ZOINSWNOGFThA", "uploads_playlist": "UUXIJgqnII2ZOINSWNOGFThA"},
    "ABC News": {"channel_id": "UCBi2mrWuNuyYy4gbM6fU18Q", "uploads_playlist": "UUBi2mrWuNuyYy4gbM6fU18Q"},
    "Think School": {"channel_id": "UCvHnbCaTpXvLXSw8Oy6bkAA", "uploads_playlist": "UUvHnbCaTpXvLXSw8Oy6bkAA"},
    "Chanakya Dialogues": {"channel_id": "UCqRPk7BdTCNXpnzNl0L0K2w", "uploads_playlist": "UUqRPk7BdTCNXpnzNl0L0K2w"},
    "Think School Hindi": {"channel_id": "UCrG2Z0ushe_xG-adCDXSe7Q", "uploads_playlist": "UUrG2Z0ushe_xG-adCDXSe7Q"},
    "Firstpost": {"channel_id": "UClLTa71UCXguBxiSZ5o7-EA", "uploads_playlist": "UUlLTa71UCXguBxiSZ5o7-EA"},
    "Al Jazeera": {"channel_id": "UCNye-wNBqNL5ZzHSJj3l8Bg", "uploads_playlist": "UUNye-wNBqNL5ZzHSJj3l8Bg"},
    "WION": {"channel_id": "UC_gUM8rL-Lrg6O3adPW9K1g", "uploads_playlist": "UU_gUM8rL-Lrg6O3adPW9K1g"},
    "Sky News Australia": {"channel_id": "UC-4K_bfuNmkqQcIgKtCBG0Q", "uploads_playlist": "UU-4K_bfuNmkqQcIgKtCBG0Q"}
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


def parse_duration(duration_str: str) -> str:
    """Convert ISO 8601 duration to human readable format (e.g., PT1H2M3S -> 1:02:03)"""
    import re
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


async def fetch_channel_videos(channel_name: str, channel_info: dict, max_results: int = 15) -> List[Dict]:
    """Fetch latest videos from a YouTube channel using playlistItems API"""
    try:
        youtube = get_youtube_service()
        
        # Calculate date 48 hours ago (expanded window for more results)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=48)
        
        # Get videos from uploads playlist
        playlist_response = youtube.playlistItems().list(
            playlistId=channel_info['uploads_playlist'],
            part='snippet,contentDetails',
            maxResults=max_results
        ).execute()
        
        # Collect video IDs for duration lookup
        video_ids = []
        video_items = []
        
        for item in playlist_response.get('items', []):
            snippet = item['snippet']
            video_id = snippet['resourceId']['videoId']
            published_at = snippet['publishedAt']
            
            # Parse publish date
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            
            # Only include videos from last 48 hours
            if pub_date < cutoff_time:
                continue
            
            video_ids.append(video_id)
            video_items.append({
                'video_id': video_id,
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'channel_name': channel_name,
                'channel_title': snippet['channelTitle'],
                'published_at': published_at,
                'thumbnail': snippet['thumbnails'].get('high', snippet['thumbnails'].get('default', {})).get('url', ''),
                'url': f"https://www.youtube.com/watch?v={video_id}"
            })
        
        # Fetch durations for all videos in one API call
        if video_ids:
            videos_response = youtube.videos().list(
                id=','.join(video_ids),
                part='contentDetails'
            ).execute()
            
            # Create duration lookup
            duration_map = {}
            for video in videos_response.get('items', []):
                vid_id = video['id']
                duration_iso = video['contentDetails'].get('duration', 'PT0S')
                duration_map[vid_id] = parse_duration(duration_iso)
            
            # Add duration to video items
            for item in video_items:
                item['duration'] = duration_map.get(item['video_id'], '0:00')
        
        logger.info(f"Found {len(video_items)} recent videos from {channel_name}")
        return video_items
        
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
    
    for channel_name, channel_info in CHANNEL_INFO.items():
        logger.info(f"Fetching videos from {channel_name}...")
        videos = await fetch_channel_videos(channel_name, channel_info)
        all_videos.extend(videos)
    
    logger.info(f"Total videos fetched: {len(all_videos)}")
    
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
                'credibility': ai_result['credibility'],
                'duration': video.get('duration', '')
            })
    
    logger.info(f"Processed {len(processed_videos)} credible videos")
    return processed_videos

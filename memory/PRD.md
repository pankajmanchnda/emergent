# Iran War Monitor - PRD

## Original Problem Statement
Build a news digest dashboard app called 'Iran War Monitor' with:
1. Database table `news_items` with columns: title, url, source, published_at, summary, tags, item_type
2. POST API endpoint at /api/news to save articles
3. Frontend dashboard showing articles as cards, sorted newest first
4. Filter buttons: All, Iran, War, Nuclear, Diplomacy
5. Dark-themed clean design
6. Cards showing: headline, source, time, tags, and link

## User Choices
- No authentication (public dashboard)
- Basic features only
- Allow custom tags
- YouTube integration with: Fox News, ABC News, Think School, Chanakya Dialogues, Firstpost, Al Jazeera, WION, Sky News Australia

## Architecture
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Frontend**: React + Tailwind CSS
- **Database**: MongoDB collection `news_items`
- **Integrations**: YouTube Data API v3, OpenAI GPT-5.2 (via Emergent LLM key)

## What's Been Implemented (April 2026)
- ✅ MongoDB `news_items` collection with all required fields
- ✅ POST /api/news - Creates news items
- ✅ GET /api/news - Returns all items sorted newest first  
- ✅ GET /api/news?tag=X - Case-insensitive tag filtering
- ✅ POST /api/news/refresh - Fetches YouTube videos from 9 channels
- ✅ YouTube Data API integration (playlistItems API)
- ✅ AI summarization with GPT-5.2 for video analysis
- ✅ Auto-tagging: Iran, War, Nuclear, Diplomacy, US, Israel, Military, Sanctions
- ✅ Credibility filtering (removes low-quality/clickbait content)
- ✅ Dark tactical "Control Room" theme
- ✅ Refresh Feed button for manual YouTube sync
- ✅ RSS/YouTube type badges on cards

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/news | Create news item |
| GET | /api/news | Get all items (sorted newest) |
| GET | /api/news?tag=X | Filter by tag |
| POST | /api/news/refresh | Fetch from YouTube channels |
| DELETE | /api/news/{id} | Delete item |

## YouTube Channels Monitored
- Fox News, ABC News, Think School, Chanakya Dialogues Hindi
- Think School Hindi, Firstpost, Al Jazeera English, WION, Sky News Australia

## Next Tasks / Backlog
### P0 (Critical)
- None - MVP complete with YouTube integration

### P1 (High Priority)
- Automated scheduling (6 AM / 6 PM IST cron jobs)
- Search functionality
- Pagination for large datasets

### P2 (Nice to Have)
- RSS feed integration for non-YouTube sources
- Email/push notifications for breaking news
- Admin panel to manage sources
- Analytics dashboard (trending topics)

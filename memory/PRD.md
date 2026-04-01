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

## Architecture
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Frontend**: React + Tailwind CSS
- **Database**: MongoDB collection `news_items`

## What's Been Implemented (April 2026)
- ✅ MongoDB `news_items` collection with all required fields + id, created_at
- ✅ POST /api/news - Creates news items with auto-generated timestamps
- ✅ GET /api/news - Returns all items sorted newest first
- ✅ GET /api/news?tag=X - Case-insensitive tag filtering
- ✅ DELETE /api/news/{id} - Delete functionality
- ✅ Dark tactical "Control Room" theme with Chivo/IBM Plex Sans/JetBrains Mono fonts
- ✅ Seamless grid layout (border-collapse effect)
- ✅ Color-coded tags (War=red, Nuclear=amber, Diplomacy=blue, Iran=green)
- ✅ RSS/YouTube type badges
- ✅ Live feed indicator, stats bar
- ✅ All data-testid attributes for testing

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/news | Create news item |
| GET | /api/news | Get all items (sorted newest) |
| GET | /api/news?tag=X | Filter by tag |
| DELETE | /api/news/{id} | Delete item |

## Next Tasks / Backlog
### P0 (Critical)
- None - MVP complete

### P1 (High Priority)
- Search functionality
- Pagination for large datasets
- Bulk import from RSS/YouTube feeds

### P2 (Nice to Have)
- Real-time auto-refresh
- Admin panel to manage news items
- RSS feed integration automation
- Email alerts for specific tags

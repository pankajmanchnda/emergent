# Iran War Monitor - Project Prompt

## Overview
Build a real-time news digest dashboard called **"Iran War Monitor"** that aggregates and displays Iran war-related news from multiple YouTube channels, with AI-powered summarization and filtering.

---

## Core Requirements

### 1. Database Schema
Create a MongoDB collection `news_items` with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| title | string | News headline |
| url | string | Link to original article/video |
| source | string | Publisher name (e.g., "WION", "Al Jazeera") |
| published_at | datetime | Publication timestamp |
| summary | string | AI-generated summary (max 150 chars) |
| tags | array[string] | Categories: Iran, War, Nuclear, Diplomacy, US, Israel, Military, Sanctions |
| item_type | string | "youtube" or "rss" |
| duration | string | Video runtime (e.g., "15:23", "1:06:15") - YouTube only |
| created_at | datetime | Record creation timestamp |

### 2. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/news` | Fetch all news items, sorted newest first |
| GET | `/api/news?tag={tag}` | Filter by tag (case-insensitive) |
| POST | `/api/news` | Create a new news item manually |
| POST | `/api/news/refresh` | Fetch latest videos from YouTube channels |
| DELETE | `/api/news/{id}` | Delete a news item |

### 3. YouTube Integration
Monitor these 9 channels for Iran war content:
- Fox News
- ABC News
- Al Jazeera English
- WION
- Firstpost
- Think School
- Think School Hindi
- The Chanakya Dialogues Hindi
- Sky News Australia

**Fetching Logic:**
- Use YouTube Data API v3 `playlistItems` endpoint (uploads playlist)
- Fetch videos from last 48 hours
- Filter using keywords: iran, nuclear, tehran, irgc, sanctions, hezbollah, etc.
- Extract video duration using `videos.list` API with `contentDetails`

### 4. AI Processing
For each Iran-related video:
- Generate 1-2 sentence factual summary (max 150 chars)
- Auto-assign relevant tags from predefined list
- Assess credibility (high/medium/low)
- Filter out clickbait and low-credibility content

**AI Integration:** OpenAI GPT-5.2 via Emergent LLM Key

---

## Frontend Requirements

### Design Theme: "Tactical Control Room"
- **Background:** #050505 (near-black)
- **Surface:** #0A0A0A
- **Borders:** #262626 (technical grid lines)
- **Accent:** #FF3300 (alert red)
- **Fonts:**
  - Headings: Chivo (900 weight, uppercase)
  - Body: IBM Plex Sans
  - Metadata/Tags: JetBrains Mono

### Layout
```
┌─────────────────────────────────────────────────────────┐
│ [Radar Icon] IRAN WAR MONITOR              ● LIVE FEED │
├─────────────────────────────────────────────────────────┤
│ Total Items: 45  │  Filter: ALL  │  Sources: 9 Channels│
├─────────────────────────────────────────────────────────┤
│ [ALL] [IRAN] [WAR] [NUCLEAR] [DIPLOMACY]  [REFRESH FEED]│
├─────────┬─────────┬─────────┬─────────┬─────────────────┤
│  Card   │  Card   │  Card   │  Card   │                 │
│         │         │         │         │  (Seamless      │
├─────────┼─────────┼─────────┼─────────┤   Grid with     │
│  Card   │  Card   │  Card   │  Card   │   border-       │
│         │         │         │         │   collapse)     │
└─────────┴─────────┴─────────┴─────────┴─────────────────┘
```

### News Card Structure
```
┌──────────────────────────────────────┐
│ SOURCE  [YT] [15:23]        12m ago  │
│                                      │
│ Headline Title Goes Here             │
│ (Bold, transitions to red on hover)  │
│                                      │
│ AI-generated summary text that       │
│ describes the video content...       │
│                                      │
│ [IRAN] [WAR] [US]              [↗]   │
└──────────────────────────────────────┘
```

### Tag Color Coding
| Tag | Color |
|-----|-------|
| War | #FF3300 (Red) |
| Nuclear | #F59E0B (Amber) |
| Diplomacy | #3B82F6 (Blue) |
| Iran | #10B981 (Green) |
| Israel | #3B82F6 (Blue) |
| Military | #EF4444 (Red) |
| Sanctions | #8B5CF6 (Purple) |
| US | #6366F1 (Indigo) |

### Interactive Elements
- **Filter Buttons:** Toggle active state with accent color
- **Refresh Feed Button:** Red gradient, spinning icon while loading
- **Cards:** Subtle background transition on hover, title turns red
- **External Links:** Arrow icon glows red on hover

---

## Tech Stack

### Backend
- **Framework:** FastAPI
- **Database:** MongoDB (Motor async driver)
- **APIs:** 
  - YouTube Data API v3
  - OpenAI GPT-5.2 (via Emergent integrations)

### Frontend
- **Framework:** React 19
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **Components:** Shadcn/UI

---

## Environment Variables

### Backend (`/app/backend/.env`)
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
YOUTUBE_API_KEY="your-youtube-api-key"
EMERGENT_LLM_KEY="your-emergent-llm-key"
```

### Frontend (`/app/frontend/.env`)
```env
REACT_APP_BACKEND_URL=https://your-app.preview.emergentagent.com
```

---

## File Structure

```
/app/
├── backend/
│   ├── server.py              # FastAPI app with all endpoints
│   ├── youtube_service.py     # YouTube fetching & AI processing
│   ├── update_durations.py    # Utility to backfill durations
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.js             # Main dashboard component
│   │   ├── App.css            # Tactical theme styles
│   │   ├── index.css          # Global styles & CSS variables
│   │   └── components/ui/     # Shadcn components
│   ├── public/
│   │   └── index.html         # Google Fonts imports
│   └── .env
└── memory/
    └── PRD.md
```

---

## Key Features Summary

1. ✅ Dark tactical "Control Room" theme
2. ✅ Real-time YouTube video aggregation from 9 news channels
3. ✅ AI-powered summarization and tagging (GPT-5.2)
4. ✅ Credibility filtering (removes clickbait/fake news)
5. ✅ Video duration display on cards
6. ✅ Tag-based filtering (Iran, War, Nuclear, Diplomacy)
7. ✅ Manual refresh button for on-demand updates
8. ✅ Responsive grid layout with seamless borders
9. ✅ RSS/YouTube type badges
10. ✅ Relative timestamps (e.g., "12m ago")

---

## Future Enhancements (P1/P2)

- [ ] Automated scheduling (6 AM / 6 PM IST cron jobs)
- [ ] Full-text search functionality
- [ ] Pagination for large datasets
- [ ] RSS feed integration for non-YouTube sources
- [ ] Email/push notifications for breaking news
- [ ] Admin panel to manage sources
- [ ] Analytics dashboard (trending topics)
- [ ] Video thumbnail previews on hover

---

## Usage

### Manual Refresh
Click the "Refresh Feed" button to fetch latest Iran war videos from all 9 YouTube channels. The system will:
1. Fetch videos published in last 48 hours
2. Filter for Iran-related content using keywords
3. Process with AI to generate summaries and tags
4. Skip duplicates and low-credibility content
5. Add new items to the database

### Filtering
Click any tag button (All, Iran, War, Nuclear, Diplomacy) to filter the displayed news items. The filter is case-insensitive.

### External Links
Click the arrow icon (↗) on any card to open the original video/article in a new tab.

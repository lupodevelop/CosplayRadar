# AniList Integration for CosplayRadar

## 🎯 Overview

This document describes the complete AniList integration for CosplayRadar, enabling the platform to fetch character data with detailed gender information and trending metrics from AniList's GraphQL API.

## ✨ Features

### 🔧 Core Integration
- **AniList GraphQL Service**: Complete service for AniList API interaction
- **Character Synchronization**: Automated sync of trending characters
- **Gender Filtering**: Support for Male, Female, and Non-binary character filtering
- **Multi-Source Support**: Seamless integration with existing Jikan API
- **Enhanced API Endpoints**: Updated `/api/characters` with AniList support

### 📊 Data Enhancement
- **Gender Information**: Complete gender data for cosplay planning
- **Media Titles**: Accurate anime/manga title associations
- **Popularity Scores**: Enhanced trending calculations
- **Weekly Trending**: Real-time trending character detection
- **Source Tracking**: Clear identification of data sources

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AniList API   │    │   Jikan API     │    │   Database      │
│   (GraphQL)     │    │   (REST)        │    │   (PostgreSQL)  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Character Sync Service                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ AniList Service │  │ Jikan Service   │  │ Database Layer  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Endpoints                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ /api/characters │  │ /api/admin/sync │  │ Frontend Pages  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 File Structure

```
apps/web/src/
├── services/
│   ├── anilistService.ts          # AniList GraphQL client
│   ├── characterSyncService.ts    # Enhanced sync service
│   └── jikanService.ts           # Existing Jikan service
├── app/
│   ├── api/
│   │   ├── characters/route.ts    # Updated with AniList support
│   │   └── admin/sync/route.ts    # Enhanced sync endpoints
│   ├── test-anilist/page.tsx     # AniList testing page
│   └── test-sync/page.tsx        # Sync testing page
└── packages/db/
    └── schema.prisma             # Enhanced with AniList fields
```

## 🔌 API Integration

### Enhanced Database Schema

```prisma
model Character {
  id              String      @id @default(cuid())
  name            String
  series          String
  category        Category
  // ... existing fields ...
  
  // New AniList fields
  source          String?     @default("jikan")  // "jikan", "anilist", "manual"
  media_title     String?                        // Original anime/manga title
  anilistId       Int?                          // AniList character ID
  gender          String?                       // "Male", "Female", "Non-binary"
  
  // ... rest of fields ...
}
```

### Updated API Endpoints

#### GET /api/characters

Enhanced with new query parameters:

```typescript
interface CharactersQuery {
  page?: string;
  limit?: string;
  category?: Category;
  difficulty?: string;
  search?: string;
  sortBy?: "popularity" | "trending" | "recent" | "difficulty";
  source?: "all" | "jikan" | "anilist" | "database";  // NEW
  gender?: "Male" | "Female" | "Non-binary";          // NEW
}
```

**Example requests:**
```bash
# Get AniList characters only
GET /api/characters?source=anilist&limit=10

# Get female characters from any source
GET /api/characters?gender=Female&limit=5

# Get trending male anime characters from AniList
GET /api/characters?source=anilist&gender=Male&category=ANIME&sortBy=trending
```

#### POST /api/admin/sync

Enhanced sync endpoint with source selection:

```bash
# Sync from AniList only
POST /api/admin/sync
{
  "action": "sync",
  "source": "anilist"
}

# Sync from both sources
POST /api/admin/sync
{
  "action": "sync"
}

# Get sync statistics
POST /api/admin/sync
{
  "action": "status"
}
```

## 🚀 AniList Service Details

### Core Methods

```typescript
class AniListService {
  // Get top characters with optional gender filtering
  async getTopCharacters({
    gender?: 'Male' | 'Female' | 'Non-binary';
    page?: number;
    perPage?: number;
  }): Promise<CharacterResponse>

  // Get weekly trending characters from popular anime
  async getWeeklyTrendingCharacters({
    page?: number;
    perPage?: number;
  }): Promise<CharacterResponse>

  // Search characters by name
  async searchCharacters(
    name: string,
    page?: number,
    perPage?: number
  ): Promise<CharacterResponse>
}
```

### GraphQL Queries

The service uses optimized GraphQL queries to fetch:
- Character basic information (name, image, description)
- Gender and age data
- Media associations (anime/manga titles)
- Popularity metrics (favorites, trending scores)
- Complete media context for accurate categorization

### Caching & Rate Limiting

- **LRU Cache**: 30-minute TTL for AniList responses
- **Rate Limiting**: 500ms delay between requests
- **Smart Caching**: Different cache keys for gender/pagination combinations

## 💾 Data Synchronization

### Character Sync Strategy

1. **Weekly Trending**: Fetches characters from trending anime
2. **Gender-Specific**: Syncs top characters by gender (Male/Female)
3. **Deduplication**: Prevents duplicate entries across sources
4. **Update Logic**: Updates existing characters with new data

### Sync Process Flow

```
1. Fetch Weekly Trending Anime → Extract Characters
2. Fetch Top Male Characters → Limit to Top 5
3. Fetch Top Female Characters → Limit to Top 5
4. For Each Character:
   - Check if exists (by name + series)
   - Create new OR update existing
   - Track sync statistics
5. Update Trend Data
```

## 🧪 Testing

### Automated Testing

Run the integration test script:

```bash
./test-integration.sh
```

### Manual Testing Pages

1. **AniList Service Test**: `/test-anilist`
   - Test character fetching with different filters
   - Verify gender filtering functionality
   - Check source attribution

2. **Sync Administration**: `/test-sync`
   - Test manual synchronization
   - View database statistics
   - Monitor sync results and errors

## 🔧 Configuration

### Environment Variables

No additional environment variables required - AniList API is public and doesn't require authentication.

### Rate Limiting Settings

```typescript
const REQUEST_DELAY = 500; // 500ms between requests
const cache = new LRUCache({
  max: 200,           // Maximum 200 cached items
  ttl: 1000 * 60 * 30 // 30-minute cache TTL
});
```

## 📈 Performance Optimization

### Caching Strategy
- **Service Level**: Individual API responses cached
- **Database Level**: Character deduplication and updates
- **API Level**: Intelligent fallback between sources

### Query Optimization
- **Selective Fields**: Only fetch required character data
- **Pagination**: Efficient pagination with proper limits
- **Batch Processing**: Process multiple characters in single requests

## 🚨 Error Handling

### Graceful Degradation
- **AniList Unavailable**: Falls back to Jikan API
- **Network Errors**: Cached responses when available
- **Sync Failures**: Detailed error logging and partial success reporting

### Error Monitoring
- **Sync Errors**: Tracked per character with detailed messages
- **API Errors**: GraphQL error parsing and reporting
- **Database Errors**: Transaction rollback and error recovery

## 🔮 Future Enhancements

### Planned Features
1. **Real-time Sync**: Webhook-based character updates
2. **Advanced Filtering**: Age ranges, character roles, series popularity
3. **Recommendation Engine**: ML-based character recommendations
4. **Image Processing**: Automatic image optimization and CDN integration
5. **Analytics Dashboard**: Detailed sync and usage metrics

### Potential Integrations
- **MyAnimeList**: Additional character source
- **Kitsu API**: Alternative anime database
- **Character.ai**: AI-powered character analysis
- **Social Media APIs**: Real-time trending detection

## 📝 API Response Examples

### Character Response with AniList Data

```json
{
  "characters": [
    {
      "id": "anilist-123456",
      "name": "Nezuko Kamado",
      "series": "Demon Slayer",
      "category": "ANIME",
      "difficulty": 3,
      "popularity": 125000,
      "imageUrl": "https://s4.anilist.co/file/...",
      "description": "Nezuko is a demon who...",
      "tags": ["demon", "bamboo", "pink hair"],
      "gender": "Female",
      "source": "anilist",
      "media_title": "Kimetsu no Yaiba",
      "anilistId": 123456,
      "trendingScore": 95.5,
      "socialLinks": {
        "anilist": "https://anilist.co/character/123456",
        "reddit": "https://reddit.com/search?q=Nezuko+Kamado",
        "twitter": "https://twitter.com/search?q=Nezuko+Kamado"
      },
      "createdAt": "2025-06-15T20:00:00Z",
      "updatedAt": "2025-06-15T20:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "totalCount": 500,
    "totalPages": 50,
    "hasNext": true,
    "hasPrev": false
  },
  "filters": {
    "source": "anilist",
    "gender": "Female",
    "category": "ANIME"
  },
  "source": "anilist"
}
```

## 🎉 Completion Status

### ✅ Completed Features
- [x] AniList GraphQL service implementation
- [x] Character synchronization with gender support
- [x] Enhanced API endpoints
- [x] Database schema updates
- [x] Testing pages and scripts
- [x] Comprehensive documentation

### 🔄 Ready for Production
The AniList integration is now fully functional and ready for production use. All core features have been implemented, tested, and documented.

---

**Last Updated**: June 15, 2025  
**Version**: 1.0.0  
**Author**: CosplayRadar Development Team

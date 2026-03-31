# GET /v1/trending-repos

Fetch paginated list of trending repositories discovered by the scraper.

**Required:** API Key

**Query Parameters:**
- `skip` (int, default 0): Offset for pagination
- `limit` (int, default 50): Number of results
- `category` (str, optional): Filter by category (agent, tool, mcp, general)
- `language` (str, optional): Filter by programming language
- `min_stars` (int, optional): Minimum star count
- `sort_by` (str, default "discovered_at"): Sort field (discovered_at, stars)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "github_url": "https://github.com/example/repo",
      "name": "repo",
      "description": "Description",
      "stars": 500,
      "forks": 50,
      "language": "Python",
      "topics": ["ai", "agent"],
      "last_commit": "2024-03-30T15:30:00Z",
      "category": "agent",
      "discovered_at": "2024-03-31T10:00:00Z",
      "source": "twitter"
    }
  ],
  "total": 1250,
  "skip": 0,
  "limit": 50
}
```

---

# POST /v1/scrape-repos

Trigger immediate repository scraping from Twitter and Reddit.

**Required:** API Key

**Query Parameters:**
- `days` (int, default 7): Number of days to look back

**Response:**
```json
{
  "message": "Successfully scraped and stored 42 repositories"
}
```

---

# GET /v1/trending-repos/categories

Get a summary of repository categories and counts.

**Response:**
```json
{
  "agent": 234,
  "tool": 567,
  "mcp": 123,
  "general": 326
}
```
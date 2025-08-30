# LifeRPG API Documentation

This document provides comprehensive documentation for the LifeRPG REST API.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Most endpoints require authentication using a Bearer token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### Authentication

#### POST /auth/login
Authenticate a user and return a JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "display_name": "User Name",
    "role": "user"
  }
}
```

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "display_name": "User Name"
}
```

**Response:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "display_name": "User Name",
    "role": "user"
  }
}
```

#### GET /me
Get current user information.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "display_name": "User Name",
  "role": "user"
}
```

### Habits

#### GET /habits
Get all habits for the current user.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "id": 1,
    "title": "Exercise",
    "description": "Daily exercise routine",
    "category": "health",
    "target_frequency": "daily",
    "streak": 5,
    "total_completions": 10,
    "created_at": "2025-08-29T10:00:00Z",
    "updated_at": "2025-08-30T10:00:00Z"
  }
]
```

#### POST /habits
Create a new habit.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "title": "Read Books",
  "description": "Read for 30 minutes daily",
  "category": "learning",
  "target_frequency": "daily"
}
```

**Response:**
```json
{
  "id": 2,
  "title": "Read Books",
  "description": "Read for 30 minutes daily",
  "category": "learning",
  "target_frequency": "daily",
  "streak": 0,
  "total_completions": 0,
  "created_at": "2025-08-30T10:00:00Z",
  "updated_at": "2025-08-30T10:00:00Z"
}
```

#### POST /habits/{habit_id}/complete
Mark a habit as completed for today.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true,
  "message": "Habit completed successfully",
  "xp_earned": 20,
  "new_streak": 6,
  "achievement_unlocked": {
    "id": "streak_5",
    "title": "Streak Master",
    "description": "Complete a habit 5 days in a row"
  }
}
```

### Gamification

#### GET /gamification/profile
Get user's gamification profile.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "level": 5,
  "xp": 1250,
  "xp_to_next_level": 250,
  "total_achievements": 8,
  "current_streaks": 3,
  "longest_streak": 15
}
```

#### GET /gamification/achievements
Get user's achievements.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "id": "first_habit",
    "title": "First Steps",
    "description": "Create your first habit",
    "icon": "🎯",
    "unlocked_at": "2025-08-29T10:00:00Z"
  }
]
```

#### GET /gamification/leaderboard
Get the global leaderboard.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "rank": 1,
    "user_id": 1,
    "display_name": "User One",
    "level": 10,
    "xp": 5000,
    "total_achievements": 25
  }
]
```

### Analytics

#### GET /analytics/habits/heatmap
Get habit completion heatmap data.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)

**Response:**
```json
{
  "2025-08-29": {
    "completed": 3,
    "total": 5
  },
  "2025-08-30": {
    "completed": 4,
    "total": 5
  }
}
```

#### GET /analytics/habits/trends
Get habit completion trends over time.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `period`: Time period ('week', 'month', 'year')

**Response:**
```json
[
  {
    "date": "2025-08-29",
    "completions": 3,
    "total_habits": 5,
    "completion_rate": 0.6
  }
]
```

### Telemetry

#### POST /telemetry/events
Send telemetry events.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "events": [
    {
      "event_type": "habit_completed",
      "timestamp": "2025-08-30T10:00:00Z",
      "properties": {
        "habit_id": 1,
        "category": "health"
      }
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "events_processed": 1
}
```

#### GET /telemetry/summary
Get telemetry summary (admin only).

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "total_events": 1500,
  "events_today": 45,
  "active_users": 12,
  "top_events": [
    {
      "event_type": "habit_completed",
      "count": 500
    }
  ]
}
```

### Plugins

#### GET /plugins
Get all plugins.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `status`: Filter by status ('active', 'disabled', 'pending_review', 'rejected')

**Response:**
```json
[
  {
    "id": "com.example.myplugin",
    "name": "My Custom Plugin",
    "version": "1.0.0",
    "author": "Plugin Author",
    "description": "A custom plugin for LifeRPG",
    "status": "active",
    "permissions": ["habits:read", "ui:dashboard"],
    "created_at": "2025-08-30T10:00:00Z"
  }
]
```

#### POST /plugins
Register a new plugin.

**Headers:** `Authorization: Bearer <token>`

**Request:** Multipart form data
- `metadata`: JSON metadata
- `wasm_file`: WASM binary file

**Response:**
```json
{
  "id": "com.example.myplugin",
  "status": "registered"
}
```

#### PATCH /plugins/{plugin_id}/status
Update plugin status.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "status": "active"
}
```

**Response:**
```json
{
  "id": "com.example.myplugin",
  "status": "active"
}
```

#### GET /plugins/extension-points
Get all extension points from loaded plugins.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "extension_points": {
    "dashboard": [
      {
        "id": "myplugin_widget",
        "plugin_id": "com.example.myplugin",
        "config": {
          "title": "My Widget",
          "size": "medium"
        }
      }
    ]
  }
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Authenticated requests**: 1000 requests per hour per user
- **Unauthenticated requests**: 100 requests per hour per IP

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Window reset time (Unix timestamp)

## Examples

### Complete Workflow Example

1. **Register a new user:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123","display_name":"Test User"}'
```

2. **Create a habit:**
```bash
curl -X POST http://localhost:8000/api/v1/habits \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Exercise","description":"Daily workout","category":"health","target_frequency":"daily"}'
```

3. **Complete the habit:**
```bash
curl -X POST http://localhost:8000/api/v1/habits/1/complete \
  -H "Authorization: Bearer YOUR_TOKEN"
```

4. **Check your gamification profile:**
```bash
curl -X GET http://localhost:8000/api/v1/gamification/profile \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## WebSocket Events (Future)

The API will support real-time updates via WebSocket connections:

- `habit.completed`: When a habit is completed
- `achievement.unlocked`: When an achievement is unlocked
- `level.up`: When user levels up
- `plugin.loaded`: When a plugin is loaded/unloaded

## Plugin API

Plugins have access to a subset of the API through host functions:

### Available Host Functions

- `get_habits()`: Get user's habits
- `create_habit(name)`: Create a new habit
- `register_dashboard_widget(config)`: Register a dashboard widget
- `console_log(message)`: Log a message
- `console_error(message)`: Log an error

### Plugin Permissions

Plugins must request specific permissions:

- `habits:read`: Read habit data
- `habits:write`: Create/modify habits
- `projects:read`: Read project data
- `projects:write`: Create/modify projects
- `ui:dashboard`: Add dashboard widgets
- `ui:settings`: Add settings pages
- `storage:plugin`: Use plugin storage
- `network:same-origin`: Make same-origin requests
- `network:external`: Make external requests

## SDK and Tools

### Frontend SDK

```javascript
import { LifeRPGClient } from '@liferpg/client-sdk';

const client = new LifeRPGClient({
  baseURL: 'http://localhost:8000/api/v1',
  token: 'your-jwt-token'
});

// Create a habit
const habit = await client.habits.create({
  title: 'Exercise',
  category: 'health'
});

// Complete a habit
await client.habits.complete(habit.id);
```

### Plugin SDK

```typescript
import { LifeRPG, PluginContext } from '@liferpg/plugin-sdk';

export function initialize(context: PluginContext): void {
  // Register a dashboard widget
  context.ui.registerDashboardWidget({
    id: 'my-widget',
    title: 'My Custom Widget',
    render: () => '<div>Widget content</div>'
  });
}
```

## Support

For API support and questions:

- **Documentation**: https://liferpg.dev/docs
- **GitHub Issues**: https://github.com/TLimoges33/LifeRPG/issues
- **Community Discord**: https://discord.gg/liferpg (placeholder)

## Changelog

### v1.0.0 (2025-08-30)
- Initial API release
- Authentication endpoints
- Habits CRUD operations
- Gamification system
- Analytics endpoints
- Telemetry system
- Plugin system with WASM support

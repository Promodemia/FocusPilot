# FocusPilot Backend API Documentation

## Base URL
```
http://localhost:8765
```

## Authentication
None (local use only)

---

## Endpoints

### 1. Health Check
**GET** `/health`

Check if backend is running and ActivityWatch is available.

**Response:**
```json
{
  "status": "ok",
  "activitywatch": "available|unavailable",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

**Status Codes:**
- `200 OK` - Backend is healthy

---

### 2. Set Daily Plan
**POST** `/plan`

Save today's daily plan.

**Request Body:**
```json
{
  "text": "9:00-10:00 Design API\n10:00-12:00 Implementation\n14:00-16:00 Testing"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Plan saved"
}
```

**Status Codes:**
- `200 OK` - Plan saved successfully
- `500 Internal Server Error` - Database error

---

### 3. Get Daily Plan
**GET** `/plan`

Retrieve today's plan.

**Response:**
```json
{
  "plan": "9:00-10:00 Design API\n10:00-12:00 Implementation",
  "date": "2024-01-15"
}
```

**Notes:**
- Returns empty string if no plan set
- Date is always today's date (UTC)

---

### 4. Get Current State
**GET** `/current_state`

Get current activity being monitored.

**Response:**
```json
{
  "activity": {
    "app_name": "Visual Studio Code",
    "window_title": "main.py - FocusPilot",
    "category": "work",
    "confidence": 0.95
  },
  "stats": {
    "work": 1200,
    "communication": 300,
    "distraction": 150,
    "break": 450,
    "unknown": 0
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

**Categories:**
- `work` - Work-related applications (code editors, IDEs, etc.)
- `communication` - Communication apps (Slack, Teams, email, etc.)
- `distraction` - Social media, entertainment
- `break` - Coffee breaks, rest time
- `unknown` - Unrecognized applications

**Stats (in seconds):**
- `work` - Total work time
- `communication` - Total communication time
- `distraction` - Total distraction time
- `break` - Total break time
- `unknown` - Total unrecognized time

---

### 5. Get Daily Statistics
**GET** `/stats`

Retrieve today's accumulated statistics.

**Response:**
```json
{
  "date": "2024-01-15",
  "stats": {
    "work_time": 3600,
    "distraction_time": 600,
    "communication_time": 1200,
    "break_time": 900,
    "plan_adherence": 0.85
  }
}
```

**Fields (in seconds):**
- `work_time` - Total work time
- `distraction_time` - Total distraction time
- `communication_time` - Total communication time
- `break_time` - Total break time
- `plan_adherence` - Adherence to plan (0.0-1.0)

---

### 6. Log Feedback
**POST** `/feedback`

Log user action for training data and feedback.

**Request Body:**
```json
{
  "action": "notification_dismissed|notification_acknowledged",
  "category": "work"
}
```

**Response:**
```json
{
  "status": "ok"
}
```

**Action Types:**
- `notification_dismissed` - User dismissed alert
- `notification_acknowledged` - User acknowledged alert
- `category_update` - User manually updated category
- `pause_resumed` - Monitoring resumed
- `custom_action` - Custom action string

---

### 7. Train Models
**POST** `/train`

Retrain ML models using historical data (last 1000 samples).

**Response:**
```json
{
  "status": "ok",
  "message": "Models trained"
}
```

**Status Codes:**
- `200 OK` - Training completed
- `400 Bad Request` - No training data available
- `500 Internal Server Error` - Training failed

**Notes:**
- Returns existing models if training fails
- Falls back to rule-based classification

---

### 8. Pause/Resume Monitoring
**POST** `/pause`

Temporarily pause or resume activity monitoring.

**Request Body:**
```json
{
  "pause": true
}
```

**Response:**
```json
{
  "status": "ok",
  "paused": true
}
```

**Notes:**
- When paused: no monitoring occurs
- When resumed: monitoring continues
- Database still updates on each poll (even when paused)

---

### 9. Send Notification
**POST** `/notify`

Internal endpoint - called by backend to notify Tauri frontend.

**Request Body:**
```json
{
  "title": "⚠️ Distraction Alert",
  "message": "Distracted for 5 minutes",
  "category": "distraction",
  "app": "YouTube"
}
```

**Notes:**
- Called automatically by monitoring thread
- Sent to `http://localhost:3000/notify` on Tauri
- Not meant to be called manually

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message"
}
```

### Common Errors

**500 - Database Error**
```json
{
  "detail": "Failed to save plan"
}
```
Solutions:
- Check if `backend/focuspilot.db` exists
- Check disk space
- Verify database file permissions

**503 - ActivityWatch Unavailable**
```json
{
  "detail": "ActivityWatch server is not responding"
}
```
Solutions:
- Start ActivityWatch manually
- Check `http://localhost:5600` in browser
- Restart ActivityWatch service

**400 - Bad Request**
```json
{
  "detail": "Invalid request body"
}
```
Solutions:
- Check request JSON format
- Verify required fields present
- Check Content-Type header

---

## Data Models

### Activity
```typescript
{
  app_name: string,           // e.g., "Visual Studio Code"
  window_title: string,       // e.g., "main.py - FocusPilot"
  category: string,           // "work", "communication", "distraction", "break", "unknown"
  confidence: number          // 0.0-1.0 classification confidence
}
```

### Statistics
```typescript
{
  work_time: number,          // seconds
  distraction_time: number,   // seconds
  communication_time: number, // seconds
  break_time: number,         // seconds
  plan_adherence: number      // 0.0-1.0
}
```

### Feedback
```typescript
{
  action: string,             // "notification_dismissed", etc.
  category?: string           // optional category
}
```

---

## Integration Examples

### Python (requests)
```python
import requests

# Get current state
response = requests.get('http://localhost:8765/current_state')
data = response.json()
print(f"Current app: {data['activity']['app_name']}")

# Set plan
requests.post('http://localhost:8765/plan',
    json={'text': 'Morning standup 9:00-9:30'})

# Log feedback
requests.post('http://localhost:8765/feedback',
    json={'action': 'notification_acknowledged', 'category': 'work'})
```

### JavaScript (fetch)
```javascript
// Get stats
const stats = await fetch('http://localhost:8765/stats')
    .then(r => r.json());
console.log(`Work time: ${stats.stats.work_time} seconds`);

// Submit plan
await fetch('http://localhost:8765/plan', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: 'My daily plan...'})
});
```

### Curl
```bash
# Check health
curl http://localhost:8765/health

# Get current state
curl http://localhost:8765/current_state

# Set plan
curl -X POST http://localhost:8765/plan \
  -H "Content-Type: application/json" \
  -d '{"text":"Sample plan"}'
```

---

## Rate Limiting

None - local development use only.

## CORS

Disabled - frontend runs locally.

## WebSocket

Not implemented - HTTP polling used instead.

## Monitoring Loop

Backend runs background monitoring thread:

```
Every 2 seconds:
1. GET current activity from ActivityWatch
2. Classify with ML model
3. Update statistics
4. Check thresholds:
   - Distraction > 2 minutes? POST /notify
   - Distraction probability > 0.7? POST /notify
5. Store in database
```

---

## Performance

- **Response Time**: <50ms typical
- **CPU**: <5% during idle monitoring
- **Memory**: ~100-150 MB (Python + FastAPI)
- **Database**: SQLite with auto-commit (no transactions)

---

## Version History

- **v2.0.0** - Initial release with FastAPI backend
- Previous: v1.0 (pure Python PyQt5 - archived)

---

**Last Updated**: January 2024

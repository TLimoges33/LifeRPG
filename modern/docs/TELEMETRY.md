# Telemetry System Documentation

## Overview

LifeRPG includes an optional telemetry system designed to help improve the application through anonymous usage analytics. The system is built with privacy-first principles and user control.

## Key Features

- **Opt-in Only**: Users must explicitly consent to telemetry collection
- **Anonymous**: No personal information or habit content is collected
- **Transparent**: Users can see exactly what data is collected
- **Administrative Control**: Can be disabled globally by administrators
- **GDPR Compliant**: Respects user privacy and data protection regulations

## Architecture

### Backend Components

1. **`telemetry.py`** - Core telemetry engine
 - Consent management
 - Event recording and sanitization
 - Pre-defined event helpers
 - Analytics aggregation

2. **Database Models**
 - `TelemetryEvent` - Stores anonymous event data
 - `Profile` - Stores user consent preferences

3. **API Endpoints**
 - `POST /api/v1/telemetry/consent` - Set user consent
 - `GET /api/v1/telemetry/consent` - Get consent status
 - `POST /api/v1/telemetry/event` - Record custom events
 - `GET /api/v1/admin/telemetry/stats` - Admin analytics

### Frontend Components

1. **`TelemetrySettings.jsx`** - User consent management UI
2. **`AdminTelemetryDashboard.jsx`** - Administrative analytics dashboard
3. **`useTelemetry.js`** - React hook for event tracking

## Data Collection

### What We Collect

- **Feature Usage**: Which features are accessed and how often
- **Performance Metrics**: Error rates and system performance
- **Aggregated Behavior**: Usage patterns and trends
- **Gamification Events**: XP earnings, level-ups, achievements

### What We Don't Collect

- Personal information (names, emails, etc.)
- Habit titles or descriptions
- User notes or content
- Location data
- Device identifiers
- IP addresses

### Event Types

```javascript
// User actions
habit_created: { habit_difficulty, habit_cadence }
habit_completed: { habit_difficulty, xp_awarded }
achievement_earned: { achievement_type, xp_awarded }
level_up: { old_level, new_level }

// Feature usage
analytics_heatmap: { feature_used: 'analytics_heatmap' }
analytics_trends: { feature_used: 'analytics_trends' }
feature_used: { feature_used: 'feature_name', duration? }

// Technical events
error_occurred: { error_type, context? }
page_view: { page }
user_interaction: { action, category?, label? }
```

## Configuration

### Environment Variables

```bash
# Enable/disable telemetry globally
TELEMETRY_ENABLED=true  # default: true
```

### User Consent

Users can opt-in/out at any time through:
1. Settings page in the UI
2. API endpoint
3. Automatic consent prompts

## Privacy Compliance

### GDPR Compliance

- **Lawful Basis**: Legitimate interest with opt-out capability
- **Data Minimization**: Only collect necessary anonymous data
- **Purpose Limitation**: Data used only for application improvement
- **Transparency**: Clear disclosure of what data is collected
- **User Control**: Easy opt-out mechanism

### Data Retention

- Events are stored indefinitely for analytics
- User consent can be withdrawn at any time
- No personal data is stored in telemetry events

## Implementation Examples

### Backend Integration

```python
from .telemetry import record_habit_completion

# In habit completion endpoint
result = gamification.process_habit_completion(db, user.id, habit_id)

# Record telemetry
record_habit_completion(db, user.id, habit.difficulty, result.get('xp_awarded', 0))
```

### Frontend Integration

```javascript
import { useTelemetry } from '../hooks/useTelemetry';

const MyComponent = () => {
  const { trackFeatureUsage, trackInteraction } = useTelemetry();

  const handleAnalyticsView = () => {
    trackFeatureUsage('analytics_dashboard');
  };

  const handleButtonClick = () => {
    trackInteraction('button_click', 'navigation', 'analytics');
  };
};
```

## Security Considerations

### Data Sanitization

All event properties are sanitized to remove:
- Strings longer than 100 characters
- Non-whitelisted property keys
- Potentially identifying information

### Access Control

- User events require authentication
- Admin analytics require admin role
- Anonymous events allowed for error reporting

## Monitoring and Analytics

### Admin Dashboard

Administrators can view:
- Total events and unique users
- Event type distribution
- Usage trends over time
- Performance insights

### Metrics Available

- Daily/weekly/monthly active users
- Feature adoption rates
- Error rates and types
- User engagement patterns

## Troubleshooting

### Common Issues

1. **Telemetry not recording**
 - Check `TELEMETRY_ENABLED` environment variable
 - Verify user has given consent
 - Check database connectivity

2. **Admin dashboard empty**
 - Verify admin role permissions
 - Check if telemetry is globally enabled
 - Ensure events are being recorded

3. **Consent not saving**
 - Check authentication token
 - Verify database write permissions
 - Check API endpoint configuration

## Future Enhancements

- Real-time event streaming
- Advanced user behavior analytics
- A/B testing framework integration
- Performance monitoring dashboard
- Automated privacy compliance reports

## API Reference

### Endpoints

```
POST /api/v1/telemetry/consent
GET /api/v1/telemetry/consent  
POST /api/v1/telemetry/event
GET /api/v1/admin/telemetry/stats
```

### Event Recording Functions

```python
# Direct event recording
record_event(db, user_id, event_name, properties)

# Convenience functions
record_habit_completion(db, user_id, difficulty, xp_awarded)
record_achievement_earned(db, user_id, achievement_type, xp_awarded)
record_level_up(db, user_id, old_level, new_level)
record_feature_usage(db, user_id, feature, duration)
record_error(db, user_id, error_type, context)
```

# LifeRPG Mobile App

A React Native mobile application for the LifeRPG habit tracking and gamification platform, built with Expo.

## Features

### Gamification
- **Experience Points (XP)**: Earn XP for completing habits
- **Leveling System**: Progress through levels as you build consistency
- **Achievements**: Unlock badges and achievements for milestones
- **Streaks**: Track and maintain daily habit streaks

### Habit Management
- **Custom Habits**: Create personalized habits with categories
- **Quick Templates**: Get started with popular habit templates
- **Smart Tracking**: Mark habits complete with a single tap
- **Rich Analytics**: View detailed progress and performance metrics

### Analytics & Insights
- **Progress Charts**: Visual representation of your habit completion
- **Streak Tracking**: Monitor your consistency over time
- **Category Analysis**: See which areas of your life are improving
- **Success Rates**: Track completion percentages

### Offline-First Sync
- **Work Offline**: Full functionality without internet connection
- **Auto-Sync**: Automatic synchronization when online
- **Conflict Resolution**: Smart handling of sync conflicts
- **Background Sync**: Keeps data up-to-date in the background

## Tech Stack

- **Framework**: React Native with Expo SDK 53
- **Navigation**: React Navigation v7 with Stack & Tab navigators
- **State Management**: React Hooks with custom sync engine
- **Storage**: Expo SecureStore for secure local data
- **Database**: SQLite for offline data storage
- **Authentication**: OAuth 2.0 with react-native-app-auth
- **Background Tasks**: Expo BackgroundFetch & TaskManager

## Architecture

### Screens
```
App.tsx
├── Auth
│   ├── LoginScreen - OAuth authentication
│   └── OnboardingScreen - First-time user experience
├── Main Tabs
│   ├── HomeScreen - Dashboard overview
│   ├── HabitsScreen - Habit list and management
│   ├── AnalyticsScreen - Progress analytics
│   └── AchievementsScreen - Badges and milestones
└── Modals
    ├── HabitDetailScreen - Individual habit management
    └── AddHabitScreen - Create new habits
```

### Core Libraries
```
src/
├── lib/
│   ├── auth.ts - Authentication management
│   ├── api.ts - HTTP client with token handling
│   ├── sync.ts - Offline-first sync engine
│   └── db.ts - Local SQLite database
├── hooks/
│   └── useSync.ts - React hooks for sync functionality
└── screens/
    └── [All screen components]
```

## Setup & Installation

### Prerequisites
- Node.js 18+
- Expo CLI: `npm install -g @expo/cli`
- iOS Simulator (Mac) or Android Emulator

### Development Setup
```bash
# Navigate to mobile directory
cd modern/mobile

# Install dependencies
npm install

# Start development server
npm start

# Run on specific platform
npm run android
npm run ios
```

### Production Build
```bash
# Install EAS CLI
npm install -g eas-cli

# Build for Android
npm run eas:build:android:dev

# Build for iOS (requires Apple Developer account)
eas build --platform ios --profile production
```

## Key Features Implementation

### 1. Offline-First Architecture
The app uses a sophisticated sync engine that:
- Queues changes locally when offline
- Syncs automatically when connection is restored
- Handles conflict resolution intelligently
- Provides real-time sync status updates

### 2. Habit Management
```typescript
// Creating a new habit
const habit = {
  title: "Drink 8 glasses of water",
  description: "Stay hydrated throughout the day",
  category: "health"
};

// Add to sync queue for offline support
await addChange({
  type: 'habit_create',
  data: habit
});
```

### 3. Gamification System
- **XP Calculation**: Dynamic XP rewards based on streak length
- **Achievement System**: Progressive unlock system
- **Level Progression**: Exponential XP requirements
- **Visual Feedback**: Immediate reward notifications

### 4. Analytics Engine
- **Completion Rates**: Calculate success percentages
- **Streak Analysis**: Track longest and current streaks
- **Category Performance**: Compare different habit types
- **Time-based Charts**: Weekly and monthly progress views

## Sync Engine Details

### Change Queue System
```typescript
interface SyncChange {
  id: string;
  type: 'habit_create' | 'habit_update' | 'habit_delete' | 'habit_complete';
  entityId?: number;
  data: any;
  timestamp: number;
  synced: boolean;
}
```

### Sync Strategies
- **Immediate Sync**: Attempt sync on every change
- **Background Sync**: Regular sync via Expo BackgroundFetch
- **Manual Sync**: User-triggered full synchronization
- **Conflict Resolution**: Last-write-wins with user notification

## Security

- **Secure Storage**: All sensitive data encrypted with Expo SecureStore
- **Token Management**: Automatic refresh token handling
- **API Security**: Bearer token authentication for all requests
- **Data Validation**: Client-side validation before sync

## Performance Optimizations

- **Lazy Loading**: Screens loaded on-demand
- **Image Optimization**: Optimized assets and caching
- **Memory Management**: Efficient state cleanup
- **Bundle Splitting**: Reduced initial load time

## Contributing

1. **Code Style**: Follow React Native and TypeScript best practices
2. **Component Structure**: Use functional components with hooks
3. **State Management**: Prefer local state with sync engine
4. **Error Handling**: Comprehensive error boundaries and user feedback
5. **Accessibility**: Full support for screen readers and accessibility features

## Future Enhancements

- [ ] Widget support for iOS/Android home screens
- [ ] Apple Health / Google Fit integration
- [ ] Social features and friend challenges
- [ ] Advanced analytics with AI insights
- [ ] Custom habit categories and icons
- [ ] Habit scheduling and reminders
- [ ] Export data functionality
- [ ] Dark mode support

## License

This project is part of the LifeRPG ecosystem and follows the same licensing terms as the main project.

## Next steps
- Hook Login.tsx to OIDC (PKCE) and store tokens securely
- Implement local DB schema (users, projects, habits, logs)
- Add pull/push sync with conflict hooks and retry/backoff
- background fetch for periodic sync

See Milestone 5 in `modern/ROADMAP.md` for the detailed plan.

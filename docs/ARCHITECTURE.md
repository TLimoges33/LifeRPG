# LifeRPG Architecture Guide

This document outlines the architecture of the LifeRPG modern application, explaining key design decisions, component interactions, and technical implementation details.

## System Architecture Overview

LifeRPG follows a modern microservices-inspired architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Client Applications                          │
│                                                                  │
│    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│    │ Web Frontend │    │ Mobile App   │    │ Public API   │     │
│    │ (React/Vite) │    │ (React Native)│   │ Consumers    │     │
│    └──────┬───────┘    └───────┬──────┘    └───────┬──────┘     │
└──────────┼──────────────────────┼────────────────────┼──────────┘
           │                      │                    │
           ▼                      ▼                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                      REST API Gateway                             │
│                                                                   │
│         (FastAPI with JWT auth, rate limiting, CORS)              │
└────────────┬───────────────────┬───────────────────┬─────────────┘
             │                   │                   │
             ▼                   ▼                   ▼
┌──────────────────┐  ┌────────────────┐  ┌───────────────────────┐
│  Core Services   │  │  Integrations  │  │  Auxiliary Services   │
│                  │  │                │  │                       │
│ - Auth Service   │  │ - Todoist      │  │ - Telemetry Service  │
│ - Habit Service  │  │ - GitHub       │  │ - Analytics Service  │
│ - User Service   │  │ - Google Cal   │  │ - Gamification       │
│ - Project Service│  │ - Slack        │  │ - Notification Service│
└────────┬─────────┘  └───────┬────────┘  └────────┬──────────────┘
         │                    │                     │
         ▼                    ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Data Layer                                   │
│                                                                   │
│   ┌──────────────┐   ┌───────────────┐   ┌────────────────────┐  │
│   │  PostgreSQL  │   │ Redis Cache & │   │ Background Workers │  │
│   │  (SQLAlchemy)│   │ Queue (RQ)    │   │ (Integration Sync) │  │
│   └──────────────┘   └───────────────┘   └────────────────────┘  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
             │                   │                   │
             ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Observability                                │
│                                                                   │
│   ┌──────────────┐   ┌───────────────┐   ┌────────────────────┐  │
│   │  Prometheus  │   │ Grafana       │   │ Structured Logging │  │
│   │  Metrics     │   │ Dashboards    │   │ (JSON, Loki)       │  │
│   └──────────────┘   └───────────────┘   └────────────────────┘  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Backend API (FastAPI)

The backend uses FastAPI to provide a modern, high-performance API with automatic OpenAPI documentation, data validation, and asynchronous request handling.

**Key Design Patterns:**

- **Repository Pattern**: Separates data access logic from business logic
- **Dependency Injection**: Clean dependency management via FastAPI's dependency system
- **Service Layer**: Business logic encapsulated in service classes
- **Unit of Work**: Transactions and session management
- **CQRS-inspired**: Separation of command and query responsibilities

**Security Features:**

- JWT authentication with proper token rotation
- OAuth2/OIDC integration with PKCE
- 2FA with TOTP
- Rate limiting
- CSRF protection
- Security headers (CSP, HSTS)

**Code Structure:**

```
backend/
├── api/                  # API routes and endpoints
│   ├── v1/               # API version 1
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── habits.py     # Habit management endpoints
│   │   ├── projects.py   # Project management endpoints
│   │   ├── analytics.py  # Analytics endpoints
│   │   └── ...
├── core/                 # Core application components
│   ├── config.py         # Application configuration
│   ├── security.py       # Security utilities
│   ├── exceptions.py     # Custom exceptions
│   └── dependencies.py   # FastAPI dependencies
├── db/                   # Database components
│   ├── base.py           # Base database functionality
│   ├── session.py        # Database session management
│   └── repositories/     # Repository implementations
├── models/               # SQLAlchemy models
├── schemas/              # Pydantic schemas
├── services/             # Business logic services
├── utils/                # Utility functions
├── workers/              # Background workers
└── main.py               # Application entry point
```

### 2. Frontend (React + Vite)

The frontend is built with React and Vite for a fast, modern web experience with responsive design and component-based architecture.

**Key Design Patterns:**

- **Component Composition**: UI built from reusable components
- **Custom Hooks**: Encapsulating reusable logic
- **Context API**: State management for shared state
- **Suspense & Error Boundaries**: For loading states and error handling
- **React Query**: For data fetching, caching, and synchronization

**Code Structure:**

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── ui/          # Basic UI components (Button, Card, etc.)
│   │   ├── habits/      # Habit-related components
│   │   ├── analytics/   # Analytics components
│   │   └── ...
│   ├── hooks/           # Custom React hooks
│   ├── contexts/        # React context providers
│   ├── pages/           # Page components
│   ├── services/        # API service functions
│   ├── utils/           # Utility functions
│   ├── types/           # TypeScript type definitions
│   ├── App.jsx          # Main App component
│   └── main.jsx         # Application entry point
├── index.html           # HTML template
└── vite.config.js       # Vite configuration
```

### 3. Mobile App (React Native / Expo)

The mobile app uses React Native with Expo for cross-platform (iOS/Android) development with a focus on offline-first and sync capabilities.

**Key Features:**

- **Offline-First**: Local SQLite database
- **Background Sync**: Push/pull with conflict resolution
- **Deep Linking**: For OIDC authentication
- **Secure Storage**: For sensitive data (tokens)
- **Push Notifications**: For reminders and updates

**Code Structure:**

```
mobile/
├── app/                 # Expo Router screens
├── assets/              # App assets (images, fonts)
├── components/          # Reusable components
├── hooks/               # Custom hooks
├── services/            # API and local services
├── store/               # State management
├── utils/               # Utility functions
├── App.tsx              # Main App component
└── app.json             # Expo configuration
```

### 4. Data Models

#### Core Entities

- **User**: Authentication and profile information
- **Habit**: Recurring actions to track
- **Project**: Grouping of related habits
- **HabitLog**: Record of habit completions
- **Achievement**: Gamification rewards

#### Entity Relationships

```
User 1──*  Project
 │
 │
 ├───1──*  Habit
 │         │
 │         │
 │         └───1──*  HabitLog
 │
 └───1──*  Achievement
 │
 └───1──*  Integration
          │
          └───1──*  IntegrationItem
```

### 5. Integration System

The integration system connects with external services like Todoist, GitHub, and Google Calendar using a pluggable adapter pattern.

**Key Components:**

- **Provider Interface**: Common interface for all integrations
- **Adapter Pattern**: Specific implementations for each provider
- **OAuth Flow**: Secure token handling and refresh
- **Webhook Receivers**: For real-time updates
- **Background Sync**: Periodic syncing with rate limiting and backoff

### 6. Gamification Engine

The gamification engine motivates users through RPG-like progression mechanics.

**Key Features:**

- **XP System**: Points for completing habits
- **Leveling**: Progression based on accumulated XP
- **Achievements**: Special rewards for milestones
- **Streaks**: Consecutive completion tracking
- **Leaderboards**: Optional social comparison

**Implementation:**

```python
class GamificationService:
    async def award_xp(self, user_id: int, amount: int, source: str) -> dict:
        """Award XP to a user and handle level ups and achievements."""
        
    async def check_achievements(self, user_id: int, action: str, metadata: dict) -> list:
        """Check if an action triggers any achievements."""
        
    async def update_streak(self, user_id: int, habit_id: int) -> dict:
        """Update streak counters for a habit."""
```

## Architectural Decisions

### Database Choice: PostgreSQL (Production) / SQLite (Development)

**Rationale**:
- **PostgreSQL**: Robust, ACID-compliant, supports complex queries and indexes
- **SQLite**: Simple setup for development and testing
- **SQLAlchemy**: ORM abstraction allows for easy switching between databases

### Authentication: JWT + OAuth2/OIDC

**Rationale**:
- **JWT**: Stateless authentication with low overhead
- **OAuth2/OIDC**: Secure delegation, no password storage, multi-provider support
- **PKCE**: Enhanced security for mobile and SPA clients

### Background Processing: Redis + RQ

**Rationale**:
- **Redis**: Fast, reliable queue with persistence options
- **RQ**: Simple Python interface with good monitoring
- **Worker Resilience**: Retries, backoff, and concurrency management

### Caching Strategy: Multi-level

**Rationale**:
- **Browser Cache**: Static assets with appropriate cache headers
- **Redis Cache**: API responses and computation results
- **Memory Cache**: Frequent lookups (e.g., user permissions)

### API Versioning

**Rationale**:
- **URL-based Versioning**: Clear, explicit API versions (e.g., `/api/v1/`)
- **Backwards Compatibility**: Maintain older versions during transitions
- **API Deprecation Policy**: Clear communication about deprecated endpoints

## Performance Considerations

### 1. Database Optimization

- **Indexes**: Strategic indexes on frequently queried fields
- **Connection Pooling**: Reuse database connections
- **Query Optimization**: Minimize N+1 queries using proper joins
- **Pagination**: For large result sets

### 2. Caching Strategy

- **Cache Headers**: HTTP caching for static assets
- **API Response Caching**: Cache common API responses
- **Computed Values**: Cache expensive calculations

### 3. Frontend Performance

- **Code Splitting**: Load only needed code
- **Tree Shaking**: Eliminate unused code
- **Lazy Loading**: Defer loading of non-critical components
- **Image Optimization**: Proper formats and sizes

## Security Architecture

### 1. Authentication & Authorization

- **JWT**: Secure, short-lived tokens
- **Refresh Tokens**: For session persistence
- **RBAC**: Role-based access control
- **2FA**: Additional security layer

### 2. Data Protection

- **HTTPS**: All traffic encrypted
- **Encrypted Storage**: Sensitive data encrypted at rest
- **Input Validation**: Prevent injection attacks
- **Output Encoding**: Prevent XSS

### 3. API Security

- **Rate Limiting**: Prevent abuse
- **CORS**: Restrict origins
- **CSRF Protection**: Prevent cross-site request forgery
- **Security Headers**: CSP, HSTS, etc.

## Observability & Monitoring

### 1. Metrics

- **Application Metrics**: Request rates, error rates, response times
- **Business Metrics**: User activity, habit completions, achievements
- **System Metrics**: CPU, memory, disk usage

### 2. Logging

- **Structured Logging**: JSON format for machine parsing
- **Log Levels**: Error, warning, info, debug
- **Context Enrichment**: User ID, request ID, etc.

### 3. Alerting

- **SLO-based Alerts**: Alert on service level objective violations
- **Error Rate Thresholds**: Alert on elevated error rates
- **Custom Business Alerts**: Unusual patterns in user behavior

## Future Architecture Considerations

### 1. Microservices Evolution

As the system grows, consider splitting into true microservices:
- **Auth Service**: Handle authentication and authorization
- **Habit Service**: Core habit tracking functionality
- **Integration Service**: Manage external integrations
- **Gamification Service**: Handle XP, levels, and achievements

### 2. Event-Driven Architecture

Introduce event sourcing and CQRS for complex domains:
- **Event Bus**: Publish domain events
- **Event Sourcing**: Store state changes as events
- **CQRS**: Separate read and write models

### 3. Serverless Components

For appropriate workloads:
- **API Lambdas**: Serverless API endpoints
- **Event Processors**: Serverless event handlers
- **Scheduled Tasks**: Serverless cron jobs

## Plugin System Design (Planned)

The planned plugin system will allow extending LifeRPG with custom functionality:

### 1. Plugin Architecture

- **WASM-based Sandbox**: Secure execution environment
- **Plugin Manifest**: Metadata, permissions, and dependencies
- **Lifecycle Hooks**: Initialize, execute, and clean up
- **Versioning**: Plugin and API version compatibility

### 2. Extension Points

- **Custom Visualizations**: Add new charts and views
- **Integration Adapters**: Connect to additional services
- **Habit Templates**: Predefined habit configurations
- **Achievement Rules**: Custom achievement conditions

### 3. Security Model

- **Permission System**: Granular permissions for plugins
- **Resource Limits**: Memory, CPU, and network constraints
- **Approval Process**: Optional plugin verification

## Conclusion

The LifeRPG architecture is designed for scalability, maintainability, and security while providing a rich user experience. This guide serves as a living document that will evolve with the project.

---

## Appendix: Technology Stack

### Backend
- **Language**: Python 3.10+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Migration**: Alembic
- **Authentication**: JWT, OAuth2/OIDC
- **Background Jobs**: Redis + RQ
- **Testing**: Pytest

### Frontend
- **Framework**: React 18+
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **State Management**: React Context + React Query
- **UI Components**: Custom component library
- **Charts**: Recharts
- **Testing**: Vitest + React Testing Library

### Mobile
- **Framework**: React Native / Expo
- **Navigation**: React Navigation
- **Local Storage**: Expo SQLite
- **Authentication**: react-native-app-auth
- **Secure Storage**: expo-secure-store
- **Background Tasks**: expo-background-fetch

### Infrastructure
- **Database**: PostgreSQL (production), SQLite (development)
- **Caching**: Redis
- **Observability**: Prometheus, Grafana, Loki
- **CI/CD**: GitHub Actions
- **Containerization**: Docker

### Development Tools
- **Linting**: ESLint, Flake8
- **Formatting**: Prettier, Black
- **Documentation**: OpenAPI, MkDocs
- **Dependency Management**: Poetry (Python), npm (JS/TS)

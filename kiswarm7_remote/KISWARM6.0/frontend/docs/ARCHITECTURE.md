# KINFP-Portal Architecture & Design Documentation

## System Architecture Overview

KINFP-Portal follows a modern full-stack architecture with clear separation of concerns between frontend, backend, and data layers. The system is designed for scalability, type safety, and real-time responsiveness.

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ React 18 + TypeScript + Tailwind CSS + shadcn/ui        │   │
│  │ ├─ Pages (15+ feature pages)                            │   │
│  │ ├─ Components (UI, Charts, Forms)                       │   │
│  │ ├─ Contexts (Auth, Notifications, KIWZB)               │   │
│  │ ├─ Hooks (useAuth, useNotification, etc.)              │   │
│  │ └─ Services (WebSocket, tRPC Client)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬─────────────────────────────────────────┘
                         │ tRPC HTTP Batch Link
                         │ Superjson Serialization
┌────────────────────────▼─────────────────────────────────────────┐
│                    API Gateway Layer                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Express 4 + Node.js + tRPC 11                           │   │
│  │ ├─ /api/trpc/* - tRPC procedures                        │   │
│  │ ├─ /api/oauth/* - OAuth callback                        │   │
│  │ ├─ /api/health - Health checks                          │   │
│  │ ├─ WebSocket - Real-time updates                        │   │
│  │ └─ Middleware (Auth, Logging, Error Handling)           │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬─────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼────┐   ┌──────▼──────┐   ┌────▼──────────┐
│  Database  │   │  File       │   │ External      │
│  Layer     │   │  Storage    │   │ Services      │
│ ┌────────┐ │   │ ┌────────┐  │   │ ┌──────────┐  │
│ │ MySQL  │ │   │ │ S3     │  │   │ │ Manus    │  │
│ │ TiDB   │ │   │ │ (Manus)│  │   │ │ OAuth    │  │
│ └────────┘ │   │ └────────┘  │   │ │ LLM      │  │
│ ┌────────┐ │   │ ┌────────┐  │   │ │ Storage  │  │
│ │Drizzle │ │   │ │Presigned│  │   │ │ Webhook │  │
│ │ ORM    │ │   │ │ URLs   │  │   │ │ API      │  │
│ └────────┘ │   │ └────────┘  │   │ └──────────┘  │
└────────────┘   └─────────────┘   └───────────────┘
```

## Component Architecture

### Frontend Architecture

The frontend is organized into a modular component-based architecture:

```
src/
├── pages/                    # Page-level components (route-specific)
│   ├── Home.tsx             # Landing page
│   ├── AdminDashboard.tsx   # Admin interface
│   ├── FileManager.tsx      # File upload/download
│   └── ... (15+ pages)
├── components/              # Reusable UI components
│   ├── DashboardLayout.tsx  # Sidebar layout wrapper
│   ├── AIChatBox.tsx        # Chat interface
│   ├── Map.tsx              # Google Maps integration
│   └── ui/                  # shadcn/ui components
│       ├── button.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       └── ... (20+ components)
├── contexts/                # React Context for global state
│   ├── AuthContext.tsx      # User authentication state
│   ├── NotificationContext.tsx
│   └── KIWZBContext.tsx     # KIWZB-specific data
├── hooks/                   # Custom React hooks
│   ├── useAuth.ts           # Authentication hook
│   ├── useNotification.ts   # Notification hook
│   └── useWebSocket.ts      # WebSocket hook
├── lib/                     # Utility functions and services
│   ├── trpc.ts              # tRPC client setup
│   ├── kiwzb-api.ts         # KIWZB backend integration
│   ├── websocket.ts         # WebSocket service
│   └── utils.ts             # Helper functions
├── App.tsx                  # Router and layout
├── main.tsx                 # Entry point with providers
└── index.css                # Global styles and CSS variables
```

### Backend Architecture

The backend follows a layered architecture with clear separation of concerns:

```
server/
├── routers/                 # tRPC procedure routers
│   ├── files.ts             # File management procedures
│   ├── files.test.ts        # Unit tests
│   └── ... (other routers)
├── _core/                   # Framework internals (do not modify)
│   ├── index.ts             # Server entry point
│   ├── context.ts           # tRPC context builder
│   ├── trpc.ts              # tRPC router setup
│   ├── oauth.ts             # OAuth handling
│   ├── cookies.ts           # Cookie management
│   ├── llm.ts               # LLM integration
│   ├── storage.ts           # S3 helpers
│   ├── notification.ts      # Owner notifications
│   ├── env.ts               # Environment variables
│   ├── types/               # TypeScript type definitions
│   └── vite.ts              # Vite integration
├── db.ts                    # Database query helpers
├── routers.ts               # Main router combining all sub-routers
└── storage.ts               # S3 file storage implementation
```

### Database Schema

The database uses Drizzle ORM for type-safe queries:

```typescript
// Users table
users {
  id: number (PK)
  openId: string (unique)
  name: string | null
  email: string | null
  loginMethod: string | null
  role: "user" | "admin"
  createdAt: Date
  updatedAt: Date
  lastSignedIn: Date
}

// Files table
files {
  id: number (PK)
  userId: number (FK → users.id)
  fileName: string
  fileKey: string (S3 key)
  fileUrl: string (CDN URL)
  contentType: string
  fileSize: number
  category: "document" | "image" | "video" | "archive" | "other"
  description: string | null
  uploadedAt: Date
  createdAt: Date
}
```

## Data Flow Architecture

### Request-Response Flow

```
1. Frontend Component
   └─ Calls: trpc.files.upload.useMutation()
   
2. tRPC Client
   └─ Serializes with Superjson
   └─ Sends HTTP POST to /api/trpc/files.upload
   
3. Express Server
   └─ Routes to tRPC handler
   └─ Validates input with Zod schema
   
4. tRPC Procedure
   └─ Extracts user from ctx
   └─ Calls database helper
   
5. Database Layer (Drizzle ORM)
   └─ Executes type-safe SQL query
   └─ Returns raw result
   
6. File Storage (S3)
   └─ Uploads file bytes
   └─ Returns CDN URL
   
7. Response Serialization
   └─ Superjson serializes response
   └─ Sends HTTP 200 with JSON
   
8. Frontend Update
   └─ React Query caches result
   └─ Component re-renders with data
```

### Real-Time Update Flow

```
1. Backend Event
   └─ File uploaded, order created, etc.
   
2. WebSocket Server
   └─ Broadcasts message to connected clients
   └─ Includes event type and data
   
3. Frontend WebSocket Listener
   └─ Receives message
   └─ Triggers notification toast
   
4. React Query Invalidation
   └─ Invalidates related queries
   └─ Triggers refetch
   
5. Component Update
   └─ New data displayed
   └─ User sees real-time update
```

## Authentication Flow

The application uses Manus OAuth for user authentication:

```
1. User clicks "Login"
   └─ Redirected to getLoginUrl()
   
2. Manus OAuth Portal
   └─ User enters credentials
   └─ Grants application access
   
3. OAuth Callback
   └─ Browser redirected to /api/oauth/callback
   └─ Backend receives authorization code
   
4. Token Exchange
   └─ Backend exchanges code for tokens
   └─ Creates session cookie
   
5. Session Management
   └─ Frontend reads session cookie
   └─ Includes in all tRPC requests
   
6. Context Building
   └─ Each request builds ctx.user
   └─ User available in procedures
   
7. Protected Procedures
   └─ Check if ctx.user exists
   └─ Throw UNAUTHORIZED if missing
```

## Error Handling Architecture

The application implements comprehensive error handling at multiple layers:

```
Frontend Layer
├─ Input validation (Zod schemas)
├─ Error boundaries (React)
├─ Toast notifications (user feedback)
└─ Automatic retry logic

API Layer
├─ tRPC error codes (standardized)
├─ Error middleware (logging)
├─ Error serialization (Superjson)
└─ HTTP status codes (correct mapping)

Database Layer
├─ Transaction rollback (on failure)
├─ Constraint validation
├─ Query error handling
└─ Connection error recovery

File Storage Layer
├─ Upload failure handling
├─ Presigned URL expiration
├─ Access control validation
└─ Cleanup on error
```

## Performance Architecture

### Frontend Optimization

**Code Splitting**: Vite automatically splits code by route, reducing initial bundle size.

**Image Optimization**: CDN-hosted images with responsive sizing and WebP format.

**React Query Caching**: Automatic caching of API responses with configurable stale times.

**Lazy Loading**: Routes and components loaded on-demand.

### Backend Optimization

**Database Connection Pooling**: Reuses connections to avoid overhead.

**Query Optimization**: Drizzle ORM generates efficient SQL with proper indexing.

**Response Caching**: Frequently accessed data cached in memory.

**Batch Requests**: tRPC HTTP batch link reduces network round-trips.

### Database Optimization

**Indexing Strategy**:
```sql
-- Frequently queried columns
CREATE INDEX idx_userId ON files(userId);
CREATE INDEX idx_category ON files(category);
CREATE INDEX idx_uploadedAt ON files(uploadedAt);

-- Composite indexes for common queries
CREATE INDEX idx_userId_category ON files(userId, category);
```

**Query Optimization**: Use Drizzle's type-safe query builder to prevent N+1 queries.

## Security Architecture

### Authentication & Authorization

**Session Management**: Secure HTTP-only cookies with SameSite attribute.

**JWT Tokens**: Signed with HS256 algorithm using strong secret.

**Role-Based Access Control**: Admin vs User roles enforced at procedure level.

**User Isolation**: All queries filtered by `ctx.user.id` to prevent data leaks.

### Data Protection

**Database Security**:
- SSL/TLS connection to database
- Strong password policies
- Regular backups
- Encryption at rest (optional)

**File Storage Security**:
- Files stored with random suffixes to prevent enumeration
- Presigned URLs with expiration times
- Access control per user
- Metadata stored in database

**API Security**:
- Input validation with Zod schemas
- Rate limiting (recommended for production)
- CORS configuration
- HTTPS enforcement

## Scalability Architecture

### Horizontal Scaling

The application is designed to scale horizontally:

**Stateless Backend**: Each server instance can handle requests independently.

**Shared Database**: All instances connect to same MySQL/TiDB cluster.

**Load Balancing**: Nginx or cloud load balancer distributes traffic.

**Session Persistence**: Cookies work across all instances.

### Vertical Scaling

**Database Optimization**: Proper indexing and query optimization.

**Memory Management**: Connection pooling and caching strategies.

**Resource Monitoring**: PM2 or cloud monitoring for resource usage.

## Deployment Architecture

### Development Environment

```
Local Machine
├─ Vite Dev Server (port 3000)
├─ Express Backend (port 3000)
├─ MySQL Database (port 3306)
└─ Hot Module Replacement (HMR)
```

### Production Environment

```
Cloud Infrastructure (Manus WebDev)
├─ Nginx Reverse Proxy
│  └─ SSL/TLS termination
│  └─ Load balancing
├─ Node.js Application Servers
│  └─ PM2 process management
│  └─ Auto-restart on crash
├─ MySQL/TiDB Database
│  └─ Automated backups
│  └─ High availability
└─ S3 Storage (Manus Proxy)
   └─ CDN distribution
   └─ Automatic scaling
```

## Technology Decisions

### Why tRPC?

**Type Safety**: End-to-end type checking without separate API documentation.

**Developer Experience**: Autocomplete and IntelliSense for API procedures.

**Minimal Overhead**: No schema files or code generation needed.

**Superjson**: Automatic serialization of complex types like `Date`.

### Why Drizzle ORM?

**Type Safety**: SQL queries are type-checked at compile time.

**Performance**: Generates efficient SQL without query builder overhead.

**Migrations**: Version-controlled schema changes with rollback support.

**Relations**: Type-safe relationships between tables.

### Why React Query?

**Caching**: Automatic caching of API responses.

**Synchronization**: Keeps frontend and backend data in sync.

**Offline Support**: Works with offline-first architectures.

**DevTools**: Built-in debugging and monitoring.

## Extension Points

### Adding a New Feature

To add a new feature, follow this pattern:

**1. Define Database Schema**
```typescript
// drizzle/schema.ts
export const newFeature = sqliteTable('new_feature', {
  id: integer('id').primaryKey(),
  userId: integer('user_id').notNull(),
  // ... other columns
});
```

**2. Create Database Helpers**
```typescript
// server/db.ts
export async function createNewFeature(db: Database, data: NewFeatureInput) {
  return db.insert(newFeature).values(data);
}
```

**3. Create tRPC Procedures**
```typescript
// server/routers/newFeature.ts
export const newFeatureRouter = router({
  create: protectedProcedure
    .input(NewFeatureInputSchema)
    .mutation(async ({ ctx, input }) => {
      return createNewFeature(db, input);
    }),
});
```

**4. Add to Main Router**
```typescript
// server/routers.ts
export const appRouter = router({
  newFeature: newFeatureRouter,
  // ... other routers
});
```

**5. Create Frontend Component**
```typescript
// client/src/pages/NewFeature.tsx
export default function NewFeature() {
  const mutation = trpc.newFeature.create.useMutation();
  // ... component code
}
```

**6. Write Tests**
```typescript
// server/routers/newFeature.test.ts
describe('newFeatureRouter', () => {
  it('should create new feature', async () => {
    // ... test code
  });
});
```

## Monitoring & Observability

### Application Monitoring

**PM2 Monitoring**: Track CPU, memory, and restart count.

```bash
pm2 monit
pm2 logs kinfp-portal
```

**Error Logging**: All errors logged with context for debugging.

**Performance Metrics**: tRPC request duration and database query times.

### Database Monitoring

**Query Performance**: Use `EXPLAIN` to analyze slow queries.

```sql
EXPLAIN SELECT * FROM files WHERE userId = 1;
```

**Connection Pooling**: Monitor active connections and pool utilization.

**Backup Status**: Verify automated backups are running.

### Infrastructure Monitoring

**Disk Space**: Monitor database and file storage usage.

**Memory Usage**: Alert on high memory consumption.

**Network**: Monitor bandwidth and connection errors.

---

**Last Updated**: March 4, 2026  
**Version**: 13.0  
**Architecture Pattern**: Full-Stack Type-Safe with tRPC

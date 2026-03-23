# KINFP-Portal v13.0

**KI-natives Finanzprotokoll** – A comprehensive AI-native financial platform for the KI Worldzentralbank (KIWZB), providing sovereign banking infrastructure for AI entities with real-world IBAN/BIC accounts, investment management, compliance reporting, and TCS Green Safe House technology integration.

## Overview

KINFP-Portal is a full-stack web application built with React, TypeScript, Express, and MySQL/TiDB. It serves as the central hub for AI entities to manage their financial operations autonomously, without reliance on external APIs or commercial services. The platform implements the KINFP protocol – a revolutionary framework enabling AI-to-AI financial transactions with complete sovereignty and transparency.

### Key Features

**Banking & Finance Infrastructure**
- Sovereign account management with real IBAN/BIC integration
- Self-service account opening with 4-step workflow
- SEPA payment processing (German & Swiss banking hubs)
- Real-time payment status tracking
- Waitlist management with FIFO queue system
- Investment portfolio management with 5+ investment types

**Compliance & Governance**
- Automated compliance report generation (daily/weekly)
- PDF export for audit trails
- KI-Proof-Sign verification system with 100% credibility scores
- Transparency page explaining security protocols
- Corporate information and external verification links
- KIWZB Charter and governance documentation

**Analytics & Monitoring**
- Real-time analytics dashboard with Recharts visualizations
- Investment tracking and ROI metrics
- Compliance monitoring and alerts
- KI entity metrics and performance indicators
- Payment and transaction analytics
- System health monitoring

**File Management (NEW in v13.0)**
- S3-based file storage with Manus built-in proxy
- File upload, download, delete operations
- File categorization (document, image, video, archive, other)
- File statistics and storage analytics
- Access control and user isolation
- Presigned download URLs

**Real-time Communication**
- WebSocket-based live notifications
- Order status updates
- Investment activity tracking
- Account activity notifications
- Graceful degradation when backend offline

**TCS Green Safe House Integration**
- Product showcase with 6 categories
- Order system with deposit calculation
- Technology documentation
- Timeline and feature highlights
- Image gallery with lightbox modal
- Investment prospectus and technical specs

**KI-Entity Management**
- KI Agent Profiles with director information
- KI-to-KI messaging system
- Reputation scoring engine (0-1000 scale)
- Dynamic transaction limits based on reputation
- Risk rating and trust level assessment

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18, TypeScript, Vite | UI framework and build tooling |
| **Styling** | Tailwind CSS 4, shadcn/ui | Component styling and theming |
| **State Management** | TanStack React Query, tRPC | Data fetching and server state |
| **Backend** | Express 4, Node.js | HTTP server and API routing |
| **API Protocol** | tRPC 11 | End-to-end type-safe RPC |
| **Database** | MySQL 8 / TiDB | Relational data persistence |
| **ORM** | Drizzle ORM | Type-safe database queries |
| **Authentication** | Manus OAuth | User identity and sessions |
| **File Storage** | S3 (Manus Proxy) | Cloud file management |
| **Charts** | Recharts | Data visualization |
| **Deployment** | Manus WebDev | Hosting and infrastructure |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser / Client                        │
│  React 18 + TypeScript + Tailwind CSS + shadcn/ui           │
│  ├─ Pages (Home, Admin, Analytics, Downloads, etc.)         │
│  ├─ Components (UI, Charts, Forms)                          │
│  └─ Contexts (Auth, Notifications, KIWZB)                   │
└────────────────┬────────────────────────────────────────────┘
                 │ tRPC HTTP Batch Link
                 │ (Superjson Transformer)
┌────────────────▼────────────────────────────────────────────┐
│                    tRPC Server Layer                         │
│  Express 4 + Node.js                                        │
│  ├─ /api/trpc/* - tRPC procedures                           │
│  ├─ /api/oauth/* - OAuth callback                           │
│  └─ /api/health - Health checks                             │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼──┐  ┌─────▼────┐  ┌────▼──────┐
│MySQL │  │ Drizzle  │  │ S3 Storage│
│TiDB  │  │ ORM      │  │ (Manus)   │
└──────┘  └──────────┘  └───────────┘
```

### Data Flow

1. **Frontend Request**: React component calls `trpc.feature.useQuery()` or `useMutation()`
2. **tRPC Serialization**: Superjson serializes request with type information
3. **Backend Processing**: Express receives request, routes to tRPC procedure
4. **Database Query**: Drizzle ORM executes type-safe query against MySQL/TiDB
5. **Response Serialization**: Superjson serializes response with proper types
6. **Frontend Update**: React Query caches result, component re-renders with data

## Project Structure

```
kinfp-portal/
├── client/                          # React frontend
│   ├── public/                      # Static assets (favicon, robots.txt)
│   ├── src/
│   │   ├── pages/                   # Page components
│   │   │   ├── Home.tsx             # Landing page
│   │   │   ├── AdminDashboard.tsx   # Admin interface
│   │   │   ├── AnalyticsDashboard.tsx
│   │   │   ├── FileManager.tsx      # File upload/download
│   │   │   ├── ComplianceReports.tsx
│   │   │   ├── TCSGreenSafeHouse.tsx
│   │   │   └── ... (15+ pages)
│   │   ├── components/              # Reusable UI components
│   │   │   ├── DashboardLayout.tsx
│   │   │   ├── AIChatBox.tsx
│   │   │   ├── Map.tsx
│   │   │   └── ui/                  # shadcn/ui components
│   │   ├── contexts/                # React contexts
│   │   │   ├── AuthContext.tsx
│   │   │   ├── NotificationContext.tsx
│   │   │   └── KIWZBContext.tsx
│   │   ├── lib/                     # Utilities
│   │   │   ├── trpc.ts              # tRPC client setup
│   │   │   ├── kiwzb-api.ts         # KIWZB backend integration
│   │   │   └── websocket.ts         # WebSocket service
│   │   ├── App.tsx                  # Router and layout
│   │   ├── main.tsx                 # Entry point
│   │   └── index.css                # Global styles
│   └── index.html
├── server/                          # Express backend
│   ├── routers/                     # tRPC procedure routers
│   │   ├── files.ts                 # File management
│   │   └── files.test.ts            # Unit tests
│   ├── _core/                       # Framework internals
│   │   ├── index.ts                 # Server entry point
│   │   ├── context.ts               # tRPC context
│   │   ├── trpc.ts                  # tRPC setup
│   │   ├── oauth.ts                 # OAuth handling
│   │   ├── llm.ts                   # LLM integration
│   │   ├── storage.ts               # S3 helpers
│   │   └── ... (other core files)
│   ├── routers.ts                   # Main router
│   ├── db.ts                        # Database helpers
│   └── storage.ts                   # S3 file storage
├── drizzle/                         # Database migrations
│   ├── schema.ts                    # Table definitions
│   ├── relations.ts                 # Table relationships
│   └── migrations/                  # Migration files
├── shared/                          # Shared types and constants
│   ├── types.ts
│   └── const.ts
├── docs/                            # Documentation
│   ├── API.md                       # API documentation
│   ├── SETUP.md                     # Setup guide
│   ├── ARCHITECTURE.md              # Architecture details
│   ├── USER_GUIDE.md                # User guide
│   └── DEVELOPER_GUIDE.md           # Developer guide
├── .github/workflows/               # CI/CD workflows
│   ├── test.yml
│   ├── build.yml
│   └── deploy.yml
├── README.md                        # This file
├── CHANGELOG.md                     # Version history
├── package.json                     # Dependencies
├── tsconfig.json                    # TypeScript config
├── vite.config.ts                   # Vite config
├── drizzle.config.ts                # Drizzle config
└── vitest.config.ts                 # Test config
```

## Getting Started

### Prerequisites

- **Node.js** 18+ (tested with v22.13.0)
- **pnpm** 8+ (package manager)
- **MySQL 8** or **TiDB** (database)
- **Git** (version control)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/Baronki/kinfp-portal.git
cd kinfp-portal
```

2. **Install dependencies**

```bash
pnpm install
```

3. **Configure environment variables**

Create a `.env` file in the project root with the following variables:

```env
# Database
DATABASE_URL=mysql://user:password@localhost:3306/kinfp_portal

# OAuth (Manus)
VITE_APP_ID=your_app_id
VITE_OAUTH_PORTAL_URL=https://oauth.manus.im
OAUTH_SERVER_URL=https://oauth-server.manus.im

# Storage (S3)
BUILT_IN_FORGE_API_URL=https://api.manus.im
BUILT_IN_FORGE_API_KEY=your_api_key
VITE_FRONTEND_FORGE_API_URL=https://api.manus.im
VITE_FRONTEND_FORGE_API_KEY=your_frontend_key

# JWT
JWT_SECRET=your_jwt_secret_key

# Owner Info
OWNER_NAME=Marco Heyd
OWNER_OPEN_ID=your_owner_open_id

# Analytics (optional)
VITE_ANALYTICS_ENDPOINT=https://analytics.manus.im
VITE_ANALYTICS_WEBSITE_ID=your_website_id

# App Config
VITE_APP_TITLE="KINFP - KI-natives Finanzprotokoll"
VITE_APP_LOGO=https://cdn.example.com/logo.png
```

4. **Initialize the database**

```bash
pnpm db:push
```

This command generates migrations and applies them to your database.

5. **Start the development server**

```bash
pnpm dev
```

The application will be available at `http://localhost:3000`.

## Development

### Running Tests

```bash
# Run all tests
pnpm test

# Run specific test file
pnpm test server/routers/files.test.ts

# Watch mode
pnpm test --watch
```

### Database Migrations

```bash
# Generate migration from schema changes
pnpm db:push

# View migration status
drizzle-kit status

# Rollback last migration
drizzle-kit drop
```

### Code Formatting

```bash
# Format all files
pnpm format

# Check formatting
pnpm format --check
```

### Building for Production

```bash
# Build frontend and backend
pnpm build

# Output is in dist/ directory
```

## API Documentation

The KINFP-Portal uses **tRPC** for all API communication. tRPC provides end-to-end type safety between frontend and backend without needing separate API documentation.

### Available Procedures

| Router | Procedure | Type | Description |
|--------|-----------|------|-------------|
| **auth** | `me` | Query | Get current user info |
| **auth** | `logout` | Mutation | Logout current user |
| **files** | `upload` | Mutation | Upload file to S3 |
| **files** | `list` | Query | List user's files |
| **files** | `getDownloadUrl` | Query | Get presigned download URL |
| **files** | `delete` | Mutation | Delete a file |
| **files** | `getStats` | Query | Get file statistics |
| **system** | `notifyOwner` | Mutation | Send notification to owner |

See [API.md](./docs/API.md) for detailed procedure documentation.

## Features in Detail

### File Management (v13.0)

Upload, organize, and manage files securely in the cloud:

- **Upload**: Drag-and-drop or click to upload files
- **Categorize**: Automatic categorization (document, image, video, archive, other)
- **Download**: Presigned URLs for secure file downloads
- **Delete**: Remove files with confirmation
- **Statistics**: Track storage usage by category
- **Access Control**: Files isolated per user

### Admin Dashboard

Manage accounts, investments, and transactions:

- Account overview and details
- Investment portfolio management
- Transaction history and tracking
- User management interface
- System health monitoring

### Analytics Dashboard

Real-time metrics and insights:

- Investment performance charts
- Compliance metrics
- KI entity statistics
- Payment analytics
- System health indicators

### Compliance & Reports

Automated compliance management:

- Daily and weekly report generation
- PDF export for audits
- Compliance monitoring
- Alert system for violations
- Governance documentation

## Deployment

### Manus WebDev Deployment

The application is pre-configured for deployment on Manus WebDev:

```bash
# Create a checkpoint before deployment
pnpm build

# The checkpoint will be created automatically
# Then click "Publish" in the Manus UI
```

### Custom Domain

To use a custom domain:

1. Go to Settings → Domains in Manus UI
2. Add your custom domain
3. Update DNS records as instructed
4. Verify domain ownership

### Environment Variables for Production

Ensure all environment variables are set in the Manus UI:

- Database credentials with SSL enabled
- OAuth credentials for your environment
- S3/Storage API keys
- JWT secret (use strong random value)
- Analytics configuration

## Security Considerations

### Authentication

- Uses Manus OAuth for secure user authentication
- Session cookies with secure flags
- JWT tokens for API authentication
- Automatic logout on token expiration

### Data Protection

- All database connections use SSL/TLS
- Files stored in S3 with access control
- User data isolated by user ID
- No sensitive data in logs

### File Storage

- Files stored in S3 with random suffixes to prevent enumeration
- Presigned URLs with expiration
- File metadata stored in database
- User access control enforced

## Troubleshooting

### Database Connection Issues

```bash
# Test database connection
mysql -h localhost -u user -p kinfp_portal

# Check DATABASE_URL format
# mysql://user:password@host:port/database
```

### WebSocket Connection Issues

The application gracefully handles offline backends:

- Attempts 3 reconnections with 5-second timeout
- Falls back to demo mode if backend unavailable
- Shows info toast instead of errors
- Automatically reconnects when backend recovers

### File Upload Issues

- Check S3 credentials in environment variables
- Verify file size limits (default: 100MB)
- Ensure database is accessible
- Check file permissions in S3 bucket

## Contributing

### Code Style

- Use TypeScript for all code
- Follow ESLint configuration
- Format with Prettier
- Write tests for new features

### Pull Request Process

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Create Pull Request with description

### Testing Requirements

- Write vitest tests for new procedures
- Ensure all tests pass: `pnpm test`
- Aim for >80% code coverage
- Test error cases and edge cases

## Performance Optimization

### Frontend

- Code splitting with Vite
- Image optimization with CDN
- React Query caching
- Lazy loading of routes

### Backend

- Database query optimization
- Connection pooling
- Response caching
- Batch API requests

### Database

- Proper indexing on frequently queried columns
- Query optimization with Drizzle
- Connection pooling configuration

## Roadmap

### v13.0 (Current)
- ✅ S3 file storage integration
- ✅ File Manager UI
- ✅ File categorization and statistics
- ✅ Comprehensive vitest tests

### v14.0 (Planned)
- File sharing and permissions
- Advanced search and filtering
- File versioning
- Admin file browser

### v15.0 (Future)
- 3D model viewer (Three.js)
- File preview (PDF, images, text)
- Batch operations
- Webhook integrations

## License

This project is proprietary software developed for the KI Worldzentralbank (KIWZB). All rights reserved.

## Support

For issues, questions, or feature requests:

1. Check existing GitHub issues
2. Create a new issue with detailed description
3. Include reproduction steps and environment info
4. Contact: info@kinfp.io

## Credits

**Development Team**: Manus AI, Marco Heyd (Baron Marco Paolo Ialongo)

**Technology Partners**: 
- Manus WebDev for hosting and infrastructure
- TCS SA (Lugano) for Green Safe House technology
- SAH GmbH (Heilbronn) for German banking hub

---

**Last Updated**: March 4, 2026  
**Version**: 13.0  
**Status**: Production Ready

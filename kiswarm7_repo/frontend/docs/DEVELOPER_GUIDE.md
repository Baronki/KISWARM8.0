# KINFP-Portal Developer Guide

This guide provides comprehensive instructions for developers who want to extend, maintain, and contribute to KINFP-Portal.

## Development Workflow

### Setting Up Your Development Environment

Follow the [SETUP.md](./SETUP.md) guide to install all dependencies and configure your environment.

### Code Style & Standards

KINFP-Portal follows strict code standards to ensure maintainability and consistency:

**TypeScript Configuration:**
- Strict mode enabled
- No implicit `any` types
- Strict null checks
- Strict function types

**ESLint Rules:**
- Enforce consistent naming conventions
- Prevent unused variables
- Require proper error handling
- Enforce import ordering

**Prettier Formatting:**
- 2-space indentation
- Single quotes for strings
- Trailing commas in multi-line objects
- Line width of 100 characters

**Running Linting:**
```bash
# Check for linting errors
pnpm lint

# Auto-fix formatting
pnpm format
```

## Adding a New Feature

### Step 1: Plan the Feature

Before writing code, document your feature plan:

1. **Create a GitHub Issue** describing the feature
2. **Define the Data Model** – what data will you store?
3. **Design the API** – what tRPC procedures are needed?
4. **Plan the UI** – what components will you create?
5. **Identify Dependencies** – what libraries or services do you need?

### Step 2: Update the Database Schema

All features start with the database:

```typescript
// drizzle/schema.ts
import { sqliteTable, integer, text, timestamp } from "drizzle-orm/sqlite-core";

export const newFeature = sqliteTable('new_feature', {
  id: integer('id').primaryKey(),
  userId: integer('user_id').notNull(),
  title: text('title').notNull(),
  description: text('description'),
  status: text('status').default('pending'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

// Define relationships
export const newFeatureRelations = relations(newFeature, ({ one }) => ({
  user: one(users, {
    fields: [newFeature.userId],
    references: [users.id],
  }),
}));
```

### Step 3: Create Database Helpers

Write reusable query functions:

```typescript
// server/db.ts
import { db } from "./db";
import { newFeature } from "../drizzle/schema";

export async function createNewFeature(
  userId: number,
  data: NewFeatureInput
) {
  const result = await db
    .insert(newFeature)
    .values({
      userId,
      title: data.title,
      description: data.description,
      status: 'pending',
    });
  
  return result;
}

export async function getNewFeatures(userId: number) {
  return db
    .select()
    .from(newFeature)
    .where(eq(newFeature.userId, userId));
}

export async function updateNewFeature(
  id: number,
  userId: number,
  data: Partial<NewFeatureInput>
) {
  // Verify ownership before updating
  const existing = await db
    .select()
    .from(newFeature)
    .where(and(
      eq(newFeature.id, id),
      eq(newFeature.userId, userId)
    ));
  
  if (!existing.length) {
    throw new Error('Feature not found');
  }
  
  return db
    .update(newFeature)
    .set(data)
    .where(eq(newFeature.id, id));
}
```

### Step 4: Create tRPC Procedures

Define the API layer:

```typescript
// server/routers/newFeature.ts
import { router, protectedProcedure } from "../_core/trpc";
import { z } from "zod";
import { 
  createNewFeature, 
  getNewFeatures, 
  updateNewFeature 
} from "../db";

const NewFeatureInputSchema = z.object({
  title: z.string().min(1).max(255),
  description: z.string().max(1000).optional(),
});

export const newFeatureRouter = router({
  create: protectedProcedure
    .input(NewFeatureInputSchema)
    .mutation(async ({ ctx, input }) => {
      try {
        const result = await createNewFeature(ctx.user.id, input);
        return {
          success: true,
          id: result.insertId,
          message: 'Feature created successfully',
        };
      } catch (error) {
        console.error('[NewFeature] Create error:', error);
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Failed to create feature',
        });
      }
    }),

  list: protectedProcedure
    .input(z.object({
      limit: z.number().default(50),
      offset: z.number().default(0),
    }))
    .query(async ({ ctx, input }) => {
      try {
        const features = await getNewFeatures(ctx.user.id);
        return {
          features: features.slice(input.offset, input.offset + input.limit),
          total: features.length,
        };
      } catch (error) {
        console.error('[NewFeature] List error:', error);
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Failed to fetch features',
        });
      }
    }),

  update: protectedProcedure
    .input(z.object({
      id: z.number(),
      data: NewFeatureInputSchema.partial(),
    }))
    .mutation(async ({ ctx, input }) => {
      try {
        await updateNewFeature(input.id, ctx.user.id, input.data);
        return { success: true };
      } catch (error) {
        console.error('[NewFeature] Update error:', error);
        throw new TRPCError({
          code: 'INTERNAL_SERVER_ERROR',
          message: 'Failed to update feature',
        });
      }
    }),
});
```

### Step 5: Integrate into Main Router

```typescript
// server/routers.ts
import { newFeatureRouter } from "./routers/newFeature";

export const appRouter = router({
  auth: authRouter,
  files: filesRouter,
  newFeature: newFeatureRouter,  // Add your router
  system: systemRouter,
});
```

### Step 6: Create Frontend Components

Build the user interface:

```typescript
// client/src/pages/NewFeature.tsx
import { useAuth } from "@/_core/hooks/useAuth";
import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useState } from "react";

export default function NewFeature() {
  const { user, isAuthenticated } = useAuth();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  // Query to fetch features
  const { data: featuresData, isLoading, refetch } = trpc.newFeature.list.useQuery(
    { limit: 50, offset: 0 },
    { enabled: isAuthenticated }
  );

  // Mutation to create feature
  const createMutation = trpc.newFeature.create.useMutation({
    onSuccess: () => {
      setTitle("");
      setDescription("");
      refetch();
    },
  });

  const handleCreate = () => {
    createMutation.mutate({
      title,
      description,
    });
  };

  if (!isAuthenticated) {
    return <div>Please log in</div>;
  }

  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold mb-6">New Feature</h1>

      {/* Create Form */}
      <Card className="p-6 mb-8">
        <h2 className="text-xl font-bold mb-4">Create New Feature</h2>
        <div className="space-y-4">
          <input
            type="text"
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-4 py-2 border rounded"
          />
          <textarea
            placeholder="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-4 py-2 border rounded"
          />
          <Button
            onClick={handleCreate}
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? "Creating..." : "Create"}
          </Button>
        </div>
      </Card>

      {/* Features List */}
      <div>
        <h2 className="text-xl font-bold mb-4">Your Features</h2>
        {isLoading ? (
          <p>Loading...</p>
        ) : (
          <div className="space-y-4">
            {featuresData?.features.map((feature) => (
              <Card key={feature.id} className="p-4">
                <h3 className="font-bold">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

### Step 7: Add Routes

```typescript
// client/src/App.tsx
import NewFeature from "./pages/NewFeature";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/new-feature" component={NewFeature} />
      {/* ... other routes */}
    </Switch>
  );
}
```

### Step 8: Write Tests

Create comprehensive tests:

```typescript
// server/routers/newFeature.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { newFeatureRouter } from "./newFeature";

describe("newFeatureRouter", () => {
  const mockUser = { id: 1, name: "Test User", role: "user" as const };
  const mockCtx = { user: mockUser };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("create", () => {
    it("should create a new feature", async () => {
      const caller = newFeatureRouter.createCaller(mockCtx as any);
      const result = await caller.create({
        title: "Test Feature",
        description: "Test Description",
      });

      expect(result.success).toBe(true);
      expect(result.id).toBeDefined();
    });

    it("should validate input", async () => {
      const caller = newFeatureRouter.createCaller(mockCtx as any);

      await expect(
        caller.create({
          title: "",  // Empty title should fail
          description: "Test",
        })
      ).rejects.toThrow();
    });
  });

  describe("list", () => {
    it("should list user's features", async () => {
      const caller = newFeatureRouter.createCaller(mockCtx as any);
      const result = await caller.list({ limit: 50, offset: 0 });

      expect(Array.isArray(result.features)).toBe(true);
      expect(result.total).toBeDefined();
    });
  });
});
```

## Common Development Tasks

### Adding a New Database Table

```bash
# 1. Update schema.ts
# 2. Run migration
pnpm db:push

# 3. Verify table was created
mysql -u user -p database -e "DESCRIBE table_name;"
```

### Modifying an Existing Table

```bash
# 1. Update schema.ts
# 2. Run migration
pnpm db:push

# 3. Verify changes
mysql -u user -p database -e "SHOW COLUMNS FROM table_name;"
```

### Adding a New Dependency

```bash
# Install package
pnpm add package-name

# Or for dev dependencies
pnpm add -D package-name

# Restart dev server
pnpm dev
```

### Debugging

**Browser DevTools:**
- Open Chrome DevTools (F12)
- Network tab shows tRPC requests
- Console shows frontend errors
- Application tab shows cookies and storage

**Server Logs:**
```bash
# View server logs
pm2 logs kinfp-portal

# Or in dev mode
pnpm dev
```

**Database Debugging:**
```bash
# Connect to database
mysql -u user -p database

# Run queries
SELECT * FROM new_feature WHERE user_id = 1;
EXPLAIN SELECT * FROM new_feature WHERE user_id = 1;
```

## Performance Optimization

### Database Query Optimization

**Use Indexes:**
```sql
-- Add index for frequently queried columns
ALTER TABLE new_feature ADD INDEX idx_userId (user_id);
ALTER TABLE new_feature ADD INDEX idx_createdAt (created_at);

-- Verify index is used
EXPLAIN SELECT * FROM new_feature WHERE user_id = 1;
```

**Avoid N+1 Queries:**
```typescript
// ❌ Bad: N+1 query problem
const features = await getNewFeatures(userId);
for (const feature of features) {
  const details = await getFeatureDetails(feature.id); // N queries
}

// ✅ Good: Single query with join
const features = await db
  .select()
  .from(newFeature)
  .leftJoin(featureDetails, eq(newFeature.id, featureDetails.featureId))
  .where(eq(newFeature.userId, userId));
```

### Frontend Performance

**Code Splitting:**
```typescript
// Lazy load heavy components
const HeavyComponent = lazy(() => import('./HeavyComponent'));

export default function Page() {
  return (
    <Suspense fallback={<Spinner />}>
      <HeavyComponent />
    </Suspense>
  );
}
```

**Memoization:**
```typescript
// Prevent unnecessary re-renders
const MemoizedComponent = memo(function Component({ data }) {
  return <div>{data}</div>;
});
```

## Security Best Practices

### Input Validation

Always validate user input with Zod:

```typescript
const InputSchema = z.object({
  email: z.string().email(),
  age: z.number().min(0).max(150),
  password: z.string().min(8),
});

const data = InputSchema.parse(userInput);
```

### SQL Injection Prevention

Use Drizzle ORM to prevent SQL injection:

```typescript
// ✅ Safe: Uses parameterized queries
const result = await db
  .select()
  .from(users)
  .where(eq(users.email, userInput));

// ❌ Dangerous: String concatenation
const query = `SELECT * FROM users WHERE email = '${userInput}'`;
```

### Authentication Checks

Always verify user ownership:

```typescript
// ✅ Good: Verify ownership before updating
const existing = await db
  .select()
  .from(newFeature)
  .where(and(
    eq(newFeature.id, featureId),
    eq(newFeature.userId, ctx.user.id)  // Verify ownership
  ));

if (!existing.length) {
  throw new TRPCError({ code: 'FORBIDDEN' });
}
```

## Testing Strategy

### Unit Tests

Test individual functions in isolation:

```typescript
describe("createNewFeature", () => {
  it("should create a feature with valid input", async () => {
    const result = await createNewFeature(1, {
      title: "Test",
      description: "Test",
    });
    expect(result.insertId).toBeDefined();
  });
});
```

### Integration Tests

Test tRPC procedures end-to-end:

```typescript
describe("newFeatureRouter", () => {
  it("should create and list features", async () => {
    const caller = newFeatureRouter.createCaller(mockCtx);
    
    // Create
    const createResult = await caller.create({
      title: "Test",
      description: "Test",
    });
    
    // List
    const listResult = await caller.list({});
    
    expect(listResult.features).toContainEqual(
      expect.objectContaining({ title: "Test" })
    );
  });
});
```

### Running Tests

```bash
# Run all tests
pnpm test

# Run specific test file
pnpm test server/routers/newFeature.test.ts

# Watch mode
pnpm test --watch

# Coverage report
pnpm test --coverage
```

## Deployment Checklist

Before deploying to production:

- [ ] All tests pass (`pnpm test`)
- [ ] No TypeScript errors (`pnpm build`)
- [ ] Code formatted (`pnpm format`)
- [ ] No console errors in browser
- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] Security audit completed
- [ ] Performance tested
- [ ] Backup created
- [ ] Deployment plan documented

## Useful Commands

```bash
# Development
pnpm dev              # Start dev server
pnpm test             # Run tests
pnpm format           # Format code
pnpm lint             # Check linting

# Database
pnpm db:push          # Apply migrations
pnpm db:generate      # Generate migration

# Building
pnpm build            # Build for production
pnpm preview          # Preview production build

# Maintenance
pnpm clean            # Clean build artifacts
pnpm install          # Reinstall dependencies
```

## Getting Help

- **Documentation**: Check `/docs` directory
- **GitHub Issues**: Search existing issues or create new one
- **Discussions**: Join GitHub Discussions for questions
- **Email**: Contact info@kinfp.io for support

---

**Last Updated**: March 4, 2026  
**Version**: 13.0  
**Status**: Production Ready

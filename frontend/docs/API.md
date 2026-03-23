# KINFP-Portal API Documentation

## Overview

KINFP-Portal uses **tRPC** (TypeScript Remote Procedure Call) for all API communication. tRPC provides end-to-end type safety between frontend and backend without requiring separate API documentation. All types are automatically inferred from the server implementation.

### Key Advantages of tRPC

**Type Safety**: The entire request-response chain is type-checked at compile time. If the backend procedure signature changes, the frontend will immediately show TypeScript errors.

**No Schema Duplication**: Unlike REST APIs that require separate OpenAPI/Swagger specs, tRPC uses a single source of truth – the server implementation.

**Automatic Client Generation**: The frontend client is automatically generated from the server router, ensuring perfect synchronization.

**Superjson Serialization**: Complex types like `Date`, `Map`, and `Set` are automatically serialized and deserialized correctly.

## Authentication

All protected procedures require a valid user session. The authentication flow works as follows:

1. User logs in via Manus OAuth
2. OAuth callback creates a session cookie
3. Each tRPC request includes the session cookie
4. Server validates the session and injects `ctx.user` into the procedure context
5. Protected procedures throw `UNAUTHORIZED` error if user is not authenticated

### Public vs Protected Procedures

**Public Procedures**: Can be called without authentication. Used for login, logout, and public data access.

**Protected Procedures**: Require a valid user session. Throw `UNAUTHORIZED` error if called without authentication.

## Router Structure

The main router is organized into feature-based sub-routers:

```typescript
appRouter = {
  auth: {
    me: publicProcedure.query(...),
    logout: publicProcedure.mutation(...),
  },
  files: {
    upload: protectedProcedure.mutation(...),
    list: protectedProcedure.query(...),
    getDownloadUrl: protectedProcedure.query(...),
    delete: protectedProcedure.mutation(...),
    getStats: protectedProcedure.query(...),
  },
  system: {
    notifyOwner: protectedProcedure.mutation(...),
  },
}
```

## Procedures Reference

### Authentication Router

#### `auth.me`

Get information about the currently authenticated user.

**Type**: Query (Read-only)  
**Authentication**: Public (no auth required)  
**Input**: None

**Output**:
```typescript
{
  id: number;
  openId: string;
  name: string | null;
  email: string | null;
  loginMethod: string | null;
  role: "user" | "admin";
  createdAt: Date;
  updatedAt: Date;
  lastSignedIn: Date;
} | null
```

**Returns**: User object if authenticated, `null` if not authenticated.

**Example Usage**:
```typescript
const { data: user, isLoading } = trpc.auth.me.useQuery();

if (isLoading) return <Spinner />;
if (!user) return <LoginButton />;
return <Dashboard user={user} />;
```

---

#### `auth.logout`

Logout the current user and clear the session cookie.

**Type**: Mutation (Write)  
**Authentication**: Public  
**Input**: None

**Output**:
```typescript
{ success: true }
```

**Example Usage**:
```typescript
const logoutMutation = trpc.auth.logout.useMutation({
  onSuccess: () => {
    window.location.href = "/";
  },
});

return (
  <Button onClick={() => logoutMutation.mutate()}>
    Logout
  </Button>
);
```

---

### Files Router

The Files router manages file uploads, downloads, and storage. All file operations are user-isolated – users can only access their own files.

#### `files.upload`

Upload a file to S3 storage and store metadata in the database.

**Type**: Mutation (Write)  
**Authentication**: Protected (requires login)  
**Input**:
```typescript
{
  fileName: string;           // Original filename (e.g., "document.pdf")
  fileData: string;           // Base64-encoded file content
  contentType?: string;       // MIME type (default: "application/octet-stream")
  category?: "document" | "image" | "video" | "archive" | "other";
  description?: string;       // Optional file description
}
```

**Output**:
```typescript
{
  success: true;
  fileName: string;
  fileUrl: string;            // CDN URL for accessing the file
  fileSize: number;           // File size in bytes
}
```

**Error Cases**:
- `UNAUTHORIZED`: User not authenticated
- `INTERNAL_SERVER_ERROR`: Database unavailable or upload failed

**Example Usage**:
```typescript
const uploadMutation = trpc.files.upload.useMutation({
  onSuccess: (result) => {
    console.log(`File uploaded: ${result.fileUrl}`);
    refetchFiles();
  },
  onError: (error) => {
    console.error(`Upload failed: ${error.message}`);
  },
});

const handleFileSelect = (file: File) => {
  const reader = new FileReader();
  reader.onload = (e) => {
    const base64 = e.target?.result as string;
    uploadMutation.mutate({
      fileName: file.name,
      fileData: base64.split(",")[1],
      contentType: file.type,
      category: categorizeFile(file.type),
    });
  };
  reader.readAsDataURL(file);
};
```

---

#### `files.list`

List files for the current user with optional filtering by category.

**Type**: Query (Read-only)  
**Authentication**: Protected  
**Input**:
```typescript
{
  category?: "document" | "image" | "video" | "archive" | "other";
  limit?: number;             // Default: 50
  offset?: number;            // Default: 0
}
```

**Output**:
```typescript
{
  files: Array<{
    id: number;
    fileName: string;
    fileUrl: string;
    fileSize: number;         // In bytes
    category: string;
    description: string | null;
    uploadedAt: Date;
  }>;
  total: number;              // Total count of files
}
```

**Example Usage**:
```typescript
const { data: filesData, isLoading } = trpc.files.list.useQuery(
  { category: "document", limit: 20, offset: 0 },
  { enabled: isAuthenticated }
);

return (
  <div>
    {filesData?.files.map((file) => (
      <FileItem key={file.id} file={file} />
    ))}
    <p>Total: {filesData?.total}</p>
  </div>
);
```

---

#### `files.getDownloadUrl`

Get a presigned download URL for a file. The URL is valid for a limited time and includes authentication.

**Type**: Query (Read-only)  
**Authentication**: Protected  
**Input**:
```typescript
{
  fileId: number;
}
```

**Output**:
```typescript
{
  fileName: string;
  downloadUrl: string;        // Presigned URL valid for limited time
}
```

**Error Cases**:
- `UNAUTHORIZED`: User not authenticated
- `NOT_FOUND`: File not found
- `FORBIDDEN`: User does not own this file

**Example Usage**:
```typescript
const { data: downloadData } = trpc.files.getDownloadUrl.useQuery(
  { fileId: 123 },
  { enabled: shouldDownload }
);

useEffect(() => {
  if (downloadData) {
    const a = document.createElement("a");
    a.href = downloadData.downloadUrl;
    a.download = downloadData.fileName;
    a.click();
  }
}, [downloadData]);
```

---

#### `files.delete`

Delete a file from storage and remove its metadata from the database.

**Type**: Mutation (Write)  
**Authentication**: Protected  
**Input**:
```typescript
{
  fileId: number;
}
```

**Output**:
```typescript
{
  success: true;
}
```

**Error Cases**:
- `UNAUTHORIZED`: User not authenticated
- `NOT_FOUND`: File not found
- `FORBIDDEN`: User does not own this file

**Example Usage**:
```typescript
const deleteMutation = trpc.files.delete.useMutation({
  onSuccess: () => {
    refetchFiles();
    toast.success("File deleted");
  },
});

const handleDelete = (fileId: number) => {
  if (confirm("Delete this file?")) {
    deleteMutation.mutate({ fileId });
  }
};
```

---

#### `files.getStats`

Get statistics about the current user's files including total count, storage usage, and breakdown by category.

**Type**: Query (Read-only)  
**Authentication**: Protected  
**Input**: None

**Output**:
```typescript
{
  totalFiles: number;
  totalSize: number;          // In bytes
  byCategory: {
    [category: string]: number; // Count of files in each category
  };
}
```

**Example Usage**:
```typescript
const { data: stats } = trpc.files.getStats.useQuery(
  undefined,
  { enabled: isAuthenticated }
);

return (
  <div>
    <p>Files: {stats?.totalFiles}</p>
    <p>Storage: {(stats?.totalSize / 1024 / 1024).toFixed(2)} MB</p>
  </div>
);
```

---

### System Router

#### `system.notifyOwner`

Send a notification to the application owner. Used for important events that require owner attention.

**Type**: Mutation (Write)  
**Authentication**: Protected  
**Input**:
```typescript
{
  title: string;              // Notification title
  content: string;            // Notification body
}
```

**Output**:
```typescript
boolean;                       // true if sent successfully, false if service unavailable
```

**Example Usage**:
```typescript
const notifyMutation = trpc.system.notifyOwner.useMutation();

const handleFormSubmit = async (data: FormData) => {
  const result = await notifyMutation.mutateAsync({
    title: "New Investment Application",
    content: `User ${data.name} submitted an investment application.`,
  });
  
  if (result) {
    console.log("Owner notified");
  }
};
```

---

## Error Handling

tRPC uses standardized error codes for all procedures:

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `PARSE_ERROR` | 400 | Input parsing failed |
| `BAD_REQUEST` | 400 | Invalid input |
| `UNAUTHORIZED` | 401 | User not authenticated |
| `FORBIDDEN` | 403 | User lacks permission |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict |
| `PRECONDITION_FAILED` | 412 | Precondition failed |
| `PAYLOAD_TOO_LARGE` | 413 | Request too large |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | Unsupported media type |
| `UNPROCESSABLE_CONTENT` | 422 | Unprocessable content |
| `TOO_MANY_REQUESTS` | 429 | Rate limited |
| `CLIENT_CLOSED_REQUEST` | 499 | Client closed connection |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |
| `NOT_IMPLEMENTED` | 501 | Not implemented |
| `BAD_GATEWAY` | 502 | Bad gateway |
| `SERVICE_UNAVAILABLE` | 503 | Service unavailable |
| `GATEWAY_TIMEOUT` | 504 | Gateway timeout |

**Error Handling Pattern**:
```typescript
const mutation = trpc.files.upload.useMutation({
  onError: (error) => {
    if (error.code === "UNAUTHORIZED") {
      // Redirect to login
      window.location.href = getLoginUrl();
    } else if (error.code === "FORBIDDEN") {
      toast.error("You don't have permission to do this");
    } else if (error.code === "INTERNAL_SERVER_ERROR") {
      toast.error("Server error: " + error.message);
    } else {
      toast.error("An error occurred: " + error.message);
    }
  },
});
```

---

## Data Types

### User Type

```typescript
interface User {
  id: number;
  openId: string;              // Unique identifier from OAuth provider
  name: string | null;
  email: string | null;
  loginMethod: string | null;  // e.g., "manus_oauth"
  role: "user" | "admin";
  createdAt: Date;
  updatedAt: Date;
  lastSignedIn: Date;
}
```

### File Type

```typescript
interface File {
  id: number;
  userId: number;              // Owner of the file
  fileName: string;
  fileKey: string;             // S3 key
  fileUrl: string;             // CDN URL
  contentType: string;         // MIME type
  fileSize: number;            // In bytes
  category: "document" | "image" | "video" | "archive" | "other";
  description: string | null;
  uploadedAt: Date;
  createdAt: Date;
}
```

---

## Best Practices

### 1. Always Check Authentication Status

```typescript
const { data: user } = trpc.auth.me.useQuery();

if (!user) {
  return <Redirect to={getLoginUrl()} />;
}
```

### 2. Use Optimistic Updates for Better UX

```typescript
const deleteMutation = trpc.files.delete.useMutation({
  onMutate: async (fileId) => {
    // Cancel ongoing queries
    await queryClient.cancelQueries({ queryKey: ["files", "list"] });
    
    // Optimistically update cache
    queryClient.setQueryData(
      ["files", "list"],
      (old: any) => ({
        ...old,
        files: old.files.filter((f: any) => f.id !== fileId),
      })
    );
  },
  onError: (error, fileId, context) => {
    // Rollback on error
    queryClient.setQueryData(["files", "list"], context?.previousData);
  },
});
```

### 3. Handle Loading States

```typescript
const { data, isLoading, error } = trpc.files.list.useQuery({});

if (isLoading) return <Spinner />;
if (error) return <ErrorMessage error={error} />;
if (!data?.files.length) return <EmptyState />;

return <FileList files={data.files} />;
```

### 4. Use Proper Input Validation

```typescript
const uploadMutation = trpc.files.upload.useMutation();

const handleUpload = (file: File) => {
  // Validate file size
  if (file.size > 100 * 1024 * 1024) {
    toast.error("File too large (max 100MB)");
    return;
  }
  
  // Validate file type
  const allowedTypes = ["application/pdf", "image/jpeg", "image/png"];
  if (!allowedTypes.includes(file.type)) {
    toast.error("File type not allowed");
    return;
  }
  
  // Proceed with upload
  uploadMutation.mutate({...});
};
```

### 5. Implement Proper Error Recovery

```typescript
const mutation = trpc.files.upload.useMutation({
  onError: (error) => {
    if (error.code === "UNAUTHORIZED") {
      // Redirect to login
      window.location.href = getLoginUrl();
    } else {
      // Retry logic
      setTimeout(() => {
        mutation.mutate(previousInput);
      }, 2000);
    }
  },
});
```

---

## Rate Limiting

Currently, there is no built-in rate limiting on tRPC procedures. For production deployments, consider implementing:

- Request rate limiting per user
- File upload size limits
- Concurrent upload limits
- Database query rate limiting

---

## Future API Additions

The following procedures are planned for future releases:

- `files.share` - Share files with other users
- `files.getMetadata` - Get detailed file metadata
- `files.search` - Full-text search across files
- `files.batch.delete` - Delete multiple files
- `files.versions.list` - List file versions
- `analytics.getMetrics` - Get system analytics

---

## Support

For API questions or issues:

1. Check the [tRPC documentation](https://trpc.io)
2. Review the [source code](https://github.com/Baronki/kinfp-portal)
3. Create a GitHub issue with details
4. Contact: info@kinfp.io

---

**Last Updated**: March 4, 2026  
**API Version**: 1.0  
**tRPC Version**: 11.0+

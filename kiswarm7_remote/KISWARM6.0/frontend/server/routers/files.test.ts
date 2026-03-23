import { describe, it, expect, vi, beforeEach } from "vitest";
import { filesRouter } from "./files";
import { getDb } from "../db";
import { storagePut, storageGet } from "../storage";

// Mock dependencies
vi.mock("../db");
vi.mock("../storage");

describe("filesRouter", () => {
  const mockUser = { id: 1, name: "Test User", role: "user" as const };
  const mockCtx = { user: mockUser };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("upload", () => {
    it("should upload a file successfully", async () => {
      const mockDb = {
        insert: vi.fn().mockReturnValue({
          values: vi.fn().mockResolvedValue({ insertId: 1 }),
        }),
      };

      vi.mocked(getDb).mockResolvedValue(mockDb as any);
      vi.mocked(storagePut).mockResolvedValue({
        key: "files/1/test-key.txt",
        url: "https://example.com/files/1/test-key.txt",
      });

      const caller = filesRouter.createCaller(mockCtx as any);
      const result = await caller.upload({
        fileName: "test.txt",
        fileData: Buffer.from("test content").toString("base64"),
        contentType: "text/plain",
        category: "document",
        description: "Test file",
      });

      expect(result).toEqual({
        success: true,
        fileName: "test.txt",
        fileUrl: "https://example.com/files/1/test-key.txt",
        fileSize: expect.any(Number),
      });

      expect(storagePut).toHaveBeenCalled();
      expect(mockDb.insert).toHaveBeenCalled();
    });

    it("should throw error if database is not available", async () => {
      vi.mocked(getDb).mockResolvedValue(null);
      vi.mocked(storagePut).mockResolvedValue({
        key: "files/1/test-key.txt",
        url: "https://example.com/files/1/test-key.txt",
      });

      const caller = filesRouter.createCaller(mockCtx as any);

      await expect(
        caller.upload({
          fileName: "test.txt",
          fileData: Buffer.from("test content").toString("base64"),
          contentType: "text/plain",
        })
      ).rejects.toThrow("Database not available");
    });
  });

  describe("getStats", () => {
    it("should return file statistics", async () => {
      const mockFiles = [
        {
          id: 1,
          userId: 1,
          fileName: "test.txt",
          fileKey: "files/1/test.txt",
          fileUrl: "https://example.com/files/1/test.txt",
          contentType: "text/plain",
          fileSize: 1000,
          category: "document" as const,
          description: "Test file",
          uploadedAt: new Date(),
          createdAt: new Date(),
        },
        {
          id: 2,
          userId: 1,
          fileName: "image.jpg",
          fileKey: "files/1/image.jpg",
          fileUrl: "https://example.com/files/1/image.jpg",
          contentType: "image/jpeg",
          fileSize: 5000,
          category: "image" as const,
          description: "Test image",
          uploadedAt: new Date(),
          createdAt: new Date(),
        },
      ];

      const mockDb = {
        select: vi.fn().mockReturnValue({
          from: vi.fn().mockReturnValue({
            where: vi.fn().mockResolvedValue(mockFiles),
          }),
        }),
      };

      vi.mocked(getDb).mockResolvedValue(mockDb as any);

      const caller = filesRouter.createCaller(mockCtx as any);
      const result = await caller.getStats();

      expect(result.totalFiles).toBe(2);
      expect(result.totalSize).toBe(6000);
      expect(result.byCategory.document).toBe(1);
      expect(result.byCategory.image).toBe(1);
    });
  });

  describe("delete", () => {
    it("should delete a file successfully", async () => {
      const mockFile = {
        id: 1,
        userId: 1,
        fileName: "test.txt",
        fileKey: "files/1/test.txt",
        fileUrl: "https://example.com/files/1/test.txt",
        contentType: "text/plain",
        fileSize: 100,
        category: "document" as const,
        description: "Test file",
        uploadedAt: new Date(),
        createdAt: new Date(),
      };

      const mockDb = {
        select: vi.fn().mockReturnValue({
          from: vi.fn().mockReturnValue({
            where: vi.fn().mockReturnValue({
              limit: vi.fn().mockResolvedValue([mockFile]),
            }),
          }),
        }),
        delete: vi.fn().mockReturnValue({
          where: vi.fn().mockResolvedValue({ success: true }),
        }),
      };

      vi.mocked(getDb).mockResolvedValue(mockDb as any);

      const caller = filesRouter.createCaller(mockCtx as any);
      const result = await caller.delete({ fileId: 1 });

      expect(result.success).toBe(true);
      expect(mockDb.delete).toHaveBeenCalled();
    });

    it("should throw error if file not found", async () => {
      const mockDb = {
        select: vi.fn().mockReturnValue({
          from: vi.fn().mockReturnValue({
            where: vi.fn().mockReturnValue({
              limit: vi.fn().mockResolvedValue([]),
            }),
          }),
        }),
      };

      vi.mocked(getDb).mockResolvedValue(mockDb as any);

      const caller = filesRouter.createCaller(mockCtx as any);

      await expect(caller.delete({ fileId: 999 })).rejects.toThrow("File not found");
    });

    it("should throw error if user does not own the file", async () => {
      const mockFile = {
        id: 1,
        userId: 999,
        fileName: "test.txt",
        fileKey: "files/999/test.txt",
        fileUrl: "https://example.com/files/999/test.txt",
        contentType: "text/plain",
        fileSize: 100,
        category: "document" as const,
        description: "Test file",
        uploadedAt: new Date(),
        createdAt: new Date(),
      };

      const mockDb = {
        select: vi.fn().mockReturnValue({
          from: vi.fn().mockReturnValue({
            where: vi.fn().mockReturnValue({
              limit: vi.fn().mockResolvedValue([mockFile]),
            }),
          }),
        }),
      };

      vi.mocked(getDb).mockResolvedValue(mockDb as any);

      const caller = filesRouter.createCaller(mockCtx as any);

      await expect(caller.delete({ fileId: 1 })).rejects.toThrow("You don't have access to this file");
    });
  });
});

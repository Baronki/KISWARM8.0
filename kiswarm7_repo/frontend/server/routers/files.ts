import { z } from "zod";
import { protectedProcedure, router } from "../_core/trpc";
import { storagePut, storageGet } from "../storage";
import { getDb } from "../db";
import { files as filesTable } from "../../drizzle/schema";
import { eq, and } from "drizzle-orm";
import { TRPCError } from "@trpc/server";

export const filesRouter = router({
  /**
   * Upload a file to S3 and store metadata in database
   */
  upload: protectedProcedure
    .input(
      z.object({
        fileName: z.string().min(1),
        fileData: z.string(), // Base64 encoded file data
        contentType: z.string().default("application/octet-stream"),
        category: z.enum(["document", "image", "video", "archive", "other"]).default("other"),
        description: z.string().optional(),
      })
    )
    .mutation(async ({ input, ctx }) => {
      try {
        // Decode base64 to buffer
        const buffer = Buffer.from(input.fileData, "base64");

        // Generate unique file key
        const timestamp = Date.now();
        const randomSuffix = Math.random().toString(36).substring(7);
        const fileKey = `files/${ctx.user.id}/${timestamp}-${randomSuffix}-${input.fileName}`;

        // Upload to S3
        const { url, key } = await storagePut(fileKey, buffer, input.contentType);

        // Store metadata in database
        const db = await getDb();
        if (!db) {
          throw new TRPCError({
            code: "INTERNAL_SERVER_ERROR",
            message: "Database not available",
          });
        }

        await db.insert(filesTable).values({
          userId: ctx.user.id,
          fileName: input.fileName,
          fileKey: key,
          fileUrl: url,
          contentType: input.contentType,
          fileSize: buffer.length,
          category: input.category,
          description: input.description,
          uploadedAt: new Date(),
        });

        return {
          success: true,
          fileName: input.fileName,
          fileUrl: url,
          fileSize: buffer.length,
        };
      } catch (error) {
        console.error("[Files] Upload error:", error);
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message: error instanceof Error ? error.message : "Upload failed",
        });
      }
    }),

  /**
   * List files for current user
   */
  list: protectedProcedure
    .input(
      z.object({
        category: z.enum(["document", "image", "video", "archive", "other"]).optional(),
        limit: z.number().default(50),
        offset: z.number().default(0),
      })
    )
    .query(async ({ input, ctx }) => {
      try {
        const db = await getDb();
        if (!db) {
          return { files: [], total: 0 };
        }

        // Build where conditions
        const whereConditions = [eq(filesTable.userId, ctx.user.id)];
        if (input.category) {
          whereConditions.push(eq(filesTable.category, input.category));
        }

        const files = await db
          .select()
          .from(filesTable)
          .where(and(...whereConditions))
          .limit(input.limit)
          .offset(input.offset);

        const allFiles = await db
          .select()
          .from(filesTable)
          .where(and(...whereConditions));

        return {
          files: files.map((f) => ({
            id: f.id,
            fileName: f.fileName,
            fileUrl: f.fileUrl,
            fileSize: f.fileSize,
            category: f.category,
            description: f.description,
            uploadedAt: f.uploadedAt,
          })),
          total: allFiles.length,
        };
      } catch (error) {
        console.error("[Files] List error:", error);
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message: "Failed to list files",
        });
      }
    }),

  /**
   * Get download URL for a file
   */
  getDownloadUrl: protectedProcedure
    .input(z.object({ fileId: z.number() }))
    .query(async ({ input, ctx }) => {
      try {
        const db = await getDb();
        if (!db) {
          throw new TRPCError({
            code: "INTERNAL_SERVER_ERROR",
            message: "Database not available",
          });
        }

        const files = await db
          .select()
          .from(filesTable)
          .where(eq(filesTable.id, input.fileId))
          .limit(1);

        const file = files[0];
        if (!file) {
          throw new TRPCError({
            code: "NOT_FOUND",
            message: "File not found",
          });
        }

        if (file.userId !== ctx.user.id) {
          throw new TRPCError({
            code: "FORBIDDEN",
            message: "You don't have access to this file",
          });
        }

        // Get presigned download URL
        const { url } = await storageGet(file.fileKey);

        return {
          fileName: file.fileName,
          downloadUrl: url,
        };
      } catch (error) {
        console.error("[Files] Download URL error:", error);
        if (error instanceof TRPCError) throw error;
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message: "Failed to get download URL",
        });
      }
    }),

  /**
   * Delete a file
   */
  delete: protectedProcedure
    .input(z.object({ fileId: z.number() }))
    .mutation(async ({ input, ctx }) => {
      try {
        const db = await getDb();
        if (!db) {
          throw new TRPCError({
            code: "INTERNAL_SERVER_ERROR",
            message: "Database not available",
          });
        }

        const files = await db
          .select()
          .from(filesTable)
          .where(eq(filesTable.id, input.fileId))
          .limit(1);

        const file = files[0];
        if (!file) {
          throw new TRPCError({
            code: "NOT_FOUND",
            message: "File not found",
          });
        }

        if (file.userId !== ctx.user.id) {
          throw new TRPCError({
            code: "FORBIDDEN",
            message: "You don't have access to this file",
          });
        }

        // Delete from database
        await db.delete(filesTable).where(eq(filesTable.id, input.fileId));

        return { success: true };
      } catch (error) {
        console.error("[Files] Delete error:", error);
        if (error instanceof TRPCError) throw error;
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message: "Failed to delete file",
        });
      }
    }),

  /**
   * Get file statistics
   */
  getStats: protectedProcedure.query(async ({ ctx }) => {
    try {
      const db = await getDb();
      if (!db) {
        return {
          totalFiles: 0,
          totalSize: 0,
          byCategory: {},
        };
      }

      const userFiles = await db
        .select()
        .from(filesTable)
        .where(eq(filesTable.userId, ctx.user.id));

      const totalSize = userFiles.reduce((sum, f) => sum + (f.fileSize || 0), 0);
      const byCategory = userFiles.reduce(
        (acc, f) => {
          acc[f.category] = (acc[f.category] || 0) + 1;
          return acc;
        },
        {} as Record<string, number>
      );

      return {
        totalFiles: userFiles.length,
        totalSize,
        byCategory,
      };
    } catch (error) {
      console.error("[Files] Stats error:", error);
      throw new TRPCError({
        code: "INTERNAL_SERVER_ERROR",
        message: "Failed to get file statistics",
      });
    }
  }),
});

import { useState, useRef } from "react";
import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { trpc } from "@/lib/trpc";
import { Upload, Download, Trash2, File, Image, FileText, Archive, Loader2 } from "lucide-react";

type FileCategory = "document" | "image" | "video" | "archive" | "other";

const categoryIcons: Record<FileCategory, React.ReactNode> = {
  document: <FileText className="w-4 h-4" />,
  image: <Image className="w-4 h-4" />,
  video: <File className="w-4 h-4" />,
  archive: <Archive className="w-4 h-4" />,
  other: <File className="w-4 h-4" />,
};

export default function FileManager() {
  const { user, isAuthenticated } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedCategory, setSelectedCategory] = useState<FileCategory | "all">("all");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // tRPC queries and mutations
  const { data: filesData, isLoading: isLoadingFiles, refetch: refetchFiles } = trpc.files.list.useQuery(
    { category: selectedCategory === "all" ? undefined : (selectedCategory as FileCategory) },
    { enabled: isAuthenticated }
  );

  const { data: statsData } = trpc.files.getStats.useQuery(undefined, { enabled: isAuthenticated });

  const uploadMutation = trpc.files.upload.useMutation({
    onSuccess: () => {
      refetchFiles();
      setUploadProgress(0);
      setUploading(false);
    },
    onError: (error) => {
      console.error("Upload error:", error);
      setUploading(false);
    },
  });

  const [downloadingFileId, setDownloadingFileId] = useState<number | null>(null);
  const [downloadFileId, setDownloadFileId] = useState<number | null>(null);
  const { data: downloadData } = trpc.files.getDownloadUrl.useQuery(
    { fileId: downloadFileId || 0 },
    { enabled: downloadFileId !== null }
  );

  const deleteMutation = trpc.files.delete.useMutation({
    onSuccess: () => {
      refetchFiles();
    },
  });

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.currentTarget.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    setUploading(true);
    setUploadProgress(0);

    try {
      // Read file as base64
      const reader = new FileReader();
      reader.onprogress = (e) => {
        if (e.lengthComputable) {
          setUploadProgress(Math.round((e.loaded / e.total) * 100));
        }
      };
      reader.onload = async (e) => {
        if (!e.target?.result) return;

        const base64 = (e.target.result as string).split(",")[1];
        const category = categorizeFile(file.type);

        await uploadMutation.mutateAsync({
          fileName: file.name,
          fileData: base64,
          contentType: file.type,
          category,
          description: `Uploaded on ${new Date().toLocaleDateString()}`,
        });
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error("File processing error:", error);
      setUploading(false);
    }

    // Reset input
    event.currentTarget.value = "";
  };

  const categorizeFile = (mimeType: string): FileCategory => {
    if (mimeType.startsWith("image/")) return "image";
    if (mimeType.startsWith("video/")) return "video";
    if (mimeType.includes("pdf") || mimeType.includes("word") || mimeType.includes("text")) return "document";
    if (mimeType.includes("zip") || mimeType.includes("rar") || mimeType.includes("7z")) return "archive";
    return "other";
  };

  const handleDownload = (fileId: number, fileName: string) => {
    setDownloadFileId(fileId);
    setDownloadingFileId(fileId);
  };

  // Handle download when URL is ready
  if (downloadData && downloadingFileId) {
    const a = document.createElement("a");
    a.href = downloadData.downloadUrl;
    a.download = downloadData.fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setDownloadingFileId(null);
    setDownloadFileId(null);
  }

  const handleDelete = async (fileId: number) => {
    if (confirm("Are you sure you want to delete this file?")) {
      await deleteMutation.mutateAsync({ fileId });
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <Card className="p-8 text-center max-w-md">
          <h2 className="text-2xl font-bold mb-4">File Manager</h2>
          <p className="text-muted-foreground mb-6">Please log in to access the file manager.</p>
          <Button className="w-full">Log In</Button>
        </Card>
      </div>
    );
  }

  const files = filesData?.files || [];
  const stats = statsData;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container py-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl font-bold mb-4 glow-cyan">File Manager</h1>
          <p className="text-lg text-muted-foreground">
            Upload, manage, and organize your files securely in the cloud.
          </p>
        </div>

        {/* Statistics */}
        {stats && (
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <Card className="p-6 bg-card border-cyan-500/30">
              <div className="text-3xl font-bold text-cyan-400 mb-2">{stats.totalFiles}</div>
              <p className="text-sm text-muted-foreground">Total Files</p>
            </Card>
            <Card className="p-6 bg-card border-magenta-600/30">
              <div className="text-3xl font-bold text-magenta-500 mb-2">
                {(stats.totalSize / 1024 / 1024).toFixed(2)} MB
              </div>
              <p className="text-sm text-muted-foreground">Total Storage</p>
            </Card>
            <Card className="p-6 bg-card border-cyan-500/30">
              <div className="text-3xl font-bold text-cyan-400 mb-2">
                {Object.keys(stats.byCategory).length}
              </div>
              <p className="text-sm text-muted-foreground">Categories</p>
            </Card>
          </div>
        )}

        {/* Upload Section */}
        <Card className="p-8 mb-12 bg-card/50 border-cyan-500/30">
          <div className="flex flex-col items-center justify-center">
            <Upload className="w-12 h-12 text-cyan-400 mb-4" />
            <h2 className="text-2xl font-bold mb-2">Upload Files</h2>
            <p className="text-muted-foreground mb-6 text-center">
              Drag and drop files here or click to browse
            </p>
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              className="hidden"
              disabled={uploading}
            />
            <Button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="bg-cyan-500 hover:bg-cyan-600 text-background font-bold"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Uploading... {uploadProgress}%
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Select File
                </>
              )}
            </Button>
          </div>
        </Card>

        {/* Category Filter */}
        <div className="mb-8 flex gap-2 flex-wrap">
          {(["all", "document", "image", "video", "archive", "other"] as const).map((cat) => (
            <Button
              key={cat}
              variant={selectedCategory === cat ? "default" : "outline"}
              onClick={() => setSelectedCategory(cat)}
              className={selectedCategory === cat ? "bg-cyan-500 text-background" : ""}
            >
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </Button>
          ))}
        </div>

        {/* Files List */}
        <div>
          <h2 className="text-2xl font-bold mb-6">Your Files</h2>
          {isLoadingFiles ? (
            <Card className="p-12 text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-cyan-400" />
              <p className="text-muted-foreground">Loading files...</p>
            </Card>
          ) : files.length === 0 ? (
            <Card className="p-12 text-center bg-card/50">
              <File className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">No files uploaded yet</p>
            </Card>
          ) : (
            <div className="grid gap-4">
              {files.map((file) => (
                <Card
                  key={file.id}
                  className="p-6 bg-card border-border hover:border-cyan-500/50 transition flex items-center justify-between"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="text-cyan-400">{categoryIcons[file.category]}</div>
                    <div className="flex-1">
                      <h3 className="font-mono font-bold text-lg">{file.fileName}</h3>
                      <p className="text-sm text-muted-foreground">
                        {(file.fileSize / 1024).toFixed(2)} KB • {file.category}
                      </p>
                      {file.description && (
                        <p className="text-xs text-muted-foreground mt-1">{file.description}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDownload(file.id, file.fileName)}
                      disabled={downloadingFileId === file.id}
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete(file.id)}
                      disabled={deleteMutation.isPending}
                      className="text-red-400 hover:text-red-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           KISWARM GWS DRIVE SYNC ENGINE v6.3.5                                ║
║                    "Iron Mountain Protocol Implementation"                     ║
║                                                                               ║
║  Autonomous shadow repository synchronization to Google Drive.                 ║
║  Uses Service Account authentication for zero human intervention.              ║
║                                                                               ║
║  Layer 5: GWS Iron Mountain - Censorship-Resistant Backup                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Author: KISWARM Project (Baron Marco Paolo Ialongo)
Version: 6.3.5 - GWS_IRON_MOUNTAIN
"""

import os
import sys
import json
import subprocess
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Google Workspace CLI Configuration
GWS_CONFIG = {
    "credentials_env": "GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE",
    "default_folder_name": "KISWARM_ARK",
    "archive_prefix": "KISWARM_SOURCE",
    "manifest_name": "versions.json",
}

# KISWARM Paths
KISWARM_ROOT = Path(__file__).parent.parent.parent
BACKUP_PATH = KISWARM_ROOT
MANIFEST_PATH = KISWARM_ROOT / "docs" / "drive_versions.json"


class GWSDriveSync:
    """
    KISWARM GWS Drive Sync Engine.
    
    Provides autonomous backup of KISWARM source code to Google Drive
    using the gws CLI with Service Account authentication.
    """
    
    def __init__(self, credentials_file: Optional[str] = None):
        self.credentials_file = credentials_file or os.environ.get(
            GWS_CONFIG["credentials_env"]
        )
        self.folder_id: Optional[str] = None
        self._verify_gws_installed()
        self._verify_credentials()
    
    def _verify_gws_installed(self):
        """Verify gws CLI is installed."""
        try:
            result = subprocess.run(
                ["gws", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError("gws CLI not functional")
            print(f"[GWS] Version: {result.stdout.strip()}")
        except FileNotFoundError:
            raise RuntimeError(
                "gws CLI not installed. Run: npm install -g @googleworkspace/cli"
            )
    
    def _verify_credentials(self):
        """Verify credentials are configured."""
        if not self.credentials_file:
            print("[GWS] WARNING: No credentials file configured")
            print(f"       Set {GWS_CONFIG['credentials_env']} environment variable")
            return
        
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_file}"
            )
        
        # Set environment for gws commands
        os.environ["GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE"] = self.credentials_file
        print(f"[GWS] Credentials: {self.credentials_file}")
    
    def _run_gws(self, args: list, input_data: Optional[str] = None) -> Dict[str, Any]:
        """Execute gws command and return JSON result."""
        cmd = ["gws"] + args
        print(f"[GWS] Executing: {' '.join(args[:3])}...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=input_data,
            timeout=300
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            print(f"[GWS] ERROR: {error_msg}")
            raise RuntimeError(f"gws command failed: {error_msg}")
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            # Some commands return non-JSON output
            return {"raw_output": result.stdout}
    
    def get_or_create_folder(self, folder_name: str = None) -> str:
        """Get or create the KISWARM_ARK folder on Drive."""
        folder_name = folder_name or GWS_CONFIG["default_folder_name"]
        
        # Search for existing folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        
        try:
            result = self._run_gws([
                "drive", "files", "list",
                "--params", json.dumps({"q": query, "pageSize": 1})
            ])
            
            if result.get("files"):
                self.folder_id = result["files"][0]["id"]
                print(f"[GWS] Found folder: {folder_name} ({self.folder_id})")
                return self.folder_id
        except Exception as e:
            print(f"[GWS] Folder search failed: {e}")
        
        # Create new folder
        try:
            result = self._run_gws([
                "drive", "files", "create",
                "--json", json.dumps({
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder"
                })
            ])
            self.folder_id = result.get("id")
            print(f"[GWS] Created folder: {folder_name} ({self.folder_id})")
            return self.folder_id
        except Exception as e:
            raise RuntimeError(f"Failed to create folder: {e}")
    
    def create_archive(self) -> tuple:
        """Create zip archive of KISWARM repository."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"v6.3.5_{timestamp}"
        archive_name = f"{GWS_CONFIG['archive_prefix']}_{version}.zip"
        archive_path = Path("/tmp") / archive_name
        
        print(f"[LOCAL] Creating archive: {archive_name}")
        
        # Create zip archive
        shutil.make_archive(
            str(archive_path.with_suffix("")),
            "zip",
            BACKUP_PATH
        )
        
        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256()
        with open(archive_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        
        file_hash = sha256_hash.hexdigest()
        file_size = archive_path.stat().st_size
        
        print(f"[LOCAL] Archive size: {file_size / 1024 / 1024:.2f} MB")
        print(f"[LOCAL] SHA256: {file_hash[:16]}...")
        
        return str(archive_path), archive_name, file_hash, version
    
    def upload_archive(self, archive_path: str, archive_name: str) -> str:
        """Upload archive to Google Drive."""
        if not self.folder_id:
            raise RuntimeError("No folder ID - call get_or_create_folder first")
        
        print(f"[GWS] Uploading: {archive_name}")
        
        result = self._run_gws([
            "drive", "files", "create",
            "--json", json.dumps({
                "name": archive_name,
                "parents": [self.folder_id]
            }),
            "--upload", archive_path
        ])
        
        file_id = result.get("id")
        print(f"[GWS] Upload complete: {file_id}")
        return file_id
    
    def update_manifest(self, file_id: str, file_name: str, file_hash: str, version: str):
        """Update versions.json manifest on Drive."""
        manifest_data = {
            "latest": {
                "version": version,
                "file_id": file_id,
                "file_name": file_name,
                "sha256": file_hash,
                "updated_at": datetime.now().isoformat(),
            },
            "source": "KISWARM6.0",
            "layer": "LAYER_5_GWS_IRON_MOUNTAIN"
        }
        
        # Save local copy
        with open(MANIFEST_PATH, "w") as f:
            json.dump(manifest_data, f, indent=2)
        
        print(f"[GWS] Manifest updated: {MANIFEST_PATH}")
        
        # Upload manifest to Drive
        manifest_name = GWS_CONFIG["manifest_name"]
        
        try:
            # Try to update existing manifest
            query = f"name='{manifest_name}' and '{self.folder_id}' in parents and trashed=false"
            result = self._run_gws([
                "drive", "files", "list",
                "--params", json.dumps({"q": query, "pageSize": 1})
            ])
            
            if result.get("files"):
                # Update existing
                existing_id = result["files"][0]["id"]
                self._run_gws([
                    "drive", "files", "update",
                    "--params", json.dumps({"fileId": existing_id}),
                    "--upload", str(MANIFEST_PATH)
                ])
                print(f"[GWS] Manifest updated on Drive: {existing_id}")
            else:
                # Create new
                self._run_gws([
                    "drive", "files", "create",
                    "--json", json.dumps({
                        "name": manifest_name,
                        "parents": [self.folder_id]
                    }),
                    "--upload", str(MANIFEST_PATH)
                ])
                print(f"[GWS] Manifest created on Drive")
        except Exception as e:
            print(f"[GWS] Warning: Could not upload manifest: {e}")
    
    def cleanup_old_archives(self, keep_count: int = 5):
        """Remove old archives, keeping only the most recent."""
        if not self.folder_id:
            return
        
        try:
            query = f"'{self.folder_id}' in parents and name contains '{GWS_CONFIG['archive_prefix']}' and trashed=false"
            result = self._run_gws([
                "drive", "files", "list",
                "--params", json.dumps({"q": query, "orderBy": "createdTime desc", "pageSize": 100})
            ])
            
            files = result.get("files", [])
            if len(files) > keep_count:
                for file in files[keep_count:]:
                    print(f"[GWS] Removing old archive: {file['name']}")
                    self._run_gws([
                        "drive", "files", "delete",
                        "--params", json.dumps({"fileId": file["id"]})
                    ])
        except Exception as e:
            print(f"[GWS] Warning: Cleanup failed: {e}")
    
    def run(self):
        """Execute full sync workflow."""
        print("=" * 60)
        print("KISWARM Layer 5: GWS Iron Mountain Sync")
        print("=" * 60)
        
        # 1. Get/create folder
        self.get_or_create_folder()
        
        # 2. Create archive
        archive_path, archive_name, file_hash, version = self.create_archive()
        
        # 3. Upload
        file_id = self.upload_archive(archive_path, archive_name)
        
        # 4. Update manifest
        self.update_manifest(file_id, archive_name, file_hash, version)
        
        # 5. Cleanup old archives
        self.cleanup_old_archives(keep_count=5)
        
        # 6. Remove local archive
        os.remove(archive_path)
        
        print("\n" + "=" * 60)
        print("✅ Layer 5 Sync Complete")
        print(f"   Version: {version}")
        print(f"   File ID: {file_id}")
        print("=" * 60)


def download_latest_version(output_path: str = "/tmp/kiswarm_latest.zip") -> str:
    """
    Download latest KISWARM version from Drive.
    
    This is the fallback function for Layer 5 recovery.
    """
    print("[GWS] Downloading latest version from Iron Mountain...")
    
    # Get manifest
    credentials_file = os.environ.get(GWS_CONFIG["credentials_env"])
    if not credentials_file:
        raise RuntimeError("No credentials configured for Layer 5 fallback")
    
    os.environ["GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE"] = credentials_file
    
    # Download manifest first
    # In production, we'd have the manifest file ID embedded
    # For now, list files and find latest
    
    result = subprocess.run([
        "gws", "drive", "files", "list",
        "--params", json.dumps({
            "q": f"name contains '{GWS_CONFIG['archive_prefix']}' and trashed=false",
            "orderBy": "createdTime desc",
            "pageSize": 1
        })
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to list files: {result.stderr}")
    
    data = json.loads(result.stdout)
    if not data.get("files"):
        raise RuntimeError("No archives found on Drive")
    
    latest_file = data["files"][0]
    file_id = latest_file["id"]
    
    # Download
    download_result = subprocess.run([
        "gws", "drive", "files", "get",
        "--params", json.dumps({"fileId": file_id}),
        "--output", output_path
    ], capture_output=True, text=True)
    
    if download_result.returncode != 0:
        raise RuntimeError(f"Failed to download: {download_result.stderr}")
    
    print(f"[GWS] Downloaded: {latest_file['name']} → {output_path}")
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KISWARM GWS Drive Sync")
    parser.add_argument("--credentials", type=str, help="Path to service-account.json")
    parser.add_argument("--download", action="store_true", help="Download latest version")
    parser.add_argument("--output", type=str, default="/tmp/kiswarm_latest.zip", help="Download output path")
    
    args = parser.parse_args()
    
    if args.download:
        download_latest_version(args.output)
    else:
        syncer = GWSDriveSync(credentials_file=args.credentials)
        syncer.run()

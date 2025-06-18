from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import time
import pickle
import hashlib
import json
from datetime import datetime
from threading import Thread
import logging
import difflib
from dataclasses import dataclass

@dataclass
class DriveConfig:
    """Configuration settings for DriveSync"""
    folder_name: str = 'CodeSync'
    file_types: tuple = ('.py',)  # File extensions to sync
    sync_interval: int = 120  # seconds
    changelog_dir: str = 'changelogs'
    token_path: str = 'token.pickle'
    credentials_path: str = 'client_secrets.json'
    log_level: int = logging.INFO

class DriveSync:
    def __init__(self, config=None):
        self.config = config or DriveConfig()
        self.SCOPES = ['https://www.googleapis.com/auth/drive.file']
        self.token_path = 'token.pickle'
        self.running = False
        self.file_hashes = {}
        self.changelog_dir = 'changelogs'
        self.service = None  # Google Drive service
        self.file_contents = {}  # Store previous contents for diff
        self.folder_id = None  # Store Drive folder ID
        self.setup_logging()
        self.ensure_changelog_dir()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

    def ensure_changelog_dir(self):
        """Create changelog directory if it doesn't exist"""
        if not os.path.exists(self.changelog_dir):
            os.makedirs(self.changelog_dir)
            self.logger.info(f"Created changelog directory: {self.changelog_dir}")

    def get_file_diff(self, filename, old_content, new_content):
        """Generate unified diff between old and new content"""
        diff = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"{filename} (previous)",
            tofile=f"{filename} (current)",
            fromfiledate=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        return ''.join(diff)

    def authenticate(self):
        """Authenticate and create/get Drive folder"""
        creds = None
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.credentials_path,
                    self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)
        self.create_drive_folder()
        self.logger.info("Authentication successful!")

    def create_drive_folder(self):
        """Create or get the sync folder in Drive"""
        self.logger.debug(f"Looking for folder: {self.config.folder_name}")
        query = f"name='{self.config.folder_name}' and mimeType='application/vnd.google-apps.folder'"
        results = self.service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
        files = results.get('files', [])

        if files:
            self.folder_id = files[0]['id']
            self.logger.info(f"Using existing folder: {self.config.folder_name}")
        else:
            file_metadata = {
                'name': self.config.folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            file = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            self.folder_id = file.get('id')
            self.logger.info(f"Created new folder: {self.config.folder_name}")

    def get_file_hash(self, filename):
        """Calculate MD5 hash of file content"""
        with open(filename, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def get_file_changes(self, filename, old_content, new_content):
        """Generate diff between old and new content"""
        diff = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=filename,
            tofile=filename,
            fromfiledate=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            tofiledate='updated'
        )
        return ''.join(diff)

    def update_changelog(self, filename, new_content):
        """Update changelog for a file"""
        changelog_file = os.path.join(self.changelog_dir, f"{filename}.json")
        
        # Get old content for comparison
        old_content = self.file_contents.get(filename, "")
        
        # Only create changelog if content changed
        if old_content != new_content:
            changes = self.get_file_diff(filename, old_content, new_content)
            
            # Load existing changelog
            changelog = []
            if os.path.exists(changelog_file):
                with open(changelog_file, 'r') as f:
                    changelog = json.load(f)
            
            # Add new entry
            changelog.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'changes': changes
            })
            
            # Save updated changelog
            with open(changelog_file, 'w') as f:
                json.dump(changelog, f, indent=2)
            
            # Update stored content
            self.file_contents[filename] = new_content
            self.logger.info(f"Updated changelog for {filename}")

    def upload_file(self, filename):
        """Upload file to Drive with detailed logging"""
        try:
            if not self.folder_id:
                self.logger.error("No folder ID available")
                return False

            # Log file details
            self.logger.debug(f"Attempting to upload: {filename}")
            self.logger.debug(f"Folder ID: {self.folder_id}")

            #Update changelog before upload
            with open(filename, 'r') as f:
                new_content = f.read()
            self.update_changelog(filename, new_content)

            
            # Create file metadata
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }

            # Create media upload object with explicit MIME type
            media = MediaFileUpload(
                filename,
                mimetype='text/x-python',  # Specific MIME type for Python files
                resumable=True
            )

            # Check for existing file
            query = f"name='{filename}' and '{self.folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                spaces='drive'
            ).execute()
            
            self.logger.debug(f"Search results: {results}")
            files = results.get('files', [])

            if files:
                file_id = files[0]['id']
                self.logger.debug(f"Updating existing file: {file_id}")
                file = self.service.files().update(
                    fileId=file_id,
                    media_body=media,
                    fields='id'  # Request ID in response
                ).execute()
                self.logger.info(f"Updated file with ID: {file.get('id')}")
            else:
                self.logger.debug("Creating new file")
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id',  # Request ID in response
                    supportsAllDrives=True
                ).execute()
                self.logger.info(f"Created new file with ID: {file.get('id')}")

            return True

        except Exception as e:
            self.logger.error(f"Upload error for {filename}: {str(e)}", exc_info=True)
            return False

    def verify_file_in_drive(self, filename):
        """Verify if file exists in Drive folder"""
        query = f"name='{filename}' and '{self.folder_id}' in parents and trashed=false"
        results = self.service.files().list(
            q=query,
            fields="files(id, name, modifiedTime)",
            spaces='drive'
        ).execute()
        
        files = results.get('files', [])
        if files:
            self.logger.info(f"Found file in Drive: {files[0]}")
            return True
        else:
            self.logger.error(f"File not found in Drive: {filename}")
            return False

    def start_sync(self, interval=120):
        """Start sync with proper process management"""
        self.running = True
        self.authenticate()
        
        # Create PID file to track process
        pid = os.getpid()
        with open('sync.pid', 'w') as f:
            f.write(str(pid))
        
        def sync_loop():
            while self.running:
                try:
                    self.sync_files()
                    time.sleep(interval)
                except Exception as e:
                    self.logger.error(f"Sync error: {str(e)}")
                    time.sleep(interval)  # Continue even after errors

        self.sync_thread = Thread(target=sync_loop, daemon=True)
        self.sync_thread.start()
        self.logger.info(f"Started sync (PID: {pid}) every {interval} seconds")

    def stop_sync(self):
        """Gracefully stop sync process"""
        self.running = False
        if hasattr(self, 'sync_thread'):
            self.logger.info("Stopping sync process...")
            self.sync_thread.join(timeout=2)  # Wait up to 2 seconds
            self.logger.info("Sync process stopped")

    def sync_files(self):
        """Sync files matching configured types"""
        for filename in os.listdir('.'):
            if any(filename.endswith(ext) for ext in self.config.file_types):
                current_hash = self.get_file_hash(filename)
                
                if filename not in self.file_hashes or self.file_hashes[filename] != current_hash:
                    self.logger.info(f"Changes detected in {filename}")
                    
                    with open(filename, 'r') as f:
                        new_content = f.read()
                    
                    self.update_changelog(filename, new_content)
                    
                    if self.upload_file(filename):
                        self.file_hashes[filename] = current_hash
                        self.logger.info(f"Successfully synced changes in {filename}")

    def view_changelog(self, filename):
        """View change history for a file"""
        changelog_file = os.path.join(self.changelog_dir, f"{filename}.json")
        if os.path.exists(changelog_file):
            with open(changelog_file, 'r') as f:
                return json.load(f)
        return []
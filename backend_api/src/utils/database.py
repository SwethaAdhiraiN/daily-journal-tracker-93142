import json
import os
import fcntl
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from threading import Lock
import logging

logger = logging.getLogger(__name__)

class JSONDatabase:
    """Thread-safe JSON file database for user and journal data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.entries_file = os.path.join(data_dir, "entries.json")
        self._file_locks = {}
        self._ensure_data_directory()
        
    def _ensure_data_directory(self):
        """Ensure data directory and files exist"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize users file if it doesn't exist
        if not os.path.exists(self.users_file):
            self._write_json_file(self.users_file, {})
            
        # Initialize entries file if it doesn't exist
        if not os.path.exists(self.entries_file):
            self._write_json_file(self.entries_file, {})
    
    def _get_file_lock(self, filepath: str) -> Lock:
        """Get or create a lock for a specific file"""
        if filepath not in self._file_locks:
            self._file_locks[filepath] = Lock()
        return self._file_locks[filepath]
    
    def _read_json_file(self, filepath: str) -> Dict[str, Any]:
        """Safely read JSON file with file locking"""
        lock = self._get_file_lock(filepath)
        
        with lock:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                    data = json.load(f)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
                    return data
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f"Error reading {filepath}: {e}")
                return {}
    
    def _write_json_file(self, filepath: str, data: Dict[str, Any]) -> bool:
        """Safely write JSON file with file locking"""
        lock = self._get_file_lock(filepath)
        
        with lock:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock for writing
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
                    return True
            except Exception as e:
                logger.error(f"Error writing {filepath}: {e}")
                return False
    
    # User Operations
    def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create a new user and return user ID"""
        users = self._read_json_file(self.users_file)
        
        # Check if username or email already exists
        for user_id, user in users.items():
            if user.get('username') == user_data.get('username'):
                raise ValueError("Username already exists")
            if user.get('email') == user_data.get('email'):
                raise ValueError("Email already exists")
        
        # Generate new user ID
        user_id = str(uuid.uuid4())
        user_data['id'] = user_id
        user_data['created_at'] = datetime.utcnow().isoformat()
        user_data['is_active'] = True
        
        users[user_id] = user_data
        
        if self._write_json_file(self.users_file, users):
            return user_id
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        users = self._read_json_file(self.users_file)
        return users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        users = self._read_json_file(self.users_file)
        for user_id, user in users.items():
            if user.get('username') == username:
                return user
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        users = self._read_json_file(self.users_file)
        for user_id, user in users.items():
            if user.get('email') == email:
                return user
        return None
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        users = self._read_json_file(self.users_file)
        
        if user_id not in users:
            return False
        
        # Update only provided fields
        for key, value in update_data.items():
            if key != 'id':  # Don't allow ID changes
                users[user_id][key] = value
        
        users[user_id]['updated_at'] = datetime.utcnow().isoformat()
        return self._write_json_file(self.users_file, users)
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete by setting is_active to False)"""
        users = self._read_json_file(self.users_file)
        
        if user_id not in users:
            return False
        
        users[user_id]['is_active'] = False
        users[user_id]['deleted_at'] = datetime.utcnow().isoformat()
        return self._write_json_file(self.users_file, users)
    
    # Journal Entry Operations
    def create_entry(self, entry_data: Dict[str, Any]) -> Optional[str]:
        """Create a new journal entry and return entry ID"""
        entries = self._read_json_file(self.entries_file)
        
        # Generate new entry ID
        entry_id = str(uuid.uuid4())
        entry_data['id'] = entry_id
        entry_data['created_at'] = datetime.utcnow().isoformat()
        entry_data['updated_at'] = datetime.utcnow().isoformat()
        
        entries[entry_id] = entry_data
        
        if self._write_json_file(self.entries_file, entries):
            return entry_id
        return None
    
    def get_entry_by_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get entry by ID"""
        entries = self._read_json_file(self.entries_file)
        return entries.get(entry_id)
    
    def get_entries_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get entries by user ID with pagination"""
        entries = self._read_json_file(self.entries_file)
        user_entries = []
        
        for entry_id, entry in entries.items():
            if entry.get('user_id') == user_id and not entry.get('deleted', False):
                user_entries.append(entry)
        
        # Sort by created_at (newest first)
        user_entries.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Apply pagination
        return user_entries[offset:offset + limit]
    
    def search_entries(self, user_id: str, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search entries with filters"""
        entries = self._read_json_file(self.entries_file)
        results = []
        
        query = search_params.get('query', '').lower()
        mood_filter = search_params.get('mood')
        tags_filter = search_params.get('tags', [])
        date_from = search_params.get('date_from')
        date_to = search_params.get('date_to')
        limit = search_params.get('limit', 20)
        offset = search_params.get('offset', 0)
        
        for entry_id, entry in entries.items():
            if entry.get('user_id') != user_id or entry.get('deleted', False):
                continue
            
            # Text search in title and content
            if query:
                title = entry.get('title', '').lower()
                content = entry.get('content', '').lower()
                if query not in title and query not in content:
                    continue
            
            # Mood filter
            if mood_filter and entry.get('mood') != mood_filter:
                continue
            
            # Tags filter
            if tags_filter:
                entry_tags = entry.get('tags', [])
                if not any(tag in entry_tags for tag in tags_filter):
                    continue
            
            # Date range filter
            entry_date = entry.get('created_at', '')
            if date_from and entry_date < date_from.isoformat():
                continue
            if date_to and entry_date > date_to.isoformat():
                continue
            
            results.append(entry)
        
        # Sort by created_at (newest first)
        results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Apply pagination
        return results[offset:offset + limit]
    
    def update_entry(self, entry_id: str, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update journal entry"""
        entries = self._read_json_file(self.entries_file)
        
        if entry_id not in entries:
            return False
        
        entry = entries[entry_id]
        
        # Check ownership
        if entry.get('user_id') != user_id:
            return False
        
        # Update only provided fields
        for key, value in update_data.items():
            if key not in ['id', 'user_id', 'created_at']:  # Don't allow these changes
                entry[key] = value
        
        entry['updated_at'] = datetime.utcnow().isoformat()
        entries[entry_id] = entry
        
        return self._write_json_file(self.entries_file, entries)
    
    def delete_entry(self, entry_id: str, user_id: str) -> bool:
        """Delete journal entry (soft delete)"""
        entries = self._read_json_file(self.entries_file)
        
        if entry_id not in entries:
            return False
        
        entry = entries[entry_id]
        
        # Check ownership
        if entry.get('user_id') != user_id:
            return False
        
        entry['deleted'] = True
        entry['deleted_at'] = datetime.utcnow().isoformat()
        entries[entry_id] = entry
        
        return self._write_json_file(self.entries_file, entries)
    
    def get_user_entry_count(self, user_id: str) -> int:
        """Get total count of user entries"""
        entries = self._read_json_file(self.entries_file)
        count = 0
        
        for entry in entries.values():
            if entry.get('user_id') == user_id and not entry.get('deleted', False):
                count += 1
        
        return count


# Global database instance
db = JSONDatabase()

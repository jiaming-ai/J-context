"""
Project manager module for organizing and persisting project data.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from .history_manager import HistoryManager
from .global_settings import GlobalSettings


class ProjectManager:
    """Manages project organization and persistent storage."""

    def __init__(self, global_settings: Optional[GlobalSettings] = None):
        self.global_settings = global_settings or GlobalSettings()
        self.app_data_dir = self.global_settings.app_data_dir
        self.projects_file = os.path.join(self.app_data_dir, "projects.json")
        self.projects: Dict[str, Dict] = {}
        self.current_project_id: Optional[str] = None
        self.current_project_data: Optional[Dict] = None
        
        # Ensure app data directory exists
        os.makedirs(self.app_data_dir, exist_ok=True)
        
        # Load existing projects
        self.load_projects()
    
    def _get_app_data_dir(self) -> str:
        """Get the application data directory in user's home."""
        home_dir = Path.home()
        
        # Use platform-appropriate directory
        if os.name == 'nt':  # Windows
            app_data = home_dir / "AppData" / "Local" / "JContext"
        else:  # Unix-like (Linux, macOS)
            app_data = home_dir / ".jcontext"
        
        return str(app_data)
    
    def _get_project_dir(self, project_id: str) -> str:
        """Get the directory for a specific project."""
        project_dir = os.path.join(self.app_data_dir, "projects", project_id)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir
    
    def load_projects(self):
        """Load projects from file."""
        if os.path.exists(self.projects_file):
            try:
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    self.projects = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.projects = {}
        else:
            self.projects = {}
    
    def save_projects(self):
        """Save projects to file."""
        try:
            with open(self.projects_file, 'w', encoding='utf-8') as f:
                json.dump(self.projects, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving projects: {e}")

    def set_app_data_dir(self, path: str):
        """Change the app data directory and reload projects."""
        if not path:
            return
        self.app_data_dir = path
        self.projects_file = os.path.join(self.app_data_dir, "projects.json")
        os.makedirs(self.app_data_dir, exist_ok=True)
        self.load_projects()
    
    def create_or_update_project(self, project_path: str, name: Optional[str] = None) -> str:
        """Create a new project or update existing one."""
        # Generate project ID from path
        project_id = self._generate_project_id(project_path)
        
        # Get project name
        if not name:
            name = os.path.basename(project_path.rstrip(os.sep))
        
        # Create/update project data
        project_data = {
            "id": project_id,
            "name": name,
            "path": project_path,
            "created": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "settings": {
                "ignored_dirs": self.global_settings.default_ignored_dirs,
                "indexed_extensions": self.global_settings.default_indexed_extensions,
            },
        }
        
        # Update if project already exists
        if project_id in self.projects:
            existing = self.projects[project_id]
            project_data["created"] = existing.get("created", project_data["created"])
            project_data["settings"] = existing.get("settings", project_data["settings"])
        
        self.projects[project_id] = project_data
        self.save_projects()
        
        return project_id
    
    def _generate_project_id(self, project_path: str) -> str:
        """Generate a unique project ID from path."""
        # Use hash of normalized path
        import hashlib
        normalized_path = os.path.normpath(os.path.abspath(project_path))
        return hashlib.md5(normalized_path.encode()).hexdigest()[:12]
    
    def get_project_list(self) -> List[Dict]:
        """Get list of all projects sorted by last accessed."""
        projects = list(self.projects.values())
        projects.sort(key=lambda p: p.get("last_accessed", ""), reverse=True)
        return projects
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get a specific project by ID."""
        return self.projects.get(project_id)
    
    def set_current_project(self, project_id: str) -> bool:
        """Set the current active project."""
        if project_id in self.projects:
            self.current_project_id = project_id
            self.current_project_data = self.projects[project_id]
            
            # Update last accessed
            self.current_project_data["last_accessed"] = datetime.now().isoformat()
            self.save_projects()
            
            return True
        return False
    
    def get_current_project(self) -> Optional[Dict]:
        """Get the current active project."""
        return self.current_project_data
    
    def get_project_history_manager(self, project_id: str) -> HistoryManager:
        """Get history manager for a specific project."""
        project_dir = self._get_project_dir(project_id)
        history_file = os.path.join(project_dir, "history.json")
        return HistoryManager(history_file)
    
    def get_current_history_manager(self) -> Optional[HistoryManager]:
        """Get history manager for current project."""
        if self.current_project_id:
            return self.get_project_history_manager(self.current_project_id)
        return None
    
    def update_project_settings(self, project_id: str, settings: Dict[str, Any]):
        """Update settings for a project."""
        if project_id in self.projects:
            self.projects[project_id]["settings"].update(settings)
            self.save_projects()
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project and its data."""
        if project_id in self.projects:
            # Delete project data directory
            project_dir = self._get_project_dir(project_id)
            try:
                import shutil
                if os.path.exists(project_dir):
                    shutil.rmtree(project_dir)
            except Exception as e:
                print(f"Error deleting project data: {e}")
            
            # Remove from projects
            del self.projects[project_id]
            self.save_projects()
            
            # Clear current project if it was the deleted one
            if self.current_project_id == project_id:
                self.current_project_id = None
                self.current_project_data = None
            
            return True
        return False
    
    def get_project_by_path(self, path: str) -> Optional[Dict]:
        """Find project by path."""
        normalized_path = os.path.normpath(os.path.abspath(path))
        for project in self.projects.values():
            if os.path.normpath(os.path.abspath(project["path"])) == normalized_path:
                return project
        return None 
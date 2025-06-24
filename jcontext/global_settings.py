import json
import os
from pathlib import Path
from typing import List, Dict, Optional

class GlobalSettings:
    """Manage global application settings."""

    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = root_dir or self._default_root_dir()
        os.makedirs(self.root_dir, exist_ok=True)
        self.settings_file = os.path.join(self.root_dir, "settings.json")
        self.settings = {
            "app_data_dir": os.path.join(self.root_dir, "data"),
            "theme": "clam",
            "font_family": "Arial",
            "font_size": 10,
            "opened_projects": [],  # Store list of opened project IDs
            "default_ignored_dirs": [
                "__pycache__", ".git", ".svn", ".hg", ".vscode", ".idea",
                "node_modules", ".env", "venv", ".venv", "env", "ENV",
                "dist", "build", "target", "bin", "obj", ".pytest_cache"
            ],
            "default_indexed_extensions": [
                ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
                ".cs", ".php", ".rb", ".go", ".rs", ".swift", ".kt", ".scala",
                ".html", ".css", ".scss", ".less", ".xml", ".json", ".yaml", ".yml",
                ".md", ".txt", ".rst", ".sql", ".sh", ".bat", ".ps1", ".r", ".m"
            ]
        }
        self.load()

    def _default_root_dir(self) -> str:
        home = Path.home()
        if os.name == "nt":
            base = home / "AppData" / "Local" / "JContext"
        else:
            base = home / ".jcontext"
        return str(base)

    def load(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.settings.update(data)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

    def save(self):
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving global settings: {e}")

    @property
    def app_data_dir(self) -> str:
        return self.settings.get("app_data_dir", self.root_dir)

    @property
    def default_ignored_dirs(self) -> List[str]:
        return list(self.settings.get("default_ignored_dirs", []))

    @property
    def default_indexed_extensions(self) -> List[str]:
        return list(self.settings.get("default_indexed_extensions", []))
    
    def get_opened_projects(self) -> List[str]:
        """Get list of opened project IDs."""
        return list(self.settings.get("opened_projects", []))
    
    def set_opened_projects(self, project_ids: List[str]):
        """Set list of opened project IDs."""
        self.settings["opened_projects"] = list(project_ids)
        self.save()
    
    def add_opened_project(self, project_id: str):
        """Add a project to the opened projects list."""
        opened = self.get_opened_projects()
        if project_id not in opened:
            opened.append(project_id)
            self.set_opened_projects(opened)
    
    def remove_opened_project(self, project_id: str):
        """Remove a project from the opened projects list."""
        opened = self.get_opened_projects()
        if project_id in opened:
            opened.remove(project_id)
            self.set_opened_projects(opened)

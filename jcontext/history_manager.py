"""
History manager module for storing and retrieving past prompts.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class HistoryManager:
    """Manages the history of prompts and their metadata."""
    
    def __init__(self, history_file: str = "prompt_history.json"):
        self.history_file = history_file
        self.history: List[Dict] = []
        self.load_history()
    
    def load_history(self):
        """Load history from file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.history = []
        else:
            self.history = []
    
    def save_history(self):
        """Save history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_prompt(self, prompt_text: str, project_path: Optional[str] = None, title: Optional[str] = None) -> str:
        """Add a new prompt to history and return its ID."""
        timestamp = datetime.now().isoformat()
        
        # Generate a unique ID
        prompt_id = f"prompt_{len(self.history)}_{int(datetime.now().timestamp())}"
        
        # Create a preview (first 100 characters)
        preview = prompt_text[:100]
        if len(prompt_text) > 100:
            preview += "..."
        
        prompt_entry = {
            "id": prompt_id,
            "text": prompt_text,
            "preview": preview,
            "timestamp": timestamp,
            "project_path": project_path,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": title or ""
        }
        
        # Add to beginning of history (most recent first)
        self.history.insert(0, prompt_entry)
        
        # Limit history size (keep last 100 entries)
        if len(self.history) > 100:
            self.history = self.history[:100]
        
        self.save_history()
        return prompt_id
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict]:
        """Get a specific prompt by ID."""
        for prompt in self.history:
            if prompt.get("id") == prompt_id:
                return prompt
        return None
    
    def get_prompt_text(self, prompt_id: str) -> Optional[str]:
        """Get the text of a specific prompt by ID."""
        prompt = self.get_prompt(prompt_id)
        return prompt.get("text") if prompt else None
    
    def get_all_prompts(self) -> List[Dict]:
        """Get all prompts (ordered by most recent first)."""
        return self.history.copy()
    
    def get_prompt_previews(self) -> List[Dict]:
        """Get prompt previews for display in UI."""
        previews = []
        for prompt in self.history:
            previews.append({
                "id": prompt.get("id"),
                "preview": prompt.get("preview", ""),
                "created": prompt.get("created", ""),
                "project_path": prompt.get("project_path", ""),
                "title": prompt.get("title", "")
            })
        return previews
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt by ID."""
        for i, prompt in enumerate(self.history):
            if prompt.get("id") == prompt_id:
                del self.history[i]
                self.save_history()
                return True
        return False
    
    def clear_history(self):
        """Clear all history."""
        self.history = []
        self.save_history()
    
    def search_prompts(self, query: str) -> List[Dict]:
        """Search prompts by text content."""
        if not query:
            return self.get_all_prompts()
        
        query_lower = query.lower()
        matches = []
        
        for prompt in self.history:
            prompt_text = prompt.get("text", "").lower()
            preview = prompt.get("preview", "").lower()
            title = prompt.get("title", "").lower()
            
            if query_lower in prompt_text or query_lower in preview or query_lower in title:
                matches.append(prompt)
        
        return matches
    
    def get_recent_prompts(self, limit: int = 10) -> List[Dict]:
        """Get the most recent prompts."""
        return self.history[:limit] 
"""
File indexer module for efficient file searching and matching.
"""

import os
import re
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional, Callable


class FileIndexer:
    """Handles file indexing and searching for the project."""
    
    def __init__(self, root_path: Optional[str] = None):
        self.root_path = root_path
        self.file_index: Dict[str, str] = {}  # filename -> full_path
        self.last_updated = 0
        self.update_callback: Optional[Callable] = None
        self.progress_callback: Optional[Callable] = None
        self._lock = threading.Lock()
        self._cancel_indexing = False
        self._indexing_stats = {'files_processed': 0, 'total_files': 0, 'current_dir': ''}
        
        # Common file extensions to index
        self.indexed_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
            '.html', '.css', '.scss', '.less', '.xml', '.json', '.yaml', '.yml',
            '.md', '.txt', '.rst', '.sql', '.sh', '.bat', '.ps1', '.r', '.m'
        }
        
        # Directories to ignore
        self.ignored_dirs = {
            '__pycache__', '.git', '.svn', '.hg', '.vscode', '.idea',
            'node_modules', '.env', 'venv', '.venv', 'env', 'ENV',
            'dist', 'build', 'target', 'bin', 'obj', '.pytest_cache'
        }
        
    def set_root_path(self, path: str):
        """Set the root path and trigger reindexing."""
        if os.path.exists(path) and os.path.isdir(path):
            self.root_path = path
            self.refresh_index()
            return True
        return False
    
    def set_update_callback(self, callback: Callable):
        """Set callback function to be called when index is updated."""
        self.update_callback = callback
    
    def set_progress_callback(self, callback: Callable):
        """Set callback function to be called during indexing progress."""
        self.progress_callback = callback
    
    def cancel_indexing(self):
        """Cancel the current indexing operation."""
        self._cancel_indexing = True
    
    def refresh_index(self):
        """Refresh the file index."""
        if not self.root_path:
            return
        
        self._cancel_indexing = False
        self._indexing_stats = {'files_processed': 0, 'total_files': 0, 'current_dir': ''}
        
        try:
            # First pass: count total files for progress tracking
            if self.progress_callback:
                self._indexing_stats['current_dir'] = 'Scanning...'
                self.progress_callback(self._indexing_stats.copy())
                self._indexing_stats['total_files'] = self._count_files(self.root_path)
            
            with self._lock:
                self.file_index.clear()
                if not self._cancel_indexing:
                    self._build_index(self.root_path)
                    self.last_updated = time.time()
                
            if self.update_callback and not self._cancel_indexing:
                self.update_callback()
        except Exception as e:
            print(f"Error during indexing: {e}")
            if self.progress_callback:
                self.progress_callback({'error': str(e)})
        finally:
            if self.progress_callback:
                if self._cancel_indexing:
                    self.progress_callback({'cancelled': True})
                else:
                    self.progress_callback({'completed': True})
    
    def _count_files(self, path: str) -> int:
        """Count total files for progress tracking."""
        count = 0
        try:
            for item in os.listdir(path):
                if self._cancel_indexing:
                    break
                    
                if item.startswith('.') and item not in {'.gitignore', '.env.example'}:
                    continue
                    
                item_path = os.path.join(path, item)
                
                if os.path.isdir(item_path):
                    if item not in self.ignored_dirs:
                        count += self._count_files(item_path)
                elif os.path.isfile(item_path):
                    _, ext = os.path.splitext(item)
                    if ext.lower() in self.indexed_extensions or not ext:
                        count += 1
        except PermissionError:
            pass
        return count
    
    def _build_index(self, path: str):
        """Recursively build the file index."""
        try:
            # Update progress with current directory
            if self.progress_callback:
                rel_path = os.path.relpath(path, self.root_path) if path != self.root_path else "."
                self._indexing_stats['current_dir'] = rel_path
                if self._indexing_stats['files_processed'] % 50 == 0:  # Update every 50 files
                    self.progress_callback(self._indexing_stats.copy())
            
            for item in os.listdir(path):
                if self._cancel_indexing:
                    break
                    
                if item.startswith('.') and item not in {'.gitignore', '.env.example'}:
                    continue
                    
                item_path = os.path.join(path, item)
                
                if os.path.isdir(item_path):
                    if item not in self.ignored_dirs:
                        self._build_index(item_path)
                elif os.path.isfile(item_path):
                    # Check if file has an indexed extension
                    _, ext = os.path.splitext(item)
                    if ext.lower() in self.indexed_extensions or not ext:
                        # Store relative path from root
                        rel_path = os.path.relpath(item_path, self.root_path)
                        self.file_index[item] = rel_path
                        
                        # Also index the full path for better matching
                        self.file_index[rel_path] = rel_path
                        
                        # Update progress
                        self._indexing_stats['files_processed'] += 1
                        
        except PermissionError:
            pass  # Skip directories we can't access
    
    def search_files(self, query: str, limit: int = 3) -> List[str]:
        """Search for files matching the query."""
        if not query or not self.file_index:
            return []
            
        with self._lock:
            matches = []
            
            # Clean query
            query = query.strip()
            if query.startswith('@'):
                query = query[1:]
                
            if not query:
                return []
            
            # Different matching strategies
            exact_matches = []
            prefix_matches = []
            contains_matches = []
            regex_matches = []
            
            # Try to use query as regex
            try:
                pattern = re.compile(query, re.IGNORECASE)
                use_regex = True
            except re.error:
                use_regex = False
            
            for filename, filepath in self.file_index.items():
                # Exact match (case insensitive)
                if filename.lower() == query.lower():
                    exact_matches.append(filepath)
                # Prefix match
                elif filename.lower().startswith(query.lower()):
                    prefix_matches.append(filepath)
                # Contains match
                elif query.lower() in filename.lower():
                    contains_matches.append(filepath)
                # Regex match
                elif use_regex and pattern.search(filename):
                    regex_matches.append(filepath)
            
            # Combine results in order of preference
            matches.extend(exact_matches[:limit])
            remaining = limit - len(matches)
            if remaining > 0:
                matches.extend(prefix_matches[:remaining])
                remaining = limit - len(matches)
                if remaining > 0:
                    matches.extend(contains_matches[:remaining])
                    remaining = limit - len(matches)
                    if remaining > 0:
                        matches.extend(regex_matches[:remaining])
            
            # Remove duplicates while preserving order
            seen = set()
            unique_matches = []
            for match in matches:
                if match not in seen:
                    seen.add(match)
                    unique_matches.append(match)
            
            return unique_matches[:limit]
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get the content of a file."""
        if not self.root_path:
            return None
            
        try:
            full_path = os.path.join(self.root_path, file_path)
            if not os.path.exists(full_path):
                return None
                
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception:
            return None
    
    def get_file_language(self, file_path: str) -> str:
        """Determine the language/syntax for a file based on its extension."""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.less': 'less',
            '.xml': 'xml',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sql': 'sql',
            '.sh': 'bash',
            '.bat': 'batch',
            '.ps1': 'powershell',
            '.r': 'r',
            '.m': 'matlab'
        }
        
        return language_map.get(ext, 'text')
    
    def get_indexed_files_count(self) -> int:
        """Get the number of indexed files."""
        return len(self.file_index) // 2  # Divide by 2 because we store both filename and filepath 
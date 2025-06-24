"""
File indexer module for efficient file searching and matching.
"""

import os
import re
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional, Callable, Set


class FileIndexer:
    """Handles file indexing and searching for the project."""
    
    def __init__(self, root_path: Optional[str] = None):
        self.root_path = root_path
        # Map of search keys (filename or relative path) to a set of file paths
        # A filename may map to multiple files in different directories.
        self.file_index: Dict[str, Set[str]] = {}
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
        """Count total files for progress tracking using scandir for speed."""
        count = 0
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if self._cancel_indexing:
                        break

                    name = entry.name
                    if name.startswith('.') and name not in {'.gitignore', '.env.example'}:
                        continue

                    if entry.is_dir(follow_symlinks=False):
                        if name not in self.ignored_dirs:
                            count += self._count_files(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        _, ext = os.path.splitext(name)
                        if ext.lower() in self.indexed_extensions or not ext:
                            count += 1
        except PermissionError:
            pass
        return count
    
    def _build_index(self, path: str):
        """Recursively build the file index using scandir."""
        try:
            rel_path = os.path.relpath(path, self.root_path) if path != self.root_path else "."
            self._indexing_stats['current_dir'] = rel_path
            if self._indexing_stats['files_processed'] % 50 == 0:
                self._report_progress()

            with os.scandir(path) as it:
                for entry in it:
                    if self._cancel_indexing:
                        break

                    name = entry.name
                    if name.startswith('.') and name not in {'.gitignore', '.env.example'}:
                        continue

                    if entry.is_dir(follow_symlinks=False):
                        if name not in self.ignored_dirs:
                            self._build_index(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        _, ext = os.path.splitext(name)
                        if ext.lower() in self.indexed_extensions or not ext:
                            rel_path = os.path.relpath(entry.path, self.root_path)
                            # Map filename to one or more relative paths
                            self.file_index.setdefault(name, set()).add(rel_path)

                            # Also index the full relative path for better matching
                            self.file_index.setdefault(rel_path, set()).add(rel_path)
                            self._indexing_stats['files_processed'] += 1
                            if self._indexing_stats['files_processed'] % 50 == 0:
                                self._report_progress()


        except PermissionError:
            pass  # Skip directories we can't access

    def _report_progress(self):
        """Report progress either via callback or stdout."""
        if self.progress_callback:
            self.progress_callback(self._indexing_stats.copy())
        else:
            total = self._indexing_stats.get('total_files', 0)
            processed = self._indexing_stats.get('files_processed', 0)
            current = self._indexing_stats.get('current_dir', '')
            if total:
                percent = (processed / total) * 100
                print(f"Indexing {processed}/{total} files ({percent:.1f}%) - {current}", end='\r', flush=True)
            else:
                print(f"Indexing... ({current})", end='\r', flush=True)
    
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
            
            for key, paths in self.file_index.items():
                for filepath in paths:
                    # Exact match (case insensitive)
                    if key.lower() == query.lower():
                        exact_matches.append(filepath)
                    # Prefix match
                    elif key.lower().startswith(query.lower()):
                        prefix_matches.append(filepath)
                    # Contains match
                    elif query.lower() in key.lower():
                        contains_matches.append(filepath)
                    # Regex match
                    elif use_regex and pattern.search(key):
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
        unique_paths: Set[str] = set()
        for paths in self.file_index.values():
            unique_paths.update(paths)
        return len(unique_paths)

    def get_all_files(self) -> List[str]:
        """Return a sorted list of all indexed file paths."""
        unique_paths: Set[str] = set()
        for paths in self.file_index.values():
            unique_paths.update(paths)
        return sorted(unique_paths)

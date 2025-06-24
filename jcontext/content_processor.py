"""
Content processor module for handling prompt text processing and file content embedding.
"""

import re
from typing import List, Tuple, Optional
from .file_indexer import FileIndexer


class ContentProcessor:
    """Processes prompt content and embeds file contents."""
    
    def __init__(self, file_indexer: FileIndexer):
        self.file_indexer = file_indexer
        
    def extract_file_references(self, text: str) -> List[str]:
        """Extract all file path references from the text."""
        # Pattern to match file paths (simple heuristic)
        # Look for text that looks like file paths: contains / or \ and has extension
        file_pattern = r'(?:[^\s@]+/)*[^\s@/]+\.[a-zA-Z0-9]+'
        matches = re.findall(file_pattern, text)
        
        # Filter to only include files that exist in our index
        valid_files = []
        for match in matches:
            if self.file_indexer.get_file_content(match) is not None:
                valid_files.append(match)
        
        return valid_files
    
    def process_content_for_copy(self, text: str, code_block_edits: dict = None) -> str:
        """Process the text and replace file paths with their content."""
        if not self.file_indexer.root_path:
            return text
        
        processed_text = text
        file_references = self.extract_file_references(text)
        code_block_edits = code_block_edits or {}
        
        # Replace each file reference with its content
        for file_path in file_references:
            # Check if we have edited content for this file
            if file_path in code_block_edits:
                edit_data = code_block_edits[file_path]
                content = edit_data['content']
                language = edit_data['language']
            else:
                content = self.file_indexer.get_file_content(file_path)
                language = self.file_indexer.get_file_language(file_path)
            
            if content is not None:
                # Create the code block
                code_block = f"```{language}\n# {file_path}\n{content}\n```"
                
                # Replace the file path with the code block
                processed_text = processed_text.replace(file_path, code_block)
        
        return processed_text
    
    def extract_file_paths_from_rendered(self, rendered_text: str) -> List[Tuple[str, str, str]]:
        """
        Extract file paths and their content from rendered text (code blocks).
        Returns list of (file_path, language, content) tuples.
        """
        pattern = r'```(\w*)\n# ([^\n]+)\n(.*?)```'
        matches = re.findall(pattern, rendered_text, re.DOTALL)
        
        file_data = []
        for language, file_path, content in matches:
            file_data.append((file_path.strip(), language.strip(), content.strip()))
        
        return file_data
    
    def convert_rendered_to_raw(self, rendered_text: str, original_raw_text: str = "") -> str:
        """
        Convert rendered text back to raw format (code blocks back to file paths).
        This preserves any edits made to the code blocks by saving them separately.
        """
        if not rendered_text:
            return ""
        
        # Extract file data from code blocks
        file_data = self.extract_file_paths_from_rendered(rendered_text)
        
        # Start with the rendered text
        raw_text = rendered_text
        
        # Replace code blocks with file paths, but preserve any non-code-block content
        for file_path, language, content in file_data:
            # Create the pattern to match the entire code block
            code_block_pattern = re.compile(
                re.escape(f"```{language}\n# {file_path}\n") + r'.*?' + re.escape("```"), 
                re.DOTALL
            )
            
            # Replace with just the file path
            raw_text = code_block_pattern.sub(file_path, raw_text)
        
        return raw_text
    
    def preserve_code_block_edits(self, rendered_text: str) -> dict:
        """
        Extract and preserve any edits made to code blocks.
        Returns a dictionary mapping file paths to their edited content.
        """
        edits = {}
        file_data = self.extract_file_paths_from_rendered(rendered_text)
        
        for file_path, language, content in file_data:
            # Get original content from file
            original_content = self.file_indexer.get_file_content(file_path)
            
            # If content differs from original, save the edit
            if original_content and content.strip() != original_content.strip():
                edits[file_path] = {
                    'language': language,
                    'content': content,
                    'original_content': original_content
                }
        
        return edits
    
    def find_at_symbol_position(self, text: str, cursor_pos: int) -> Optional[Tuple[int, int, str]]:
        """
        Find @ symbol and the query after it at the cursor position.
        Returns (start_pos, end_pos, query) or None if not found.
        """
        if cursor_pos <= 0:
            return None
            
        # Look backwards for @ symbol
        at_pos = -1
        for i in range(cursor_pos - 1, -1, -1):
            if text[i] == '@':
                at_pos = i
                break
            elif text[i].isspace():
                # Stop if we hit whitespace before finding @
                break
        
        if at_pos == -1:
            return None
        
        # Look forward for the end of the query (whitespace or end of string)
        end_pos = cursor_pos
        for i in range(cursor_pos, len(text)):
            if text[i].isspace():
                break
            end_pos = i + 1
        
        # Extract the query (everything after @)
        query = text[at_pos + 1:end_pos]
        return (at_pos, end_pos, query)
    
    def replace_at_query_with_path(self, text: str, start_pos: int, end_pos: int, file_path: str) -> str:
        """Replace the @query with the selected file path."""
        return text[:start_pos] + file_path + text[end_pos:]
    
    def validate_file_paths(self, text: str) -> List[Tuple[str, bool]]:
        """
        Validate all file paths in the text.
        Returns list of (file_path, is_valid) tuples.
        """
        file_references = self.extract_file_references(text)
        results = []
        
        for file_path in file_references:
            is_valid = self.file_indexer.get_file_content(file_path) is not None
            results.append((file_path, is_valid))
        
        return results
    
    def get_text_statistics(self, text: str) -> dict:
        """Get statistics about the text content."""
        lines = text.split('\n')
        words = len(text.split())
        characters = len(text)
        file_references = self.extract_file_references(text)
        
        return {
            'lines': len(lines),
            'words': words,
            'characters': characters,
            'file_references': len(file_references),
            'valid_files': len([f for f in file_references 
                              if self.file_indexer.get_file_content(f) is not None])
        }
    
    def preview_processed_content(self, text: str, max_length: int = 500) -> str:
        """Generate a preview of how the processed content would look."""
        processed = self.process_content_for_copy(text)
        
        if len(processed) <= max_length:
            return processed
        
        return processed[:max_length] + "\n... (truncated)" 
# JContext - LLM Context Generator

A powerful GUI application that helps generate prompts with embedded file content for Large Language Models (LLMs). Features intelligent file insertion, render mode, customizable settings, and comprehensive history management.

## Features

### Core Functionality
- **Project Directory Selection**: Select any project directory to work with
- **Smart File Insertion**: Use `@` symbol to search and insert file paths with intelligent autocomplete
- **Regex Search**: Support for partial and regex matching of file names
- **Content Embedding**: Copy button replaces file paths with actual file content in code blocks
- **History Management**: Automatically saves past prompts with titles and allows easy selection

### New Enhanced Features
- **Improved Font System**: Uses common system fonts (Arial/Courier New) for better readability
- **Enhanced Autocomplete Navigation**: Use arrow keys (↑/↓) to navigate file suggestions
- **Title Support**: Add optional titles to your prompts for better organization
- **Configurable Settings**: Customize ignored directories and indexed file extensions
- **Render Mode**: Toggle between raw text and rendered view (file paths as code blocks)
- **Keyboard Shortcuts**: Ctrl+Enter for quick copying, Tab for autocomplete selection
- **Bidirectional Editing**: Edit code blocks in render mode, changes preserved when switching back

## Installation

### Option 1: Using Virtual Environment (Recommended)

```bash
cd J-context
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Option 2: Using System Python

```bash
cd J-context
pip install pyperclip  # Optional, for clipboard functionality
```

## Usage

### Running the Application

```bash
cd J-context
python main.py
```

### How to Use

1. **Select Project Directory**: Click "Browse" to select your project root directory
2. **Add Title (Optional)**: Enter a descriptive title for your prompt
3. **Write Your Prompt**: Type your prompt in the main text area
4. **Insert Files**: Use `@` followed by file name to search and insert files
   - Type `@main.py` to search for files containing "main.py"
   - Use regex patterns like `@.*\.py$` for advanced matching
   - Use ↑/↓ arrow keys to navigate suggestions
   - Press Tab to select the highlighted match
5. **Use Render Mode**: Toggle "Render Mode" to see file paths as code blocks
   - Edit code blocks directly in render mode
   - Changes are preserved when switching back to raw mode
6. **Copy with Content**: Click "Copy with Content" or press Ctrl+Enter
7. **Save to History**: Save your prompts with optional titles for later use
8. **Customize Settings**: Access File → Settings to configure ignored directories and file extensions

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+Enter** | Copy content with file embedding |
| **Tab** | Select highlighted autocomplete suggestion |
| **↑/↓ Arrow Keys** | Navigate autocomplete suggestions |
| **Escape** | Hide autocomplete popup |

### Example Usage

```
Title: Code Review Request

Here's my code structure for the file indexing feature:

@main.py
@jcontext/gui.py
@jcontext/file_indexer.py

Please help me optimize the file indexing performance and suggest improvements for the GUI layout.
```

**In Render Mode, this becomes:**

```
Title: Code Review Request

Here's my code structure for the file indexing feature:

```python
# main.py
#!/usr/bin/env python3
# ... (actual file content)
```

```python
# jcontext/gui.py
"""
Main GUI module for the JContext application.
"""
# ... (actual file content)
```

```python
# jcontext/file_indexer.py
"""
File indexer module for efficient file searching and matching.
"""
# ... (actual file content)
```

Please help me optimize the file indexing performance and suggest improvements for the GUI layout.
```

## Features in Detail

### File Search and Autocomplete

- **Smart Matching**: Combines exact, prefix, contains, and regex matching
- **Enhanced Navigation**: Use arrow keys to navigate through up to 5 suggestions
- **Non-intrusive Popup**: Shows suggestions in a compact popup window
- **Tab Selection**: Press Tab to select the best match
- **Real-time Search**: Updates as you type after the `@` symbol

### Render Mode

- **Visual Preview**: See how your prompt will look with embedded content
- **Direct Editing**: Edit code blocks directly in render mode
- **Bidirectional Sync**: Changes preserved when switching between modes
- **Seamless Workflow**: Perfect for fine-tuning embedded content

### Enhanced Settings

- **Ignored Directories**: Customize which directories to skip during indexing
  - Default: `__pycache__`, `.git`, `node_modules`, `dist`, `build`, etc.
- **File Extensions**: Configure which file types to index
  - Default: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.html`, `.css`, `.md`, etc.
- **Reset to Defaults**: Easily restore default settings

### Advanced History Management

- **Title Support**: Add descriptive titles to organize your prompts
- **Project Association**: Links prompts to specific project directories
- **Quick Preview**: Shows creation date and content preview
- **Search and Filter**: Find past prompts quickly by title or content
- **Bulk Operations**: Clear all history or delete individual items

### File Content Processing

- **Language Detection**: Automatically detects file language based on extension
- **Code Block Formatting**: Wraps file content in appropriate markdown code blocks
- **Error Handling**: Gracefully handles files that can't be read
- **Path Validation**: Verifies file existence and accessibility

## Project Structure

```
J-context/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── jcontext/              # Main package
    ├── __init__.py        # Package initialization
    ├── gui.py             # Enhanced GUI implementation
    ├── file_indexer.py    # File search and indexing
    ├── history_manager.py # History management with titles
    └── content_processor.py # Content processing and render mode
```

## Dependencies

- **Python 3.6+**: Core language
- **tkinter**: GUI framework (included with Python)
- **pyperclip**: Clipboard operations (optional, fallback available)

## Configuration

The application creates the following files in the working directory:

- `prompt_history.json`: Stores prompt history with titles and metadata
- Project-specific index files (created as needed)

All settings are stored in memory and applied to the current session. For persistent settings, use the Settings dialog accessible via File → Settings.

## Advanced Usage Tips

### File Pattern Matching

- **Exact match**: `@main.py` - finds files named exactly "main.py"
- **Prefix match**: `@gui` - finds files starting with "gui"
- **Contains match**: `@index` - finds files containing "index"
- **Regex patterns**: `@.*\.py$` - finds all Python files
- **Path matching**: `@jcontext/gui` - matches files in specific directories

### Render Mode Workflow

1. Write your prompt with file references in raw mode
2. Toggle render mode to see the full content
3. Edit code blocks directly (add comments, remove sections, etc.)
4. Toggle back to raw mode - your edits are preserved
5. Copy with Ctrl+Enter to get the final formatted content

### Performance Optimization

- Use the "Refresh" button to update the file index after adding new files
- The application automatically ignores common build/cache directories
- File indexing runs in the background to avoid blocking the UI
- Larger projects may take a moment to index initially

## Troubleshooting

### Common Issues

1. **"pyperclip not found"**: The app will show content in a popup window instead
2. **Permission errors**: Ensure you have read access to the project directory
3. **Large projects**: Initial indexing may take time for projects with many files
4. **Font issues**: The app automatically falls back to system fonts if needed

### Settings Issues

- If settings seem not to apply, try refreshing the index manually
- Reset to defaults if you encounter issues with custom settings
- Settings are session-based and need to be reapplied each time

## Contributing

This is a modular application designed for easy extension:

1. **File Processing**: Extend `ContentProcessor` class for new features
2. **Search Logic**: Modify `FileIndexer` class for enhanced search capabilities
3. **UI Components**: Add to `JContextGUI` class for new interface elements
4. **History Features**: Extend `HistoryManager` class for additional metadata
5. **Settings**: Add new configuration options via the `SettingsDialog`

## Changelog

### Latest Version
- ✅ Improved font system with common fonts (Arial/Courier New)
- ✅ Enhanced autocomplete with arrow key navigation
- ✅ Optional title field for better prompt organization
- ✅ Configurable settings for directories and file extensions
- ✅ Ctrl+Enter hotkey for quick content copying
- ✅ Render mode toggle with bidirectional editing
- ✅ Expanded window size for better usability
- ✅ Enhanced history management with title support

## License

This project is open source. Feel free to modify and distribute as needed.

## Support

For issues or questions, please check the code comments or create an issue in the project repository. The application includes comprehensive error handling and user-friendly messages to guide you through common scenarios. 
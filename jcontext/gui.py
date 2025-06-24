"""
Main GUI module for the JContext application.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, font
try:
    from ttkthemes import ThemedTk
except ImportError:  # Fallback if ttkthemes is not installed
    ThemedTk = None
import threading
import os
import sys
import platform
from typing import Optional, List
from .file_indexer import FileIndexer
from .history_manager import HistoryManager
from .content_processor import ContentProcessor
from .project_manager import ProjectManager
from .global_settings import GlobalSettings

# Try to import pyperclip, provide fallback if not available
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


class SettingsDialog:
    """Settings dialog for project and global settings."""

    def __init__(self, parent, file_indexer: FileIndexer, global_settings: GlobalSettings):
        self.parent = parent
        self.file_indexer = file_indexer
        self.global_settings = global_settings
        self.result = None
        
    def show(self):
        """Show the settings dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Settings")
        self.dialog.geometry("600x520")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (520 // 2)
        self.dialog.geometry(f"600x520+{x}+{y}")

        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Project settings tab
        proj_tab = ttk.Frame(notebook)
        notebook.add(proj_tab, text="Project")

        ignore_frame = ttk.LabelFrame(proj_tab, text="Ignored Directories", padding=5)
        ignore_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        ttk.Label(ignore_frame, text="Directories to ignore during indexing (one per line):").pack(anchor=tk.W)
        self.ignore_text = scrolledtext.ScrolledText(ignore_frame, height=8)
        self.ignore_text.pack(fill=tk.BOTH, expand=True, pady=5)
        ignore_dirs = '\n'.join(sorted(self.file_indexer.ignored_dirs))
        self.ignore_text.insert('1.0', ignore_dirs)

        ext_frame = ttk.LabelFrame(proj_tab, text="Indexed File Extensions", padding=5)
        ext_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        ttk.Label(ext_frame, text="File extensions to index (one per line, include the dot):").pack(anchor=tk.W)
        self.ext_text = scrolledtext.ScrolledText(ext_frame, height=8)
        self.ext_text.pack(fill=tk.BOTH, expand=True, pady=5)
        extensions = '\n'.join(sorted(self.file_indexer.indexed_extensions))
        self.ext_text.insert('1.0', extensions)

        # Global settings tab
        glob_tab = ttk.Frame(notebook)
        notebook.add(glob_tab, text="Global")

        storage_frame = ttk.LabelFrame(glob_tab, text="Storage Directory", padding=5)
        storage_frame.pack(fill=tk.X, pady=(0, 10))
        self.storage_var = tk.StringVar(value=self.global_settings.app_data_dir)
        ttk.Entry(storage_frame, textvariable=self.storage_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(storage_frame, text="Browse", command=self.browse_storage).pack(side=tk.LEFT, padx=5)

        theme_frame = ttk.LabelFrame(glob_tab, text="Theme and Font", padding=5)
        theme_frame.pack(fill=tk.X, pady=(0, 10))
        themes = []
        if hasattr(self.parent, "get_themes"):
            try:
                themes = sorted(self.parent.get_themes())
            except Exception:
                themes = []
        self.theme_var = tk.StringVar(value=self.global_settings.settings.get("theme", "clam"))
        ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT)
        ttk.Combobox(theme_frame, values=themes, textvariable=self.theme_var, width=15).pack(side=tk.LEFT, padx=5)
        self.font_var = tk.StringVar(value=self.global_settings.settings.get("font_family", "DejaVu Sans"))
        self.font_size_var = tk.IntVar(value=self.global_settings.settings.get("font_size", 10))
        ttk.Label(theme_frame, text="Font:").pack(side=tk.LEFT)
        ttk.Entry(theme_frame, textvariable=self.font_var, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Label(theme_frame, text="Size:").pack(side=tk.LEFT)
        ttk.Spinbox(theme_frame, from_=6, to=32, textvariable=self.font_size_var, width=5).pack(side=tk.LEFT)

        default_frame = ttk.LabelFrame(glob_tab, text="Defaults for New Projects", padding=5)
        default_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(default_frame, text="Ignored Dirs (one per line):").pack(anchor=tk.W)
        self.default_ignore_text = scrolledtext.ScrolledText(default_frame, height=4)
        self.default_ignore_text.pack(fill=tk.BOTH, expand=True, pady=(0,5))
        self.default_ignore_text.insert('1.0', '\n'.join(sorted(self.global_settings.default_ignored_dirs)))
        ttk.Label(default_frame, text="Indexed Extensions (one per line):").pack(anchor=tk.W)
        self.default_ext_text = scrolledtext.ScrolledText(default_frame, height=4)
        self.default_ext_text.pack(fill=tk.BOTH, expand=True)
        self.default_ext_text.insert('1.0', '\n'.join(sorted(self.global_settings.default_indexed_extensions)))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Apply", command=self.apply).pack(side=tk.RIGHT, padx=(0, 5))

        self.parent.wait_window(self.dialog)
        return self.result
        
    def reset_defaults(self):
        """Reset settings to defaults."""
        self.ignore_text.delete('1.0', tk.END)
        self.ignore_text.insert('1.0', '\n'.join(sorted(self.global_settings.default_ignored_dirs)))

        self.ext_text.delete('1.0', tk.END)
        self.ext_text.insert('1.0', '\n'.join(sorted(self.global_settings.default_indexed_extensions)))
        
    def apply(self):
        """Apply the settings."""
        # Get ignored directories
        ignore_text = self.ignore_text.get('1.0', tk.END).strip()
        ignored_dirs = set()
        for line in ignore_text.split('\n'):
            line = line.strip()
            if line:
                ignored_dirs.add(line)
        
        # Get file extensions
        ext_text = self.ext_text.get('1.0', tk.END).strip()
        extensions = set()
        for line in ext_text.split('\n'):
            line = line.strip()
            if line:
                if not line.startswith('.'):
                    line = '.' + line
                extensions.add(line.lower())
        
        # Apply to file indexer
        self.file_indexer.ignored_dirs = ignored_dirs
        self.file_indexer.indexed_extensions = extensions

        # Global settings
        self.global_settings.settings["app_data_dir"] = self.storage_var.get()
        self.global_settings.settings["theme"] = self.theme_var.get()
        self.global_settings.settings["font_family"] = self.font_var.get()
        self.global_settings.settings["font_size"] = int(self.font_size_var.get())
        default_ign = self.default_ignore_text.get('1.0', tk.END).strip().split('\n')
        self.global_settings.settings["default_ignored_dirs"] = [d.strip() for d in default_ign if d.strip()]
        default_ext = self.default_ext_text.get('1.0', tk.END).strip().split('\n')
        cleaned_ext = []
        for ext in default_ext:
            ext = ext.strip()
            if ext:
                if not ext.startswith('.'):
                    ext = '.' + ext
                cleaned_ext.append(ext.lower())
        self.global_settings.settings["default_indexed_extensions"] = cleaned_ext
        self.global_settings.save()

        self.result = True
        self.dialog.destroy()

    def browse_storage(self):
        directory = filedialog.askdirectory(title="Select Storage Directory")
        if directory:
            self.storage_var.set(directory)
        
    def cancel(self):
        """Cancel the dialog."""
        self.result = False
        self.dialog.destroy()


class ProjectTab:
    """Represents a single project tab with its own text editor and components."""
    
    def __init__(self, parent_gui, project_id, project_data):
        self.parent_gui = parent_gui
        self.project_id = project_id
        self.project_data = project_data
        
        # Initialize project-specific components
        self.file_indexer = FileIndexer()
        self.content_processor = ContentProcessor(self.file_indexer)
        self.autocomplete_popup = None
        
        # Project-specific state
        self.title_text = tk.StringVar()
        self.render_mode = tk.BooleanVar(value=False)
        self.raw_text = ""
        self.rendered_text = ""
        self.code_block_edits = {}
        
        # Auto-save state
        self.current_history_id = None  # Track if we're editing an existing item
        self.auto_save_timer = None
        self.last_saved_content = ""
        self.last_saved_title = ""
        
        # Apply project settings to file indexer
        settings = project_data.get('settings', {})
        if 'ignored_dirs' in settings:
            if isinstance(settings['ignored_dirs'], list):
                self.file_indexer.ignored_dirs = set(settings['ignored_dirs'])
            else:
                self.file_indexer.ignored_dirs = settings['ignored_dirs']
        if 'indexed_extensions' in settings:
            if isinstance(settings['indexed_extensions'], list):
                self.file_indexer.indexed_extensions = set(settings['indexed_extensions'])
            else:
                self.file_indexer.indexed_extensions = settings['indexed_extensions']
        
        # Set up file indexer
        if self.file_indexer.set_root_path(project_data['path']):
            self.file_indexer.set_update_callback(self.on_index_updated)
            self.file_indexer.set_progress_callback(self.on_index_progress)
            # Start indexing in background
            threading.Thread(target=self.file_indexer.refresh_index, daemon=True).start()
    
    def create_tab_content(self, parent):
        """Create the content for this project tab."""
        # Main content frame (horizontal split)
        content_frame = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - text editor
        self.setup_text_editor(content_frame)
        
        # Right panel - history and controls
        self.setup_right_panel(content_frame)
        
        return content_frame
    
    def setup_text_editor(self, parent):
        """Set up the main text editor for this project."""
        editor_frame = ttk.Frame(parent)
        parent.add(editor_frame, weight=3)
        
        # Title and prompt label on the same line
        title_frame = ttk.Frame(editor_frame)
        title_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(title_frame, text="Title (optional):").pack(side=tk.LEFT)
        self.title_entry = ttk.Entry(title_frame, textvariable=self.title_text, width=30)
        self.title_entry.pack(side=tk.LEFT, padx=(5, 10))

        ttk.Label(title_frame, text="Prompt Text (use @ to insert files):").pack(side=tk.LEFT)
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(editor_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # Use a more conservative font approach for better Linux compatibility
        default_family = self.parent_gui.get_system_appropriate_font()
        default_size = int(self.parent_gui.global_settings.settings.get("font_size", 10))
        
        try:
            text_font = font.Font(family=default_family, size=default_size)
        except:
            # Fallback to system default
            text_font = font.nametofont("TkTextFont")
        
        self.text_editor = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=text_font,
            undo=True
        )
        self.text_editor.pack(fill=tk.BOTH, expand=True)
        
        # Bind events for autocomplete and navigation
        self.text_editor.bind('<KeyRelease>', self.on_key_release_combined)
        self.text_editor.bind('<KeyPress>', self.on_key_press)
        self.text_editor.bind('<Button-1>', self.hide_autocomplete)
        self.text_editor.bind('<Tab>', self.on_tab_press)
        self.text_editor.bind('<Control-Shift-Return>', self.copy_with_content)
        
        # Bind text change events for auto-save
        self.title_text.trace('w', self.on_text_changed)
        
        # Control buttons
        button_frame = ttk.Frame(editor_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="Copy with Content (Ctrl+Shift+Enter)",
                  command=self.copy_with_content).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="New",
                  command=self.new_prompt).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(button_frame, text="Clear",
                  command=self.clear_text).pack(side=tk.LEFT, padx=(5, 0))

        # Render toggle aligned to the right
        self.render_toggle = ttk.Checkbutton(
            button_frame,
            text="Render Mode",
            variable=self.render_mode,
            command=self.toggle_render_mode
        )
        self.render_toggle.pack(side=tk.RIGHT)

        # Statistics
        self.stats_label = ttk.Label(button_frame, text="")
        self.stats_label.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Set up autocomplete
        self.autocomplete_popup = AutocompletePopup(self.parent_gui.root, self.text_editor)
        
    def setup_right_panel(self, parent):
        """Set up the right panel with history and file tree."""
        right_frame = ttk.Frame(parent)
        parent.add(right_frame, weight=1)

        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # History tab
        history_tab = ttk.Frame(notebook)
        notebook.add(history_tab, text="History")

        list_frame = ttk.Frame(history_tab)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.history_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=scrollbar.set)
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_listbox.bind('<Double-Button-1>', self.load_from_history)
        self.history_listbox.bind('<Button-3>', self.show_history_context_menu)

        # Remove the button frame - no more Load/Delete buttons
        # hist_button_frame = ttk.Frame(history_tab)
        # hist_button_frame.pack(fill=tk.X, pady=5)

        # Files tab
        files_tab = ttk.Frame(notebook)
        notebook.add(files_tab, text="Files")

        tree_frame = ttk.Frame(files_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.files_tree = ttk.Treeview(tree_frame, show='tree')
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=tree_scroll.set)
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_tree.bind('<Double-Button-1>', self.on_file_double_click)

        # Load history and file tree
        self.refresh_history()
        self.refresh_file_tree()
    
    def on_text_changed(self, *args):
        """Handle text change for auto-save (immediate)."""
        self.schedule_auto_save()
    
    def on_text_changed_delayed(self, event):
        """Handle text change for auto-save (after key release)."""
        # Call the original on_key_release handler first
        self.on_key_release(event)
        self.schedule_auto_save()
    
    def on_key_release_combined(self, event):
        """Combined handler for key release - handles both autocomplete and auto-save."""
        # Handle autocomplete first
        self.on_key_release(event)
        # Then schedule auto-save
        self.schedule_auto_save()
    
    def schedule_auto_save(self):
        """Schedule auto-save after a delay."""
        if self.auto_save_timer:
            self.parent_gui.root.after_cancel(self.auto_save_timer)
        self.auto_save_timer = self.parent_gui.root.after(2000, self.auto_save)  # 2 second delay
    
    def auto_save(self):
        """Auto-save the current content."""
        if self.render_mode.get():
            text = self.raw_text if self.raw_text else self.text_editor.get('1.0', tk.END).strip()
        else:
            text = self.text_editor.get('1.0', tk.END).strip()
            
        title = self.title_text.get().strip()
        
        # Check if content has changed
        if text == self.last_saved_content and title == self.last_saved_title:
            return
            
        if not text:  # Don't save empty content
            return
        
        # Set current project and get history manager
        self.parent_gui.project_manager.set_current_project(self.project_id)
        history_manager = self.parent_gui.project_manager.get_current_history_manager()
        if history_manager:
            if self.current_history_id:
                # Update existing item
                history_manager.update_prompt(self.current_history_id, text, title)
            else:
                # Create new item if we don't have one
                if not title:
                    title = "Untitled"
                self.current_history_id = history_manager.add_prompt(text, self.file_indexer.root_path, title)
            
            self.last_saved_content = text
            self.last_saved_title = title
            self.refresh_history()
    
    def new_prompt(self):
        """Create a new prompt from fresh."""
        self.text_editor.delete('1.0', tk.END)
        self.title_text.set("")
        self.raw_text = ""
        self.rendered_text = ""
        self.code_block_edits = {}
        self.render_mode.set(False)
        self.current_history_id = None
        self.last_saved_content = ""
        self.last_saved_title = ""
        self.update_statistics()
    
    def show_history_context_menu(self, event):
        """Show context menu for history items."""
        # Get the item under the cursor
        index = self.history_listbox.nearest(event.y)
        if index < 0:
            return
            
        self.history_listbox.selection_clear(0, tk.END)
        self.history_listbox.selection_set(index)
        
        # Create context menu
        context_menu = tk.Menu(self.parent_gui.root, tearoff=0)
        context_menu.add_command(label="Load", command=self.load_from_history)
        context_menu.add_command(label="Remove", command=self.delete_from_history)
        context_menu.add_command(label="Copy", command=self.copy_history_item)
        context_menu.add_command(label="Duplicate", command=self.duplicate_history_item)
        
        # Show the menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def copy_history_item(self):
        """Copy the selected history item to clipboard."""
        selection = self.history_listbox.curselection()
        if not selection:
            return
            
        # Set current project and get history manager
        self.parent_gui.project_manager.set_current_project(self.project_id)
        history_manager = self.parent_gui.project_manager.get_current_history_manager()
        if not history_manager:
            return
            
        index = selection[0]
        previews = history_manager.get_prompt_previews()
        
        if index < len(previews):
            prompt_id = previews[index]['id']
            prompt_data = history_manager.get_prompt(prompt_id)
            if prompt_data:
                text = prompt_data['text']
                try:
                    if CLIPBOARD_AVAILABLE:
                        pyperclip.copy(text)
                        self.parent_gui.status_text.set("History item copied to clipboard")
                        messagebox.showinfo("Success", "History item copied to clipboard!")
                    else:
                        self.parent_gui.show_processed_content(text)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
    
    def duplicate_history_item(self):
        """Duplicate the selected history item."""
        selection = self.history_listbox.curselection()
        if not selection:
            return
            
        # Set current project and get history manager
        self.parent_gui.project_manager.set_current_project(self.project_id)
        history_manager = self.parent_gui.project_manager.get_current_history_manager()
        if not history_manager:
            return
            
        index = selection[0]
        previews = history_manager.get_prompt_previews()
        
        if index < len(previews):
            prompt_id = previews[index]['id']
            prompt_data = history_manager.get_prompt(prompt_id)
            if prompt_data:
                text = prompt_data['text']
                title = prompt_data.get('title', '')
                # Add " (Copy)" to the title
                new_title = f"{title} (Copy)" if title else "Copy"
                history_manager.add_prompt(text, self.file_indexer.root_path, new_title)
                self.refresh_history()
                self.parent_gui.status_text.set("History item duplicated")
    
    def on_index_updated(self):
        """Called when file index is updated."""
        self.parent_gui.root.after(0, self._update_project_info)
        self.parent_gui.root.after(0, self.refresh_file_tree)
        
    def _update_project_info(self):
        """Update project info display."""
        if self.file_indexer.root_path:
            file_count = self.file_indexer.get_indexed_files_count()
            self.parent_gui.status_text.set(f"Ready - {file_count} files indexed")
        else:
            self.parent_gui.status_text.set("Ready")
    
    def on_index_progress(self, stats):
        """Handle indexing progress updates."""
        self.parent_gui.on_index_progress(stats)
    
    # Include all the text editor methods from the original class
    def on_key_press(self, event):
        """Handle key press events for navigation."""
        if self.autocomplete_popup and self.autocomplete_popup.popup:
            if event.keysym in ['Up', 'Down']:
                if self.autocomplete_popup.move_selection(event.keysym.lower()):
                    return 'break'
        return None
            
    def on_key_release(self, event):
        """Handle key release events for autocomplete."""
        if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Return', 'Escape']:
            if event.keysym == 'Escape':
                self.hide_autocomplete()
            return
            
        self.update_statistics()
        
        if not self.render_mode.get():
            self.check_autocomplete()
    
    def on_tab_press(self, event):
        """Handle tab key press for autocomplete selection."""
        if self.autocomplete_popup and self.autocomplete_popup.popup:
            selected = self.autocomplete_popup.get_selected()
            if selected:
                self.insert_autocomplete_selection(selected)
                return 'break'
        return None
    
    def check_autocomplete(self):
        """Check if we should show autocomplete."""
        cursor_pos = self.text_editor.index(tk.INSERT)
        text = self.text_editor.get('1.0', tk.END)
        
        cursor_char_idx = self.get_cursor_char_index(cursor_pos, text)
        
        at_info = self.content_processor.find_at_symbol_position(text, cursor_char_idx)
        if at_info:
            start_pos, end_pos, query = at_info
            if query:
                suggestions = self.file_indexer.search_files(query, limit=5)
                if suggestions:
                    try:
                        x, y, _, _ = self.text_editor.bbox(tk.INSERT)
                        x += self.text_editor.winfo_rootx()
                        y += self.text_editor.winfo_rooty()
                        
                        self.autocomplete_popup.show(x, y, suggestions)
                        return
                    except tk.TclError:
                        pass
                    
        self.hide_autocomplete()
        
    def get_cursor_char_index(self, cursor_pos, text):
        """Convert tkinter cursor position to character index."""
        lines = text.split('\n')
        line_num, col_num = map(int, cursor_pos.split('.'))
        
        cursor_char_idx = 0
        for i in range(line_num - 1):
            if i < len(lines):
                cursor_char_idx += len(lines[i]) + 1
        cursor_char_idx += col_num
        
        return cursor_char_idx
        
    def insert_autocomplete_selection(self, selected_path):
        """Insert the selected file path from autocomplete."""
        cursor_pos = self.text_editor.index(tk.INSERT)
        text = self.text_editor.get('1.0', tk.END)
        cursor_char_idx = self.get_cursor_char_index(cursor_pos, text)
        
        at_info = self.content_processor.find_at_symbol_position(text, cursor_char_idx)
        if at_info:
            start_pos, end_pos, query = at_info

            start_tk_pos = self.char_index_to_tk_pos(start_pos, text)
            end_tk_pos = self.char_index_to_tk_pos(end_pos, text)

            self.text_editor.delete(start_tk_pos, end_tk_pos)
            self.text_editor.insert(start_tk_pos, selected_path)
        else:
            self.text_editor.insert(cursor_pos, selected_path)

        self.hide_autocomplete()
        
    def char_index_to_tk_pos(self, char_idx, text):
        """Convert character index to tkinter position."""
        lines = text.split('\n')
        current_char = 0
        
        for line_num, line in enumerate(lines):
            if current_char + len(line) >= char_idx:
                col = char_idx - current_char
                return f"{line_num + 1}.{col}"
            current_char += len(line) + 1
            
        return f"{len(lines)}.0"
        
    def hide_autocomplete(self, event=None):
        """Hide the autocomplete popup."""
        if self.autocomplete_popup:
            self.autocomplete_popup.hide()
    
    def toggle_render_mode(self):
        """Toggle between raw and rendered text mode."""
        current_text = self.text_editor.get('1.0', tk.END).rstrip('\n')
        
        if self.render_mode.get():
            self.raw_text = current_text
            self.rendered_text = self.content_processor.process_content_for_copy(current_text)
            
            self.text_editor.delete('1.0', tk.END)
            self.text_editor.insert('1.0', self.rendered_text)
            
            self.hide_autocomplete()
            
        else:
            current_rendered = self.text_editor.get('1.0', tk.END).rstrip('\n')
            
            if current_rendered != self.rendered_text:
                self.code_block_edits = self.content_processor.preserve_code_block_edits(current_rendered)
                converted_raw = self.content_processor.convert_rendered_to_raw(current_rendered, self.raw_text)
                
                self.text_editor.delete('1.0', tk.END)
                self.text_editor.insert('1.0', converted_raw)
                
                self.raw_text = converted_raw
            else:
                self.text_editor.delete('1.0', tk.END)
                self.text_editor.insert('1.0', self.raw_text)
        
        self.update_statistics()
            
    def update_statistics(self):
        """Update text statistics display."""
        text = self.text_editor.get('1.0', tk.END)
        
        if self.render_mode.get() and self.raw_text:
            stats = self.content_processor.get_text_statistics(self.raw_text)
        else:
            stats = self.content_processor.get_text_statistics(text)
        
        edit_count = len(self.code_block_edits)
        edit_text = f" | Edits: {edit_count}" if edit_count > 0 else ""
        
        stats_text = f"Lines: {stats['lines']} | Words: {stats['words']} | Files: {stats['file_references']}{edit_text}"
        self.stats_label.config(text=stats_text)
        
    def copy_with_content(self, event=None):
        """Copy the text with file contents embedded."""
        if self.render_mode.get():
            processed_text = self.text_editor.get('1.0', tk.END).rstrip('\n')
        else:
            text = self.text_editor.get('1.0', tk.END)
            processed_text = self.content_processor.process_content_for_copy(text, self.code_block_edits)
        
        try:
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(processed_text)
                self.parent_gui.status_text.set("Copied to clipboard with file contents")
                messagebox.showinfo("Success", "Content copied to clipboard!")
            else:
                self.parent_gui.show_processed_content(processed_text)
                
            # Create a new history item when copying (only if we don't have a current one)
            if not self.current_history_id:
                self.save_new_history_item()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
    
    def save_new_history_item(self):
        """Save current content as a new history item."""
        if self.render_mode.get():
            text = self.raw_text if self.raw_text else self.text_editor.get('1.0', tk.END).strip()
        else:
            text = self.text_editor.get('1.0', tk.END).strip()
            
        if not text:
            return
        
        title = self.title_text.get().strip()
        if not title:
            title = "Untitled"
        
        # Set current project and get history manager
        self.parent_gui.project_manager.set_current_project(self.project_id)
        history_manager = self.parent_gui.project_manager.get_current_history_manager()
        if history_manager:
            self.current_history_id = history_manager.add_prompt(text, self.file_indexer.root_path, title)
            self.last_saved_content = text
            self.last_saved_title = title
            self.refresh_history()
            self.parent_gui.status_text.set("Saved to history")
            
    def clear_text(self):
        """Clear the text editor."""
        self.text_editor.delete('1.0', tk.END)
        self.title_text.set("")
        self.raw_text = ""
        self.rendered_text = ""
        self.code_block_edits = {}
        self.render_mode.set(False)
        self.current_history_id = None
        self.last_saved_content = ""
        self.last_saved_title = ""
        self.update_statistics()
        
    def refresh_history(self):
        """Refresh the history listbox."""
        self.history_listbox.delete(0, tk.END)
        
        # Set current project and get history manager
        self.parent_gui.project_manager.set_current_project(self.project_id)
        history_manager = self.parent_gui.project_manager.get_current_history_manager()
        if history_manager:
            previews = history_manager.get_prompt_previews()
            for preview in previews:
                title = preview.get('title', '')
                if title:
                    display_text = f"{preview['created']} - {title}"
                else:
                    display_text = f"{preview['created']} - {preview['preview']}"
                self.history_listbox.insert(tk.END, display_text)

    def refresh_file_tree(self):
        """Refresh the file tree view."""
        if not hasattr(self, 'files_tree'):
            return

        self.files_tree.delete(*self.files_tree.get_children())

        if not self.file_indexer.root_path:
            return

        paths = self.file_indexer.get_all_files()
        tree_nodes = {'': ''}

        for path in paths:
            parts = path.split(os.sep)
            parent_key = ''
            for part in parts:
                key = os.path.join(parent_key, part) if parent_key else part
                if key not in tree_nodes:
                    node = self.files_tree.insert(tree_nodes[parent_key], 'end', text=part, open=False)
                    tree_nodes[key] = node
                parent_key = key
            
    def load_from_history(self, event=None):
        """Load selected item from history."""
        selection = self.history_listbox.curselection()
        if not selection:
            return
            
        # Set current project and get history manager
        self.parent_gui.project_manager.set_current_project(self.project_id)
        history_manager = self.parent_gui.project_manager.get_current_history_manager()
        if not history_manager:
            return
            
        index = selection[0]
        previews = history_manager.get_prompt_previews()
        
        if index < len(previews):
            prompt_id = previews[index]['id']
            prompt_data = history_manager.get_prompt(prompt_id)
            if prompt_data:
                text = prompt_data['text']
                title = prompt_data.get('title', '')
                
                self.text_editor.delete('1.0', tk.END)
                self.text_editor.insert('1.0', text)
                self.title_text.set(title)
                self.render_mode.set(False)
                self.raw_text = text
                self.rendered_text = ""
                self.code_block_edits = {}
                
                # Set current history ID and save state
                self.current_history_id = prompt_id
                self.last_saved_content = text
                self.last_saved_title = title
                
                self.update_statistics()
                
    def delete_from_history(self):
        """Delete selected item from history."""
        selection = self.history_listbox.curselection()
        if not selection:
            return
            
        # Set current project and get history manager
        self.parent_gui.project_manager.set_current_project(self.project_id)
        history_manager = self.parent_gui.project_manager.get_current_history_manager()
        if not history_manager:
            return
            
        if messagebox.askyesno("Confirm", "Delete selected history item?"):
            index = selection[0]
            previews = history_manager.get_prompt_previews()
            
            if index < len(previews):
                prompt_id = previews[index]['id']
                history_manager.delete_prompt(prompt_id)
                self.refresh_history()

    def on_file_double_click(self, event=None):
        """Insert file path from tree into the prompt text."""
        item = self.files_tree.focus()
        if not item:
            return

        parts = []
        while item and item != "":
            parts.insert(0, self.files_tree.item(item, "text"))
            item = self.files_tree.parent(item)

        if parts:
            file_path = os.path.join(*parts)
            self.insert_autocomplete_selection(file_path)


class AutocompletePopup:
    """Popup window for file autocomplete suggestions."""
    
    def __init__(self, parent, text_widget):
        self.parent = parent
        self.text_widget = text_widget
        self.popup = None
        self.listbox = None
        self.suggestions = []
        self.selected_index = 0
        
    def show(self, x, y, suggestions):
        """Show the autocomplete popup at the given position."""
        if not suggestions:
            self.hide()
            return
            
        self.suggestions = suggestions
        self.selected_index = 0
        
        if self.popup:
            self.popup.destroy()
            
        self.popup = tk.Toplevel(self.parent)
        self.popup.wm_overrideredirect(True)
        style = ttk.Style(self.parent)
        bg = style.lookup("TEntry", "fieldbackground") or "white"
        fg = style.lookup("TEntry", "foreground") or "black"
        self.popup.configure(bg=bg, relief='solid', borderwidth=1)
        
        # Position the popup
        self.popup.geometry(f"+{x}+{y+20}")
        
        # Create listbox
        default_font = font.nametofont("TkTextFont")
        self.listbox = tk.Listbox(
            self.popup,
            height=min(len(suggestions), 5),
            bg=bg,
            fg=fg,
            font=default_font
        )
        self.listbox.pack()
        
        # Add suggestions
        for suggestion in suggestions:
            self.listbox.insert(tk.END, suggestion)
            
        # Select first item
        self.listbox.selection_set(0)
        
        # Bind events
        self.listbox.bind('<Double-Button-1>', self.on_select)
        self.popup.bind('<Escape>', lambda e: self.hide())
        
    def hide(self):
        """Hide the autocomplete popup."""
        if self.popup:
            self.popup.destroy()
            self.popup = None
            self.listbox = None
    
    def move_selection(self, direction):
        """Move selection up or down."""
        if not self.listbox:
            return False
            
        if direction == 'up':
            if self.selected_index > 0:
                self.selected_index -= 1
        elif direction == 'down':
            if self.selected_index < len(self.suggestions) - 1:
                self.selected_index += 1
        else:
            return False
        
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.selected_index)
        self.listbox.see(self.selected_index)
        return True
    
    def get_selected(self):
        """Get the currently selected suggestion."""
        if self.suggestions and 0 <= self.selected_index < len(self.suggestions):
            return self.suggestions[self.selected_index]
        return None
    
    def on_select(self, event=None):
        """Handle selection of an item."""
        selection = self.listbox.curselection()
        if selection:
            self.selected_index = selection[0]


class JContextGUI:
    """Main GUI application class with tabbed project interface."""

    def __init__(self):
        self.global_settings = GlobalSettings()
        if ThemedTk:
            self.root = ThemedTk(theme=self.global_settings.settings.get("theme", "clam"))
        else:
            self.root = tk.Tk()
            try:
                style = ttk.Style(self.root)
                style.theme_use(self.global_settings.settings.get("theme", "clam"))
            except Exception:
                pass
        self.root.title("JContext - LLM Context Generator")
        self.root.geometry("1200x800")

        # Initialize components
        self.project_manager = ProjectManager(self.global_settings)
        
        # Apply initial theme and menu styling
        self.apply_global_settings()
        
        # GUI state
        self.status_text = tk.StringVar(value="Ready")
        
        # Progress bar for indexing
        self.progress_var = tk.DoubleVar()
        self.progress_text = tk.StringVar(value="")
        
        # Project tabs
        self.project_tabs = {}  # project_id -> ProjectTab instance
        
        # Set up GUI
        # Flag to ignore the first tab changed event fired during initialization
        self.ignore_initial_tab_event = True

        self.setup_gui()

        # Load existing projects
        self.load_existing_projects()

        # Allow tab changed events after initialization
        self.ignore_initial_tab_event = False
        
    def get_system_appropriate_font(self):
        """Get a font that works well on the current system."""
        import platform
        
        system = platform.system()
        if system == "Linux":
            # Common fonts that work well on Linux
            linux_fonts = ["DejaVu Sans", "Liberation Sans", "Ubuntu", "Cantarell"]
            for font_name in linux_fonts:
                try:
                    test_font = font.Font(family=font_name, size=10)
                    if test_font.actual("family") == font_name:
                        return font_name
                except:
                    continue
            return "TkDefaultFont"  # Fallback to system default
        elif system == "Darwin":  # macOS
            return "SF Pro Display"
        else:  # Windows
            return "Segoe UI"
        
    def setup_gui(self):
        """Set up the main GUI components."""
        # Main menu
        self.setup_menu()
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Project tabs notebook
        self.setup_project_tabs(main_frame)
        
        # Status bar
        self.setup_status_bar()
        
    def setup_menu(self):
        """Set up the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.select_new_project)
        file_menu.add_command(label="Refresh Index", command=self.refresh_current_index)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Clear History", command=self.clear_current_history)
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab", command=self.close_current_tab)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def setup_project_tabs(self, parent):
        """Set up the project tabs notebook."""
        self.project_notebook = ttk.Notebook(parent)
        self.project_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create the "+" tab for adding new projects
        self.add_new_tab_button()
        
        # Bind tab selection event
        self.project_notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Bind right-click context menu
        self.project_notebook.bind("<Button-3>", self.show_tab_context_menu)
        
        # Bind left-click for close button detection
        self.project_notebook.bind("<Button-1>", self.on_tab_click)
        
    def add_new_tab_button(self):
        """Add a '+' button tab for creating new projects."""
        # Create a dummy frame for the + tab
        plus_frame = ttk.Frame(self.project_notebook)
        self.project_notebook.add(plus_frame, text=" + ")
        
        # Store reference to the plus tab
        self.plus_tab_index = self.project_notebook.index("end") - 1
        
    def on_tab_changed(self, event):
        """Handle tab selection changes."""
        # The notebook fires a tab changed event when it is first created.
        # Ignore that initial event to avoid opening the project dialog
        # before the user interacts with the UI.
        if getattr(self, "ignore_initial_tab_event", False):
            self.ignore_initial_tab_event = False
            return
        selected_tab = self.project_notebook.select()
        if not selected_tab:
            return
            
        current_index = self.project_notebook.index(selected_tab)
        
        # Check if the + tab was clicked
        if current_index == self.plus_tab_index:
            # User clicked the + tab, open new project dialog
            self.select_new_project()
            # Switch back to the previously selected tab if no new project was created
            if len(self.project_tabs) > 0:
                # Get the last project tab
                for project_id, tab in self.project_tabs.items():
                    tab_index = self.project_notebook.index(tab.tab_id)
                    self.project_notebook.select(tab_index)
                    break
    
    def on_tab_click(self, event):
        """Handle tab click events for close button detection."""
        try:
            tab_index = self.project_notebook.index("@%d,%d" % (event.x, event.y))
        except tk.TclError:
            return  # Click was not on a tab
        
        # Don't handle clicks on the + tab
        if tab_index == self.plus_tab_index:
            return
        
        # Find the project tab
        clicked_project_id = None
        for project_id, tab in self.project_tabs.items():
            if self.project_notebook.index(tab.tab_id) == tab_index:
                clicked_project_id = project_id
                break
        
        if not clicked_project_id:
            return
        
        # Get the tab text to check if close button was clicked
        tab_text = self.project_notebook.tab(tab_index, "text")
        
        # Calculate approximate position of the ✕ symbol
        # Only close if the click is very close to the ✕ position
        tab_bbox = self.project_notebook.bbox(tab_index)
        if tab_bbox:
            tab_x, tab_y, tab_width, tab_height = tab_bbox
            # Check if click is in the rightmost 15 pixels where ✕ would be
            close_area_x = tab_x + tab_width - 15
            if event.x >= close_area_x and "✕" in tab_text:
                self.close_tab_by_id(clicked_project_id)
                return "break"  # Prevent normal tab selection
        
        return None
        
    def select_new_project(self):
        """Open dialog to select a new project directory."""
        # When the application is closing the root window might already be
        # destroyed which would cause filedialog to raise a TclError.  Guard
        # against that situation.
        if not self.root.winfo_exists():
            return
        try:
            directory = filedialog.askdirectory(
                title="Select Project Root Directory"
            )
        except tk.TclError:
            return
        if directory:
            # Create or update project
            project_id = self.project_manager.create_or_update_project(directory)
            self.create_project_tab(project_id)
    
    def create_project_tab(self, project_id):
        """Create a new project tab."""
        project_data = self.project_manager.get_project_by_id(project_id)
        if not project_data:
            messagebox.showerror("Error", "Failed to load project data")
            return
        
        # Check if tab already exists
        if project_id in self.project_tabs:
            # Switch to existing tab
            tab = self.project_tabs[project_id]
            tab_index = self.project_notebook.index(tab.tab_id)
            self.project_notebook.select(tab_index)
            return
        
        # Create new project tab
        project_tab = ProjectTab(self, project_id, project_data)
        
        # Create tab frame
        tab_frame = ttk.Frame(self.project_notebook)
        tab_content = project_tab.create_tab_content(tab_frame)
        
        # Create close button frame for the tab
        close_frame = ttk.Frame(self.project_notebook)
        project_name = os.path.basename(project_data['path'])
        
        # Add tab with close button text
        tab_index = self.plus_tab_index
        tab_text = f"{project_name} ✕"
        self.project_notebook.insert(tab_index, tab_frame, text=tab_text)
        
        # Store tab reference
        project_tab.tab_id = tab_frame
        project_tab.project_name = project_name
        self.project_tabs[project_id] = project_tab
        
        # Add to opened projects in settings
        self.global_settings.add_opened_project(project_id)
        
        # Update plus tab index
        self.plus_tab_index += 1
        
        # Select the new tab
        self.project_notebook.select(tab_index)
        
        # Update status
        self.status_text.set(f"Indexing {project_name}...")
        self.show_progress()
    
    def close_current_tab(self):
        """Close the currently selected project tab."""
        selected_tab = self.project_notebook.select()
        if not selected_tab:
            return
            
        current_index = self.project_notebook.index(selected_tab)
        
        # Don't close the + tab
        if current_index == self.plus_tab_index:
            return
        
        # Find which project tab this is
        project_id_to_remove = None
        for project_id, tab in self.project_tabs.items():
            if tab.tab_id == selected_tab:
                project_id_to_remove = project_id
                break
        
        if project_id_to_remove:
            # Remove tab
            self.project_notebook.forget(current_index)
            
            # Remove from our tracking
            del self.project_tabs[project_id_to_remove]
            
            # Remove from opened projects in settings
            self.global_settings.remove_opened_project(project_id_to_remove)
            
            # Update plus tab index
            self.plus_tab_index -= 1
            
            # Update status
            if len(self.project_tabs) == 0:
                self.status_text.set("Ready - No projects open")
            else:
                self.status_text.set("Ready")
    
    def get_current_project_tab(self):
        """Get the currently active project tab."""
        selected_tab = self.project_notebook.select()
        if not selected_tab:
            return None
            
        current_index = self.project_notebook.index(selected_tab)
        
        # Check if it's the + tab
        if current_index == self.plus_tab_index:
            return None
        
        # Find the corresponding project tab
        for project_id, tab in self.project_tabs.items():
            if tab.tab_id == selected_tab:
                return tab
        
        return None
    
    def load_existing_projects(self):
        """Load existing projects as tabs."""
        # Load projects that were previously opened
        opened_projects = self.global_settings.get_opened_projects()
        for project_id in opened_projects:
            project = self.project_manager.get_project_by_id(project_id)
            if project and os.path.exists(project['path']):
                self.create_project_tab(project_id)
            else:
                # Path doesn't exist anymore, remove from projects and opened list
                if project:
                    self.project_manager.delete_project(project_id)
                self.global_settings.remove_opened_project(project_id)
    
    def close_tab_by_id(self, project_id):
        """Close a specific project tab by its ID."""
        if project_id not in self.project_tabs:
            return
            
        tab = self.project_tabs[project_id]
        tab_index = self.project_notebook.index(tab.tab_id)
        
        # Remove tab
        self.project_notebook.forget(tab_index)
        
        # Remove from our tracking
        del self.project_tabs[project_id]
        
        # Remove from opened projects in settings
        self.global_settings.remove_opened_project(project_id)
        
        # Update plus tab index
        self.plus_tab_index -= 1
        
        # Update status
        if len(self.project_tabs) == 0:
            self.status_text.set("Ready - No projects open")
        else:
            self.status_text.set("Ready")
    
    def show_tab_context_menu(self, event):
        """Show right-click context menu for project tabs."""
        # Find which tab was right-clicked
        try:
            tab_index = self.project_notebook.index("@%d,%d" % (event.x, event.y))
        except tk.TclError:
            return  # Click was not on a tab
        
        # Don't show context menu for + tab
        if tab_index == self.plus_tab_index:
            return
        
        # Find the project tab
        clicked_tab = None
        clicked_project_id = None
        for project_id, tab in self.project_tabs.items():
            if self.project_notebook.index(tab.tab_id) == tab_index:
                clicked_tab = tab
                clicked_project_id = project_id
                break
        
        if not clicked_tab:
            return
        
        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(
            label="Refresh",
            command=lambda: self.refresh_tab_index(clicked_project_id)
        )
        context_menu.add_separator()
        context_menu.add_command(
            label="Close",
            command=lambda: self.close_tab_by_id(clicked_project_id)
        )
        context_menu.add_command(
            label="Close Others",
            command=lambda: self.close_other_tabs(clicked_project_id)
        )
        context_menu.add_command(
            label="Close All",
            command=self.close_all_tabs
        )
        
        # Show the menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def refresh_tab_index(self, project_id):
        """Refresh the file index for a specific project tab."""
        if project_id not in self.project_tabs:
            return
            
        tab = self.project_tabs[project_id]
        self.status_text.set("Refreshing index...")
        self.show_progress()
        
        threading.Thread(target=tab.file_indexer.refresh_index, daemon=True).start()
    
    def close_other_tabs(self, keep_project_id):
        """Close all tabs except the specified one."""
        tabs_to_close = []
        for project_id in self.project_tabs.keys():
            if project_id != keep_project_id:
                tabs_to_close.append(project_id)
        
        for project_id in tabs_to_close:
            self.close_tab_by_id(project_id)
    
    def close_all_tabs(self):
        """Close all project tabs."""
        tabs_to_close = list(self.project_tabs.keys())
        for project_id in tabs_to_close:
            self.close_tab_by_id(project_id)
        
        # Clear all opened projects from settings
        self.global_settings.set_opened_projects([])
    
    def apply_global_settings(self):
        """Apply global settings like theme and font."""
        try:
            # Apply theme
            theme = self.global_settings.settings.get("theme", "clam")
            if hasattr(self.root, 'set_theme'):
                self.root.set_theme(theme)
            else:
                style = ttk.Style(self.root)
                available_themes = style.theme_names()
                if theme in available_themes:
                    style.theme_use(theme)
        except Exception as e:
            print(f"Warning: Could not apply theme: {e}")
    
    def get_themes(self):
        """Get available themes."""
        try:
            if hasattr(self.root, 'get_themes'):
                return self.root.get_themes()
            else:
                style = ttk.Style(self.root)
                return style.theme_names()
        except Exception:
            return ["clam", "alt", "default", "classic"]
    
    def show_settings(self):
        """Show the settings dialog."""
        current_tab = self.get_current_project_tab()
        if current_tab:
            dialog = SettingsDialog(self.root, current_tab.file_indexer, self.global_settings)
            result = dialog.show()
            if result:
                # Apply new settings
                self.apply_global_settings()
                messagebox.showinfo("Settings", "Settings saved successfully!")
        else:
            messagebox.showwarning("Warning", "Please open a project first")
    
    def refresh_current_index(self):
        """Refresh the index for the current project."""
        current_tab = self.get_current_project_tab()
        if current_tab:
            self.status_text.set("Refreshing index...")
            self.show_progress()
            threading.Thread(target=current_tab.file_indexer.refresh_index, daemon=True).start()
        else:
            messagebox.showwarning("Warning", "No project selected")
    
    def clear_current_history(self):
        """Clear history for the current project."""
        current_tab = self.get_current_project_tab()
        if current_tab:
            if messagebox.askyesno("Confirm", "Clear all history for this project?"):
                # Set current project and get history manager
                self.project_manager.set_current_project(current_tab.project_id)
                history_manager = self.project_manager.get_current_history_manager()
                if history_manager:
                    history_manager.clear_all()
                    current_tab.refresh_history()
                    self.status_text.set("History cleared")
        else:
            messagebox.showwarning("Warning", "No project selected")
    
    def show_about(self):
        """Show about dialog."""
        about_text = """JContext - LLM Context Generator

A tool for generating context-rich prompts for Large Language Models.

Features:
- File indexing and search
- Autocomplete for file paths
- Project management
- History tracking with auto-save
- Content processing

Keyboard Shortcuts:
- Ctrl+Shift+Enter: Copy content with file embedding
- Tab: Select autocomplete suggestion  
- Arrow keys: Navigate autocomplete
- Double-click history: Load item
- Right-click history: Context menu

Version: 1.0
"""
        messagebox.showinfo("About JContext", about_text)
    
    def setup_status_bar(self):
        """Set up the status bar."""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Status label
        self.status_label = ttk.Label(status_frame, textvariable=self.status_text)
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Progress bar (initially hidden)
        self.progress_bar = ttk.Progressbar(
            status_frame,
            variable=self.progress_var,
            mode='indeterminate'
        )
        
        # Progress text label
        self.progress_label = ttk.Label(status_frame, textvariable=self.progress_text)
        self.progress_label.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def show_progress(self):
        """Show the progress bar."""
        self.progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)
        self.progress_label.pack(side=tk.RIGHT, padx=5, pady=2)
        self.progress_bar.start(10)
    
    def hide_progress(self):
        """Hide the progress bar."""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()
        self.progress_text.set("")
    
    def on_index_progress(self, stats):
        """Handle indexing progress updates."""
        if stats.get('done', False):
            self.root.after(0, self.hide_progress)
            file_count = stats.get('total_files', 0)
            self.root.after(0, lambda: self.status_text.set(f"Ready - {file_count} files indexed"))
        else:
            processed = stats.get('processed', 0)
            total = stats.get('total', 0)
            if total > 0:
                self.root.after(0, lambda: self.progress_text.set(f"Indexing... {processed}/{total}"))
    
    def show_processed_content(self, content):
        """Show processed content in a new window when clipboard is not available."""
        content_window = tk.Toplevel(self.root)
        content_window.title("Processed Content")
        content_window.geometry("800x600")
        
        # Center the window
        content_window.update_idletasks()
        x = (content_window.winfo_screenwidth() // 2) - (800 // 2)
        y = (content_window.winfo_screenheight() // 2) - (600 // 2)
        content_window.geometry(f"800x600+{x}+{y}")
        
        main_frame = ttk.Frame(content_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Processed content (clipboard not available):").pack(anchor=tk.W, pady=(0, 5))
        
        text_widget = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        text_widget.insert('1.0', content)
        text_widget.config(state=tk.DISABLED)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        def select_all():
            text_widget.config(state=tk.NORMAL)
            text_widget.tag_add(tk.SEL, "1.0", tk.END)
            text_widget.mark_set(tk.INSERT, "1.0")
            text_widget.see(tk.INSERT)
            text_widget.config(state=tk.DISABLED)
        
        ttk.Button(button_frame, text="Select All", command=select_all).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Close", command=content_window.destroy).pack(side=tk.RIGHT)

    # ...existing code...
    def run(self):
        """Run the application."""
        self.root.mainloop()
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
        self.font_var = tk.StringVar(value=self.global_settings.settings.get("font_family", "Arial"))
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
    """Main GUI application class."""

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

        default_family = self.global_settings.settings.get("font_family", "Arial")
        default_size = int(self.global_settings.settings.get("font_size", 10))
        try:
            font.nametofont("TkDefaultFont").configure(family=default_family, size=default_size)
            font.nametofont("TkTextFont").configure(family=default_family, size=default_size)
            font.nametofont("TkMenuFont").configure(family=default_family, size=default_size)
        except Exception:
            pass

        # Initialize components
        self.project_manager = ProjectManager(self.global_settings)
        self.file_indexer = FileIndexer()
        self.content_processor = ContentProcessor(self.file_indexer)
        self.autocomplete_popup = None

        # Apply initial theme and menu styling now that components exist
        self.apply_global_settings()
        
        # GUI state
        self.current_project_path = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")
        self.title_text = tk.StringVar()
        self.render_mode = tk.BooleanVar(value=False)
        
        # Store text content for render mode switching
        self.raw_text = ""
        self.rendered_text = ""
        self.code_block_edits = {}  # Store edits made to code blocks
        
        # Progress bar for indexing
        self.progress_var = tk.DoubleVar()
        self.progress_text = tk.StringVar(value="")
        
        # Set up GUI
        self.setup_gui()
        
        # Set up callbacks
        self.file_indexer.set_update_callback(self.on_index_updated)
        self.file_indexer.set_progress_callback(self.on_index_progress)
        
        # Load the most recent project if available
        self.load_most_recent_project()
        
    def setup_gui(self):
        """Set up the main GUI components."""
        # Main menu
        self.setup_menu()
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Project selection frame
        self.setup_project_frame(main_frame)
        
        # Content frame (horizontal split)
        content_frame = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Left panel - text editor
        self.setup_text_editor(content_frame)
        
        # Right panel - history and controls
        self.setup_right_panel(content_frame)
        
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
        file_menu.add_command(label="Refresh Index", command=self.refresh_index)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Clear History", command=self.clear_history)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def setup_project_frame(self, parent):
        """Set up the project selection frame."""
        project_frame = ttk.LabelFrame(parent, text="Project", padding=5)
        project_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Project selection row
        proj_select_frame = ttk.Frame(project_frame)
        proj_select_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(proj_select_frame, text="Project:").pack(side=tk.LEFT)
        
        self.project_combo = ttk.Combobox(proj_select_frame, state='readonly', width=40)
        self.project_combo.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        self.project_combo.bind('<<ComboboxSelected>>', self.on_project_selected)
        
        ttk.Button(proj_select_frame, text="New Project", command=self.select_new_project).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(proj_select_frame, text="Refresh", command=self.refresh_index).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Current path display
        ttk.Label(project_frame, text="Path:").pack(anchor=tk.W, pady=(5, 0))
        self.path_entry = ttk.Entry(project_frame, textvariable=self.current_project_path, state='readonly')
        self.path_entry.pack(fill=tk.X, pady=2)
        
        # Load projects into combo
        self.refresh_project_list()
        
    def setup_text_editor(self, parent):
        """Set up the main text editor."""
        editor_frame = ttk.Frame(parent)
        parent.add(editor_frame, weight=3)
        
        # Title and prompt label on the same line
        title_frame = ttk.Frame(editor_frame)
        title_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(title_frame, text="Title (optional):").pack(side=tk.LEFT)
        self.title_entry = ttk.Entry(title_frame, textvariable=self.title_text, width=30)
        self.title_entry.pack(side=tk.LEFT, padx=(5, 10))

        ttk.Label(title_frame, text="Prompt Text (use @ to insert files):").pack(side=tk.LEFT)

        # Render toggle will be placed with the control buttons
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(editor_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # Use global font settings
        default_font = (
            self.global_settings.settings.get("font_family", "Arial"),
            int(self.global_settings.settings.get("font_size", 10))
        )
        
        self.text_editor = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=default_font,
            undo=True
        )
        self.text_editor.pack(fill=tk.BOTH, expand=True)
        
        # Bind events for autocomplete and navigation
        self.text_editor.bind('<KeyRelease>', self.on_key_release)
        self.text_editor.bind('<KeyPress>', self.on_key_press)
        self.text_editor.bind('<Button-1>', self.hide_autocomplete)
        self.text_editor.bind('<Tab>', self.on_tab_press)
        self.text_editor.bind('<Control-Return>', self.copy_with_content)
        
        # Control buttons
        button_frame = ttk.Frame(editor_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="Copy with Content (Ctrl+Enter)",
                  command=self.copy_with_content).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Save to History",
                  command=self.save_to_history).pack(side=tk.LEFT, padx=(5, 0))
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
        self.autocomplete_popup = AutocompletePopup(self.root, self.text_editor)
        
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

        hist_button_frame = ttk.Frame(history_tab)
        hist_button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(hist_button_frame, text="Load",
                  command=self.load_from_history).pack(side=tk.LEFT)
        ttk.Button(hist_button_frame, text="Delete",
                  command=self.delete_from_history).pack(side=tk.LEFT, padx=(5, 0))

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
        
    def setup_status_bar(self):
        """Set up the status bar."""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Label(status_frame, textvariable=self.status_text).pack(side=tk.LEFT, padx=5)
        
        # Progress bar for indexing
        self.progress_frame = ttk.Frame(status_frame)
        self.progress_frame.pack(side=tk.RIGHT, padx=5)
        
        self.progress_label = ttk.Label(self.progress_frame, textvariable=self.progress_text)
        self.progress_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, length=200)
        self.progress_bar.pack(side=tk.LEFT)
        
        # Cancel button for indexing
        self.cancel_button = ttk.Button(self.progress_frame, text="Cancel", command=self.cancel_indexing)
        self.cancel_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Initially hide progress components
        self.progress_frame.pack_forget()
        
    def show_settings(self):
        """Show the settings dialog."""
        dialog = SettingsDialog(self.root, self.file_indexer, self.global_settings)
        result = dialog.show()

        if result:
            # Save settings to current project
            current_project = self.project_manager.get_current_project()
            if current_project:
                settings = {
                    'ignored_dirs': list(self.file_indexer.ignored_dirs),
                    'indexed_extensions': list(self.file_indexer.indexed_extensions)
                }
                self.project_manager.update_project_settings(current_project['id'], settings)
            
            self.project_manager.set_app_data_dir(self.global_settings.app_data_dir)
            # Refresh index with new settings
            self.apply_global_settings()
            self.refresh_index()
            self.status_text.set("Settings applied - index refreshed")
        
    def refresh_project_list(self):
        """Refresh the project list in the combo box."""
        projects = self.project_manager.get_project_list()
        project_names = [f"{p['name']} ({p['path']})" for p in projects]
        self.project_combo['values'] = project_names
        
        # Select current project if any
        current_project = self.project_manager.get_current_project()
        if current_project:
            current_name = f"{current_project['name']} ({current_project['path']})"
            if current_name in project_names:
                self.project_combo.set(current_name)
        
    def on_project_selected(self, event=None):
        """Handle project selection from combo box."""
        selection = self.project_combo.get()
        if not selection:
            return
            
        # Extract project path from selection
        path_start = selection.rfind('(') + 1
        path_end = selection.rfind(')')
        if path_start > 0 and path_end > path_start:
            project_path = selection[path_start:path_end]
            
            # Find project by path
            project = self.project_manager.get_project_by_path(project_path)
            if project:
                self.load_project(project['id'])
    
    def select_new_project(self):
        """Open dialog to select a new project directory."""
        directory = filedialog.askdirectory(title="Select Project Root Directory")
        if directory:
            # Create or update project
            project_id = self.project_manager.create_or_update_project(directory)
            self.load_project(project_id)
            self.refresh_project_list()
    
    def load_project(self, project_id: str):
        """Load a project by ID."""
        if self.project_manager.set_current_project(project_id):
            project = self.project_manager.get_current_project()
            self.current_project_path.set(project['path'])
            
            # Apply project settings to file indexer
            settings = project.get('settings', {})
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
            
            # Set file indexer root path and start indexing
            if self.file_indexer.set_root_path(project['path']):
                self.status_text.set(f"Indexing {project['name']}...")
                self.show_progress()
                
                # Index in background
                threading.Thread(target=self.file_indexer.refresh_index, daemon=True).start()
            else:
                messagebox.showerror("Error", "Failed to set project directory")
                
            # Refresh history for this project
            self.refresh_history()
        else:
            messagebox.showerror("Error", "Failed to load project")
                
    def refresh_index(self):
        """Refresh the file index."""
        if not self.file_indexer.root_path:
            messagebox.showwarning("Warning", "Please select a project first")
            return
            
        self.status_text.set("Refreshing index...")
        self.show_progress()
        
        threading.Thread(target=self.file_indexer.refresh_index, daemon=True).start()
    
    def show_progress(self):
        """Show the progress bar."""
        self.progress_frame.pack(side=tk.RIGHT, padx=5)
        self.progress_var.set(0)
        self.progress_text.set("Starting...")
    
    def hide_progress(self):
        """Hide the progress bar."""
        self.progress_frame.pack_forget()
        self.progress_var.set(0)
        self.progress_text.set("")
    
    def cancel_indexing(self):
        """Cancel the current indexing operation."""
        self.file_indexer.cancel_indexing()
        self.status_text.set("Indexing cancelled")
    
    def on_index_progress(self, stats):
        """Handle indexing progress updates."""
        def update_ui():
            if 'error' in stats:
                self.hide_progress()
                self.status_text.set(f"Error: {stats['error']}")
                messagebox.showerror("Indexing Error", f"Failed to index project:\n{stats['error']}")
            elif 'cancelled' in stats:
                self.hide_progress()
                self.status_text.set("Indexing cancelled")
            elif 'completed' in stats:
                self.hide_progress()
                # Will be updated by on_index_updated callback
            else:
                total = stats.get('total_files', 0)
                processed = stats.get('files_processed', 0)
                current_dir = stats.get('current_dir', '')
                
                if total > 0:
                    progress = (processed / total) * 100
                    self.progress_var.set(progress)
                    self.progress_text.set(f"{processed}/{total} files ({current_dir})")
                else:
                    self.progress_text.set(f"Scanning... ({current_dir})")
        
        # Schedule UI update on main thread
        self.root.after(0, update_ui)
    
    def load_most_recent_project(self):
        """Load the most recently accessed project."""
        projects = self.project_manager.get_project_list()
        if projects:
            # Load the first project (most recent)
            most_recent = projects[0]
            if os.path.exists(most_recent['path']):
                self.load_project(most_recent['id'])
            else:
                # Path doesn't exist anymore, remove from projects
                self.project_manager.delete_project(most_recent['id'])
                self.refresh_project_list()
        
    def on_index_updated(self):
        """Called when file index is updated."""
        self.root.after(0, self._update_project_info)
        self.root.after(0, self.refresh_file_tree)
        
    def _update_project_info(self):
        """Update project info display."""
        if self.file_indexer.root_path:
            file_count = self.file_indexer.get_indexed_files_count()
            self.status_text.set(f"Ready - {file_count} files indexed")
        else:
            self.status_text.set("Ready")
    
    def on_key_press(self, event):
        """Handle key press events for navigation."""
        # Handle arrow keys for autocomplete navigation
        if self.autocomplete_popup and self.autocomplete_popup.popup:
            if event.keysym in ['Up', 'Down']:
                if self.autocomplete_popup.move_selection(event.keysym.lower()):
                    return 'break'  # Prevent default behavior
        return None
            
    def on_key_release(self, event):
        """Handle key release events for autocomplete."""
        if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Return', 'Escape']:
            if event.keysym == 'Escape':
                self.hide_autocomplete()
            return
            
        # Update statistics
        self.update_statistics()
        
        # Check for @ symbol autocomplete (only in raw mode)
        if not self.render_mode.get():
            self.check_autocomplete()
        
    def on_tab_press(self, event):
        """Handle tab key press for autocomplete selection."""
        if self.autocomplete_popup and self.autocomplete_popup.popup:
            selected = self.autocomplete_popup.get_selected()
            if selected:
                self.insert_autocomplete_selection(selected)
                return 'break'  # Prevent default tab behavior
        return None
        
    def check_autocomplete(self):
        """Check if we should show autocomplete."""
        cursor_pos = self.text_editor.index(tk.INSERT)
        text = self.text_editor.get('1.0', tk.END)
        
        # Convert cursor position to character index
        cursor_char_idx = self.get_cursor_char_index(cursor_pos, text)
        
        # Check for @ query
        at_info = self.content_processor.find_at_symbol_position(text, cursor_char_idx)
        if at_info:
            start_pos, end_pos, query = at_info
            if query:  # Only show if there's a query
                suggestions = self.file_indexer.search_files(query, limit=5)
                if suggestions:
                    # Get screen coordinates
                    try:
                        x, y, _, _ = self.text_editor.bbox(tk.INSERT)
                        x += self.text_editor.winfo_rootx()
                        y += self.text_editor.winfo_rooty()
                        
                        self.autocomplete_popup.show(x, y, suggestions)
                        return
                    except tk.TclError:
                        pass  # Ignore if bbox fails
                    
        # Hide autocomplete if no @ query
        self.hide_autocomplete()
        
    def get_cursor_char_index(self, cursor_pos, text):
        """Convert tkinter cursor position to character index."""
        lines = text.split('\n')
        line_num, col_num = map(int, cursor_pos.split('.'))
        
        cursor_char_idx = 0
        for i in range(line_num - 1):
            if i < len(lines):
                cursor_char_idx += len(lines[i]) + 1  # +1 for newline
        cursor_char_idx += col_num
        
        return cursor_char_idx
        
    def insert_autocomplete_selection(self, selected_path):
        """Insert the selected file path from autocomplete."""
        cursor_pos = self.text_editor.index(tk.INSERT)
        text = self.text_editor.get('1.0', tk.END)
        cursor_char_idx = self.get_cursor_char_index(cursor_pos, text)
        
        # Find the @ query to replace
        at_info = self.content_processor.find_at_symbol_position(text, cursor_char_idx)
        if at_info:
            start_pos, end_pos, query = at_info

            # Convert character indices back to tkinter positions
            start_tk_pos = self.char_index_to_tk_pos(start_pos, text)
            end_tk_pos = self.char_index_to_tk_pos(end_pos, text)

            # Replace the @query with the selected path
            self.text_editor.delete(start_tk_pos, end_tk_pos)
            self.text_editor.insert(start_tk_pos, selected_path)
        else:
            # No @ query, just insert at cursor
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
            current_char += len(line) + 1  # +1 for newline
            
        return f"{len(lines)}.0"
        
    def hide_autocomplete(self, event=None):
        """Hide the autocomplete popup."""
        if self.autocomplete_popup:
            self.autocomplete_popup.hide()
    
    def toggle_render_mode(self):
        """Toggle between raw and rendered text mode."""
        current_text = self.text_editor.get('1.0', tk.END).rstrip('\n')
        
        if self.render_mode.get():
            # Switching to render mode
            self.raw_text = current_text
            self.rendered_text = self.content_processor.process_content_for_copy(current_text)
            
            # Update text editor with rendered content
            self.text_editor.delete('1.0', tk.END)
            self.text_editor.insert('1.0', self.rendered_text)
            
            # Disable autocomplete in render mode
            self.hide_autocomplete()
            
        else:
            # Switching back to raw mode
            current_rendered = self.text_editor.get('1.0', tk.END).rstrip('\n')
            
            # Check if user made changes to rendered text
            if current_rendered != self.rendered_text:
                # User edited the rendered content - preserve edits and convert back to raw
                self.code_block_edits = self.content_processor.preserve_code_block_edits(current_rendered)
                converted_raw = self.content_processor.convert_rendered_to_raw(current_rendered, self.raw_text)
                
                self.text_editor.delete('1.0', tk.END)
                self.text_editor.insert('1.0', converted_raw)
                
                # Update raw text to preserve the structure
                self.raw_text = converted_raw
            else:
                # No changes, restore original raw text
                self.text_editor.delete('1.0', tk.END)
                self.text_editor.insert('1.0', self.raw_text)
        
        self.update_statistics()
            
    def update_statistics(self):
        """Update text statistics display."""
        text = self.text_editor.get('1.0', tk.END)
        
        # If in render mode, use raw text for statistics
        if self.render_mode.get() and self.raw_text:
            stats = self.content_processor.get_text_statistics(self.raw_text)
        else:
            stats = self.content_processor.get_text_statistics(text)
        
        # Add info about code block edits
        edit_count = len(self.code_block_edits)
        edit_text = f" | Edits: {edit_count}" if edit_count > 0 else ""
        
        stats_text = f"Lines: {stats['lines']} | Words: {stats['words']} | Files: {stats['file_references']}{edit_text}"
        self.stats_label.config(text=stats_text)
        
    def copy_with_content(self, event=None):
        """Copy the text with file contents embedded."""
        if self.render_mode.get():
            # In render mode, copy the current rendered text
            processed_text = self.text_editor.get('1.0', tk.END).rstrip('\n')
        else:
            # In raw mode, process the text first
            text = self.text_editor.get('1.0', tk.END)
            processed_text = self.content_processor.process_content_for_copy(text, self.code_block_edits)
        
        try:
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(processed_text)
                self.status_text.set("Copied to clipboard with file contents")
                messagebox.showinfo("Success", "Content copied to clipboard!")
            else:
                # Fallback: show in a new window
                self.show_processed_content(processed_text)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
            
    def show_processed_content(self, content):
        """Show processed content in a new window."""
        window = tk.Toplevel(self.root)
        window.title("Processed Content")
        window.geometry("800x600")
        
        text_widget = scrolledtext.ScrolledText(window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert('1.0', content)
        text_widget.config(state='disabled')
        
        # Copy button
        def copy_from_window():
            window.clipboard_clear()
            window.clipboard_append(content)
            messagebox.showinfo("Success", "Content copied to clipboard!")
            
        ttk.Button(window, text="Copy to Clipboard", command=copy_from_window).pack(pady=5)
        
    def save_to_history(self):
        """Save current text to history."""
        # Get the appropriate text to save
        if self.render_mode.get():
            text = self.raw_text if self.raw_text else self.text_editor.get('1.0', tk.END).strip()
        else:
            text = self.text_editor.get('1.0', tk.END).strip()
            
        if not text:
            messagebox.showwarning("Warning", "No text to save")
            return
        
        # Get title
        title = self.title_text.get().strip()
        
        # Use current project's history manager
        history_manager = self.project_manager.get_current_history_manager()
        if history_manager:
            history_manager.add_prompt(text, self.file_indexer.root_path, title)
            self.refresh_history()
            self.status_text.set("Saved to history")
        else:
            messagebox.showwarning("Warning", "No project selected")
        
    def clear_text(self):
        """Clear the text editor."""
        self.text_editor.delete('1.0', tk.END)
        self.title_text.set("")
        self.raw_text = ""
        self.rendered_text = ""
        self.code_block_edits = {}
        self.render_mode.set(False)
        self.update_statistics()
        
    def refresh_history(self):
        """Refresh the history listbox."""
        self.history_listbox.delete(0, tk.END)
        
        history_manager = self.project_manager.get_current_history_manager()
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
            
        history_manager = self.project_manager.get_current_history_manager()
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
                self.update_statistics()
                
    def delete_from_history(self):
        """Delete selected item from history."""
        selection = self.history_listbox.curselection()
        if not selection:
            return
            
        history_manager = self.project_manager.get_current_history_manager()
        if not history_manager:
            return
            
        if messagebox.askyesno("Confirm", "Delete selected history item?"):
            index = selection[0]
            previews = history_manager.get_prompt_previews()
            
            if index < len(previews):
                prompt_id = previews[index]['id']
                history_manager.delete_prompt(prompt_id)
                self.refresh_history()
                
    def clear_history(self):
        """Clear all history."""
        history_manager = self.project_manager.get_current_history_manager()
        if not history_manager:
            messagebox.showwarning("Warning", "No project selected")
            return

        if messagebox.askyesno("Confirm", "Clear all history for current project?"):
            history_manager.clear_history()
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
            
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo("About",
                           "JContext - LLM Context Generator\n\n"
                           "A tool for creating LLM prompts with embedded file content.\n\n"
                           "Features:\n"
                           "• Use @ to insert files with autocomplete\n"
                           "• Arrow keys to navigate suggestions\n"
                           "• Render mode to preview/edit content\n"
                           "• Configurable settings\n"
                          "• Ctrl+Enter to copy content")

    def apply_global_settings(self):
        """Apply theme, fonts and storage directory from global settings."""
        if ThemedTk and isinstance(self.root, ThemedTk):
            try:
                self.root.set_theme(self.global_settings.settings.get("theme", "clam"))
            except Exception:
                pass
        else:
            try:
                style = ttk.Style(self.root)
                style.theme_use(self.global_settings.settings.get("theme", "clam"))
            except Exception:
                pass
        family = self.global_settings.settings.get("font_family", "Arial")
        size = int(self.global_settings.settings.get("font_size", 10))
        try:
            font.nametofont("TkDefaultFont").configure(family=family, size=size)
            font.nametofont("TkTextFont").configure(family=family, size=size)
            font.nametofont("TkMenuFont").configure(family=family, size=size)
        except Exception:
            pass

        # Apply menu styling to match theme
        try:
            style = ttk.Style(self.root)
            bg = style.lookup("TFrame", "background")
            fg = style.lookup("TLabel", "foreground")
            self.root.option_add("*Menu.background", bg)
            self.root.option_add("*Menu.foreground", fg)
            self.root.option_add("*Menu.font", font.nametofont("TkMenuFont"))
        except Exception:
            pass
        self.project_manager.set_app_data_dir(self.global_settings.app_data_dir)
        
    def run(self):
        """Run the application."""
        self.root.mainloop() 
import time
import threading
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
from watchdog.observers import Observer

from image_handler import ImageHandler
from settings_manager import SettingsManager
from gui_tabs import MainSettingsTab, ImageProcessingTab, NoteProcessingTab, NoteCommandsTab
from theme_manager import ModernThemeManager


class ImageProcessorGUI:
    HOTKEY_ID = 1
    HOTKEY_ID_CLIPBOARD = 2
    def __init__(self, root):
        self.root = root
        self.root.title("Obsidian Image Processor")
        self.root.geometry("1300x950")
        self.root.minsize(1200, 800)
        
        # Initialize theme
        self.theme = ModernThemeManager()
        self.style = self.theme.apply_modern_theme(root)
        
        # Register theme change callback
        self.theme.register_theme_change_callback(self.on_theme_changed)
        
        # Initialize settings
        self.settings = self._create_settings_variables()
        self.note_commands = self._create_note_command_variables()
        
        self.observer = None
        self.handler = None  # Keep reference to handler
        self.is_running = False

        self._hotkey_thread = None
        self._hotkey_running = False
        
        self.setup_ui()
        self.load_settings()

        # start global hotkey listener (Windows)
        try:
            self.start_global_hotkey()
        except Exception:
            # fail silently if OS not supported or registration fails
            self.log_message("Global hotkey not available", "WARNING")

        
        # Bind override prefix changes to update handler dynamically
        self.settings['override_prefix'].trace('w', self.on_override_prefix_change)
    
    def copy_to_clipboard(self, text):
        """Thread-safe clipboard copy"""
        self.root.after(0, lambda: self._copy_to_clipboard_main_thread(text))
        
    def _copy_to_clipboard_main_thread(self, text):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
        except Exception as e:
            self.log_message(f"Failed to copy to clipboard: {e}", "ERROR")

    def start_global_hotkey(self):
        """Start a background message loop and register Ctrl+Alt+A and Ctrl+Alt+D as global hotkeys (Windows)."""
        if self._hotkey_thread and self._hotkey_thread.is_alive():
            return

        def _hotkey_loop():
            user32 = ctypes.windll.user32
            WM_HOTKEY = 0x0312
            MOD_ALT = 0x0001
            MOD_CONTROL = 0x0002
            VK_A = 0x41
            VK_D = 0x44

            # Register Ctrl+Alt+A (Normal Mode)
            if not user32.RegisterHotKey(None, self.HOTKEY_ID, MOD_CONTROL | MOD_ALT, VK_A):
                self.root.after(0, lambda: self.log_message("Failed to register global hotkey (Ctrl+Alt+A).", "WARNING"))
            
            # Register Ctrl+Alt+D (Clipboard Mode)
            if not user32.RegisterHotKey(None, self.HOTKEY_ID_CLIPBOARD, MOD_CONTROL | MOD_ALT, VK_D):
                self.root.after(0, lambda: self.log_message("Failed to register global hotkey (Ctrl+Alt+D).", "WARNING"))

            msg = wintypes.MSG()
            # message loop will block on GetMessageW
            while self._hotkey_running:
                res = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if res == 0:  # WM_QUIT posted
                    break
                if res == -1:
                    break
                if msg.message == WM_HOTKEY:
                    if msg.wParam == self.HOTKEY_ID:
                        # schedule toggle normal on the tkinter thread
                        self.root.after(0, lambda: self.toggle_monitoring_mode(clipboard=False))
                    elif msg.wParam == self.HOTKEY_ID_CLIPBOARD:
                        # schedule toggle clipboard on the tkinter thread
                        self.root.after(0, lambda: self.toggle_monitoring_mode(clipboard=True))
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

            user32.UnregisterHotKey(None, self.HOTKEY_ID)
            user32.UnregisterHotKey(None, self.HOTKEY_ID_CLIPBOARD)

        self._hotkey_running = True
        self._hotkey_thread = threading.Thread(target=_hotkey_loop, daemon=True)
        self._hotkey_thread.start()

    def stop_global_hotkey(self):
        """Stop the hotkey message loop and unregister the hotkey."""
        if not self._hotkey_thread:
            return
        self._hotkey_running = False
        try:
            # Post WM_QUIT to unblock GetMessageW in the hotkey thread
            WM_QUIT = 0x0012
            ctypes.windll.user32.PostThreadMessageW(self._hotkey_thread.ident, WM_QUIT, 0, 0)
        except Exception:
            pass
        self._hotkey_thread = None

    def _create_settings_variables(self):
        """Create tkinter variables for all settings"""
        defaults = SettingsManager.get_default_settings()
        variables = {}
        
        for key, value in defaults.items():
            if isinstance(value, bool):
                variables[key] = tk.BooleanVar(value=value)
            elif isinstance(value, int):
                variables[key] = tk.IntVar(value=value)
            elif isinstance(value, float):
                variables[key] = tk.DoubleVar(value=value)
            else:
                variables[key] = tk.StringVar(value=value)
        
        return variables
    
    def _create_note_command_variables(self):
        """Create tkinter variables for note commands"""
        defaults = SettingsManager.get_default_note_commands()
        variables = {}
        
        for key, value in defaults.items():
            variables[key] = tk.BooleanVar(value=value)
        
        return variables
        
    def on_theme_changed(self):
        """Called when theme is toggled"""
        # Reapply theme styles
        self.style = self.theme.apply_modern_theme(self.root, self.style)
        
        # Refresh all widget colors
        self.theme.refresh_widget_colors(self.root)
        
        # Update the theme toggle button text
        if hasattr(self, 'theme_button'):
            icon = "🌙" if self.theme.is_dark_mode else "☀️"
            theme_name = self.theme.get_theme_name()
            self.theme_button.config(text=f"{icon} {theme_name} Theme")
        
        # Log the theme change
        theme_name = self.theme.get_theme_name()
        self.log_message(f"Switched to {theme_name} theme", "INFO")
        
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.theme.toggle_theme()
        
    def on_override_prefix_change(self, *args):
        """Called when override prefix changes - updates handler in real-time"""
        if self.handler and self.is_running:
            new_options = {key: var.get() for key, var in self.settings.items()}
            self.handler.update_options(new_options)
            
            override_value = self.settings['override_prefix'].get().strip()
            if override_value:
                self.log_message(f"Override prefix updated to: '{override_value}'", "INFO")
            else:
                self.log_message("Override prefix cleared", "INFO")
        
    def setup_ui(self):
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.theme.colors['bg_secondary'])
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header with title and theme toggle
        header_frame = tk.Frame(main_container, bg=self.theme.colors['bg_secondary'])
        header_frame.pack(fill="x", pady=(0, 10))
        
        # App title
        title_label = tk.Label(
            header_frame,
            text="🖼️ Obsidian Image Processor",
            bg=self.theme.colors['bg_secondary'],
            fg=self.theme.colors['text_primary'],
            font=('Segoe UI', 16, 'bold')
        )
        title_label.pack(side="left")
        
        # Theme toggle button
        icon = "🌙" if self.theme.is_dark_mode else "☀️"
        theme_name = self.theme.get_theme_name()
        self.theme_button = ttk.Button(
            header_frame,
            text=f"{icon} {theme_name} Theme",
            command=self.toggle_theme,
            style='Theme.TButton'
        )
        self.theme_button.pack(side="right")
        
        # Create notebook for tabs with modern styling
        notebook = ttk.Notebook(main_container, style='Modern.TNotebook')
        notebook.pack(fill="both", expand=True)
        
        # Main Settings Tab
        main_tab = tk.Frame(notebook, bg=self.theme.colors['bg_primary'])
        notebook.add(main_tab, text="🏠 Main Settings")
        MainSettingsTab(main_tab, self.settings, self.theme)
        
        # Image Processing Tab
        image_tab = tk.Frame(notebook, bg=self.theme.colors['bg_primary'])
        notebook.add(image_tab, text="🖼️ Image Processing")
        ImageProcessingTab(image_tab, self.settings, self.theme)
        
        # Note Processing Tab
        note_tab = tk.Frame(notebook, bg=self.theme.colors['bg_primary'])
        notebook.add(note_tab, text="📝 Note Processing")
        NoteProcessingTab(note_tab, self.settings, self.theme)
        
        # Note Commands Tab
        commands_tab = tk.Frame(notebook, bg=self.theme.colors['bg_primary'])
        notebook.add(commands_tab, text="⚡ Commands")
        NoteCommandsTab(commands_tab, self.settings, self.note_commands, self.log_message, self.theme)
        
        # Control Panel at bottom
        self.setup_control_panel(main_container)
        
        # Log Output
        self.setup_log_output(main_container)
        
    def setup_control_panel(self, parent):
        """Setup the modern control panel with buttons and status"""
        control_card = self.theme.create_card_frame(parent)
        control_card.pack(fill="x", pady=(15, 0))
        
        # Control content frame
        control_content = tk.Frame(control_card, bg=self.theme.colors['bg_primary'])
        control_content.pack(fill="x", padx=10, pady=8)
        
        # Left side - buttons
        button_frame = tk.Frame(control_content, bg=self.theme.colors['bg_primary'])
        button_frame.pack(side="left", fill="x", expand=True)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="🚀 Start Monitoring", 
            command=self.toggle_monitoring,
            style='Primary.TButton'
        )
        self.start_button.pack(side="left", padx=(0, 6))

        self.start_button.bind("<Control-Alt-a>", lambda e: self.toggle_monitoring())
        
        ttk.Button(
            button_frame, 
            text="💾 Save Settings", 
            command=self.save_settings,
            style='Modern.TButton'
        ).pack(side="left", padx=3)
        
        ttk.Button(
            button_frame, 
            text="📁 Load Settings", 
            command=self.load_settings,
            style='Modern.TButton'
        ).pack(side="left", padx=3)
        
        ttk.Button(
            button_frame, 
            text="🧹 Clear Log", 
            command=self.clear_log,
            style='Modern.TButton'
        ).pack(side="left", padx=3)
        
        # Right side - status
        status_frame = tk.Frame(control_content, bg=self.theme.colors['bg_primary'])
        status_frame.pack(side="right")
        
        self.status_badge = self.theme.create_status_badge(status_frame, "⏹️ Stopped", "danger")
        self.status_badge.pack()
    
    def setup_log_output(self, parent):
        """Setup the modern log output area"""
        log_card = self.theme.create_card_frame(parent, "📋 Activity Log")
        log_card.config(height=250)
        log_card.pack_propagate(False)
        log_card.pack(fill="x", expand=False, pady=(15, 0))
        
        # Log content
        log_content = tk.Frame(log_card, bg=self.theme.colors['bg_primary'])
        log_content.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        # Create custom styled text widget
        log_bg = '#2d3748' if self.theme.is_dark_mode else '#fafafa'
        self.log_text = tk.Text(
            log_content, 
            wrap=tk.WORD,
            bg=log_bg,
            fg=self.theme.colors['text_primary'],
            font=('Consolas', 10),
            relief='solid',
            bd=1,
            padx=10,
            pady=10,
            insertbackground=self.theme.colors['text_primary']
        )
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(log_content, orient="vertical", command=self.log_text.yview, 
                                 style='Modern.Vertical.TScrollbar')
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Pack with scrollbar
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)
            
    def toggle_monitoring(self):
        """Toggle between start and stop monitoring"""
        if not self.is_running:
            self.start_monitoring()
        else:
            self.stop_monitoring()
            
    def toggle_monitoring_mode(self, clipboard=False):
        """Toggle monitoring with specific mode preference"""
        was_running = self.is_running
        was_clipboard = self.settings['clipboard_mode'].get()
        
        # Update the setting to the requested mode
        self.settings['clipboard_mode'].set(clipboard)
        
        if was_running:
            self.stop_monitoring()
            # If we were running in a different mode, restart in the new mode
            if was_clipboard != clipboard:
                self.root.after(200, self.start_monitoring) # Small delay to ensure clean stop
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start the file monitoring process"""
        try:
            vault_path = self.settings['vault_path'].get()
            images_folder = self.settings['images_folder'].get()
            
            if not vault_path or not Path(vault_path).exists():
                messagebox.showerror("Error", "Please select a valid Obsidian vault path")
                return
                
            if not images_folder or not Path(images_folder).exists():
                messagebox.showerror("Error", "Please select a valid images folder")
                return
            
            # Check Pillow if JPG conversion is enabled
            if self.settings['convert_jpg'].get():
                try:
                    from PIL import Image
                except ImportError:
                    if not messagebox.askyesno("Warning", 
                        "Pillow library is required for JPG conversion but not installed.\n"
                        "Do you want to continue without JPG conversion?"):
                        return
                    self.settings['convert_jpg'].set(False)
            
            # Prepare options dictionary
            options = {key: var.get() for key, var in self.settings.items()}
            
            # Add note commands settings if enabled
            if self.settings['enable_note_commands'].get():
                options['note_commands_enabled'] = {key: var.get() for key, var in self.note_commands.items()}
            
            # Create handler and observer
            self.handler = ImageHandler(vault_path, self.settings['default_prefix'].get(), 
                                       options, log_callback=self.log_message,
                                       clipboard_callback=self.copy_to_clipboard)
            self.observer = Observer()
            self.observer.schedule(self.handler, images_folder, recursive=False)
            
            # Start monitoring in a separate thread
            self.observer.start()
            
            self.is_running = True
            self.start_button.config(text="⏹️ Stop Monitoring", style='Danger.TButton')
            self.status_badge.destroy()
            status_text = "▶️ Running (Clipboard)" if self.settings['clipboard_mode'].get() else "▶️ Running"
            self.status_badge = self.theme.create_status_badge(
                self.status_badge.master, status_text, "success"
            )
            self.status_badge.pack()
            self.log_message("🚀 Started monitoring " + images_folder)
            
            if self.settings['clipboard_mode'].get():
                self.log_message("📋 Clipboard Mode Active: Image codes will be copied to clipboard", "INFO")
            
            # Log the current override prefix status
            override_value = self.settings['override_prefix'].get().strip()
            if override_value:
                self.log_message(f"Override prefix is active: '{override_value}'", "INFO")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {str(e)}")
            self.log_message(f"Error: {str(e)}", "ERROR")
            
    def stop_monitoring(self):
        """Stop the file monitoring process"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            
        self.handler = None
        self.is_running = False
        self.start_button.config(text="🚀 Start Monitoring", style='Primary.TButton')
        self.status_badge.destroy()
        self.status_badge = self.theme.create_status_badge(
            self.status_badge.master, "⏹️ Stopped", "danger"
        )
        self.status_badge.pack()
        self.log_message("⏹️ Stopped monitoring")
        
    def log_message(self, message, level="INFO"):
        """Add a message to the log output with modern formatting"""
        timestamp = time.strftime("%H:%M:%S")
        
        # Color code by level
        level_colors = {
            "INFO": "#2563eb",
            "WARNING": "#f59e0b", 
            "ERROR": "#ef4444",
            "SUCCESS": "#10b981"
        }
        
        # Icons by level
        level_icons = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "SUCCESS": "✅"
        }
        
        icon = level_icons.get(level, "•")
        color = level_colors.get(level, "#64748b")
        
        # Insert with formatting
        self.log_text.insert(tk.END, f"[{timestamp}] {icon} {message}\n")
        self.log_text.see(tk.END)
        
    def clear_log(self):
        """Clear all log messages"""
        self.log_text.delete(1.0, tk.END)
        
    def save_settings(self):
        """Save current settings to file"""
        try:
            settings_dict = {key: var.get() for key, var in self.settings.items()}
            note_commands_dict = {key: var.get() for key, var in self.note_commands.items()}
            
            # Add theme setting
            settings_dict['dark_theme'] = self.theme.is_dark_mode
            
            success, message = SettingsManager.save_settings(settings_dict, note_commands_dict)
            
            self.log_message(message)
            if success:
                messagebox.showinfo("Success", "Settings saved to settings.json")
            else:
                messagebox.showerror("Error", message)
        except Exception as e:
            error_msg = f"Failed to save settings: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self.log_message(error_msg, "ERROR")
            
    def load_settings(self):
        """Load settings from file"""
        try:
            success, settings_dict, note_commands_dict, message = SettingsManager.load_settings()
            
            if success:
                # Check for theme setting and apply it first
                if 'dark_theme' in settings_dict and settings_dict['dark_theme'] != self.theme.is_dark_mode:
                    # Toggle theme if needed
                    if settings_dict['dark_theme']:
                        if not self.theme.is_dark_mode:
                            self.theme.toggle_theme()
                    else:
                        if self.theme.is_dark_mode:
                            self.theme.toggle_theme()
                
                # Update settings variables
                for key, value in settings_dict.items():
                    if key in self.settings and key != 'dark_theme':  # Skip dark_theme as it's handled above
                        self.settings[key].set(value)
                
                # Update note commands variables
                for key, value in note_commands_dict.items():
                    if key in self.note_commands:
                        self.note_commands[key].set(value)
                        
                self.log_message(message)
            else:
                self.log_message(message, "WARNING")
        except Exception as e:
            error_msg = f"Failed to load settings: {str(e)}"
            self.log_message(error_msg, "ERROR")


def main():
    """Main entry point of the application"""
    root = tk.Tk()
    app = ImageProcessorGUI(root)
    
    # Handle window closing
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("Quit", "Monitoring is still running. Do you want to stop and exit?"):
                app.stop_monitoring()
                app.stop_global_hotkey()
                root.destroy()
        else:
            app.stop_global_hotkey()
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
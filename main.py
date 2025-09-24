import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
from watchdog.observers import Observer

from image_handler import ImageHandler
from settings_manager import SettingsManager
from gui_tabs import MainSettingsTab, ImageProcessingTab, NoteProcessingTab, NoteCommandsTab


class ImageProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Obsidian Image Processor")
        self.root.geometry("1200x900")
        
        # Initialize settings
        self.settings = self._create_settings_variables()
        self.note_commands = self._create_note_command_variables()
        
        self.observer = None
        self.handler = None  # Keep reference to handler
        self.is_running = False
        
        self.setup_ui()
        self.load_settings()
        
        # Bind override prefix changes to update handler dynamically
        self.settings['override_prefix'].trace('w', self.on_override_prefix_change)
    
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
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=False, padx=5, pady=5)
        
        # Main Settings Tab
        main_tab = ttk.Frame(notebook)
        notebook.add(main_tab, text="Main Settings")
        MainSettingsTab(main_tab, self.settings)
        
        # Image Processing Tab
        image_tab = ttk.Frame(notebook)
        notebook.add(image_tab, text="Image Processing")
        ImageProcessingTab(image_tab, self.settings)
        
        # Note Processing Tab
        note_tab = ttk.Frame(notebook)
        notebook.add(note_tab, text="Note Processing")
        NoteProcessingTab(note_tab, self.settings)
        
        # Note Commands Tab
        commands_tab = ttk.Frame(notebook)
        notebook.add(commands_tab, text="Note Commands")
        NoteCommandsTab(commands_tab, self.settings, self.note_commands, self.log_message)
        
        # Control Panel at bottom
        self.setup_control_panel()
        
        # Log Output
        self.setup_log_output()
        
    def setup_control_panel(self):
        """Setup the control panel with buttons and status"""
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        self.start_button = ttk.Button(control_frame, text="Start Monitoring", command=self.toggle_monitoring)
        self.start_button.pack(side="left", padx=5)
        
        ttk.Button(control_frame, text="Save Settings", command=self.save_settings).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Load Settings", command=self.load_settings).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Clear Log", command=self.clear_log).pack(side="left", padx=5)
        
        self.status_label = ttk.Label(control_frame, text="Status: Stopped", foreground="red")
        self.status_label.pack(side="right", padx=5)
    
    def setup_log_output(self):
        """Setup the log output area"""
        log_frame = ttk.LabelFrame(self.root, text="Log Output")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
            
    def toggle_monitoring(self):
        """Toggle between start and stop monitoring"""
        if not self.is_running:
            self.start_monitoring()
        else:
            self.stop_monitoring()
            
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
                                       options, log_callback=self.log_message)
            self.observer = Observer()
            self.observer.schedule(self.handler, images_folder, recursive=False)
            
            # Start monitoring in a separate thread
            self.observer.start()
            
            self.is_running = True
            self.start_button.config(text="Stop Monitoring")
            self.status_label.config(text="Status: Running", foreground="green")
            self.log_message("Started monitoring " + images_folder)
            
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
        self.start_button.config(text="Start Monitoring")
        self.status_label.config(text="Status: Stopped", foreground="red")
        self.log_message("Stopped monitoring")
        
    def log_message(self, message, level="INFO"):
        """Add a message to the log output"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
    def clear_log(self):
        """Clear all log messages"""
        self.log_text.delete(1.0, tk.END)
        
    def save_settings(self):
        """Save current settings to file"""
        try:
            settings_dict = {key: var.get() for key, var in self.settings.items()}
            note_commands_dict = {key: var.get() for key, var in self.note_commands.items()}
            
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
                # Update settings variables
                for key, value in settings_dict.items():
                    if key in self.settings:
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
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
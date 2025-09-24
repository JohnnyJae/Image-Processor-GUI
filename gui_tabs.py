import tkinter as tk
from tkinter import ttk, filedialog


class MainSettingsTab:
    def __init__(self, parent, settings):
        self.settings = settings
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        # Vault Path
        vault_frame = ttk.LabelFrame(parent, text="Paths Configuration")
        vault_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(vault_frame, text="Obsidian Vault Path:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(vault_frame, textvariable=self.settings['vault_path'], width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(vault_frame, text="Browse", command=lambda: self.browse_folder('vault_path')).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(vault_frame, text="Images Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(vault_frame, textvariable=self.settings['images_folder'], width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(vault_frame, text="Browse", command=lambda: self.browse_folder('images_folder')).grid(row=1, column=2, padx=5, pady=5)
        
        # Prefix Settings Frame
        prefix_frame = ttk.LabelFrame(parent, text="Prefix Settings")
        prefix_frame.pack(fill="x", padx=10, pady=10)
        
        # Override prefix (highest priority)
        ttk.Label(prefix_frame, text="Override Prefix:", anchor="w", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        override_entry = ttk.Entry(prefix_frame, textvariable=self.settings['override_prefix'], width=40, font=("Arial", 9))
        override_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(prefix_frame, text="(Overrides all other prefixes when not empty)", 
                 font=("Arial", 8), foreground="red").grid(row=0, column=2, padx=5, pady=5)
        
        # Default prefix
        ttk.Label(prefix_frame, text="Default Prefix:", anchor="w").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(prefix_frame, textvariable=self.settings['default_prefix'], width=40).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(prefix_frame, text="(Used when no override or note commands)", 
                 font=("Arial", 8), foreground="gray").grid(row=1, column=2, padx=5, pady=5)
        
        # Basic Settings
        basic_frame = ttk.LabelFrame(parent, text="Basic Settings")
        basic_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(basic_frame, text="Cooldown (seconds):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Spinbox(basic_frame, from_=0.1, to=10.0, increment=0.1, textvariable=self.settings['cooldown'], width=10).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Processing Options
        process_frame = ttk.LabelFrame(parent, text="Processing Options")
        process_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Checkbutton(process_frame, text="Add image code to note", variable=self.settings['add_to_note']).pack(anchor="w", padx=5, pady=2)
        ttk.Checkbutton(process_frame, text="Auto-rename files", variable=self.settings['auto_rename']).pack(anchor="w", padx=5, pady=2)
        ttk.Checkbutton(process_frame, text="Auto-numbering", variable=self.settings['auto_numbering']).pack(anchor="w", padx=5, pady=2)
        
    def browse_folder(self, setting_key):
        folder = filedialog.askdirectory()
        if folder:
            self.settings[setting_key].set(folder)


class ImageProcessingTab:
    def __init__(self, parent, settings):
        self.settings = settings
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        # JPG Conversion Settings
        jpg_frame = ttk.LabelFrame(parent, text="JPG Conversion Settings")
        jpg_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Checkbutton(jpg_frame, text="Convert images to JPG", variable=self.settings['convert_jpg']).pack(anchor="w", padx=5, pady=5)
        
        quality_frame = ttk.Frame(jpg_frame)
        quality_frame.pack(fill="x", padx=20, pady=5)
        ttk.Label(quality_frame, text="JPG Quality:").pack(side="left", padx=5)
        quality_scale = ttk.Scale(quality_frame, from_=1, to=100, orient="horizontal", variable=self.settings['jpg_quality'], length=200)
        quality_scale.pack(side="left", padx=5)
        self.quality_label = ttk.Label(quality_frame, text="95%")
        self.quality_label.pack(side="left", padx=5)
        
        def update_quality_label(value):
            self.quality_label.config(text=f"{int(float(value))}%")
        quality_scale.config(command=update_quality_label)
        
        ttk.Checkbutton(jpg_frame, text="Optimize JPG files", variable=self.settings['optimize_jpg']).pack(anchor="w", padx=5, pady=5)
        ttk.Checkbutton(jpg_frame, text="Delete original after conversion", variable=self.settings['delete_original']).pack(anchor="w", padx=5, pady=5)
        
        color_frame = ttk.Frame(jpg_frame)
        color_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(color_frame, text="Background Color (for transparent images):").pack(side="left", padx=5)
        ttk.Entry(color_frame, textvariable=self.settings['bg_color'], width=15).pack(side="left", padx=5)
        ttk.Button(color_frame, text="Choose Color", command=self.choose_color).pack(side="left", padx=5)
        
    def choose_color(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(initialcolor=self.settings['bg_color'].get())
        if color[1]:
            self.settings['bg_color'].set(color[1])


class NoteProcessingTab:
    def __init__(self, parent, settings):
        self.settings = settings
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        # Note Search Settings
        search_frame = ttk.LabelFrame(parent, text="Note Search Settings")
        search_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Checkbutton(search_frame, text="Search notes recursively in subdirectories", variable=self.settings['recursive']).pack(anchor="w", padx=5, pady=5)
        ttk.Checkbutton(search_frame, text="Skip .excalidraw.md files", variable=self.settings['skip_excalidraw']).pack(anchor="w", padx=5, pady=5)
        
        # Image Format Settings
        format_frame = ttk.LabelFrame(parent, text="Image Format Settings")
        format_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(format_frame, text="Image Format:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(format_frame, textvariable=self.settings['image_format'], width=40).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(format_frame, text="(use {filename} as placeholder)", font=("Arial", 8), foreground="gray").grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(format_frame, text="Separator:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(format_frame, textvariable=self.settings['separator'], width=40).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(format_frame, text="(text to add before image code)", font=("Arial", 8), foreground="gray").grid(row=1, column=2, padx=5, pady=5)
        
        # Command Processing
        command_frame = ttk.LabelFrame(parent, text="Command Processing")
        command_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Checkbutton(command_frame, text="Clean commands from notes after processing", variable=self.settings['clean_commands']).pack(anchor="w", padx=5, pady=5)


class NoteCommandsTab:
    def __init__(self, parent, settings, note_commands, log_callback):
        self.settings = settings
        self.note_commands = note_commands
        self.log_callback = log_callback
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        # Enable/Disable Note Commands
        enable_frame = ttk.LabelFrame(parent, text="Note Commands")
        enable_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Checkbutton(enable_frame, text="Enable note commands", variable=self.settings['enable_note_commands'], 
                       command=self.toggle_note_commands).pack(anchor="w", padx=5, pady=5)
        
        # Prefix Priority Information
        priority_frame = ttk.LabelFrame(parent, text="Prefix Priority Order")
        priority_frame.pack(fill="x", padx=10, pady=10)
        
        priority_text = """Priority (highest to lowest):
1. Override Prefix (from Main Settings tab) - Always wins when not empty
2. Note Command Prefix ($prefix=) - From note content
3. Auto-detected Prefix - Most common prefix found in existing image codes
4. Default Prefix - Fallback option"""
        
        priority_label = tk.Text(priority_frame, height=6, width=70, font=("Arial", 9))
        priority_label.insert("1.0", priority_text)
        priority_label.config(state="disabled", background="#f0f0f0", relief="flat", borderwidth=0)
        priority_label.pack(padx=10, pady=10)
        
        # Individual Commands
        commands_frame = ttk.LabelFrame(parent, text="Available Commands (when enabled in notes)")
        commands_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a grid of checkboxes for each command
        commands_info = [
            ('$prefix=', 'Set custom prefix (overridden by Override Prefix)', 'prefix'),
            ('$quality=', 'Set JPG quality (1-100)', 'quality'),
            ('$format=', 'Set custom image format', 'format'),
            ('$separator=', 'Set custom separator', 'separator'),
            ('$convert=', 'Enable/disable JPG conversion', 'convert'),
            ('$rename=', 'Enable/disable auto-rename', 'rename'),
            ('$numbering=', 'Enable/disable auto-numbering', 'numbering'),
            ('$bg_color=', 'Set background color', 'bg_color'),
        ]
        
        ttk.Label(commands_frame, text="Command", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(commands_frame, text="Description", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(commands_frame, text="Enable", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, pady=5)
        
        for i, (cmd, desc, var_name) in enumerate(commands_info, start=1):
            ttk.Label(commands_frame, text=cmd, font=("Courier", 10)).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(commands_frame, text=desc).grid(row=i, column=1, sticky="w", padx=5, pady=2)
            cmd_checkbox = ttk.Checkbutton(commands_frame, variable=self.note_commands[var_name])
            cmd_checkbox.grid(row=i, column=2, padx=5, pady=2)
        
        # Example usage
        example_frame = ttk.LabelFrame(parent, text="Example Usage in Notes")
        example_frame.pack(fill="x", padx=10, pady=10)
        
        example_text = """$prefix=Screenshot
$quality=85
$format=![[{filename}]]
$separator=---
$convert=true
$rename=false

Note: Override Prefix will ignore the $prefix= command above."""
        
        example_label = tk.Text(example_frame, height=8, width=50, font=("Courier", 9))
        example_label.insert("1.0", example_text)
        example_label.config(state="disabled", background="#f0f0f0")
        example_label.pack(padx=10, pady=10)
        
    def toggle_note_commands(self):
        """Enable/disable individual note command checkboxes"""
        state = self.settings['enable_note_commands'].get()
        if self.log_callback:
            self.log_callback(f"Note commands {'enabled' if state else 'disabled'}")
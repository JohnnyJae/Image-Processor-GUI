import tkinter as tk
from tkinter import ttk, filedialog


class MainSettingsTab:
    def __init__(self, parent, settings, theme):
        self.settings = settings
        self.theme = theme
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        # Main scroll frame
        canvas = tk.Canvas(parent, bg=self.theme.colors['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.colors['bg_primary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        # Ensure the inner frame always matches the canvas width so grid columns fill correctly
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Horizontal container for paths and prefix settings
        horizontal_container = tk.Frame(scrollable_frame, bg=self.theme.colors['bg_primary'])
        horizontal_container.pack(fill="x", padx=5, pady=(6, 3))
        horizontal_container.grid_columnconfigure(0, weight=1, uniform="group1")
        horizontal_container.grid_columnconfigure(1, weight=1, uniform="group1")
        
        # Vault Path Card
        paths_card = self.theme.create_card_frame(horizontal_container, "🗂️ Paths Configuration")
        paths_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        paths_content = tk.Frame(paths_card, bg=self.theme.colors['bg_primary'])
        paths_content.pack(fill="x", padx=10, pady=(3, 6))
        
        # Vault path row
        vault_row = tk.Frame(paths_content, bg=self.theme.colors['bg_primary'])
        vault_row.pack(fill="x", pady=(0, 15))
        
        tk.Label(vault_row, text="Obsidian Vault Path:", 
                bg=self.theme.colors['bg_primary'], fg=self.theme.colors['text_primary'],
                font=('Segoe UI', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        
        vault_input_frame = tk.Frame(vault_row, bg=self.theme.colors['bg_primary'])
        vault_input_frame.pack(fill="x")
        
        vault_entry = ttk.Entry(vault_input_frame, textvariable=self.settings['vault_path'], 
                               font=('Segoe UI', 10), style='Modern.TEntry')
        vault_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ttk.Button(vault_input_frame, text="📁 Browse", 
                  command=lambda: self.browse_folder('vault_path'),
                  style='Modern.TButton').pack(side="right")
        
        # Images folder row
        images_row = tk.Frame(paths_content, bg=self.theme.colors['bg_primary'])
        images_row.pack(fill="x")
        
        tk.Label(images_row, text="Images Folder:", 
                bg=self.theme.colors['bg_primary'], fg=self.theme.colors['text_primary'],
                font=('Segoe UI', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        
        images_input_frame = tk.Frame(images_row, bg=self.theme.colors['bg_primary'])
        images_input_frame.pack(fill="x")
        
        images_entry = ttk.Entry(images_input_frame, textvariable=self.settings['images_folder'],
                                font=('Segoe UI', 10), style='Modern.TEntry')
        images_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ttk.Button(images_input_frame, text="📁 Browse",
                  command=lambda: self.browse_folder('images_folder'),
                  style='Modern.TButton').pack(side="right")
        
        # Prefix Settings Card
        prefix_card = self.theme.create_card_frame(horizontal_container, "🏷️ Prefix Settings")
        prefix_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        prefix_content = tk.Frame(prefix_card, bg=self.theme.colors['bg_primary'])
        prefix_content.pack(fill="x", padx=15, pady=(5, 10))
        
        # Automatic Prefix Toggle
        auto_prefix_frame = tk.Frame(prefix_content, bg='#e0f2fe', relief='solid', bd=1)
        auto_prefix_frame.pack(fill="x", pady=(0, 15))
        
        auto_prefix_inner = tk.Frame(auto_prefix_frame, bg='#e0f2fe')
        auto_prefix_inner.pack(fill="x", padx=15, pady=15)
        
        self.auto_prefix_checkbox = ttk.Checkbutton(
            auto_prefix_inner, 
            text="🤖 Automatic Prefix (from filename)", 
            variable=self.settings['automatic_prefix_enabled'],
            command=self.on_automatic_prefix_toggle,
            style='Modern.TCheckbutton'
        )
        self.auto_prefix_checkbox.pack(anchor="w", pady=(0, 8))
        
        # User prefix entry (shown when automatic is enabled)
        self.auto_prefix_user_frame = tk.Frame(auto_prefix_inner, bg='#e0f2fe')
        
        tk.Label(self.auto_prefix_user_frame, text="Game/User Prefix:", 
                bg='#e0f2fe', fg='#0277bd',
                font=('Segoe UI', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        
        ttk.Entry(self.auto_prefix_user_frame, textvariable=self.settings['automatic_prefix_user'],
                 font=('Segoe UI', 10), style='Modern.TEntry').pack(fill="x", pady=(0, 5))
        
        tk.Label(self.auto_prefix_user_frame, text="💡 Example: 'DyingLight' + 'Good Vibrations.md' → DyingLight-GoodVibrations_1.jpg",
                bg='#e0f2fe', fg='#0277bd',
                font=('Segoe UI', 9)).pack(anchor="w")
        
        # Override prefix (with conditional highlighting)
        self.override_frame = tk.Frame(prefix_content, bg='#fef3c7', relief='solid', bd=1)
        
        override_inner = tk.Frame(self.override_frame, bg='#fef3c7')
        override_inner.pack(fill="x", padx=15, pady=15)
        
        tk.Label(override_inner, text="🎯 Override Prefix (Highest Priority):", 
                bg='#fef3c7', fg='#92400e',
                font=('Segoe UI', 10, 'bold')).pack(anchor="w", pady=(0, 8))
        
        self.override_entry = ttk.Entry(override_inner, textvariable=self.settings['override_prefix'], 
                                      font=('Segoe UI', 11), style='Modern.TEntry')
        self.override_entry.pack(fill="x", pady=(0, 5))
        
        tk.Label(override_inner, text="⚠️ When set, this prefix overrides all other prefix sources",
                bg='#fef3c7', fg='#92400e',
                font=('Segoe UI', 9)).pack(anchor="w")
        
        # Default prefix
        self.default_row = tk.Frame(prefix_content, bg=self.theme.colors['bg_primary'])
        
        tk.Label(self.default_row, text="Default Prefix:", 
                bg=self.theme.colors['bg_primary'], fg=self.theme.colors['text_primary'],
                font=('Segoe UI', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        
        self.default_entry = ttk.Entry(self.default_row, textvariable=self.settings['default_prefix'],
                 font=('Segoe UI', 10), style='Modern.TEntry')
        self.default_entry.pack(fill="x", pady=(0, 5))
        
        tk.Label(self.default_row, text="Used as fallback when no override or note commands are present",
                bg=self.theme.colors['bg_primary'], fg=self.theme.colors['text_secondary'],
                font=('Segoe UI', 9)).pack(anchor="w")
        
        # Initial state setup
        self.on_automatic_prefix_toggle()
        
        # Horizontal container for basic and processing options
        options_container = tk.Frame(scrollable_frame, bg=self.theme.colors['bg_primary'])
        options_container.pack(fill="x", padx=5, pady=10)
        options_container.grid_columnconfigure(0, weight=1, uniform="group2")
        options_container.grid_columnconfigure(1, weight=1, uniform="group2")
        
        # Basic Settings Card
        basic_card = self.theme.create_card_frame(options_container, "⚙️ Basic Settings")
        basic_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        basic_content = tk.Frame(basic_card, bg=self.theme.colors['bg_primary'])
        basic_content.pack(fill="x", padx=5, pady=(3, 6))
        
        cooldown_row = tk.Frame(basic_content, bg=self.theme.colors['bg_primary'])
        cooldown_row.pack(fill="x", pady=(0, 5))
        
        tk.Label(cooldown_row, text="⏱️ Processing Cooldown (seconds):", 
                bg=self.theme.colors['bg_primary'], fg=self.theme.colors['text_primary'],
                font=('Segoe UI', 10, 'bold')).pack(anchor="w", pady=(0, 5))
        
        ttk.Spinbox(cooldown_row, from_=0.1, to=10.0, increment=0.1, 
                   textvariable=self.settings['cooldown'], width=5,
                   font=('Segoe UI', 10), style='Modern.TSpinbox').pack(anchor="w")
        
        # Processing Options Card
        options_card = self.theme.create_card_frame(options_container, "🔄 Processing Options")
        options_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        options_content = tk.Frame(options_card, bg=self.theme.colors['bg_primary'])
        options_content.pack(fill="x", padx=15, pady=(5, 10))
        
        ttk.Checkbutton(options_content, text="📝 Add image code to note", 
                       variable=self.settings['add_to_note'],
                       style='Modern.TCheckbutton').pack(anchor="w", pady=3)
        ttk.Checkbutton(options_content, text="📋 Clipboard Mode (Copy code instead of pasting)", 
                       variable=self.settings['clipboard_mode'],
                       style='Modern.TCheckbutton').pack(anchor="w", pady=3)
        ttk.Checkbutton(options_content, text="🏷️ Auto-rename files", 
                       variable=self.settings['auto_rename'],
                       style='Modern.TCheckbutton').pack(anchor="w", pady=3)
        ttk.Checkbutton(options_content, text="🔢 Auto-numbering", 
                       variable=self.settings['auto_numbering'],
                       style='Modern.TCheckbutton').pack(anchor="w", pady=3)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def browse_folder(self, setting_key):
        folder = filedialog.askdirectory()
        if folder:
            self.settings[setting_key].set(folder)
    
    def on_automatic_prefix_toggle(self):
        """Toggle UI elements based on automatic prefix setting"""
        automatic_enabled = self.settings['automatic_prefix_enabled'].get()
        
        if automatic_enabled:
            # Show automatic prefix user entry
            self.auto_prefix_user_frame.pack(fill="x", pady=(0, 8))
            
            # Hide/disable override and default prefix sections
            self.override_frame.pack_forget()
            self.default_row.pack_forget()
        else:
            # Hide automatic prefix user entry
            self.auto_prefix_user_frame.pack_forget()
            
            # Show override and default prefix sections
            self.override_frame.pack(fill="x", pady=(0, 15))
            self.default_row.pack(fill="x")


class ImageProcessingTab:
    def __init__(self, parent, settings, theme):
        self.settings = settings
        self.theme = theme
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        # Main scroll frame
        canvas = tk.Canvas(parent, bg=self.theme.colors['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.colors['bg_primary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        # Ensure the inner frame always matches the canvas width so grid columns fill correctly
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Horizontal container: left = JPG Conversion, right = Processing Options / Background
        horizontal_container = tk.Frame(scrollable_frame, bg=self.theme.colors['bg_primary'])
        horizontal_container.pack(fill="x", padx=5, pady=15)
        horizontal_container.grid_columnconfigure(0, weight=1, uniform="img_group")
        horizontal_container.grid_columnconfigure(1, weight=1, uniform="img_group")

        # JPG Conversion Settings Card (left)
        jpg_card = self.theme.create_card_frame(horizontal_container, "🖼️ JPG Conversion Settings")
        jpg_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        jpg_content = tk.Frame(jpg_card, bg=self.theme.colors['bg_primary'])
        jpg_content.pack(fill="x", padx=20, pady=(10, 20))

        ttk.Checkbutton(jpg_content, text="🔄 Convert images to JPG", 
                       variable=self.settings['convert_jpg'],
                       style='Modern.TCheckbutton').pack(anchor="w", pady=(0, 15))

        # Quality settings
        quality_frame = tk.Frame(jpg_content, bg=self.theme.colors['bg_primary'])
        quality_frame.pack(fill="x", pady=(0, 15))

        tk.Label(quality_frame, text="Quality Level:", 
                bg=self.theme.colors['bg_primary'], fg=self.theme.colors['text_primary'],
                font=('Segoe UI', 10, 'bold')).pack(anchor="w", pady=(0, 8))

        quality_control = tk.Frame(quality_frame, bg=self.theme.colors['bg_primary'])
        quality_control.pack(fill="x")

        quality_scale = ttk.Scale(quality_control, from_=1, to=100, orient="horizontal", 
                                 variable=self.settings['jpg_quality'], length=300,
                                 style='Modern.Horizontal.TScale')
        quality_scale.pack(side="left", padx=(0, 15))

        self.quality_label = tk.Label(quality_control, text="95%", 
                                     bg=self.theme.colors['bg_primary'], fg=self.theme.colors['text_primary'],
                                     font=('Segoe UI', 12, 'bold'))
        self.quality_label.pack(side="left")

        def update_quality_label(value):
            self.quality_label.config(text=f"{int(float(value))}%")
        quality_scale.config(command=update_quality_label)

        # Processing Options Card (right)
        options_card = self.theme.create_card_frame(horizontal_container, "🔄 Processing Options")
        options_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        options_content = tk.Frame(options_card, bg=self.theme.colors['bg_primary'])
        options_content.pack(fill="x", padx=15, pady=(10, 15))

        ttk.Checkbutton(options_content, text="⚡ Optimize JPG files", 
                       variable=self.settings['optimize_jpg'],
                       style='Modern.TCheckbutton').pack(anchor="w", pady=3)
        ttk.Checkbutton(options_content, text="🗑️ Delete original after conversion", 
                       variable=self.settings['delete_original'],
                       style='Modern.TCheckbutton').pack(anchor="w", pady=3)

        # Background color settings
        color_frame = tk.Frame(options_content, bg=self.theme.colors['bg_primary'])
        color_frame.pack(fill="x", pady=(10, 0))

        tk.Label(color_frame, text="Background Color (for transparent images):", 
                bg=self.theme.colors['bg_primary'], fg=self.theme.colors['text_primary'],
                font=('Segoe UI', 10, 'bold')).pack(anchor="w", pady=(0, 8))

        color_input = tk.Frame(color_frame, bg=self.theme.colors['bg_primary'])
        color_input.pack(fill="x")

        ttk.Entry(color_input, textvariable=self.settings['bg_color'], width=20,
                 font=('Segoe UI', 10), style='Modern.TEntry').pack(side="left", padx=(0, 10))

        ttk.Button(color_input, text="🎨 Choose Color", command=self.choose_color,
                  style='Modern.TButton').pack(side="left")
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def choose_color(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(initialcolor=self.settings['bg_color'].get())
        if color[1]:
            self.settings['bg_color'].set(color[1])


class NoteProcessingTab:
    def __init__(self, parent, settings, theme):
        self.settings = settings
        self.theme = theme
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        # Main scroll frame
        canvas = tk.Canvas(parent, bg=self.theme.colors['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.colors['bg_primary'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        # Horizontal container: Note Search (left) and Image Format (right)
        horizontal_top = tk.Frame(scrollable_frame, bg=self.theme.colors['bg_primary'])
        horizontal_top.pack(fill="x", padx=5, pady=10)
        horizontal_top.grid_columnconfigure(0, weight=1, uniform="note_group")
        horizontal_top.grid_columnconfigure(1, weight=1, uniform="note_group")

        # Note Search Settings Card (left)
        search_card = self.theme.create_card_frame(horizontal_top, "🔍 Note Search Settings")
        search_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))

        search_content = tk.Frame(search_card, bg=self.theme.colors['bg_primary'])
        search_content.pack(fill="x", padx=20, pady=(10, 20))

        ttk.Checkbutton(search_content, text="Search notes recursively in subdirectories", 
                       variable=self.settings['recursive'],
                       style='Modern.TCheckbutton').pack(anchor="w", pady=3)
        ttk.Checkbutton(search_content, text="Skip .excalidraw.md files", 
                       variable=self.settings['skip_excalidraw'],
                       style='Modern.TCheckbutton').pack(anchor="w", pady=3)

        # Image Format Settings Card (right)
        format_card = self.theme.create_card_frame(horizontal_top, "🖼️ Image Format Settings")
        format_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 5))

        format_content = tk.Frame(format_card, bg=self.theme.colors['bg_primary'])
        format_content.pack(fill="x", padx=20, pady=(10, 20))

        tk.Label(format_content, text="Image Format:", 
                 bg=self.theme.colors['bg_primary'], fg=self.theme.colors['text_primary'],
                 font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=(0, 5))

        ttk.Entry(format_content, textvariable=self.settings['image_format'], width=40,
                 font=('Segoe UI', 10), style='Modern.TEntry').grid(row=0, column=1, padx=5, pady=5)

        tk.Label(format_content, text="(use {filename} as placeholder)", 
                 font=("Segoe UI", 9), fg="gray", bg=self.theme.colors['bg_primary']).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(format_content, text="Separator:", 
                 bg=self.theme.colors['bg_primary'], fg=self.theme.colors['text_primary'],
                 font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky="w", pady=(0, 5))

        ttk.Entry(format_content, textvariable=self.settings['separator'], width=40,
                 font=('Segoe UI', 10), style='Modern.TEntry').grid(row=1, column=1, padx=5, pady=5)

        tk.Label(format_content, text="(text to add before image code)", 
                 font=("Segoe UI", 9), fg="gray", bg=self.theme.colors['bg_primary']).grid(row=1, column=2, padx=5, pady=5)

        # Horizontal container: Command Processing (left) and Additional (right)
        horizontal_bottom = tk.Frame(scrollable_frame, bg=self.theme.colors['bg_primary'])
        horizontal_bottom.pack(fill="x", padx=5, pady=(5, 10))
        horizontal_bottom.grid_columnconfigure(0, weight=1, uniform="note_group")
        horizontal_bottom.grid_columnconfigure(1, weight=1, uniform="note_group")

        # Command Processing Card (left)
        command_card = self.theme.create_card_frame(horizontal_bottom, "⚙️ Command Processing")
        command_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        command_content = tk.Frame(command_card, bg=self.theme.colors['bg_primary'])
        command_content.pack(fill="x", padx=20, pady=(10, 20))

        ttk.Checkbutton(command_content, text="Clean commands from notes after processing", 
                       variable=self.settings['clean_commands'],
                       style='Modern.TCheckbutton').pack(anchor="w", pady=3)

        # Additional Settings Card (right) - placeholder to keep two-column layout
        add_card = self.theme.create_card_frame(horizontal_bottom, "🧩 Additional Settings")
        add_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        add_content = tk.Frame(add_card, bg=self.theme.colors['bg_primary'])
        add_content.pack(fill="x", padx=20, pady=(10, 20))
        ttk.Label(add_content, text="No additional settings", background=self.theme.colors['bg_primary']).pack(anchor="w")

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class NoteCommandsTab:
    def __init__(self, parent, settings, note_commands, log_callback, theme):
        self.settings = settings
        self.note_commands = note_commands
        self.log_callback = log_callback
        self.theme = theme
        self.setup_ui(parent)
    
    def setup_ui(self, parent):
        # Main scroll frame
        canvas = tk.Canvas(parent, bg=self.theme.colors['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.colors['bg_primary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        # Ensure the inner frame always matches the canvas width so grid columns fill correctly
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width))        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Two-row horizontal layout: top row = enable + priority, bottom row = commands + example
        top_row = tk.Frame(scrollable_frame, bg=self.theme.colors['bg_primary'])
        top_row.pack(fill="x", padx=5, pady=(10, 5))
        top_row.grid_columnconfigure(0, weight=1, uniform="cmd_group")
        top_row.grid_columnconfigure(1, weight=1, uniform="cmd_group")

        # Enable/Disable Note Commands Card (left)
        enable_card = self.theme.create_card_frame(top_row, "🛠️ Note Commands")
        enable_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        enable_content = tk.Frame(enable_card, bg=self.theme.colors['bg_primary'])
        enable_content.pack(fill="x", padx=20, pady=(10, 20))

        ttk.Checkbutton(enable_content, text="Enable note commands", 
                       variable=self.settings['enable_note_commands'], 
                       command=self.toggle_note_commands,
                       style='Modern.TCheckbutton').pack(anchor="w", pady=3)

        # Prefix Priority Information Card (right)
        priority_card = self.theme.create_card_frame(top_row, "📊 Prefix Priority Order")
        priority_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        priority_content = tk.Frame(priority_card, bg=self.theme.colors['bg_primary'])
        priority_content.pack(fill="x", padx=20, pady=(10, 20))

        priority_text = """Priority (highest to lowest):
1. Override Prefix (from Main Settings tab) - Always wins when not empty
2. Note Command Prefix ($prefix=) - From note content
3. Auto-detected Prefix - Most common prefix found in existing image codes
4. Default Prefix - Fallback option"""

        priority_label = tk.Text(priority_content, height=6, width=70, font=("Segoe UI", 9))
        priority_label.insert("1.0", priority_text)
        priority_label.config(state="disabled", background="#f0f0f0", relief="flat", borderwidth=0)
        priority_label.pack(padx=10, pady=10)

        # Bottom row: Available Commands (left) and Example Usage (right)
        bottom_row = tk.Frame(scrollable_frame, bg=self.theme.colors['bg_primary'])
        bottom_row.pack(fill="both", expand=True, padx=5, pady=(5, 10))
        bottom_row.grid_columnconfigure(0, weight=1, uniform="cmd_group")
        bottom_row.grid_columnconfigure(1, weight=1, uniform="cmd_group")

        # Individual Commands Card (left)
        commands_card = self.theme.create_card_frame(bottom_row, "📋 Available Commands")
        commands_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        commands_content = tk.Frame(commands_card, bg=self.theme.colors['bg_primary'])
        commands_content.pack(fill="x", padx=20, pady=(10, 20))

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

        ttk.Label(commands_content, text="Command", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(commands_content, text="Description", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(commands_content, text="Enable", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=5, pady=5)

        for i, (cmd, desc, var_name) in enumerate(commands_info, start=1):
            ttk.Label(commands_content, text=cmd, font=("Courier", 10)).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(commands_content, text=desc).grid(row=i, column=1, sticky="w", padx=5, pady=2)
            cmd_checkbox = ttk.Checkbutton(commands_content, variable=self.note_commands[var_name])
            cmd_checkbox.grid(row=i, column=2, padx=5, pady=2)

        # Example usage (right)
        example_card = self.theme.create_card_frame(bottom_row, "💡 Example Usage in Notes")
        example_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        example_content = tk.Frame(example_card, bg=self.theme.colors['bg_primary'])
        example_content.pack(fill="x", padx=20, pady=(10, 20))

        example_text = """$prefix=Screenshot
$quality=85
$format=![[{filename}]]
$separator=---
$convert=true
$rename=false

Note: Override Prefix will ignore the $prefix= command above."""

        example_label = tk.Text(example_content, height=8, width=50, font=("Courier", 9))
        example_label.insert("1.0", example_text)
        example_label.config(state="disabled", background="#f0f0f0")
        example_label.pack(padx=10, pady=10)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def toggle_note_commands(self):
        """Enable/disable individual note command checkboxes"""
        state = self.settings['enable_note_commands'].get()
        if self.log_callback:
            self.log_callback(f"Note commands {'enabled' if state else 'disabled'}")
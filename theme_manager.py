import tkinter as tk
from tkinter import ttk


class ModernThemeManager:
    def __init__(self):
        self.is_dark_mode = False
        self.theme_change_callbacks = []
        
        # Light theme colors
        self.light_colors = {
            'primary': '#2563eb',      # Blue
            'primary_dark': '#1d4ed8',
            'secondary': '#64748b',    # Slate gray
            'success': '#10b981',      # Green
            'danger': '#ef4444',       # Red
            'warning': '#f59e0b',      # Amber
            'bg_primary': '#ffffff',   # White
            'bg_secondary': '#f8fafc', # Light gray
            'bg_tertiary': '#e2e8f0',  # Medium gray
            'text_primary': '#0f172a', # Dark slate
            'text_secondary': '#64748b', # Medium slate
            'border': '#e2e8f0',       # Light border
            'accent': '#8b5cf6',       # Purple
        }
        
        # Dark theme colors
        self.dark_colors = {
            'primary': '#3b82f6',      # Brighter blue for dark theme
            'primary_dark': '#2563eb',
            'secondary': '#94a3b8',    # Lighter slate gray
            'success': '#22c55e',      # Brighter green
            'danger': '#f87171',       # Lighter red
            'warning': '#fbbf24',      # Brighter amber
            'bg_primary': '#1e293b',   # Dark slate
            'bg_secondary': '#0f172a', # Very dark slate
            'bg_tertiary': '#334155',  # Medium dark slate
            'text_primary': '#f8fafc', # Light text
            'text_secondary': '#cbd5e1', # Medium light text
            'border': '#475569',       # Dark border
            'accent': '#a78bfa',       # Lighter purple
        }
        
        # Start with light theme
        self.colors = self.light_colors.copy()
        
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.is_dark_mode = not self.is_dark_mode
        self.colors = self.dark_colors.copy() if self.is_dark_mode else self.light_colors.copy()
        
        # Trigger all registered callbacks
        for callback in self.theme_change_callbacks:
            callback()
    
    def register_theme_change_callback(self, callback):
        """Register a callback to be called when theme changes"""
        self.theme_change_callbacks.append(callback)
    
    def get_theme_name(self):
        """Get the current theme name"""
        return "Dark" if self.is_dark_mode else "Light"
        
    def apply_modern_theme(self, root, style=None):
        """Apply modern theme to the application"""
        if style is None:
            style = ttk.Style()
        
        # Configure the theme
        style.theme_use('clam')
        
        # Modern button styles
        style.configure(
            'Modern.TButton',
            padding=(8, 6),
            font=('Segoe UI', 9),
            focuscolor='none',
            borderwidth=1,
            relief='solid'
        )
        
        style.map(
            'Modern.TButton',
            background=[
                ('active', self.colors['primary']),
                ('pressed', self.colors['primary_dark']),
                ('!active', self.colors['primary'])
            ],
            foreground=[('!active', 'white'), ('active', 'white')],
            relief=[('!active', 'flat'), ('active', 'flat')],
            bordercolor=[('!active', self.colors['border'])]
        )
        
        # Theme toggle button style
        style.configure(
            'Theme.TButton',
            padding=(8, 6),
            font=('Segoe UI', 9),
            focuscolor='none',
            borderwidth=1,
            relief='solid'
        )
        
        style.map(
            'Theme.TButton',
            background=[
                ('active', self.colors['accent']),
                ('pressed', self.colors['secondary']),
                ('!active', self.colors['bg_tertiary'])
            ],
            foreground=[
                ('active', 'white'),
                ('pressed', 'white'),
                ('!active', self.colors['text_primary'])
            ],
            relief=[('!active', 'flat'), ('active', 'flat')],
            bordercolor=[('!active', self.colors['border'])]
        )
        
        # Primary button style
        style.configure(
            'Primary.TButton',
            padding=(10, 8),
            font=('Segoe UI', 9, 'bold'),
            focuscolor='none',
        )
        
        style.map(
            'Primary.TButton',
            background=[
                ('active', self.colors['success']),
                ('pressed', '#059669'),
                ('!active', self.colors['success'])
            ],
            foreground=[('!active', 'white'), ('active', 'white')],
            relief=[('!active', 'flat'), ('active', 'flat')]
        )
        
        # Danger button style
        style.configure(
            'Danger.TButton',
            padding=(10, 8),
            font=('Segoe UI', 9, 'bold'),
            focuscolor='none',
        )
        
        style.map(
            'Danger.TButton',
            background=[
                ('active', '#dc2626'),
                ('pressed', '#b91c1c'),
                ('!active', self.colors['danger'])
            ],
            foreground=[('!active', 'white'), ('active', 'white')],
            relief=[('!active', 'flat'), ('active', 'flat')]
        )
        
        # Modern frame styles
        style.configure(
            'Modern.TLabelFrame',
            background=self.colors['bg_primary'],
            borderwidth=1,
            relief='solid',
            labelmargins=(10, 5, 10, 5)
        )
        
        style.configure(
            'Modern.TLabelFrame.Label',
            background=self.colors['bg_primary'],
            foreground=self.colors['text_primary'],
            font=('Segoe UI', 11, 'bold')
        )
        
        # Modern entry styles
        style.configure(
            'Modern.TEntry',
            fieldbackground=self.colors['bg_primary'],
            borderwidth=1,
            relief='solid',
            padding=(8, 6),
            font=('Segoe UI', 10),
            foreground=self.colors['text_primary'],
            insertcolor=self.colors['text_primary']
        )
        
        style.map(
            'Modern.TEntry',
            bordercolor=[('focus', self.colors['primary'])]
        )
        
        # Modern spinbox styles
        style.configure(
            'Modern.TSpinbox',
            fieldbackground=self.colors['bg_primary'],
            borderwidth=1,
            relief='solid',
            padding=(8, 6),
            font=('Segoe UI', 10),
            foreground=self.colors['text_primary'],
            insertcolor=self.colors['text_primary']
        )
        
        style.map(
            'Modern.TSpinbox',
            bordercolor=[('focus', self.colors['primary'])]
        )
        
        # Modern scale styles
        style.configure(
            'Modern.Horizontal.TScale',
            background=self.colors['bg_primary'],
            troughcolor=self.colors['bg_tertiary'],
            sliderlength=20,
            borderwidth=0,
            sliderrelief='flat'
        )
        
        style.map(
            'Modern.Horizontal.TScale',
            background=[('active', self.colors['primary'])]
        )
        
        # Modern notebook styles
        style.configure(
            'Modern.TNotebook',
            background=self.colors['bg_secondary'],
            borderwidth=0,
            tabmargins=(0, 0, 0, 0)
        )
        
        style.configure(
            'Modern.TNotebook.Tab',
            padding=(20, 12),
            font=('Segoe UI', 10),
            focuscolor='none'
        )
        
        style.map(
            'Modern.TNotebook.Tab',
            background=[
                ('selected', self.colors['bg_primary']),
                ('!selected', self.colors['bg_tertiary'])
            ],
            foreground=[
                ('selected', self.colors['text_primary']),
                ('!selected', self.colors['text_secondary'])
            ],
            expand=[('selected', (0, 0, 0, 2))]
        )
        
        # Modern checkbutton styles
        style.configure(
            'Modern.TCheckbutton',
            background=self.colors['bg_primary'],
            foreground=self.colors['text_primary'],
            font=('Segoe UI', 10),
            focuscolor='none'
        )
        
        style.map(
            'Modern.TCheckbutton',
            background=[('active', self.colors['bg_primary'])],
            foreground=[('active', self.colors['text_primary'])]
        )
        
        # Modern scrollbar styles
        style.configure(
            'Modern.Vertical.TScrollbar',
            background=self.colors['bg_tertiary'],
            troughcolor=self.colors['bg_secondary'],
            borderwidth=0,
            arrowcolor=self.colors['text_secondary'],
            darkcolor=self.colors['bg_tertiary'],
            lightcolor=self.colors['bg_tertiary']
        )
        
        # Modern label styles
        style.configure(
            'Title.TLabel',
            background=self.colors['bg_primary'],
            foreground=self.colors['text_primary'],
            font=('Segoe UI', 12, 'bold')
        )
        
        style.configure(
            'Subtitle.TLabel',
            background=self.colors['bg_primary'],
            foreground=self.colors['text_secondary'],
            font=('Segoe UI', 10)
        )
        
        # Configure root window
        root.configure(bg=self.colors['bg_secondary'])
        
        return style
        
    def create_card_frame(self, parent, title=None, **kwargs):
        """Create a modern card-like frame"""
        # Set default border color if not specified
        border_color = kwargs.pop('highlightbackground', self.colors['border'])
        
        card = tk.Frame(parent, bg=self.colors['bg_primary'], relief='solid', bd=1, 
                       highlightbackground=border_color, highlightthickness=1, **kwargs)
        
        if title:
            title_frame = tk.Frame(card, bg=self.colors['bg_primary'], height=40)
            title_frame.pack(fill='x', padx=15, pady=(15, 0))
            title_frame.pack_propagate(False)
            
            title_label = tk.Label(
                title_frame, 
                text=title, 
                bg=self.colors['bg_primary'],
                fg=self.colors['text_primary'],
                font=('Segoe UI', 12, 'bold'),
                anchor='w'
            )
            title_label.pack(fill='both', expand=True)
            
        return card
        
    def create_status_badge(self, parent, text, status_type="info"):
        """Create a modern status badge"""
        colors_map = {
            'success': (self.colors['success'], 'white'),
            'danger': (self.colors['danger'], 'white'),
            'warning': (self.colors['warning'], 'white'),
            'info': (self.colors['primary'], 'white')
        }
        
        bg_color, fg_color = colors_map.get(status_type, colors_map['info'])
        
        badge = tk.Label(
            parent,
            text=text,
            bg=bg_color,
            fg=fg_color,
            font=('Segoe UI', 9, 'bold'),
            padx=8,
            pady=4
        )
        return badge
    
    def refresh_widget_colors(self, widget):
        """Recursively refresh colors for all widgets"""
        try:
            widget_class = widget.winfo_class()

            # Frames: use primary bg by default, but preserve special secondary/tertiary frames
            if widget_class == 'Frame':
                try:
                    current_bg = widget.cget('bg')
                except Exception:
                    current_bg = None

                if current_bg in ['#f8fafc', '#0f172a']:  # previously secondary
                    widget.configure(bg=self.colors['bg_secondary'])
                elif current_bg in ['#e2e8f0', '#334155']:  # previously tertiary
                    widget.configure(bg=self.colors['bg_tertiary'])
                else:
                    widget.configure(bg=self.colors['bg_primary'])

            elif widget_class == 'Label':
                # prefer to blend with parent background
                try:
                    parent_bg = widget.master.cget('bg')
                except Exception:
                    parent_bg = self.colors['bg_primary']
                widget.configure(bg=parent_bg, fg=self.colors['text_primary'])

            elif widget_class == 'Canvas':
                widget.configure(bg=self.colors['bg_primary'], highlightcolor=self.colors['border'])

            elif widget_class == 'Text':
                # Heuristic: treat log-like text specially if it already uses a dark/light log BG
                try:
                    name = str(widget)
                except Exception:
                    name = ''
                if 'log' in name.lower():
                    bg_color = '#2d3748' if self.is_dark_mode else '#fafafa'
                    widget.configure(bg=bg_color, fg=self.colors['text_primary'],
                                     insertbackground=self.colors['text_primary'])
                else:
                    widget.configure(bg=self.colors['bg_primary'], fg=self.colors['text_primary'],
                                     insertbackground=self.colors['text_primary'])

            elif widget_class == 'Toplevel':
                widget.configure(bg=self.colors['bg_secondary'])

            # Recursively update children
            for child in widget.winfo_children():
                self.refresh_widget_colors(child)

        except tk.TclError:
            # Widget might have been destroyed, skip
            pass

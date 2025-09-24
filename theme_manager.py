import tkinter as tk
from tkinter import ttk


class ModernThemeManager:
    def __init__(self):
        self.colors = {
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
        
    def apply_modern_theme(self, root):
        """Apply modern theme to the application"""
        style = ttk.Style()
        
        # Configure the theme
        style.theme_use('clam')
        
        # Modern button styles
        style.configure(
            'Modern.TButton',
            padding=(8, 6),
            font=('Segoe UI', 9),
            focuscolor='none',
        )
        
        style.map(
            'Modern.TButton',
            background=[
                ('active', self.colors['primary']),
                ('pressed', self.colors['primary_dark']),
                ('!active', self.colors['primary'])
            ],
            foreground=[('!active', 'white'), ('active', 'white')],
            relief=[('!active', 'flat'), ('active', 'flat')]
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
            font=('Segoe UI', 10)
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
        
    def create_card_frame(self, parent, title=None, **kwargs):
        """Create a modern card-like frame"""
        card = tk.Frame(parent, bg=self.colors['bg_primary'], relief='solid', bd=1, **kwargs)
        
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

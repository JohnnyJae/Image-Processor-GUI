import os
import re
import time
import logging
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import mimetypes
import json

class ImageHandler(FileSystemEventHandler):
    def __init__(self, obsidian_vault_path, default_prefix, options, log_callback=None):
        self.obsidian_vault_path = Path(obsidian_vault_path)
        self.default_prefix = default_prefix
        self.options = options
        self.last_processed_time = 0
        self.cooldown_seconds = options.get('cooldown', 2.0)
        self.log_callback = log_callback
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def log(self, message, level="INFO"):
        """Custom log method that sends to GUI"""
        if self.log_callback:
            self.log_callback(f"[{level}] {message}")
        self.logger.log(getattr(logging, level), message)
        
    def on_created(self, event):
        if event.is_directory:
            return
            
        # Check cooldown
        current_time = time.time()
        if current_time - self.last_processed_time < self.cooldown_seconds:
            self.log(f"Cooldown active, ignoring {event.src_path}", "INFO")
            return
            
        file_path = Path(event.src_path)
        
        # Check if it's an image file
        if not self.is_image_file(file_path):
            return
            
        try:
            self.process_image(file_path)
            self.last_processed_time = current_time
        except Exception as e:
            self.log(f"Error processing {file_path}: {str(e)}", "ERROR")
    
    def is_image_file(self, file_path):
        """Check if the file is an image based on MIME type"""
        try:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            return mime_type and mime_type.startswith('image/')
        except:
            return False
    
    def convert_to_jpg(self, image_path, note_commands=None):
        """Convert image to JPG format if it's not already JPG"""
        # Check if conversion is disabled globally or by note command
        convert_enabled = self.options.get('convert_jpg', True)
        if note_commands and 'convert' in note_commands:
            convert_enabled = note_commands['convert']
            
        if not convert_enabled:
            self.log(f"JPG conversion disabled, skipping {image_path.name}", "DEBUG")
            return image_path
            
        try:
            # Import here to avoid dependency if conversion is disabled
            from PIL import Image
            
            # Check if already JPG
            if image_path.suffix.lower() in ['.jpg', '.jpeg']:
                self.log(f"Image {image_path.name} is already JPG format", "INFO")
                return image_path
            
            self.log(f"Converting {image_path.name} to JPG format", "INFO")
            
            # Get quality from note commands or use default
            quality = note_commands.get('quality', self.options.get('jpg_quality', 95)) if note_commands else self.options.get('jpg_quality', 95)
            bg_color = note_commands.get('bg_color', self.options.get('bg_color', '#FFFFFF')) if note_commands else self.options.get('bg_color', '#FFFFFF')
            
            # Ensure bg_color starts with # for hex colors
            if not bg_color.startswith('#'):
                bg_color = '#' + bg_color
            
            # Open the image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for PNG with transparency, etc.)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create a background with specified color
                    try:
                        bg_rgb = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))
                    except ValueError:
                        bg_rgb = (255, 255, 255)  # Default to white if color parsing fails
                        self.log(f"Invalid background color {bg_color}, using white", "WARNING")
                    
                    background = Image.new('RGB', img.size, bg_rgb)
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create new filename with .jpg extension
                jpg_path = image_path.with_suffix('.jpg')
                
                # Save as JPG with specified quality
                img.save(jpg_path, 'JPEG', quality=quality, optimize=self.options.get('optimize_jpg', True))
                
                self.log(f"Saved converted image as {jpg_path.name} (quality: {quality}%)", "INFO")
            
            # Delete the original file if requested
            if self.options.get('delete_original', True):
                try:
                    image_path.unlink()
                    self.log(f"Deleted original file {image_path.name}", "INFO")
                except Exception as e:
                    self.log(f"Could not delete original file {image_path.name}: {str(e)}", "WARNING")
            
            return jpg_path
            
        except ImportError:
            self.log("Pillow library is required for JPG conversion but not installed", "ERROR")
            return image_path
        except Exception as e:
            self.log(f"Error converting {image_path.name} to JPG: {str(e)}", "ERROR")
            return image_path
    
    def get_last_modified_note(self):
        """Find the most recently modified .md file in the vault"""
        try:
            # Search for all .md files in the vault
            md_files = []
            search_path = self.obsidian_vault_path
            
            if self.options.get('recursive', True):
                pattern = '**/*.md'
            else:
                pattern = '*.md'
                
            for md_file in search_path.glob(pattern):
                # Skip .excalidraw.md files if requested
                if self.options.get('skip_excalidraw', True) and md_file.name.endswith('.excalidraw.md'):
                    continue
                # Double check the file extension
                if md_file.suffix.lower() == '.md':
                    md_files.append(md_file)
            
            if not md_files:
                raise Exception(f"No markdown (.md) files found in vault")
            
            self.log(f"Found {len(md_files)} markdown files in vault", "INFO")
            
            # Sort by modification time, most recent first
            latest_note = max(md_files, key=lambda x: x.stat().st_mtime)
            self.log(f"Using most recently modified note: {latest_note}", "INFO")
            return latest_note
        except Exception as e:
            self.log(f"Error finding last modified markdown note: {str(e)}", "ERROR")
            raise
    
    def parse_note_commands(self, content):
        """Parse special commands from the note content"""
        commands = {}
        
        # Command patterns - case insensitive
        command_patterns = {
            'prefix': r'\$pre(?:fix)?=([^\s\n]+)',
            'quality': r'\$quality=(\d+)',
            'format': r'\$format=([^\n]+)',
            'separator': r'\$sep(?:arator)?=([^\n]*)',
            'convert': r'\$convert=(true|false|on|off|yes|no)',
            'rename': r'\$rename=(true|false|on|off|yes|no)',
            'numbering': r'\$num(?:bering)?=(true|false|on|off|yes|no)',
            'bg_color': r'\$bg(?:_?color)?=([#\w]+)',
        }
        
        for command, pattern in command_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                value = matches[-1]  # Use the last occurrence if multiple
                
                # Convert boolean-like values
                if command in ['convert', 'rename', 'numbering']:
                    value = value.lower() in ['true', 'on', 'yes', '1']
                elif command == 'quality':
                    try:
                        value = max(1, min(100, int(value)))
                    except ValueError:
                        continue
                
                commands[command] = value
                self.log(f"Found note command: {command} = {value}", "INFO")
        
        return commands

    def extract_prefix_and_highest_number(self, content, note_commands=None):
        """Extract prefix and find highest number from existing image codes"""
        if not self.options.get('auto_numbering', True) and not (note_commands and note_commands.get('numbering')):
            # Check for temporary prefix override
            prefix = note_commands.get('prefix', self.default_prefix) if note_commands else self.default_prefix
            return prefix, 0
            
        # Use prefix from note commands if available
        target_prefix = note_commands.get('prefix', self.default_prefix) if note_commands else self.default_prefix
        
        # Pattern to match [[File:Prefix_Number.Extension]] with optional captions and formatting
        pattern = r'\[\[File:([^_]+)_(\d+)\.[^|\]]+(?:\|[^\]]+)?\]\]'
        matches = re.findall(pattern, content)
        
        if not matches:
            return target_prefix, 0
        
        # If we have a specific prefix from commands, only look for that prefix
        if note_commands and 'prefix' in note_commands:
            target_numbers = []
            for prefix, number in matches:
                if prefix == target_prefix:
                    target_numbers.append(int(number))
            
            highest_number = max(target_numbers) if target_numbers else 0
            self.log(f"Using command prefix: {target_prefix}, highest number: {highest_number}", "INFO")
            return target_prefix, highest_number
        
        # Original logic for automatic prefix detection
        prefix_counts = {}
        prefix_numbers = {}
        
        for prefix, number in matches:
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
            if prefix not in prefix_numbers:
                prefix_numbers[prefix] = []
            prefix_numbers[prefix].append(int(number))
        
        # Use the most common prefix
        most_common_prefix = max(prefix_counts.keys(), key=lambda x: prefix_counts[x])
        highest_number = max(prefix_numbers[most_common_prefix]) if prefix_numbers[most_common_prefix] else 0
        
        self.log(f"Extracted prefix: {most_common_prefix}, highest number: {highest_number}", "INFO")
        return most_common_prefix, highest_number
    
    def process_image(self, original_path):
        """Main processing function"""
        self.log(f"Processing new image: {original_path}", "INFO")
        
        if not self.options.get('add_to_note', True):
            # Still convert if enabled, but don't process notes
            processed_path = self.convert_to_jpg(original_path)
            self.log("Note insertion disabled, processing complete", "INFO")
            return
        
        # Get the last modified note
        note_path = self.get_last_modified_note()
        
        # Read note content
        with open(note_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse commands from the note
        note_commands = self.parse_note_commands(content)
        if note_commands:
            self.log(f"Applied note commands: {note_commands}", "INFO")
        
        # Convert to JPG if enabled (considering note commands)
        processed_path = self.convert_to_jpg(original_path, note_commands)
        
        # Extract prefix and highest number (considering note commands)
        prefix, highest_number = self.extract_prefix_and_highest_number(content, note_commands)
        
        # Check if renaming is enabled (globally or by note command)
        auto_rename = self.options.get('auto_rename', True)
        if note_commands and 'rename' in note_commands:
            auto_rename = note_commands['rename']
        
        # Check if numbering is enabled (globally or by note command)  
        auto_numbering = self.options.get('auto_numbering', True)
        if note_commands and 'numbering' in note_commands:
            auto_numbering = note_commands['numbering']
        
        # Generate new filename
        if auto_numbering:
            new_number = highest_number + 1
            file_extension = '.jpg' if (self.options.get('convert_jpg', True) or (note_commands and note_commands.get('convert'))) else processed_path.suffix
            new_filename = f"{prefix}_{new_number}{file_extension}"
        else:
            # Use original name or simple incremental naming
            file_extension = '.jpg' if (self.options.get('convert_jpg', True) or (note_commands and note_commands.get('convert'))) else processed_path.suffix
            new_filename = f"{prefix}_{int(time.time())}{file_extension}"
        
        new_path = processed_path.parent / new_filename
        
        # Rename the file if auto-renaming is enabled
        if auto_rename:
            try:
                processed_path.rename(new_path)
                self.log(f"Renamed {processed_path.name} to {new_filename}", "INFO")
                final_filename = new_filename
            except Exception as e:
                self.log(f"Error renaming file: {str(e)}", "ERROR")
                final_filename = processed_path.name
        else:
            final_filename = processed_path.name
        
        # Generate image code with custom format (from note commands or options)
        image_format = note_commands.get('format') if note_commands else self.options.get('image_format', "[[File:{filename}]]")
        if image_format:
            image_code = image_format.replace('{filename}', final_filename)
        else:
            image_code = f"[[File:{final_filename}]]"
        
        # Use separator from note commands or options
        separator_text = note_commands.get('separator') if note_commands and 'separator' in note_commands else self.options.get('separator', '')
        separator = '\n' + separator_text if separator_text else '\n'
        
        # Append to note
        with open(note_path, 'a', encoding='utf-8') as f:
            f.write(f"{separator}{image_code}")
        
        self.log(f"Added {image_code} to {note_path.name}", "INFO")
        
        # Clean up processed commands (optional - remove them from the note)
        if note_commands and self.options.get('clean_commands', False):
            self.clean_note_commands(note_path, content)

    def clean_note_commands(self, note_path, content):
        """Remove processed commands from the note"""
        try:
            # Patterns for all commands
            command_patterns = [
                r'\$pre(?:fix)?=[^\s\n]+',
                r'\$quality=\d+',
                r'\$format=[^\n]+',
                r'\$sep(?:arator)?=[^\n]*',
                r'\$convert=(?:true|false|on|off|yes|no)',
                r'\$rename=(?:true|false|on|off|yes|no)',
                r'\$num(?:bering)?=(?:true|false|on|off|yes|no)',
                r'\$bg(?:_?color)?=[#\w]+',
            ]
            
            cleaned_content = content
            for pattern in command_patterns:
                cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.IGNORECASE)
            
            # Remove empty lines that might have been left
            lines = cleaned_content.split('\n')
            cleaned_lines = []
            for line in lines:
                if line.strip():  # Keep non-empty lines
                    cleaned_lines.append(line)
                elif cleaned_lines and cleaned_lines[-1].strip():  # Keep one empty line after content
                    cleaned_lines.append(line)
            
            if cleaned_content != content:
                with open(note_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(cleaned_lines))
                self.log(f"Cleaned commands from {note_path.name}", "INFO")
                    
        except Exception as e:
            self.log(f"Error cleaning commands from note: {str(e)}", "ERROR")


class ImageProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Obsidian Image Processor")
        self.root.geometry("1000x800")
        
        # Variables for settings
        self.settings = {
            'vault_path': tk.StringVar(),
            'images_folder': tk.StringVar(),
            'default_prefix': tk.StringVar(value="Game"),
            'convert_jpg': tk.BooleanVar(value=True),
            'jpg_quality': tk.IntVar(value=95),
            'optimize_jpg': tk.BooleanVar(value=True),
            'bg_color': tk.StringVar(value="#FFFFFF"),
            'delete_original': tk.BooleanVar(value=True),
            'auto_rename': tk.BooleanVar(value=True),
            'auto_numbering': tk.BooleanVar(value=True),
            'add_to_note': tk.BooleanVar(value=True),
            'recursive': tk.BooleanVar(value=True),
            'skip_excalidraw': tk.BooleanVar(value=True),
            'image_format': tk.StringVar(value="[[File:{filename}]]"),
            'separator': tk.StringVar(value=""),
            'clean_commands': tk.BooleanVar(value=False),
            'cooldown': tk.DoubleVar(value=2.0),
            'enable_note_commands': tk.BooleanVar(value=True)
        }
        
        # Note command variables
        self.note_commands = {
            'prefix': tk.BooleanVar(value=True),
            'quality': tk.BooleanVar(value=True),
            'format': tk.BooleanVar(value=True),
            'separator': tk.BooleanVar(value=True),
            'convert': tk.BooleanVar(value=True),
            'rename': tk.BooleanVar(value=True),
            'numbering': tk.BooleanVar(value=True),
            'bg_color': tk.BooleanVar(value=True),
        }
        
        self.observer = None
        self.is_running = False
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Main Settings Tab
        main_tab = ttk.Frame(notebook)
        notebook.add(main_tab, text="Main Settings")
        self.setup_main_tab(main_tab)
        
        # Image Processing Tab
        image_tab = ttk.Frame(notebook)
        notebook.add(image_tab, text="Image Processing")
        self.setup_image_tab(image_tab)
        
        # Note Processing Tab
        note_tab = ttk.Frame(notebook)
        notebook.add(note_tab, text="Note Processing")
        self.setup_note_tab(note_tab)
        
        # Note Commands Tab
        commands_tab = ttk.Frame(notebook)
        notebook.add(commands_tab, text="Note Commands")
        self.setup_commands_tab(commands_tab)
        
        # Control Panel at bottom
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        self.start_button = ttk.Button(control_frame, text="Start Monitoring", command=self.toggle_monitoring)
        self.start_button.pack(side="left", padx=5)
        
        ttk.Button(control_frame, text="Save Settings", command=self.save_settings).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Load Settings", command=self.load_settings).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Clear Log", command=self.clear_log).pack(side="left", padx=5)
        
        self.status_label = ttk.Label(control_frame, text="Status: Stopped", foreground="red")
        self.status_label.pack(side="right", padx=5)
        
        # Log Output
        log_frame = ttk.LabelFrame(self.root, text="Log Output")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
    def setup_main_tab(self, parent):
        # Vault Path
        vault_frame = ttk.LabelFrame(parent, text="Paths Configuration")
        vault_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(vault_frame, text="Obsidian Vault Path:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(vault_frame, textvariable=self.settings['vault_path'], width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(vault_frame, text="Browse", command=lambda: self.browse_folder('vault_path')).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(vault_frame, text="Images Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(vault_frame, textvariable=self.settings['images_folder'], width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(vault_frame, text="Browse", command=lambda: self.browse_folder('images_folder')).grid(row=1, column=2, padx=5, pady=5)
        
        # Basic Settings
        basic_frame = ttk.LabelFrame(parent, text="Basic Settings")
        basic_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(basic_frame, text="Default Prefix:", anchor="w").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(basic_frame, textvariable=self.settings['default_prefix'], width=40).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(basic_frame, text="Cooldown (seconds):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Spinbox(basic_frame, from_=0.1, to=10.0, increment=0.1, textvariable=self.settings['cooldown'], width=10).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # Processing Options
        process_frame = ttk.LabelFrame(parent, text="Processing Options")
        process_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Checkbutton(process_frame, text="Add image code to note", variable=self.settings['add_to_note']).pack(anchor="w", padx=5, pady=2)
        ttk.Checkbutton(process_frame, text="Auto-rename files", variable=self.settings['auto_rename']).pack(anchor="w", padx=5, pady=2)
        ttk.Checkbutton(process_frame, text="Auto-numbering", variable=self.settings['auto_numbering']).pack(anchor="w", padx=5, pady=2)
        
    def setup_image_tab(self, parent):
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
        
    def setup_note_tab(self, parent):
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
        
    def setup_commands_tab(self, parent):
        # Enable/Disable Note Commands
        enable_frame = ttk.LabelFrame(parent, text="Note Commands")
        enable_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Checkbutton(enable_frame, text="Enable note commands", variable=self.settings['enable_note_commands'], 
                       command=self.toggle_note_commands).pack(anchor="w", padx=5, pady=5)
        
        # Individual Commands
        commands_frame = ttk.LabelFrame(parent, text="Available Commands (when enabled in notes)")
        commands_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a grid of checkboxes for each command
        commands_info = [
            ('$prefix=', 'Set custom prefix', 'prefix'),
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
            self.cmd_checkbox = ttk.Checkbutton(commands_frame, variable=self.note_commands[var_name])
            self.cmd_checkbox.grid(row=i, column=2, padx=5, pady=2)
        
        # Example usage
        example_frame = ttk.LabelFrame(parent, text="Example Usage in Notes")
        example_frame.pack(fill="x", padx=10, pady=10)
        
        example_text = """$prefix=Screenshot
$quality=85
$format=![[{filename}]]
$separator=---
$convert=true
$rename=false"""
        
        example_label = tk.Text(example_frame, height=6, width=50, font=("Courier", 9))
        example_label.insert("1.0", example_text)
        example_label.config(state="disabled", background="#f0f0f0")
        example_label.pack(padx=10, pady=10)
        
    def toggle_note_commands(self):
        """Enable/disable individual note command checkboxes"""
        state = self.settings['enable_note_commands'].get()
        # This would need to store references to all command checkboxes
        # For now, it just logs the state
        self.log_message(f"Note commands {'enabled' if state else 'disabled'}")
        
    def browse_folder(self, setting_key):
        folder = filedialog.askdirectory()
        if folder:
            self.settings[setting_key].set(folder)
            
    def choose_color(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(initialcolor=self.settings['bg_color'].get())
        if color[1]:
            self.settings['bg_color'].set(color[1])
            
    def toggle_monitoring(self):
        if not self.is_running:
            self.start_monitoring()
        else:
            self.stop_monitoring()
            
    def start_monitoring(self):
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
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {str(e)}")
            self.log_message(f"Error: {str(e)}", "ERROR")
            
    def stop_monitoring(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            
        self.is_running = False
        self.start_button.config(text="Start Monitoring")
        self.status_label.config(text="Status: Stopped", foreground="red")
        self.log_message("Stopped monitoring")
        
    def log_message(self, message, level="INFO"):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        
    def save_settings(self):
        try:
            settings_dict = {key: var.get() for key, var in self.settings.items()}
            settings_dict['note_commands'] = {key: var.get() for key, var in self.note_commands.items()}
            
            with open('settings.json', 'w') as f:
                json.dump(settings_dict, f, indent=4)
                
            self.log_message("Settings saved successfully")
            messagebox.showinfo("Success", "Settings saved to settings.json")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            
    def load_settings(self):
        try:
            if Path('settings.json').exists():
                with open('settings.json', 'r') as f:
                    settings_dict = json.load(f)
                    
                for key, value in settings_dict.items():
                    if key == 'note_commands':
                        for cmd_key, cmd_value in value.items():
                            if cmd_key in self.note_commands:
                                self.note_commands[cmd_key].set(cmd_value)
                    elif key in self.settings:
                        self.settings[key].set(value)
                        
                self.log_message("Settings loaded successfully")
            elif Path('config.txt').exists():
                # Try to load from old config.txt format
                self.load_legacy_config()
        except Exception as e:
            self.log_message(f"Failed to load settings: {str(e)}", "ERROR")
            
    def load_legacy_config(self):
        """Load configuration from old config.txt format"""
        try:
            config = {}
            with open('config.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
            
            if 'vault_path' in config:
                self.settings['vault_path'].set(config['vault_path'])
            if 'images_folder' in config:
                self.settings['images_folder'].set(config['images_folder'])
            if 'default_prefix' in config:
                self.settings['default_prefix'].set(config['default_prefix'])
                
            self.log_message("Legacy config loaded from config.txt")
        except Exception as e:
            self.log_message(f"Failed to load legacy config: {str(e)}", "ERROR")


def main():
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

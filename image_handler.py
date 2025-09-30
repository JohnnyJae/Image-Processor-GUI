import os
import re
import time
import logging
from pathlib import Path
from watchdog.events import FileSystemEventHandler
import mimetypes


class ImageHandler(FileSystemEventHandler):
    def __init__(self, obsidian_vault_path, default_prefix, options, log_callback=None):
        self.obsidian_vault_path = Path(obsidian_vault_path)
        self.default_prefix = default_prefix
        self.options = options
        self.last_processed_time = 0
        self.cooldown_seconds = options.get('cooldown', 2.0)
        self.log_callback = log_callback
        
        # Performance optimizations
        self._cached_note_path = None
        self._cached_note_mtime = 0
        self._note_cache_valid = False
        
        # Pre-compile regex patterns for better performance
        self._compiled_patterns = self._compile_regex_patterns()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def _compile_regex_patterns(self):
        """Pre-compile regex patterns for better performance"""
        return {
            'prefix': re.compile(r'\$pre(?:fix)?=([^\s\n]+)', re.IGNORECASE),
            'quality': re.compile(r'\$quality=(\d+)', re.IGNORECASE),
            'format': re.compile(r'\$format=([^\n]+)', re.IGNORECASE),
            'separator': re.compile(r'\$sep(?:arator)?=([^\n]*)', re.IGNORECASE),
            'convert': re.compile(r'\$convert=(true|false|on|off|yes|no)', re.IGNORECASE),
            'rename': re.compile(r'\$rename=(true|false|on|off|yes|no)', re.IGNORECASE),
            'numbering': re.compile(r'\$num(?:bering)?=(true|false|on|off|yes|no)', re.IGNORECASE),
            'bg_color': re.compile(r'\$bg(?:_?color)?=([#\w]+)', re.IGNORECASE),
            'image_code': re.compile(r'\[\[File:([^_]+)_(\d+)\.[^|\]]+(?:\|[^\]]+)?\]\]')
        }
        
    def update_options(self, new_options):
        """Update options dynamically without restarting"""
        self.options.update(new_options)
        self.cooldown_seconds = self.options.get('cooldown', 2.0)
        
    def log(self, message, level="INFO"):
        """Custom log method that sends to GUI"""
        if self.log_callback:
            self.log_callback(f"[{level}] {message}")
        self.logger.log(getattr(logging, level), message)
        
    def create_subprefix_from_filename(self, note_path):
        """Create a subprefix from the note filename by removing non-alphanumeric chars and capitalizing words"""
        filename = note_path.stem  # Get filename without extension
        
        # Remove non-alphanumeric characters and split into words
        import string
        # Replace non-alphanumeric with spaces, then split
        cleaned = ''.join(c if c.isalnum() else ' ' for c in filename)
        words = cleaned.split()
        
        # Capitalize each word and join them
        subprefix = ''.join(word.capitalize() for word in words if word)
        
        return subprefix if subprefix else "Untitled"
        
    def build_automatic_prefix(self, note_path):
        """Build automatic prefix from user prefix and note filename"""
        user_prefix = self.options.get('automatic_prefix_user', '').strip()
        subprefix = self.create_subprefix_from_filename(note_path)
        
        if user_prefix and subprefix:
            # Ensure only one hyphen between user prefix and subprefix
            user_clean = user_prefix.rstrip('-')
            final_prefix = f"{user_clean}-{subprefix}"
        elif user_prefix:
            final_prefix = user_prefix.rstrip('-')
        elif subprefix:
            final_prefix = subprefix
        else:
            # Fallback to default prefix
            final_prefix = self.default_prefix
            
        self.log(f"Built automatic prefix: {final_prefix} (user: '{user_prefix}', subprefix: '{subprefix}')", "INFO")
        return final_prefix
        
    def on_created(self, event):
        if event.is_directory:
            return
            
        # Check cooldown
        current_time = time.time()
        if current_time - self.last_processed_time < self.cooldown_seconds:
            self.log(f"Cooldown active, ignoring {event.src_path}", "INFO")
            return
            
        file_path = Path(str(event.src_path))
        
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
        """Find the most recently modified .md file in the vault with caching"""
        try:
            # Check if we have a cached note and if it's still valid
            if self._cached_note_path and self._note_cache_valid:
                try:
                    current_mtime = self._cached_note_path.stat().st_mtime
                    # If the cached note is still the most recent, return it
                    if current_mtime >= self._cached_note_mtime:
                        self.log(f"Using cached note: {self._cached_note_path}", "DEBUG")
                        return self._cached_note_path
                except (OSError, FileNotFoundError):
                    # Cached file no longer exists, invalidate cache
                    self._note_cache_valid = False
            
            # Cache miss or invalid - do full search
            self.log("Performing full note search (cache miss)", "DEBUG")
            
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
            
            # Update cache
            self._cached_note_path = latest_note
            self._cached_note_mtime = latest_note.stat().st_mtime
            self._note_cache_valid = True
            
            self.log(f"Using most recently modified note: {latest_note}", "INFO")
            return latest_note
        except Exception as e:
            self.log(f"Error finding last modified markdown note: {str(e)}", "ERROR")
            raise
    
    def parse_note_commands(self, content):
        """Parse special commands from the note content using pre-compiled patterns"""
        commands = {}
        
        # Use pre-compiled patterns for better performance
        for command, pattern in self._compiled_patterns.items():
            if command == 'image_code':  # Skip this one, it's for prefix extraction
                continue
                
            matches = pattern.findall(content)
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

    def get_effective_prefix(self, content, note_commands=None, note_path=None):
        """Get the effective prefix considering automatic, override, note commands, and auto-detection"""
        
        # Priority 1: Automatic prefix system (if enabled)
        if self.options.get('automatic_prefix_enabled', False):
            if note_path:
                automatic_prefix = self.build_automatic_prefix(note_path)
                self.log(f"Using automatic prefix: {automatic_prefix}", "INFO")
                return automatic_prefix
            else:
                self.log("Automatic prefix enabled but no note path provided, falling back", "WARNING")
        
        # Priority 2: Override prefix (highest priority in manual mode)
        override_prefix = self.options.get('override_prefix', '').strip()
        if override_prefix:
            self.log(f"Using override prefix: {override_prefix}", "INFO")
            return override_prefix
        
        # Priority 3: Note command prefix
        if note_commands and 'prefix' in note_commands:
            self.log(f"Using note command prefix: {note_commands['prefix']}", "INFO")
            return note_commands['prefix']
        
        # Priority 4: Auto-detected prefix (if auto-numbering is enabled)
        if self.options.get('auto_numbering', True) or (note_commands and note_commands.get('numbering')):
            # Use pre-compiled pattern for better performance
            matches = self._compiled_patterns['image_code'].findall(content)
            
            if matches:
                # Count occurrences of each prefix
                prefix_counts = {}
                for prefix, number in matches:
                    prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
                
                # Use the most common prefix
                most_common_prefix = max(prefix_counts.keys(), key=lambda x: prefix_counts[x])
                self.log(f"Auto-detected prefix: {most_common_prefix}", "INFO")
                return most_common_prefix
        
        # Priority 5: Default prefix (lowest priority)
        self.log(f"Using default prefix: {self.default_prefix}", "INFO")
        return self.default_prefix

    def extract_prefix_and_highest_number(self, content, note_commands=None, note_path=None):
        """Extract prefix and find highest number from existing image codes"""
        # Get the effective prefix
        effective_prefix = self.get_effective_prefix(content, note_commands, note_path)
        
        # If numbering is disabled, return prefix with number 0
        if not self.options.get('auto_numbering', True) and not (note_commands and note_commands.get('numbering')):
            return effective_prefix, 0
        
        # For automatic prefix system, always start numbering at 1 instead of finding highest
        if self.options.get('automatic_prefix_enabled', False):
            # Use pre-compiled pattern for better performance
            matches = self._compiled_patterns['image_code'].findall(content)
            
            if not matches:
                return effective_prefix, 0
            
            # Find the highest number for the effective prefix
            prefix_numbers = []
            for prefix, number in matches:
                if prefix == effective_prefix:
                    prefix_numbers.append(int(number))
            
            highest_number = max(prefix_numbers) if prefix_numbers else 0
            self.log(f"Using automatic prefix: {effective_prefix}, highest number: {highest_number}", "INFO")
            return effective_prefix, highest_number
        
        # Use pre-compiled pattern for better performance
        matches = self._compiled_patterns['image_code'].findall(content)
        
        if not matches:
            return effective_prefix, 0
        
        # Find the highest number for the effective prefix
        prefix_numbers = []
        for prefix, number in matches:
            if prefix == effective_prefix:
                prefix_numbers.append(int(number))
        
        highest_number = max(prefix_numbers) if prefix_numbers else 0
        self.log(f"Using prefix: {effective_prefix}, highest number: {highest_number}", "INFO")
        return effective_prefix, highest_number
    
    def process_image(self, original_path):
        """Main processing function with optimized file I/O"""
        start_time = time.time()
        self.log(f"Processing new image: {original_path}", "INFO")
        
        if not self.options.get('add_to_note', True):
            # Still convert if enabled, but don't process notes
            processed_path = self.convert_to_jpg(original_path)
            self.log("Note insertion disabled, processing complete", "INFO")
            return
        
        # Get the last modified note
        note_path = self.get_last_modified_note()
        
        # Read note content ONCE
        with open(note_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Parse commands from the note
        note_commands = self.parse_note_commands(original_content)
        if note_commands:
            self.log(f"Applied note commands: {note_commands}", "INFO")
        
        # Convert to JPG if enabled (considering note commands)
        processed_path = self.convert_to_jpg(original_path, note_commands)
        
        # Extract prefix and highest number (considering note commands, override, and automatic prefix)
        prefix, highest_number = self.extract_prefix_and_highest_number(original_content, note_commands, note_path)
        
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
        
        # Prepare final content for single write operation
        final_content = original_content
        
        # Clean up processed commands if requested (modify content before writing)
        if note_commands and self.options.get('clean_commands', False):
            final_content = self._clean_commands_from_content(final_content)
        
        # Add image code to final content
        final_content += f"{separator}{image_code}"
        
        # Write everything in ONE operation
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        # Invalidate note cache since we modified the file
        self._note_cache_valid = False
        
        processing_time = time.time() - start_time
        self.log(f"Added {image_code} to {note_path.name} (processed in {processing_time:.2f}s)", "INFO")

    def _clean_commands_from_content(self, content):
        """Remove processed commands from content (internal helper)"""
        try:
            # Use pre-compiled patterns for cleaning
            cleaned_content = content
            for pattern in self._compiled_patterns.values():
                if pattern != self._compiled_patterns['image_code']:  # Don't remove image codes
                    cleaned_content = pattern.sub('', cleaned_content)
            
            # Remove empty lines that might have been left
            lines = cleaned_content.split('\n')
            cleaned_lines = []
            for line in lines:
                if line.strip():  # Keep non-empty lines
                    cleaned_lines.append(line)
                elif cleaned_lines and cleaned_lines[-1].strip():  # Keep one empty line after content
                    cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
                    
        except Exception as e:
            self.log(f"Error cleaning commands from content: {str(e)}", "ERROR")
            return content
    
    def clean_note_commands(self, note_path, content):
        """Remove processed commands from the note (legacy method for compatibility)"""
        try:
            cleaned_content = self._clean_commands_from_content(content)
            
            if cleaned_content != content:
                with open(note_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                self.log(f"Cleaned commands from {note_path.name}", "INFO")
                    
        except Exception as e:
            self.log(f"Error cleaning commands from note: {str(e)}", "ERROR")
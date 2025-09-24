import json
from pathlib import Path


class SettingsManager:
    """Manages loading and saving of application settings"""
    
    @staticmethod
    def get_default_settings():
        """Returns the default settings dictionary"""
        return {
            'vault_path': '',
            'images_folder': '',
            'default_prefix': 'Game',
            'override_prefix': '',
            'convert_jpg': True,
            'jpg_quality': 95,
            'optimize_jpg': True,
            'bg_color': '#FFFFFF',
            'delete_original': True,
            'auto_rename': True,
            'auto_numbering': True,
            'add_to_note': True,
            'recursive': True,
            'skip_excalidraw': True,
            'image_format': '[[File:{filename}]]',
            'separator': '',
            'clean_commands': False,
            'cooldown': 2.0,
            'enable_note_commands': True,
            'dark_theme': False
        }
    
    @staticmethod
    def get_default_note_commands():
        """Returns the default note commands settings"""
        return {
            'prefix': True,
            'quality': True,
            'format': True,
            'separator': True,
            'convert': True,
            'rename': True,
            'numbering': True,
            'bg_color': True,
        }
    
    @staticmethod
    def save_settings(settings_dict, note_commands_dict, filename='settings.json'):
        """Save settings to JSON file"""
        try:
            combined_settings = settings_dict.copy()
            combined_settings['note_commands'] = note_commands_dict
            
            with open(filename, 'w') as f:
                json.dump(combined_settings, f, indent=4)
            return True, "Settings saved successfully"
        except Exception as e:
            return False, f"Failed to save settings: {str(e)}"
    
    @staticmethod
    def load_settings(filename='settings.json'):
        """Load settings from JSON file"""
        try:
            if Path(filename).exists():
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                # Separate main settings from note commands
                note_commands = data.pop('note_commands', {})
                return True, data, note_commands, "Settings loaded successfully"
            else:
                # Try legacy config
                success, settings, message = SettingsManager.load_legacy_config()
                if success:
                    return True, settings, SettingsManager.get_default_note_commands(), message
                else:
                    return False, {}, {}, "No settings file found"
        except Exception as e:
            return False, {}, {}, f"Failed to load settings: {str(e)}"
    
    @staticmethod
    def load_legacy_config(filename='config.txt'):
        """Load configuration from old config.txt format"""
        try:
            if not Path(filename).exists():
                return False, {}, "Legacy config file not found"
                
            config = {}
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
            
            # Map legacy settings to new format
            settings = SettingsManager.get_default_settings()
            if 'vault_path' in config:
                settings['vault_path'] = config['vault_path']
            if 'images_folder' in config:
                settings['images_folder'] = config['images_folder']
            if 'default_prefix' in config:
                settings['default_prefix'] = config['default_prefix']
                
            return True, settings, "Legacy config loaded from config.txt"
        except Exception as e:
            return False, {}, f"Failed to load legacy config: {str(e)}"
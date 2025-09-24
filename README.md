# Obsidian Image Processor

This application automatically processes images added to a specified folder and integrates them with your Obsidian notes.

## Features

- **Automatic Image Processing**: Monitors a folder for new images and processes them automatically
- **JPG Conversion**: Converts images to JPG format with configurable quality settings
- **Auto-naming**: Automatically names files with prefixes and sequential numbering
- **Note Integration**: Automatically adds image codes to your most recently modified Obsidian note
- **Note Commands**: Control processing behavior with special commands in your notes
- **Flexible Configuration**: Extensive settings for customizing behavior

## Files Structure

- `main.py` - Main application entry point and GUI management
- `image_handler.py` - Core image processing logic
- `gui_tabs.py` - GUI tab components for settings
- `settings_manager.py` - Settings loading/saving functionality
- `obsidian_gui.py` - Original monolithic file (can be removed after migration)

## Requirements

- Python 3.7+
- tkinter (usually included with Python)
- watchdog (for file monitoring)
- Pillow (PIL) - for image conversion (optional)

## Installation

1. Install required dependencies:
```bash
pip install watchdog pillow
```

2. Run the application:
```bash
python main.py
```

## Usage

1. **Setup Paths**: Configure your Obsidian vault path and images folder in the "Main Settings" tab
2. **Configure Processing**: Adjust image processing settings in the "Image Processing" tab
3. **Note Settings**: Configure how images are added to notes in the "Note Processing" tab
4. **Start Monitoring**: Click "Start Monitoring" to begin watching for new images

## Note Commands

You can control processing behavior by adding special commands to your notes:

- `$prefix=NewPrefix` - Set custom prefix for images
- `$quality=85` - Set JPG quality (1-100)
- `$format=![[{filename}]]` - Set custom image format
- `$separator=---` - Set custom separator text
- `$convert=false` - Disable JPG conversion
- `$rename=false` - Disable auto-renaming
- `$numbering=false` - Disable auto-numbering
- `$bg_color=#FFFFFF` - Set background color for transparent images

## Settings

Settings are automatically saved to `settings.json` and can be loaded on startup.

## Migration from Original File

If you were using the original `obsidian_gui.py`, your settings should automatically migrate to the new format. The new modular structure provides better maintainability and separation of concerns.
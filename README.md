# Obsidian Image Processor (Tkinter GUI)

An easy-to-use desktop GUI that watches an image folder and automatically processes new images for use in an Obsidian vault. The app can convert images to JPG, rename files using configurable prefixes and numbering, and append image links to the most-recently-modified markdown note in your vault. A modern Tkinter-based UI exposes settings, note-command controls, and a realtime activity log.

This README covers installation, usage, the available settings, and the inline note commands you can use to customize behavior per-note.

## Highlights

- Monitor a folder for newly created images (uses `watchdog`).
- Optional conversion to JPG with background handling for transparent images (uses `Pillow`).
- Auto-rename and auto-numbering using configurable prefixes.
- Multiple prefix sources: Override (highest priority), per-note commands, auto-detected from existing image codes, or a default fallback.
- Append formatted image code into the most recently modified `.md` note in your vault.
- Per-note commands (embedded in the note) to change quality, format, separator, conversion, renaming, numbering and background color.
- Save and load settings to `settings.json`.

## Quick start (Windows / PowerShell)

1. Ensure you have Python 3.10+ installed and available on PATH.
2. Open PowerShell in the project folder (where `main.py` lives).
3. Create and activate a virtual environment, install requirements, and run the app:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\main.py
```

Notes:
- If you don't want to use a virtual environment you can install requirements globally, but a venv is recommended.
- `Tkinter` is required — it usually ships with the standard Python installer on Windows.

## Files of interest

- `main.py` — GUI app entry point and orchestrator.
- `image_handler.py` — core file-watcher logic and image processing behavior.
- `gui_tabs.py` — the UI tab implementations (settings, image processing, notes, commands).
- `settings_manager.py` — load/save and default settings logic.
- `theme_manager.py` — UI theme and styling utilities.
- `settings.json` — persisted settings created via the GUI (in project folder by default).

## Installation (dependencies)

Dependencies are declared in `requirements.txt`. The main runtime requirements are:

- watchdog (file system monitoring)
- Pillow (image conversion) — optional only if you enable JPG conversion

Install with pip (see Quick start above).

## Running the app

- Start the app with `python main.py`.
- In the GUI set your Obsidian vault path and the images folder to watch.
- Configure prefixes, conversion options, and other behavior in the tabs.
- Click "Start Monitoring" to begin watching the images folder.

When a new image is added to the watched folder the app will:

1. Respect the configured cooldown to avoid duplicate processing.
2. Optionally convert the image to JPG (honoring per-note commands when present).
3. Optionally rename the file (prefix + numbering) according to the active prefix logic.
4. Append the configured image format (default `[[File:{filename}]]`) to the most recently modified `.md` note in the vault.

## Settings (exposed in GUI / saved in `settings.json`)

Key settings (defaults are included in the app and `SettingsManager.get_default_settings()`):

- `vault_path` — path to your Obsidian vault (where `.md` notes live).
- `images_folder` — path to watch for new images (the folder you drop screenshots/images into).
- `default_prefix` — fallback prefix used when no other prefix source is available.
- `override_prefix` — when set (non-empty) this takes highest priority and always wins.
- `automatic_prefix_enabled` — build prefixes automatically from the last-modified note's file name.
- `automatic_prefix_user` — optional user/game prefix to preprend when automatic prefixes are enabled.
- `convert_jpg` — convert incoming images to JPG (requires Pillow).
- `jpg_quality` — JPEG quality (1–100).
- `optimize_jpg` — pass `optimize=True` when saving JPEGs.
- `bg_color` — hex color used as background when converting transparent images.
- `delete_original` — remove original file after conversion.
- `auto_rename` — rename incoming files to prefix_number.ext.
- `auto_numbering` — enable numeric incrementing when renaming.
- `image_format` — how to insert image code into the note. Use `{filename}` placeholder. Default: `[[File:{filename}]]`.
- `separator` — text inserted before the image code in the note (commonly a newline or `---`).
- `clean_commands` — remove processed inline note commands from a note after they are applied.
- `cooldown` — seconds to wait between processing events (helps when multiple FS events fire).
- `enable_note_commands` — whether to respect per-note commands at all.

You can save settings from the GUI; they are written to `settings.json` in the project directory. The GUI can also load `config.txt` legacy files if present.

## Note commands (inline control inside a Markdown note)

When note commands are enabled, the app will parse special commands from the currently selected/most-recent note. Commands are case-insensitive and the last occurrence wins. Commands are simple inline directives anywhere in the note text. The supported commands are:

- `$prefix=VALUE` — set a prefix for this note (e.g. `$prefix=Screenshot`).
- `$quality=NN` — set JPEG quality (1–100) for conversions triggered while this note is active.
- `$format=...` — custom insertion format using `{filename}` (e.g. `$format=![[{filename}]]`).
- `$separator=...` — text to insert before the image code (for example `---` or an empty line).
- `$convert=true|false` — enable/disable JPG conversion for this note.
- `$rename=true|false` — enable/disable auto-renaming for this note.
- `$numbering=true|false` — enable/disable auto-numbering for this note.
- `$bg_color=#RRGGBB` — background color to use when flattening transparent images for this note.

Examples inside a note:

```
$prefix=Screenshot
$quality=85
$format=![[{filename}]]
$separator=---
$convert=true
$rename=false
```

If `override_prefix` is set in the main settings it will ignore `$prefix=` commands in notes.

## Prefix resolution order (highest → lowest)

1. Override Prefix (from the Main Settings tab) — highest priority when not empty
2. Note Command `$prefix=` — per-note override when note commands enabled
3. Auto-detected prefix — the app can inspect existing image codes like `[[File:Prefix_1.jpg]]` and pick the most common prefix
4. Default Prefix — final fallback

## Example workflow

1. Configure `vault_path` to your Obsidian vault and `images_folder` to your screenshots folder.
2. (Optional) Add `$prefix=MyScreens` and `$quality=90` to a note you are working in.
3. Start monitoring in the GUI.
4. Save a screenshot into the watched folder. The app will convert/rename and append `[[File:MyScreens_1.jpg]]` (or your chosen format) to the most recently edited note.

## Troubleshooting & tips

- Pillow is required only when JPG conversion is enabled. If Pillow is missing the GUI will warn and offer to continue without conversion.
- Ensure the `vault_path` and `images_folder` are correct and that the app has filesystem permissions to read/write them.
- If images are processed multiple times or not at all, adjust the `cooldown` setting.
- The watcher schedules the handler non-recursively by default for performance; enable recursive search for notes using the `recursive` option.
- On Windows, long paths or OneDrive syncing can sometimes interfere—use local folders where possible or ensure OneDrive doesn't lock files.

## Development notes

- The GUI is built with Tkinter and uses a `ModernThemeManager` in `theme_manager.py` for nicer visuals.
- Core logic lives in `image_handler.py`. Behavior is exposed via `SettingsManager` and the GUI tabs in `gui_tabs.py`.
- Tests are not included in this repository. Suggested small test ideas: validate prefix extraction, simulate `parse_note_commands()` with sample note text, and run `convert_to_jpg()` against small test images.

## Contributing

Contributions, bug reports and feature requests are welcome. Please open an issue or submit a PR. If you add features that change settings or note-commands, update this README accordingly.

## License

No license file is included in this repository. Add a `LICENSE` file if you wish to declare an explicit license.

---

If you'd like, I can also:

- Add an example `settings.example.json` file to the repo.
- Add a small unit test file for `image_handler.parse_note_commands` and `SettingsManager`.

Tell me which of those you'd like next and I'll add them.

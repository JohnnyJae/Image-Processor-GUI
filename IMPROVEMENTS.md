# Improvements & Roadmap

This document outlines potential improvements, refactoring opportunities, and feature additions for the Obsidian Image Processor.

## 1. Refactoring & Code Quality

- **Remove Legacy Code:** 

- **Refactor `ImageHandler.process_image`:** 
  - The `process_image` method in `image_handler.py` is too large. Break it down into smaller, single-responsibility methods such as `_convert_image()`, `_generate_filename()`, and `_append_to_note()`.
- **Add Type Hinting:** 
  - Add Python type hints (PEP 484) to function signatures across all files to improve readability and enable static analysis.
- **Strategy Pattern:** 
  - If logic branches for different processing modes become complex, refactor them into separate Strategy classes.

## 2. Features & Functionality

- **Undo Capability:** 
  - Add a feature to revert the last action (file rename + note append) in case of accidental processing.
- **Configurable Extensions:** 
  - Move the hardcoded list of supported image extensions (currently in `image_handler.py`) to `settings.json` so users can easily add support for other formats (e.g., `.webp`, `.svg`).

## 3. Error Handling & Stability

- **Specific Exception Handling:** 
  - Replace broad `except Exception:` blocks with specific exceptions (e.g., `PermissionError`, `FileNotFoundError`) to provide more actionable error messages to the user.
- **Early Dependency Check:** 
  - Check for `Pillow` availability at application startup in `main.py`. If missing, disable the "Convert to JPG" UI options immediately rather than waiting for a runtime error during processing.

## 4. Testing & Documentation

- **Unit Tests:** 
  - Create a `tests/` directory.
  - Add tests for `image_handler.py` to verify regex patterns (e.g., `$prefix=` parsing) and filename generation logic.
  - Add tests for `settings_manager.py` to ensure settings are saved/loaded correctly.
- **Docstrings:** 
  - Expand docstrings in `image_handler.py`, specifically explaining the reasoning behind any `time.sleep()` calls or retry logic.

## 5. UI/UX

- **Input Validation:** 
  - Add immediate visual feedback (e.g., red border or warning icon) in the Settings tab if the entered "Vault Path" or "Images Folder" does not exist.
- **Non-Blocking Operations:** 
  - Ensure that clipboard operations and heavy file processing tasks do not block the main UI thread, potentially by using `threading` or `asyncio` more effectively.

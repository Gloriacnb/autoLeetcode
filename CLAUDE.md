# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

autoLeetcode is a Python tool that automates solving LeetCode problems from screenshots using Google's Gemini API. It monitors a directory for new screenshots, analyzes them with AI to generate solution code, tests the generated code, and copies working solutions to the clipboard.

## Development Commands

### Installation
```bash
uv sync
```

### Running the Application
```bash
uv run python monitor_screenshots.py
```

The application can also be run via the installed entry point:
```bash
autoleetcode
```

## Architecture

### Core Components

**monitor_screenshots.py** - Main application entry point containing:
- `ScreenshotHandler`: Watchdog event handler that processes new image files
- File system monitoring using `watchdog` library
- AI code generation and testing loop with automatic error correction

**Configuration (config.ini)**
- `[Paths]`: Source screenshot directory and output code directory
- `[GeminiAPI]`: API key, model name, and generation prompt

### Processing Pipeline

1. **Screenshot Detection**: `ScreenshotHandler.on_created()` is triggered when new images (.png, .jpg, .jpeg) appear
2. **Code Generation**: Image is sent to Gemini API with the configured prompt
3. **Code Extraction**: Response is parsed for "题目名称:" title and markdown code blocks
4. **Testing Loop**: Generated code is run via subprocess; if it fails, error output is sent back to Gemini for fixes (max 3 attempts)
5. **Completion**: Working code is saved to OUTPUT_CODE_DIRECTORY and copied to clipboard

### Key Functions

- `_process_screenshot()`: Main pipeline orchestrator
- `_extract_code_from_markdown()`: Parses Gemini response to extract title and Python code
- `_fix_code()`: Sends broken code + error message to Gemini for correction
- `_run_and_test_code()`: Executes generated Python file and captures stderr
- `_get_code_path()`: Generates sanitized filename from problem title

### Important Constants

- `MAX_FIX_ATTEMPTS = 3`: Maximum iterations for fixing broken code
- `CONFIG_FILE = 'config.ini'`: Required configuration file

### Dependencies

- `google-generativeai`: Gemini API client
- `watchdog`: File system monitoring
- `pillow`: Image processing
- `pyperclip`: Clipboard operations

## Configuration Notes

The config.ini file must be created from config.ini.template before running. The API key must be set to a valid Gemini API key, and paths must be absolute paths to existing directories.

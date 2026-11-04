# FoxVC VS Code Extension

Official Visual Studio Code & Cursor extension for the **FoxVC** programming language.

## Features
* **Syntax Highlighting:** Complete grammar support for all 25 keywords (`act`, `emit`, `lock`, `shift`, `pick`, `alt`, `spin`, etc.) and standard library shelves.
* **Auto-Formatting (`foxvc fmt`):** Formats `.fox` code to canonical 4-space indentation.
* **Native Testing (`foxvc test`):** Run unit test suites directly from the command palette.
* **Standalone Compilation (`foxvc build`):** Compile current script into a 15KB standalone binary with 1 click.

## Usage
* Open any `.fox` file.
* Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS) and type:
  * `FoxVC: Run Current Script`
  * `FoxVC: Build Standalone Native Binary`
  * `FoxVC: Format Code (foxvc fmt)`
  * `FoxVC: Run Test Suite (foxvc test)`

# FocusReader for Windows

FocusReader for Windows is a native C17 Win32 tray app that places a click-through reading guard over ordinary desktop applications.

## Features

- A system-wide guard that follows the pointer on the active monitor.
- Optional horizontal coverage for the remainder of the current line.
- Optional click-to-pin positioning.
- Adjustable guard color and opacity.
- A 180 ms fade when the guard is toggled.
- Global `Ctrl+Alt+F` shortcut.
- Notification-area controls and one overlay per display.
- Local settings only; no network activity, analytics, or page inspection.

## Run it

Install CMake and a Windows C compiler, then run these commands from the repository root:

```powershell
cmake -S windows -B build\windows
cmake --build build\windows --config Release
.\build\windows\bin\FocusReader.Windows.exe
```

Visual Studio's MSVC toolchain is recommended, and the same CMake project also supports MinGW GCC. The settings window opens when FocusReader starts. The guard begins turned off.

1. Choose the guard behavior, color, and opacity.
2. Press `Ctrl+Alt+F` or use the notification-area menu to turn the guard on.
3. Move the pointer to guide the guard. In click-to-pin mode, click to place it.
4. Close the settings window when finished configuring it; FocusReader remains in the notification area.
5. Choose **Exit** from the notification-area menu to stop the app.

Double-clicking the notification-area icon reopens Settings.

## Build and check

```powershell
cmake -S windows -B build\windows
cmake --build build\windows --config Release
ctest --test-dir build\windows -C Release --output-on-failure
```

The checks cover guard geometry, settings normalization, and fade interpolation without requiring a test framework or third-party packages.

## Build installer and release artifacts

Install CMake and a Windows C compiler. Inno Setup 6 can be installed for the current user with:

```powershell
winget install --id JRSoftware.InnoSetup -e --scope user
```

Then run this command from the repository root:

```powershell
.\scripts\build-release.ps1 -Version 0.1.0
```

The script creates these versioned files under `artifacts\`:

- a native Windows x64 installer;
- a portable Windows x64 ZIP;
- a Chrome extension ZIP; and
- `SHA256SUMS.txt`.

The installer is per-user: it requires no administrator access, installs under `%LOCALAPPDATA%\Programs\FocusReader`, creates a Start menu shortcut, offers an optional desktop shortcut, and registers an uninstaller.

The tagged-release workflow runs the same packaging script for tags such as `v0.1.0` and attaches the results to a GitHub Release.

This early installer is unsigned, so Windows may display a reputation warning. Code signing is the next distribution-hardening step.

## Settings and privacy

Preferences are stored locally at `%LOCALAPPDATA%\FocusReader\settings.json`. The app observes pointer position, left-button state, display geometry, and its global shortcut only to place or toggle the overlays. It does not inspect other windows or make network requests.

The enabled state deliberately resets when the app launches.

## Project layout

```text
CMakeLists.txt                Native build and CTest definition
include/focusreader.h         Shared C interfaces and data types
src/main.c                    Win32 UI, tray, overlay, and settings
src/core.c                    Guard geometry and fade calculations
tests/test_core.c             Dependency-free native logic checks
resources/app.manifest       DPI and Windows compatibility settings
resources/*.rc.in            Version and manifest resources
..\installer\FocusReader.iss  Inno Setup installer definition
..\scripts\build-release.ps1 Release packaging and checksums
```


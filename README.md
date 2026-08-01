# FocusReader

FocusReader covers unread content so you can stay with the text directly in front of you. Move the pointer down a page and an opaque shield follows beneath it. An optional horizontal guard also covers the remainder of the current line.

This repository contains two dependency-free implementations:

- A Manifest V3 Chrome extension under [`chrome/`](chrome/README.md).
- A native C17 Win32 tray app under [`windows/`](windows/README.md).

## Chrome extension

### Current features

- Toggle the guard independently on each tab.
- Move the guard with the pointer or pin it by clicking.
- Cover content below the reading position.
- Optionally cover the remainder of the current line.
- Adjust guard color and density.
- Toggle the current tab with `Alt+Shift+F`.
- Keep preferences in Chrome's synchronized extension storage.

### Install locally

1. Download or clone this repository.
2. Open `chrome://extensions` in Chrome.
3. Enable **Developer mode**.
4. Select **Load unpacked**.
5. Choose the repository's `chrome` folder—the folder containing `manifest.json`.
6. Pin FocusReader from Chrome's Extensions menu if you want the toolbar control to remain visible.
7. Reload any already-open page before using FocusReader on it for the first time.

No build step is required.

### Use it

1. Open a normal `http://` or `https://` page.
2. Select the FocusReader toolbar icon.
3. Choose **Turn on for this tab**.
4. Move the pointer to guide the shield down the page.

If **Click to pin position** is enabled, click or tap the page to place the guard. Click or tap again to move it.

The enabled state is deliberately tab-local and resets when that tab navigates. Color, density, and behavior preferences persist across tabs.

### Browser support and current boundaries

The MVP runs on ordinary HTTP and HTTPS pages in Chrome 114 or newer. Chrome-managed pages such as `chrome://extensions`, the Chrome Web Store, and Chrome's built-in PDF viewer are outside this first version.

PDF support is planned as a dedicated extension-owned reader rather than an attempt to alter Chrome's internal PDF viewer. Local `file://` pages are also excluded for now.

Some sites use browser top-layer UI, embedded cross-origin frames, or unusually aggressive page styles. The guard is isolated in a shadow root and uses no page text, but those browser boundaries can still affect what it covers.

### Privacy and permissions

FocusReader's only named Chrome API permission is `storage`. It also requests site access on HTTP and HTTPS pages so its content script can draw the guard. That site access can technically expose page content to an extension, so the implementation is intentionally narrow: FocusReader does not inspect, retain, or transmit page text or form values. The extension has no analytics and makes no network requests.

See [PRIVACY.md](PRIVACY.md) for the complete current policy.

### Development

The extension uses plain HTML, CSS, and JavaScript. Chrome loads the `chrome` directory directly.

```text
chrome/                    Complete unpacked Chrome extension
  manifest.json            Extension manifest
  src/                     Extension source and popup UI
  scripts/check.mjs        Dependency-free package validation
  test/                    Node built-in tests for shared logic
installer/                 Inno Setup definition
scripts/                   Release packaging scripts
windows/                   Native Windows app and checks
.github/workflows/         CI and tagged-release automation
```

Run the automated checks with Node 20 or newer:

```powershell
npm --prefix chrome test
npm --prefix chrome run check
```

For manual testing guidance, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Windows desktop app

The Windows version provides a system-wide, click-through guard across ordinary desktop applications. It follows the pointer on the active monitor, supports the horizontal guard and click-to-pin behavior, fades when toggled, and stays available from the notification area.

Build it with CMake and a Windows C compiler (Visual Studio's MSVC toolchain is recommended):

```powershell
cmake -S windows -B build\windows
cmake --build build\windows --config Release
.\build\windows\bin\FocusReader.Windows.exe
```

Use `Ctrl+Alt+F` to toggle it globally. Closing the settings window leaves FocusReader running; choose **Exit** from its notification-area menu to stop it.

See [windows/README.md](windows/README.md) for complete build, test, and publishing instructions.

## Releases and installation

The repository includes CI for both implementations and a tagged-release workflow. Pushing a semantic version tag such as `v0.1.0` causes GitHub Actions to test the project and create a GitHub Release containing:

- a per-user Windows x64 installer;
- a portable native Windows ZIP;
- a version-stamped Chrome extension ZIP; and
- SHA-256 checksums for every release asset.

The Windows installer uses Inno Setup 6 and installs to the current user's local application directory without requiring administrator access. To build the same artifacts locally, install CMake, a Windows C compiler, and Inno Setup 6, then run:

```powershell
.\scripts\build-release.ps1 -Version 0.1.0
```

Artifacts are written to `artifacts\`. See [windows/README.md](windows/README.md) for installer details and [chrome/README.md](chrome/README.md) for Chrome packaging details.

Release ZIPs can be loaded manually in Chrome after extraction, but public one-click Chrome installation requires publishing the package through the Chrome Web Store.

## Project status

This is an early alpha intended to establish the interaction model. Expected next steps include accessibility refinement, icons and visual polish, a dedicated PDF reader, site and multi-monitor testing, Windows code signing, and Chrome Web Store submission.


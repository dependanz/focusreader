# Contributing

Thanks for helping make FocusReader more useful and comfortable to read with.

## Development setup

The Chrome extension requires no dependency installation or build step. Use Chrome 114 or newer and Node 20 or newer.

1. Load the repository's `chrome` directory as an unpacked extension from `chrome://extensions`.
2. After changing extension code, select **Reload** on the extension card.
3. Reload the page under test.
4. Run `npm --prefix chrome test` and `npm --prefix chrome run check` before proposing a change.

For Windows development, use Windows 10 or 11 with CMake and a Windows C compiler. Visual Studio's MSVC toolchain is recommended:

```powershell
cmake -S windows -B build\windows
cmake --build build\windows --config Release
ctest --test-dir build\windows -C Release --output-on-failure
```

The Windows app is C17 and uses the Win32 API directly. Its checks have no third-party package dependencies.

Full release packaging also requires Inno Setup 6. Build the same assets produced by the release workflow with:

```powershell
.\scripts\build-release.ps1 -Version 0.1.0
```

Do not commit files from `artifacts\`; they are generated release outputs.

## Manual test checklist

- The extension is off when a supported page first loads.
- The popup can enable and disable the current tab.
- `Alt+Shift+F` toggles the current tab.
- The lower shield follows pointer movement.
- The horizontal guard can be turned on and off.
- Click-to-pin mode places the guard without blocking the page click.
- Color and density changes update an already-enabled page.
- Navigating the tab resets its enabled state.
- The popup explains when a Chrome-managed page is unsupported.
- Page links, selection, scrolling, and form controls still work through the overlay.

Test both light and dark pages and at multiple browser zoom levels. When reporting a compatibility issue, include the site, Chrome version, operating system, and a minimal reproduction if the page is public.

For the Windows app, verify the notification-area controls, `Ctrl+Alt+F`, click-through behavior over several applications, mixed-DPI monitors, click-to-pin mode, and a clean exit from the notification-area menu.

## Code expectations

- Keep the extension dependency-free unless a dependency has a clear security and maintenance justification.
- Do not add remotely hosted executable code.
- Keep the overlay non-interactive so it cannot block page controls.
- Avoid reading page content; FocusReader should depend on pointer and viewport geometry.
- Update documentation and privacy disclosures with behavior changes.


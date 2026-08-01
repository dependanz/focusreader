# FocusReader for Chrome

This directory is the complete Manifest V3 extension source. It has no runtime or build dependencies.

## Load it locally

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Select **Load unpacked**.
4. Choose this `chrome` directory—the directory containing `manifest.json`.

After changing extension code, select **Reload** on the extension card and refresh the page under test.

## Check it

Run from the repository root:

```powershell
npm --prefix chrome test
npm --prefix chrome run check
```

## Package it

The repository release script creates a version-stamped ZIP containing only `manifest.json` and `src/`:

```powershell
.\scripts\build-release.ps1 -Version 0.1.0 -SkipInstaller
```

The generated `artifacts\FocusReader-0.1.0-chrome.zip` is suitable for manual unpacked installation or upload to the Chrome Web Store. Chrome normally requires public consumer extensions to be distributed through the Chrome Web Store; a GitHub Release ZIP is not a one-click Chrome installer.

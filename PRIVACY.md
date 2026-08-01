# Privacy policy

Last updated: July 31, 2026

FocusReader is designed to work locally on your device.

## Data collection

FocusReader does not collect, sell, or transmit personal information, browsing history, page text, or usage analytics.

## Chrome page access

The extension requests access to ordinary HTTP and HTTPS pages and runs a content script on them to:

- observe pointer position;
- observe viewport size; and
- draw the reading guards.

The current implementation does not inspect, copy, store, or transmit page text or form values.
Chrome may describe this site access broadly during installation because content scripts are technically capable of reading a page. FocusReader uses the access only for the pointer, viewport, and overlay behavior listed above.


## Stored preferences

FocusReader stores guard color, density, horizontal-guard preference, and pinning preference with `chrome.storage.sync`. Chrome may synchronize those preferences between browsers signed in to the same Chrome profile, according to the user's Chrome Sync settings.

Whether FocusReader is enabled is kept only in the page itself and is not persisted between navigations.

## Windows app access

The Windows app observes the system pointer position, left-button state, display geometry, and its own global keyboard shortcut. It uses those signals only to position and toggle transparent reading guards. It does not inspect the contents of other application windows.

Windows preferences are stored locally at `%LOCALAPPDATA%\FocusReader\settings.json`. The Windows enabled state is not persisted between launches.

## Network activity

Neither implementation makes network requests or includes analytics, advertising, or remotely hosted code.

## Changes

Material changes to this policy should be documented in this file alongside the corresponding product change.


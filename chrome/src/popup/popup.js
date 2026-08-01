(function initializeFocusReaderPopup() {
  "use strict";

  const preferencesApi = globalThis.FocusReaderPreferences;
  const elements = {
    availabilityMessage: document.querySelector("#availabilityMessage"),
    color: document.querySelector("#color"),
    colorValue: document.querySelector("#colorValue"),
    fixedPosition: document.querySelector("#fixedPosition"),
    horizontalGuard: document.querySelector("#horizontalGuard"),
    opacity: document.querySelector("#opacity"),
    opacityValue: document.querySelector("#opacityValue"),
    statusBadge: document.querySelector("#statusBadge"),
    toggleButton: document.querySelector("#toggleButton")
  };

  let activeTabId = null;
  let enabled = false;
  let available = false;
  let preferences = preferencesApi.normalizePreferences();

  function renderPreferences() {
    elements.horizontalGuard.checked = preferences.horizontalGuard;
    elements.fixedPosition.checked = preferences.fixedPosition;
    elements.opacity.value = String(Math.round(preferences.opacity * 100));
    elements.opacityValue.textContent = `${Math.round(
      preferences.opacity * 100
    )}%`;
    elements.color.value = preferences.color.toLowerCase();
    elements.colorValue.textContent = preferences.color;
  }

  function renderState() {
    elements.toggleButton.disabled = !available;
    elements.toggleButton.textContent = enabled
      ? "Turn off for this tab"
      : "Turn on for this tab";

    if (!available) {
      elements.statusBadge.textContent = "Unavailable";
      elements.statusBadge.dataset.state = "unavailable";
      elements.availabilityMessage.textContent =
        "FocusReader runs on ordinary web pages. Chrome pages and the built-in PDF viewer are not supported yet.";
      return;
    }

    elements.statusBadge.textContent = enabled ? "On" : "Off";
    elements.statusBadge.dataset.state = enabled ? "on" : "off";
    elements.availabilityMessage.textContent = enabled
      ? "Move the pointer down the page to guide the shield."
      : "This tab is ready. FocusReader starts only when you turn it on.";
  }

  function preferencesFromControls() {
    return preferencesApi.normalizePreferences({
      color: elements.color.value,
      opacity: Number(elements.opacity.value) / 100,
      horizontalGuard: elements.horizontalGuard.checked,
      fixedPosition: elements.fixedPosition.checked
    });
  }

  async function savePreferences() {
    preferences = preferencesFromControls();
    renderPreferences();
    await chrome.storage.sync.set({
      [preferencesApi.STORAGE_KEY]: preferences
    });
  }

  elements.opacity.addEventListener("input", function previewOpacity() {
    elements.opacityValue.textContent = `${elements.opacity.value}%`;
  });

  elements.opacity.addEventListener("change", function persistOpacity() {
    savePreferences().catch(function ignoreClosedPopup() {});
  });

  elements.color.addEventListener("input", function previewColor() {
    elements.colorValue.textContent = elements.color.value.toUpperCase();
  });

  elements.color.addEventListener("change", function persistColor() {
    savePreferences().catch(function ignoreClosedPopup() {});
  });

  elements.horizontalGuard.addEventListener("change", function persistGuard() {
    savePreferences().catch(function ignoreClosedPopup() {});
  });

  elements.fixedPosition.addEventListener("change", function persistPinning() {
    savePreferences().catch(function ignoreClosedPopup() {});
  });

  elements.toggleButton.addEventListener("click", async function toggleGuard() {
    if (!available || !Number.isInteger(activeTabId)) {
      return;
    }

    elements.toggleButton.disabled = true;

    try {
      const state = await chrome.tabs.sendMessage(activeTabId, {
        type: "focusreader:set-enabled",
        enabled: !enabled
      });
      enabled = Boolean(state && state.enabled);
    } catch (_error) {
      available = false;
      enabled = false;
    }

    renderState();
  });

  async function initialize() {
    const stored = await chrome.storage.sync.get(preferencesApi.STORAGE_KEY);
    preferences = preferencesApi.normalizePreferences(
      stored[preferencesApi.STORAGE_KEY]
    );
    renderPreferences();

    const tabs = await chrome.tabs.query({
      active: true,
      currentWindow: true
    });
    activeTabId = tabs[0] && tabs[0].id;

    if (!Number.isInteger(activeTabId)) {
      renderState();
      return;
    }

    try {
      const state = await chrome.tabs.sendMessage(activeTabId, {
        type: "focusreader:get-state"
      });
      available = Boolean(state && state.available);
      enabled = Boolean(state && state.enabled);
    } catch (_error) {
      available = false;
      enabled = false;
    }

    renderState();
  }

  initialize().catch(function showInitializationFailure() {
    available = false;
    enabled = false;
    renderPreferences();
    renderState();
  });
})();


(function initializeFocusReaderContentScript() {
  "use strict";

  if (window.top !== window || globalThis.__focusReaderLoaded) {
    return;
  }

  globalThis.__focusReaderLoaded = true;

  const preferencesApi = globalThis.FocusReaderPreferences;
  const geometryApi = globalThis.FocusReaderGeometry;

  if (!preferencesApi || !geometryApi) {
    return;
  }

  const HOST_ID = "focusreader-extension-root";
  let preferences = preferencesApi.normalizePreferences();
  let enabled = false;
  let point = {
    x: Math.round(window.innerWidth / 2),
    y: Math.round(window.innerHeight * 0.45)
  };

  const host = document.createElement("div");
  host.id = HOST_ID;
  host.setAttribute("aria-hidden", "true");
  host.style.setProperty("all", "initial", "important");
  host.style.setProperty("position", "fixed", "important");
  host.style.setProperty("inset", "0", "important");
  host.style.setProperty("display", "block", "important");
  host.style.setProperty("pointer-events", "none", "important");
  host.style.setProperty("overflow", "hidden", "important");
  host.style.setProperty("z-index", "2147483647", "important");
  host.style.setProperty("visibility", "visible", "important");
  host.style.setProperty("--focusreader-opacity", "0");

  const shadowRoot = host.attachShadow({ mode: "closed" });
  const style = document.createElement("style");
  style.textContent = `
    :host {
      color-scheme: light dark;
    }

    .guard {
      position: fixed;
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      border: 0;
      background: var(--focusreader-color, #585e65);
      opacity: var(--focusreader-opacity, 0);
      pointer-events: none;
      transition: opacity 180ms cubic-bezier(0.2, 0, 0, 1);
      will-change: left, top, width, height, opacity;
    }

    @media (prefers-reduced-motion: reduce) {
      .guard {
        transition: none;
      }
    }
  `;

  const verticalGuard = document.createElement("div");
  verticalGuard.className = "guard vertical-guard";

  const horizontalGuard = document.createElement("div");
  horizontalGuard.className = "guard horizontal-guard";

  shadowRoot.append(style, verticalGuard, horizontalGuard);
  document.documentElement.append(host);

  function setRect(element, rect) {
    element.style.left = `${rect.left}px`;
    element.style.top = `${rect.top}px`;
    element.style.width = `${rect.width}px`;
    element.style.height = `${rect.height}px`;
  }

  function render() {
    host.style.setProperty("--focusreader-color", preferences.color);
    host.style.setProperty(
      "--focusreader-opacity",
      enabled ? String(preferences.opacity) : "0"
    );

    if (!enabled) {
      return;
    }

    const rects = geometryApi.calculateGuardRects({
      x: point.x,
      y: point.y,
      width: window.innerWidth,
      height: window.innerHeight
    });

    setRect(verticalGuard, rects.vertical);
    setRect(horizontalGuard, rects.horizontal);
    horizontalGuard.hidden = !preferences.horizontalGuard;
  }

  function reportState() {
    try {
      const pending = chrome.runtime.sendMessage({
        type: "focusreader:state-changed",
        enabled
      });
      if (pending && typeof pending.catch === "function") {
        pending.catch(function ignoreMissingReceiver() {});
      }
    } catch (_error) {
      // The extension may have been reloaded while this page stayed open.
    }
  }

  function setEnabled(nextEnabled, shouldReport) {
    enabled = Boolean(nextEnabled);
    render();

    if (shouldReport) {
      reportState();
    }

    return {
      available: true,
      enabled,
      preferences
    };
  }

  function updatePoint(event) {
    point = {
      x: event.clientX,
      y: event.clientY
    };
    render();
  }

  document.addEventListener(
    "pointermove",
    function handlePointerMove(event) {
      if (!enabled || preferences.fixedPosition) {
        return;
      }

      updatePoint(event);
    },
    { capture: true, passive: true }
  );

  document.addEventListener(
    "pointerdown",
    function handlePointerDown(event) {
      if (!enabled) {
        return;
      }

      if (preferences.fixedPosition || event.pointerType === "touch") {
        updatePoint(event);
      }
    },
    { capture: true, passive: true }
  );

  window.addEventListener("resize", render, { passive: true });

  chrome.runtime.onMessage.addListener(function handleMessage(
    message,
    _sender,
    sendResponse
  ) {
    if (!message || typeof message.type !== "string") {
      return undefined;
    }

    if (message.type === "focusreader:get-state") {
      sendResponse({
        available: true,
        enabled,
        preferences
      });
      return false;
    }

    if (message.type === "focusreader:set-enabled") {
      sendResponse(setEnabled(message.enabled, true));
      return false;
    }

    if (message.type === "focusreader:toggle") {
      sendResponse(setEnabled(!enabled, true));
      return false;
    }

    return undefined;
  });

  chrome.storage.sync
    .get(preferencesApi.STORAGE_KEY)
    .then(function applyStoredPreferences(result) {
      preferences = preferencesApi.normalizePreferences(
        result[preferencesApi.STORAGE_KEY]
      );
      render();
    })
    .catch(function keepDefaultPreferences() {});

  chrome.storage.onChanged.addListener(function handleStorageChange(
    changes,
    areaName
  ) {
    const change = changes[preferencesApi.STORAGE_KEY];
    if (areaName !== "sync" || !change) {
      return;
    }

    preferences = preferencesApi.normalizePreferences(change.newValue);
    render();
  });
})();


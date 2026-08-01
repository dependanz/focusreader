(function initializeFocusReaderPreferences(globalScope) {
  "use strict";

  const STORAGE_KEY = "preferences";
  const MIN_OPACITY = 0.4;

  const DEFAULTS = Object.freeze({
    color: "#585E65",
    opacity: 1,
    horizontalGuard: true,
    fixedPosition: false
  });

  function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
  }

  function normalizeColor(value) {
    if (typeof value !== "string" || !/^#[0-9a-f]{6}$/i.test(value)) {
      return DEFAULTS.color;
    }

    return value.toUpperCase();
  }

  function normalizePreferences(value) {
    const source = value && typeof value === "object" ? value : {};
    const parsedOpacity = Number(source.opacity);

    return {
      color: normalizeColor(source.color),
      opacity: Number.isFinite(parsedOpacity)
        ? clamp(parsedOpacity, MIN_OPACITY, 1)
        : DEFAULTS.opacity,
      horizontalGuard:
        typeof source.horizontalGuard === "boolean"
          ? source.horizontalGuard
          : DEFAULTS.horizontalGuard,
      fixedPosition:
        typeof source.fixedPosition === "boolean"
          ? source.fixedPosition
          : DEFAULTS.fixedPosition
    };
  }

  globalScope.FocusReaderPreferences = Object.freeze({
    DEFAULTS,
    MIN_OPACITY,
    STORAGE_KEY,
    normalizePreferences
  });
})(globalThis);


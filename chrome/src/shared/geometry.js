(function initializeFocusReaderGeometry(globalScope) {
  "use strict";

  const DEFAULT_LINE_HEIGHT = 30;
  const DEFAULT_CLEARANCE = 6;

  function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
  }

  function finiteOr(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function calculateGuardRects(input) {
    const width = Math.max(0, finiteOr(input && input.width, 0));
    const height = Math.max(0, finiteOr(input && input.height, 0));
    const x = clamp(finiteOr(input && input.x, width / 2), 0, width);
    const y = clamp(finiteOr(input && input.y, height / 2), 0, height);
    const lineHeight = Math.max(
      0,
      finiteOr(input && input.lineHeight, DEFAULT_LINE_HEIGHT)
    );
    const clearance = Math.max(
      0,
      finiteOr(input && input.clearance, DEFAULT_CLEARANCE)
    );

    const shieldTop = clamp(y + clearance, 0, height);
    const horizontalTop = clamp(y - lineHeight, 0, shieldTop);

    return {
      vertical: {
        left: 0,
        top: shieldTop,
        width,
        height: Math.max(0, height - shieldTop)
      },
      horizontal: {
        left: x,
        top: horizontalTop,
        width: Math.max(0, width - x),
        height: Math.max(0, shieldTop - horizontalTop)
      }
    };
  }

  globalScope.FocusReaderGeometry = Object.freeze({
    DEFAULT_CLEARANCE,
    DEFAULT_LINE_HEIGHT,
    calculateGuardRects
  });
})(globalThis);


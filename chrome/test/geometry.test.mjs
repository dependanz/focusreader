import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const source = await readFile(
  new URL("../src/shared/geometry.js", import.meta.url),
  "utf8"
);
const context = vm.createContext({});
vm.runInContext(source, context);
const geometryApi = context.FocusReaderGeometry;

function plain(value) {
  return JSON.parse(JSON.stringify(value));
}

test("builds a lower shield and current-line guard", () => {
  assert.deepEqual(
    plain(
      geometryApi.calculateGuardRects({
        x: 400,
        y: 300,
        width: 1000,
        height: 800,
        lineHeight: 30,
        clearance: 6
      })
    ),
    {
      vertical: {
        left: 0,
        top: 306,
        width: 1000,
        height: 494
      },
      horizontal: {
        left: 400,
        top: 270,
        width: 600,
        height: 36
      }
    }
  );
});

test("clamps pointer coordinates to the viewport", () => {
  const rects = geometryApi.calculateGuardRects({
    x: -20,
    y: 900,
    width: 1000,
    height: 800
  });

  assert.deepEqual(plain(rects.vertical), {
    left: 0,
    top: 800,
    width: 1000,
    height: 0
  });
  assert.equal(rects.horizontal.left, 0);
  assert.equal(rects.horizontal.width, 1000);
});

test("handles an empty viewport without negative dimensions", () => {
  const rects = geometryApi.calculateGuardRects({
    x: 10,
    y: 10,
    width: 0,
    height: 0
  });

  assert.deepEqual(plain(rects), {
    vertical: { left: 0, top: 0, width: 0, height: 0 },
    horizontal: { left: 0, top: 0, width: 0, height: 0 }
  });
});


import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const source = await readFile(
  new URL("../src/shared/preferences.js", import.meta.url),
  "utf8"
);
const context = vm.createContext({});
vm.runInContext(source, context);
const preferencesApi = context.FocusReaderPreferences;

function plain(value) {
  return JSON.parse(JSON.stringify(value));
}

test("uses the documented defaults", () => {
  assert.deepEqual(plain(preferencesApi.normalizePreferences()), {
    color: "#585E65",
    opacity: 1,
    horizontalGuard: true,
    fixedPosition: false
  });
});

test("normalizes valid values", () => {
  assert.deepEqual(
    plain(
      preferencesApi.normalizePreferences({
        color: "#abcdef",
        opacity: 0.72,
        horizontalGuard: false,
        fixedPosition: true
      })
    ),
    {
      color: "#ABCDEF",
      opacity: 0.72,
      horizontalGuard: false,
      fixedPosition: true
    }
  );
});

test("clamps density and rejects malformed values", () => {
  assert.equal(preferencesApi.normalizePreferences({ opacity: 3 }).opacity, 1);
  assert.equal(
    preferencesApi.normalizePreferences({ opacity: 0.1 }).opacity,
    preferencesApi.MIN_OPACITY
  );
  assert.equal(
    preferencesApi.normalizePreferences({ color: "red" }).color,
    preferencesApi.DEFAULTS.color
  );
});


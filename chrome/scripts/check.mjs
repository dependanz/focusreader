import { readFile, readdir } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const manifestPath = path.join(root, "manifest.json");
const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
const errors = [];

function check(condition, message) {
  if (!condition) {
    errors.push(message);
  }
}

async function fileExists(relativePath) {
  try {
    await readFile(path.join(root, relativePath));
    return true;
  } catch (_error) {
    return false;
  }
}

async function listFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await listFiles(fullPath)));
    } else {
      files.push(fullPath);
    }
  }

  return files;
}

check(manifest.manifest_version === 3, "manifest_version must be 3");
check(Boolean(manifest.name), "manifest name is required");
check(/^\d+\.\d+\.\d+$/.test(manifest.version), "version must be x.y.z");
check(
  Array.isArray(manifest.permissions) &&
    manifest.permissions.length === 1 &&
    manifest.permissions[0] === "storage",
  "storage should be the only API permission"
);

const referencedFiles = new Set([
  manifest.action && manifest.action.default_popup,
  manifest.background && manifest.background.service_worker
]);

for (const contentScript of manifest.content_scripts || []) {
  for (const script of contentScript.js || []) {
    referencedFiles.add(script);
  }
  for (const stylesheet of contentScript.css || []) {
    referencedFiles.add(stylesheet);
  }
}

for (const relativePath of referencedFiles) {
  check(
    typeof relativePath === "string" && (await fileExists(relativePath)),
    `manifest references missing file: ${relativePath}`
  );
}

const sourceFiles = (await listFiles(path.join(root, "src"))).filter((file) =>
  file.endsWith(".js")
);

for (const sourceFile of sourceFiles) {
  const syntax = spawnSync(process.execPath, ["--check", sourceFile], {
    encoding: "utf8"
  });
  check(
    syntax.status === 0,
    `${path.relative(root, sourceFile)} has invalid JavaScript syntax:\n${syntax.stderr}`
  );

  const source = await readFile(sourceFile, "utf8");
  check(
    !/https?:\/\//i.test(source),
    `${path.relative(root, sourceFile)} contains a remote URL`
  );
}

const popupHtml = await readFile(
  path.join(root, manifest.action.default_popup),
  "utf8"
);
check(!/<script[^>]+src=["']https?:/i.test(popupHtml), "popup loads remote code");
check(!/<script(?![^>]+src=)[^>]*>/i.test(popupHtml), "popup uses inline JavaScript");

if (errors.length > 0) {
  console.error("FocusReader package validation failed:\n");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exitCode = 1;
} else {
  console.log(
    `FocusReader package validation passed (${sourceFiles.length} JavaScript files checked).`
  );
}


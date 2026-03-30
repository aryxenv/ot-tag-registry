#!/usr/bin/env node
/**
 * Export an Excalidraw JSON file to a dark-mode PNG.
 *
 * Pipeline: .excalidraw → Kroki.io (SVG) → @resvg/resvg-js (PNG)
 *
 * Usage:
 *   node scripts/export-excalidraw.mjs <input.excalidraw> [output.png]
 *
 * If output is omitted, the PNG is written to diagrams/export/<name>.png
 */

const fs = require("fs");
const path = require("path");
const https = require("https");
const { Resvg } = require("@resvg/resvg-js");

const DARK_BG = "#000000";
const PNG_WIDTH = 1600;
const KROKI_URL = "https://kroki.io/excalidraw/svg";

function fetchSvg(excalidrawJson) {
  return new Promise((resolve, reject) => {
    const url = new URL(KROKI_URL);
    const options = {
      hostname: url.hostname,
      path: url.pathname,
      method: "POST",
      headers: { "Content-Type": "text/plain" },
    };

    const req = https.request(options, (res) => {
      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => {
        const body = Buffer.concat(chunks).toString("utf8");
        if (res.statusCode !== 200) {
          reject(new Error(`Kroki returned ${res.statusCode}: ${body.slice(0, 200)}`));
        } else {
          resolve(body);
        }
      });
    });

    req.on("error", reject);
    req.write(excalidrawJson);
    req.end();
  });
}

function svgToPng(svg) {
  const resvg = new Resvg(svg, {
    fitTo: { mode: "width", value: PNG_WIDTH },
    background: DARK_BG,
  });
  const rendered = resvg.render();
  return { buffer: rendered.asPng(), width: rendered.width, height: rendered.height };
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error("Usage: node scripts/export-excalidraw.mjs <input.excalidraw> [output.png]");
    process.exit(1);
  }

  const inputPath = path.resolve(args[0]);
  if (!fs.existsSync(inputPath)) {
    console.error(`File not found: ${inputPath}`);
    process.exit(1);
  }

  const baseName = path.basename(inputPath, path.extname(inputPath));
  const outputPath = args[1]
    ? path.resolve(args[1])
    : path.resolve("excalidraw", "diagrams", "export", `${baseName}.png`);

  // Ensure the Excalidraw JSON includes dark theme settings
  const raw = fs.readFileSync(inputPath, "utf8");
  let json;
  try {
    json = JSON.parse(raw);
  } catch {
    console.error("Invalid JSON in input file");
    process.exit(1);
  }

  json.appState = json.appState || {};
  json.appState.theme = "dark";
  json.appState.viewBackgroundColor = DARK_BG;

  // Kroki's Excalidraw renderer ignores text elements that have containerId
  // (bound/label text). Unbind them so they render as standalone text at
  // their existing x/y position, which is already centered by Excalidraw.
  const wasContainerText = new Set();
  for (const el of json.elements || []) {
    if (el.type === "text" && el.containerId) {
      wasContainerText.add(el.id);
      delete el.containerId;
    }
    // Remove boundElements text references from shapes
    if (el.boundElements) {
      el.boundElements = el.boundElements.filter((b) => b.type !== "text");
    }
  }

  // Ensure standalone text (titles, annotations) is visible on the dark bg.
  // Originally-container text keeps its dark color — it sits on colored fills.
  const BG_COLORS = new Set(["#000000", "#000", "#1e1e1e", "#1e1e2e", "#191919", "#121212"]);
  const LIGHT_TEXT = "#e0e0e0";
  let fixed = 0;
  for (const el of json.elements || []) {
    if (el.type === "text" && !wasContainerText.has(el.id) && BG_COLORS.has((el.strokeColor || "").toLowerCase())) {
      el.strokeColor = LIGHT_TEXT;
      fixed++;
    }
  }
  if (fixed > 0) {
    console.log(`  Fixed ${fixed} standalone text element(s) → ${LIGHT_TEXT}`);
  }

  const excalidrawJson = JSON.stringify(json);

  console.log(`Exporting: ${path.basename(inputPath)} → ${path.relative(".", outputPath)}`);
  console.log("  Fetching SVG from Kroki.io...");
  const svg = await fetchSvg(excalidrawJson);

  console.log("  Converting SVG → PNG...");
  const { buffer, width, height } = svgToPng(svg);

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, buffer);
  console.log(`  Done: ${width}×${height}, ${(buffer.length / 1024).toFixed(1)} KB`);
}

main().catch((err) => {
  console.error("Export failed:", err.message);
  process.exit(1);
});

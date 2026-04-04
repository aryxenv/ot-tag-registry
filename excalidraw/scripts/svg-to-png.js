#!/usr/bin/env node
/**
 * Convert an SVG file to a dark-mode PNG using @resvg/resvg-js.
 *
 * Usage:
 *   node scripts/svg-to-png.js <input.svg> [output.png]
 *
 * If output is omitted, the PNG is written next to the SVG with a .png extension.
 *
 * Designed for the MCP SVG export pipeline:
 *   1. Export SVG from Excalidraw MCP (`export_scene format="svg"`)
 *   2. Save SVG to excalidraw/diagrams/export/<name>.svg
 *   3. Run this script to produce a 1600px-wide dark-mode PNG
 */

const fs = require("fs");
const path = require("path");
const { Resvg } = require("@resvg/resvg-js");

const DARK_BG = "#0d1117";
const PNG_WIDTH = 1600;

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error("Usage: node scripts/svg-to-png.js <input.svg> [output.png]");
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
    : path.join(path.dirname(inputPath), `${baseName}.png`);

  const svg = fs.readFileSync(inputPath, "utf8");

  console.log(`Converting: ${path.basename(inputPath)} → ${path.relative(".", outputPath)}`);

  const resvg = new Resvg(svg, {
    fitTo: { mode: "width", value: PNG_WIDTH },
    background: DARK_BG,
  });
  const rendered = resvg.render();
  const buffer = rendered.asPng();

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, buffer);
  console.log(`  Done: ${rendered.width}×${rendered.height}, ${(buffer.length / 1024).toFixed(1)} KB`);
}

main();

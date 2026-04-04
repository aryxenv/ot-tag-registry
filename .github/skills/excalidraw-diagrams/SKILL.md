---
name: excalidraw-diagrams
description: "Create, update, and export architecture diagrams using Excalidraw MCP. Use when: diagram, architecture diagram, visualize, draw system, illustrate flow, create diagram, update diagram, export diagram, add diagram to README."
---

# Excalidraw Diagrams

Create architecture and flow diagrams via the Excalidraw MCP server, export them to PNG, and embed them in docs.

## When to Use

- User asks for a diagram, architecture visual, or flow illustration
- User asks to visualize a system, data flow, or component relationship
- User asks to add a diagram to a README or doc
- Any request involving "diagram", "draw", "visualize", "illustrate"

## Workspace Layout

```
excalidraw/
├── diagrams/                # .excalidraw source files
│   └── export/              # Exported PNGs (gitignored or committed)
├── scripts/
│   └── export-excalidraw.js # Kroki → resvg export pipeline
└── package.json             # Has @resvg/resvg-js dependency
```

## MCP Server

The Excalidraw MCP server is configured in `.vscode/mcp.json`:

```json
{
  "excalidraw": {
    "command": "npx.cmd",
    "args": ["-y", "excalidraw-mcp-server"]
  }
}
```

Always use MCP tools (prefixed `mcp_excalidraw_*`) to create and manipulate diagrams. **Never hand-write Excalidraw JSON.**

## Procedure

### Step 1 — Plan the Diagram

Before touching any tool, decide:

- **Type**: Architecture overview, data flow, sequence, component relationship
- **Elements**: List the boxes, labels, arrows, and groupings needed
- **Layout**: Left-to-right for flows, top-to-bottom for hierarchies, grid for components

### Step 2 — Create the Diagram with MCP

1. Call `mcp_excalidraw_create_view` to set up a new canvas if needed.
2. Use `mcp_excalidraw_batch_create_elements` to place all elements at once (faster than individual creates).
3. Use `mcp_excalidraw_create_element` for one-off additions.
4. Organize with `mcp_excalidraw_group_elements`, `mcp_excalidraw_align_elements`, and `mcp_excalidraw_distribute_elements`.
5. Lock finished sections with `mcp_excalidraw_lock_elements`.

#### Element Cheat Sheet

| Element     | Use For                          | MCP Type  |
| ----------- | -------------------------------- | --------- |
| `rectangle` | Services, containers, components | Shape     |
| `ellipse`   | Start/end nodes, badges          | Shape     |
| `diamond`   | Decision points                  | Shape     |
| `arrow`     | Data flow, relationships         | Connector |
| `text`      | Titles, annotations              | Label     |

#### Color Palette (Excalidraw defaults)

| Color      | Hex       | Use For                   |
| ---------- | --------- | ------------------------- |
| Blue       | `#1971c2` | Primary services, APIs    |
| Green      | `#2f9e44` | Databases, storage        |
| Orange     | `#e67700` | External services, AI     |
| Purple     | `#6741d9` | Agents, orchestration     |
| Gray       | `#868e96` | Infrastructure, secondary |
| Light Blue | `#d0ebff` | Container backgrounds     |

#### Sizing

- **Spacing**: 40–60px between elements
- **Text padding**: 20px inside rectangles
- **Arrow gap**: 10px from source/target edges
- **Font sizes**: Title 28px, heading 22px, body 16px, caption 12px
- **Min width**: 80px for readability

### Step 3 — Export to PNG via the Script

After the diagram is finalized in Excalidraw, export it using the [export script](../../excalidraw/scripts/export-excalidraw.js):

```bash
cd excalidraw && npm install   # ensure @resvg/resvg-js is installed
node scripts/export-excalidraw.js diagrams/<name>.excalidraw
```

This produces a dark-mode PNG at `excalidraw/diagrams/export/<name>.png` (1600px wide).

To specify a custom output path:

```bash
node scripts/export-excalidraw.js diagrams/<name>.excalidraw diagrams/export/custom-name.png
```

### Step 4 — Save the .excalidraw Source

Use `mcp_excalidraw_export_scene` to get the raw JSON, then save it to `excalidraw/diagrams/<name>.excalidraw`. This keeps the source editable for future updates.

### Step 5 — Embed in Documentation

Reference the exported PNG using a **relative path** from the doc's location:

```markdown
<!-- From project root README.md -->

![Architecture](excalidraw/diagrams/export/architecture.png)

<!-- From client/README.md -->

![Architecture](../excalidraw/diagrams/export/architecture.png)

<!-- From server/README.md -->

![Architecture](../excalidraw/diagrams/export/architecture.png)
```

Always use the `excalidraw/diagrams/export/` path — never link to `.excalidraw` source files in rendered docs.

## Updating an Existing Diagram

1. Query existing elements with `mcp_excalidraw_query_elements`.
2. Modify with `mcp_excalidraw_update_element` or `mcp_excalidraw_delete_element`.
3. Re-export using Step 3 above (overwrites the previous PNG).
4. No doc changes needed if the filename stays the same.

## Conventions

- **File naming**: Lowercase kebab-case (e.g., `data-flow.excalidraw`, `tag-lifecycle.excalidraw`)
- **Roughness**: Use `0` for clean technical diagrams, `1` for informal sketches
- **Theme**: Export script forces dark mode — design with that in mind (use bright fills, light text)
- **One diagram per file** — don't combine unrelated visuals

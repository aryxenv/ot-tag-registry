---
name: fluent-ui
description: Enforces Fluent UI v9 as the component library for all frontend work. Covers theming, component selection, styling patterns, and the MCP server for looking up components. Use this when building or modifying any client UI.
---

# Fluent UI — Frontend Component Library

## MCP Server

This repo has a **Fluent UI MCP server** configured in `.vscode/mcp.json`:

```json
{
  "servers": {
    "fluent-ui": {
      "command": "npx.cmd",
      "args": ["mcp-fluent-ui"]
    }
  }
}
```

**Use the `mcp-fluent-ui` MCP server tools** when you need to:
- Look up which Fluent UI component to use for a given UI pattern
- Check component props, slots, and usage examples
- Find the right icon from `@fluentui/react-icons`

Always consult the MCP server before reaching for custom implementations. If Fluent UI has a component for it, use it.

## Required Packages

```
@fluentui/react-components   # All UI components + theming
@fluentui/react-icons         # Icon set
```

Do **not** install `@fluentui/react` (v8) — the project uses v9 exclusively.

## Theme

The app uses a **custom GitHub-style dark theme** defined in `apps/client/src/theme.ts`.

Key colors:
| Token | Value | Usage |
|-------|-------|-------|
| `colorNeutralBackground1` | `#0d1117` | Page background |
| `colorNeutralBackground2` | `#161b22` | Cards, sidebar, surfaces |
| `colorNeutralBackground3` | `#21262d` | Hover states, elevated surfaces |
| `colorNeutralStroke1` | `#30363d` | Borders |
| `colorNeutralForeground1` | `#e6edf3` | Primary text |
| `colorNeutralForeground2` | `#8b949e` | Secondary text |
| `colorBrandForegroundLink` | `#58a6ff` | Links, brand accent |

The brand ramp is built around `#58a6ff` (GitHub blue).

### Rules
- **Dark mode first.** The app ships with a dark theme. All UI must look correct against dark backgrounds.
- Use `tokens` from `@fluentui/react-components` for colors — never hardcode colors unless extending the theme.
- The theme is applied via `<FluentProvider theme={contosoTheme}>` in `main.tsx`.

## Styling

Use **`makeStyles`** from `@fluentui/react-components` for all custom styles.

```tsx
import { makeStyles, tokens } from '@fluentui/react-components'

const useStyles = makeStyles({
  container: {
    padding: '16px',
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: '8px',
    border: `1px solid ${tokens.colorNeutralStroke1}`,
  },
})
```

### Rules
- Use `makeStyles` — not CSS files, inline styles, or other CSS-in-JS libraries.
- Reference theme tokens (`tokens.colorNeutralBackground1`, etc.) instead of raw hex values.
- Hardcoded colors are acceptable only for brand-specific overrides already defined in `theme.ts`.

## Component Patterns

### Typography
Use Fluent text components — not raw HTML headings or `<p>` tags:
```tsx
import { Title1, Title2, Title3, Subtitle1, Text } from '@fluentui/react-components'

<Title1>Page Title</Title1>
<Text size={300}>Description text</Text>
```

### Icons
Import from `@fluentui/react-icons`. Use `Regular` weight by default, `Filled` for active states:
```tsx
import { BoardRegular, BoardFilled } from '@fluentui/react-icons'
```

### Layout
Use Fluent primitives and `makeStyles` with flexbox — not CSS grid frameworks or layout libraries.

## What NOT to do

- ❌ Install or use `@fluentui/react` (v8) — we use v9 (`@fluentui/react-components`)
- ❌ Use CSS files for component styling — use `makeStyles`
- ❌ Hardcode colors without referencing `tokens`
- ❌ Use raw HTML elements (`<h1>`, `<button>`, `<input>`) when a Fluent component exists
- ❌ Build custom components for patterns Fluent UI already provides — check the MCP server first
- ❌ Use light theme defaults — all UI must be dark-mode compatible

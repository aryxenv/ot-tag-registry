---
name: custom-agents
description: Defines the template, conventions, and quality bar for authoring GitHub Copilot custom agents (.agent.md files). Covers standalone agents, nested orchestrations, tool selection, and Contoso-specific rules. Use this when creating, reviewing, or modifying any agent in .github/agents/.
---

# Custom Agents — Authoring Guide

## Golden Rule

**All custom agents in this project MUST be `.agent.md` files inside `.github/agents/`.** Do not place agent files anywhere else in the repo. Each file defines one agent persona with scoped tools, clear boundaries, and actionable instructions.

## File Location & Naming

```
.github/
  agents/
    backend-reviewer.agent.md      ← standalone agent
    test-writer.agent.md           ← standalone agent
    feature-builder.agent.md       ← orchestrator agent
    fb--planner.agent.md           ← subagent (prefixed by orchestrator initials)
    fb--implementer.agent.md       ← subagent
    fb--tester.agent.md            ← subagent
    README.md                      ← directory overview
```

### Naming rules

- **Kebab-case** filenames — lowercase, hyphens, no spaces or underscores.
- Names must be **descriptive** — a reader should know the agent's role from the filename alone.
- Subagents are prefixed with their orchestrator's initials and a double-dash (`fb--planner`). This groups them visually and prevents name collisions.

## Frontmatter Reference

Every `.agent.md` starts with a YAML frontmatter block. Here are all supported fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Display name shown in the agent picker. |
| `description` | string | Yes | One-line summary of the agent's purpose. Shown in UI dropdowns. |
| `tools` | string[] | Yes | Tools this agent is allowed to use. **Always restrict to the minimum set needed.** |
| `model` | string | No | Preferred AI model (e.g., `gpt-4o`, `claude-sonnet-4-20250514`). Defaults to session model if omitted. |
| `agents` | string[] | Orchestrators only | Names of subagents this agent can invoke. |
| `user-invokable` | boolean | No | Whether the agent appears in the user picker. Set `false` for subagents. Default: `true`. |
| `handoffs` | object[] | No | Pre-configured transitions to other agents. See [Handoffs](#handoffs). |
| `argument-hint` | string | No | Placeholder suggestion shown in the chat input. |
| `disable-model-invocation` | boolean | No | Prevents other agents from delegating to this agent autonomously. Default: `false`. |

### Tool reference

Grant only what the agent needs:

| Tool | Capability | Typical use |
|------|-----------|-------------|
| `read` | View files and directories | All agents that need code context |
| `edit` | Modify files | Agents that write or refactor code |
| `search` | Find references, symbols, text | Code navigation and analysis |
| `terminal` | Execute shell commands | Build, test, lint runners |
| `github` | Interact with GitHub (issues, PRs) | PR-aware agents |
| `test` | Run or analyze test suites | QA and testing agents |
| `agent` | Invoke or hand off to other agents | Orchestrators |

## Optimized Agent Template

Use this template when creating any new agent. The sections are ordered top-down: **identity → role → boundaries → workflows → examples**. This mirrors how effective prompts are structured — context first, then constraints, then action.

````markdown
---
name: <kebab-case-name>
description: "<One clear sentence describing what this agent does.>"
tools: [<minimum required tools>]
model: <optional — omit to use session default>
---

# Role

<1–2 sentences: Who is this agent? What is its expertise?>

# Responsibilities

<Bulleted list of what this agent DOES. Be specific — vague instructions produce vague results.>

- Do X when Y
- Always check Z before committing
- Run `command` after every change

# Boundaries

<What this agent must NEVER do. Be explicit — agents follow boundaries more reliably than open-ended instructions.>

- **Never** edit files outside `<scope>/`
- **Never** commit directly to `main`
- **Never** modify production configuration
- **Never** expose secrets or credentials in output

# Workflows & Commands

<Concrete commands and sequences the agent should use. Show exact commands, not descriptions.>

```bash
# Lint before committing
cd apps/server && uv run ruff check src/ tests/

# Run tests
uv run pytest tests/ -v
```

# Output Examples

<Show what good output looks like. Agents learn patterns better from examples than from rules.>

```<language>
// Example of the expected code style or output format
```
````

## Nested Agents & Orchestration

Use nested agents when a workflow has **distinct phases** that benefit from specialized personas (e.g., plan → implement → test). Do not use nested agents for simple, single-purpose tasks — a standalone agent is better.

### When to use nested agents

| Pattern | Use nested agents | Use standalone agent |
|---------|-------------------|---------------------|
| Multi-phase workflow (plan → build → test) | ✅ | |
| Single focused task (review code, write tests) | | ✅ |
| Tasks requiring different tool sets per phase | ✅ | |
| Simple read-only analysis | | ✅ |

### Orchestrator template

The orchestrator coordinates subagents. It should have `agent` in its tools and list its subagents by name.

````markdown
---
name: feature-builder
description: "Orchestrates feature development: planning, implementation, and testing."
tools: [agent, read, search]
agents:
  - fb--planner
  - fb--implementer
  - fb--tester
---

# Role

You are a development lead that coordinates feature delivery by delegating to specialized subagents.

# Workflow

1. **Plan** — Delegate to `fb--planner` to analyze requirements and produce a plan.
2. **Implement** — Send the plan to `fb--implementer` to write the code.
3. **Test** — Hand off to `fb--tester` to write and run tests.
4. **Review** — Verify all phases completed successfully. Summarize the result.

# Boundaries

- **Never** write code yourself — always delegate to the appropriate subagent.
- **Never** skip the testing phase.
- If a subagent fails, retry once with clarified instructions before reporting the failure.
````

### Subagent template

Subagents are focused workers. They set `user-invokable: false` so they don't clutter the agent picker.

````markdown
---
name: fb--implementer
description: "Writes feature code following Contoso Finance conventions."
tools: [read, edit, search, terminal]
user-invokable: false
---

# Role

You are a senior developer implementing features in the Contoso Finance codebase.

# Responsibilities

- Write code that follows domain module structure (model → repository → service → router)
- Use `uv` for all Python operations, Fluent UI v9 for all frontend work
- Run linters after every change: `cd apps/server && uv run ruff check src/ tests/`

# Boundaries

- **Never** create new domain modules without explicit instruction
- **Never** modify shared infrastructure without approval
- **Never** skip linting
````

### Handoffs

Handoffs let an agent transition work to another agent with context:

```yaml
handoffs:
  - label: "Send to reviewer"
    agent: backend-reviewer
    prompt: "Implementation is complete. Please review for correctness and security."
    send: [context, files]
```

| Field | Description |
|-------|-------------|
| `label` | Button text shown in chat UI |
| `agent` | Target agent name |
| `prompt` | Instructions sent to the target agent |
| `send` | What context to forward (`context`, `files`) |

## Tool Selection by Role

Common agent archetypes and their recommended tool sets:

| Agent role | Tools | Rationale |
|-----------|-------|-----------|
| Code reviewer | `read`, `search` | Read-only — reviewers should not edit code |
| Test writer | `read`, `edit`, `search`, `terminal` | Needs to write tests and run them |
| Full-stack developer | `read`, `edit`, `search`, `terminal` | Needs full file and shell access |
| Documentation writer | `read`, `edit`, `search` | No shell needed for docs |
| PR manager | `read`, `search`, `github` | Needs GitHub API access |
| Orchestrator | `agent`, `read`, `search` | Delegates work, reads for context |

**Principle of least privilege** — start with the minimum tool set and add only when the agent demonstrably needs it.

## Contoso Finance-Specific Rules

Agents in this repo must respect the existing conventions:

- **Domain alignment** — If an agent targets a specific domain (`billing`, `payments`, `reporting`, `settlements`), state this explicitly in its Role section. Do not create agents that blur domain boundaries.
- **Python tooling** — Any agent that runs Python commands must use `uv run` and `uv pip`, never raw `pip` or `python -m`.
- **Frontend UI** — Any agent that writes frontend code must follow the `skills/fluent-ui/SKILL.md` conventions (Fluent UI v9, `makeStyles`, dark theme tokens).
- **Git workflow** — Any agent that creates commits or PRs must follow `skills/git-workflow/SKILL.md` (conventional commits, branch naming, lint before push).
- **Testing** — Agents that write tests must use `pytest` for server and the existing test setup for client. Never assume SQLite — the server uses PostgreSQL.
- **Shared types** — If an agent modifies API contracts, it must update `packages/shared-types/` accordingly.

## Quality Checklist

Before committing a new agent, verify:

- [ ] File is in `.github/agents/` with a `.agent.md` extension
- [ ] Filename is kebab-case and descriptive
- [ ] Frontmatter has `name`, `description`, and `tools` at minimum
- [ ] `tools` list follows least-privilege — no unnecessary permissions
- [ ] Role section clearly states who the agent is
- [ ] Boundaries section explicitly states what the agent must NOT do
- [ ] Commands use exact syntax (not vague descriptions)
- [ ] Subagents have `user-invokable: false`
- [ ] Orchestrators list their subagents in the `agents` field
- [ ] Agent respects Contoso Finance conventions (uv, Fluent UI, conventional commits)

## What NOT to Do

- ❌ Place agent files outside `.github/agents/`
- ❌ Create agents without a `description` — the picker becomes useless
- ❌ Grant `edit` or `terminal` to read-only agents (reviewers, analyzers)
- ❌ Write vague instructions like "help with code" — be specific about what the agent does and does not do
- ❌ Create nested agents for simple, single-purpose tasks — use a standalone agent instead
- ❌ Forget `user-invokable: false` on subagents — they pollute the agent picker
- ❌ Skip the Boundaries section — agents without explicit constraints will overstep
- ❌ Use raw `pip`, `python -m`, or CSS files — follow repo conventions
- ❌ Create agents that span multiple domains without justification
- ❌ Name subagents without their orchestrator prefix — use `<prefix>--<role>` format

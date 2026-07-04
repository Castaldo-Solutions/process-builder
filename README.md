# Process Builder — AI Skill for Business Process Diagrams

An open-source [Claude Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) that turns a conversation about a business process into a professional **swimlane diagram** in [draw.io / diagrams.net](https://www.diagrams.net/) format, using a hybrid **BPMN 2.0** notation with a curated palette.

> **Note:** the skill content (prompts, interview guides, generated labels) is in **Italian**, as it was designed for process-mapping interviews with Italian-speaking teams. The generator script and its JSON schema are language-agnostic — diagrams can be produced in any language.

## What it does

- **AS-IS mode** — interviews the user about how a process works today (who does what, when, with which tool, where it hurts) and produces a diagram with actors as lanes, BPMN gateways for decisions, tool annotations, and **pain points** highlighted outside the flow.
- **TO-BE mode** — starting from an AS-IS, proposes an optimized process in two variants: **Quick Win** (2–4 weeks, light automation) and **Full Automation** (deep integrations), with automated/new tasks visually marked.
- The agent is required to **ask questions before drawing**: it never generates a diagram until it knows who does what, in which order, with which tool, and which decisions exist and what they depend on.

## How it works

The agent never writes draw.io XML by hand. It produces a small JSON description of the process and runs:

```bash
python scripts/generate_swimlane.py process.json process.drawio
```

The script handles layout (columns, lanes, phases, multi-row pain points), BPMN shapes, escaping, an optional legend — and validates the JSON first, with actionable error messages (duplicate ids, orphan connections, unknown actors...). Gateway exits are automatically routed on distinct sides of the diamond so arrows never overlap.

```bash
python scripts/generate_swimlane.py process.json --validate   # check only
python scripts/generate_swimlane.py process.json out.drawio --strict  # warnings block too
```

Requirements: **Python ≥ 3.9**, no third-party dependencies.

## Repository layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | The skill entry point: workflows, hard rules, quality checklist |
| `references/interview-guide.md` | How to run the AS-IS / TO-BE interview, and when a process deserves multiple phases |
| `references/style-guide.md` | Visual style: shapes, palette, BPMN conventions |
| `references/drawio-xml-guide.md` | JSON input schema for the generator script |
| `scripts/generate_swimlane.py` | JSON → .drawio generator (validation + layout) |
| `examples/` | Ready-to-run example JSONs (single phase, 3 phases with link events, TO-BE with info panels) |
| `evals/` | Evaluation scenarios used to test the skill |

## Try it in 30 seconds

```bash
python scripts/generate_swimlane.py examples/richiesta_ferie_as_is.json ferie.drawio
```

Open `ferie.drawio` in [app.diagrams.net](https://app.diagrams.net/) or in draw.io Desktop.

## Using it as a Claude Skill

Copy this repository into a `process-builder` folder inside your Claude skills directory (or package it as `process-builder.skill`), then ask something like:

> "Let's map our order-management process: draw the AS-IS."

The agent will interview you, confirm the reconstruction, and hand you the `.drawio` file.

## License

[MIT](LICENSE) — use it, fork it, ship it.

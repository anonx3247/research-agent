# Local Research Agent

A deliberately small deep-research launcher for the locally installed Hermes Agent. It uses one Hermes profile with explicit provider routing:

| Mode | Planner/verifier/synthesizer | Researchers | Data policy |
|---|---|---|---|
| `private` | Tinfoil `kimi-k2-6` | Tinfoil `gpt-oss-120b` | Local, private, library, and public sources |
| `open` | OpenRouter `deepseek/deepseek-v4-pro` | OpenRouter `deepseek/deepseek-v4-flash-0731` | Public question and public web sources only |

The workflow is intentionally fixed:

1. One Hermes parent session creates exactly three independent assignments.
2. It calls native `delegate_task` once to run three cheap leaf subagents in parallel.
3. The same parent verifies the returned evidence and writes the report.
4. At most one failed critical worker is retried once.

A research request creates one visible Hermes session, not one session per phase or worker. Subagents appear in Hermes' subagent tree rather than as top-level sessions.

There is no server, database, task graph, checkpoint system, remote runner, or automatic revision loop.

## Requirements

- Python 3.11+
- `uv`
- Hermes Agent available as `hermes`
- `HERMES_CUSTOM_TINFOIL_API_KEY` and `OPENROUTER_API_KEY` in the active Hermes profile
- A searchable library at `~/dev/library` for private-mode library research

## Install

```bash
./scripts/install.sh
```

This installs the editable CLI with `uv tool` and symlinks the Hermes skill into:

```text
$HERMES_HOME/skills/research/local-deep-research
```

Start a new Hermes session after installation so it discovers the skill.

## Usage

Estimate without making model calls:

```bash
research-agent estimate --mode open
research-agent estimate --mode private
```

Run interactively:

```bash
research-agent run --mode open "What changed in French energy policy since 2017?"
```

Use a file to avoid shell quoting and accidental prompt expansion:

```bash
research-agent run \
  --mode private \
  --question-file question.md \
  --output report.md
```

For a pre-authorized non-interactive run:

```bash
research-agent run --mode open --question-file question.md --yes
```

If `--mode` is omitted in a terminal, the CLI asks whether to use private Tinfoil inference or open OpenRouter inference. In non-interactive use, `--mode` is mandatory.

## Cost controls

Defaults are in [`config/models.toml`](config/models.toml):

- Three workers
- $10 preflight ceiling
- Conservative token budgets for each phase
- One critical-worker retry
- 20 parent iterations and 12 iterations per worker
- Live OpenRouter price refresh with configured-price fallback

Hermes writes aggregate parent-and-subagent usage into `report.usage.json`. When a provider reports tokens but no cost, the launcher estimates cost using the configured parent price. A provider-side API-key budget remains the only strict protection against a request exceeding the ceiling while it is running, so assign a $10 OpenRouter guardrail to the key used here.

Private prices are configured from Tinfoil's published model prices. `kimi-k2-6` is currently marked deprecated by Tinfoil; change `config/models.toml` when the private parent is replaced.

## Privacy boundary

The selected provider—not the Hermes profile—is the privacy boundary.

- Private mode sends every model call through Tinfoil and may use local tools.
- Open mode sends every model call through OpenRouter and gives workers only public `web` and `browser` tools.
- Open mode never automatically falls back to private mode, and private mode never falls back to OpenRouter.

Hermes itself still runs as your operating-system user. Toolset restrictions reduce accidental local access but are not an OS sandbox.

## Development

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

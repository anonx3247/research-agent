---
name: local-deep-research
description: Use when the user asks for deep research. Route explicitly to private Tinfoil or open OpenRouter models, then run the local research-agent CLI.
version: 0.1.0
author: Local
license: Proprietary
metadata:
  hermes:
    tags: [research, privacy, tinfoil, openrouter, multi-agent]
---

# Local Deep Research

## Purpose

Run bounded, source-backed research through the local `research-agent` command. One visible Hermes parent plans and synthesizes, while native `delegate_task` leaf subagents perform three cheaper research assignments in parallel.

## Routing Gate

Before starting:

1. If the user explicitly said `private` or `open`, honor it.
2. Otherwise ask exactly: **“Should this research run privately through Tinfoil, or openly through OpenRouter?”**
3. Do not begin until the user chooses.

### Private

Use for local files, the local library, internal notes, personal data, private repositories, or anything the user does not want sent through OpenRouter.

- Parent: Tinfoil Kimi
- Workers: Tinfoil GPT-OSS 120B
- Local and public-web tools are allowed.

### Open

Use only for a question and context the user approves sending through OpenRouter.

- Parent: OpenRouter DeepSeek V4 Pro
- Workers: OpenRouter DeepSeek V4 Flash
- Public web sources only
- Do not pass local paths, private excerpts, internal notes, personal data, or unrelated conversation history.

## Procedure

1. Restate the approved research question without adding private context.
2. Write it to a uniquely named temporary UTF-8 file.
3. Run the estimate first:

   ```bash
   research-agent estimate --mode MODE
   ```

4. Tell the user the displayed estimate and hard cap. Obtain confirmation unless the user explicitly authorized this run after seeing the cost envelope.
5. Run:

   ```bash
   research-agent run --mode MODE --question-file FILE --yes --output REPORT
   ```

6. Read and return the generated Markdown report.
7. Report the actual cost from the generated `.usage.json` file.
8. Delete only the temporary question file you created. Keep the report and usage file.

## Hard Rules

- Never silently choose open mode.
- Never downgrade private to open when Tinfoil fails.
- Never paste private-mode context into an open-mode invocation.
- Never launch a second run automatically after failure.
- Use native `delegate_task`; do not spawn separate Hermes worker processes.
- Do not add researchers beyond the CLI default unless the user asks.
- A report is complete only when every consequential factual claim has a source, uncertainty is explicit, and the strongest counterargument is addressed.

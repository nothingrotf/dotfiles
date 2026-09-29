---
name: pane
description: Use Pane from inside a Pane terminal (PANE_SESSION_ID is set) through the runpane CLI. Use when delegating work to agents in their own Panes and worktrees, showing a page or file when supported, reading or sending input to another panel, or coordinating Panes from a Session orchestrator.
---
<!-- pane-managed-skill v1 -->

# Pane

Pane runs agents in terminal panels grouped into Panes, each Pane with its own
worktree. Sessions are orchestrator conversations that own Panes. You drive all
of it through the `runpane` CLI.

## Establish the control surface

1. Check for `runpane` on PATH. If it is absent, use
   `npx --yes runpane@latest` in place of `runpane` in every command below.
2. Run `runpane doctor --json`, then `runpane agent-context --json`. For a
   command's exact schema, run `runpane agent-context --command "<command>" --json`.
3. If runpane cannot be reached or doctor fails, stop and tell the user what
   failed. Do not substitute raw `git worktree` checkouts or built-in
   subagents for work that belongs in a Pane, and do not invent commands.
   From WSL when Pane runs on Windows, use the Windows wrapper through
   PowerShell from a Windows directory, for example
   `powershell.exe -NoProfile -Command 'Set-Location $env:TEMP; runpane doctor --json'`.
   Use that form for subsequent commands too. A Linux wrapper cannot reach
   the Windows named-pipe daemon; a Windows-mounted shim can also fail in WSL.

## Common commands

- Find a repository: `runpane repos list --json`
- Delegate work in a new Pane:
  `runpane panes create --repo <repo> --name <name> --agent <codex|claude|cursor> --prompt "<task>" --source agent --no-focus --wait-ready --yes --json`
- When `runpane agent-context --command "panels open" --json` lists the
  command, show the user a page or file with
  `runpane panels open --file <path> --source agent --yes --json` or
  `runpane panels open --url <url> --source agent --yes --json`.
- Inspect a Pane: `runpane panes list --json`, `runpane panels list --pane <pane-id> --json`
- Read or wait on a panel: `runpane panels screen --panel <panel-id> --limit 80 --json`,
  `runpane panels wait --panel <panel-id> --for idle --json`
- Send a message: `runpane panels submit --panel <panel-id> --text "<message>" --yes --json`

## Sessions

When `PANE_ORCHESTRATION_SESSION_ID` is set you are a Session orchestrator.
When `panes create` or `panes adopt` returns an `association` result,
check `association.ok`. Confirm with
`runpane sessions overview --session "$PANE_ORCHESTRATION_SESSION_ID" --json`.
If the Pane is absent, including when an older CLI returns no association
result, run `runpane sessions associate --session "$PANE_ORCHESTRATION_SESSION_ID" --pane <pane-id> --json`
and confirm again before sending work.
Never take over a Pane that belongs to another Session.

Opening a terminal or Session is not a request to start work. Act on the
user's request, and do not focus Pane windows unless the user asks.

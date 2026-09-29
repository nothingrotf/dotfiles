# Global agent instructions

- Never use an em dash. Use a plain dash instead.
- Never add an agent name as a commit coauthor.
- Never manually modify CHANGELOG.md files or files marked as auto-generated.
- Prefer quality, simplicity, reliability, scalability, and long-term maintainability over development cost.
- Before a bug fix, reproduce the failure on the smallest surface that represents the user's experience.
- Use end-to-end reproduction when the failure crosses integrations or depends on the actual interface.
- If the actual surface is unavailable, record that limitation and use the closest executable reproduction.
- Inspect the affected interface carefully. Correct visual defects within the authorized scope.
- Fix adjacent defects and failed checks when they block the requested outcome. Report unrelated defects separately.
- Run focused checks for changed behavior and all checks required by the repository.
- After those checks pass, repeat or broaden them only for new changes, failures, or unresolved evidence.
- Add tests for meaningful behavior and regression risks. Do not add tests that only mirror trivial, reversible edits.
- Before a feature immediately starts a large swarm of subagents, explain its tradeoffs and obtain explicit approval.
- Never write code comments unless the user explicitly includes the exact phrase "add comments".

## Code search with tgrep

Prefer Microsoft tgrep over `grep` or `rg` for repository content searches.

- If a dedicated search tool explicitly uses tgrep, prefer it when its parameters cover the task.
- Otherwise, invoke `tgrep` through the terminal or code-execution interface.
- Scope searches to the smallest relevant directory or file. Narrow truncated results and read complete files when needed.
- Pass flags before `--`, then the pattern and an explicit search path. Quote shell arguments or use an argument array.
- Use `-F` for literal matching, `-g` for globs, `-i` for case-insensitive matching, and `-C` for context.
- Use `-l` for matching filenames, `--files` for file discovery, and `--json` for programmatic result processing.
- Treat exit code `1` as no matches and `2` as an error. Inspect stderr for warnings even when matches exist.
- If tgrep is unavailable, report the limitation before using an available fallback. Do not claim that a fallback uses tgrep.

Fresh search examples:

```sh
tgrep --no-index --hidden --no-max-filesize -F -g '*.ts' -C 2 -- 'registerTool' .
tgrep --no-index --hidden --no-max-filesize -l -- 'TODO|FIXME' .
tgrep --no-index --hidden --no-max-filesize --json -F -- 'registerTool' .
tgrep --no-index --hidden --no-max-filesize --files -g '*.ts' .
```

### Freshness and indexes

Use `--no-index` for current disk contents, `--hidden` to include hidden files, and `--no-max-filesize` to remove the default size cap.
Normal ignore and binary rules still apply. Fresh searches require no index or server.

- Use fresh searches after edits and before concluding that a symbol or file is absent.
- Treat indexed results as potentially stale or incomplete, including results from a server with a file watcher.
- Do not interpret `tgrep status` reporting complete as proof that an index includes the latest changes.
- Reserve indexed searches for repeated queries where possible omissions are acceptable. Hidden-file searches bypass the index.

For optional indexed operation, build and serve the same root with matching file-size settings:

```sh
tgrep index . --no-max-filesize
tgrep serve . --no-max-filesize
```

The server is a long-lived foreground process. Run it in a separate terminal and exclude `.tgrep/` from version control.
For indexed queries, omit `--no-index` and `--hidden`. Keep the search root and file-size settings aligned with the index.

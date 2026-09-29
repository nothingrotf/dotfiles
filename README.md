# dotfiles

Personal development configuration with [chezmoi](https://www.chezmoi.io/) and [mise](https://mise.jdx.dev/).
This repository replaces the manual-copy layout of `pi-config`.

- Chezmoi manages files, machine-specific selections, diffs, and application.
- Mise manages tool versions and repository tasks.
- Git stores configuration, not credentials or application state.

The repository uses standard chezmoi conventions instead of a custom installer.
Files are regular copies, so application writes do not silently change the Git checkout.

## Setup

Install mise 2026.9.16 or later using the [installation guide](https://mise.jdx.dev/installing-mise.html).
On macOS, use Homebrew:

```sh
brew install mise
```

Clone the repository into a `dotfiles` directory:

```sh
git clone https://github.com/nothingrotf/dotfiles.git ~/dotfiles
cd ~/dotfiles
```

Review `mise.toml` and the source files before trusting them.
Install the pinned chezmoi version and select this machine's modules:

```sh
mise trust
mise install
mise run init
```

Initialization stores the checkout path and selections in the local chezmoi configuration.
It does not apply dotfiles or install Pi, Zed, or Ghostty.

Preview the changes before applying:

```sh
mise run plan
mise run diff
```

Back up differing local files outside this repository before applying.
Applying replaces managed file contents, including local edits, instead of merging settings automatically.
The apply task displays the diff and requests interactive confirmation through chezmoi.

```sh
mise run apply
mise run status
```

No installation step changes shell startup files, runs background services, or pushes Git commits.
Authentication and application installation remain separate.

## Layout

`.chezmoiroot` limits deployment to `home/`.
Root documentation, tests, workflows, and `mise.toml` are never deployed into the home directory.

| Source | Destination | Module |
| --- | --- | --- |
| `home/AGENTS.md` | `~/AGENTS.md` | `agents` |
| `home/dot_agents/` | `~/.agents/` | `agents` |
| `home/dot_pi/` | `~/.pi/` | `pi` |
| `home/dot_config/zed/` | `~/.config/zed/` | `zed` |
| `home/dot_config/ghostty/` | `~/.config/ghostty/` | `ghostty` |
| `home/dot_config/mise/conf.d/dotfiles-tools.toml` | `~/.config/mise/conf.d/dotfiles-tools.toml` | `runtimes` |

The `dot_` prefix represents a leading dot in a deployed filename.
The `executable_` prefix preserves executable scripts.
The `private_` prefix preserves `~/.pi/agent` permissions at `0700` and Zed settings permissions at `0600`.
The clone can live anywhere because chezmoi resolves sources from its configured source directory.

The application paths follow the existing `~/.config` layout.
A custom `XDG_CONFIG_HOME` does not automatically relocate these managed targets.
Adjust the source layout before applying on machines that use different application paths.

## Machine-specific modules

Initialization prompts for `agents`, `pi`, `zed`, `ghostty`, and `runtimes`.
All prompts default to enabled, but initialization alone writes no application files.
Without initialized selections, every module stays disabled.

The generated `~/.config/chezmoi/chezmoi.toml` contains local data such as:

```toml
[data]
agents = true
pi = true
zed = false
ghostty = false
runtimes = true
```

Keep the generated `sourceDir` when editing that file.
These choices stay local and do not enter Git.
Select both `agents` and `pi` for the complete agent setup.

From this checkout, run `mise exec -- chezmoi init --prompt` to choose again.
Initialization regenerates the chezmoi configuration and replaces unrelated hand-edited fields.
Back up an existing chezmoi configuration before initializing this repository.
Disabling a module stops managing it without deleting its existing files.
The configuration does not use chezmoi's `exact_` directories or removal scripts.
Unmanaged neighboring files remain untouched.

For machine-specific content, use a `.tmpl` source file and variables from the local `[data]` table.
Keep secrets in a password manager or in unmanaged files.
Do not copy credentials into a template or commit them under an unrecognized filename.

## Local Pi extensions

The imported Pi settings keep all 13 local package paths from the current machine.
They resolve from `~/.pi/agent` to `~/Workspaces/pi-extensions/packages/`.
They contain no fixed username or absolute macOS home path.

On a new machine, create that checkout before starting Pi:

```sh
mkdir -p ~/Workspaces
git clone https://github.com/nothingrotf/pi-extensions.git ~/Workspaces/pi-extensions
```

If the checkout already exists, keep it instead of cloning over it.
From the dotfiles checkout, install its dependencies with the pinned Bun version:

```sh
mise run pi:deps
```

This explicit task runs `bun install --frozen-lockfile` inside the existing extensions checkout.
It does not clone, pull, reset, or change the selected Pi packages.
The current npm package declarations remain unchanged.
Install the separate `tgrep` executable before using the search extension.
On macOS, run `brew install tgrep`.
For other platforms, follow the [extension setup guide](https://github.com/nothingrotf/pi-extensions/tree/main/packages/tgrep).
Install Pi separately and authenticate its providers on each machine.

## Runtime defaults

The optional `runtimes` module declares Node.js 24.21.0 and Bun 1.4.2.
Its dedicated `conf.d` fragment preserves any existing global mise `config.toml`.
Applying the fragment does not download or activate these runtimes.

After applying it, inspect the global selection and install tools from the home directory:

```sh
cd ~
mise config ls
mise ls --current
mise install
```

This installs every selected global tool, including tools declared outside this repository.
Project configurations can override these defaults.
Change shared versions in `home/dot_config/mise/conf.d/dotfiles-tools.toml`.

Add the appropriate activation command once to the existing shell configuration:

```sh
eval "$(mise activate zsh)"
```

For Bash, use `eval "$(mise activate bash)"` instead.
For Fish, use `mise activate fish | source` in `~/.config/fish/config.fish`.
Deactivate competing runtime managers for the same tools before enabling mise.

## Daily workflow

Edit source files in this checkout, then preview and apply:

```sh
mise run diff
mise run apply
```

To retain a reviewed change that an application wrote, re-add that specific file:

```sh
mise exec -- chezmoi add ~/.pi/agent/settings.json
git diff
```

For a templated file, edit its source or use `chezmoi merge` instead of replacing the template blindly.
Use `mise exec -- chezmoi add <path>` to add a new configuration file.
Inspect the Git diff before committing.
Never add whole runtime directories such as `~/.pi/agent` or `~/.config`.

Git ignores known runtime paths, and `.chezmoiignore` also excludes them from deployment.
Neither filter can identify arbitrary secrets embedded inside a settings file.

Chezmoi does not synchronize application edits back into Git automatically.
It also does not restore pre-migration files when a module is disabled.
Restore previous settings from the backup when undoing the migration.

## Migration notes

The migration imports 489 configuration files from the current local machine, not the outdated GitHub snapshot.
Settings, shared skills, themes, commands, instructions, and model policies retain their local contents.
Obsolete Superset resources and VCC settings no longer enter the source tree.
Onboarding, credentials, sessions, caches, logs, backup files, and installed packages remain machine-local.

The Pi module preserves the current model selections, trust preferences, and local package declarations.
The shared skills do not duplicate the skills supplied by Pi packages.

The repository is now `nothingrotf/dotfiles`.
For an existing `pi-config` checkout, update its remote:

```sh
git remote set-url origin https://github.com/nothingrotf/dotfiles.git
```

Use the `dotfiles` URL for new clones.

## Verification

Run the integration suite with the pinned tools:

```sh
mise run test
```

The suite invokes the real chezmoi CLI against temporary homes and source checkouts.
It checks initialization, module selection, dry runs, diffs, idempotence, executable permissions, and preservation of unmanaged state.
It also checks local module choices and the global mise runtime fragment.
The GitHub Actions workflow runs the suite on macOS and Linux.
The suite validates deployment, not the behavior of Pi, Zed, or Ghostty.
Imported skill references retain their original whitespace, so `git diff --check` reports Markdown whitespace warnings in those files.

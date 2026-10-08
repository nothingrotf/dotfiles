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

Initialization does not change shell startup files or start services.
The optional `shell` module replaces startup files only after a reviewed apply.
Authentication, package installation, and macOS preferences remain separate tasks.

## Layout

`.chezmoiroot` limits deployment to `home/`.
Root documentation, tests, workflows, scripts, inventories, preferences, and `mise.toml` never deploy into the home directory.

| Source | Destination | Module |
| --- | --- | --- |
| `home/AGENTS.md` | `~/AGENTS.md` | `agents` |
| `home/dot_agents/` | `~/.agents/` | `agents` |
| `home/dot_pi/` | `~/.pi/` | `pi` |
| `home/dot_config/zed/` | `~/.config/zed/` | `zed` |
| `home/dot_config/ghostty/` | `~/.config/ghostty/` | `ghostty` |
| `home/dot_config/mise/conf.d/dotfiles-tools.toml` | `~/.config/mise/conf.d/dotfiles-tools.toml` | `runtimes` |
| `home/dot_Brewfile`, `home/dot_config/homebrew/` | `~/.Brewfile`, `~/.config/homebrew/` | `brew` |
| Shell startup files, `home/dot_config/fish/`, `home/dot_config/shell/` | Zsh, Bash, Fish, and Tcsh configuration | `shell` |
| `home/dot_gitconfig.tmpl`, `home/dot_config/git/` | `~/.gitconfig`, `~/.config/git/` | `git` |
| `home/dot_tmux.conf`, CLI configuration directories | Tmux, Starship, Atuin, Yazi, Worktrunk, GitHub CLI, ccstatusline | `cli` |
| `home/dot_config/herdr/` | `~/.config/herdr/` | `herdr` |
| `home/dot_config/opencode/` | `~/.config/opencode/` | `opencode` |
| `home/dot_config/kaku/` | `~/.config/kaku/` | `kaku` |

The `dot_` prefix represents a leading dot in a deployed filename.
The `executable_` prefix preserves executable scripts.
The `empty_` prefix ensures that chezmoi creates the empty `~/.hushlogin` file.
The `private_` prefix preserves `~/.pi/agent` permissions at `0700` and Zed settings permissions at `0600`.
The clone can live anywhere because chezmoi resolves sources from its configured source directory.

The application paths follow the existing `~/.config` layout.
A custom `XDG_CONFIG_HOME` does not automatically relocate these managed targets.
Adjust the source layout before applying on machines that use different application paths.

## Machine-specific modules

Initialization prompts for every module in the layout table.
The original `agents`, `pi`, `zed`, `ghostty`, and `runtimes` modules default to enabled.
New modules default to disabled to preserve existing shell and Git configuration.
Without initialized selections, every module stays disabled.
The `brew` and `kaku` modules deploy files only on macOS.
Initialization alone writes no application files.

The generated `~/.config/chezmoi/chezmoi.toml` contains local data such as:

```toml
[data]
agents = true
pi = true
zed = false
ghostty = false
runtimes = true
brew = false
shell = false
git = false
cli = false
herdr = false
opencode = false
kaku = false
gitName = ""
gitEmail = ""
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

The Pi settings preserve the selected local package paths from the current machine.
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

The `shell` module activates mise in interactive Zsh, Bash, and Fish sessions when the executable exists.
Without that module, add the appropriate activation command once to the existing shell configuration:

```sh
eval "$(mise activate zsh)"
```

For Bash, use `eval "$(mise activate bash)"` instead.
For Fish, use `mise activate fish | source` in `~/.config/fish/config.fish`.
Deactivate competing runtime managers for the same tools before enabling mise.

## Homebrew packages and applications

`home/dot_Brewfile` records the current Homebrew taps, requested formulae, casks, Go packages, uv tools, and npm packages.
Homebrew resolves transitive formula dependencies instead of recording every installed library.
The snapshot preserves existing Homebrew Node versions, even though the `runtimes` module also declares Node.
It records current state rather than migrating runtime ownership.
Review third-party taps and duplicated runtimes before installing on another machine.

The `brew` module deploys manifests only.
Tasks read the manifests directly from the checkout, so they do not require a chezmoi apply.
Check or install the recorded packages explicitly:

```sh
mise run brew:check
mise run brew:install
```

Check and install tasks pass `--no-upgrade` to preserve existing package versions.
The install task disables Homebrew's automatic installation cleanup and does not run cleanup or service commands.
Homebrew can still upgrade dependencies when a package installation requires them.
No task removes existing packages or forces an application overwrite.

`home/dot_config/homebrew/Brewfile.apps` lists 13 additional apps found outside the Homebrew installation inventory.
Their current Homebrew cask identifiers were checked during import.
Keep this manifest separate because an existing app bundle can conflict with a cask installation.

```sh
mise run brew:apps:check
mise run brew:apps:install
```

Move or uninstall a conflicting app manually before installing its cask.
Do not use a forced overwrite without a backup.
Dia, Zeron, T3 Code Nightly, Apple apps, and the Claude Code URL handler remain outside this additional manifest.
`inventory/apps.json` records the application names, including those without a checked cask mapping.

After an intentional package change, refresh only the Homebrew snapshot:

```sh
mise run brew:dump
git diff -- home/dot_Brewfile
```

The dump omits description comments and service restart directives.
It does not update the manually maintained additional-app manifest.
`inventory/bun-global.json` records the existing Bun global package specifications.
That inventory includes platform-specific packages and overlapping CLIs, so no task installs it automatically.

## Shell and Git configuration

Back up existing startup files before enabling `shell`.
The module preserves shell integrations and aliases while replacing fixed usernames with `$HOME`.
Optional tools and environment files receive existence checks.
Shell startup does not download tools.

The shared profile discovers Homebrew.
A shared shell fragment adds existing personal executable directories and the Homebrew rustup directory.
Login profiles and interactive Bash and Zsh sessions load this fragment.
Fish receives equivalent Homebrew initialization and path setup.
Bash and Zsh login shells load the shared profile.
Fish retains Starship, rbenv, Atuin, Worktrunk, and the `eza` and `bat` aliases.
Mise activates only in interactive shells.
The previous NVM startup snippet is omitted to avoid competing with mise.

Bash enables Atuin only when the unmanaged `~/.bash-preexec.sh` dependency exists.
Restore that dependency separately when Bash history integration is required.
Atuin preferences preserve daemon autostart, so starting an integrated shell can start its daemon.
Generated Python, Vite+, Kaku, and completion files remain owned by their installers.

When enabling `git`, provide the existing author name and email during initialization.
Chezmoi stores those values in local `gitName` and `gitEmail` data, not in repository files.
Applying the Git module fails before replacing its configuration when either identity value is blank.
The Git template preserves the current branch default, pull policy, LFS filters, and aliases.
Install Git LFS separately when a repository requires those filters.
An optional `~/.gitconfig.local` include overrides shared settings without entering version control.
SSH keys, SSH host configuration, signing keys, and GitHub authentication remain machine-local.

## CLI and terminal preferences

The `cli` module preserves preferences for Atuin, Starship, Yazi, Worktrunk, GitHub CLI, Tmux, and ccstatusline.
Atuin history and sync credentials remain local.
Worktrunk's empty project table is omitted to keep future project trust choices unmanaged.
Yazi includes both local Kaku flavors and preserves the current dark flavor selection.
Tmux loads Kaku's generated integration only when that file exists.

The `herdr` module contains daemon preferences and GUI overrides, not generated GUI defaults.
Sessions, plugin installation records, runtime locks, credentials, and local checkout paths remain excluded.
The `kaku` module preserves the existing Lua overrides and loads application-bundled defaults.
Kaku retains ownership of generated shell integrations and terminal session state.

The `opencode` module contains the main settings and the three existing Plannotator commands.
It preserves the current unrestricted permission policy and Chrome DevTools MCP declaration.
Review that policy before enabling the module on a shared machine.
Herdr and Poracode installers retain ownership of their OpenCode plugin files.
Reinstall those integrations through their owning applications instead of copying generated code into dotfiles.

## macOS preferences

`preferences/macos.json` records 14 selected preferences from the current machine.
It covers appearance, keyboard repeat, automatic text behavior, Finder, and Dock.
It excludes recent documents, application positions, accounts, and arbitrary preference databases.
These preferences remain independent of chezmoi modules.

Preview the typed commands before applying:

```sh
mise run macos:plan
mise run macos:apply
```

The apply task requires an explicit `y` confirmation.
It does not restart applications or change the login shell.
Log out and back in when an application does not refresh its preferences.
Both tasks reject non-macOS systems.

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
It also checks local module choices, Git identity rendering, and the global mise runtime fragment.
Additional tests validate shell startup, package task arguments, platform guards, and macOS confirmation without changing preferences.
The GitHub Actions workflow runs the suite on macOS and Linux.
The suite validates deployment, not the behavior of Pi, Zed, or Ghostty.
Imported skill references retain their original whitespace, so `git diff --check` reports Markdown whitespace warnings in those files.

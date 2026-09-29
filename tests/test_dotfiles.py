import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHEZMOI = os.environ.get("DOTFILES_CHEZMOI_BIN") or shutil.which("chezmoi")
MISE = os.environ.get("DOTFILES_MISE_BIN") or shutil.which("mise")
DEFAULT_MODULES = ("agents", "pi", "zed", "ghostty", "runtimes")
MODULES = DEFAULT_MODULES + ("brew", "shell", "git", "cli", "herdr", "opencode", "kaku")


class DotfilesTests(unittest.TestCase):
    def setUp(self):
        if not CHEZMOI or not MISE:
            self.fail("Run with mise run test or set DOTFILES_CHEZMOI_BIN and DOTFILES_MISE_BIN")
        temporary = tempfile.TemporaryDirectory(prefix="dotfiles-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.home = self.root / "home with spaces"
        self.home.mkdir()
        self.repo = self.root / "source with spaces"
        shutil.copytree(
            ROOT,
            self.repo,
            ignore=shutil.ignore_patterns(
                ".git", "__pycache__", "local", "backups", "*.local.toml"
            ),
        )
        self.config = self.home / ".config/chezmoi/chezmoi.toml"
        self.env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("MISE_", "XDG_", "GIT_", "CHEZMOI_"))
        }
        self.env.update(
            HOME=str(self.home),
            XDG_CONFIG_HOME=str(self.home / ".config"),
            XDG_DATA_HOME=str(self.home / ".local/share"),
            XDG_STATE_HOME=str(self.home / ".local/state"),
            XDG_CACHE_HOME=str(self.home / ".cache"),
            MISE_CONFIG_DIR=str(self.home / ".config/mise"),
            MISE_DATA_DIR=str(self.home / ".local/share/mise"),
            MISE_STATE_DIR=str(self.home / ".local/state/mise"),
            MISE_CACHE_DIR=str(self.home / ".cache/mise"),
            MISE_SYSTEM_CONFIG_DIR=str(self.root / "system"),
            MISE_TRUSTED_CONFIG_PATHS=str(self.repo),
            MISE_CEILING_PATHS=str(self.root),
            MISE_AUTO_ENV="false",
            MISE_COLOR="0",
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
        )
        self.command("git", "init", "--quiet")

    def command(self, *args, check=True):
        result = subprocess.run(
            args,
            cwd=self.repo,
            env=self.env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            timeout=60,
        )
        if check and result.returncode:
            self.fail(f"{args}:\n{result.stdout}\n{result.stderr}")
        return result

    def chezmoi(self, *args, check=True):
        return self.command(
            CHEZMOI,
            "--source", str(self.repo),
            "--destination", str(self.home),
            "--config", str(self.config),
            "--persistent-state", str(self.root / "chezmoi-state.boltdb"),
            "--cache", str(self.root / "chezmoi-cache"),
            "--no-tty", "--no-pager", "--color=false", "--use-builtin-diff",
            *args,
            check=check,
        )

    def select(self, modules=MODULES):
        self.config.parent.mkdir(parents=True, exist_ok=True)
        data = [f'sourceDir = {json.dumps(str(self.repo))}', "", "[data]"]
        data.extend(f"{module} = {str(module in modules).lower()}" for module in MODULES)
        data.extend(['gitName = "Test User"', 'gitEmail = "test@example.invalid"'])
        self.config.write_text("\n".join(data) + "\n")

    def targets(self, modules=MODULES):
        mappings = {
            "agents": [("AGENTS.md", "AGENTS.md"), ("dot_agents", ".agents")],
            "pi": [("dot_pi", ".pi")],
            "zed": [("dot_config/zed", ".config/zed")],
            "ghostty": [("dot_config/ghostty", ".config/ghostty")],
            "runtimes": [("dot_config/mise", ".config/mise")],
            "brew": [("dot_Brewfile", ".Brewfile"), ("dot_config/homebrew", ".config/homebrew")],
            "shell": [
                (f"dot_{name}", f".{name}") for name in
                ("bash_profile", "bashrc", "profile", "zprofile", "zshenv", "zshrc", "tcshrc")
            ] + [("empty_dot_hushlogin", ".hushlogin")] + [("dot_config/fish", ".config/fish"), ("dot_config/shell", ".config/shell")],
            "git": [("dot_gitconfig.tmpl", ".gitconfig"), ("dot_config/git", ".config/git")],
            "cli": [("dot_tmux.conf", ".tmux.conf")] + [
                (f"dot_config/{name}", f".config/{name}") for name in
                ("starship.toml", "atuin", "yazi", "worktrunk", "gh", "ccstatusline")
            ],
            "herdr": [("dot_config/herdr", ".config/herdr")],
            "opencode": [("dot_config/opencode", ".config/opencode")],
            "kaku": [("dot_config/kaku", ".config/kaku")],
        }
        targets = {}
        for module in modules:
            if module in ("brew", "kaku") and sys.platform != "darwin":
                continue
            for source_path, target_path in mappings[module]:
                source = self.repo / "home" / source_path
                target = self.home / target_path
                if source.is_file():
                    targets[target] = source
                    continue
                for file in source.rglob("*"):
                    if file.is_file():
                        parts = []
                        for part in file.relative_to(source).parts:
                            part = part.removeprefix("private_").removeprefix("executable_")
                            if part.startswith("dot_"):
                                part = "." + part.removeprefix("dot_")
                            parts.append(part)
                        targets[target.joinpath(*parts)] = file
        return targets

    def test_no_modules_are_deployed_before_initialization(self):
        self.chezmoi("apply", "--dry-run", "--verbose")
        self.chezmoi("apply", "--force")
        self.assertTrue(all(not target.exists() for target in self.targets()))

    def test_init_records_defaults_without_deploying_files(self):
        self.chezmoi("init", "--promptDefaults")
        config = tomllib.loads(self.config.read_text())
        self.assertEqual(Path(config["sourceDir"]), self.repo)
        self.assertEqual(config["data"], {
            **{module: module in DEFAULT_MODULES for module in MODULES},
            "gitName": "", "gitEmail": "",
        })
        source = self.command(CHEZMOI, "--config", str(self.config), "source-path")
        self.assertEqual(Path(source.stdout.strip()), self.repo / "home")
        self.assertTrue(all(not target.exists() for target in self.targets()))
        self.chezmoi("apply", "--dry-run", "--verbose")
        self.assertTrue(all(not target.exists() for target in self.targets()))
        self.select(("agents", "pi"))
        self.chezmoi("init", "--promptDefaults")
        config = tomllib.loads(self.config.read_text())
        self.assertEqual(config["data"], {
            **{module: module in ("agents", "pi") for module in MODULES},
            "gitName": "Test User", "gitEmail": "test@example.invalid",
        })

    def test_each_module_has_only_its_own_files(self):
        for module in MODULES:
            with self.subTest(module=module):
                self.select((module,))
                managed = self.chezmoi("managed", "--include=files").stdout.splitlines()
                expected = {str(target.relative_to(self.home)) for target in self.targets((module,))}
                self.assertEqual(set(managed), expected)

    def test_dry_run_then_apply_is_idempotent(self):
        self.select()
        targets = self.targets()
        self.chezmoi("apply", "--dry-run", "--verbose")
        self.chezmoi("diff")
        self.assertTrue(all(not target.exists() for target in targets))
        self.chezmoi("apply", "--force")
        before = {}
        for target, source in targets.items():
            with self.subTest(target=str(target)):
                self.assertTrue(target.is_file())
                self.assertFalse(target.is_symlink())
                expected = self.chezmoi("cat", str(target)).stdout.encode() if source.suffix == ".tmpl" else source.read_bytes()
                self.assertEqual(target.read_bytes(), expected)
                self.assertEqual(
                    bool(target.stat().st_mode & stat.S_IXUSR),
                    source.name.startswith("executable_"),
                )
                before[target] = target.stat().st_mtime_ns
        self.assertEqual(stat.S_IMODE((self.home / ".pi/agent").stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.home / ".config/zed/settings.json").stat().st_mode), 0o600)
        self.chezmoi("verify")
        self.chezmoi("apply", "--force")
        self.assertEqual(before, {target: target.stat().st_mtime_ns for target in targets})
        self.assertEqual(self.chezmoi("diff").stdout, "")
        self.assertEqual(self.chezmoi("status").stdout, "")
        for name in ("README.md", "mise.toml", "tests", ".github", "scripts", "preferences", "inventory"):
            self.assertFalse((self.home / name).exists())

    def test_runtime_sources_are_excluded_and_unmanaged_files_survive(self):
        self.select()
        private_source = self.repo / "home/dot_pi/private_agent/auth.json"
        private_source.write_text('{"token":"source-only-test-value"}\n')
        for relative in (
            "dot_config/gh/hosts.yml", "dot_config/herdr/github-credentials",
            "dot_config/herdr/session.json", "dot_config/fish/fish_variables",
            "dot_config/kaku/state.json", "dot_gitconfig.local",
        ):
            source = self.repo / "home" / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("source-only-test-value\n")
        sessions = self.repo / "home/dot_pi/private_agent/sessions"
        sessions.mkdir()
        (sessions / "private.jsonl").write_text("source session\n")
        unmanaged = {
            ".pi/agent/auth.json": "destination-only-test-value\n",
            ".pi/agent/sessions/keep.jsonl": "session\n",
            ".pi/agent/mcp-onboarding.json": "machine-local discovery\n",
            ".agents/skills/local/SKILL.md": "local skill\n",
            ".config/zed/private.json": "local setting\n",
            ".config/mise/config.toml": "[settings]\ncolor = false\n",
            ".gitconfig.local": "[user]\nname = Local User\n",
            ".config/gh/hosts.yml": "local auth state\n",
            ".config/fish/fish_variables": "local shell state\n",
            ".config/herdr/session.json": "local session\n",
            ".config/herdr/github-credentials": "local credential state\n",
            ".config/kaku/state.json": "local terminal state\n",
            ".local/share/atuin/history.db": "local history\n",
        }
        for relative, content in unmanaged.items():
            path = self.home / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        (self.home / ".pi/agent").chmod(0o700)
        self.chezmoi("apply", "--force")
        self.assertEqual(stat.S_IMODE((self.home / ".pi/agent").stat().st_mode), 0o700)
        self.assertFalse((self.home / ".pi/agent/sessions/private.jsonl").exists())
        for relative, content in unmanaged.items():
            self.assertEqual((self.home / relative).read_text(), content)
        self.select(())
        self.chezmoi("apply", "--force")
        for relative, content in unmanaged.items():
            self.assertEqual((self.home / relative).read_text(), content)
        self.assertTrue((self.home / ".pi/agent/settings.json").exists())

    def test_diffs_show_local_edits_and_interactive_apply_does_not_overwrite(self):
        self.select(("pi",))
        self.chezmoi("apply", "--force")
        settings = self.home / ".pi/agent/settings.json"
        settings.write_text('{"theme":"local-edit"}\n')
        self.assertIn("local-edit", self.chezmoi("diff").stdout)
        result = self.chezmoi("apply", "--interactive", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(settings.read_text(), '{"theme":"local-edit"}\n')
        self.chezmoi("add", str(settings))
        self.assertEqual((self.repo / "home/dot_pi/private_agent/settings.json").read_bytes(), settings.read_bytes())
        self.assertEqual(self.chezmoi("diff").stdout, "")

    def test_global_runtime_fragment_is_discovered_without_installing_tools(self):
        self.select(("runtimes",))
        self.chezmoi("apply", "--force")
        result = self.command(MISE, "-C", str(self.home), "ls", "--current", "--json")
        tools = json.loads(result.stdout)
        versions = tomllib.loads(
            (self.repo / "home/dot_config/mise/conf.d/dotfiles-tools.toml").read_text()
        )["tools"]
        for name, version in versions.items():
            self.assertEqual(tools[name][0]["requested_version"], version)
        self.assertFalse((Path(self.env["MISE_DATA_DIR"]) / "installs").exists())

    def test_git_identity_is_local_and_local_overrides_survive(self):
        self.select(("git",))
        self.chezmoi("init", "--promptDefaults")
        data = tomllib.loads(self.config.read_text())["data"]
        self.assertEqual(data["gitName"], "Test User")
        self.assertEqual(data["gitEmail"], "test@example.invalid")
        self.chezmoi("apply", "--force")
        gitconfig = self.home / ".gitconfig"
        self.assertEqual(self.command("git", "config", "--file", str(gitconfig), "user.name").stdout.strip(), "Test User")
        local = self.home / ".gitconfig.local"
        local.write_text('[user]\nname = Local User\n')
        result = self.command("git", "config", "--includes", "--file", str(gitconfig), "user.name")
        self.assertEqual(result.stdout.strip(), "Local User")
        self.chezmoi("apply", "--force")
        self.assertEqual(local.read_text(), '[user]\nname = Local User\n')

    def test_git_apply_rejects_missing_identity_without_overwriting(self):
        self.select(("git",))
        gitconfig = self.home / ".gitconfig"
        gitconfig.write_text('[user]\nname = Existing User\nemail = existing@example.invalid\n')
        for key, replacement in (("gitName", ""), ("gitEmail", ""), ("gitName", "   "), ("gitEmail", "   ")):
            with self.subTest(key=key, replacement=replacement):
                self.select(("git",))
                data = self.config.read_text()
                value = "Test User" if key == "gitName" else "test@example.invalid"
                self.config.write_text(data.replace(f'{key} = "{value}"', f'{key} = "{replacement}"'))
                result = self.chezmoi("apply", "--force", check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Git author name and email", result.stderr)
                self.assertIn("Existing User", gitconfig.read_text())

    def test_private_paths_are_ignored_by_git(self):
        paths = [
            "mise.local.toml",
            "local/settings.json",
            "home/dot_pi/private_agent/auth.json",
            "home/dot_env",
            "home/dot_env.production",
            "home/dot_npmrc",
            "home/dot_pi/private_agent/mcp-onboarding.json",
            "home/dot_pi/private_agent/git/github.com/example/file",
            "home/dot_pi/private_agent/npm/node_modules/package/file",
            "home/dot_pi/private_agent/sessions/session.jsonl",
            "home/dot_pi/private_agent/web-search-cache/result.json",
            "home/private_dot_pi/private_agent/state/runtime.json",
            "home/dot_agents/rules/pstack-models.md.bkp1",
            "backups/settings.json",
            "home/dot_gitconfig.local",
            "home/dot_config/gh/hosts.yml",
            "home/dot_config/herdr/github-credentials",
            "home/dot_config/herdr/session.json",
            "home/dot_config/fish/fish_variables",
            "home/dot_config/worktrunk/config.toml.lock",
            "home/dot_config/kaku/state.json",
        ]
        for path in paths:
            with self.subTest(path=path):
                self.command("git", "check-ignore", "--quiet", path)
        self.assertFalse((self.repo / "home/dot_pi/private_agent/mcp-onboarding.json").exists())
        self.assertFalse((self.repo / "home/dot_pi/private_agent/npm").exists())


if __name__ == "__main__":
    unittest.main()

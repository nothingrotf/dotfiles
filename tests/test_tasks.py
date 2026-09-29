import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import macos


ROOT = Path(__file__).resolve().parents[1]


class MacosTests(unittest.TestCase):
    def test_plan_never_writes_preferences(self):
        with patch.object(macos.sys, "platform", "darwin"), patch.object(macos.subprocess, "run") as run:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(macos.main(["plan"]), 0)
            run.assert_not_called()
            self.assertIn("defaults write com.apple.dock autohide -bool true", output.getvalue())
            self.assertIn("KeyRepeat -float 2", output.getvalue())

    def test_apply_requires_explicit_confirmation(self):
        for answer in ("n", "", "yes"):
            with self.subTest(answer=answer):
                with patch.object(macos.sys, "platform", "darwin"), patch("builtins.input", return_value=answer):
                    with patch.object(macos.subprocess, "run") as run, contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(macos.main(["apply"]), 1)
                        run.assert_not_called()
        with patch.object(macos.sys, "platform", "darwin"), patch("builtins.input", side_effect=EOFError):
            with patch.object(macos.subprocess, "run") as run, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(macos.main(["apply"]), 1)
                run.assert_not_called()

    def test_confirmed_apply_uses_typed_arguments_without_restart(self):
        with patch.object(macos.sys, "platform", "darwin"), patch("builtins.input", return_value="y"):
            with patch.object(macos.subprocess, "run") as run, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(macos.main(["apply"]), 0)
                self.assertEqual([call.args[0] for call in run.call_args_list], macos.commands())
                self.assertTrue(all(call.kwargs == {"check": True} for call in run.call_args_list))

    def test_other_platforms_cannot_apply(self):
        with patch.object(macos.sys, "platform", "linux"), patch.object(macos.subprocess, "run") as run:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                macos.main(["apply"])
            self.assertEqual(error.exception.code, 2)
            run.assert_not_called()

    def test_boolean_is_not_accepted_as_numeric_preference(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preferences.json"
            path.write_text(json.dumps([{"domain": "test", "key": "test", "type": "float", "value": True}]))
            with self.assertRaises(ValueError):
                macos.commands(path)


class BrewTasksTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="dotfiles brew ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.script = self.root / "scripts/brew.sh"
        self.script.parent.mkdir()
        shutil.copyfile(ROOT / "scripts/brew.sh", self.script)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "brew-log"
        self.env = dict(os.environ, PATH=f"{self.bin}:/usr/bin:/bin", BREW_LOG=str(self.log))
        self.stub("uname", "printf '%s\\n' Darwin\n")
        self.stub("brew", 'test "$HOMEBREW_NO_INSTALL_CLEANUP" = 1 || exit 3\ntest "$HOMEBREW_NO_AUTO_UPDATE" = 1 || exit 4\nprintf "%s\\n" "$@" > "$BREW_LOG"\n')

    def stub(self, name, content):
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + content)
        path.chmod(0o700)

    def command(self, action):
        return subprocess.run(["sh", str(self.script), action], env=self.env, capture_output=True, text=True, timeout=10)

    def test_check_and_install_use_separate_manifests(self):
        for action, arguments, manifest in (
            ("check", ["bundle", "check", "--no-upgrade"], "home/dot_Brewfile"),
            ("install", ["bundle", "install", "--no-upgrade"], "home/dot_Brewfile"),
            ("apps-check", ["bundle", "check", "--no-upgrade"], "home/dot_config/homebrew/Brewfile.apps"),
            ("apps-install", ["bundle", "install", "--no-upgrade"], "home/dot_config/homebrew/Brewfile.apps"),
        ):
            with self.subTest(action=action):
                self.assertEqual(self.command(action).returncode, 0)
                self.assertEqual(self.log.read_text().splitlines(), arguments + [f"--file={self.root / manifest}"])

    def test_dump_does_not_record_services_or_comments(self):
        self.assertEqual(self.command("dump").returncode, 0)
        self.assertEqual(self.log.read_text().splitlines(), [
            "bundle", "dump", "--no-describe", "--no-restart", "--force",
            f"--file={self.root / 'home/dot_Brewfile'}",
        ])

    def test_platform_and_invalid_action_guards(self):
        self.assertEqual(self.command("unknown").returncode, 2)
        self.assertFalse(self.log.exists())
        self.stub("uname", "printf '%s\\n' Linux\n")
        self.assertEqual(self.command("install").returncode, 1)
        self.assertFalse(self.log.exists())


class ShellTests(unittest.TestCase):
    def test_startup_without_optional_tools_or_local_installations(self):
        with tempfile.TemporaryDirectory(prefix="dotfiles shell ") as directory:
            home = Path(directory)
            env = dict(os.environ, HOME=directory, PATH="/usr/bin:/bin", TERM="xterm", XDG_CONFIG_HOME=str(home / ".config"))
            for name in ("bashrc", "zshrc"):
                shutil.copyfile(ROOT / f"home/dot_{name}", home / f".{name}")
            for name, command in (
                ("bash", ["bash", "--noprofile", "--norc", "-ic", '. "$HOME/.bashrc"; printf shell-ready']),
                ("zsh", ["zsh", "-df", "-ic", '. "$HOME/.zshrc"; printf shell-ready']),
                ("fish", ["fish", "--no-config", "-ic", f'source "{ROOT}/home/dot_config/fish/config.fish"; printf shell-ready']),
            ):
                with self.subTest(shell=name):
                    executable = shutil.which(name)
                    if not executable:
                        continue
                    command[0] = executable
                    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=15)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("shell-ready", result.stdout)
                    self.assertNotIn("command not found", result.stderr)
                    self.assertNotIn("No such file", result.stderr)

    def test_nonlogin_shells_find_personal_and_rustup_bins(self):
        with tempfile.TemporaryDirectory(prefix="dotfiles paths ") as directory:
            home = Path(directory)
            local = home / ".local/bin"
            rustup = home / "homebrew/opt/rustup/bin"
            for path, name in ((local, "dotfiles-local-tool"), (rustup, "rustup")):
                path.mkdir(parents=True)
                executable = path / name
                executable.write_text("#!/bin/sh\nexit 0\n")
                executable.chmod(0o700)
            env_source = ROOT / "home/dot_config/shell/env.sh"
            target = home / ".config/shell/env.sh"
            target.parent.mkdir(parents=True)
            shutil.copyfile(env_source, target)
            env = dict(os.environ, HOME=directory, PATH="/usr/bin:/bin", TERM="xterm", HOMEBREW_PREFIX=str(home / "homebrew"))
            for shell, arguments in (("bash", ["--noprofile", "--norc"]), ("zsh", ["-df"])):
                executable = shutil.which(shell)
                if not executable:
                    continue
                with self.subTest(shell=shell):
                    source = ROOT / f"home/dot_{shell}rc"
                    result = subprocess.run(
                        [executable, *arguments, "-ic", f'. "{source}"; command -v dotfiles-local-tool && command -v rustup'],
                        env=env, capture_output=True, text=True, timeout=15,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(str(local), result.stdout)
                    self.assertIn(str(rustup), result.stdout)

    def test_shell_files_parse(self):
        for shell, files in (
            ("sh", [ROOT / "scripts/brew.sh", ROOT / "home/dot_profile", ROOT / "home/dot_config/shell/env.sh"]),
            ("bash", [ROOT / "home/dot_bashrc", ROOT / "home/dot_bash_profile"]),
            ("zsh", [ROOT / f"home/dot_{name}" for name in ("zprofile", "zshrc", "zshenv")]),
            ("fish", list((ROOT / "home/dot_config/fish").rglob("*.fish"))),
        ):
            executable = shutil.which(shell)
            if not executable:
                continue
            for file in files:
                with self.subTest(file=str(file)):
                    result = subprocess.run([executable, "-n", str(file)], capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

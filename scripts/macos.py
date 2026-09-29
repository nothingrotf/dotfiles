import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys


PREFERENCES = Path(__file__).resolve().parents[1] / "preferences/macos.json"


def commands(path=PREFERENCES):
    preferences = json.loads(path.read_text())
    result = []
    types = {"bool": bool, "float": (int, float), "int": int, "string": str}
    for preference in preferences:
        kind = preference["type"]
        value = preference["value"]
        if kind not in types or not isinstance(value, types[kind]):
            raise ValueError(f"Invalid preference: {preference['key']}")
        if isinstance(value, bool) and kind != "bool":
            raise ValueError(f"Invalid numeric preference: {preference['key']}")
        argument = str(value).lower() if kind == "bool" else str(value)
        result.append([
            "defaults", "write", preference["domain"], preference["key"],
            f"-{kind}", argument,
        ])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Preview or apply selected macOS preferences")
    parser.add_argument("action", choices=("plan", "apply"))
    args = parser.parse_args(argv)
    if sys.platform != "darwin":
        parser.error("macOS preferences require macOS")
    planned = commands()
    for command in planned:
        print(shlex.join(command))
    if args.action == "plan":
        return 0
    try:
        answer = input("Apply these preferences? [y/N] ")
    except EOFError:
        return 1
    if answer.strip().lower() != "y":
        return 1
    for command in planned:
        subprocess.run(command, check=True)
    print("Preferences applied. Log out and back in to refresh affected applications.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

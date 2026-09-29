#!/bin/sh
set -eu

if [ "$(uname -s)" != Darwin ]; then
    printf '%s\n' 'These Homebrew manifests require macOS.' >&2
    exit 1
fi
if ! command -v brew >/dev/null 2>&1; then
    printf '%s\n' 'Install Homebrew before running this task.' >&2
    exit 1
fi

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export HOMEBREW_NO_AUTO_UPDATE=1
export HOMEBREW_NO_INSTALL_CLEANUP=1

case "${1:-}" in
    check) brew bundle check --no-upgrade --file="$root/home/dot_Brewfile" ;;
    install) brew bundle install --no-upgrade --file="$root/home/dot_Brewfile" ;;
    dump) brew bundle dump --no-describe --no-restart --force --file="$root/home/dot_Brewfile" ;;
    apps-check) brew bundle check --no-upgrade --file="$root/home/dot_config/homebrew/Brewfile.apps" ;;
    apps-install) brew bundle install --no-upgrade --file="$root/home/dot_config/homebrew/Brewfile.apps" ;;
    *) printf '%s\n' 'Expected check, install, dump, apps-check, or apps-install.' >&2; exit 2 ;;
esac

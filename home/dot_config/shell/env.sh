dotfiles_brew_prefix=${HOMEBREW_PREFIX:-}
if [ -z "$dotfiles_brew_prefix" ]; then
    for dotfiles_prefix in /opt/homebrew /usr/local /home/linuxbrew/.linuxbrew; do
        if [ -x "$dotfiles_prefix/bin/brew" ]; then
            dotfiles_brew_prefix=$dotfiles_prefix
            break
        fi
    done
fi

for dotfiles_bin in "$HOME/.local/bin" "$HOME/.bun/bin" "$HOME/.cargo/bin" "$HOME/.druk/bin" "$HOME/.empryo/bin" "$HOME/.maestro/bin" "${dotfiles_brew_prefix:+$dotfiles_brew_prefix/opt/rustup/bin}"; do
    if [ -d "$dotfiles_bin" ]; then
        case ":$PATH:" in
            *":$dotfiles_bin:"*) ;;
            *) PATH="$dotfiles_bin:$PATH" ;;
        esac
    fi
done
unset dotfiles_bin dotfiles_prefix dotfiles_brew_prefix
export PATH

if [ -r "$HOME/.cargo/env" ]; then
    . "$HOME/.cargo/env"
fi

for dotfiles_bin in "$HOME/.local/bin" "$HOME/.bun/bin" "$HOME/.cargo/bin" "$HOME/.druk/bin" "$HOME/.empryo/bin" "$HOME/.maestro/bin"
    if test -d "$dotfiles_bin"
        fish_add_path -g "$dotfiles_bin"
    end
end
if set -q HOMEBREW_PREFIX; and test -d "$HOMEBREW_PREFIX/opt/rustup/bin"
    fish_add_path -g "$HOMEBREW_PREFIX/opt/rustup/bin"
end
set -gx BUN_INSTALL "$HOME/.bun"

if status is-interactive
    if command -q rbenv
        rbenv init - fish | source
    end
    if command -q mise
        mise activate fish | source
    end
    if command -q starship
        starship init fish | source
    end
    if command -q atuin
        atuin init fish | source
    end
    if command -q wt
        command wt config shell init fish | source
    end
    if command -q eza
        alias ls="eza --icons --grid"
    end
    if command -q bat
        alias cat="bat"
    end
    bind \e\x7f backward-kill-path-component
end

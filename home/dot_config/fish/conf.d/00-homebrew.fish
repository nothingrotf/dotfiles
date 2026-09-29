for dotfiles_brew in /opt/homebrew/bin/brew /usr/local/bin/brew /home/linuxbrew/.linuxbrew/bin/brew
    if test -x "$dotfiles_brew"
        "$dotfiles_brew" shellenv fish | source
        break
    end
end

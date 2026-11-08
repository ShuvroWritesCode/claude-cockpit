# claude-cockpit

A tmux cockpit for Claude Code in Ghostty: live usage, token burn, system stats and project git status around your session. One keybind to launch.

Layout: `[account/usage/system | claude | project/shell]`

## Install
```sh
mkdir -p ~/.config/claude-cockpit ~/.local/bin
cp panel.py project.py common.py statusline.py btop.conf ~/.config/claude-cockpit/
cp bin/cockpit ~/.local/bin/ && chmod +x ~/.local/bin/cockpit
```
Needs `tmux`, `btop`, `python3`. Ghostty keybind (see `ghostty-config.ghostty`): `cmd+alt+c` runs `cockpit`.

Usage: `cockpit [dir]` to start or re-attach, `cockpit --kill [dir]` to close.

Note: the left panel shows your account email on your own screen only; nothing is sent anywhere.

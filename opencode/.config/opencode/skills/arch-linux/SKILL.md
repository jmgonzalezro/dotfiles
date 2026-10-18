---
name: Arch Linux
description: Administración de Arch Linux — pacman, AUR, systemd, Qtile, NVIDIA y solución de problemas del sistema.
---

## Entorno del usuario
- Arch Linux (rolling release), kernel reciente.
- Escritorio Qtile en backend Wayland; tmux + Alacritty como terminal.
- GPU NVIDIA RTX 3070, driver 615.78. Config de Xorg en /etc/X11/xorg.conf.d/20-nvidia.conf.
- Dotfiles versionados en ~/dotfiles, enlazados desde ~/.config (alacritty, qtile, nvim, tmux, rofi, dunst...).

## Paquetes
- Instalar: `sudo pacman -S <paquete>`
- Actualizar TODO el sistema: `sudo pacman -Syu` (nunca parcial en rolling release)
- Buscar: `pacman -Ss <texto>`, ver info: `pacman -Si <paquete>`
- AUR: `yay -S <paquete>` o `paru -S <paquete>`
- Limpiar caché de paquetes: `sudo pacman -Sc` (con cuidado)

## Servicios (systemd)
- Estado: `systemctl status <servicio>`
- Arranque: `sudo systemctl enable --now <servicio>`
- Logs: `journalctl -u <servicio> -e` o `journalctl -f`

## Qtile
- Config: ~/.config/qtile/config.py (symlink a ~/dotfiles/qtile/.config/qtile/config.py)
- Recargar: atajo `mod+control+r`, o `qtile cmd-obj -o cmd -f reload_config`
- Backend Wayland: `wl_input_rules` disponible en la config.

## NVIDIA
- Estado de la GPU: `nvidia-smi`
- No modificar /etc/X11/xorg.conf.d/20-nvidia.conf sin dejar respaldo previo.
- Tras cambios de driver, verificar que la sesión (Qtile) arranca bien.

## Buenas prácticas
- Hacer respaldo antes de tocar la config del window manager o la de GPU.
- Preferir cambios reversibles; explicar el impacto a nivel de sistema.
- Ante un problema de arranque/sesión, tener a mano un tty de respaldo (Ctrl+Alt+F*).

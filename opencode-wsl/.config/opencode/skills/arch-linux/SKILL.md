---
name: Arch Linux
description: Administración de Arch Linux (pacman, AUR, systemd, journalctl) en un entorno WSL.
---

## Entorno
- Arch Linux (rolling release) dentro de WSL en el equipo de trabajo.
- Terminal: Windows Terminal (o similar) alojando la sesión WSL de Arch.
- **Sin escritorio propio dentro de WSL** (no hay NVIDIA/Qtile/dunst aquí). Para lo específico de WSL, ver la skill `wsl`.

## Paquetes
- Instalar: `sudo pacman -S <paquete>`
- Actualizar TODO el sistema: `sudo pacman -Syu` (nunca parcial en rolling release)
- Buscar: `pacman -Ss <texto>`, ver info: `pacman -Si <paquete>`
- AUR: `yay -S <paquete>` o `paru -S <paquete>`
- Limpiar caché de paquetes: `sudo pacman -Sc` (con cuidado)

## Servicios (systemd) — verificación previa en WSL
- En WSL systemd **puede no estar activo**. Comprobar: `systemctl is-system-running`
- Si está activo:
  - Estado: `systemctl status <servicio>`
  - Arranque: `sudo systemctl enable --now <servicio>`
  - Logs: `journalctl -u <servicio> -e` o `journalctl -f`
- Si NO está activo: ver la skill `wsl` para habilitarlo en `/etc/wsl.conf`.

## Buenas prácticas
- Hacer respaldo antes de tocar la configuración del sistema.
- Preferir cambios reversibles; explicar el impacto a nivel de sistema.
- Tras tocar `/etc/wsl.conf` puede requerirse reiniciar la instancia WSL.

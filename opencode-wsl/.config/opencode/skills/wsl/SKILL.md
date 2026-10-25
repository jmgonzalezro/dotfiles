---
name: WSL
description: Entorno WSL (Windows Subsystem for Linux) — /etc/wsl.conf, systemd, rendimiento de /mnt/c, interoperabilidad con Windows y reinicio de WSL.
---

## Entorno
- WSL2 con Arch, dentro de Windows. El programa y administra Arch aquí.
- La sesión WSL se abre desde Windows Terminal.

## Config clave
- `/etc/wsl.conf` — config de WSL: `[boot] systemd=true`, `[automount]`, `[network]`.
- La config de Windows/host normalmente NO se edita desde dentro de WSL salvo indicación.

## systemd en WSL
- Verificar: `systemctl is-system-running`
- Para activarlo, añadir a `/etc/wsl.conf`:
  ```ini
  [boot]
  systemd=true
  ```
  y reiniciar WSL (desde PowerShell: `wsl --shutdown`, o `wsl --terminate <distro>`).

## Rendimiento de ficheros
- **Trabaja dentro del FS de WSL (`~/...`), no en `/mnt/c/...`** — el acceso al disco Windows es lento (9p) y penaliza git, npm y builds.
- Clona y desarrolla los proyectos en el home de WSL.

## Interoperabilidad con Windows
- Ejecutar binarios/programas Windows desde WSL: `explorer.exe`, `code.exe`, `cmd.exe /c ...` (interop habilitado por defecto).
- Rutas de Windows en WSL: `/mnt/c/...`

## Reiniciar / recuperar WSL
- `wsl --shutdown` (PowerShell/CMD, apaga todas las distros) o `wsl --terminate <distro>`.
- Útil tras cambiar `/etc/wsl.conf` o si la instancia se atasca.

## Notas
- WSLg permite apps gráficas ligeras, pero aquí no hay gestor de ventanas ni NVIDIA de escritorio.
- No hay dunst ni notificaciones de escritorio (no se configuran a propósito).

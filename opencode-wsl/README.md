# opencode-wsl — config separada para el curro (WSL + Arch)

Config de OpenCode **independiente** para el ordenador de trabajo (Windows + WSL/Arch).
No comparte ficheros con la config de casa (`opencode/`): es un juego aparte.

## Qué incluye

- `opencode.jsonc` — modelo MiMo Free, permisos de seguridad, context7. **Sin notificaciones.**
- `cli.json` — terminal, contexto nvim, título de ventana. **attention desactivado.**
- `agents/` — `arch-admin` (**versión WSL**, sin NVIDIA/Qtile/dunst) + `reviewer`.
- `skills/` — `arch-linux` (pacman/systemd en WSL) + `wsl` (lo específico de WSL).
- `commands/` — los mismos 6 comandos de casa: `/commit` `/review` `/explain` `/fix` `/test` `/doc`.

## Instalación en WSL

1. Clona tus dotfiles dentro de WSL (o copia esta carpeta a la máquina):

   ```bash
   git clone git@github.com:jmgonzalezro/dotfiles.git ~/dotfiles
   ```

2. Enlaza los ficheros a `~/.config/opencode/`:

   ```bash
   mkdir -p ~/.config/opencode
   cd ~/.config/opencode
   SRC=~/dotfiles/opencode-wsl/.config/opencode
   ln -s "$SRC/opencode.jsonc" .
   ln -s "$SRC/cli.json" .
   ln -s "$SRC/agents" .
   ln -s "$SRC/skills" .
   ln -s "$SRC/commands" .
   ```

   (`service.json` y `node_modules/` los crea OpenCode; no hace falta tocarlos.)

3. Instala OpenCode y entra con tu cuenta **OpenCode Console/Go** (mismos modelos gratis).
   Verifica con `/models`.

4. Autentica **context7** la primera vez: en el TUI, `/mcps` → seleccionar `context7` → iniciar sesión (OAuth por máquina).

5. *(Opcional)* Si quieres probar `personal_site` u otra web desde el curro, añade playwright:

   ```bash
   opencode mcp add playwright --global -- npx -y @playwright/mcp
   npx playwright install chromium   # navegador la primera vez
   ```

## Notas de uso

- **Mantén los proyectos en `~/` (FS de WSL)**, no en `/mnt/c` — el disco Windows es lento (9p).
- El `AGENTS.md` va por proyecto: ejecuta `opencode` dentro de un proyecto y `/init` para generarlo.
- Sin `gh` instalado: el MCP de GitHub no se usa (decisión).

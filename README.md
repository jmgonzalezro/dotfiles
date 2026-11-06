# My dotfiles

Dotfiles multi-máquina: **sobremesa** (Arch + qtile X11), **portátil** (mismo
stack) y **PC de trabajo** (WSL/Windows). Cada carpeta de primer nivel es un
paquete de GNU Stow que espeja `$HOME` (p. ej. `qtile/.config/qtile/…`), y cada
máquina elige qué paquetes instala.

## Requisitos

```
# Arch
pacman -S git stow

# Debian/Ubuntu (WSL)
sudo apt install git stow
```

## Instalación en una máquina

```
git clone --recurse-submodules git@github.com:jmgonzalezro/dotfiles.git
cd dotfiles
./bootstrap.sh desktop      # o: laptop | work-wsl
```

`bootstrap.sh`:

1. Lee la lista de paquetes de `hosts/<host>.list`.
2. Elimina symlinks previos que apunten al repo (idempotente: se puede repetir).
3. Hace `stow` de cada paquete en `$HOME` (o `$TARGET`).

Opciones: `--dry-run` (simula sin tocar nada) y argumento de host para forzarlo.
La detección automática usa `/proc/version` (WSL) y el hostname (ver función
`detect_host` en el script).

## Estructura

```
hosts/              # manifiestos: qué paquetes van en cada máquina
  desktop.list
  laptop.list
  work-wsl.list
host-desktop/       # overrides de qtile del sobremesa (host.py: xrandr 144Hz)
host-laptop/        # overrides del portátil (host.py vacío de momento)
qtile/ rofi/ dunst/ alacritty/ picom/ gsimplecal/ scripts/ systemd/ ...  # paquetes compartidos
local/              # ~/.local/share (tema del greeter LightDM)
opencode/           # opencode (sobremesa/portátil)
opencode-wsl/       # opencode para WSL (config completa alternativa)
tmux_bash/          # ~/.bashrc + ~/.tmux.conf
nvim/               # submódulo
```

## Cambiar la config de un host concreto

Lo que difiere entre máquinas **no** va en el archivo compartido, sino en el
paquete `host-<máquina>`, con un nombre distinto para evitar conflictos de stow.
Ejemplo actual: `qtile` carga `~/.config/qtile/host.py` si existe; el sobremesa
define ahí su `xrandr` (DP-2@144) y el portátil lo deja vacío.

Para añadir un override nuevo: crea el archivo bajo `host-<máquina>/.config/…`
con un nombre que no exista en el paquete compartido, y haz que la config
compartida lo lea de forma opcional (como `host.py` en qtile).

## Añadir una máquina nueva

1. Crea `hosts/<nueva>.list` con los paquetes que quieras.
2. (Opcional) crea `host-<nueva>/` con sus overrides.
3. Añade su hostname a `detect_host` en `bootstrap.sh` o pasa el nombre a mano.

## Submódulos

```
git submodule update --init --recursive
```

El bootstrap ya lo hace cuando el manifiesto incluye `nvim`.

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
./bootstrap.sh desktop      # o: laptop | wsl
./bootstrap.sh laptop       # en el portátil
```

`bootstrap.sh`:

1. Lee la lista de paquetes de `hosts/<host>.list`.
2. Elimina symlinks previos que apunten al repo (idempotente: se puede repetir).
3. Hace `stow` de cada paquete en `$HOME` (o `$TARGET`).

Opciones: `--dry-run` (simula sin tocar nada). La detección automática no usa
el hostname (es `jose` en todas las máquinas): **WSL** se detecta por el kernel
y para el resto crea `~/.dotfiles-host` con `desktop` o `laptop`, o pasa el
host como argumento.

Notas por host:

- **Greeter LightDM** (desktop/laptop): tras el bootstrap, instala/actualiza el
  tema en el sistema con `sudo ~/.local/share/lightdm-greeter/install.sh`
  (idempotente, con respaldos `.bak`; se aplica en el próximo login).
- **Wallpapers** (desktop/laptop): `~/Images/wallpapers` queda enlazado al repo;
  el fondo elegido se guarda por máquina en `~/.local/state/qtile/wallpaper`.
- **WSL**: sin GUI; el manifiesto solo instala nvim, opencode-wsl y bash/tmux.

## Estructura

```
hosts/              # manifiestos: qué paquetes van en cada máquina
  desktop.list
  laptop.list
  wsl.list
wallpapers/         # ~/Images/wallpapers (fondos del selector de wallpaper)
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

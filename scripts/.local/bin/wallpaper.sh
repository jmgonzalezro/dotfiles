#!/usr/bin/env bash
# wallpaper.sh — selector visual de fondos + aleatorio + persistencia.
#
#   wallpaper.sh              fondo actual
#   wallpaper.sh menu         rejilla de miniaturas en rofi (click izq. en la barra)
#   wallpaper.sh random       fondo al azar (click der. en la barra)
#   wallpaper.sh set <ruta>   aplicar un archivo concreto
#   wallpaper.sh apply        reaplicar el guardado (lo usa el autostart)
#
# Inspirado en el selector de gh0stzk / Abhra00 (dotfiles-new), simplificado:
# sin ImageMagick ni hyprpaper. Las miniaturas se generan con Pillow (ya
# instalado) en ~/.cache/wallcache y solo se regeneran si el archivo cambia
# (sha1 guardado al lado). Sin dependencias nuevas.
set -euo pipefail

WALL_DIR="${WALLPAPER_DIR:-$HOME/Images/wallpapers}"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/wallcache"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/qtile"
STATE_FILE="$STATE_DIR/wallpaper"
ROFI_THEME="${XDG_CONFIG_HOME:-$HOME/.config}/rofi/wallSelect.rasi"
THUMB_SIZE="${THUMB_SIZE:-440}"

# Imprime las entradas de rofi (nombre + icono por el protocolo NUL) y
# mantiene la caché: genera lo que falte o haya cambiado, borra huérfanos.
list_entries() {
    python3 - "$WALL_DIR" "$CACHE_DIR" "$THUMB_SIZE" <<'PY'
import hashlib
import sys
from pathlib import Path

from PIL import Image

wall_dir, cache_dir, size = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
cache_dir.mkdir(parents=True, exist_ok=True)

files = sorted(
    (f for f in wall_dir.iterdir() if f.is_file() and f.suffix.lower() in EXTENSIONS),
    key=lambda p: p.name.lower(),
)
if not files:
    sys.exit(f"No hay fondos en {wall_dir}")

live = set()
for source in files:
    key = hashlib.sha1(str(source).encode()).hexdigest()[:12]
    thumb = cache_dir / f"{key}.jpg"
    stamp_file = cache_dir / f".{key}.sha1"
    live.update({thumb.name, stamp_file.name})

    stamp = hashlib.sha1(source.read_bytes()).hexdigest()
    stale = (
        not thumb.is_file()
        or not stamp_file.is_file()
        or stamp_file.read_text().strip() != stamp
    )
    if stale:
        with Image.open(source) as image:
            image = image.convert("RGB")
            scale = max(size / image.width, size / image.height)
            image = image.resize(
                (round(image.width * scale), round(image.height * scale)), Image.LANCZOS
            )
            left = (image.width - size) // 2
            top = (image.height - size) // 2
            image = image.crop((left, top, left + size, top + size))
            image.save(thumb, "JPEG", quality=82)
        stamp_file.write_text(stamp)

    print(f"{source.name}\0icon\x1f{thumb}", end="\n")

for leftover in cache_dir.iterdir():
    if leftover.name not in live:
        leftover.unlink(missing_ok=True)
PY
}

notify() {
    command -v dunstify >/dev/null 2>&1 || return 0
    dunstify -a fondo -r 9996 -t 1500 "$@" >/dev/null 2>&1 || true
}

set_wallpaper() {
    local path="$1"
    if [[ ! -f "$path" ]]; then
        echo "No existe el fondo: $path" >&2
        return 1
    fi
    # feh reescribe ~/.fehbg, así que la restauración externa sigue funcionando.
    feh --bg-fill "$path"
    mkdir -p "$STATE_DIR"
    printf '%s\n' "$path" >"$STATE_FILE"
    notify "Fondo: $(basename "$path")"
}

saved_wallpaper() {
    local path=""
    if [[ -r "$STATE_FILE" ]]; then
        IFS= read -r path <"$STATE_FILE" || true
    fi
    if [[ -n "$path" && -f "$path" ]]; then
        printf '%s' "$path"
        return 0
    fi
    # Sin estado todavía: respetar lo que haya en ~/.fehbg, si apunta a algo real.
    if [[ -r "$HOME/.fehbg" ]]; then
        path="$(sed -n "s/.*--bg-[a-z]* '\(.*\)'.*/\1/p" "$HOME/.fehbg" | head -1)"
        if [[ -n "$path" && -f "$path" ]]; then
            printf '%s' "$path"
            return 0
        fi
    fi
    return 1
}

random_wallpaper() {
    local files=()
    shopt -s nullglob nocaseglob
    files=("$WALL_DIR"/*.jpg "$WALL_DIR"/*.jpeg "$WALL_DIR"/*.png "$WALL_DIR"/*.webp "$WALL_DIR"/*.gif)
    shopt -u nullglob nocaseglob
    if ((${#files[@]} == 0)); then
        echo "No hay fondos en $WALL_DIR" >&2
        return 1
    fi
    printf '%s\n' "${files[RANDOM % ${#files[@]}]}"
}

case "${1:-}" in
"" | current)
    if saved_wallpaper >/dev/null; then
        saved_wallpaper
        echo
    else
        echo "Sin fondo guardado (usa: wallpaper.sh random | menu)"
    fi
    ;;
menu)
    command -v rofi >/dev/null 2>&1 || {
        echo "rofi no está instalado" >&2
        exit 1
    }
    # Una sola instancia de rofi: si ya hay una abierta, se cierra.
    pkill -x rofi 2>/dev/null || true
    selection="$(list_entries | rofi -dmenu -i -no-custom -show-icons -theme "$ROFI_THEME" -p fondo)" || exit 0
    [[ -n "$selection" ]] || exit 0
    set_wallpaper "$WALL_DIR/$selection"
    ;;
random)
    set_wallpaper "$(random_wallpaper)"
    ;;
set)
    [[ -n "${2:-}" ]] || {
        echo "Uso: wallpaper.sh set <ruta>" >&2
        exit 1
    }
    # Acepta ruta absoluta o nombre dentro del directorio de fondos.
    if [[ -f "$2" ]]; then
        set_wallpaper "$2"
    else
        set_wallpaper "$WALL_DIR/$(basename "$2")"
    fi
    ;;
apply)
    if saved_wallpaper >/dev/null; then
        set_wallpaper "$(saved_wallpaper)"
    else
        set_wallpaper "$(random_wallpaper)"
    fi
    ;;
*)
    echo "Uso: wallpaper.sh [menu|random|apply|set <ruta>|current]" >&2
    exit 1
    ;;
esac

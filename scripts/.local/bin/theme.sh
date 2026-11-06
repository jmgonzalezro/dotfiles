#!/usr/bin/env bash
# theme.sh — selector de temas de Qtile + Alacritty + Rofi + Dunst.
#
# Sin dependencias nuevas: los .toml de ~/.config/qtile/themes son la única
# fuente de verdad; theme-apps.py los traduce a los archivos que cada app
# importa. El tema activo se guarda en ${XDG_STATE_HOME:-~/.local/state}/qtile/theme.
#
#   theme.sh              tema actual + disponibles
#   theme.sh <tema>       aplicar por nombre
#   theme.sh toggle       alternar (ciclo entre todos los temas)
#   theme.sh menu         selector con rofi
#   theme.sh list         solo nombres, uno por línea
#   theme.sh render       regenerar los archivos de app del tema actual
#                         (sin recargar nada; lo usa el arranque de Qtile)
#
# Orden de aplicación (todo o nada): valida la config de Qtile y el CSS de
# rofi ANTES de tocar el estado; si algo falla, no se aplica nada.
set -euo pipefail

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/qtile"
THEMES_DIR="$CONFIG_DIR/themes"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/qtile"
STATE_FILE="$STATE_DIR/theme"
APP_DIR="$STATE_DIR/app"
CONFIG="$CONFIG_DIR/config.py"
RENDER="$HOME/.local/bin/theme-apps.py"
DUNSTRC="${XDG_CONFIG_HOME:-$HOME/.config}/dunst/dunstrc"
ALACRITTY_CONF="${XDG_CONFIG_HOME:-$HOME/.config}/alacritty/alacritty.toml"

shopt -s nullglob
themes=()
for f in "$THEMES_DIR"/*.toml; do
    themes+=("$(basename "$f" .toml)")
done
shopt -u nullglob

if ((${#themes[@]} == 0)); then
    echo "No hay temas en $THEMES_DIR" >&2
    exit 1
fi

contains() {
    local needle="$1" t
    for t in "${themes[@]}"; do
        [[ "$t" == "$needle" ]] && return 0
    done
    return 1
}

current() {
    local name=""
    if [[ -r "$STATE_FILE" ]]; then
        IFS= read -r name <"$STATE_FILE" || true
    fi
    if [[ -n "$name" ]] && contains "$name"; then
        printf '%s' "$name"
    else
        printf '%s' "${themes[0]}"
    fi
}

theme_file() {
    printf '%s/%s.toml' "$THEMES_DIR" "$1"
}

# Genera los tres archivos de app para el tema $1 en el directorio $2.
render_apps() {
    local name="$1" dest="$2"
    python3 "$RENDER" "$(theme_file "$name")" --outdir "$dest" --dunstrc "$DUNSTRC"
}

# rofi falla en SILENCIO si el rasi tiene un error de sintaxis (vuelve al tema
# solarized por defecto, rc=0). Por eso validamos el tema ya parseado: fuente y
# color de fondo deben ser los del tema.
validate_rofi() {
    local dest="$1" name="$2" dumpfile="$1/.rofi-dump"
    command -v rofi >/dev/null 2>&1 || return 0
    # El dump se guarda en archivo: un heredoc ocuparía el stdin de python.
    rofi -config "$dest/rofi.rasi" -dump-theme >"$dumpfile" 2>&1 || true
    if ! python3 - "$(theme_file "$name")" "$dumpfile" <<'PY'
import re, sys, tomllib

with open(sys.argv[1], "rb") as fh:
    rofi = tomllib.load(fh)["rofi"]

dump = open(sys.argv[2], encoding="utf-8", errors="replace").read()
font = rofi["font"]
match = re.search(r"^\s+font:\s+(.*?)\s*$", dump, re.M)
found = match.group(1).rstrip(";").strip().strip('"') if match else "(nada)"
if found != font:
    print(f"rofi: se esperaba la fuente {font!r}, se obtuvo {found!r}", file=sys.stderr)
    raise SystemExit(1)

match = re.search(r"^\s+background:\s+rgba \(\s*(\d+),\s*(\d+),\s*(\d+)", dump, re.M)
if not match:
    print("rofi: no pude leer el color de fondo del tema", file=sys.stderr)
    raise SystemExit(1)
hexrgb = rofi["background"].lstrip("#")[:6]
esperado = tuple(int(hexrgb[i:i + 2], 16) for i in (0, 2, 4))
obtenido = tuple(int(x) for x in match.groups())
if obtenido != esperado:
    print(f"rofi: fondo esperado {esperado}, obtenido {obtenido}", file=sys.stderr)
    raise SystemExit(1)
PY
    then
        rm -f "$dumpfile"
        return 1
    fi
    rm -f "$dumpfile"
    return 0
}

reload_dunst() {
    local path="$1"
    command -v dunstctl >/dev/null 2>&1 || return 0
    if dunstctl reload "$path" >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

reload_qtile() {
    command -v qtile >/dev/null 2>&1 || return 0
    qtile cmd-obj -o cmd -f reload_config >/dev/null 2>&1 ||
        echo "Aviso: Qtile no respondió; el tema se aplicará en la próxima recarga." >&2
}

# Sustituye $APP_DIR por el directorio preparado en $1 (atómico a nivel de dir).
commit_apps() {
    local staged="$1"
    rm -rf "$APP_DIR.old"
    [[ -d "$APP_DIR" ]] && mv "$APP_DIR" "$APP_DIR.old"
    mv "$staged" "$APP_DIR"
}

apply() {
    local new="$1" prev staged="$STATE_DIR/app.staging"
    if ! contains "$new"; then
        echo "Tema desconocido: $new (disponibles: ${themes[*]})" >&2
        return 1
    fi
    prev="$(current)"

    # 1. Qtile: la config debe ejecutarse sin errores con este tema.
    if ! QTILE_THEME="$new" python3 "$CONFIG" >/dev/null 2>&1; then
        echo "El tema '$new' no valida (config de Qtile rota); no se aplica." >&2
        return 1
    fi

    # 2. Render a un directorio de paso + validación de rofi.
    rm -rf "$staged"
    if ! render_apps "$new" "$staged"; then
        echo "El tema '$new' no se pudo renderizar; no se aplica." >&2
        rm -rf "$staged"
        return 1
    fi
    if ! validate_rofi "$staged" "$new"; then
        echo "El tema '$new' genera un rofi inválido; no se aplica." >&2
        rm -rf "$staged"
        return 1
    fi

    # 3. Commit: a partir de aquí el tema es el nuevo.
    mkdir -p "$STATE_DIR"
    printf '%s\n' "$new" >"$STATE_FILE"
    commit_apps "$staged"

    # 4. Recargas. Alacritty y rofi leen su archivo al arrancar; dunst necesita
    #    que se lo digan. Alacritty solo vigila SU config principal, no el
    #    import: tocarla fuerza a releer la cadena en caliente en las ventanas
    #    ya abiertas (cambia el mtime, no el contenido).
    if [[ -f "$ALACRITTY_CONF" ]]; then
        touch "$ALACRITTY_CONF"
    fi
    reload_qtile
    if ! reload_dunst "$APP_DIR/dunstrc"; then
        echo "Aviso: dunst no recargó; conserva la configuración anterior." >&2
    fi

    if command -v dunstify >/dev/null 2>&1; then
        dunstify -a tema -r 9997 -t 1500 "Tema: $new" >/dev/null 2>&1 || true
    fi
    echo "Tema: $new (antes: $prev)"
}

case "${1:-}" in
"" | status | current)
    cur="$(current)"
    echo "Actual: $cur"
    echo "Disponibles:"
    for t in "${themes[@]}"; do
        if [[ "$t" == "$cur" ]]; then
            echo "  * $t"
        else
            echo "    $t"
        fi
    done
    ;;
list)
    printf '%s\n' "${themes[@]}"
    ;;
render)
    # Solo regenera los archivos de app del tema activo; no recarga nada.
    # Lo llama el autostart de Qtile para que dunst arranque ya tematizado.
    cur="$(current)"
    staged="$STATE_DIR/app.staging"
    rm -rf "$staged"
    render_apps "$cur" "$staged"
    commit_apps "$staged"
    ;;
toggle | next | cycle)
    cur="$(current)"
    idx=0
    for i in "${!themes[@]}"; do
        [[ "${themes[$i]}" == "$cur" ]] && idx=$i
    done
    apply "${themes[$(((idx + 1) % ${#themes[@]}))]}"
    ;;
menu)
    if command -v rofi >/dev/null 2>&1; then
        choice="$(printf '%s\n' "${themes[@]}" | rofi -dmenu -p tema)" || exit 0
        [[ -n "$choice" ]] && apply "$choice"
    else
        echo "rofi no está instalado; usa: theme.sh <tema>" >&2
        exit 1
    fi
    ;;
*)
    apply "$1"
    ;;
esac

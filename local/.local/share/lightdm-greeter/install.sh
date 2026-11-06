#!/usr/bin/env bash
# Instala (o revierte) el tema del greeter de LightDM.
#
#   sudo ./install.sh
#   sudo ./install.sh --uninstall
#
# Es idempotente: se puede ejecutar varias veces. La primera vez guarda
# copias .bak del tema y de la configuración originales.

set -euo pipefail

SRC="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
THEME_SRC="$SRC/theme/MonochromeHacker"
THEME_DST="/usr/share/themes/MonochromeHacker"
BG_SRC="$SRC/background.png"
BG_DST="/usr/share/pixmaps/monochrome-hacker.png"
CONF_SRC="$SRC/lightdm-gtk-greeter.conf"
CONF_DST="/etc/lightdm/lightdm-gtk-greeter.conf"

if [[ $EUID -ne 0 ]]; then
    echo "Ejecuta con sudo: sudo $0" >&2
    exit 1
fi

if [[ ${1:-} == "--uninstall" ]]; then
    if [[ "$THEME_DST" == /usr/share/themes/* ]]; then
        rm -rf -- "$THEME_DST"
    fi
    [[ -d "${THEME_DST}.bak" ]] && mv -- "${THEME_DST}.bak" "$THEME_DST"
    [[ -f "${CONF_DST}.bak" ]] && mv -- "${CONF_DST}.bak" "$CONF_DST"
    rm -f -- "$BG_DST"
    echo "Greeter revertido a la versión anterior."
    echo "Se aplicará en el próximo inicio de sesión."
    exit 0
fi

[[ -f "$THEME_SRC/gtk-3.0/gtk.css" ]] || { echo "Falta $THEME_SRC/gtk-3.0/gtk.css" >&2; exit 1; }
[[ -f "$BG_SRC" ]] || { echo "Falta $BG_SRC (genera con: python background.py background.png)" >&2; exit 1; }

# Copias de seguridad solo la primera vez.
if [[ -d "$THEME_DST" && ! -e "${THEME_DST}.bak" ]]; then
    cp -a -- "$THEME_DST" "${THEME_DST}.bak"
    echo "Respaldo del tema: ${THEME_DST}.bak"
fi
if [[ -f "$CONF_DST" && ! -e "${CONF_DST}.bak" ]]; then
    cp -a -- "$CONF_DST" "${CONF_DST}.bak"
    echo "Respaldo de la config: ${CONF_DST}.bak"
fi

install -d -- "$THEME_DST/gtk-3.0" /usr/share/pixmaps
install -m644 -- "$THEME_SRC/gtk-3.0/gtk.css" "$THEME_DST/gtk-3.0/gtk.css"
install -m644 -- "$THEME_SRC/index.theme"     "$THEME_DST/index.theme"
install -m644 -- "$BG_SRC"                     "$BG_DST"
install -m644 -- "$CONF_SRC"                   "$CONF_DST"

echo "Instalado:"
echo "  $THEME_DST"
echo "  $BG_DST"
echo "  $CONF_DST"
echo
echo "El greeter se aplicará en el próximo inicio de sesión."
echo "Para probarlo sin reiniciar: sudo systemctl restart lightdm (cierra la sesión)."
echo "Revertir: sudo $0 --uninstall"

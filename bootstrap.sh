#!/usr/bin/env bash
# Bootstrap de dotfiles por máquina usando GNU Stow.
#
#   ./bootstrap.sh [desktop|laptop|work-wsl] [--dry-run]
#
# - Lee los paquetes de hosts/<host>.list
# - Limpia symlinks previos que apunten a este repo (idempotente)
# - Hace stow de cada paquete en $HOME (o $TARGET)
#
# En WSL instala antes: sudo apt install stow
set -euo pipefail

REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${TARGET:-$HOME}"
DRY=0
HOST=""

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY=1 ;;
        -h|--help) echo "uso: $0 [desktop|laptop|wsl] [--dry-run]"; exit 0 ;;
        *) HOST="$arg" ;;
    esac
done

detect_host() {
    # 1) Override por máquina (el hostname es "jose" en todas las máquinas)
    if [ -f "$HOME/.dotfiles-host" ]; then
        head -n1 "$HOME/.dotfiles-host"
        return
    fi
    # 2) WSL se detecta solo por el kernel
    if grep -qi microsoft /proc/version 2>/dev/null; then
        echo "wsl"; return
    fi
    echo ""
}

[ -n "$HOST" ] || HOST="$(detect_host)"
if [ -z "$HOST" ]; then
    echo "No he podido detectar la máquina. Uso: $0 [desktop|laptop|wsl]" >&2
    echo "Consejo: crea ~/.dotfiles-host con \"desktop\" o \"laptop\" en cada máquina." >&2
    exit 1
fi

MANIFEST="$REPO/hosts/$HOST.list"
[ -f "$MANIFEST" ] || { echo "No existe $MANIFEST" >&2; exit 1; }
command -v stow >/dev/null || { echo "Falta stow: pacman -S stow | apt install stow" >&2; exit 1; }

mapfile -t PKGS < <(grep -vE '^[[:space:]]*(#|$)' "$MANIFEST")
echo "→ Host: $HOST (${#PKGS[@]} paquetes) → target: $TARGET"
[ "$DRY" = 1 ] && echo "→ MODO SIMULACIÓN (no cambia nada)"

# Submódulos (nvim) si el host los necesita
if printf '%s\n' "${PKGS[@]}" | grep -qx nvim && [ "$DRY" = 0 ]; then
    git -C "$REPO" submodule update --init --recursive
fi

# 1) Limpieza: quita symlinks de $TARGET que ya apunten dentro del repo
echo "→ Limpiando symlinks previos hacia el repo…"
while IFS= read -r -d '' link; do
    dest="$(readlink -f -- "$link" 2>/dev/null || true)"
    case "$dest" in
        "$REPO"/*)
            # No tocar el estado "enabled" de systemd (son symlinks legítimos)
            case "$link" in */systemd/user/*.wants/*) continue ;; esac
            echo "   rm $link → ${dest#"$REPO"/}"
            [ "$DRY" = 1 ] || rm -- "$link"
            ;;
    esac
done < <(find "$TARGET" -maxdepth 6 -type l -print0 2>/dev/null)

# 1b) Archivos reales en destino idénticos al repo (p. ej. apps que reescriben
#     su config): se sustituyen por el symlink de stow. Si difieren, aviso.
for pkg in "${PKGS[@]}"; do
    while IFS= read -r -d '' src; do
        rel="${src#"$REPO/$pkg"/}"
        dst="$TARGET/$rel"
        if [ -f "$dst" ] && [ ! -L "$dst" ] && cmp -s "$src" "$dst"; then
            echo "   rm $dst (idéntico al repo)"
            [ "$DRY" = 1 ] || rm -- "$dst"
        elif [ -f "$dst" ] && [ ! -L "$dst" ]; then
            echo "   AVISO: $dst difiere del repo y no se toca" >&2
        fi
    done < <(find "$REPO/$pkg" -type f -print0)
done

# 2) Stow paquete a paquete
STOW_OPTS=(--restow)
[ "$DRY" = 1 ] && STOW_OPTS+=(--simulate)

for pkg in "${PKGS[@]}"; do
    extra=()
    # qtile no se pliega en un único symlink: host-<maquina> añade host.py
    [ "$pkg" = "qtile" ] && extra+=(--no-folding)
    echo "→ stow $pkg"
    stow "${STOW_OPTS[@]}" "${extra[@]}" --dir="$REPO" --target="$TARGET" "$pkg"
done

if printf '%s\n' "${PKGS[@]}" | grep -qx local; then
    echo "ℹ Greeter LightDM: instala/actualiza el tema en el sistema con:"
    echo "    sudo ~/.local/share/lightdm-greeter/install.sh"
fi

echo "✅ Listo. Si ha cambiado algo de qtile/X11, reinicia la sesión gráfica."

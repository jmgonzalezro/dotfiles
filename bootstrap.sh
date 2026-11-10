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

# ¿El destino de un symlink sigue perteneciendo a un paquete del manifiesto?
# (el 1.er componente del path dentro del repo es el nombre del paquete)
gestionado() {
    local pk="${1#"$REPO"/}" p
    pk="${pk%%/*}"
    for p in "${PKGS[@]}"; do [ "$p" = "$pk" ] && return 0; done
    return 1
}

# 1) Limpieza: solo symlinks que apunten al repo y que ya NO pertenezcan a
#    ningún paquete del manifiesto (paquetes retirados). Los que siguen en el
#    manifiesto se dejan intactos: stow los re-crea o corrige, y así un fallo
#    de stow en un paquete jamás deja symlinks borrados a medias.
echo "→ Limpiando symlinks obsoletos hacia el repo…"
while IFS= read -r -d '' link; do
    dest="$(readlink -f -- "$link" 2>/dev/null || true)"
    case "$dest" in
        "$REPO"/*)
            # No tocar el estado "enabled" de systemd (son symlinks legítimos)
            case "$link" in */systemd/user/*.wants/*) continue ;; esac
            if gestionado "$dest"; then continue; fi
            echo "   rm $link → ${dest#"$REPO"/}"
            [ "$DRY" = 1 ] || rm -- "$link"
            ;;
    esac
done < <(find "$TARGET" -maxdepth 6 -type l -print0 2>/dev/null)

# 1b) Archivos reales en destino idénticos al repo (p. ej. apps que reescriben
#     su config): se sustituyen por el symlink de stow. Si difieren, aviso.
#     Los marcados en .stow-local-ignore se saltan: los gestiona la propia app
#     (opencode.jsonc, cli.json…), nunca deben ser symlinks.
ignorado_por_stow() {
    local pkg="$1" rel="$2" ig="$REPO/$1/.stow-local-ignore" pat
    [ -f "$ig" ] || return 1
    while IFS= read -r pat; do
        printf '%s\n' "$rel" | grep -Eq -- "$pat" && return 0
    done < <(grep -vE '^[[:space:]]*(#|$)' "$ig")
    return 1
}

for pkg in "${PKGS[@]}"; do
    while IFS= read -r -d '' src; do
        rel="${src#"$REPO/$pkg"/}"
        dst="$TARGET/$rel"
        # Si dst resuelve DENTRO del repo (el destino es una carpeta symlinkeada
        # al repo), src y dst son el MISMO fichero: "limpiarlo" borraría el
        # contenido del repo. Nunca se toca.
        case "$(readlink -f -- "$dst" 2>/dev/null || true)" in
            "$REPO"/*) continue ;;
        esac
        if ignorado_por_stow "$pkg" "$rel"; then
            continue
        elif [ -f "$dst" ] && [ ! -L "$dst" ] && cmp -s "$src" "$dst"; then
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

FAILED=()
for pkg in "${PKGS[@]}"; do
    extra=()
    # qtile no se pliega en un único symlink: host-<maquina> añade host.py
    [ "$pkg" = "qtile" ] && extra+=(--no-folding)
    echo "→ stow $pkg"
    # Un conflicto en un paquete NO aborta el resto: se informa al final.
    if ! stow "${STOW_OPTS[@]}" "${extra[@]}" --dir="$REPO" --target="$TARGET" "$pkg"; then
        echo "   AVISO: conflicto en el paquete '$pkg'; continúo con el resto" >&2
        FAILED+=("$pkg")
    fi
done

if printf '%s\n' "${PKGS[@]}" | grep -qx local; then
    echo "ℹ Greeter LightDM: instala/actualiza el tema en el sistema con:"
    echo "    sudo ~/.local/share/lightdm-greeter/install.sh"
fi

if [ "${#FAILED[@]}" -gt 0 ]; then
    echo "⚠ Paquetes con conflicto (NO instalados): ${FAILED[*]}" >&2
    echo "  Suele ser un archivo local que difiere del repo. Mira los AVISOs de arriba" >&2
    echo "  y decide cuál manda: cp local→repo, o exídelo en .stow-local-ignore." >&2
    exit 1
fi

echo "✅ Listo. Si ha cambiado algo de qtile/X11, reinicia la sesión gráfica."

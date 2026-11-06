#!/usr/bin/env python3
"""Genera la parte "de tema" de alacritty, rofi y dunst.

Lee un tema de ~/.config/qtile/themes (TOML) y escribe en un directorio de
estado tres archivos que las apps cargan como include:

    <outdir>/alacritty.toml   lo importa alacritty.toml vía [general].import
    <outdir>/rofi.rasi        lo importa config.rasi vía ?import (al final)
    <outdir>/dunstrc          config COMPLETA: dunst no admite includes, así
                              que se copia el dunstrc real sustituyendo solo
                              las claves de color/tipografía

Nada de esto vive en dotfiles: son archivos generados. La fuente de verdad
siguen siendo los .toml de temas.

Uso:
    theme-apps.py <tema.toml> --outdir DIR [--dunstrc RUTA]
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

# claves de dunstrc que dependen del tema, por sección
DUNST_KEYS = {
    "global": {
        "frame_width": lambda d: str(d["frame_width"]),
        "frame_color": lambda d: f'"{d["frame_color"]}"',
        "font": lambda d: f'"{d["font"]}"',
    },
    "urgency_low": {
        "background": lambda d: f'"{d["low_background"]}"',
        "foreground": lambda d: f'"{d["low_foreground"]}"',
        "frame_color": lambda d: f'"{d["low_frame_color"]}"',
    },
    "urgency_normal": {
        "background": lambda d: f'"{d["normal_background"]}"',
        "foreground": lambda d: f'"{d["normal_foreground"]}"',
        "frame_color": lambda d: f'"{d["normal_frame_color"]}"',
    },
    "urgency_critical": {
        "background": lambda d: f'"{d["critical_background"]}"',
        "foreground": lambda d: f'"{d["critical_foreground"]}"',
        "frame_color": lambda d: f'"{d["critical_frame_color"]}"',
    },
}

LINE_RE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z_][\w-]*)\s*=\s*(?P<value>.*)$")


def load_theme(path: Path) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def header(theme: dict, comment: str = "#") -> str:
    """Cabecera 'no editar'. El comentario cambia según el formato:
    TOML y dunstrc usan '#', rasi solo admite '//' y '/* */'."""
    text = f"Generado por theme.sh desde el tema '{theme['name']}'. No editar."
    if comment == "#":
        return f"# {text}\n"
    return f"/* {text} */\n"


def render_alacritty(theme: dict) -> str:
    a = theme["alacritty"]
    out = [header(theme), "\n[colors]\n", "draw_bold_text_with_bright_colors = true\n"]

    for index, key in ((16, "indexed_16"), (17, "indexed_17")):
        value = a.get(key)
        if value:
            out.append(f'\n[[colors.indexed_colors]]\ncolor = "{value}"\nindex = {index}\n')

    out.append(f'\n[colors.primary]\nbackground = "{a["background"]}"\nforeground = "{a["foreground"]}"\n')
    out.append(f'\n[colors.cursor]\ncursor = "{a["cursor"]}"\ntext = "{a["cursor_text"]}"\n')

    if a.get("selection_background") and a.get("selection_foreground"):
        out.append(
            "\n[colors.selection]"
            f'\nbackground = "{a["selection_background"]}"'
            f'\ntext = "{a["selection_foreground"]}"\n'
        )

    for sub in ("normal", "bright"):
        out.append(f"\n[colors.{sub}]\n")
        for colour in ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"):
            value = a[f"{sub}_{colour}"]
            out.append(f'{colour} = "{value}"\n')

    out.append(f"\n[window]\nopacity = {float(a['opacity'])}\n")
    return "".join(out)


def render_rofi_colors(theme: dict) -> str:
    """Solo variables + fuente: lo importa tanto config.rasi (vía rofi.rasi)
    como los temas auxiliares (p. ej. el selector de fondos)."""
    r = theme["rofi"]
    return f"""{header(theme, "/*")}
/* Rofi 2.0: estas variables son las que consume el tema solarized por
   defecto, así que redefinirlas recolorea todos sus estados. */
* {{
    background:           {r["background"]};
    foreground:           {r["foreground"]};
    lightbg:              {r["background"]};
    lightfg:              {r["foreground"]};
    blue:                 {r["accent"]};
    red:                  {r["urgent"]};

    bg:                   {r["background"]};
    fg:                   {r["foreground"]};
    dim:                  {r["dim"]};
    urgent:               {r["urgent"]};
    accent:               {r["accent"]};
    sel-bg:               {r["selection_background"]};
    sel-fg:               {r["selection_foreground"]};
    transparent:          transparent;

    font:                 "{r["font"]}";
}}
"""


def render_rofi(theme: dict) -> str:
    r = theme["rofi"]
    border = f"{int(r['border'])}px"
    radius = f"{int(r['radius'])}px"
    return f"""{header(theme, "/*")}
/* Import relativo: rofi lo resuelve desde este mismo directorio, así el par
   rofi.rasi + rofi-colors.rasi sigue funcionando al mover el directorio. */
?import "rofi-colors.rasi"

window {{
    background-color:     @bg;
    border:               {border};
    border-color:         {r["border_color"]};
    border-radius:        {radius};
}}

inputbar {{
    border:               0 0 {border} 0;
    border-color:         @dim;
}}

message {{
    border:               {border} 0 0 0;
    border-color:         @dim;
}}
"""


def render_dunst(theme: dict, source: Path) -> str:
    d = theme["dunst"]
    section = None
    out: list[str] = []

    for line in source.read_text(encoding="utf-8").splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].strip()
            out.append(line)
            continue

        keys = DUNST_KEYS.get(section or "")
        match = LINE_RE.match(line.rstrip("\n"))
        if keys and match and match.group("key") in keys:
            key = match.group("key")
            out.append(f"{match.group('indent')}{key} = {keys[key](d)}\n")
            continue

        out.append(line)

    return header(theme) + "".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("theme", type=Path, help="ruta al .toml del tema")
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument(
        "--dunstrc",
        type=Path,
        default=Path.home() / ".config/dunst/dunstrc",
        help="dunstrc real que sirve de plantilla",
    )
    args = parser.parse_args()

    theme = load_theme(args.theme)
    missing = [s for s in ("alacritty", "rofi", "dunst") if s not in theme]
    if missing:
        print(f"Tema '{theme.get('name', args.theme.stem)}' sin secciones: {', '.join(missing)}", file=sys.stderr)
        return 1

    outdir: Path = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    alacritty = render_alacritty(theme)
    # validación sintáctica antes de escribir: si el TOML no parsea, no se toca nada
    tomllib.loads(alacritty)

    (outdir / "alacritty.toml").write_text(alacritty, encoding="utf-8")
    (outdir / "rofi-colors.rasi").write_text(render_rofi_colors(theme), encoding="utf-8")
    (outdir / "rofi.rasi").write_text(render_rofi(theme), encoding="utf-8")

    if not args.dunstrc.is_file():
        print(f"No encuentro {args.dunstrc}; no genero dunstrc", file=sys.stderr)
        return 1
    (outdir / "dunstrc").write_text(render_dunst(theme, args.dunstrc), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

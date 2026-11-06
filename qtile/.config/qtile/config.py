# Docs: https://docs.qtile.org/

import os
import shlex
import subprocess
import tomllib
from pathlib import Path

from libqtile import bar, hook, layout, qtile, widget
from libqtile.config import (
    Click,
    Drag,
    DropDown,
    Group,
    Key,
    Match,
    Rule,
    ScratchPad,
    Screen,
)
from libqtile.lazy import lazy

terminal = "alacritty"
mod = "mod4"
HOME = os.path.expanduser

# ── Temas ──────────────────────────────────────────────────────────────
# Cada tema es un .toml en ./themes. El activo vive en
# ~/.local/state/qtile/theme (estado de máquina, fuera de dotfiles).
# QTILE_THEME=<nombre> permite probar un tema sin tocar el estado.
CONFIG_DIR = Path(__file__).resolve().parent
THEMES_DIR = CONFIG_DIR / "themes"
STATE_FILE = Path(
    os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")
) / "qtile" / "theme"
DEFAULT_THEME = "monochrome"


def available_themes():
    return sorted(path.stem for path in THEMES_DIR.glob("*.toml"))


def current_theme_name():
    try:
        name = STATE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return DEFAULT_THEME
    return name if name in available_themes() else DEFAULT_THEME


def load_theme(name):
    with (THEMES_DIR / f"{name}.toml").open("rb") as fh:
        return tomllib.load(fh)


theme = load_theme(os.environ.get("QTILE_THEME") or current_theme_name())
colors = theme["colors"]

# Overrides por máquina: el paquete stow host-<máquina> deja ~/.config/qtile/host.py
# (p. ej. host_autostart con el xrandr de cada equipo). Opcional.
host_autostart = []
HOST_FILE = CONFIG_DIR / "host.py"
if HOST_FILE.is_file():
    exec(compile(HOST_FILE.read_text(encoding="utf-8"), str(HOST_FILE), "exec"), globals())


# ── Arranque (solo una vez por sesión) ─────────────────────────────────
@hook.subscribe.startup_once
def autostart():
    # Comandos específicos de la máquina (xrandr, etc.) desde ~/.config/qtile/host.py
    for cmd in host_autostart:
        subprocess.Popen(cmd)
    # Screensaver 10 min (→ i3lock vía xss-lock) + DPMS: monitor off a los 20 min
    subprocess.Popen(["xset", "s", "600", "0"])
    subprocess.Popen(["xset", "dpms", "600", "900", "1200"])
    # xss-lock: bloquea al inactividad. NO configurar suspend/logind IdleAction:
    # el XHCI del chipset (02:00.0) está dañado y devuelve -EBUSY → el suspend rebota.
    subprocess.Popen(["xss-lock", "--transfer-sleep-lock", "--", HOME("~/.local/bin/lock.sh")])
    # Regenera los archivos de tema de las apps antes de lanzarlas: dunst no
    # admite includes, así que arranca directamente con el config generado.
    subprocess.run([HOME("~/.local/bin/theme.sh"), "render"], check=False)
    # Restaura el fondo guardado (ya no hay widget que lo sortee al recargar).
    subprocess.Popen([HOME("~/.local/bin/wallpaper.sh"), "apply"])
    themed_dunstrc = STATE_FILE.parent / "app" / "dunstrc"
    dunst_cmd = ["dunst", "--config", str(themed_dunstrc)] if themed_dunstrc.is_file() else ["dunst"]
    for cmd in (
        ["picom", "--config", HOME("~/.config/picom.conf")],
        dunst_cmd,
        ["steam", "-silent"],
    ):
        subprocess.Popen(cmd)


# ── Helpers ────────────────────────────────────────────────────────────
def move_window_to_other_screen(qtile):
    """Mueve la ventana enfocada al siguiente screen (no-op con un solo monitor)."""
    win = qtile.current_window
    if win is not None and len(qtile.screens) > 1:
        win.toscreen((win.screen.index + 1) % len(qtile.screens))


# ── Notificaciones de ventanas urgentes ────────────────────────────────
@hook.subscribe.client_urgent_hint_changed
def urgent_notification(win):
    if win.urgent:
        wm_class = win.get_wm_class()
        app = wm_class[0] if wm_class else "app"
        title = win.name or ""
        qtile.spawn(
            " ".join(
                [
                    "dunstify",
                    "-u", "critical",
                    "-r", "9998",
                    "-t", "8000",
                    "-a", shlex.quote(app),
                    shlex.quote(f"[{app}] {title}"),
                ]
            )
        )


keys = [
    # ── Sesión ──────────────────────────────────────────────────────────
    Key([mod, "shift"], "q", lazy.spawn(HOME("~/.local/bin/powermenu.sh")), desc="Menu de apagado"),
    Key([mod], "p", lazy.spawn(HOME("~/.local/bin/lock.sh")), desc="Bloquear pantalla"),
    Key([mod, "control"], "r", lazy.reload_config(), desc="Recargar config"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Cerrar Qtile"),

    # ── Temas ───────────────────────────────────────────────────────────
    Key([mod, "shift"], "t", lazy.spawn(HOME("~/.local/bin/theme.sh") + " toggle"), desc="Cambiar tema (alternar)"),
    Key([mod, "shift", "control"], "t", lazy.spawn(HOME("~/.local/bin/theme.sh") + " menu"), desc="Selector de temas"),

    # ── Lanzadores ──────────────────────────────────────────────────────
    Key([mod], "Return", lazy.spawn(terminal), desc="Terminal"),
    Key([mod, "control"], "Return", lazy.spawn(f"{terminal} -e tmux"), desc="Terminal en tmux"),
    Key([mod], "d", lazy.spawn("rofi -show combi -combi-modes window,drun -p '>'"), desc="Lanzador + selector de ventanas"),
    Key([mod], "r", lazy.spawncmd(), desc="Prompt de comandos en la barra"),
    Key([mod, "shift"], "o", lazy.spawn(f"{terminal} -e opencode"), desc="OpenCode (asistente IA)"),

    # ── Pantallas ───────────────────────────────────────────────────────
    Key([mod], "q", lazy.to_screen(0), desc="Foco a pantalla 0"),
    Key([mod], "e", lazy.to_screen(1).when(func=lambda: len(qtile.screens) > 1), desc="Foco a pantalla 1"),
    Key([mod, "shift"], "e", lazy.function(move_window_to_other_screen), desc="Mover ventana a otra pantalla"),

    # ── Foco ────────────────────────────────────────────────────────────
    Key([mod], "h", lazy.layout.left(), desc="Foco izquierda"),
    Key([mod], "l", lazy.layout.right(), desc="Foco derecha"),
    Key([mod], "j", lazy.layout.down(), desc="Foco abajo"),
    Key([mod], "k", lazy.layout.up(), desc="Foco arriba"),
    Key([mod, "control"], "Tab", lazy.group.next_window(), desc="Siguiente ventana"),
    Key([mod, "control", "shift"], "Tab", lazy.group.prev_window(), desc="Ventana anterior"),

    # ── Mover ventanas ──────────────────────────────────────────────────
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Mover ventana a la izquierda"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Mover ventana a la derecha"),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Mover ventana abajo"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Mover ventana arriba"),

    # ── Redimensionar ───────────────────────────────────────────────────
    Key([mod, "control"], "h", lazy.layout.grow_left(), desc="Redimensionar izquierda"),
    Key([mod, "control"], "l", lazy.layout.grow_right(), desc="Redimensionar derecha"),
    Key([mod, "control"], "j", lazy.layout.grow_down(), desc="Redimensionar abajo"),
    Key([mod, "control"], "k", lazy.layout.grow_up(), desc="Redimensionar arriba"),
    Key([mod], "n", lazy.layout.normalize(), desc="Resetear tamaños"),
    Key([mod, "shift"], "Return", lazy.layout.flip(), desc="Voltear master al otro lado"),

    # ── Layouts ─────────────────────────────────────────────────────────
    Key([mod], "Tab", lazy.next_layout(), desc="Siguiente layout"),
    Key([mod, "shift"], "Tab", lazy.prev_layout(), desc="Layout anterior"),

    # ── Estado de la ventana ────────────────────────────────────────────
    Key([mod], "w", lazy.window.kill(), desc="Cerrar ventana"),
    Key([mod], "f", lazy.window.toggle_fullscreen(), desc="Fullscreen"),
    Key([mod], "t", lazy.window.toggle_floating(), desc="Floating"),
    Key([mod], "m", lazy.window.toggle_minimize(), desc="Minimizar"),
    Key([mod, "shift"], "m", lazy.group.unminimize_all(), desc="Restaurar minimizadas"),

    # ── Navegación entre grupos ─────────────────────────────────────────
    Key([mod], "period", lazy.screen.next_group(), desc="Grupo siguiente"),
    Key([mod], "comma", lazy.screen.prev_group(), desc="Grupo anterior"),
    Key([mod], "grave", lazy.screen.toggle_group(), desc="Ultimo grupo (toggle)"),

    # ── Scratchpads ─────────────────────────────────────────────────────
    Key([mod], "minus", lazy.group["scratchpad"].dropdown_toggle("term"), desc="Terminal dropdown"),
    Key([mod, "shift"], "minus", lazy.group["scratchpad"].dropdown_toggle("calendar"), desc="Calendario (calcurse)"),
    Key([mod, "control"], "minus", lazy.group["scratchpad"].dropdown_toggle("sysmon"), desc="Monitor de sistema (btop)"),

    # ── Audio ───────────────────────────────────────────────────────────
    Key([], "XF86AudioMute", lazy.spawn(HOME("~/.local/bin/volume.sh") + " mute")),
    Key([], "XF86AudioLowerVolume", lazy.spawn(HOME("~/.local/bin/volume.sh") + " down")),
    Key([], "XF86AudioRaiseVolume", lazy.spawn(HOME("~/.local/bin/volume.sh") + " up")),

    # ── Capturas de pantalla ────────────────────────────────────────────
    Key([mod], "Print", lazy.spawn(HOME("~/.local/bin/screenshot.sh") + " full"), desc="Screenshot + portapapeles"),
    Key([mod, "control"], "Print", lazy.spawn(HOME("~/.local/bin/screenshot.sh") + " area"), desc="Screenshot area + portapapeles"),

    # ── Idioma del teclado ──────────────────────────────────────────────
    Key([mod], "space", lazy.widget["keyboardlayout"].next_keyboard(), desc="Siguiente layout de teclado"),
]

# Teclas para cambiar de VT (solo activo en Wayland)
for vt in range(1, 8):
    keys.append(
        Key(
            ["control", "mod1"],
            f"f{vt}",
            lazy.core.change_vt(vt).when(func=lambda: qtile.core.name == "wayland"),
            desc=f"Switch to VT{vt}",
        )
    )

groups = [Group(name) for name in "12345"]

for group in groups:
    keys.extend(
        [
            Key(
                [mod],
                group.name,
                lazy.group[group.name].toscreen(),
                desc="Ir al grupo {}".format(group.name),
            ),
            Key(
                [mod, "shift"],
                group.name,
                lazy.window.togroup(group.name, switch_group=True),
                desc="Mover ventana al grupo {} y seguirla".format(group.name),
            ),
            Key(
                [mod, "control"],
                group.name,
                lazy.window.togroup(group.name),
                desc="Mover ventana al grupo {}".format(group.name),
            ),
        ]
    )

groups.append(
    ScratchPad(
        "scratchpad",
        [
            DropDown(
                "term",
                terminal,
                opacity=0.95,
                height=0.7,
                width=0.7,
                x=0.15,
                y=0.15,
                on_focus_lost_hide=True,
            ),
            # calcurse -> www.calcurse.org
            DropDown(
                "calendar",
                f"{terminal} -e calcurse",
                opacity=0.95,
                height=0.5,
                width=0.5,
                x=0.25,
                y=0.25,
                on_focus_lost_hide=True,
            ),
            DropDown(
                "sysmon",
                f"{terminal} -e btop",
                opacity=0.95,
                height=0.7,
                width=0.6,
                x=0.2,
                y=0.15,
                on_focus_lost_hide=True,
            ),
            # pacman -Syu en consola emergente inferior (Enter cancela sudo,
            # una tecla cierra al terminar)
            DropDown(
                "updates",
                f"{terminal} -e bash -c 'sudo pacman -Syu; echo; read -n1 -p \"Pulsa una tecla para cerrar...\"'",
                opacity=0.95,
                height=0.42,
                width=1.0,
                x=0.0,
                y=0.55,
                on_focus_lost_hide=True,
            ),
        ],
    )
)

widget_defaults = dict(
    font=theme["font"],
    fontsize=theme["fontsize"],
    padding=4,
    foreground=colors["fg"],
)
extension_defaults = widget_defaults.copy()


def make_bar(include_systray=True):
    """Barra inferior. Solo la pantalla principal debe llevar el Systray."""
    widgets = [
        widget.GroupBox(
            highlight_method=theme["groupbox_highlight_method"],
            borderwidth=theme["groupbox_borderwidth"],
            rounded=False,
            this_current_screen_border=colors["accent"],
            this_screen_border=colors["dim"],
            other_current_screen_border=colors["dim"],
            other_screen_border=colors["border_normal"],
            active=colors["fg"],
            inactive=colors["dim"],
            urgent_border=colors["urgent"],
            urgent_text=colors["urgent"],
            disable_drag=True,
        ),
        # padding 2: el GroupBox deja 10px a su derecha y WindowName 5.2 a la
        # suya; con 2 los huecos quedan en 12/7.2 (centro ≈9.5, como la derecha).
        widget.CurrentLayout(mode="icon", scale=0.6, foreground=colors["accent"], padding=2),
        widget.Prompt(cursor_type="block", prompt="> "),
        widget.WindowName(
            stretch=True,
            empty_group_string=" ",
            max_chars=100,
            foreground=colors["fg"],
        ),
        widget.CheckUpdates(
            # El widget cuenta LÍNEAS de salida: el script imprime un paquete
            # por línea (vacío si no hay updates) — sin | wc -l.
            custom_command=f"{HOME('~/.local/bin/checkupdates-repo')} 2>/dev/null",
            display_format="\uf0ac {updates}",
            padding=0,  # el "1" termina a 0.8px de la celda: hueco final ≈9.8
            no_update_string="",
            colour_have_updates=colors["urgent"],
            colour_no_updates=colors["fg"],
            update_interval=1800,
            mouse_callbacks={
                "Button1": lazy.group["scratchpad"].dropdown_toggle("updates"),
            },
        ),
        # Test de velocidad -> notificación dunst con ping/bajada/subida.
        #  = md-speedometer: arco + aguja, como cualquier velocímetro.
        # fontsize 15 para que su ink (12.5px) iguale al del resto de iconos
        # (globo/imagen/power = 11-12px). padding 9 porque este glifo se sale
        # 3.5px de su celda monoespaciada: 9 - 3.5 + 4 (Volume) = hueco 9.5.
        widget.TextBox(
            text="\U000f04c5",
            fontsize=15,
            padding=9,
            foreground=colors["fg"],
            mouse_callbacks={
                "Button1": lazy.spawn(HOME("~/.local/bin/speedtest.sh")),
            },
        ),
        widget.Volume(
            # Dos espacios: el altavoz (ink 15px) se sale de su celda de 7.8px
            # y con uno solo quedaba pegado al número.
            unmute_format="\uf028  {volume}%",
            mute_format="MUTE",
            mute_foreground=colors["urgent"],
            volume_app="pavucontrol",
            get_volume_command="pactl get-sink-volume @DEFAULT_SINK@",
            check_mute_command="pactl get-sink-mute @DEFAULT_SINK@",
            check_mute_string="yes",
            mute_command="pactl set-sink-mute @DEFAULT_SINK@ toggle",
            volume_up_command=HOME("~/.local/bin/volume.sh") + " up",
            volume_down_command=HOME("~/.local/bin/volume.sh") + " down",
        ),
        # padding 3: sus letras aportan 1.2px internos; 3+1.2+3+1.2 ≈ 9.
        widget.KeyboardLayout(configured_keyboards=["us", "es"], padding=3),
    ]
    if include_systray:
        # icon_size 12: tapa dura de Qtile sobre la altura -> ink 12px, igual
        # que globo/imagen/power. padding 5: el icono se sale 4px de su caja,
        # así que 5-4+8 (selector de fondo) = hueco 9.
        widgets.append(widget.Systray(padding=5, icon_size=12))
    widgets += [
        # Selector visual de fondos: antes era widget.Wallpaper, que además
        # re-sorteaba el fondo en cada recarga de Qtile. Ahora el icono solo
        # abre la rejilla de rofi (izq.) o sortea (der.); el fondo se guarda
        # en ~/.local/state/qtile/wallpaper.
        widget.TextBox(
            text="\uf03e",
            # Este glifo se sale 4.2px de su celda; con padding 8 el hueco
            # resultante con el reloj queda en ~9px, igual que el resto.
            padding=8,
            mouse_callbacks={
                "Button1": lazy.spawn(HOME("~/.local/bin/wallpaper.sh") + " menu"),
                "Button3": lazy.spawn(HOME("~/.local/bin/wallpaper.sh") + " random"),
            },
        ),
        widget.Clock(
            format="%a %d %b %H:%M:%S",
            mouse_callbacks={
                "Button1": lazy.group["scratchpad"].dropdown_toggle("calendar")
            },
        ),
        widget.TextBox(
            text="\uf011",
            padding=4,
            mouse_callbacks={"Button1": lazy.spawn(HOME("~/.local/bin/powermenu.sh"))},
        ),
    ]
    return bar.Bar(
        widgets,
        theme["bar_size"],
        background=theme["bar_background"],
        opacity=theme["bar_opacity"],
        border_width=theme["bar_border_width"],
        border_color=theme["bar_border_color"],
    )


screens = [Screen(**{theme["bar_position"]: make_bar()})]
# Con un segundo monitor, añadir:
# screens.append(Screen(bottom=make_bar(include_systray=False)))

# Arrastrar/redimensionar ventanas flotantes con el ratón
mouse = [
    Drag(
        [mod],
        "Button1",
        lazy.window.set_position_floating(),
        start=lazy.window.get_position(),
    ),
    Click(
        [mod],
        "Button2",
        lazy.window.bring_to_front(),
    ),
    Drag(
        [mod],
        "Button3",
        lazy.window.set_size_floating(),
        start=lazy.window.get_size(),
    ),
]

dgroups_key_binder = None
dgroups_app_rules = [
    Rule(Match(wm_class="steam"), group="5"),
    Rule(Match(wm_class="steamwebhelper"), group="5"),
]
follow_mouse_focus = True
bring_front_click = False
floats_kept_above = True
cursor_warp = False
floating_layout = layout.Floating(
    border_focus=colors["border_focus"],
    border_normal=colors["border_normal"],
    float_rules=[
        # Run the utility of `xprop` to see the wm class and name of an X client.
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
        Match(wm_class="steam", title="Friends List"),
        Match(wm_class="steam", title="Settings"),
        Match(wm_class="steam", title="Screenshot Uploader"),
        Match(wm_class="steam", title="Steam - News"),
        Match(wm_class="feh"),
    ]
)

layouts = [
    layout.Max(),
    layout.MonadTall(
        margin=theme["layout"]["margin"],
        border_width=theme["layout"]["border_width"],
        border_focus=colors["border_focus"],
        border_normal=colors["border_normal"],
        ratio=theme["layout"]["ratio_tall"],
    ),
    layout.MonadWide(
        margin=theme["layout"]["margin"],
        border_width=theme["layout"]["border_width"],
        border_focus=colors["border_focus"],
        border_normal=colors["border_normal"],
        ratio=theme["layout"]["ratio_wide"],
    ),
]

auto_minimize = False
auto_fullscreen = True

focus_on_window_activation = "smart"  # urgent, focus, smart
reconfigure_screens = True

wl_input_rules = None

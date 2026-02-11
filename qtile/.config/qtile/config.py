from libqtile import bar, layout, qtile, widget
import libqtile
from libqtile.config import Click, Drag, Group, Key, Match, Screen, ScratchPad, DropDown
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal

from qtile_extras import widget as widget_extras
import qtile_extras
import qtile_extras.hook

import os

os.system("picom &")
os.system("dunst &")

if qtile.core.name == "x11":
    term = "urxvt"
elif qtile.core.name == "wayland":
    term = "foot"
mod = "mod4"


def open_calendar(qtile):
    qtile.spawn('gsimplecal')


def close_calendar(qtile):
    qtile.spawn('killall -q gsimplecal')


def open_pavucontrol():
    qtile.spawn("pavucontrol")


def open_nm_connection_editor():
    qtile.spawn("nm-connection-editor")


def open_rofi_wifi_menu():
    qtile.spawn("/home/jose/.local/bin/rofi-wifi-menu")


@qtile_extras.hook.subscribe.up_battery_critical
def battery_critical(battery_name):
    qtile.spawn('notify-send "Battery is critical" -u "critical"')


@qtile_extras.hook.subscribe.up_battery_full
def battery_full(battery_name):
    battery_status = os.popen(f"upower -i $(upower -e | grep {battery_name}) | grep state").read()
    if "fully-charged" in battery_status:
        qtile.spawn('notify-send "Battery is fully charged" -u "low"')


@qtile_extras.hook.subscribe.up_battery_low
def battery_low(battery_name):
    qtile.spawn("notify-send 'Battery is running low' -u 'normal'")


@qtile_extras.hook.subscribe.up_power_connected
def plugged_in():
    qtile.spawn("notify-send 'Battery is connected' -u 'normal'")
    qtile.spawn("paplay ~/Downloads/Thip.ogg")


@qtile_extras.hook.subscribe.up_power_disconnected
def unplugged():
    qtile.spawn("notify-send 'Battery is disconnected' -u 'normal'")
    qtile.spawn("paplay ~/Downloads/Thip.ogg")
    # qtile.spawn("ffplay power_off.wav")


terminal = guess_terminal()

keys = [
    Key([mod], "h", lazy.layout.left(), desc="Move focus to left"),
    Key([mod], "l", lazy.layout.right(), desc="Move focus to right"),
    Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
    Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
    Key([mod, "control"], "l", lazy.group.next_window(), desc="Move window focus to other window",),
    # Move windows between left/right columns or move up/down in current stack.
    # Moving out of range in Columns layout will create new column.
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Move window to the left"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Move window to the right",),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move window down"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),
    # Cambiar entre layouts
    Key([mod], "Tab", lazy.next_layout(), desc="Cambiar al siguiente layout"),
    Key([mod, "shift"], "Tab", lazy.prev_layout(), desc="Cambiar al anterior layout"),
    # Grow windows. If current window is on the edge of screen and direction
    # will be to screen edge - window would shrink.
    Key([mod, "control"], "h", lazy.layout.grow_left(), desc="Grow window to the left"),
    Key([mod, "control"], "l", lazy.layout.grow_right(), desc="Grow window to the right"),
    Key([mod, "control"], "j", lazy.layout.grow_down(), desc="Grow window down"),
    Key([mod, "control"], "k", lazy.layout.grow_up(), desc="Grow window up"),
    Key([mod], "n", lazy.layout.normalize(), desc="Reset all window sizes"),
    Key([mod], "d", lazy.spawn("rofi -show drun")),
    # Toggle between split and unsplit sides of stack.
    # Split = all windows displayed
    # Unsplit = 1 window displayed, like Max layout, but still with
    # multiple stack panes
    Key([mod, "shift"], "Return", lazy.layout.toggle_split(), desc="Toggle between split and unsplit sides of stack"),
    Key([mod], "Return", lazy.spawn(terminal), desc="Launch terminal"),
    # Toggle between different layouts as defined below
    Key([mod], "w", lazy.window.kill(), desc="Kill focused window"),
    Key([mod], "f", lazy.window.toggle_fullscreen(), desc="Toggle fullscreen on the focused window",),
    Key([mod], "t", lazy.window.toggle_floating(), desc="Toggle floating on the focused window",),
    Key([mod, "control"], "r", lazy.reload_config(), desc="Reload the config"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
    Key([mod], "r", lazy.spawncmd(), desc="Spawn a command using a prompt widget"),
    Key([mod], "space", lazy.widget["keyboardlayout"].next_keyboard(), desc="Next keyboard layout",),
    Key([], "XF86AudioMute", lazy.spawn("pactl set-sink-mute @DEFAULT_SINK@ toggle")),
    Key([], "XF86AudioLowerVolume", lazy.spawn("amixer sset Master 5%-")),
    Key([], "XF86AudioRaiseVolume", lazy.spawn("amixer sset Master 5%+")),
    # Brightness
    Key([], "XF86MonBrightnessUp", lazy.spawn("brightnessctl set +5%")),
    Key([], "XF86MonBrightnessDown", lazy.spawn("brightnessctl set 5%-")),
    # Screenshtos
    Key([mod], "Print", lazy.spawn("scrot /home/jose/Images/%Y-%m-%d-%T-screenshot.png"),),
    Key([mod, 'control'], "Print", lazy.spawn("scrot -s /home/jose/Images/%Y-%m-%d-%T-screenshot.png"),),
]

# Add key bindings to switch VTs in Wayland.
# We can't check qtile.core.name in default config as it is loaded before qtile is started
# We therefore defer the check until the key binding is run by using .when(func=...)
for vt in range(1, 8):
    keys.append(
        Key(
            ["control", "mod1"],
            f"f{vt}",
            lazy.core.change_vt(vt).when(
                func=lambda: qtile.core.name == "wayland"),
            desc=f"Switch to VT{vt}",
        )
    )


groups = [Group(i) for i in "12345"]

for i in groups:
    keys.extend(
        [
            # mod1 + group number = switch to group
            Key(
                [mod],
                i.name,
                lazy.group[i.name].toscreen(),
                desc="Switch to group {}".format(i.name),
            ),
            # mod1 + shift + group number = switch to & move focused window to group
            Key(
                [mod, "shift"],
                i.name,
                lazy.window.togroup(i.name, switch_group=True),
                desc="Switch to & move focused window to group {}".format(
                    i.name),
            ),
            # # mod1 + control + group number = move focused window to group
            Key([mod, "control"], i.name, lazy.window.togroup(i.name),
                desc="move focused window to group {}".format(i.name)),
        ]
    )

# groups.append(
#     ScratchPad("scratchpad", [
#         DropDown("pavucontrol", "pavucontrol", width=0.8, height=0.8, x=0.1, y=0.1, opacity=0.9),
#     ])
# )

widget_defaults = dict(
    font="sans",
    fontsize=14,
    padding=5,
)
extension_defaults = widget_defaults.copy()

screens = [
    Screen(
        bottom=bar.Bar(
            [
                widget.GroupBox(),
                widget.CurrentLayout(
                    mode='both',
                    foreground='ff5733',
                    scale=0.6,
                    spacing=5,
                ),
                widget.Prompt(),
                widget.WindowName(),
                widget.Chord(
                    chords_colors={
                        "launch": ("#ff0000", "#ffffff"),
                    },
                    name_transform=lambda name: name.upper(),
                ),
                widget.Systray(),
                widget.Volume(
                    emoji=True,
                    volume_app="PulseAudio Volume Control",
                    mute_format=" ",
                    emoji_list=["", "", "", "", " "],
                    mute_foreground="ff5733",
                    fontsize=16,
                    width=25,
                    mouse_callbacks={"Button1": open_pavucontrol},
                ),
                widget.Volume(
                    volume_app="PulseAudio Volume Control",
                    mute_foreground="ff5733",
                    fmt="{}",
                    fontsize=16,
                    mouse_callbacks={"Button1": open_pavucontrol},
                ),
                widget.Backlight(
                    backlight_name="intel_backlight",
                    fontsize=16,
                    format=" {percent:2.0%}",
                ),
                widget_extras.WiFiIcon(
                    mouse_callbacks={
                        "Button3": open_nm_connection_editor,
                    },
                    wifi_arc=90,
                ),
                widget_extras.Bluetooth(
                    default_text="",
                    fontsize=16,
                ),
                widget.KeyboardLayout(configured_keyboards=["us", "es"]),
                widget.Wallpaper(
                    directory="~/Images/wallpapers/",
                    label=" ",
                    fontsize=16,
                    option="fill",
                    random_selection=True,
                ),
                widget_extras.UPowerWidget(
                    battery_height=10,
                    fill_critical='#cc0000',
                    fill_low='#aa00aa',
                    percentage_low=0.2,
                    percentage_critical=0.1,
                    spacing=5,
                ),
                widget.Clock(
                    format="%Y-%m-%d - %H:%M",
                    fontsize=16,
                    mouse_callbacks={'Button1': lambda: qtile.spawn('gsimplecal')},
                ),
            ],
            24,
        ),
    ),
]

# Drag floating layouts.
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
        lazy.window.bring_to_front()
    ),
    Drag(
        [mod],
        "Button3",
        lazy.window.set_size_floating(), start=lazy.window.get_size()
    ),
]

dgroups_key_binder = None
dgroups_app_rules = []  # type: list
follow_mouse_focus = True
bring_front_click = False
floats_kept_above = True
cursor_warp = False
floating_layout = layout.Floating(
    float_rules=[
        # Run the utility of `xprop` to see the wm class and name of an X client.
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
    ]
)

layouts = [
    layout.Max(),
    layout.MonadTall(margin=8, border_width=2, border_focus="#0000ff", ratio=0.6),
    layout.MonadWide(margin=8, border_width=2, border_focus="#0000ff", ratio=0.7),
]


auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True

auto_minimize = True

wl_input_rules = None

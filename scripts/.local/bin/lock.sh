#!/bin/sh

# Monocromo hacker: bg #0a0a0a · fg #e6e6e6 · dim #5c5c5c · accent #ff0000
BG='#0a0a0aff'
FG='#e6e6e6ff'
DIM='#5c5c5cff'
ACCENT='#ff0000ff'
CLEAR='#00000000'

i3lock \
    --nofork \
    --ignore-empty-password \
    --inside-color=$CLEAR \
    --ring-color=$DIM \
    --line-color=$CLEAR \
    --separator-color=$DIM \
    --insidever-color=$CLEAR \
    --ringver-color=$FG \
    --insidewrong-color=$CLEAR \
    --ringwrong-color=$ACCENT \
    --verif-color=$FG \
    --wrong-color=$ACCENT \
    --time-color=$FG \
    --date-color=$DIM \
    --layout-color=$DIM \
    --keyhl-color=$ACCENT \
    --bshl-color=$ACCENT \
    --time-font="JetBrainsMono Nerd Font" \
    --time-size=48 \
    --date-font="JetBrainsMono Nerd Font" \
    --date-size=16 \
    --blur 5 \
    --clock \
    --indicator \
    --time-str="%H:%M" \
    --date-str="%A, %d %B"
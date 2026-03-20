---
description: "Control Ubuntu desktop UI from the terminal — find windows, send mouse/keyboard events, take and analyze screenshots. Use when you need to interact with GUI applications like Minecraft, browsers, file managers, or any X11 application."
---

# Ubuntu Screen Interaction Skill

## Overview

This skill enables an AI agent to interact with the Ubuntu X11 desktop from the terminal — finding windows, sending clicks and keystrokes, capturing screenshots, and analyzing screen content to verify actions worked.

## Prerequisites

### Detect your DISPLAY

The `$DISPLAY` variable may differ from `:0`. Always detect it first:

```bash
echo $DISPLAY              # Check current shell's DISPLAY
# If empty or wrong, find it:
ps aux | grep Xorg          # Look for the display number in args (e.g., vt2 = :1)
ls /tmp/.X11-unix/          # Lists X sockets like X0, X1
```

**Important:** Every X11 command must use the correct display. Set `DISPLAY=:1` (or whatever your display is) as a prefix for every command, or export it.

### Install tools

```bash
# Core tools (apt)
sudo apt-get install -y \
  scrot          \  # Screenshot capture
  xdotool        \  # Window management + synthetic input
  xautomation    \  # xte: XTest-based input (works with LWJGL/Java apps)
  wmctrl         \  # Window listing, activation, positioning
  x11-utils         # xprop, xwininfo, xlsclients

# Python packages
pip3 install --break-system-packages \
  Pillow         \  # Screenshot analysis (crop, pixel sampling)
  python-xlib       # XTest protocol fallback for input events
```

```bash
# Additional Python packages (optional, fast but more deps)
pip3 install --break-system-packages \
  pyautogui      \  # Fast mouse/key (needs python3-tk)
  pynput            # XTest-based input, scriptable
sudo apt-get install -y python3-tk  # Required by pyautogui
```

### Tool NOT available / broken

| Tool | Status | Notes |
|------|--------|-------|
| `ydotool` | **Broken** on most Ubuntu setups | Requires ydotoold daemon + uinput access, usually fails with permission errors |
| `dotool` | **Not in apt** | Not packaged for Ubuntu |
| `gnome-screenshot` | Not installed by default | `scrot` is lighter and faster |

---

## Tier List: What Works

> **Updated with data from benchmark.py** — 10 trials × 4 tests × 5 tools.
> LWJGL tested against Minecraft 1.21.11 with screenshot-diff verification.

### Tier 1: Recommended

| Tool | Purpose | Speed | Notes |
|------|---------|-------|-------|
| `xte` | Mouse + keyboard input | 1.2ms click, 1.1ms key | XTest extension. Best balance of speed + simplicity. No deps beyond apt. |
| `wmctrl` | List + activate windows | — | Reliable. Works by title substring. |
| `scrot` | Screenshots | ~0.7s full screen | Fast, no deps. |
| `xprop` / `xwininfo` | Window properties + geometry | — | Essential for coordinate calculation. |
| Pillow (Python) | Screenshot analysis | — | Crop, pixel sampling, color detection. |

### Tier 1.5: Fast Alternatives

| Tool | Purpose | Speed | Notes |
|------|---------|-------|-------|
| `pyautogui` | Mouse + keyboard (Python) | **0.5ms click, 0.2ms key** (fastest) | Requires `python3-tk`. Uses Xlib internally. FAILSAFE must be disabled. |
| `pynput` | Mouse + keyboard (Python) | 1.3ms click, 1.2ms key | XTest-based. Clean API. Minimal deps. |

### Tier 2: Usable but Slower

| Tool | Purpose | Speed | Notes |
|------|---------|-------|-------|
| `xdotool` | Window management + input | **102ms click**, 13.6ms key (slowest) | Good for `windowactivate --sync`. Slow clicks due to subprocess + 100ms internal delay. |
| `python-xlib` XTest | Programmatic XTest events | 21.6ms click, 11.3ms key | More verbose than `xte`, but fully scriptable. Display open/close overhead. |

### Tier 3: Avoid

| Tool | Why |
|------|-----|
| `ydotool` | Permission issues, daemon requirement, not working on Ubuntu |
| `dotool` | Not in Ubuntu apt repos |

---

## Recipes

### 1. List all windows

```bash
DISPLAY=:1 wmctrl -l
```

Output:
```
0x00c00004  0 hostname  Visual Studio Code
0x03600017  0 hostname  Mozilla Firefox
0x04a0000b  0 hostname  Minecraft 1.21.11 - Singleplayer
```

### 2. Activate (raise + focus) a window by title

```bash
DISPLAY=:1 wmctrl -a "Firefox"           # Partial match on title
```

**Warning:** `wmctrl -a` matches the FIRST window containing the string. If multiple windows match (e.g., "Minecraft Launcher" and "Minecraft 1.21.11 - Singleplayer"), use the window ID instead:

```bash
# Find the specific window ID
GAME_WID=$(DISPLAY=:1 wmctrl -l | grep "Singleplayer" | awk '{print $1}')
DISPLAY=:1 wmctrl -i -a "$GAME_WID"     # -i = by ID

# Or use xdotool windowactivate for guaranteed focus:
DISPLAY=:1 xdotool windowactivate --sync "$GAME_WID"
```

### 3. Get window geometry

```bash
# By window ID
DISPLAY=:1 xwininfo -id 0x04a0000b

# Interactive (click to select)
DISPLAY=:1 xwininfo
```

Key output fields:
```
Absolute upper-left X: 972
Absolute upper-left Y: 840
Width: 2015
Height: 761
```

### 4. Get window ID by name

```bash
DISPLAY=:1 xdotool search --name "Minecraft"    # Returns window ID(s)
```

Or from wmctrl:
```bash
DISPLAY=:1 wmctrl -l | grep "Minecraft" | awk '{print $1}'
```

### 5. Send mouse click (works with ALL apps including Java/LWJGL)

```bash
# Move mouse to absolute screen coordinates, then click
DISPLAY=:1 xte 'mousemove 2007 1200'    # Move to (2007, 1200)
DISPLAY=:1 xte 'mouseclick 1'            # Left click (1=left, 2=middle, 3=right)
```

**Chained (recommended):**
```bash
DISPLAY=:1 xte 'mousemove 2007 1200' 'mouseclick 1'
```

**Double-click:**
```bash
DISPLAY=:1 xte 'mousemove 2007 1200' 'mouseclick 1' 'mouseclick 1'
```

### 6. Send keyboard input

```bash
# Single key
DISPLAY=:1 xte 'key Escape'
DISPLAY=:1 xte 'key Return'
DISPLAY=:1 xte 'key Tab'
DISPLAY=:1 xte 'key t'

# Type a string
DISPLAY=:1 xte 'str /tp @s 500 200 500'

# Key combo (Ctrl+C)
DISPLAY=:1 xte 'keydown Control_L' 'key c' 'keyup Control_L'
```

### 7. Take a screenshot

```bash
# Full screen
DISPLAY=:1 scrot /tmp/screenshot.png

# Specific window (by focus)
DISPLAY=:1 scrot -u /tmp/focused_window.png

# After delay
DISPLAY=:1 scrot -d 3 /tmp/delayed.png
```

### 8. Analyze screenshot with Python

```python
from PIL import Image

img = Image.open('/tmp/screenshot.png')
w, h = img.size

# Crop a specific window area (x, y, x+w, y+h)
window = img.crop((972, 840, 972+2015, 840+761))

# Sample pixel colors
px = window.getpixel((100, 100))  # (R, G, B)

# Detect sky blue (outdoor Minecraft view)
sky_count = 0
for y in range(0, h//4, 5):
    for x in range(0, w, 20):
        r, g, b = img.getpixel((x, y))[:3]
        if b > 150 and b > r and b > g:
            sky_count += 1
print(f"Sky pixels: {sky_count}")

# Detect brightness (is screen dark = underground/menu?)
total = sum(sum(img.getpixel((x, y))[:3])/3 
            for y in range(0, h, 20) for x in range(0, w, 20))
samples = (h//20) * (w//20)
print(f"Avg brightness: {total/samples:.0f}")
```

### 9. Full workflow: activate window → click → verify

```bash
# Step 1: Activate the target window
DISPLAY=:1 wmctrl -a "Minecraft"
sleep 0.5

# Step 2: Get its geometry
DISPLAY=:1 xwininfo -name "Minecraft" 2>/dev/null | grep -E "Absolute|Width|Height"

# Step 3: Click at a computed position
# (e.g., center of window = abs_x + width/2, abs_y + height/2)
DISPLAY=:1 xte 'mousemove 1979 1220' 'mouseclick 1'
sleep 1

# Step 4: Screenshot and verify
DISPLAY=:1 scrot /tmp/verify.png
```

### 10. XTest via Python (programmatic alternative to xte)

```python
import os, time
os.environ['DISPLAY'] = ':1'
from Xlib import X, display
from Xlib.ext import xtest

d = display.Display(':1')

# Move mouse
xtest.fake_input(d, X.MotionNotify, detail=0, x=2007, y=1200)
d.sync()
time.sleep(0.2)

# Click
xtest.fake_input(d, X.ButtonPress, detail=1)
d.sync()
time.sleep(0.05)
xtest.fake_input(d, X.ButtonRelease, detail=1)
d.sync()

# Press key (keycode 9 = Escape, 36 = Return)
xtest.fake_input(d, X.KeyPress, detail=9)
d.sync()
time.sleep(0.05)
xtest.fake_input(d, X.KeyRelease, detail=9)
d.sync()

d.close()
```

---

## Key Gotchas

### LWJGL/Java/OpenGL apps: all XTest tools work, but focus matters

All 5 tested tools (xdotool, xte, pyautogui, pynput, python-xlib) successfully sent keyboard input to Minecraft 1.21.11 (LWJGL), producing identical 24.2% pixel change in ESC-toggle tests.

The critical requirement is **proper window focus**:
```bash
# CORRECT: use windowactivate --sync first, then send input
DISPLAY=:1 xdotool windowactivate --sync <WINDOW_ID>
sleep 0.5
DISPLAY=:1 xte 'key Escape'

# WRONG: wmctrl -a may match the wrong window (e.g., launcher instead of game)
DISPLAY=:1 wmctrl -a "Minecraft"  # May focus Minecraft Launcher, not the game!
```

**Key insight:** Earlier assumptions that xdotool's `SendEvent` mechanism fails with LWJGL were caused by focus problems, not tool limitations. When the window is properly focused with `xdotool windowactivate --sync`, all tools work equally.

**For mouse clicks on LWJGL apps**, prefer XTest-based tools (xte, pynput, python-xlib) as xdotool's `SendEvent` for mouse clicks may be less reliable than for keyboard events.

### DISPLAY must be correct

Terminals spawned by VS Code, SSH, or cron often have `DISPLAY=:0` or unset. The actual desktop may be on `:1`. Always verify:

```bash
echo $DISPLAY                    # Current
ls /tmp/.X11-unix/               # Available displays
ps aux | grep Xorg | grep -oP 'vt\d+'  # Which VT → display number
```

### Window coordinates are ABSOLUTE screen coordinates

`xte mousemove` uses absolute screen coordinates, not window-relative. To click inside a window:

```
click_x = window_abs_x + relative_x_within_window
click_y = window_abs_y + relative_y_within_window
```

Get `window_abs_x/y` from `xwininfo`.

### Minecraft window title stays "Singleplayer" even when in-game

Don't rely on the window title to detect Minecraft state. Instead:
- Check `~/.minecraft/logs/latest.log` for `ServerLevel[WorldName]` entries
- Analyze screenshot brightness/colors (sky blue = outdoor, dark = underground/menu)

### Screenshots on high-DPI / multi-monitor

`scrot` captures the full X root, which may be large (e.g., 5120x2160). Use Pillow to crop to the window area before analysis.

---

## Benchmark Results

> Run `benchmark.py` in this directory to reproduce. Tested on Ubuntu 22.04, X11, 1920x1080.

### Speed (avg ms, 10 trials per test)

| Tool | mouse_move | mouse_click | key_press | Notes |
|------|-----------|-------------|-----------|-------|
| xdotool | 51.3 | **102.0** | 13.6 | Slowest clicks (subprocess + internal 100ms delay) |
| xte | 51.2 | 1.2 | 1.1 | Consistent, fast |
| pyautogui | 53.4 | **0.5** | **0.2** | Fastest (native Python, no subprocess) |
| pynput | 52.0 | 1.3 | 1.2 | Similar to xte |
| python-xlib | 51.1 | 21.6 | 11.3 | Display open/close overhead per call |

All tools achieved **100% success rate** on mouse_move, mouse_click, and key_press tests.

### LWJGL/Java Compatibility (Minecraft 1.21.11)

| Tool | ESC Toggle | Pixel Change | Method |
|------|-----------|-------------|--------|
| xdotool | ✓ | 24.2% | XSendEvent (keyboard) |
| xte | ✓ | 24.2% | XTest extension |
| pyautogui | ✓ | 24.2% | Xlib keyboard |
| pynput | ✓ | 24.2% | XTest extension |
| python-xlib | ✓ | 24.2% | XTest extension |

All tools reached LWJGL when the window was properly focused via `xdotool windowactivate --sync`.

### Recommendation

- **Default choice:** `xte` — fast, reliable, zero Python deps, works everywhere
- **Python scripting:** `pynput` — clean API, XTest-based, minimal deps
- **Max speed:** `pyautogui` — fastest clicks/keys, but requires `python3-tk`
- **Window management:** `xdotool` — best for `windowactivate --sync`, but avoid for high-frequency clicks

---

## Diagnostic Commands

```bash
# What display server is running?
ps aux | grep -E "Xorg|Xwayland|wayland"

# All X11 clients
DISPLAY=:1 xlsclients

# Window tree (parent/child)
DISPLAY=:1 xprop -root _NET_CLIENT_LIST

# Window class (useful for matching)
DISPLAY=:1 xprop -id <WINDOW_ID> WM_CLASS

# Check if XTest extension is available
DISPLAY=:1 xdpyinfo | grep -i test
```

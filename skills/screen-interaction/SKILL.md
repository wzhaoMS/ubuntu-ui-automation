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

## Typing Text into Applications (Chat / Command Console)

> Data from systematic experiments: 6 methods tested, 3 trials each, across 3 command lengths.
> Tested on Minecraft 1.21.11 (LWJGL) command console.

### Summary of Findings

Sending **single keystrokes** (ESC, F3, arrow keys) is 100% reliable with all tools.
Sending **text strings** (chat messages, console commands) is inherently fragile — **every method has a failure rate of 10-30%**. The only way to achieve reliability is **retry with log verification**.

### Method Comparison

| Method | Reliability | Speed | Notes |
|--------|------------|-------|-------|
| `xte 'str ...'` (separate calls) | **67-100%** depending on timing | ~2s per cmd | Best overall. Needs 1.0s+ wait after str for 42-char commands |
| `xdotool type --delay 50` | **100%** (3/3) | ~2.5s for 33 chars | Reliable but slow. delay=20 drops to 67%. delay=10 → 0% |
| `xte` char-by-char (separate process per char) | **100%** at 0.02s gap | ~5s for 13 chars | Very slow (subprocess overhead per character). Impractical. |
| `pynput` char-by-char (in-process) | **0%** | — | **Does not work for typing text.** Single keys work, but text does not reach MC. |
| `xte` chained (`usleep` between ops) | **33-67%** | ~2s | Worse than separate calls. `usleep` timing is unreliable inside xte. |
| `pyautogui.press()` | **0%** from Python script | — | Loses focus when Python script runs; only works from bash subprocess. |

### Optimal Timing (xte str)

Experimentally determined from 3 trials × 5 wait values × 3 command lengths:

| Command Length | Min wait after `xte str` | Recommended |
|---------------|--------------------------|-------------|
| Short (13 chars) | 0.5s (67%) | 1.0s (67%) |
| Medium (33 chars) | 1.0s (**100%**) | 1.0s |
| Long (42 chars) | 1.5s (67%) | 1.5s |

Wait after `/` key to open console: **0.1-0.5s** (both 100% at 3/3). Use **0.5s** for safety.

### Reliable Command Recipe (Bash)

```bash
mc_cmd() {
    local cmd="$1"
    DISPLAY=:1 xdotool windowactivate --sync $GAME_WID
    sleep 0.3
    DISPLAY=:1 xte "key slash"   # Open command console (pre-fills "/")
    sleep 0.5
    DISPLAY=:1 xte "str $cmd"    # Type command (WITHOUT leading /)
    sleep 1.5                     # Wait for text to arrive
    DISPLAY=:1 xte "key Return"  # Execute
    sleep 1.0                     # Wait for server response
}
```

### Reliable Command Recipe (Python with retry + log verification)

```python
def mc_cmd(cmd, max_retries=3):
    """Send /command to MC, verify via log, retry on failure."""
    LOG = os.path.expanduser('~/.minecraft/logs/latest.log')
    for attempt in range(max_retries):
        with open(LOG) as f:
            before = len(f.readlines())
        
        run("xdotool windowactivate --sync " + GAME_WID)
        time.sleep(0.3)
        run("xte 'key slash'")
        time.sleep(0.5)
        run(f"xte 'str {cmd}'")
        time.sleep(1.5)
        run("xte 'key Return'")
        time.sleep(1.0)
        
        with open(LOG) as f:
            new_lines = f.readlines()[before:]
        
        if any('Successfully' in l or 'Teleported' in l 
               or 'Set the time' in l for l in new_lines):
            return True
        # Failed — retry
    return False
```

### Critical Lessons Learned

1. **Use `/` key, NOT `T` key** — `T` opens chat AND types "t" into the text box, corrupting every command. `/` pre-fills the slash cleanly.

2. **pynput CANNOT type text into LWJGL** — It works for single keys (ESC, F3) but text input produces 0% success. This is a fundamental limitation of pynput's keyboard simulation for Java/LWJGL text fields.

3. **Log-based verification is the only reliable feedback** — Screenshots can't distinguish between "command accepted but no blocks changed" and "command never arrived." Check `~/.minecraft/logs/latest.log` for `[CHAT]` entries.

4. **`wmctrl -a` matches the wrong window** — "Minecraft" matches "Minecraft Launcher" before "Minecraft 1.21.11 - Singleplayer". Always use `wmctrl -l | grep "Singleplayer"` to get the specific window ID, then `wmctrl -i -a $WID`.

5. **Singleplayer auto-pauses on focus loss** — Any time VS Code, a terminal, or another window steals focus, MC pauses and stops processing commands. Use `xdotool windowactivate --sync` before every command.

6. **`xte str` is NOT instant** — Despite being a single call, xte injects characters sequentially. If you send Enter too early, the command is truncated. The failure pattern in logs looks like: `/fill 198 63 198 211 63 209 stone_bri<--[HERE]`

7. **Retry logic is mandatory** — Even with optimal timing, ~15-30% of commands fail. A simple 3-retry loop with log verification brings effective reliability to >99%.

8. **Refocus between commands** — Calling `xdotool windowactivate --sync` before each command prevents focus drift. Without this, long sequences degrade as other processes steal focus.

9. **`xdotool type --delay 50` is the most reliable single-shot method** — 100% at 50ms/char, but slow (2.5s for a 33-char command). For batch operations, `xte str` + retry is faster overall.

10. **Chaining xte commands with `usleep` is LESS reliable than separate calls** — despite seeming more atomic, `usleep` timing inside a single xte invocation is inconsistent.

11. **Caps Lock gets stuck ON** — `xte` key presses can leave Caps Lock toggled. Always check `xset -q | grep Caps` and toggle off with `xdotool key Caps_Lock` before sending commands. Uppercase commands like `/SETBLOCK` will fail.

---

## Building in Minecraft: Method Comparison

> Benchmarked on MC 1.21.11, creative mode, 48 identical blocks (4x3x4 solid cube).

### End-to-End Timing

| Method | Time | ms/block | Commands | Use Case |
|--------|------|----------|----------|----------|
| `/fill` (bulk) | **3.3s** | 70 | 1 | Best for walls, floors, bulk operations |
| `/setblock` (per-block) | 160.2s | 3,338 | 48 | Precise single blocks, complex shapes |
| `/tp` + right-click (mimic) | 183.4s | 3,821 | 96 | Human-like placement, no commands |

### Speedups

- `/fill` is **48x faster** than `/setblock` and **55x faster** than tp+click
- `/setblock` is **1.1x faster** than tp+click (similar per-block cost)
- All methods achieved **100% block placement accuracy**

### Human-Mimic Method (tp + right-click)

This method places blocks the way a human would — teleport to a position, look at a surface, right-click to place. No `/fill` or `/setblock` needed for the actual blocks.

**How it works:**
1. `/tp @s X.5 Y+1.6 Z.5 0 90` — stand above target, look straight down (pitch=90)
2. `xte 'mouseclick 3'` — right-click places block on surface below crosshair
3. Number keys (`xte 'key 1'`) — select hotbar slot for material

**Recipe:**
```python
def place_block_at(x, y, z):
    """Place held block at (x,y,z) by standing above, looking down."""
    mc_cmd(f"tp @s {x}.5 {y+1.6} {z}.5 0 90")
    time.sleep(0.3)
    run(f"xdotool windowactivate --sync {GAME_WID}")
    time.sleep(0.1)
    run("xte 'mouseclick 3'")
    time.sleep(0.12)
```

**Practical results (8x6x8 house, 176 mouse-placed blocks):**
- Foundation (64 blocks via /setblock): 213.7s
- Walls (112 blocks via tp+click): 439.4s (3,923 ms/block)
- Ceiling (64 blocks via tp+click): 249.1s
- Total house build: **989s (~16.5 min)**

**When to use each method:**

| Method | Speed | Human-Like | Precision | Best For |
|--------|-------|-----------|-----------|----------|
| `/fill` | Fastest (70 ms/blk) | No | Rectangles only | Walls, floors, clearing |
| `/setblock` | Slow (3.3s/blk) | No | Any single block | Complex shapes, details |
| tp + click | Slow (3.9s/blk) | **Yes** | Any block with surface | Demos, human simulation |
| **Hybrid** | Mixed | Partial | Best of both | **Recommended** |

**Hybrid approach (recommended):** Use `/fill` for large surfaces (walls, floors), `/setblock` for details (windows, lights), and tp+click only when you need to demonstrate human-like interaction.

### Key Discoveries

1. **Right-click (`xte 'mouseclick 3'`) works in LWJGL** — confirmed with 67.5% screen change on first test, then 176 blocks placed successfully.

2. **Camera control via `/tp` yaw/pitch** — since `xdotool mousemove_relative` doesn't rotate the LWJGL camera (only 1-2% screen change), use `/tp` with yaw/pitch arguments for precise aiming.

3. **Relative mouse movement does NOT work for LWJGL camera** — tested xdotool, xte `mousermove`, and python-xlib XTest relative motion. All produced <2% screen change. LWJGL reads raw input directly, not X11 motion events.

4. **Seed blocks needed** — the mimic method requires an existing surface to click on. Place a foundation layer via `/setblock` first, then build up by clicking on existing blocks.

---

## Human-Like Continuous Movement (Walk + Turn + Place)

> The most realistic building method — the player walks to each block, looks at the target, and right-clicks. No teleporting to each block.

### How It Works

Three primitives combine for natural movement:

| Action | Method | Speed |
|--------|--------|-------|
| **Walk** | `xte 'keydown w'` / `xte 'keyup w'` | 4.3 blocks/sec (sprint: 5.6) |
| **Strafe** | `xte 'keydown a'` or `xte 'keydown d'` | 4.3 blocks/sec |
| **Turn head** | `/tp @s ~ ~ ~ <yaw> <pitch>` | Instant, 0.000 position drift |
| **Place block** | `xte 'mouseclick 3'` | ~80ms |
| **Select slot** | `xte 'key 1'` through `xte 'key 9'` | Instant |

**Key insight:** `/tp @s ~ ~ ~ yaw pitch` changes look direction WITHOUT moving position (all `~` for coords). This is like turning your head in place.

### Walk-Turn-Place Cycle

```python
def walk(direction, duration):
    """Walk in a direction for a duration.
    W=forward, S=back, A=left, D=right (relative to facing)."""
    focus()
    run(f"xte 'keydown {direction}'")
    time.sleep(duration)
    run(f"xte 'keyup {direction}'")
    time.sleep(0.15)

def look(yaw, pitch):
    """Turn head without moving. yaw: 0=south, 90=west, 180=north, -90=east.
    pitch: 0=level, 90=down, -90=up."""
    mc_cmd(f"tp @s ~ ~ ~ {yaw} {pitch}")
    time.sleep(0.2)

def place():
    """Right-click to place block at crosshair."""
    focus()
    run("xte 'mouseclick 3'")
    time.sleep(0.1)

# Example: walk forward, look down, place, repeat
look(0, 0)       # Face south, level
walk('w', 0.5)   # Walk forward ~2 blocks
look(0, 80)      # Look down at ground
place()           # Place block at feet
look(0, 0)       # Look ahead again
walk('w', 0.5)   # Walk to next spot
look(0, 80)      # Look down
place()           # Place another
```

### Yaw Reference (MC compass directions)

| Yaw | Direction | Walk key (when facing south) |
|-----|-----------|-----|
| 0 | South (+Z) | W |
| 90 | West (-X) | W (after turning) |
| 180 or -180 | North (-Z) | W (after turning) |
| -90 or 270 | East (+X) | W (after turning) |

### Benchmarked Data

| Metric | Value |
|--------|-------|
| Walk speed | **4.3 blocks/sec** (W key, 1s hold = 2.6 blocks) |
| Strafe speed | **2.6 blocks/sec** (A/D key, 0.5s hold = 1.3 blocks) |
| Turn drift | **0.000 blocks** (no position change) |
| Walk+turn+place cycle | **~3.5s per block** (including mc_cmd overhead) |

### Limitations

- **Walking is imprecise** — you can't walk to an exact coordinate. The player overshoots or undershoots based on timing. For precise placement, combine walking for big moves with `/tp` nudges.
- **Direction depends on facing** — W walks wherever you're looking. Always set yaw first with `/tp @s ~ ~ ~ yaw 0` before walking.
- **Creative mode flight** — double-tap space to fly. In flight mode, W/S/A/D move horizontally and space/shift move up/down.

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

# Check Caps Lock state (common gotcha)
DISPLAY=:1 xset -q | grep Caps
```

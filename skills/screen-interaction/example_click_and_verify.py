#!/usr/bin/env python3
"""
Example: activate a window, click a button, take a screenshot, analyze it.

Usage:
    DISPLAY=:1 python3 example_click_and_verify.py "Firefox" 500 300
"""

import sys
import os
import subprocess
import time
from PIL import Image

def get_display():
    """Detect the correct X display."""
    d = os.environ.get('DISPLAY')
    if d:
        return d
    for n in ['1', '0']:
        if os.path.exists(f'/tmp/.X11-unix/X{n}'):
            return f':{n}'
    raise RuntimeError("No X display found")

def run(cmd):
    """Run a shell command with DISPLAY set."""
    env = {**os.environ, 'DISPLAY': get_display()}
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)

def list_windows():
    """List all windows as (id, title) pairs."""
    r = run('wmctrl -l')
    windows = []
    for line in r.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split(None, 3)
        if len(parts) >= 4:
            windows.append((parts[0], parts[3]))
    return windows

def activate_window(title_substring):
    """Raise and focus a window by partial title match."""
    r = run(f'wmctrl -a "{title_substring}"')
    return r.returncode == 0

def get_window_geometry(title_substring):
    """Get window position and size."""
    windows = list_windows()
    wid = None
    for id_, title in windows:
        if title_substring.lower() in title.lower():
            wid = id_
            break
    if not wid:
        return None
    r = run(f'xwininfo -id {wid}')
    geo = {}
    for line in r.stdout.split('\n'):
        if 'Absolute upper-left X' in line:
            geo['x'] = int(line.split(':')[1].strip())
        elif 'Absolute upper-left Y' in line:
            geo['y'] = int(line.split(':')[1].strip())
        elif 'Width:' in line:
            geo['width'] = int(line.split(':')[1].strip())
        elif 'Height:' in line:
            geo['height'] = int(line.split(':')[1].strip())
    return geo

def click(x, y):
    """Send a real mouse click at absolute screen coordinates."""
    run(f"xte 'mousemove {x} {y}' 'mouseclick 1'")

def key(keyname):
    """Send a keypress."""
    run(f"xte 'key {keyname}'")

def type_text(text):
    """Type a string."""
    # Escape single quotes for shell
    safe = text.replace("'", "'\\''")
    run(f"xte 'str {safe}'")

def screenshot(path='/tmp/screenshot.png'):
    """Capture the full screen."""
    run(f'scrot {path}')
    return path

def analyze_brightness(path, region=None):
    """Return average brightness of a screenshot or region."""
    img = Image.open(path)
    if region:
        img = img.crop(region)
    total = 0
    samples = 0
    w, h = img.size
    for y in range(0, h, 20):
        for x in range(0, w, 20):
            total += sum(img.getpixel((x, y))[:3]) / 3
            samples += 1
    return total / samples if samples else 0

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <window_title> <rel_x> <rel_y>")
        sys.exit(1)

    title = sys.argv[1]
    rel_x = int(sys.argv[2])
    rel_y = int(sys.argv[3])

    print(f"1. Finding window: {title}")
    geo = get_window_geometry(title)
    if not geo:
        print(f"   Window '{title}' not found")
        sys.exit(1)
    print(f"   Found at ({geo['x']}, {geo['y']}), size {geo['width']}x{geo['height']}")

    print(f"2. Activating window")
    activate_window(title)
    time.sleep(0.5)

    abs_x = geo['x'] + rel_x
    abs_y = geo['y'] + rel_y
    print(f"3. Clicking at absolute ({abs_x}, {abs_y})")
    click(abs_x, abs_y)
    time.sleep(1)

    print(f"4. Taking screenshot")
    path = screenshot('/tmp/click_verify.png')

    print(f"5. Analyzing")
    region = (geo['x'], geo['y'], geo['x'] + geo['width'], geo['y'] + geo['height'])
    brightness = analyze_brightness(path, region)
    print(f"   Window brightness: {brightness:.0f}/255")
    print(f"   Screenshot saved: {path}")

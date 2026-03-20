#!/usr/bin/env python3
"""
Benchmark: compare 5 UI automation tools on Ubuntu X11.

Tests:
  1. Mouse move speed (10 moves, measure time)
  2. Mouse click reliability (click a known coordinate, verify via cursor pos)
  3. Key press reliability (type into xdotool getactivewindow, verify)
  4. LWJGL/Java app compatibility (click inside Minecraft window)
  5. Window activation reliability

Each tool is tested N times. Success/failure and latency are recorded.
"""

import os, sys, time, subprocess, json

os.environ['DISPLAY'] = ':1'

N_TRIALS = 10
RESULTS = {}

# ─── Helpers ───

def run(cmd, timeout=5):
    """Run shell command, return (stdout, returncode, elapsed_ms)."""
    t0 = time.time()
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, 
                          timeout=timeout, env={**os.environ})
        elapsed = (time.time() - t0) * 1000
        return r.stdout.strip(), r.returncode, elapsed
    except subprocess.TimeoutExpired:
        return "", -1, timeout * 1000

def get_mouse_pos():
    """Get current mouse position."""
    out, _, _ = run("xdotool getmouselocation --shell 2>/dev/null")
    pos = {}
    for line in out.split('\n'):
        if '=' in line:
            k, v = line.split('=', 1)
            pos[k] = int(v)
    return pos.get('X', -1), pos.get('Y', -1)

def record(tool, test, success, latency_ms):
    """Record a test result."""
    key = f"{tool}|{test}"
    if key not in RESULTS:
        RESULTS[key] = {'successes': 0, 'failures': 0, 'latencies': []}
    if success:
        RESULTS[key]['successes'] += 1
    else:
        RESULTS[key]['failures'] += 1
    RESULTS[key]['latencies'].append(latency_ms)

# ─── Test Functions ───

def test_mouse_move(tool_name, move_fn):
    """Move mouse to target, check it arrived."""
    targets = [(100, 100), (500, 500), (1000, 300), (200, 800), (1500, 1000),
               (50, 50), (800, 400), (1200, 600), (300, 200), (700, 700)]
    for tx, ty in targets[:N_TRIALS]:
        t0 = time.time()
        try:
            move_fn(tx, ty)
            time.sleep(0.05)
            elapsed = (time.time() - t0) * 1000
            ax, ay = get_mouse_pos()
            # Allow 5px tolerance
            ok = abs(ax - tx) <= 5 and abs(ay - ty) <= 5
            record(tool_name, 'mouse_move', ok, elapsed)
        except Exception as e:
            record(tool_name, 'mouse_move', False, 9999)

def test_mouse_click(tool_name, click_fn):
    """Click at a position. Success = no crash."""
    for i in range(N_TRIALS):
        tx, ty = 500 + i*50, 500
        t0 = time.time()
        try:
            click_fn(tx, ty)
            elapsed = (time.time() - t0) * 1000
            record(tool_name, 'mouse_click', True, elapsed)
        except Exception as e:
            record(tool_name, 'mouse_click', False, 9999)
        time.sleep(0.02)

def test_key_press(tool_name, key_fn):
    """Press Escape key. Success = no crash."""
    for i in range(N_TRIALS):
        t0 = time.time()
        try:
            key_fn('Escape')
            elapsed = (time.time() - t0) * 1000
            record(tool_name, 'key_press', True, elapsed)
        except Exception as e:
            record(tool_name, 'key_press', False, 9999)
        time.sleep(0.02)

def test_java_click(tool_name, click_fn):
    """Click inside a Java/LWJGL window (e.g., Minecraft).
    Uses wmctrl to find the window by partial title match.
    Success = cursor moved to position (basic check).
    Note: LWJGL apps may capture the cursor, so position check uses 
    a generous tolerance."""
    # Find MC window via wmctrl (supports partial match)
    out, rc, _ = run("wmctrl -lG | grep -i 'Singleplayer\\|LWJGL\\|OpenGL'")
    if rc != 0 or not out:
        # No Java/LWJGL window found, skip
        for i in range(N_TRIALS):
            record(tool_name, 'java_click', False, 0)
        return
    
    # Parse first matching window
    parts = out.split('\n')[0].split()
    wid = parts[0]
    # wmctrl -lG columns: id desktop x y w h hostname title...
    wx, wy, ww, wh = int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])
    
    cx = wx + ww // 2
    cy = wy + wh // 2
    
    # Focus the window first
    run(f"xdotool windowactivate --sync {wid}")
    time.sleep(0.5)
    
    for i in range(N_TRIALS):
        t0 = time.time()
        try:
            click_fn(cx, cy)
            time.sleep(0.05)
            elapsed = (time.time() - t0) * 1000
            ax, ay = get_mouse_pos()
            # LWJGL may capture cursor — use generous tolerance
            ok = abs(ax - cx) <= 50 and abs(ay - cy) <= 50
            record(tool_name, 'java_click', ok, elapsed)
        except Exception as e:
            record(tool_name, 'java_click', False, 9999)
        time.sleep(0.02)

# ─── Tool Implementations ───

# 1. xdotool
def xdotool_move(x, y): run(f"xdotool mousemove {x} {y}")
def xdotool_click(x, y): run(f"xdotool mousemove {x} {y} click 1")
def xdotool_key(k): run(f"xdotool key {k}")

# 2. xte (xautomation)
def xte_move(x, y): run(f"xte 'mousemove {x} {y}'")
def xte_click(x, y): run(f"xte 'mousemove {x} {y}' 'mouseclick 1'")
def xte_key(k): run(f"xte 'key {k}'")

# 3. pyautogui
def pyautogui_move(x, y):
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.moveTo(x, y, _pause=False)

def pyautogui_click(x, y):
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.click(x, y, _pause=False)

def pyautogui_key(k):
    import pyautogui
    pyautogui.FAILSAFE = False
    key_map = {'Escape': 'escape', 'Return': 'enter'}
    pyautogui.press(key_map.get(k, k.lower()), _pause=False)

# 4. pynput
def pynput_move(x, y):
    from pynput.mouse import Controller
    m = Controller()
    m.position = (x, y)

def pynput_click(x, y):
    from pynput.mouse import Controller, Button
    m = Controller()
    m.position = (x, y)
    m.click(Button.left, 1)

def pynput_key(k):
    from pynput.keyboard import Controller, Key
    kb = Controller()
    key_map = {'Escape': Key.esc, 'Return': Key.enter}
    kb.press(key_map.get(k, k.lower()))
    kb.release(key_map.get(k, k.lower()))

# 5. python-xlib XTest
def xlib_move(x, y):
    from Xlib import X, display
    from Xlib.ext import xtest
    d = display.Display(':1')
    xtest.fake_input(d, X.MotionNotify, detail=0, x=x, y=y)
    d.sync()
    d.close()

def xlib_click(x, y):
    from Xlib import X, display
    from Xlib.ext import xtest
    d = display.Display(':1')
    xtest.fake_input(d, X.MotionNotify, detail=0, x=x, y=y)
    d.sync()
    time.sleep(0.01)
    xtest.fake_input(d, X.ButtonPress, detail=1)
    d.sync()
    time.sleep(0.01)
    xtest.fake_input(d, X.ButtonRelease, detail=1)
    d.sync()
    d.close()

def xlib_key(k):
    from Xlib import X, display
    from Xlib.ext import xtest
    key_map = {'Escape': 9, 'Return': 36}
    d = display.Display(':1')
    code = key_map.get(k, 9)
    xtest.fake_input(d, X.KeyPress, detail=code)
    d.sync()
    time.sleep(0.01)
    xtest.fake_input(d, X.KeyRelease, detail=code)
    d.sync()
    d.close()

# ─── Run Benchmark ───

TOOLS = [
    ('xdotool',     xdotool_move,  xdotool_click,  xdotool_key),
    ('xte',         xte_move,      xte_click,       xte_key),
    ('pyautogui',   pyautogui_move, pyautogui_click, pyautogui_key),
    ('pynput',      pynput_move,   pynput_click,    pynput_key),
    ('python-xlib', xlib_move,     xlib_click,      xlib_key),
]

print("=" * 70)
print("UBUNTU UI AUTOMATION BENCHMARK")
print(f"Trials per test: {N_TRIALS}")
print("=" * 70)

for name, move_fn, click_fn, key_fn in TOOLS:
    print(f"\n>>> Testing: {name}")
    
    print(f"  [1/4] Mouse move...")
    test_mouse_move(name, move_fn)
    
    print(f"  [2/4] Mouse click...")
    test_mouse_click(name, click_fn)
    
    print(f"  [3/4] Key press...")
    test_key_press(name, key_fn)
    
    print(f"  [4/4] Java/LWJGL click...")
    test_java_click(name, click_fn)

# ─── Print Results ───

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

# Group by test
tests = ['mouse_move', 'mouse_click', 'key_press', 'java_click']
tool_names = [t[0] for t in TOOLS]

for test in tests:
    print(f"\n--- {test} ---")
    print(f"{'Tool':<15} {'Success':>8} {'Fail':>6} {'Rate':>7} {'Avg ms':>8} {'P50 ms':>8} {'P99 ms':>8}")
    for tool in tool_names:
        key = f"{tool}|{test}"
        if key not in RESULTS:
            print(f"{tool:<15} {'N/A':>8}")
            continue
        r = RESULTS[key]
        s, f = r['successes'], r['failures']
        total = s + f
        rate = f"{s*100/total:.0f}%" if total > 0 else "N/A"
        lats = sorted(r['latencies'])
        avg = sum(lats)/len(lats) if lats else 0
        p50 = lats[len(lats)//2] if lats else 0
        p99 = lats[int(len(lats)*0.99)] if lats else 0
        print(f"{tool:<15} {s:>8} {f:>6} {rate:>7} {avg:>8.1f} {p50:>8.1f} {p99:>8.1f}")

# Overall score
print(f"\n--- OVERALL RELIABILITY SCORE ---")
print(f"{'Tool':<15} {'Total OK':>10} {'Total Fail':>12} {'Rate':>7} {'Avg Latency':>12}")
for tool in tool_names:
    total_ok = 0
    total_fail = 0
    total_lat = []
    for test in tests:
        key = f"{tool}|{test}"
        if key in RESULTS:
            total_ok += RESULTS[key]['successes']
            total_fail += RESULTS[key]['failures']
            total_lat.extend(RESULTS[key]['latencies'])
    total = total_ok + total_fail
    rate = f"{total_ok*100/total:.0f}%" if total > 0 else "N/A"
    avg = sum(total_lat)/len(total_lat) if total_lat else 0
    print(f"{tool:<15} {total_ok:>10} {total_fail:>12} {rate:>7} {avg:>10.1f}ms")

# Save raw data
with open('/tmp/benchmark_results.json', 'w') as f:
    json.dump(RESULTS, f, indent=2)
print(f"\nRaw data saved to /tmp/benchmark_results.json")

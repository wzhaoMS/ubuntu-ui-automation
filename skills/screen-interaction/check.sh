#!/usr/bin/env bash
# Quick test: verifies all required tools are installed and working
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; exit 1; }

# Detect display
if [[ -z "$DISPLAY" ]]; then
    if [[ -e /tmp/.X11-unix/X1 ]]; then
        export DISPLAY=:1
    elif [[ -e /tmp/.X11-unix/X0 ]]; then
        export DISPLAY=:0
    else
        fail "No X display found"
    fi
fi
pass "DISPLAY=$DISPLAY"

# Check CLI tools
for tool in scrot xdotool xte wmctrl xprop xwininfo; do
    which "$tool" >/dev/null 2>&1 && pass "$tool installed" || fail "$tool missing — run: sudo apt-get install -y scrot xdotool xautomation wmctrl x11-utils"
done

# Check Python packages
python3 -c "from PIL import Image; print('OK')" >/dev/null 2>&1 && pass "Pillow installed" || fail "Pillow missing — run: pip3 install Pillow"
python3 -c "from Xlib.ext import xtest; print('OK')" >/dev/null 2>&1 && pass "python-xlib installed" || fail "python-xlib missing — run: pip3 install python-xlib"

# Test screenshot
scrot /tmp/_ui_test.png && pass "scrot works (screenshot saved to /tmp/_ui_test.png)" || fail "scrot failed"

# Test wmctrl
wmctrl -l >/dev/null 2>&1 && pass "wmctrl works ($(wmctrl -l | wc -l) windows found)" || fail "wmctrl failed"

# Test xte
xte 'mousemove 0 0' 2>/dev/null && pass "xte works" || fail "xte failed"

rm -f /tmp/_ui_test.png
echo ""
echo "All checks passed. Ready to automate."

# Ubuntu UI Automation Skill

A reference guide for AI agents to interact with the Ubuntu desktop — controlling windows, sending mouse/keyboard events, taking screenshots, and analyzing screen content programmatically.

## Quick Start

```bash
# Install all required tools
sudo apt-get install -y scrot xdotool xautomation wmctrl xprop x11-utils

# Python packages (for screenshot analysis + XTest fallback)
pip3 install --break-system-packages Pillow python-xlib
```

See [SKILL.md](skills/screen-interaction/SKILL.md) for the full skill reference.

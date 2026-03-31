#!/usr/bin/env python3
"""
Watch ue5_plugin/UnrealAI/ and sync changes to the UE project.
Syncs Python files and C++ source files.
Usage: python watch.py
"""
import shutil
import time
from pathlib import Path

PLUGIN_SRC = Path(__file__).parent / "ue5_plugin/UnrealAI"
PLUGIN_DST = Path("/Users/MikeCoker/Documents/Unreal Projects/UEAITest/Plugins/UnrealAI")

# (glob pattern, description)
WATCH_PATTERNS = [
    ("Content/Python/**/*.py",          "python"),
    ("Source/**/*.cpp",                 "c++"),
    ("Source/**/*.h",                   "c++"),
    ("Source/**/*.cs",                  "build"),
    ("*.uplugin",                       "uplugin"),
]

def sync(changed: Path):
    rel = changed.relative_to(PLUGIN_SRC)
    dest = PLUGIN_DST / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(changed, dest)
    print(f"  synced: {rel}")

def all_watched_files():
    files = {}
    for pattern, _ in WATCH_PATTERNS:
        for p in PLUGIN_SRC.glob(pattern):
            if "__pycache__" not in str(p):
                files[p] = p.stat().st_mtime
    return files

def watch():
    print(f"Watching {PLUGIN_SRC}")
    print(f"     → {PLUGIN_DST}")
    print("Ctrl+C to stop\n")
    mtimes = all_watched_files()
    while True:
        time.sleep(0.5)
        current = all_watched_files()
        for p, mtime in current.items():
            if mtimes.get(p) != mtime:
                mtimes[p] = mtime
                sync(p)
        # Detect new files
        for p in set(current) - set(mtimes):
            mtimes[p] = current[p]
            sync(p)

if __name__ == "__main__":
    try:
        watch()
    except KeyboardInterrupt:
        print("\nStopped.")

"""Put tools/audit on sys.path so the audit modules import as top-level names."""

from __future__ import annotations

import os
import pathlib
import sys

# OpenAL Soft crashes with an access violation in alcOpenDevice on this host's
# audio stack since the .NET 10 / engine-bleed update (reproduces on unmodified
# master). The "null" driver gives headless gates a working silent device
# without touching the engine. An explicit operator override wins.
os.environ.setdefault("ALSOFT_DRIVERS", "null")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "tools" / "audit"

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "tools" / "audit"

for candidate in (str(AUDIT_DIR), str(REPO_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

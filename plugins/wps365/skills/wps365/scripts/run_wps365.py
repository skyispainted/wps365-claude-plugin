# -*- coding: utf-8 -*-
"""Run the WPS 365 CLI bundled with the active Claude plugin."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from wps365.cli import main


if __name__ == "__main__":
    raise SystemExit(main())

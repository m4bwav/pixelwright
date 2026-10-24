#!/usr/bin/env python3
"""sw.py: spritewright's old name for pixelwright's pxw.py, kept for one release. Runs pxw.py with the same
arguments, so briefs, notes and scripts that call sw.py keep working. New work calls ../../pixelwright/scripts/pxw.py.
"""
import runpy
import sys
from pathlib import Path

sys.argv[0] = str(Path(__file__).resolve().parents[2] / "pixelwright" / "scripts" / "pxw.py")
runpy.run_path(sys.argv[0], run_name="__main__")

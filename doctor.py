#!/usr/bin/env python3
"""Root launcher for FreeCut Studio Environment Doctor (`python doctor.py`)."""
import os
import runpy
import sys

here = os.path.dirname(os.path.abspath(__file__))
target = os.path.join(here, ".agents", "skills", "freecut-unified-engine", "scripts", "doctor.py")
sys.path.insert(0, os.path.dirname(target))
runpy.run_path(target, run_name="__main__")

"""Compatibility module for running the Kebabalab simplified server.

This thin wrapper keeps backwards compatibility with the historical
``server_simplified.py`` entry point while delegating all of the actual
implementation to the package module ``kebabalab.server``.
"""

from __future__ import annotations

import pathlib
import sys

_PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

from kebabalab.server import *  # noqa: F401,F403
from kebabalab.server import main

__all__ = [name for name in globals() if not name.startswith("_")]

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Main entry point for starting the Yggdrasil GUI application."""

from gui import ui

# Ensures execution when started directly (__main__) or spawned via multiprocessing (__mp_main__)
if __name__ in {"__main__", "__mp_main__"}:
    ui.start()

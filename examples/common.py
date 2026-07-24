"""Shared helpers for Glue examples."""
from __future__ import annotations

import os
from typing import Optional, Tuple

import bottle

# Repo-level branding (favicon, logo, …) — single copy for all examples
ASSETS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'assets'))

# Default example window size
WINDOW_SIZE: Tuple[int, int] = (1280, 720)

_ASSET_FILES = (
    'favicon.ico',
    'favicon-16x16.png',
    'favicon-32x32.png',
    'apple-touch-icon.png',
    'android-chrome-192x192.png',
    'android-chrome-512x512.png',
    'site.webmanifest',
    'logo.png',
)


def use_shared_assets(app: Optional[bottle.Bottle] = None) -> None:
    """Serve files from repo ``assets/`` at the URL root.

    Call **before** :func:`glue.start` so these routes are registered ahead of
    Glue's catch-all static handler. Browsers can then load ``/favicon.ico``
    (and related icons) without copying them into every ``web/`` folder.
    """
    target = app if app is not None else bottle.default_app()

    for filename in _ASSET_FILES:
        # Bind filename in default-arg so the closure is correct
        def _handler(name: str = filename):
            return bottle.static_file(name, root=ASSETS_DIR)

        target.route(f'/{filename}', callback=_handler)

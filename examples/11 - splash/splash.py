"""Transparent startup splash using Glue's public splash API."""

import multiprocessing
from pathlib import Path

import bottle

import glue

HERE = Path(__file__).resolve().parent
UI_DIR = HERE / 'ui'
ASSET_DIR = HERE.parents[1] / 'assets'
LOGO_PATH = ASSET_DIR / 'android-chrome-512x512.png'


def main():
    app = bottle.Bottle()

    @app.get('/splash-logo.png')
    def splash_logo():
        return bottle.static_file(LOGO_PATH.name, root=str(ASSET_DIR))

    glue.init(path=str(UI_DIR), app_name='glue-splash-demo')
    glue.start(
        mode='webview',
        port=0,
        app=app,
        title='Glue Splash API',
        splash=LOGO_PATH,
    )


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()

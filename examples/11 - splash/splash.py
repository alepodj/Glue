"""Transparent startup splash using Glue's public splash API."""

# The splash renderer uses a spawned process. freeze_support() below keeps that
# process safe on Windows and in frozen/PyInstaller applications.
import multiprocessing

import glue


def main():
    glue.init()

    # True auto-discovers ui/splash.png. Every other start option stays at its
    # normal default. Splash-enabled apps also center automatically.
    glue.start(splash=True)


# Required with multiprocessing spawn: a splash child imports this file, but
# must not run main() and recursively launch another application.
if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()

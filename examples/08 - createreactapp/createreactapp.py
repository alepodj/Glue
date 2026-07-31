"""Main Python application file for the Glue CRA demo."""

import os
import random
import sys
from pathlib import Path

import glue

HERE = Path(__file__).resolve().parent


@glue.expose
def say_hello_py(x):
    """Print message from JavaScript on app initialization, then call a JS function."""
    print('Hello from %s' % x)
    glue.say_hello_js('Python {from within say_hello_py()}!')


@glue.expose
def expand_user(folder):
    """Return the full path to display in the UI."""
    return f'{os.path.expanduser(folder)}/*'


@glue.expose
def pick_file(folder):
    """Return a random file from the specified folder."""
    folder = os.path.expanduser(folder)
    if os.path.isdir(folder):
        files = [
            name for name in os.listdir(folder) if not os.path.isdir(os.path.join(folder, name))
        ]
        if not files:
            return f'No files found in {folder}'
        return random.choice(files)
    return f'{folder} is not a valid folder'


def start_glue(develop):
    """Start Glue with either production or development configuration."""

    if develop:
        directory = HERE / 'src'
        page = {'port': 3000}
        # Dev: no browser window — CRA already opened localhost:3000
        mode = None
    else:
        directory = HERE / 'build'
        page = 'index.html'
        mode = 'auto'

    glue.init(str(directory), ['.tsx', '.ts', '.jsx', '.js', '.html'])

    # Calls queue until the first page connects, but do not repeat on reload.
    say_hello_py('Python World!')
    glue.say_hello_js('Python World!')

    glue.show_log('https://github.com/samuelhwilliams/Eel/issues/363 (show_log)')

    glue.start(
        page,
        mode=mode,
        host='localhost',
        port=8080,
    )


if __name__ == '__main__':
    # Pass any second argument to enable debugging
    start_glue(develop=len(sys.argv) == 2)

import contextlib
import os
import sys
import platform
import subprocess
import tempfile
import time
from pathlib import Path

import psutil

# Path to the test data folder.
TEST_DATA_DIR = Path(__file__).parent / "data"


def _process_connections(proc):
    if hasattr(proc, 'net_connections'):
        return proc.net_connections()
    return proc.connections()


def get_process_listening_port(proc, timeout=30.0):
    """Return the first LISTEN port for *proc* or any of its children."""
    psutil_proc = psutil.Process(proc.pid)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f'Glue example process exited before listening (exit code {proc.returncode})'
            )
        try:
            candidates = [psutil_proc] + psutil_proc.children(recursive=True)
        except psutil.NoSuchProcess as exc:
            raise RuntimeError('Glue example process no longer exists') from exc

        for candidate in candidates:
            try:
                for conn in _process_connections(candidate):
                    if conn.status == 'LISTEN':
                        return conn.laddr.port
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        time.sleep(0.01)

    raise TimeoutError(
        f'No LISTEN port found for pid {proc.pid} within {timeout}s '
        f'(platform={platform.system()})'
    )


@contextlib.contextmanager
def get_glue_server(example_py, start_html):
    """Run a Glue example with the mode/port overridden so that no browser is launched and a random port is assigned"""
    test = None

    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=os.path.dirname(example_py), delete=False) as test:
            # Wrap glue.start so mode/port from the example call are overridden
            # (start() would otherwise apply its defaults and ignore pre-set _start_args).
            test.write(f"""
import glue

_real_start = glue.start

def _test_start(*args, **kwargs):
    kwargs['mode'] = None
    kwargs['port'] = 0
    return _real_start(*args, **kwargs)

glue.start = _test_start

import {os.path.splitext(os.path.basename(example_py))[0]}
""")
        proc = subprocess.Popen(
                [sys.executable, test.name],
                cwd=os.path.dirname(example_py),
            )
        glue_port = get_process_listening_port(proc)

        yield f"http://localhost:{glue_port}/{start_html}"

        proc.terminate()

    finally:
        if test:
            try:
                os.unlink(test.name)
            except FileNotFoundError:
                pass


def get_console_logs(driver, minimum_logs=0, *, contains=None, timeout=5.0):
    """Collect browser console logs.

    If *contains* is a sequence of substrings, keep polling until each appears
    in some log message (or *timeout* seconds elapse).
    """
    deadline = time.time() + timeout
    console_logs = driver.get_log('browser')

    def _messages():
        return [entry['message'] for entry in console_logs]

    while True:
        if contains:
            messages = _messages()
            if all(any(needle in msg for msg in messages) for needle in contains):
                return console_logs
        elif len(console_logs) >= minimum_logs:
            return console_logs

        if time.time() >= deadline:
            return console_logs

        time.sleep(0.1)
        console_logs += driver.get_log('browser')

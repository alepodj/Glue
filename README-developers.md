# Glue Developers

## Setting up your environment

```bash
git clone git@github.com:alepodj/Glue.git
cd Glue
python -m venv .venv
# Windows: .venv\Scripts\activate
source venv/bin/activate
```

**Python:** Glue requires **3.10+**.

### Three requirements files

| File | Install when | Purpose |
|------|----------------|---------|
| `requirements.txt` | Running or packaging Glue | **Runtime** only (bottle, gevent, pywebview, …). Same idea as `setup.py` `install_requires`. App users never need the other two. |
| `requirements-test.txt` | Developing / testing | Tools that run **inside** a test environment: pytest, Selenium, Ruff, mypy, plus `.[jinja2,build]`. Tox installs this into each clean venv. |
| `requirements-meta.txt` | Using Tox or CI bootstrap | Tools on the **host** that *drive* testing: mainly **tox** (and helpers). Install this *before* `tox`; Tox then creates envs and pulls in `requirements-test.txt` itself. |

Typical install for contributors:

```bash
pip install -r requirements.txt
pip install -r requirements-test.txt   # day-to-day pytest / ruff / mypy
pip install -r requirements-meta.txt   # only if you will run tox
```

Or editable package + the same test/meta files: `pip install -e ".[jinja2,build]"`.

---

## How testing is organized

Pytest collects only files named `test_*.py`. Support code is intentionally **not** named that way.

```text
tests/
  conftest.py           # pytest magic: auto-loaded fixtures (e.g. Selenium `driver`)
  helpers/              # importable Python helpers — not collected as tests
    utils.py            # get_glue_server, console logs, TEST_DATA_DIR
  data/
    init_test/          # fixture *files* (HTML/JS/TSX) for expose()/init scanning — not a real app
  unit/                 # fast, mocked; no browser
    test_init.py
    test_expose.py
    test_browsers.py
    test_webview.py
    test_security.py
    test_settings.py
    test_routes.py
  integration/          # Selenium against examples/ (needs Chrome)
    test_examples.py
```

| Piece | Role |
|--------|------|
| **`conftest.py`** | Reserved pytest name. Defines fixtures like `driver`. Do not rename to `test_*.py`. |
| **`helpers/`** | Shared Python utilities imported as `from tests.helpers import …`. |
| **`data/init_test/`** | Sample UI snippets (plain HTML, Jinja-ish HTML, CRA-style `App.tsx`, minified JS) so unit tests can verify `glue.init` / the expose parser still finds `glue.expose` / `window.glue.expose`. Not launched by Selenium. |
| **`unit/`** | Library behavior in-process. Run these constantly. |
| **`integration/`** | Spawns real example scripts with `mode=None`, opens pages in headless Chrome. Slower; needs Chrome installed. |

Integration covers selected examples (hello world, callbacks, file access, jinja, custom routes). Others are skipped on purpose (e.g. `02` forces Chrome but the harness overrides `mode=None`; CRA needs an npm build). See the module docstring in `tests/integration/test_examples.py`.

---

## Day-to-day commands (no Tox)

Most work only needs **test** deps on your current Python:

```bash
# Fast feedback (preferred while coding)
python -m pytest tests/unit -q

# Full suite including Selenium (Chrome required)
python -m pytest tests -q --timeout=240

# Lint / format (Ruff — we do not use Black)
ruff check glue tests
ruff format glue tests           # write
ruff format --check glue tests   # CI-style check

# Types
mypy --strict glue
```

Config: `pyproject.toml` (Ruff), `mypy.ini` (mypy).

---

## Tox (clean envs + multiple Pythons)

Tox does **not** invent a second test suite. For each env it installs `requirements-test.txt` and runs the same pytest / Ruff / mypy commands.

### Does `tox` run tests on every Python?

**Yes — that is what bare `tox` is for.**  
`tox.ini` `envlist` is: `lint`, `typecheck`, and **`py310` … `py314`**.

So `tox` (no `-e`) will:

1. Run **lint** (Ruff) once  
2. Run **typecheck** (mypy) once  
3. Run **pytest** once **per** Python env (`py310`, `py311`, `py312`, `py313`, `py314`)

Each `py3xx` env is a **separate clean venv** using that version’s interpreter. You must have that Python installed locally (e.g. 3.12 for `py312`). If a version is missing, Tox will **fail or skip that env** (depending on Tox/settings) — it cannot invent interpreters. **CI** installs each version and is the reliable full matrix.

To run **one** version only: `tox -e py312` (pytest on 3.12 only, not the whole list).

### How to run Tox (step by step)

From a clone of the repo:

```bash
# 1) Virtualenv on any 3.10+ you already have
python -m venv .venv
# Windows: .venv\Scripts\activate
source venv/bin/activate

# 2) Host tools only — Tox itself (meta), not the full test stack yet
pip install -r requirements-meta.txt

# 3a) Optional: one quality gate
tox -e lint
tox -e typecheck

# 3b) Optional: pytest on a single Python you have installed
tox -e py312
tox -e py312 -- tests/unit -q          # unit only, quieter

# 3c) Full local matrix (lint + typecheck + every py3xx you have)
tox
```

You do **not** need to manually `pip install -r requirements-test.txt` before Tox for those commands — Tox creates `.tox/py312/` (etc.) and installs test deps there. Installing `requirements-test.txt` into your *venv* is still useful for running `pytest` / `ruff` **without** Tox (see day-to-day above).

Chrome is required for integration tests inside each `py3xx` env when the full `tests/` tree runs. For a quicker Tox pytest pass:  
`tox -e py312 -- tests/unit -q`

### What CI runs

`.github/workflows/test.yml`:

1. **lint** — `tox -e lint` (once)  
2. **typecheck** — `tox -e typecheck` (once)  
3. **test** — pytest via Tox on each of 3.10–3.14 × Ubuntu / Windows / macOS  

(CI runs lint/typecheck as separate jobs; the matrix job runs the `py3xx` envs, not necessarily a single bare `tox` on one machine.)

---

## Suggested workflow for new contributors

1. Install runtime + **test** requirements; run `pytest tests/unit` and `ruff check`.
2. Before a PR: unit tests + Ruff + mypy; run integration if you touched examples or the bridge.
3. Use **Tox** when checking another Python version or matching CI (`tox -e lint`, `tox -e typecheck`, `tox -e py3xx`).
4. You usually do **not** need every Python locally — rely on CI for the full OS/version grid.

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

## Releasing to PyPI

**Model:** you do **not** publish on every commit. PyPI versions are permanent and unique. Instead:

1. Bump the version in the repo and merge to `main`
2. Push a git tag `vX.Y.Z` that matches that version  
3. GitHub Actions (`.github/workflows/publish.yml`) builds the package, uploads **`glue-ui`** to PyPI, and creates a GitHub Release

Users install with `pip install glue-ui` and still `import glue`.

### Why not every push?

A normal `git push` of commits would either spam junk versions or fail when the version number did not change. Tags = “this commit is a release.”

### One-time setup (you must do this once)

#### A. PyPI account

1. Create an account at [https://pypi.org/account/register/](https://pypi.org/account/register/)
2. Enable **2FA** (required for publishing)

#### B. GitHub Environment named `pypi`

1. Open your repo on GitHub → **Settings** → **Environments** → **New environment**
2. Name it exactly: `pypi`
3. (Optional) Add a required reviewer or wait timer; leave empty for automatic publish

#### C. Trusted Publisher on PyPI (no API token)

Preferred: GitHub proves identity via OIDC — no long-lived `pypi_token` secret.

1. Log in to PyPI → **Your account** → **Publishing**  
   ([https://pypi.org/manage/account/publishing/](https://pypi.org/manage/account/publishing/))
2. Under **Pending publishers** (first release) fill in:

   | Field | Value |
   |-------|--------|
   | PyPI Project Name | `glue-ui` |
   | Owner | `alepodj` |
   | Repository name | `Glue` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

3. Save. The first successful workflow run **creates** the `glue-ui` project and attaches you as owner.

**Name note:** Distribution name is `glue-ui`; import stays `glue`. If PyPI rejects `glue-ui`, try `alepodj-glue`.

#### D. Commit and push the workflow

Ensure `main` includes `.github/workflows/publish.yml` **before** you push the first version tag (so the tag’s workflow file exists).

### GitHub Pages (docs site)

The marketing + documentation site lives in [`docs/`](../docs/) and publishes to **https://alepodj.github.io/Glue/**.

One-time: repo **Settings → Pages →** Deploy from branch **`main`** / folder **`/docs`**.

### Each release (after setup)

1. Update `__version__` in `glue/__init__.py` and `version=` in `setup.py` to the same value (e.g. `0.6.6`)
2. Add a CHANGELOG section for that version
3. Commit and push to `main`
4. Tag and push the tag (PowerShell example):

```powershell
git checkout main
git pull
git tag v0.6.6
git push origin v0.6.6
```

5. Watch **Actions** → **Publish** — it should go green
6. Confirm [https://pypi.org/project/glue-ui/](https://pypi.org/project/glue-ui/) and GitHub → **Releases**

If the tag version ≠ `setup.py` version, the workflow fails on purpose (fix the version, delete the bad tag if needed, retag).

### Optional: TestPyPI first

For a dry run, add a second Trusted Publisher pointing at TestPyPI and a separate workflow; not required for day-to-day releases.

---

## Suggested workflow for new contributors

1. Install runtime + **test** requirements; run `pytest tests/unit` and `ruff check`.
2. Before a PR: unit tests + Ruff + mypy; run integration if you touched examples or the bridge.
3. Use **Tox** when checking another Python version or matching CI (`tox -e lint`, `tox -e typecheck`, `tox -e py3xx`).
4. You usually do **not** need every Python locally — rely on CI for the full OS/version grid.

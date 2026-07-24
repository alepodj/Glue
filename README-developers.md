# Glue Developers

## Setting up your environment

In order to start developing with Glue you'll need to checkout the code, set up a development and testing environment, and check that everything is in order.

### Clone the repository
```bash
git clone git@github.com:alepodj/Glue.git
```

### (Recommended) Create a virtual environment
It's recommended that you use virtual environments for this project. Your process for setting up a virtual environment will vary depending on OS and tool of choice, but might look something like this:

```bash
python3 -m venv venv
source venv/bin/activate
```

**Note**: `venv` is listed in the `.gitignore` file so it's the recommended virtual environment name


### Install project requirements

```bash
pip3 install -r requirements.txt        # Glue's 'prod' requirements
pip3 install -r requirements-test.txt   # pytest, selenium, mypy, Glue[jinja2,build]
pip3 install -r requirements-meta.txt   # tox
```

Or editable install with extras: `pip install -e ".[jinja2,build]"`.

### (Recommended) Run Automated Tests

CI runs on GitHub Actions (see `.github/workflows/test.yml`). Locally, Tox can run tests against each major version we support (3.7+). You will need multiple Python installs for the full Tox matrix; `.python-version` pins a recommended default (currently 3.10).

#### Test dependencies

Integration tests use **Chrome** plus **Selenium** with **`webdriver_manager`** (ChromeDriver is downloaded automatically — you do not need to install ChromeDriver by hand).

#### Running Tests

Quick local run (current Python):

```bash
python -m pytest tests/unit tests/integration -q --timeout=240
```

To test Glue against a specific Tox env, e.g. Python 3.10:

```bash
tox -e py310
```

To test Glue against all configured Tox envs:

```bash
tox
```

Typecheck:

```bash
tox -e typecheck
```

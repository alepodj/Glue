# 08 - Create React App

A React + TypeScript frontend connected to Glue.

## What it demonstrates

- Serving a compiled Create React App build with Glue.
- Connecting Glue to the CRA development server.
- Preserving exposed JavaScript names through production minification.

## Files

- `createreactapp.py` — Glue entry point for development and production.
- `public/index.html` — CRA document template.
- `src/App.tsx` — React application and exposed JavaScript functions.
- `src/App.css` — application-specific styling.

CRA's generated filenames are retained because its build tooling depends on
them.

## Run

Install the JavaScript dependencies:

```powershell
cd "examples/08 - createreactapp"
npm install
```

For development, run `npm start`, then in another terminal:

```powershell
python createreactapp.py develop
```

For the production build:

```powershell
npm run build
python createreactapp.py
```

## Key API

```python
glue.init(str(directory), ['.tsx', '.ts', '.jsx', '.js', '.html'])
glue.start(page, mode=mode, host='localhost', port=8080)
```

These explicit paths and host options are required to switch between CRA's
development server and compiled build.

## Minified function names

Production minification can rename `glue.expose(functionName)`. Use
`window.glue.expose(functionName, 'functionName')` in minified source so Glue's
static analyzer and Python calls retain the public name.

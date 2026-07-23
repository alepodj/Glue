# Glue — Full Project Map

Baseline architecture map for `alepodj/Glue` (forked from Eel 0.18.2).

**Status:** Glue `0.2.0` — Chromium-family browser launch  
**Package identity:** name `Glue`, import `glue`, JS `glue`, routes `/glue.js` + `/glue`  
**License:** MIT (Chris Knott 2018 + alepodj 2026)  
**Courtesy:** Glue is a fork of [Eel](https://github.com/python-eel/Eel)

## Layout

```
Glue/
  glue/                # library
  examples/            # demos (no Electron / Edge-only folders)
  tests/
  setup.py             # Glue 0.2.0
  PROJECT_MAP.md
```

## Browser policy

- Default `mode='auto'`: Windows Edge → Chrome; elsewhere Chrome/Chromium
- Always prefer `app_mode=True` (`--app`)
- Supported: `auto`, `chrome`, `edge`, `custom`, `None`/`False`
- Removed: Electron, MSIE, system webbrowser fallback
- Smoke examples: `01 - hello_world` (auto), `02 - hello_world_chrome` (`mode='chrome'`)

## Lifecycle

1. `import glue` → load `glue.js`
2. `@glue.expose` → register Python callables
3. `glue.init('web')` → scan `glue.expose(...)` in web files
4. `glue.start(...)` → open browser (auto), then Bottle + GeventWebSocketServer
5. Browser loads `/glue.js` → WS `ws://host/glue?page=...`
6. JSON RPC `call` / `return` until last socket closes → `sys.exit()`

## Routes

| Path | Purpose |
|------|---------|
| `/glue.js` | Injected bridge |
| `/`, `/<path>` | Static / Jinja |
| `/glue` | WebSocket RPC |

## Next workstreams

- Protocol hardening
- Architecture refactor
- Feature additions

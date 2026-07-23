# Glue — Full Project Map

Baseline architecture map for `alepodj/Glue` (forked from Eel 0.18.2).

**Status:** rebranded to Glue (`0.1.0`)  
**Package identity:** name `Glue`, import `glue`, JS `glue`, routes `/glue.js` + `/glue`  
**License:** MIT (Chris Knott 2018 + alepodj 2026)  
**Courtesy:** Glue is a fork of [Eel](https://github.com/python-eel/Eel)

## Layout

```
Glue/
  glue/                # library (~9 files)
  examples/01–10/
  tests/
  setup.py             # Glue 0.1.0
  PROJECT_MAP.md
```

## Lifecycle

1. `import glue` → load `glue.js`
2. `@glue.expose` → register Python callables
3. `glue.init('web')` → scan `glue.expose(...)` in web files
4. `glue.start(...)` → open browser, then Bottle + GeventWebSocketServer
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

> "Hello World example": Create-React-App (CRA) and Glue

## Extra Installation Instructions

As discussed in the [main README](https://github.com/alepodj/Glue), the CreateReactApp (CRA) JavaScript framework can work with Glue. This particular project was bootstrapped with `npx create-react-app 07_CreateReactApp --typescript` (Typescript enabled), but the below modifications can be implemented in any CRA configuration or CRA version.

If you run into any issues with this example, open a [new issue](https://github.com/alepodj/Glue/issues/new).

### Running

1. **Install JS packages:** in this directory, run `npm install`
2. **Run Python:** `python glue_CRA.py`
3. **Distribute:** (Run `npm run build` first) Build a binary distribution with PyInstaller using `python -m glue glue_CRA.py build --onefile` (See more detailed PyInstaller instructions at bottom of [the main README](https://github.com/alepodj/Glue))

### JS exposure when using a minifier

`npm run build` will rename variables and functions to minimize file size renaming `glue.expose(funcName)` to something like `D.expose(J)`. The renaming breaks Glue's static JS-code analyzer, which looks for `glue.expose(*)`. To fix this issue, in your JS code, convert all `glue.expose(funcName)` to `window.glue.expose(funcName, 'funcName')`. This workaround guarantees that 'funcName' will be available to call from Python.

### Notable files

- `glue_CRA.py`: Basic Glue entry file
  - If run without arguments, the script will load `index.html` from the build/ directory (which is ideal for building with PyInstaller/distribution)

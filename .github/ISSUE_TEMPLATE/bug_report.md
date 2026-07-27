---
name: Bug report
about: Report something that is broken or unexpected
title: ''
labels: bug
assignees: ''

---

**Glue version**
e.g. `0.6.0` (`import glue; print(glue.__version__)`)

**Describe the bug**
A clear and concise description of what went wrong.

**To Reproduce**
Minimal steps or a small script + `ui/` snippet that shows the bug:

```python
import glue

glue.init(path='ui')  # optional: app_name='...'
# ...
glue.start(mode='auto')  # or 'webview' / 'chrome' / 'edge' / None
```

**Expected behavior**
What you expected to happen instead.

**System Information**
- OS: [e.g. Windows 11, macOS 14, Ubuntu 24.04]
- Python: [e.g. 3.12 — Glue requires 3.10+]
- Window host / `mode`: [e.g. `auto` → PyWebView; or Chrome 120 / Edge 120 / `mode=None`]

**Screenshots**
If applicable, add screenshots or console output.

**Additional context**
Anything else that might help (stack traces, how you installed Glue, etc.).

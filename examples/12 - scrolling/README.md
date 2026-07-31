# 12 - Scrolling

A naturally overflowing page beneath Glue's simulated native title bar.

## What it demonstrates

- Normal document scrolling in a default Glue window.
- Keeping the frameless PyWebView title bar and its controls fixed.
- Preventing content scrollbars from overlapping the title bar.

## Files

- `scrolling.py` — minimal Glue entry point.
- `ui/index.html` — long-form content that creates a scrollbar.

## Run

```powershell
cd "examples/12 - scrolling"
python scrolling.py
```

## Key API

```python
glue.init()
glue.start()
```

Both calls deliberately use Glue's defaults. In PyWebView mode, scroll the page
and confirm that the scrollbar begins below the title-bar controls.

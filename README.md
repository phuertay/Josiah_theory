# Josiah theory (US)

US spelling fork of [Josiah Tan](https://github.com/Josiah-tan)'s [Josiah_theory](https://github.com/Josiah-tan/Josiah_theory).

## Files

| File | Role |
|------|------|
| `josiah_us.json` | Main US dictionary (BASE) |
| `Josiah_afterburner.py` | Python dict: invents missing Cheatsheet outlines from BASE only |
| `greek.json` / `stitching.json` | Bundled extras from upstream |

## Afterburner

- Loads only `josiah_us.json` beside it — no other-dict awareness.
- Place it in your Plover stack yourself (typically below numbers / Harri). Not auto-registered.
- `SPELLING = "US"` (default) or `"UK"` for ise/ize literals this file invents.
- Lapwing `#` capitalize when the parent outline exists; bare `#` stays BASE `{*+}`.
- Cheatsheet: [wiki/Cheatsheet](https://github.com/phuertay/Josiah_theory/wiki/Cheatsheet)

Credit: theory by **Josiah Tan**.

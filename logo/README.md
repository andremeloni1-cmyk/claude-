# AM Monogram — Andre Meloni Photography

An animated, heavy "bubble-brutalist" **AM** monogram built as a single,
dependency-free HTML file. The letters draw on, slide together into a tight
interlocked kerning, and a shared horizontal sightline locks them as one mark —
then it settles into a gentle idle loop.

## Files
- **`index.html`** — the animated logo. Open it directly in any browser. No build step.
- **`am-monogram.svg`** — the static final mark (use for favicons, print, social).

## Tweaking
All the dials live in the `:root` block at the top of `index.html`:

| Variable | What it does |
|---|---|
| `--ink` / `--bg` | logo + background colours |
| `--stroke-weight` | thickness of the letter strokes |
| `--kern-slide` | how far A & M travel to lock together |
| `--draw-dur` | letter draw-on speed |
| `--slide-dur` | slide-together speed |
| `--bar-dur` | sightline extend speed |
| `--loop-gap` | pause before the animation loops |

- **Replay** button re-triggers the animation; it also auto-loops.
- Respects `prefers-reduced-motion` (renders the static final state, no motion).

## Exporting to video/GIF
With `ffmpeg` + a headless screen recorder, or simplest via a browser screen
recording of the looping page. For a transparent WebM, set `--bg:transparent`
in `:root`, record, then export. Ask and I can wire up an automated
Puppeteer-based capture script.

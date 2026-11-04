# How it works: the animation

`how_it_works.py` is a [Manim](https://www.manim.community) scene. It makes
[`../images/how-it-works.gif`](../images/how-it-works.gif), which follows a knob turned in the Dash app
through the library to your callback, and the dial update back out to two apps, then a DashStore uploading
history to the Dash server. Keep it in step with the code: the names it shows are real (the `aKNB` knob,
`dial1` dial and `knob_event_handler` of `Examples/ex03.py`, the connection classes, ZMQ, the Device
thread's `_on_message()`, publishing to `"ALL"`, `state_str`, `app_timeout`, `batch_delay`, `DashStore`
and the SDU messages).

## Rendering

Manim needs Cairo and pkg-config (`brew install cairo pkgconf`, or `apt install libcairo2-dev
libpango1.0-dev pkg-config`). It doesn't need LaTeX: the scene only uses `Text`.

```sh
python3 -m venv .venv && .venv/bin/pip install manim
.venv/bin/manim --resolution 1280,720 --fps 15 how_it_works.py HowItWorks
.venv/bin/python to_gif.py media/videos/how_it_works/720p15/HowItWorks.mp4 ../images/how-it-works.gif 960
```

For a quick draft, use `-ql` in place of `--resolution` and `--fps`. The fonts are Helvetica Neue and Menlo,
from macOS; other systems substitute their own.

Manim's own `--format gif` writes every frame whole. `to_gif.py` stores only what changes between frames,
which gives about 5 MB for the minute.

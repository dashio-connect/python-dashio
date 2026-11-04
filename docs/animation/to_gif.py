"""
Converts the rendered MP4 to a small looping GIF for the README.

Manim's own GIF output stores every frame whole (about 300 MB here). This one stores only what
changes: pixels that change by less than THRESH (the video's compression noise) keep their last
value, so most of each frame is unchanged, and all frames share one palette.

    python to_gif.py <video.mp4> <out.gif> [width]
"""

import sys

import av
import numpy as np
from PIL import Image

THRESH = 6
REFRESH = 30  # Frames between full refreshes, so slow fades leave nothing behind


def main():
    src, dst = sys.argv[1], sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 960

    rgb = []
    with av.open(src) as container:
        stream = container.streams.video[0]
        step = 1000 / float(stream.average_rate)
        for frame in container.decode(stream):
            img = frame.to_image()
            img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
            rgb.append(np.asarray(img).astype(np.int16))

    frames, durations, cur = [], [], None
    for n, a in enumerate(rgb):
        if cur is None or n % REFRESH == 0:
            cur = a.copy()
        else:
            mask = np.abs(a - cur).max(axis=2) > THRESH
            if not mask.any():
                durations[-1] += step
                continue
            # Grow the mask by a pixel, so anti-aliased edges change with what they border
            grown = mask.copy()
            grown[1:] |= mask[:-1]
            grown[:-1] |= mask[1:]
            grown[:, 1:] |= mask[:, :-1]
            grown[:, :-1] |= mask[:, 1:]
            cur = np.where(grown[..., None], a, cur)
        frames.append(Image.fromarray(cur.astype(np.uint8)))
        durations.append(step)

    # One palette from frames across the whole animation. Octree keeps the small bright colours
    # (the knob's arc) that median cut gives up to the large dark areas.
    picks = frames[:: max(1, len(frames) // 12)]
    sample = Image.new("RGB", (frames[0].width, frames[0].height * len(picks)))
    for i, f in enumerate(picks):
        sample.paste(f, (0, i * frames[0].height))
    palette = sample.quantize(colors=128, method=Image.Quantize.FASTOCTREE)
    out = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]

    # GIF delays are in centiseconds: round the frame boundaries, not each delay, so the
    # animation keeps its length
    ends = np.round(np.cumsum(durations) / 10) * 10
    delays = np.diff(np.concatenate([[0], ends])).astype(int).tolist()
    out[0].save(dst, save_all=True, append_images=out[1:], duration=delays, loop=0, disposal=1)
    print(f"{len(rgb)} frames -> {len(out)}, {sum(durations) / 1000:.1f} s")


if __name__ == "__main__":
    main()

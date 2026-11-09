#!/usr/bin/env python3
"""
Prepare electerm-android screenshots for the Google Play store listing.

Play's rules for phone screenshots (see the "Add preview assets" help page):

  - JPEG or 24-bit PNG (no alpha)
  - Minimum dimension 320 px, maximum 3840 px
  - The maximum dimension must not be more than TWICE the minimum dimension
  - For eligibility in recommendation surfaces, at least four screenshots at
    1080 px or above, 9:16 portrait (1080x1920) or 16:9 landscape

The device screenshots come off a modern phone: 1152x2376, which is a ratio of
2.06 — over Play's hard limit of 2.0, so the store would reject them as they
are. Two things have to come off:

  - the status bar (grey strip at the top), and
  - the keyboard-shortcut bar at the bottom (the orange Esc / Tab / Ctrl row).

Both boundaries are measured per image rather than hardcoded: the status bar
height differs between shots (the clock and carrier text change the layout),
so a fixed crop leaves a grey sliver on some of them.

Output: temp/play-assets/screenshot-{1,2,3}.jpg
"""

from PIL import Image
import os

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ANDROID_ROOT = os.path.join(os.path.dirname(_REPO_ROOT), 'electerm-android')
SRC_DIR = os.path.join(_ANDROID_ROOT, 'temp')
OUT_DIR = os.path.join(_ANDROID_ROOT, 'temp', 'play-assets')

SOURCES = ['w1.jpg', 'w2.jpg', 'w3.jpg']

# Play's recommended portrait ratio.
TARGET_H = 2048  # 1152 * 16 / 9

# The app's terminal background, sampled from the source screenshots.
BG = (37, 18, 1)

JPEG_QUALITY = 92


def find_status_bar_bottom(im):
    """First row that is no longer the flat grey of the status bar.

    The status bar is a solid grey strip and the app content below it is
    dark. Scanning down the left edge — away from the clock, the signal icons
    and the battery — finds the boundary without being confused by them.
    """
    px = im.load()
    w, h = im.size
    probes = [2, 12, 24, 36]
    for y in range(h):
        row = [px[x, y] for x in probes]
        # The status bar grey is uniform grey; anything else means we are past it.
        if all(c[0] == c[1] == c[2] and abs(c[0] - 117) <= 8 for c in row):
            continue
        return y
    return 0


def find_shortcut_bar_top(im):
    """Top of the orange shortcut bar, scanning up from the bottom.

    The shortcut bar (Esc / Tab / Ctrl+C / Ctrl+V / Ctrl+Z) starts with a
    solid orange rule that spans the full width. That full-width rule is the
    reliable marker: the keys further down only cover part of the row, and
    the About dialog in w2 has no such bar at all (it does contain a large
    brown logo plate, which a loose colour match picks up instead).
    """
    px = im.load()
    w, h = im.size
    step = 4
    samples = len(range(0, w, step))
    for y in range(h - 1, 0, -1):
        orange = sum(1 for x in range(0, w, step)
                     if px[x, y][0] > 120
                     and 60 < px[x, y][1] < 110
                     and px[x, y][2] < 70)
        # The top rule of the bar covers the whole width.
        if orange > samples * 0.9:
            return y
    return h


def prepare(name):
    src_path = os.path.join(SRC_DIR, name)
    if not os.path.exists(src_path):
        raise SystemExit(f'FATAL: {src_path} not found')

    im = Image.open(src_path).convert('RGB')
    w, h = im.size
    print(f'{name}: source {w}x{h} (ratio {max(w, h) / min(w, h):.3f})')

    status_bottom = find_status_bar_bottom(im)
    shortcut_top = find_shortcut_bar_top(im)
    print(f'  status bar ends at y={status_bottom}, '
          f'shortcut bar starts at y={shortcut_top}')

    # Crop the status bar and the shortcut bar.
    content = im.crop((0, status_bottom, w, shortcut_top))
    cw, ch = content.size
    print(f'  cropped to {cw}x{ch} (ratio {max(cw, ch) / min(cw, ch):.3f})')

    if max(cw, ch) > 2 * min(cw, ch):
        raise SystemExit(
            f'FATAL: {name} is still over Play\'s 2:1 limit after cropping')

    # Pad to 9:16 with the app background, centring the content.
    if ch < TARGET_H:
        pad = TARGET_H - ch
        top = pad // 2
        canvas = Image.new('RGB', (cw, TARGET_H), BG)
        canvas.paste(content, (0, top))
        content = canvas
        print(f'  padded to {cw}x{TARGET_H} (9:16), {pad}px split '
              f'{top}/{pad - top}')

    out_name = f'screenshot-{name.split(".")[0].replace("w", "")}.jpg'
    out_path = os.path.join(OUT_DIR, out_name)
    content.save(out_path, 'JPEG', quality=JPEG_QUALITY, optimize=True)

    size = os.path.getsize(out_path)
    print(f'  -> {out_path} ({size / 1024:.1f} KB)')
    return out_path


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f'Source: {SRC_DIR}')
    print(f'Output: {OUT_DIR}\n')

    for name in SOURCES:
        prepare(name)
        print()

    print('All screenshots prepared. Upload them under')
    print('Grow users -> Store presence -> Main store listing ->')
    print('Graphics -> Phone screenshots.')


if __name__ == '__main__':
    main()

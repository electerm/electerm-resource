#!/usr/bin/env python3
"""
Generate Google Play store listing graphics for electerm-android.

Produces (into OUT_DIR, default: ../temp/play-assets of the electerm-android
repo):

    play-icon-512.png      App icon       512x512  32-bit PNG, full square
    play-feature-1024x500.png  Feature graphic  1024x500  24-bit PNG, no alpha

Google Play's rules this script follows (see the "Add preview assets" help
page and the icon design specifications):

  App icon
    - 512x512, 32-bit PNG, max 1024 KB, sRGB
    - FULL SQUARE. Play applies its own rounded mask (30% radius) and its own
      drop shadow, so the source must not have rounded corners or a baked-in
      shadow. A pre-rounded source gets masked a second time and looks wrong.
    - The artwork should fill the canvas; a minimalistic mark works best as a
      full-bleed background.

  Feature graphic
    - 1024x500, JPEG or 24-bit PNG (no alpha)
    - The focal point has to sit in the middle, because the edges get cut off
      in some Play surfaces. Keep the logo clear of the outer margins.
    - Avoid pure white / black / dark grey backgrounds: they blend into the
      Play Store chrome. The electerm dark slate (#15171a) reads as the app's
      own theme instead.

Screenshots are NOT generated here — those have to be captured from a real
device running the app.

Sources (all from this repo):
    static/images/electerm-logo-2016-square.png   full-bleed square mark
    static/images/electerm.png                   wordmark (white on transparent)
"""

from PIL import Image
import os

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE_SQUARE = os.path.join(
    _REPO_ROOT, 'static', 'images', 'electerm-logo-2016-square.png')
SOURCE_MARK = os.path.join(
    _REPO_ROOT, 'static', 'images', 'electerm-logo-2048-1.png')
SOURCE_WORDMARK = os.path.join(
    _REPO_ROOT, 'static', 'images', 'electerm.png')

# Where the assets land. Defaults to the electerm-android repo checkout that
# sits next to this one; override with argv[1].
_DEFAULT_OUT = os.path.join(
    os.path.dirname(_REPO_ROOT), 'electerm-android', 'temp', 'play-assets')

ICON_SIZE = 512
FEATURE_W, FEATURE_H = 1024, 500

# Brand colours (also used by the app itself).
BRAND_BG = (21, 23, 26)        # #15171a — electerm dark slate
BRAND_MARK = (83, 71, 65)      # #534741 — icon plate brown


def _save_png(img, path, optimize=True):
    """Save a PNG and report its size — Play caps the icon at 1024 KB."""
    img.save(path, 'PNG', optimize=optimize)
    size = os.path.getsize(path)
    print(f'Created: {path} ({img.width}x{img.height}, {size / 1024:.1f} KB)')
    return size


def create_app_icon(out_dir):
    """512x512 full-square app icon.

    The source is already a full-bleed square with no rounded corners, so it
    only needs resizing. Play masks it itself.

    Play asks for a 32-bit PNG, which means an alpha channel. The artwork is
    opaque, but the channel is written anyway (fully opaque) so the file is
    literally a 32-bit PNG as specified.
    """
    source = Image.open(SOURCE_SQUARE).convert('RGB')
    icon = source.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS).convert('RGBA')

    path = os.path.join(out_dir, 'play-icon-512.png')
    size = _save_png(icon, path)

    if size > 1024 * 1024:
        raise SystemExit(
            f'FATAL: the icon is {size / 1024:.1f} KB, over Play\'s 1024 KB limit'
        )

    # Guard against shipping a pre-rounded or transparent icon by mistake.
    corner = icon.getpixel((0, 0))
    if corner[:3] != BRAND_MARK:
        raise SystemExit(
            f'FATAL: the top-left corner is {corner}, expected the flat brand '
            f'colour {BRAND_MARK}. Play masks the icon itself — the source '
            'must be a full square with square corners.'
        )
    print('         full square, square corners, 32-bit PNG — as Play expects')
    return path


def create_feature_graphic(out_dir):
    """1024x500 feature graphic.

    Layout: the logo mark and wordmark sit as one centred group, on the
    electerm dark slate. Play crops the edges in some surfaces, so everything
    that matters stays in the middle band.
    """
    feature = Image.new('RGB', (FEATURE_W, FEATURE_H), BRAND_BG)

    # The mark: the rounded-square version, so the plate does not read as a
    # hard brown slab sitting on the dark background. The 2016 square source
    # is used for the app icon instead, where Play needs a full square.
    mark_source = Image.open(SOURCE_MARK).convert('RGBA')
    mark_size = 240
    mark = mark_source.resize((mark_size, mark_size), Image.LANCZOS)

    # The wordmark, recoloured to solid white so it reads on the dark plate.
    wordmark_source = Image.open(SOURCE_WORDMARK).convert('RGBA')
    # Trim the transparent padding so the group is centred on its own ink.
    bbox = wordmark_source.getbbox()
    if bbox:
        wordmark_source = wordmark_source.crop(bbox)
    wordmark_height = 84
    ratio = wordmark_height / wordmark_source.height
    wordmark = wordmark_source.resize(
        (max(1, int(wordmark_source.width * ratio)), wordmark_height),
        Image.LANCZOS)

    # Recolor by thresholding the alpha channel rather than compositing a
    # white layer: the source wordmark is black, and alpha-compositing white
    # over black leaves grey fringes along every glyph edge.
    alpha = wordmark.getchannel('A')
    wordmark = Image.new('RGBA', wordmark.size, (255, 255, 255, 0))
    wordmark.putalpha(alpha.point(lambda a: 255 if a > 96 else 0))

    gap = 36
    group_w = mark_size + gap + wordmark.width
    group_h = max(mark_size, wordmark.height)
    group_x = (FEATURE_W - group_w) // 2
    group_y = (FEATURE_H - group_h) // 2

    feature.paste(mark, (group_x, group_y), mark)
    # Centre the wordmark against the mark, not against the group's box.
    feature.paste(
        wordmark,
        (group_x + mark_size + gap,
         group_y + (mark_size - wordmark.height) // 2),
        wordmark)

    path = os.path.join(out_dir, 'play-feature-1024x500.png')
    # 24-bit PNG: convert to RGB so there is no alpha channel.
    _save_png(feature.convert('RGB'), path)

    left = group_x
    right = group_x + group_w
    print(f'         group spans x {left}..{right} of {FEATURE_W}, '
          f'centred with {left}px margins on both sides')
    return path


def main():
    out_dir = os.path.abspath(
        sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_OUT)
    os.makedirs(out_dir, exist_ok=True)
    print(f'Output directory: {out_dir}\n')

    print(f'Source mark:      {SOURCE_SQUARE}')
    print(f'Source wordmark:  {SOURCE_WORDMARK}\n')

    create_app_icon(out_dir)
    print()
    create_feature_graphic(out_dir)

    print('\nDone. Upload play-icon-512.png and play-feature-1024x500.png in')
    print('Play Console under Grow users -> Store presence -> Main store listing.')
    print('\nScreenshots are not generated by this script — capture those from a')
    print('real device or emulator running the app.')


if __name__ == '__main__':
    import sys
    main()

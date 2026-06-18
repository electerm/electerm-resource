#!/usr/bin/env python3
"""Generate appx and build icon files from the source logo."""

from PIL import Image

SOURCE = 'static/images/electerm-logo-2048-1.png'

def make_resized(src, size, bg=(0, 0, 0, 0)):
    """Resize logo to target size, centering on transparent background for non-square."""
    w, h = size
    img = src.copy()
    img.thumbnail((w, h), Image.LANCZOS)
    if img.size == (w, h):
        return img
    canvas = Image.new('RGBA', (w, h), bg)
    offset = ((w - img.width) // 2, (h - img.height) // 2)
    canvas.paste(img, offset, img if img.mode == 'RGBA' else None)
    return canvas

def main():
    src = Image.open(SOURCE).convert('RGBA')
    print(f'Source: {src.size}')

    # --- APPX ---
    appx_specs = {
        'build-res/appx/Square44x44Logo.png': (44, 44),
        'build-res/appx/Square150x150Logo.png': (150, 150),
        'build-res/appx/StoreLogo.png': (1080, 1080),
        'build-res/appx/Wide310x150Logo.png': (310, 150),
    }
    for path, size in appx_specs.items():
        img = make_resized(src, size)
        img.save(path)
        print(f'Saved {path} ({img.size})')

    # --- ICO (Windows) ---
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_images = [make_resized(src, s) for s in ico_sizes]

    # icons.ico and icons-win.ico are identical
    # ICO: save the largest image, tell Pillow to embed these sizes
    for path in ['build/icons.ico', 'build/icons-win.ico']:
        ico_images[-1].save(path, format='ICO', sizes=ico_sizes)
        print(f'Saved {path} ({len(ico_sizes)} sizes)')

    # --- ICNS (macOS) ---
    icns_sizes = [(16, 16), (32, 32), (128, 128), (256, 256), (512, 512), (1024, 1024)]
    icns_images = [make_resized(src, s) for s in icns_sizes]
    icns_path = 'build/icons.icns'
    icns_images[0].save(icns_path, format='ICNS', append_images=icns_images[1:])
    print(f'Saved {icns_path} ({len(icns_sizes)} sizes)')

    print('Done!')

if __name__ == '__main__':
    main()

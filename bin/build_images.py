#!/usr/bin/env python3
"""
Generate build images from source logos.
Creates:
  - build-res/appx/*.png (Windows Store icons, from electerm-logo-transparent.png)
  - build/icons.icns (macOS icon, from electerm-logo-mac.png)
  - build/icons.ico (Windows icon, from electerm-logo-transparent.png)
  - build/icons-win.ico (Windows icon, from electerm-logo-transparent.png)
"""

from PIL import Image
import struct
import io
import os

SOURCE_MAC = '/Users/zxd/dev/electerm-resource/static/images/electerm-logo-mac.png'
SOURCE_TRANSPARENT = '/Users/zxd/dev/electerm-resource/static/images/electerm-logo-transparent.png'
APPX_DIR = '/Users/zxd/dev/electerm-resource/build-res/appx/'
BUILD_DIR = '/Users/zxd/dev/electerm-resource/build/'


def resize_image(source, size):
    """Resize source image to target size with high quality."""
    return source.resize((size, size), Image.LANCZOS)


def create_appx_images(source):
    """Create Windows Store PNG images."""
    appx_specs = [
        ('Square44x44Logo.png', 44),
        ('Square150x150Logo.png', 150),
        ('Wide310x150Logo.png', (310, 150)),
        ('StoreLogo.png', 1080),
    ]

    for filename, size in appx_specs:
        if isinstance(size, tuple):
            # Wide format - resize to fit height, then crop/center to width
            w, h = size
            # Resize to fill height
            ratio = h / source.height
            new_w = int(source.width * ratio)
            img = source.resize((new_w, h), Image.LANCZOS)
            # Center crop to target width
            left = (new_w - w) // 2
            img = img.crop((left, 0, left + w, h))
        else:
            img = resize_image(source, size)

        output_path = os.path.join(APPX_DIR, filename)
        img.save(output_path, 'PNG')
        print(f'Created: {output_path} ({img.size[0]}x{img.size[1]})')


def create_ico(source):
    """Create Windows .ico files with multiple sizes."""
    ico_sizes = [16, 32, 48, 64, 128, 256]

    for ico_name in ['icons.ico', 'icons-win.ico']:
        output_path = os.path.join(BUILD_DIR, ico_name)
        source.save(
            output_path,
            format='ICO',
            sizes=[(s, s) for s in ico_sizes]
        )
        print(f'Created: {output_path}')


def create_icns(source, output_dir=BUILD_DIR, output_name='icons.icns'):
    """Create macOS .icns file with all required sizes."""
    # ICNS icon types and their sizes
    icns_entries = [
        ('ic11', 16),     # 16x16
        ('ic12', 32),     # 32x32
        ('ic07', 128),    # 128x128
        ('ic13', 256),    # 256x256 @2x
        ('ic08', 256),    # 256x256
        ('ic14', 512),    # 512x512 @2x
        ('ic09', 512),    # 512x512
        ('ic10', 1024),   # 1024x1024
    ]

    # Build ICNS file manually
    icns_data = bytearray()

    # Reserve space for header (magic + file size)
    icns_data.extend(b'icns')
    icns_data.extend(struct.pack('>I', 0))  # placeholder for file size

    for icon_type, size in icns_entries:
        img = resize_image(source, size)

        # Convert to PNG in memory
        png_buffer = io.BytesIO()
        img.save(png_buffer, format='PNG')
        png_bytes = png_buffer.getvalue()

        # Write icon entry
        entry_size = 8 + len(png_bytes)
        icns_data.extend(icon_type.encode('ascii'))
        icns_data.extend(struct.pack('>I', entry_size))
        icns_data.extend(png_bytes)

    # Update file size in header
    file_size = len(icns_data)
    icns_data[4:8] = struct.pack('>I', file_size)

    output_path = os.path.join(output_dir, output_name)
    with open(output_path, 'wb') as f:
        f.write(icns_data)

    print(f'Created: {output_path} ({file_size} bytes)')


def main():
    print(f'Loading mac source: {SOURCE_MAC}')
    source_mac = Image.open(SOURCE_MAC).convert('RGBA')
    print(f'Source size: {source_mac.size}')

    print(f'Loading transparent source: {SOURCE_TRANSPARENT}')
    source_transparent = Image.open(SOURCE_TRANSPARENT).convert('RGBA')
    print(f'Source size: {source_transparent.size}')

    # icns uses the mac logo
    create_icns(source_mac)

    # appx and ico/ico-win use the transparent logo
    create_appx_images(source_transparent)
    create_ico(source_transparent)

    print('\nDone! All images created.')


if __name__ == '__main__':
    main()

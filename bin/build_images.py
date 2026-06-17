#!/usr/bin/env python3
"""
Generate build images from source logo.
Creates:
  - build-res/appx/*.png (Windows Store icons)
  - build/icons.icns (macOS icon)
  - build/icons.ico (Windows icon)
  - build/icons-win.ico (Windows icon)
"""

from PIL import Image
import struct
import io
import os

SOURCE = '/Users/zxd/dev/electerm-resource/static/images/electerm-logo-2048.png'
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
        images = [resize_image(source, s) for s in ico_sizes]
        images[0].save(
            output_path,
            format='ICO',
            sizes=[(s, s) for s in ico_sizes],
            append_images=images[1:]
        )
        print(f'Created: {output_path}')


def create_icns(source):
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

    output_path = os.path.join(BUILD_DIR, 'icons.icns')
    with open(output_path, 'wb') as f:
        f.write(icns_data)

    print(f'Created: {output_path} ({file_size} bytes)')


def main():
    print(f'Loading source: {SOURCE}')
    source = Image.open(SOURCE).convert('RGBA')
    print(f'Source size: {source.size}')

    create_appx_images(source)
    create_ico(source)
    create_icns(source)

    print('\nDone! All images created.')


if __name__ == '__main__':
    main()

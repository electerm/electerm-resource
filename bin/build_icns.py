#!/usr/bin/env python3
"""
Create macOS .icns file from temp logo.
"""

from PIL import Image
import struct
import io

SOURCE = '/Users/zxd/dev/electerm-resource/temp/electerm-logo-2048.png'
OUTPUT = '/Users/zxd/dev/electerm-resource/build/icons.icns'


def resize_image(source, size):
    """Resize source image to target size with high quality."""
    return source.resize((size, size), Image.LANCZOS)


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

        # Convert to RGBA for PNG
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

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

    with open(OUTPUT, 'wb') as f:
        f.write(icns_data)

    print(f'Created: {OUTPUT} ({file_size} bytes)')


def main():
    print(f'Loading source: {SOURCE}')
    source = Image.open(SOURCE)
    print(f'Source size: {source.size}, mode: {source.mode}')

    create_icns(source)
    print('Done!')


if __name__ == '__main__':
    main()

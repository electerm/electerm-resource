#!/usr/bin/env python3
"""
Create Windows .ico files matching original sizes.
"""

from PIL import Image
import struct
import io

SOURCE = '/Users/zxd/dev/electerm-resource/static/images/electerm-logo-2048.png'
BUILD_DIR = '/Users/zxd/dev/electerm-resource/build/'


def resize_image(source, size):
    """Resize source image to target size with high quality."""
    return source.resize((size, size), Image.LANCZOS)


def create_ico_manual(images, output_path):
    """Create ICO file manually for proper multi-size support."""
    # ICO header: reserved(2) + type(2) + count(2)
    ico_data = bytearray()
    ico_data.extend(struct.pack('<HHH', 0, 1, len(images)))

    # Calculate offset to image data (header + directory entries)
    # Each entry: 16 bytes
    data_offset = 6 + len(images) * 16

    # Collect PNG data for each image
    png_data_list = []
    for img in images:
        # Convert to RGBA
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Save as PNG in memory
        png_buffer = io.BytesIO()
        img.save(png_buffer, format='PNG')
        png_data_list.append(png_buffer.getvalue())

    # Write directory entries
    for i, (img, png_data) in enumerate(zip(images, png_data_list)):
        width = img.size[0] if img.size[0] < 256 else 0
        height = img.size[1] if img.size[1] < 256 else 0

        ico_data.extend(struct.pack('BBBB', width, height, 0, 0))  # width, height, colors, reserved
        ico_data.extend(struct.pack('<HH', 1, 32))  # planes, bpp
        ico_data.extend(struct.pack('<I', len(png_data)))  # data size
        ico_data.extend(struct.pack('<I', data_offset))  # data offset

        # Update offset for next image
        data_offset += len(png_data)

    # Write image data
    for png_data in png_data_list:
        ico_data.extend(png_data)

    with open(output_path, 'wb') as f:
        f.write(ico_data)


def create_ico_files(source):
    """Create Windows .ico files matching original sizes."""
    # icons.ico: 4 images (16, 32, 48, 256)
    ico_sizes = [16, 32, 48, 256]
    images = [resize_image(source, s) for s in ico_sizes]
    output_path = BUILD_DIR + 'icons.ico'
    create_ico_manual(images, output_path)
    print(f'Created: {output_path} ({len(images)} images)')

    # icons-win.ico: 1 image (256x256)
    win_img = resize_image(source, 256)
    output_path = BUILD_DIR + 'icons-win.ico'
    create_ico_manual([win_img], output_path)
    print(f'Created: {output_path} (1 image)')


def main():
    print(f'Loading source: {SOURCE}')
    source = Image.open(SOURCE).convert('RGBA')
    print(f'Source size: {source.size}')

    create_ico_files(source)
    print('Done!')


if __name__ == '__main__':
    main()

"""
AgriLink PWA Icons Generator
============================
SVG → PNG icons बनवतो (Windows friendly)

INSTALL: pip install svglib reportlab pillow
RUN: python generate_icons.py
"""

import os
from PIL import Image
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

INPUT_SVG  = 'projectapp/static/images/agrilink-icon.svg'
OUTPUT_DIR = 'projectapp/static/images/'
SIZES      = [72, 96, 128, 144, 152, 192, 384, 512]

os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_icons(svg_path, output_dir, sizes):
    if not os.path.exists(svg_path):
        print(f'❌ File not found: {svg_path}')
        return

    print(f'📂 Input : {svg_path}')
    print(f'📁 Output: {output_dir}\n')

    drawing = svg2rlg(svg_path)
    tmp = os.path.join(output_dir, '_tmp_base.png')
    renderPM.drawToFile(drawing, tmp, fmt='PNG')

    base = Image.open(tmp).convert('RGBA')

    for size in sizes:
        out = os.path.join(output_dir, f'icon-{size}x{size}.png')
        base.resize((size, size), Image.LANCZOS).save(out, 'PNG')
        print(f'✅ icon-{size}x{size}.png')

    os.remove(tmp)
    print(f'\n🎉 All {len(sizes)} icons created!')

if __name__ == '__main__':
    print('🌾 AgriLink PWA Icon Generator starting...\n')
    generate_icons(INPUT_SVG, OUTPUT_DIR, SIZES)
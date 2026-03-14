"""
AgriLink PWA Icons Generator
============================
तुमच्या existing logo वरून सगळे icons बनवतो.

INSTALL: pip install Pillow
RUN: python generate_icons.py

तुमचा logo image path खाली set करा.
"""

from PIL import Image
import os

# ✅ तुमचा existing logo/image path येथे set करा
INPUT_IMAGE = 'projectapp/static/images/farmer2.jpg'
# Output folder
OUTPUT_DIR = 'static/images/'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Required icon sizes for PWA
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]


def generate_icons(input_path, output_dir, sizes):
    try:
        img = Image.open(input_path).convert('RGBA')

        for size in sizes:
            resized = img.resize((size, size), Image.LANCZOS)
            output_path = os.path.join(output_dir, f'icon-{size}x{size}.png')
            resized.save(output_path, 'PNG')
            print(f'✅ Created: {output_path}')

        print(f'\n🎉 All {len(sizes)} icons created in {output_dir}')
        print('Icons list:')
        for size in sizes:
            print(f'  - icon-{size}x{size}.png')

    except FileNotFoundError:
        print(f'❌ Image not found: {input_path}')
        print('👉 INPUT_IMAGE path बदला — तुमच्या logo चा path द्या')
    except Exception as e:
        print(f'❌ Error: {e}')


if __name__ == '__main__':
    print('🌾 AgriLink PWA Icon Generator starting...')
    generate_icons(INPUT_IMAGE, OUTPUT_DIR, SIZES)
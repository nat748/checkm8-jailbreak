"""
Generate a simple icon for the checkm8 app using PIL.
Creates both .ico (Windows) and .icns (macOS) formats.
"""

from PIL import Image, ImageDraw, ImageFont
import sys

def create_icon():
    """Create a simple purple gradient icon with 'c8' text."""
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Purple gradient background (circle)
        for i in range(size // 2):
            r = size // 2 - i
            color_intensity = 180 - (i * 60 // (size // 2))
            color = (139 + i, 92 + i, 246 - (i * 40 // (size // 2)), 255)
            draw.ellipse(
                [size // 2 - r, size // 2 - r, size // 2 + r, size // 2 + r],
                fill=color
            )

        # Add "c8" text
        try:
            # Try to use a nice font
            font_size = size // 3
            font = ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            # Fallback to default
            font = ImageFont.load_default()

        text = "c8"
        # Get text bbox for centering
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        position = ((size - text_width) // 2, (size - text_height) // 2 - size // 20)
        draw.text(position, text, fill=(255, 255, 255, 255), font=font)

        images.append(img)

    # Save as .ico (Windows)
    images[0].save(
        'assets/icon.ico',
        format='ICO',
        sizes=[(s, s) for s in sizes]
    )
    print("Created assets/icon.ico")

    # Save as .png for Linux
    images[4].save('assets/icon.png', format='PNG')
    print("Created assets/icon.png")

    # For macOS .icns, we need to create individual png files and use iconutil
    # or we can just save the largest as a placeholder
    images[5].save('assets/icon_256.png', format='PNG')
    print("Created assets/icon_256.png (use 'iconutil' on macOS to create .icns)")
    print("\nTo create .icns on macOS:")
    print("  mkdir icon.iconset")
    print("  sips -z 16 16   icon_256.png --out icon.iconset/icon_16x16.png")
    print("  sips -z 32 32   icon_256.png --out icon.iconset/icon_16x16@2x.png")
    print("  sips -z 32 32   icon_256.png --out icon.iconset/icon_32x32.png")
    print("  sips -z 64 64   icon_256.png --out icon.iconset/icon_32x32@2x.png")
    print("  sips -z 128 128 icon_256.png --out icon.iconset/icon_128x128.png")
    print("  sips -z 256 256 icon_256.png --out icon.iconset/icon_128x128@2x.png")
    print("  iconutil -c icns icon.iconset -o assets/icon.icns")

if __name__ == '__main__':
    create_icon()

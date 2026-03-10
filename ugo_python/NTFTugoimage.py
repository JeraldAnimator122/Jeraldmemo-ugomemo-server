import struct
from pathlib import Path
from PIL import Image


# --- Helpers -------------------------------------------------------------

def rgb_to_bgr555(r, g, b):
    """
    Convert 8-bit per channel RGB to Nintendo DS BGR555 (little-endian 16-bit).
    """
    r5 = (r >> 3) & 0x1F
    g5 = (g >> 3) & 0x1F
    b5 = (b >> 3) & 0x1F
    value = (b5 << 10) | (g5 << 5) | r5
    return struct.pack("<H", value)


def image_to_4bpp_tiles(img):
    """
    Convert a palettized image (mode 'P') to 4bpp tiled data (8x8 tiles).
    Returns (tile_data_bytes, palette_rgba_list).
    """
    if img.mode != "P":
        raise ValueError("Image must be palettized (mode 'P').")

    w, h = img.size
    if w % 8 != 0 or h % 8 != 0:
        raise ValueError("Image width and height must be multiples of 8.")

    # Get palette as list of (r, g, b, a)
    palette = img.getpalette()
    # Pillow palette is [r0,g0,b0, r1,g1,b1, ...]
    palette_rgba = []
    for i in range(0, len(palette), 3):
        r = palette[i]
        g = palette[i + 1]
        b = palette[i + 2]
        palette_rgba.append((r, g, b, 255))

    # Limit to 16 colors for 4bpp
    if len(palette_rgba) > 16:
        palette_rgba = palette_rgba[:16]

    pixels = img.load()
    tiles = bytearray()

    # Walk tiles in 8x8 blocks
    for ty in range(0, h, 8):
        for tx in range(0, w, 8):
            # Each tile: 8x8 pixels, 4bpp → 32 bytes
            for y in range(8):
                row = []
                for x in range(8):
                    idx = pixels[tx + x, ty + y]
                    if idx >= 16:
                        idx = 0  # clamp to first 16 colors
                    row.append(idx)

                # Pack 2 pixels per byte: low nibble = first, high nibble = second
                for i in range(0, 8, 2):
                    p0 = row[i] & 0x0F
                    p1 = row[i + 1] & 0x0F
                    byte = p0 | (p1 << 4)
                    tiles.append(byte)

    return bytes(tiles), palette_rgba[:16]


def write_ntft_stub(path, width, height, tile_data):
    """
    Write a very simple NTFT-like file:
    [header stub][raw 4bpp tile data]

    This is NOT a fully correct Nitro NTFT header—it's a stub you can adapt.
    """
    with open(path, "wb") as f:
        # --- Fake header (16 bytes) ---
        # Magic
        f.write(b"NTFT")
        # Width, Height (pixels)
        f.write(struct.pack("<HH", width, height))
        # Format: 4bpp tiled (placeholder value)
        f.write(struct.pack("<H", 0x0003))
        # Reserved / padding
        f.write(b"\x00" * 6)

        # --- Tile data ---
        f.write(tile_data)


def write_palette_bgr555(path, palette_rgba):
    """
    Write a .pal file with 16 BGR555 colors (little-endian).
    """
    with open(path, "wb") as f:
        for i in range(16):
            if i < len(palette_rgba):
                r, g, b, a = palette_rgba[i]
            else:
                r, g, b, a = (0, 0, 0, 255)
            f.write(rgb_to_bgr555(r, g, b))


# --- Main conversion -----------------------------------------------------

def convert_png_to_ntft(input_path):
    input_path = Path(input_path)
    img = Image.open(input_path).convert("RGBA")

    # Quantize to 16 colors, then palettize
    img = img.quantize(colors=16, method=Image.MEDIANCUT)
    img = img.convert("P")

    w, h = img.size
    tile_data, palette = image_to_4bpp_tiles(img)

    ntft_path = input_path.with_suffix(".ntft")
    pal_path = input_path.with_suffix(".pal")

    write_ntft_stub(ntft_path, w, h, tile_data)
    write_palette_bgr555(pal_path, palette)

    print(f"Written: {ntft_path}")
    print(f"Written: {pal_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python png_to_ntft.py input.png")
        sys.exit(1)

    convert_png_to_ntft(sys.argv[1])

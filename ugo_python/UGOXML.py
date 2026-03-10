#!/usr/bin/env python3
"""
ugomemo-ugo.py
Convert UGOXML → UGAR-style .ugo binary files
Compatible with Jeraldmemo’s UGO loader.
"""

import base64
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
import sys


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def b64_utf16le(text: str) -> str:
    """Encode a string as UTF-16LE → Base64 (Hatena-style)."""
    return base64.b64encode(text.encode("utf-16le")).decode("ascii")


def parse_ugoxml(path: Path):
    """Extract layout, title, and button records from UGOXML."""
    tree = ET.parse(path)
    root = tree.getroot()

    # Layout
    layout = int(root.findtext("./layout/value", default="0"))

    # Title block
    title = root.find("title")
    title_labels = []
    if title is not None:
        for lbl in title.findall("label"):
            title_labels.append((lbl.text or "").strip())
        title_num = int(title.findtext("num", default="0"))
    else:
        title_num = 0

    # Buttons
    buttons = []
    for btn in root.findall("button"):
        label = (btn.findtext("label") or "").strip()
        address = (btn.findtext("address") or "").strip()
        trait = int(btn.findtext("trait", default="0"))
        buttons.append((label, address, trait))

    return layout, title_labels, title_num, buttons


def build_records(layout, title_labels, title_num, buttons):
    """Build UGAR-style record list."""
    records = []

    # -----------------------------
    # Type 1: Title record
    # -----------------------------
    # Format we’ve seen:
    # 1   0   <label0_b64> <label1_b64> <label2_b64> <desc_b64>
    main = title_labels[0] if len(title_labels) > 0 else ""
    sub = title_labels[1] if len(title_labels) > 1 else ""
    extra = title_labels[2] if len(title_labels) > 2 else ""
    desc = ""  # optional description

    records.append((
        1,
        0,
        [
            b64_utf16le(main),
            b64_utf16le(sub),
            b64_utf16le(extra),
            b64_utf16le(desc),
        ]
    ))

    # -----------------------------
    # Type 4: Button records
    # -----------------------------
    # Format:
    # 4   <address>   <trait>   <label_b64>   0
    for label, address, trait in buttons:
        records.append((
            4,
            0,
            [
                address,
                str(trait),
                b64_utf16le(label),
                "0",
            ]
        ))

    return records


def write_ugo(path: Path, records):
    """
    Write a UGAR-style .ugo file:
    [ 'UGAR' magic ]
    [ uint32 version ]
    [ uint32 record_count ]
    [ UTF-8 text lines ]
    """
    with open(path, "wb") as f:
        # Magic
        f.write(b"UGAR")

        # Version (placeholder)
        f.write(struct.pack("<I", 2))

        # Record count
        f.write(struct.pack("<I", len(records)))

        # Write each record as a tab-separated line
        for rec_type, flags, fields in records:
            line = str(rec_type) + "\t" + "\t".join(fields) + "\n"
            f.write(line.encode("utf-8"))


def convert(input_path: str):
    path = Path(input_path)
    layout, title_labels, title_num, buttons = parse_ugoxml(path)
    records = build_records(layout, title_labels, title_num, buttons)

    out_path = path.with_suffix(".ugo")
    write_ugo(out_path, records)

    print(f"Converted: {path.name} → {out_path.name}")


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python UGOXML.py input.ugoxml")
        sys.exit(1)

    convert(sys.argv[1])

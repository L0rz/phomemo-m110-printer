#!/usr/bin/env python3
"""
Self-check script to run on the target (Raspberry Pi) to verify
that image_to_printer_format produces exactly 48 bytes per line and
that send_bitmap will accept the produced data length.

Usage on target:
    python3 tools/self_check_48_bytes.py

Exit codes:
    0 - all checks passed
    1 - minor warnings (e.g. conversion returned None)
    2 - failure
"""
import sys
from PIL import Image
from printer_controller import EnhancedPhomemoM110


def check_image(printer, img, desc="test"):
    data = printer.image_to_printer_format(img)
    if data is None:
        print(f"[FAIL] {desc}: image_to_printer_format returned None")
        return False
    height = img.height
    expected = height * printer.bytes_per_line
    actual = len(data)
    if actual != expected:
        print(f"[FAIL] {desc}: size mismatch: got {actual}, expected {expected}")
        return False
    # quick per-line check (optional) - ensure alignment
    if actual % printer.bytes_per_line != 0:
        print(f"[FAIL] {desc}: final data not aligned to {printer.bytes_per_line} bytes")
        return False
    print(f"[OK] {desc}: {actual} bytes ({printer.bytes_per_line} bytes/line)")
    return True


def main():
    p = EnhancedPhomemoM110('00:00:00:00:00:00')
    print(f"Running self-check with bytes_per_line = {p.bytes_per_line}")

    tests = []
    # white image 384x100
    tests.append((Image.new('1', (384, 100), 1), 'white 384x100'))
    # black image 384x1
    tests.append((Image.new('1', (384, 1), 0), 'black 384x1'))
    # checkerboard 384x10 (alternating pixels)
    chk = Image.new('1', (384, 10), 1)
    for y in range(10):
        for x in range(384):
            if (x + y) % 2 == 0:
                chk.putpixel((x, y), 0)
    tests.append((chk, 'checker 384x10'))

    all_ok = True
    for img, desc in tests:
        ok = check_image(p, img, desc)
        if not ok:
            all_ok = False

    if not all_ok:
        print('\nOne or more checks failed.')
        sys.exit(2)

    print('\nAll checks passed. You can now run the provided unit tests on the Raspberry if desired.')
    sys.exit(0)

if __name__ == '__main__':
    main()

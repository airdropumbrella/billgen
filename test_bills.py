#!/usr/bin/env python3
"""Verify that all bill templates generate correctly with valid barcodes."""

import barcode
from barcode.writer import ImageWriter
from PIL import Image
import io, os, sys

sys.path.insert(0, os.path.dirname(__file__))
from billgen import TEMPLATES, make_barcode

def test_barcode():
    """Test that barcode generation works."""
    bc_img = make_barcode('TEST-12345', w=300, h=60)
    assert bc_img.width == 300
    assert bc_img.height == 60
    # Check it has both black and white pixels
    pixels = list(bc_img.getdata())
    black = sum(1 for p in pixels if (p[0] if isinstance(p, tuple) else p) < 50)
    white = sum(1 for p in pixels if (p[0] if isinstance(p, tuple) else p) > 200)
    assert black > 50, f'Barcode too few black pixels: {black}'
    assert white > 50, f'Barcode too few white pixels: {white}'
    ratio = black / len(pixels)
    assert 0.15 < ratio < 0.85, f'Barcode bad ratio: {ratio:.1%}'
    print(f'  [PASS] Barcode: {black} black, {white} white ({ratio:.0%})')

def test_template(name):
    """Test that a single template generates successfully."""
    desc, gen_fn = TEMPLATES[name]
    out = f'/tmp/test_{name}.png'
    path, size = gen_fn(out)
    
    img = Image.open(path)
    assert img.width == 420, f'Bad width: {img.width}'
    assert img.height > 400, f'Bad height: {img.height}'
    assert img.height < 1500, f'Too tall: {img.height}'
    
    # Verify image has diverse content (not blank)
    pixels = list(img.resize((100, 100)).getdata())
    colors = set(p[:3] for p in pixels if isinstance(p, tuple))
    assert len(colors) > 10, f'Too few colors: {len(colors)}'
    
    os.remove(out)
    print(f'  [PASS] {name}: {size[0]}x{size[1]} — {desc}')

if __name__ == '__main__':
    print('Testing barcode generation...')
    test_barcode()
    
    for name in TEMPLATES:
        print(f'Testing {name} template...')
        test_template(name)
    
    print(f'\nAll {len(TEMPLATES)} templates passed!')

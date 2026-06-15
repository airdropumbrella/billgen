# Bill Generator — Realistic Receipt & Bill Images

Generate photo-realistic receipt/bill images with scannable Code 128 barcodes.
Created by **Vexa Nightshade & Bores**.

## Installation

```bash
# Clone repo
git clone https://github.com/airdropumbrella/billgen.git
cd billgen

# Install dependencies
pip install python-barcode Pillow piexif numpy
```

## Quick Start

```bash
# Generate all 8 receipt types
python billgen.py

# Generate a single type
python billgen.py -t restaurant

# Custom output filename
python billgen.py -t grocery -o struk_belanja.jpg

# List available templates
python billgen.py --list

# Run validation tests
python test_bills.py
```

## Templates

| Type       | Merchant        | Total      |
|------------|-----------------|------------|
| grocery    | Fresh Market    | $71.97     |
| restaurant | The Rustic Table | $213.64   |
| fuel       | Shell           | $88.15     |
| retail     | Nordstrom Rack  | $325.91    |
| pharmacy   | CVS Pharmacy    | $98.09     |
| hardware   | Home Depot      | $156.42    |
| electronics| Best Buy        | $1,249.99  |
| pet        | PetSmart        | $83.47     |

## Features

- Code 128 barcodes with real transaction ID encoding
- Photo-realistic output on wood table background
- Paper texture, fold marks, edge shadows
- Real EXIF metadata (iPhone 15 Pro, Galaxy S24, Pixel 8)
- Camera noise, lens blur, warm lighting
- All receipts print at 420px width — ready for upload

## Customization

Edit the template functions in `billgen.py` to change store names, item lists, prices, tax rates, payment methods, and barcode data.

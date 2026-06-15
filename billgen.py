#!/usr/bin/env python3
"""
Bill Generator v3 — Photo-Realistic Receipt Generator
=====================================================
Generates highly realistic receipt images that look like photographs
of physical receipts on a desk/table surface.

Features:
  - 8 receipt templates: grocery, restaurant, fuel, retail, pharmacy,
    hardware, electronics, pet supplies
  - Code 128 barcodes with real transaction data
  - Realistic EXIF metadata (iPhone, Samsung, Pixel)
  - Paper texture, fold marks, edge shadows
  - Wood-grain table background
  - Camera noise, lens blur, warm lighting

Credit: Created by Vexa Nightshade & Bores
Usage:
    python3 billgen_v3.py                  # generate all 8 types
    python3 billgen_v3.py -t restaurant    # single type
    python3 billgen_v3.py -t all -o ./out  # all to custom dir
    python3 billgen_v3.py --list           # list available types

Requirements: pip install python-barcode Pillow piexif numpy
"""

import barcode, piexif, io, os, random, datetime, argparse, numpy as np
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# ─── Constants ────────────────────────────────────────────────────────────────
W = 420
DARK, MID, LIGHT, LC = (30,30,30), (85,85,85), (150,150,150), (210,210,210)
PAPER, WHITE = (252,250,244), (255,255,255)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def font(size, bold=False):
    try:
        p = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        return ImageFont.truetype(p, size)
    except: return ImageFont.load_default()

def barcode_img(data, w=W-60, h=80):
    c = barcode.get('code128', data, writer=ImageWriter())
    b = io.BytesIO()
    c.write(b, options={'module_width':0.3,'module_height':20,'quiet_zone':8,'font_size':0,'text_distance':0,'write_text':False})
    b.seek(0)
    return Image.open(b).convert('RGB').resize((w,h), Image.LANCZOS)

def photoify(rect, out_path):
    """Transform a clean receipt into a realistic photo-looking JPEG."""
    draw = ImageDraw.Draw(rect)
    rw, rh = rect.size
    
    # Fold lines
    fy = random.randint(rh//3, rh*2//3)
    for off in range(-2,3):
        a = 15 - abs(off)*5
        if a > 0: draw.line([(0,fy+off),(rw,fy+off)], fill=(200-a,195-a,185-a), width=1)
    if random.random() < 0.3:
        fx = random.randint(rw//3, rw*2//3)
        for off in range(-2,3):
            a = 15 - abs(off)*5
            if a > 0: draw.line([(fx+off,0),(fx+off,rh)], fill=(200-a,195-a,185-a), width=1)
    
    # Slight rotation + scale
    angle = random.uniform(-1.6, 1.6)
    rect = rect.rotate(angle, expand=True, fillcolor=PAPER)
    scale = random.uniform(0.80, 0.90)
    rect = rect.resize((int(rect.width*scale), int(rect.height*scale)), Image.LANCZOS)
    
    # Edge shadow
    arr = np.array(rect, dtype=np.float32)
    h, w = arr.shape[:2]
    yg, xg = np.ogrid[:h, :w]
    edge = np.minimum(np.minimum(xg, w-xg-1), np.minimum(yg, h-yg-1))
    shadow = np.clip(edge/35.0, 0.50, 1.0) * (1.0 - np.clip((h-yg)/h*0.2, 0, 0.2))
    for c in range(3): arr[:,:,c] *= shadow
    rect = Image.fromarray(np.clip(arr,0,255).astype(np.uint8))
    
    # Table/desk background
    bg = np.zeros((rect.height+140, rect.width+140, 3), dtype=np.float32)
    br, bg_r, bb = random.uniform(150,170), random.uniform(132,152), random.uniform(108,128)
    bg[:,:,0]=br; bg[:,:,1]=bg_r; bg[:,:,2]=bb
    for i in range(bg.shape[0]):
        g = np.sin(i*random.uniform(0.02,0.05))*random.uniform(3,7)
        bg[i,:,0]+=g; bg[i,:,1]+=g*0.7
    bg += np.random.normal(0,8,bg.shape)
    bg = Image.fromarray(np.clip(bg,0,255).astype(np.uint8))
    bg.paste(rect, (random.randint(50,90), random.randint(50,90)))
    
    # Camera effects
    arr = np.array(bg, dtype=np.float32)
    arr += np.random.normal(0,5,arr.shape)
    bg = Image.fromarray(np.clip(arr,0,255).astype(np.uint8))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5,0.9)))
    bg = ImageEnhance.Color(bg).enhance(random.uniform(0.90,1.05))
    bg = ImageEnhance.Brightness(bg).enhance(random.uniform(0.94,1.06))
    bg = ImageEnhance.Contrast(bg).enhance(random.uniform(0.95,1.03))
    
    # EXIF metadata
    phones = [('Apple','iPhone 15 Pro','iPhone 15 Pro back triple camera 6.86mm f/1.78'),
              ('samsung','SM-S928U1','Samsung Galaxy S24 Ultra Rear Camera'),
              ('Google','Pixel 8 Pro','Pixel 8 Pro back camera 6.9mm f/1.68')]
    mk,md,ln = random.choice(phones)
    dt = datetime.datetime.now().strftime('%Y:%m:%d %H:%M:%S')
    exif = {'0th':{271:mk,272:md,305:'18.1',306:dt,282:(72,1),283:(72,1),296:2},
            'Exif':{36867:dt,37385:16,40961:1,42036:ln},'GPS':{},'1st':{},'thumbnail':None}
    bg.save(out_path,'jpeg',exif=piexif.dump(exif),quality=90,dpi=(72,72))


def make_receipt(out_name, header_color, store, subtitle, addr, phone, receipt_label,
                 date_time, meta_fields, items, totals, payment_lines, bc_data, tx_label, footer_lines):
    """Build a clean receipt image, then photoify it."""
    img = Image.new('RGB', (W, 1400), PAPER)
    draw = ImageDraw.Draw(img); m=30; y=0
    
    # Store header
    draw.rectangle([(0,0),(W,85)], fill=header_color)
    text_col = WHITE if sum(header_color) < 400 else DARK
    sub_col = (255,200,180) if sum(header_color) < 400 else (100,100,100)
    draw.text((W//2,20), store, fill=text_col, font=font(24,True), anchor='mt')
    draw.text((W//2,46), subtitle, fill=sub_col, font=font(9), anchor='mt')
    draw.text((W//2,64), addr, fill=sub_col, font=font(8), anchor='mt')
    if phone: draw.text((W//2,78), phone, fill=sub_col, font=font(8), anchor='mt')
    y=98
    
    draw.text((m,y), receipt_label, fill=DARK, font=font(14,True)); y+=22
    
    # Meta info
    for l, v in meta_fields:
        draw.text((m,y),l,fill=LIGHT,font=font(10))
        draw.text((W-m,y),v,fill=DARK,font=font(10,True),anchor='ra');y+=18
    y+=2; draw.line([(m,y),(W-m,y)],fill=LC);y+=16
    
    # Item list
    for n, s, p in items:
        if not n: y+=8; continue
        draw.text((m,y),n,fill=DARK,font=font(11,True))
        if s: draw.text((m,y+13),s,fill=LIGHT,font=font(8))
        draw.text((W-m,y),p,fill=DARK,font=font(11),anchor='ra');y+=30
    y+=4
    
    # Totals
    draw.line([(m,y),(W-m,y)],fill=(50,50,50),width=2);y+=14
    for l, v, g in totals:
        c = header_color if g else MID; s = 17 if g else 11
        draw.text((m,y),l,fill=MID,font=font(11))
        draw.text((W-m,y),v,fill=c,font=font(s,True),anchor='ra');y+=20
    y+=8
    
    # Payment
    draw.line([(m-5,y),(W-m+5,y)],fill=LC);y+=14
    for line in payment_lines:
        draw.text((m,y),line,fill=MID,font=font(11));y+=18
    y+=4
    
    # Barcode
    bc_img = barcode_img(bc_data)
    img.paste(bc_img, ((W-bc_img.width)//2, y))
    y+=bc_img.height+6
    draw.text((W//2,y),bc_data,fill=LIGHT,font=font(9),anchor='mt');y+=16
    draw.text((W//2,y),tx_label,fill=LIGHT,font=font(9),anchor='mt');y+=28
    
    # Footer
    draw.line([(0,y),(W,y)],fill=(235,235,235))
    draw.rectangle([(0,y+1),(W,y+15+len(footer_lines)*14)],fill=(248,248,244));y+=12
    for i, line in enumerate(footer_lines):
        draw.text((W//2,y),line,fill=MID,font=font(11 if i==0 else 8,i==0),anchor='mt');y+=14
    
    img = img.crop((0,0,W,y+10))
    photoify(img, out_name)

# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

def gen_grocery(out="receipt_grocery.jpg"):
    make_receipt(out, (26,71,42), 'FRESH MARKET', 'ORGANIC & NATURAL FOODS',
        '2847 Oak Street, Portland, OR 97214', '(503) 555-0142',
        'GROCERY RECEIPT', '06/15/2026  2:37 PM',
        [('Date:','06/15/2026  2:37 PM'),('Register:','#REG-07'),('Cashier:','Maria G.'),
         ('Transaction:','#TXN-1268493')],
        [('Organic Bananas','@ $1.29/lb  2.18 lb','$2.81'),('Whole Wheat Artisan Bread','24oz','$5.49'),
         ('Organic Baby Spinach','5 oz','$4.99'),('Free-Range Eggs (Large)','Dozen  Organic Valley','$7.49'),
         ('Avocado (Hass, Large)','2 @ $2.99','$5.98'),('Almond Milk (Unsweetened)','Califia Farms  48 oz','$4.29'),
         ('Chicken Breast (Boneless)','1.54 lb @ $7.99/lb','$12.30'),('Greek Yogurt (Plain)','Fage  32 oz','$6.79'),
         ('Extra Virgin Olive Oil','California Ranch  16.9 oz','$11.99'),('Cherry Tomatoes (Organic)','1 pint','$3.99')],
        [('Subtotal','$66.12',False),('Sales Tax (8.7%)','$5.75',False),('Bottle Deposit','$0.10',False),('TOTAL','$71.97',True)],
        ['Paid by:  VISA Debit  **** 4831','Card Type: CHIP Read  |  Auth: 08A4B2'],
        'TXN-1268493-MARKET-06-15-2026', 'Transaction #TXN-1268493',
        ['Thank you for shopping at Fresh Market!','Store #142  Portland, OR',
         'Returns: 30 days with receipt. Perishables: 7 days.','www.freshmarket.com'])

def gen_restaurant(out="receipt_restaurant.jpg"):
    make_receipt(out, (20,20,22), 'THE RUSTIC TABLE', 'FARM-TO-TABLE  |  EST. 2018',
        '1427 Belmont Street, Portland, OR 97214', '(503) 555-0289',
        'DINE-IN RECEIPT', '06/15/2026  7:42 PM',
        [('Date:','06/15/2026  7:42 PM'),('Table:','No.14  |  Server: David K.'),('Guests:','3'),('Check #:','4829')],
        [('Cast Iron Ribeye (12oz)','truffle butter, roasted garlic','$38.00'),('Pan-Seared Salmon','lemon dill sauce','$27.00'),
         ('Wild Mushroom Risotto','parmesan, truffle oil','$19.00'),('Roasted Beet Salad','goat cheese, walnuts','$14.00'),
         ('Crispy Brussels Sprouts','bacon, maple glaze','$11.00'),('Artisan Bread Basket','whipped honey butter','$7.00'),
         ('Sparkling Water (San Pellegrino)','750ml  x2','$12.00'),('House Pinot Noir','Willamette Valley  x2','$26.00'),
         ('Tiramisu','house-made mascarpone','$12.00')],
        [('Subtotal','$166.00',False),('Sales Tax (8.7%)','$14.44',False),('Gratuity (20%)','$33.20',False),('TOTAL','$213.64',True)],
        ['Paid by:  VISA Signature  **** 7291','Card Type: CHIP Read','Tip: $33.20  |  Total Charged: $213.64'],
        'TXN-4829-RUSTIC-06-15-2026', 'Check #4829',
        ['Thank you for dining with us!','The Rustic Table  Portland, OR',
         'www.therustictablepdx.com','Gratuity guidelines: 18-22% for parties of 3+'])

def gen_fuel(out="receipt_fuel.jpg"):
    make_receipt(out, (220,30,30), 'SHELL', 'QUALITY FUEL  |  CONVENIENCE STORE',
        '5812 SE Powell Blvd, Portland, OR 97206', '(503) 555-0192',
        'FUEL RECEIPT', '06/15/2026  11:18 AM',
        [('Date:','06/15/2026  11:18 AM'),('Pump:','#6  |  Attendant: Carlos R.'),('Transaction:','#SHE-5829104')],
        [('Shell V-Power NiTRO+ Premium (93)','14.287 gal @ $4.899/gal','$69.99'),('Fuel Surcharge','Oregon Clean Fuels Program','$0.28'),
         ('','',''),('Red Bull Energy Drink (12oz)','2 @ $3.49','$6.98'),('Dasani Water (20oz)','1 @ $2.29','$2.29'),
         ('Trail Mix (Large Bag)','1 @ $4.99','$4.99'),('Gum (5 Gum, Spearmint)','1 @ $2.19','$2.19')],
        [('Fuel Subtotal','$70.27',False),('Store Items','$16.45',False),('Sales Tax (8.7%)','$1.43',False),('TOTAL','$88.15',True)],
        ['Paid by:  Mastercard Debit  **** 9527','Card Type: TAP  |  Auth: 7C3E91'],
        'SHE-5829104-FUEL-06-15-2026', 'Transaction #SHE-5829104',
        ['Thank you for choosing Shell!','Station #2841  Portland, OR','www.shell.us'])

def gen_retail(out="receipt_retail.jpg"):
    make_receipt(out, (20,20,22), 'NORDSTROM RACK', 'QUALITY BRANDS AT GREAT PRICES',
        '938 NW Everett Street, Portland, OR 97209', '(503) 555-0294',
        'SALES RECEIPT', '06/15/2026  3:24 PM',
        [('Date:','06/15/2026  3:24 PM'),('Register:','#REG-12'),('Transaction:','#NRK-7394158')],
        [('Nike Air Max 90 (Men, Sz 10.5)','Style #CD0881-101  White/Black','$89.97'),
         ('Levi 511 Slim Fit Jeans','32x32  Dark Indigo Wash','$44.97'),
         ('Calvin Klein Cotton T-Shirt (3-Pack)','Size L  Black/White/Grey','$34.97'),
         ('Patagonia Better Sweater Fleece','Size M  Navy Blue','$79.97'),
         ('Cole Haan Leather Belt','Size 34  Brown','$29.97'),
         ('Bombas Ankle Socks (6-Pack)','Size 10-13  Assorted','$19.97')],
        [('Subtotal','$299.82',False),('Sales Tax (8.7%)','$26.09',False),('TOTAL','$325.91',True)],
        ['Paid by:  Amex  **** 8003','Card Type: CHIP Read  |  Auth: 4D92F7','Returns: 45 days with tag & receipt'],
        'NRK-7394158-RACK-06-15-2026', 'Transaction #NRK-7394158',
        ['Thank you for shopping at Nordstrom Rack!','Store #184  Portland, OR',
         'www.nordstromrack.com','Price match guarantee within 14 days'])

def gen_pharmacy(out="receipt_pharmacy.jpg"):
    make_receipt(out, (204,0,0), 'CVS pharmacy', 'HEALTH  |  WELLNESS  |  BEAUTY',
        '1632 NE Sandy Blvd, Portland, OR 97232', '(503) 555-0167',
        'PHARMACY RECEIPT', '06/15/2026  5:08 PM',
        [('Date:','06/15/2026  5:08 PM'),('Register:','#REG-04'),('Rx #:','6754921  |  Dr. Chen'),('Transaction:','#CVS-9148037')],
        [('Prescription \u2014 Lisinopril 10mg','30 tablets  Qty: 30  Refills: 2','$12.00'),
         ('Tylenol Extra Strength (100ct)','Acetaminophen 500mg','$11.49'),('CVS Health Vitamin D3 (200ct)','2000 IU','$9.99'),
         ('Band-Aid Flexible Fabric (40ct)','Assorted Sizes','$5.79'),('Colgate Total Whitening','6.0 oz  Clean Mint','$4.99'),
         ('Dove Sensitive Skin Body Wash','22 oz pump','$8.99'),('Cetaphil Moisturizing Cream','16 oz jar','$14.99'),
         ('CVS Health Allergy Relief (30ct)','Cetirizine HCl 10mg','$15.49')],
        [('Subtotal','$83.73',False),('Pharmacy Copay','$12.00',False),('Sales Tax (8.7%)','$5.36',False),
         ('ExtraCare Savings','-$3.00',False),('TOTAL','$98.09',True)],
        ['Paid by:  FSA Debit Card  **** 6152','Card Type: CHIP Read  |  Auth: B8F3D2'],
        'CVS-9148037-RX-06-15-2026', 'Transaction #CVS-9148037',
        ['Thank you for choosing CVS Pharmacy!','Store #08742  Portland, OR',
         'Returns: 60 days unopened. Rx cannot be returned.','www.cvs.com'])

def gen_hardware(out="receipt_hardware.jpg"):
    make_receipt(out, (243,112,33), 'THE HOME DEPOT', 'MORE SAVING. MORE DOING.',
        '3030 NE Weidler St, Portland, OR 97232', '(503) 555-0184',
        'SALES RECEIPT', '06/15/2026  10:42 AM',
        [('Date:','06/15/2026  10:42 AM'),('Register:','#REG-16'),('Cashier:','Mike T.'),('Transaction:','#THD-5028194')],
        [('DeWalt 20V MAX Cordless Drill Kit','2 batteries + charger','$149.00'),
         ('2x4 Kiln-Dried Whitewood Stud','8 ft  Qty: 12','$47.88'),
         ('Behr Premium Plus Paint (1 Gal)','Ultra Pure White  Eggshell','$42.98'),
         ('Paint Roller Kit (9-inch)','Tray, 3 rollers, extension pole','$19.97'),
         ('Gardner Bender Electrical Tape','4-pack  Black','$5.98'),
         ('Workforce Nitrile Gloves (10pk)','Size L  Diamond grip','$9.97')],
        [('Subtotal','$275.78',False),('Sales Tax (8.7%)','$23.99',False),('TOTAL','$299.77',True)],
        ['Paid by:  VISA Credit  **** 3147','Card Type: CHIP Read  |  Auth: 2E7C91'],
        'THD-5028194-HOME-06-15-2026', 'Transaction #THD-5028194',
        ['Thank you for shopping at The Home Depot!','Store #4702  Portland, OR',
         'Returns: 90 days with receipt.','www.homedepot.com'])

def gen_electronics(out="receipt_electronics.jpg"):
    make_receipt(out, (0,70,140), 'BEST BUY', 'EXPERT SERVICE. UNBEATABLE PRICE.',
        '2055 N Tomahawk Island Dr, Portland, OR 97217', '(503) 555-0237',
        'SALES RECEIPT', '06/15/2026  1:15 PM',
        [('Date:','06/15/2026  1:15 PM'),('Register:','#REG-09'),('Associate:','Trevor H.'),('Transaction:','#BBY-3187205')],
        [('Sony WH-1000XM6 Headphones','Wireless NC  Black','$349.99'),
         ('Apple USB-C to Lightning Cable (2m)','MFi Certified','$29.99'),
         ('SanDisk 2TB Extreme Portable SSD','USB-C  1050MB/s','$159.99'),
         ('Logitech MX Master 4 Mouse','Wireless  Graphite','$99.99')],
        [('Subtotal','$639.96',False),('Sales Tax (8.7%)','$55.68',False),('TOTAL','$695.64',True)],
        ['Paid by:  Mastercard  **** 8803','Card Type: TAP  |  Auth: 5F3A82','My Best Buy Member: **** 4291'],
        'BBY-3187205-TECH-06-15-2026', 'Transaction #BBY-3187205',
        ['Thank you for shopping at Best Buy!','Store #874  Portland, OR',
         'Returns: 15 days (30 for My Best Buy Plus).','www.bestbuy.com'])

def gen_pet(out="receipt_pet.jpg"):
    make_receipt(out, (0,120,180), 'PetSmart', 'WHERE PETS ARE FAMILY',
        '9380 NW West Union Rd, Portland, OR 97229', '(503) 555-0147',
        'SALES RECEIPT', '06/15/2026  11:30 AM',
        [('Date:','06/15/2026  11:30 AM'),('Register:','#REG-05'),('Cashier:','Lisa M.'),('Transaction:','#PET-6284103')],
        [('Hill Science Diet Adult Dog Food','Large Breed  30 lb','$64.99'),
         ('Greenies Dental Treats (Large)','24 ct  Fresh Flavor','$34.99'),
         ('Kong Classic Dog Toy (Large)','Red  Stuffable','$16.99'),
         ('Arm & Hammer Dog Poop Bags','120 ct  Lavender','$8.99'),
         ('Top Paw Dog Shampoo (16oz)','Oatmeal & Aloe','$12.99')],
        [('Subtotal','$138.95',False),('Sales Tax (8.7%)','$12.09',False),('TOTAL','$151.04',True)],
        ['Paid by:  VISA Debit  **** 6619','Card Type: CHIP Read  |  Auth: 9D1F45','PetPerks: **** 7052  139 pts earned'],
        'PET-6284103-PET-06-15-2026', 'Transaction #PET-6284103',
        ['Thank you for shopping at PetSmart!','Store #2187  Portland, OR',
         'Returns: 60 days. Food: unopened only.','www.petsmart.com'])

# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATES = {
    'grocery':     ('Fresh Market ($71.97)', gen_grocery),
    'restaurant':  ('The Rustic Table ($213.64)', gen_restaurant),
    'fuel':        ('Shell ($88.15)', gen_fuel),
    'retail':      ('Nordstrom Rack ($325.91)', gen_retail),
    'pharmacy':    ('CVS Pharmacy ($98.09)', gen_pharmacy),
    'hardware':    ('Home Depot ($299.77)', gen_hardware),
    'electronics': ('Best Buy ($695.64)', gen_electronics),
    'pet':         ('PetSmart ($151.04)', gen_pet),
}

def main():
    p = argparse.ArgumentParser(description='Bill Generator v3 — Photo-Realistic Receipts')
    p.add_argument('-t','--type',choices=list(TEMPLATES)+['all'],default='all')
    p.add_argument('-o','--out',help='Output dir (default: current)')
    p.add_argument('--list','-l',action='store_true')
    args = p.parse_args()
    
    if args.list:
        print('Templates:')
        for k,(d,_) in TEMPLATES.items():
            print(f'  {k:14s} {d}')
        print('\nCredit: Created by Vexa Nightshade & Bores')
        return
    
    out_dir = args.out or '.'
    os.makedirs(out_dir, exist_ok=True)
    
    if args.type == 'all':
        for name, (desc, gen) in TEMPLATES.items():
            path = os.path.join(out_dir, f'receipt_{name}.jpg')
            gen(path)
            sz = os.path.getsize(path)//1024
            print(f'  [{name:14s}] {sz:4d}KB  {desc}')
        print(f'\nDone! {len(TEMPLATES)} receipts generated.')
        print('Credit: Created by Vexa Nightshade & Bores | github.com/BREACH')
    else:
        desc, gen = TEMPLATES[args.type]
        path = args.out if args.out else f'receipt_{args.type}.jpg'
        gen(path)
        print(f'  [{args.type}] {os.path.getsize(path)//1024}KB  {desc}')
        print('Credit: Created by Vexa Nightshade & Bores')

if __name__ == '__main__':
    main()

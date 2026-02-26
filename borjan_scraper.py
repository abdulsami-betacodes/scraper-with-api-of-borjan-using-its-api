"""
Borjan.com.pk — Full Async Product Scraper
==========================================
Uses Shopify's built-in /products.json API
Scrapes ALL products concurrently — blazing fast
Output: borjan_products.json
"""

import re
import json
import asyncio
import aiohttp
from datetime import datetime


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
BASE_URL      = "https://www.borjan.com.pk"
API_ENDPOINT  = f"{BASE_URL}/products.json"
LIMIT         = 250          # Max Shopify allows per page
MAX_WORKERS   = 10          # Concurrent page fetches
#OUTPUT_FILE   = "borjan_products.csv"
OUTPUT_FILE   = "borjan_products.json"
HEADERS = {
    "User-Agent"      : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept"          : "application/json, text/plain, */*",
    "Accept-Language" : "en-US,en;q=0.9",
    "Referer"         : BASE_URL,
}


# ─────────────────────────────────────────────
# HELPER — GENDER DETECTION
# ─────────────────────────────────────────────
def get_gender(product_type: str, tags: list) -> str:
    text = (product_type + " " + " ".join(tags)).lower()
    if any(w in text for w in ["women", "girl", "ladies", "female", "her"]):
        return "Women"
    if any(w in text for w in ["men", "boy", "male", "his", "gents"]):
        return "Men"
    if any(w in text for w in ["kid", "child", "junior", "youth", "unisex"]):
        return "Kids"
    return "Unisex"


# ─────────────────────────────────────────────
# HELPER — CATEGORY DETECTION
# ─────────────────────────────────────────────
CATEGORY_MAP = {
    "sandal"    : "Sandals",
    "slipper"   : "Slippers",
    "chappal"   : "Chappals",
    "heel"      : "Heels",
    "pump"      : "Pumps",
    "boot"      : "Boots",
    "sneaker"   : "Sneakers",
    "sport"     : "Sports",
    "loafer"    : "Loafers",
    "moccasin"  : "Moccasins",
    "peshawari" : "Peshawari",
    "khussa"    : "Khussa",
    "flat"      : "Flats",
    "wedge"     : "Wedges",
    "oxford"    : "Oxfords",
    "casual"    : "Casual",
    "formal"    : "Formal",
    "flip"      : "Flip Flops",
}

def get_category(product_type: str) -> str:
    pt = product_type.lower()
    for key, label in CATEGORY_MAP.items():
        if key in pt:
            return label
    return "Other"


# ─────────────────────────────────────────────
# HELPER — CLEAN HTML DESCRIPTION
# ─────────────────────────────────────────────
def clean_html(raw: str) -> str:
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)       # strip HTML tags
    text = re.sub(r"\s+", " ", text).strip()   # collapse whitespace
    return text


# ─────────────────────────────────────────────
# HELPER — PRICE CALCULATIONS
# ─────────────────────────────────────────────
def get_prices(variants: list):
    prices       = []
    compare_prices = []

    for v in variants:
        try:
            prices.append(float(v.get("price") or 0))
        except:
            pass
        try:
            cp = v.get("compare_at_price")
            if cp:
                compare_prices.append(float(cp))
        except:
            pass

    regular_price = min(compare_prices) if compare_prices else (min(prices) if prices else 0.0)
    sale_price    = min(prices) if prices else 0.0

    # If compare_at_price == price, it's not on sale
    on_sale = regular_price > sale_price if regular_price and sale_price else False

    if on_sale and regular_price:
        discount_pct = round(((regular_price - sale_price) / regular_price) * 100, 2)
    else:
        discount_pct  = 0.0
        regular_price = sale_price   # no sale, both same

    return regular_price, sale_price, on_sale, discount_pct


# ─────────────────────────────────────────────
# HELPER — SIZES & STOCK PER SIZE
# ─────────────────────────────────────────────
def get_sizes_and_stock(variants: list):
    sizes         = []
    stock_per_size = {}

    for v in variants:
        size = (v.get("option2") or v.get("option1") or "").strip()
        if size and size not in sizes:
            sizes.append(size)
        available = v.get("available", False)
        stock_per_size[size] = "In Stock" if available else "Out of Stock"

    # Overall stock status
    if any(v == "In Stock" for v in stock_per_size.values()):
        stock_status = "In Stock"
    elif sizes:
        stock_status = "Out of Stock"
    else:
        stock_status = "Unknown"

    return sizes, stock_per_size, stock_status


# ─────────────────────────────────────────────
# HELPER — IMAGES
# ─────────────────────────────────────────────
def get_images(product: dict) -> list:
    imgs = []
    for img in product.get("images", []):
        src = img.get("src", "")
        if src:
            imgs.append(src)
    return imgs


# ─────────────────────────────────────────────
# CORE — PARSE ONE PRODUCT
# ─────────────────────────────────────────────
def parse_product(p: dict) -> dict:
    handle   = (p.get("handle") or "").strip()
    ptype    = (p.get("product_type") or "").strip()
    tags     = p.get("tags") or []
    variants = p.get("variants") or []

    first_variant        = variants[0] if variants else {}
    original_url         = f"{BASE_URL}/products/{handle}"
    description          = clean_html(p.get("body_html") or "")
    regular_price, sale_price, on_sale, discount_pct = get_prices(variants)
    sizes, stock_per_size, stock_status              = get_sizes_and_stock(variants)
    imgs                 = get_images(p)

    return {
        "product_name"  : (p.get("title")                  or "").strip(),
        "url"           : original_url,
        "handle"        : handle,
        "product_id"    : str(p.get("id")                   or ""),
        "gender"        : get_gender(ptype, tags),
        "category"      : get_category(ptype),
        "product_type"  : ptype,
        "description"   : description,
        "color"         : (first_variant.get("option1")     or "").strip(),
        "all_sizes"     : sizes,
        "tags"          : tags,
        "regular_price" : regular_price,
        "sale_price"    : sale_price,
        "currency"      : "PKR",
        "discount_pct"  : discount_pct,
        "is_on_sale"    : on_sale,
        "stock_per_size": stock_per_size,
        "stock_status"  : stock_status,
        "primary_image" : imgs[0] if imgs else "",
        "all_images"    : imgs,
        "rating"        : None,
        "review_count"  : 0,
        "sku"           : (first_variant.get("sku")         or "").strip(),
        "barcode"       : (first_variant.get("barcode")     or "").strip(),
        "vendor"        : (p.get("vendor")                  or "").strip(),
        "created_at"    : (p.get("created_at")              or ""),
        "updated_at"    : (p.get("updated_at")              or ""),
        "scraped_at"    : datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────
# ASYNC — FETCH ONE PAGE
# ─────────────────────────────────────────────
async def fetch_page(session: aiohttp.ClientSession, page: int, semaphore: asyncio.Semaphore) -> list:
    url    = f"{API_ENDPOINT}?limit={LIMIT}&page={page}"
    async with semaphore:
        try:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    print(f"  [!] Page {page} returned status {resp.status}")
                    return []
                data = await resp.json()
                products = data.get("products", [])
                print(f"  [✓] Page {page} — {len(products)} products fetched")
                return products
        except Exception as e:
            print(f"  [✗] Page {page} failed: {e}")
            return []


# ─────────────────────────────────────────────
# ASYNC — SMART PAGE DISCOVERY + FETCH
# ─────────────────────────────────────────────
async def fetch_all_products(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> list:
    """
    Strategy:
    1. Fetch pages in batches of MAX_WORKERS concurrently
    2. If any page in the batch returns 0 products — we've hit the end
    3. Collect everything until exhausted
    """
    all_raw   = []
    page      = 1
    batch_size = MAX_WORKERS

    while True:
        # Build a batch of page numbers
        batch_pages = list(range(page, page + batch_size))
        print(f"  [→] Fetching pages {batch_pages[0]} to {batch_pages[-1]}...")

        tasks   = [fetch_page(session, p, semaphore) for p in batch_pages]
        results = await asyncio.gather(*tasks)

        done = False
        for page_products in results:
            if not page_products:
                done = True  # hit an empty page — we're at the end
                break
            all_raw.extend(page_products)

        if done:
            break

        page += batch_size

    return all_raw


# ─────────────────────────────────────────────
# MAIN — ORCHESTRATE EVERYTHING
# ─────────────────────────────────────────────
async def main():
    print("=" * 50)
    print("  Borjan.com.pk — Full Store Async Scraper")
    print("  Scraping EVERY product — no filters")
    print("=" * 50)

    semaphore = asyncio.Semaphore(MAX_WORKERS)

    async with aiohttp.ClientSession() as session:

        # Step 1 — fetch ALL products across all pages
        print("\n[1] Fetching all products (batched concurrent)...\n")
        raw_products = await fetch_all_products(session, semaphore)

        # Step 2 — parse every product
        print(f"\n[2] Parsing {len(raw_products)} raw products...")
        all_products = []
        seen_ids     = set()   # deduplicate just in case

        for p in raw_products:
            pid = str(p.get("id", ""))
            if pid in seen_ids:
                continue
            seen_ids.add(pid)
            all_products.append(parse_product(p))

    # Step 3 — save to JSON
    print(f"\n[3] Saving {len(all_products)} products to '{OUTPUT_FILE}'...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done! {len(all_products)} unique products saved to '{OUTPUT_FILE}'")
    print("=" * 50)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(main())

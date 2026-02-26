"""
Borjan.com.pk — FastAPI
=======================
Endpoints:
  POST /scrape     → scrapes and saves to borjan_products.json, returns summary
  GET  /products   → returns saved data with optional pagination

Run:
  pip install fastapi uvicorn aiohttp
  python -m uvicorn api:app --reload
"""

import json
import os
import asyncio
import aiohttp
from fastapi import FastAPI, Query
from borjan_scraper import fetch_all_products, parse_product, OUTPUT_FILE


app = FastAPI(title="Borjan Scraper API", version="1.0.0")


# ─────────────────────────────────────────────
# POST /scrape — scrape, save to file, return summary only
# ─────────────────────────────────────────────
@app.post("/scrape")
async def scrape():

    print("⏳ Scraping started...")       
    semaphore = asyncio.Semaphore(10)
    async with aiohttp.ClientSession() as session:
        raw = await fetch_all_products(session, semaphore)

    products = []
    seen     = set()
    for p in raw:
        pid = str(p.get("id", ""))
        if pid not in seen:
            seen.add(pid)
            products.append(parse_product(p))

    # save to file — don't send all data to browser
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"✅ Done! {len(products)} products saved.")

    # return just a small summary — fast and clean
    return {
        "message" : "✅ Scrape complete!",
        "total"   : len(products),
        "saved_to": OUTPUT_FILE
    }


# ─────────────────────────────────────────────
# GET /products — read from file, paginate
# ─────────────────────────────────────────────
@app.get("/products")
def get_products(
    page  : int = Query(1,   description="Page number"),
    limit : int = Query(20,  description="Products per page"),
):
    if not os.path.exists(OUTPUT_FILE):
        return {"message": "No data yet. Run POST /scrape first."}

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        all_products = json.load(f)

    # pagination math
    start    = (page - 1) * limit
    end      = start + limit
    chunk    = all_products[start:end]

    return {
        "total"      : len(all_products),
        "page"       : page,
        "limit"      : limit,
        "total_pages": -(-len(all_products) // limit),  # ceiling division
        "products"   : chunk
    }
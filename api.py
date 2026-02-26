"""
Borjan.com.pk — FastAPI
=======================
Endpoints:
  GET  /products              → all products (from saved file)
  GET  /products/{id}         → single product by ID
  GET  /products?category=X   → filter by category
  GET  /products?gender=X     → filter by gender
  POST /scrape                → re-run scraper, refresh saved data

Run:
  pip install fastapi uvicorn aiohttp
  uvicorn api:app --reload
"""

import json
import os
import asyncio
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse

# ── import the scraper functions we already wrote ──
from borjan_scraper import fetch_all_products, parse_product, OUTPUT_FILE
import aiohttp


app = FastAPI(
    title       = "Borjan Scraper API",
    description = "Scrape & serve Borjan.com.pk product data",
    version     = "1.0.0"
)

# tracks if a scrape is currently running so we don't run two at once
scrape_status = {"running": False, "last_scraped": None, "total": 0}


# ─────────────────────────────────────────────
# UTILITY — load products from saved JSON file
# ─────────────────────────────────────────────
def load_products() -> list:
    if not os.path.exists(OUTPUT_FILE):
        return []
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────
# UTILITY — run the scraper and save to file
# ─────────────────────────────────────────────
async def run_scraper():
    scrape_status["running"] = True
    try:
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

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        scrape_status["last_scraped"] = datetime.now().isoformat()
        scrape_status["total"]        = len(products)

    finally:
        scrape_status["running"] = False


# ─────────────────────────────────────────────
# ROOT — health check
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message"      : "Borjan Scraper API is running",
        "last_scraped" : scrape_status["last_scraped"],
        "total_products": scrape_status["total"],
        "docs"         : "/docs"
    }


# ─────────────────────────────────────────────
# GET /products — all products with optional filters
# ─────────────────────────────────────────────
@app.get("/products")
def get_products(
    category : str = Query(None, description="Filter by category e.g. Heels, Sandals"),
    gender   : str = Query(None, description="Filter by gender e.g. Men, Women, Kids"),
    in_stock : bool = Query(None, description="True = only in stock products"),
):
    products = load_products()

    if not products:
        raise HTTPException(status_code=404, detail="No data found. Run POST /scrape first.")

    # apply filters if provided
    if category:
        products = [p for p in products if p.get("category", "").lower() == category.lower()]

    if gender:
        products = [p for p in products if p.get("gender", "").lower() == gender.lower()]

    if in_stock is not None:
        status   = "In Stock" if in_stock else "Out of Stock"
        products = [p for p in products if p.get("stock_status") == status]

    return {
        "total"    : len(products),
        "products" : products
    }


# ─────────────────────────────────────────────
# GET /products/{id} — single product by ID
# ─────────────────────────────────────────────
@app.get("/products/{product_id}")
def get_product(product_id: str):
    products = load_products()
    match    = next((p for p in products if p.get("product_id") == product_id), None)

    if not match:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")

    return match


# ─────────────────────────────────────────────
# POST /scrape — trigger a fresh scrape
# ─────────────────────────────────────────────
@app.post("/scrape")
async def scrape(background_tasks: BackgroundTasks):
    if scrape_status["running"]:
        return JSONResponse(
            status_code = 409,
            content     = {"message": "Scrape already running. Please wait."}
        )

    # run scraper in background so API stays responsive
    background_tasks.add_task(run_scraper)

    return {
        "message" : "Scrape started in background.",
        "tip"     : "Check GET /scrape/status to see when it's done."
    }


# ─────────────────────────────────────────────
# GET /scrape/status — check if scrape is done
# ─────────────────────────────────────────────
@app.get("/scrape/status")
def scrape_status_check():
    return {
        "running"       : scrape_status["running"],
        "last_scraped"  : scrape_status["last_scraped"],
        "total_products": scrape_status["total"]
    }
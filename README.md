# Borjan Scraper API

A high-performance async web scraper for Borjan.com.pk (Pakistani shoe store) with a FastAPI backend for accessing scraped product data.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.133+-green.svg)
![aiohttp](https://img.shields.io/badge/aiohttp-3.13+-orange.svg)

## 📋 Overview

This project scrapes product data from Borjan.com.pk, a popular Pakistani footwear retailer using Shopify. It uses asynchronous programming to efficiently fetch thousands of products concurrently and provides a REST API for accessing the scraped data with pagination support.

## ✨ Features

- **Async Concurrent Scraping**: Fetches up to 10 pages simultaneously for blazing fast performance
- **Smart Pagination Discovery**: Automatically detects the total number of products and handles pagination
- **Rich Product Parsing**:
  - Gender detection (Men/Women/Kids/Unisex)
  - Category mapping (Sandals, Slippers, Boots, Sneakers, etc.)
  - Price calculations with discount detection
  - Size and stock status per variant
  - Image URLs extraction
- **REST API Endpoints**:
  - `POST /scrape` - Run the scraper and save to JSON
  - `GET /products` - Access products with pagination
- **JSON Output**: Clean structured data output

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   cd borjan
   ```

2. **Create and activate virtual environment** (optional but recommended)
   ```bash
   python -m venv myvenv
   source myvenv/bin/activate  # On macOS/Linux
   # On Windows: myvenv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage

### Running the API Server

```bash
python -m uvicorn api:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

FastAPI provides interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Running the Scraper Standalone

You can also run the scraper directly without the API:

```bash
python borjan_scraper.py
```

## 📡 API Endpoints

### POST /scrape

Triggers the scraper to fetch all products from Borjan.com.pk and saves them to `borjan_products.json`.

**Response:**
```json
{
  "message": "✅ Scrape complete!",
  "total": 1234,
  "saved_to": "borjan_products.json"
}
```

### GET /products

Retrieves paginated product data from the saved JSON file.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| limit | int | 20 | Products per page |

**Response:**
```json
{
  "total": 1234,
  "page": 1,
  "limit": 20,
  "total_pages": 62,
  "products": [
    {
      "product_name": "Formal Leather Shoes",
      "url": "https://www.borjan.com.pk/products/formal-leather-shoes",
      "handle": "formal-leather-shoes",
      "product_id": "123456789",
      "gender": "Men",
      "category": "Formal",
      "product_type": "Formal Shoes",
      "description": "...",
      "color": "Black",
      "all_sizes": ["7", "8", "9", "10", "11"],
      "regular_price": 8500.0,
      "sale_price": 6500.0,
      "currency": "PKR",
      "discount_pct": 23.53,
      "is_on_sale": true,
      "stock_per_size": {...},
      "stock_status": "In Stock",
      "primary_image": "https://...",
      "all_images": [...],
      "sku": "...",
      "vendor": "Borjan"
    }
  ]
}
```

## 📂 Project Structure

```
borjan/
├── api.py                 # FastAPI application
├── borjan_scraper.py      # Async web scraper
├── borjan_products.json   # Scraped data output (generated)
├── borjan_products.csv    # CSV output (optional)
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── myvenv/                # Virtual environment
```

## 📦 Output Data Format

Each product contains the following fields:

| Field | Type | Description |
|-------|------|-------------|
| product_name | string | Product title |
| url | string | Product page URL |
| handle | string | Shopify handle |
| product_id | string | Unique product ID |
| gender | string | Men/Women/Kids/Unisex |
| category | string | Mapped category |
| product_type | string | Original product type |
| description | string | Clean HTML-free description |
| color | string | Primary color |
| all_sizes | array | Available sizes |
| regular_price | float | Original price (PKR) |
| sale_price | float | Sale price (PKR) |
| discount_pct | float | Discount percentage |
| is_on_sale | boolean | Sale status |
| stock_per_size | object | Stock status per size |
| stock_status | string | Overall stock status |
| primary_image | string | Main product image URL |
| all_images | array | All product images |
| sku | string | Stock keeping unit |
| vendor | string | Product vendor |
| scraped_at | string | ISO timestamp |

## 🧰 Technologies Used

- **Python 3.11+** - Programming language
- **FastAPI** - Modern web framework
- **aiohttp** - Async HTTP client
- **asyncio** - Asynchronous programming
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

## ⚡ Performance

- Concurrent fetching of up to 10 pages simultaneously
- Smart pagination detection
- Deduplication of products
- Efficient memory usage with async generators

## 📝 License

This project is for educational purposes. Please respect Borjan.com.pk's terms of service when using this scraper.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


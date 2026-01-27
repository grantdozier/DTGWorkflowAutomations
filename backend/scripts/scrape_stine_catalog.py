"""
Scrape STINE Home + Yard Website for Complete Product Catalog

This script crawls stinehome.com to extract ALL products with:
- Product codes/SKUs
- Descriptions
- Categories
- Prices
- Units of measure

This builds a REAL material catalog from their actual inventory.
"""

import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time
import json
import re
from urllib.parse import urljoin, urlparse
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.material import Material

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StineCatalogScraper:
    """Scrape STINE Home + Yard website for products"""

    def __init__(self):
        self.base_url = "https://www.stinehome.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.visited_urls = set()
        self.products = []

    def get_category_urls(self):
        """Get all product category URLs"""
        logger.info("Fetching category URLs...")

        categories = [
            "/home-improvement/building-supplies/lumber-and-trim/",
            "/home-improvement/building-supplies/",
            "/building-materials/",
            "/building-materials/lumber/",
            "/building-materials/lumber/treated-pine/",
            "/building-materials/lumber/framing-lumber/",
            "/building-materials/plywood-osb/",
            "/home-improvement/building-supplies/roofing/",
            "/home-improvement/building-supplies/siding/",
            "/home-improvement/hardware/",
            "/home-improvement/building-supplies/insulation/",
            "/home-improvement/building-supplies/drywall/",
        ]

        return [self.base_url + cat for cat in categories]

    def scrape_page(self, url):
        """Scrape a single page for products"""
        if url in self.visited_urls:
            return []

        self.visited_urls.add(url)

        try:
            logger.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            products_found = []

            # Look for product listings (common patterns)
            # Pattern 1: Product cards/tiles
            product_cards = soup.find_all(['div', 'article'], class_=re.compile(r'product|item|tile', re.I))

            for card in product_cards:
                product = self.extract_product_from_card(card)
                if product:
                    products_found.append(product)

            # Pattern 2: Table rows
            product_rows = soup.find_all('tr', class_=re.compile(r'product|item', re.I))
            for row in product_rows:
                product = self.extract_product_from_row(row)
                if product:
                    products_found.append(product)

            # Pattern 3: List items
            product_items = soup.find_all('li', class_=re.compile(r'product|item', re.I))
            for item in product_items:
                product = self.extract_product_from_list_item(item)
                if product:
                    products_found.append(product)

            logger.info(f"  Found {len(products_found)} products")
            time.sleep(1)  # Be nice to the server

            return products_found

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return []

    def extract_product_from_card(self, card):
        """Extract product data from a product card"""
        try:
            # Look for product name/title
            title_elem = card.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|product', re.I))
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)

            # Look for SKU
            sku_elem = card.find(['span', 'div', 'p'], class_=re.compile(r'sku|code|item', re.I))
            sku = sku_elem.get_text(strip=True) if sku_elem else None

            # Look for price
            price_elem = card.find(['span', 'div', 'p'], class_=re.compile(r'price', re.I))
            price = None
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                if price_match:
                    price = float(price_match.group(1).replace(',', ''))

            # Look for unit
            unit_elem = card.find(['span', 'div'], class_=re.compile(r'unit|uom', re.I))
            unit = unit_elem.get_text(strip=True) if unit_elem else "EA"

            if title and (sku or price):
                return {
                    'title': title,
                    'sku': sku or self.generate_sku_from_title(title),
                    'price': price,
                    'unit': unit
                }

        except Exception as e:
            logger.debug(f"Error extracting from card: {e}")

        return None

    def extract_product_from_row(self, row):
        """Extract product from table row"""
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                return None

            # Assume first cell is SKU/code, second is description, third is price
            sku = cells[0].get_text(strip=True)
            title = cells[1].get_text(strip=True) if len(cells) > 1 else None
            price = None

            if len(cells) > 2:
                price_text = cells[2].get_text(strip=True)
                price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                if price_match:
                    price = float(price_match.group(1).replace(',', ''))

            if title:
                return {
                    'title': title,
                    'sku': sku,
                    'price': price,
                    'unit': 'EA'
                }

        except Exception as e:
            logger.debug(f"Error extracting from row: {e}")

        return None

    def extract_product_from_list_item(self, item):
        """Extract product from list item"""
        try:
            # Similar to card extraction
            title_elem = item.find(['a', 'span', 'div'])
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)

            # Look for price in the same element or nearby
            price_match = re.search(r'\$?([\d,]+\.?\d*)', item.get_text())
            price = float(price_match.group(1).replace(',', '')) if price_match else None

            if title:
                return {
                    'title': title,
                    'sku': self.generate_sku_from_title(title),
                    'price': price,
                    'unit': 'EA'
                }

        except Exception as e:
            logger.debug(f"Error extracting from list item: {e}")

        return None

    def generate_sku_from_title(self, title):
        """Generate a SKU from product title if none exists"""
        # Extract key identifiers: dimensions, product type
        # e.g., "2x4x8 Pine Stud" -> "2408P"

        title_upper = title.upper()

        # Try to find dimension pattern
        dim_match = re.search(r'(\d+)[X\s]*(\d+)[X\s]*(\d+)', title_upper)
        if dim_match:
            d1, d2, d3 = dim_match.groups()
            # Add first letter of material
            mat_match = re.search(r'(PINE|SPF|FIR|OAK|CEDAR|PLY|OSB)', title_upper)
            mat_code = mat_match.group(0)[0] if mat_match else ''
            return f"{d1}{d2}{d3}{mat_code}"

        # Fallback: first letters of words
        words = re.findall(r'\b\w+\b', title_upper)
        return ''.join([w[0] for w in words[:4]])

    def categorize_product(self, product):
        """Determine category from product title"""
        title_lower = product['title'].lower()

        if any(x in title_lower for x in ['stud', '2x4', '2x6', '2x8', '2x10', '2x12', 'plate', 'joist']):
            return 'Walls'
        elif any(x in title_lower for x in ['osb', 'plywood', 'sheathing']):
            return 'Sheathing'
        elif any(x in title_lower for x in ['roof', 'shingle', 'felt', 'truss']):
            return 'Roofing'
        elif any(x in title_lower for x in ['siding', 'hardi', 'vinyl']):
            return 'Siding'
        elif any(x in title_lower for x in ['insulation', 'batt', 'r-']):
            return 'Insulation'
        elif any(x in title_lower for x in ['drywall', 'gypsum', 'sheetrock']):
            return 'Drywall'
        elif any(x in title_lower for x in ['nail', 'screw', 'bolt', 'anchor', 'hanger']):
            return 'Hardware'
        elif any(x in title_lower for x in ['stake', 'rebar', 'concrete', 'form']):
            return 'Foundation'
        elif any(x in title_lower for x in ['trim', 'molding', 'base', 'casing']):
            return 'Trim'
        else:
            return 'Miscellaneous'

    def scrape_all(self):
        """Scrape all categories"""
        logger.info("="*60)
        logger.info("STINE HOME + YARD - CATALOG SCRAPER")
        logger.info("="*60)

        category_urls = self.get_category_urls()
        logger.info(f"Found {len(category_urls)} categories to scrape")

        all_products = []

        for url in category_urls:
            products = self.scrape_page(url)
            all_products.extend(products)

        # Deduplicate by SKU
        unique_products = {}
        for product in all_products:
            sku = product['sku']
            if sku not in unique_products or (product.get('price') and not unique_products[sku].get('price')):
                unique_products[sku] = product

        self.products = list(unique_products.values())

        # Categorize products
        for product in self.products:
            product['category'] = self.categorize_product(product)

        logger.info(f"\n{'='*60}")
        logger.info(f"Scraping complete!")
        logger.info(f"Total products found: {len(self.products)}")
        logger.info(f"Products with prices: {sum(1 for p in self.products if p.get('price'))}")
        logger.info(f"{'='*60}\n")

        return self.products

    def save_to_json(self, filename="stine_catalog.json"):
        """Save scraped products to JSON"""
        output_path = Path(filename)
        with open(output_path, 'w') as f:
            json.dump(self.products, f, indent=2)
        logger.info(f"Saved catalog to: {output_path}")

    def save_to_database(self, company_id):
        """Save products to database"""
        db = SessionLocal()
        try:
            # Clear existing materials
            deleted = db.query(Material).filter(Material.company_id == company_id).delete()
            logger.info(f"Cleared {deleted} existing materials")

            # Add new materials
            added = 0
            for product in self.products:
                if product.get('price'):  # Only add products with prices
                    material = Material(
                        company_id=company_id,
                        product_code=product['sku'],
                        description=product['title'],
                        category=product['category'],
                        unit=product.get('unit', 'EA'),
                        unit_price=product['price'],
                        notes=f"Scraped from stinehome.com",
                        is_active=True
                    )
                    db.add(material)
                    added += 1

            db.commit()
            logger.info(f"[OK] Saved {added} materials to database")
            return added

        except Exception as e:
            logger.error(f"[ERROR] Failed to save to database: {e}")
            db.rollback()
            return 0
        finally:
            db.close()


def main():
    """Main scraping function"""
    print("\n" + "="*60)
    print("STINE CATALOG SCRAPER")
    print("Crawling stinehome.com for products and prices...")
    print("="*60 + "\n")

    scraper = StineCatalogScraper()

    # Scrape website
    products = scraper.scrape_all()

    # Save to JSON for inspection
    scraper.save_to_json("stine_catalog.json")

    # Show sample products
    print("\nSample products found:")
    for product in products[:10]:
        price_str = f"${product['price']:.2f}" if product.get('price') else "N/A"
        print(f"  {product['sku']}: {product['title']} - {price_str} ({product['category']})")

    # Save to database
    db = SessionLocal()
    try:
        stine_user = db.query(User).filter(User.email == "stine@gmail.com").first()
        if stine_user:
            saved_count = scraper.save_to_database(stine_user.company_id)
            print(f"\n[OK] Saved {saved_count} materials to STINE's catalog")
        else:
            print("\n[ERROR] STINE user not found")
    finally:
        db.close()

    print("\n" + "="*60)
    print("Scraping complete!")
    print(f"Total products: {len(products)}")
    print(f"With prices: {sum(1 for p in products if p.get('price'))}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

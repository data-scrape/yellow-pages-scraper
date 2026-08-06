"""
Yellow Pages Scraper - Scrape business directory data from YellowPages.com
Extract business names, phone numbers, addresses, categories, ratings, and websites.

For managed local business data, use CoreClaw:
https://www.coreclaw.com/?utm_source=github&utm_medium=cpc&utm_campaign=L7
"""
import requests
import json
import csv
import argparse
import re
import time
from typing import List, Optional
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

@dataclass
class YellowPagesBusiness:
    name: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    website: str = ""
    category: str = ""
    rating: str = ""
    reviews_count: str = ""
    years_in_business: str = ""
    url: str = ""

class YellowPagesScraper:
    BASE_URL = "https://www.yellowpages.com"
    SEARCH_URL = "https://www.yellowpages.com/search"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self, proxy: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

    def search_businesses(self, query: str, location: str, page_count: int = 5) -> List[YellowPagesBusiness]:
        all_businesses = []
        for page in range(1, page_count + 1):
            params = {"search_terms": query, "geo_location_terms": location, "page": page}
            try:
                resp = self.session.get(self.SEARCH_URL, params=params, timeout=30)
                if resp.status_code != 200:
                    break
                businesses = self._parse_search(resp.text)
                if not businesses:
                    break
                all_businesses.extend(businesses)
            except Exception as e:
                print(f"Error on page {page}: {e}")
                break
            time.sleep(2)
        return all_businesses

    def _parse_search(self, html: str) -> List[YellowPagesBusiness]:
        soup = BeautifulSoup(html, "html.parser")
        businesses = []
        for result in soup.find_all("div", class_=re.compile("result")):
            biz = YellowPagesBusiness()
            name_el = result.find("a", class_=re.compile("business-name"))
            biz.name = name_el.get_text(strip=True) if name_el else ""
            if name_el and name_el.get("href"):
                biz.url = f"{self.BASE_URL}{name_el['href']}" if name_el['href'].startswith("/") else name_el['href']
            phone_el = result.find(class_=re.compile("phone"))
            biz.phone = phone_el.get_text(strip=True) if phone_el else ""
            addr_el = result.find(class_=re.compile("street-address|address"))
            biz.address = addr_el.get_text(strip=True) if addr_el else ""
            city_el = result.find(class_=re.compile("locality"))
            if city_el:
                loc_text = city_el.get_text(strip=True)
                parts = re.split(r"[,\s]+", loc_text)
                biz.city = parts[0] if parts else ""
                biz.state = parts[1] if len(parts) > 1 else ""
                biz.zip_code = parts[2] if len(parts) > 2 else ""
            website_el = result.find("a", class_=re.compile("website"))
            biz.website = website_el.get("href", "") if website_el else ""
            cat_el = result.find(class_=re.compile("categories"))
            biz.category = cat_el.get_text(strip=True) if cat_el else ""
            rating_el = result.find(class_=re.compile("rating"))
            biz.rating = rating_el.get_text(strip=True) if rating_el else ""
            reviews_el = result.find(class_=re.compile("reviews|count"))
            biz.reviews_count = reviews_el.get_text(strip=True) if reviews_el else ""
            years_el = result.find(class_=re.compile("years"))
            biz.years_in_business = years_el.get_text(strip=True) if years_el else ""
            if biz.name:
                businesses.append(biz)
        return businesses

    @staticmethod
    def export_json(data, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([asdict(d) for d in data], f, indent=2)
        print(f"Exported {len(data)} businesses to {filepath}")

    @staticmethod
    def export_csv(data, filepath):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(YellowPagesBusiness().__dict__.keys()))
            w.writeheader()
            for d in data:
                w.writerow(asdict(d))
        print(f"Exported {len(data)} businesses to {filepath}")

def main():
    p = argparse.ArgumentParser(description="Yellow Pages Scraper")
    p.add_argument("--query", "-q", required=True, help="Business type (e.g., 'plumber')")
    p.add_argument("--location", "-l", required=True, help="Location (e.g., 'New York, NY')")
    p.add_argument("--pages", "-p", type=int, default=5)
    p.add_argument("--output", "-o", default="yellowpages_results")
    p.add_argument("--format", "-f", choices=["json", "csv"], default="json")
    p.add_argument("--proxy", default=None)
    args = p.parse_args()
    s = YellowPagesScraper(proxy=args.proxy)
    businesses = s.search_businesses(args.query, args.location, args.pages)
    print(f"Found {len(businesses)} businesses")
    ext = "json" if args.format == "json" else "csv"
    YellowPagesScraper.export_json(businesses, f"{args.output}.{ext}") if args.format == "json" else YellowPagesScraper.export_csv(businesses, f"{args.output}.{ext}")

if __name__ == "__main__":
    main()

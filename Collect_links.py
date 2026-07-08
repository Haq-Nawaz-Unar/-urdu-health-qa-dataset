"""
collect_links.py
------------------
Kisi bhi health "listing/category" page (jese express.pk/health/ ya
urdupoint.com/health/) se automatically andar ke individual article links
nikal ke links.json mein save karta hai. Agar listing page mein "next
page" / pagination hoti hai, wo bhi follow karta hai (agar pattern match ho).

Kaise use karein:
1. pip install requests beautifulsoup4 --break-system-packages
2. Neeche LISTING_PAGES mein listing/category page URLs dalein
3. python collect_links.py
4. Output: links.json (list of article URLs) - isse copy karke
   scrape.py ki URLS list mein daal dein
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# -------------------------------------------------------------
# STEP 1: Yahan listing/category page URLs dalein
# (jahan health articles ki headlines/links list hoti hain)
# -------------------------------------------------------------
LISTING_PAGES = [
    "https://www.express.pk/health/",
    "https://www.urdupoint.com/health/",
]

# Kitne pagination pages tak jaana hai (agar site support kare)
# e.g. https://www.express.pk/health/2, /health/3 ...
MAX_PAGES_PER_SITE = 5

# Link mein ye keyword hona chahiye taake pakka article ho, listing/menu na ho
# (site ke hisaab se adjust kar sakte hain, e.g. "/health/" ya article ID pattern)
MUST_CONTAIN = ["health", "sehat", "bemari", "ilaj", "article"]


def is_probably_article(url: str, base_domain: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc and base_domain not in parsed.netloc:
        return False
    path = parsed.path.lower()
    # Category/menu pages usually chhoti path rakhte hain ya trailing slash
    if path.endswith("/") or len(path) < 15:
        return False
    return any(k in url.lower() for k in MUST_CONTAIN) or path.count("-") >= 2


def collect_from_page(url: str, base_domain: str) -> set:
    found = set()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[SKIP] {url} -> {e}")
        return found

    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.find_all("a", href=True):
        full_url = urljoin(url, a["href"])
        if is_probably_article(full_url, base_domain):
            found.add(full_url.split("#")[0])

    return found


def main():
    if not LISTING_PAGES:
        print("LISTING_PAGES khali hai! Pehle listing page URLs dalein.")
        return

    all_links = set()

    for listing_url in LISTING_PAGES:
        base_domain = urlparse(listing_url).netloc
        print(f"\n--- Scanning: {listing_url} ---")

        for page_num in range(1, MAX_PAGES_PER_SITE + 1):
            page_url = listing_url if page_num == 1 else f"{listing_url.rstrip('/')}/{page_num}"
            print(f"Page {page_num}: {page_url}")
            links = collect_from_page(page_url, base_domain)
            if not links:
                break
            all_links.update(links)
            time.sleep(1)

    all_links = sorted(all_links)
    with open("links.json", "w", encoding="utf-8") as f:
        json.dump(all_links, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(all_links)} article links collected -> links.json")
    print("Ye links copy karke scrape.py ki URLS list mein daal dein.")


if __name__ == "__main__":
    main()
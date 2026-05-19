from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os

# ============================================
# CREATE EXPORT FOLDER
# ============================================

os.makedirs("exports", exist_ok=True)

# ============================================
# GLOBAL VARIABLES
# ============================================

visited = set()

# ============================================
# URL VALIDATION
# ============================================

def is_valid_url(base_url, target_url):

    parsed_base = urlparse(base_url)
    parsed_target = urlparse(target_url)

    # Stay on same domain
    if parsed_base.netloc != parsed_target.netloc:
        return False

    # Only HTTP/HTTPS
    if parsed_target.scheme not in ["http", "https"]:
        return False

    return True

# ============================================
# BROWSER CRAWLER
# ============================================

def crawl(page, url, depth):

    if depth == 0:
        return

    if url in visited:
        return

    visited.add(url)

    try:

        print(f"\n[+] Crawling: {url}")

        # Open page
        page.goto(url, timeout=15000)

        # Save screenshot
        screenshot_name = (
            urlparse(url).netloc.replace(".", "_") + ".png"
        )

        page.screenshot(
            path=f"exports/{screenshot_name}"
        )

        print("[+] Screenshot Saved")

        # Get rendered HTML
        html = page.content()

        # Parse HTML
        soup = BeautifulSoup(html, "html.parser")

        # Extract links
        links = soup.find_all("a", href=True)

        print(f"[+] Links Found: {len(links)}")

        # Save URLs
        with open(
            "exports/browser_links.txt",
            "a",
            encoding="utf-8"
        ) as file:

            file.write(url + "\n")

        # Recursive crawl
        for link in links:

            href = link["href"]

            full_url = urljoin(url, href)

            full_url = full_url.split("#")[0]

            if is_valid_url(url, full_url):

                crawl(page, full_url, depth - 1)

    except Exception as e:

        print(f"[-] Error: {e}")

# ============================================
# MAIN FUNCTION
# ============================================

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    target = input("Enter URL: ").strip()

    depth = int(input("Depth: "))

    # Auto add HTTPS
    if not target.startswith("http"):
        target = "https://" + target

    crawl(page, target, depth)

    browser.close()

print("\n[+] Browser crawling completed.")
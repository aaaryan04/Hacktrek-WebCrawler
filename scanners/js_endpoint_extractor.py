from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import re
import os

# ============================================
# CREATE EXPORT FOLDER
# ============================================

os.makedirs("exports", exist_ok=True)

# ============================================
# GET USER INPUT
# ============================================

url = input("Enter URL: ").strip()

if not url.startswith("http"):
    url = "https://" + url

# ============================================
# START PLAYWRIGHT
# ============================================

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    print(f"\n[+] Opening: {url}")

    page.goto(url, timeout=20000)

    # Wait for JS rendering
    page.wait_for_timeout(5000)

    # Get rendered HTML
    html = page.content()

    soup = BeautifulSoup(html, "html.parser")

    # ============================================
    # FIND JS FILES
    # ============================================

    scripts = soup.find_all("script", src=True)

    print(f"\n[+] JavaScript Files Found: {len(scripts)}\n")

    endpoints = set()

    # ============================================
    # PROCESS EXTERNAL JS FILES
    # ============================================

    for script in scripts:

        js_url = urljoin(url, script["src"])

        print(f"[+] JS File: {js_url}")

        try:

            response = requests.get(js_url, timeout=10)

            js_content = response.text

            patterns = [
                r'/api/[a-zA-Z0-9_/.-]*',
                r'/v1/[a-zA-Z0-9_/.-]*',
                r'/graphql[a-zA-Z0-9_/.-]*',
                r'/auth/[a-zA-Z0-9_/.-]*'
            ]

            for pattern in patterns:

                matches = re.findall(pattern, js_content)

                for match in matches:
                    endpoints.add(match)

        except Exception as e:

            print(f"[-] JS Error: {e}")

    # ============================================
    # PROCESS INLINE JS
    # ============================================

    inline_scripts = soup.find_all("script")

    print(f"\n[+] Inline Scripts Found: {len(inline_scripts)}")

    for script in inline_scripts:

        js_content = script.text

        patterns = [
            r'/api/[a-zA-Z0-9_/.-]*',
            r'/v1/[a-zA-Z0-9_/.-]*',
            r'/graphql[a-zA-Z0-9_/.-]*',
            r'/auth/[a-zA-Z0-9_/.-]*'
        ]

        for pattern in patterns:

            matches = re.findall(pattern, js_content)

            for match in matches:
                endpoints.add(match)

    # ============================================
    # PRINT RESULTS
    # ============================================

    print("\n=== DISCOVERED ENDPOINTS ===\n")

    if endpoints:

        with open(
            "exports/js_endpoints.txt",
            "w",
            encoding="utf-8"
        ) as file:

            for endpoint in endpoints:

                print(f"[+] {endpoint}")

                file.write(endpoint + "\n")

        print(
            "\n[+] Endpoints saved to exports/js_endpoints.txt"
        )

    else:

        print("[-] No endpoints found.")

    browser.close()
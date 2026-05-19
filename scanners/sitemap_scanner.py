import requests
import xml.etree.ElementTree as ET
import os

# ============================================
# CREATE EXPORT FOLDER
# ============================================

os.makedirs("exports", exist_ok=True)

# ============================================
# GET USER INPUT
# ============================================

url = input("Enter URL: ").strip()

# Add HTTPS automatically
if not url.startswith("http"):
    url = "https://" + url

# Build sitemap URL
sitemap_url = url.rstrip("/") + "/sitemap.xml"

# ============================================
# REQUEST SITEMAP
# ============================================

try:

    response = requests.get(sitemap_url, timeout=10)

    print(f"\n[+] Sitemap URL: {sitemap_url}")
    print(f"[+] Status Code: {response.status_code}")

    # ============================================
    # HANDLE RESPONSE
    # ============================================

    if response.status_code == 200:

        print("\n[+] Parsing sitemap...\n")

        # Parse XML
        root = ET.fromstring(response.content)

        # XML namespace
        namespace = {
            "ns": "http://www.google.com/schemas/sitemap/0.84"
        }

        sitemap_links = []

        # Extract all <loc> URLs
        for loc in root.findall(".//ns:loc", namespace):

            link = loc.text

            sitemap_links.append(link)

            print(f"[+] {link}")

        # Save results
        with open("exports/sitemap_links.txt", "w", encoding="utf-8") as file:

            for item in sitemap_links:
                file.write(item + "\n")

        print("\n[+] Sitemap links saved to exports/sitemap_links.txt")

    elif response.status_code == 404:

        print("\n[-] sitemap.xml NOT FOUND")

    else:

        print(f"\n[-] Unexpected Status Code: {response.status_code}")

except Exception as e:

    print(f"\n[-] Error: {e}")
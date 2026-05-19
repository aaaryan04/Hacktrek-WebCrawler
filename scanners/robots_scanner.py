import requests

# ============================================
# GET USER INPUT
# ============================================

url = input("Enter URL: ").strip()

# Add HTTPS automatically
if not url.startswith("http"):
    url = "https://" + url

# Build robots.txt URL
robots_url = url.rstrip("/") + "/robots.txt"

# ============================================
# REQUEST robots.txt
# ============================================

try:

    response = requests.get(robots_url, timeout=10)

    print(f"\n[+] robots.txt URL: {robots_url}")
    print(f"[+] Status Code: {response.status_code}")

    # ============================================
    # HANDLE RESPONSE
    # ============================================

    if response.status_code == 200:

        print("\n=== robots.txt CONTENT ===\n")

        print(response.text)

    elif response.status_code == 404:

        print("\n[-] robots.txt NOT FOUND")

    else:

        print(f"\n[-] Unexpected Status Code: {response.status_code}")

except Exception as e:

    print(f"\n[-] Error: {e}")
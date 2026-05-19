import requests

# ============================================
# SECURITY HEADERS
# ============================================

SECURITY_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Referrer-Policy"
]

# ============================================
# GET USER INPUT
# ============================================

url = input("Enter URL: ").strip()

# Add HTTPS automatically
if not url.startswith("http"):
    url = "https://" + url

# ============================================
# SEND REQUEST
# ============================================

try:

    response = requests.get(url, timeout=10)

    print(f"\n[+] URL: {url}")
    print(f"[+] Status Code: {response.status_code}\n")

    headers = response.headers

    print("=== SECURITY HEADER ANALYSIS ===\n")

    for header in SECURITY_HEADERS:

        if header in headers:

            print(f"[+] {header}: FOUND")

        else:

            print(f"[-] {header}: MISSING")

except Exception as e:

    print(f"\n[-] Error: {e}")
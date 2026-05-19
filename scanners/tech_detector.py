import requests
from bs4 import BeautifulSoup

# ============================================
# GET USER INPUT
# ============================================

url = input("Enter URL: ").strip()

if not url.startswith("http"):
    url = "https://" + url

# ============================================
# TECHNOLOGY SIGNATURES
# ============================================

TECH_SIGNATURES = {

    "React": [
        "react",
        "_reactrootcontainer",
        "data-reactroot"
    ],

    "Vue.js": [
        "vue"
    ],

    "Angular": [
        "angular",
        "ng-app"
    ],

    "WordPress": [
        "wp-content",
        "wordpress"
    ],

    "jQuery": [
        "jquery"
    ],

    "Bootstrap": [
        "bootstrap"
    ],

    "Django": [
        "csrftoken"
    ],

    "Laravel": [
        "laravel"
    ]
}

# ============================================
# REQUEST WEBSITE
# ============================================

try:

    response = requests.get(url, timeout=10)

    html = response.text.lower()

    headers = str(response.headers).lower()

    soup = BeautifulSoup(html, "html.parser")

    print(f"\n[+] URL: {url}")
    print(f"[+] Status Code: {response.status_code}")

    detected = set()

    # ============================================
    # HTML + HEADER SIGNATURE DETECTION
    # ============================================

    for tech, signatures in TECH_SIGNATURES.items():

        for signature in signatures:

            if (
                signature.lower() in html
                or signature.lower() in headers
            ):

                detected.add(tech)

    # ============================================
    # SCRIPT SRC DETECTION
    # ============================================

    scripts = soup.find_all("script", src=True)

    for script in scripts:

        src = script.get("src", "").lower()

        if "react" in src:
            detected.add("React")

        if "vue" in src:
            detected.add("Vue.js")

        if "angular" in src:
            detected.add("Angular")

        if "jquery" in src:
            detected.add("jQuery")

        if "bootstrap" in src:
            detected.add("Bootstrap")

    # ============================================
    # META GENERATOR DETECTION
    # ============================================

    metas = soup.find_all("meta")

    for meta in metas:

        content = str(meta).lower()

        if "wordpress" in content:
            detected.add("WordPress")

    # ============================================
    # PRINT RESULTS
    # ============================================

    print("\n=== DETECTED TECHNOLOGIES ===\n")

    if detected:

        for tech in detected:

            print(f"[+] {tech}")

    else:

        print("[-] No technologies detected")

except Exception as e:

    print(f"\n[-] Error: {e}")
import requests
from bs4 import BeautifulSoup
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

# ============================================
# REQUEST PAGE
# ============================================

try:

    response = requests.get(url, timeout=10)

    print(f"\n[+] URL: {url}")
    print(f"[+] Status Code: {response.status_code}")

    # Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all forms
    forms = soup.find_all("form")

    print(f"\n[+] Total Forms Found: {len(forms)}\n")

    # Save results
    with open("exports/forms.txt", "w", encoding="utf-8") as file:

        # Process each form
        for index, form in enumerate(forms, start=1):

            print(f"========== FORM {index} ==========")

            # Form details
            action = form.get("action")
            method = form.get("method")

            print(f"Action : {action}")
            print(f"Method : {method}")

            file.write(f"========== FORM {index} ==========\n")
            file.write(f"Action : {action}\n")
            file.write(f"Method : {method}\n")

            # Extract inputs
            inputs = form.find_all("input")

            for input_tag in inputs:

                input_name = input_tag.get("name")
                input_type = input_tag.get("type")

                print(f"Input Name : {input_name}")
                print(f"Input Type : {input_type}")

                file.write(f"Input Name : {input_name}\n")
                file.write(f"Input Type : {input_type}\n")

            print()

            file.write("\n")

    print("[+] Forms saved to exports/forms.txt")

except Exception as e:

    print(f"\n[-] Error: {e}")
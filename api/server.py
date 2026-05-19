import time
import requests
import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bs4 import BeautifulSoup

from api.logger import (
    add_log,
    clear_logs,
    get_logs
)

# ============================================
# CREATE FASTAPI APP
# ============================================

app = FastAPI()

# ============================================
# ENABLE CORS
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# NORMALIZE URL
# ============================================

def normalize_url(url: str):

    if not url.startswith("http"):
        url = "https://" + url

    return url

# ============================================
# HOME ROUTE
# ============================================

@app.get("/")
def home():

    return {
        "message": "Hacktrek-WebCrawler API Running"
    }

# ============================================
# LIVE LOGS API
# ============================================

@app.get("/logs")
def logs():

    return {
        "logs": get_logs()
    }

# ============================================
# HEADER SCANNER API
# ============================================

@app.get("/headers")
def header_scanner(url: str):

    try:

        clear_logs()

        add_log("[+] Starting header scan...")

        time.sleep(1)

        url = normalize_url(url)

        add_log(f"[+] Connecting to {url}")

        response = requests.get(
            url,
            timeout=10
        )

        add_log("[+] Headers collected")

        time.sleep(1)

        add_log("[+] Scan completed")

        return {

            "url": url,

            "status_code": response.status_code,

            "headers": dict(response.headers)
        }

    except Exception as e:

        add_log(f"[-] Error: {str(e)}")

        return {
            "error": str(e)
        }

# ============================================
# FORM EXTRACTOR API
# ============================================

@app.get("/forms")
def form_extractor(url: str):

    try:

        clear_logs()

        add_log("[+] Starting form extraction...")

        time.sleep(1)

        url = normalize_url(url)

        response = requests.get(
            url,
            timeout=10
        )

        add_log("[+] Parsing HTML...")

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        forms = soup.find_all("form")

        results = []

        for form in forms:

            form_data = {

                "action": form.get("action"),

                "method": form.get("method"),

                "inputs": []
            }

            inputs = form.find_all("input")

            for input_tag in inputs:

                form_data["inputs"].append({

                    "name": input_tag.get("name"),

                    "type": input_tag.get("type")
                })

            results.append(form_data)

        add_log(f"[+] Forms found: {len(results)}")

        add_log("[+] Extraction completed")

        return {

            "url": url,

            "forms_found": len(results),

            "forms": results
        }

    except Exception as e:

        add_log(f"[-] Error: {str(e)}")

        return {
            "error": str(e)
        }

# ============================================
# TECHNOLOGY DETECTOR API
# ============================================

@app.get("/tech")
def tech_detector(url: str):

    try:

        clear_logs()

        add_log("[+] Starting technology detection...")

        time.sleep(1)

        url = normalize_url(url)

        response = requests.get(
            url,
            timeout=10
        )

        html = response.text.lower()

        technologies = []

        signatures = {

            "WordPress": "wp-content",

            "React": "react",

            "Vue.js": "vue",

            "Angular": "angular",

            "Bootstrap": "bootstrap",

            "jQuery": "jquery",

            "Laravel": "laravel",

            "Django": "csrftoken"
        }

        for tech, signature in signatures.items():

            if signature in html:

                technologies.append(tech)

                add_log(f"[+] Detected: {tech}")

        add_log("[+] Detection completed")

        return {

            "url": url,

            "technologies": technologies
        }

    except Exception as e:

        add_log(f"[-] Error: {str(e)}")

        return {
            "error": str(e)
        }

# ============================================
# ROBOTS.TXT API
# ============================================

@app.get("/robots")
def robots_scanner(url: str):

    try:

        clear_logs()

        add_log("[+] Fetching robots.txt...")

        time.sleep(1)

        url = normalize_url(url)

        robots_url = url.rstrip("/") + "/robots.txt"

        response = requests.get(
            robots_url,
            timeout=10
        )

        add_log(f"[+] Status Code: {response.status_code}")

        add_log("[+] robots.txt fetched")

        return {

            "robots_url": robots_url,

            "status_code": response.status_code,

            "content": response.text
        }

    except Exception as e:

        add_log(f"[-] Error: {str(e)}")

        return {
            "error": str(e)
        }

# ============================================
# SITEMAP API
# ============================================

@app.get("/sitemap")
def sitemap_scanner(url: str):

    try:

        clear_logs()

        add_log("[+] Fetching sitemap.xml...")

        time.sleep(1)

        url = normalize_url(url)

        sitemap_url = url.rstrip("/") + "/sitemap.xml"

        response = requests.get(
            sitemap_url,
            timeout=10
        )

        add_log(f"[+] Status Code: {response.status_code}")

        add_log("[+] Sitemap fetched")

        return {

            "sitemap_url": sitemap_url,

            "status_code": response.status_code,

            "content": response.text
        }

    except Exception as e:

        add_log(f"[-] Error: {str(e)}")

        return {
            "error": str(e)
        }

# ============================================
# SUBDOMAIN SCANNER API
# ============================================

@app.get("/subdomains")
def subdomain_scanner(url: str):

    try:

        if not url.startswith("http"):
            url = "https://" + url

        domain = (
            url.replace("https://", "")
            .replace("http://", "")
            .replace("/", "")
        )

        common_subdomains = [

            "www",
            "mail",
            "admin",
            "api",
            "dev",
            "test",
            "beta",
            "blog",
            "shop",
            "support"
        ]

        found = []

        for sub in common_subdomains:

            full_domain = f"{sub}.{domain}"

            found.append(full_domain)

        return {

            "target": domain,
            "subdomains_found": len(found),
            "subdomains": found
        }

    except Exception as e:

        return {
            "error": str(e)
        }
from urllib.parse import urlparse, parse_qs

        # ============================================
# URL PARAMETER EXTRACTOR API
# ============================================

@app.get("/params")
def parameter_extractor(url: str):

    try:

        clear_logs()

        add_log("[+] Starting parameter extraction...")

        time.sleep(1)

        url = normalize_url(url)

        response = requests.get(
            url,
            timeout=10
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        links = soup.find_all("a")

        found_params = []

        for link in links:

            href = link.get("href")

            if href and "?" in href:

                found_params.append(href)

        add_log(f"[+] URLs with parameters found: {len(found_params)}")

        add_log("[+] Extraction completed")

        return {

            "url": url,

            "parameters_found": len(found_params),

            "parameter_urls": found_params
        }

    except Exception as e:

        add_log(f"[-] Error: {str(e)}")

        return {

            "error": str(e)
        }
    

    
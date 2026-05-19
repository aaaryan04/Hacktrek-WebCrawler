import aiohttp
import asyncio
import os

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# ============================================
# CREATE EXPORT FOLDER
# ============================================

os.makedirs("exports", exist_ok=True)

# ============================================
# GLOBAL VARIABLES
# ============================================

visited = set()
results = []

# Limit concurrent requests
semaphore = asyncio.Semaphore(5)

# ============================================
# LOGGER
# ============================================

def log(message):

    print(message)

    with open("exports/logs.txt", "a", encoding="utf-8") as file:
        file.write(message + "\n")

# ============================================
# URL VALIDATION
# ============================================

def is_valid_url(base_url, target_url):

    parsed_base = urlparse(base_url)
    parsed_target = urlparse(target_url)

    # Allow only same exact domain
    if parsed_base.netloc != parsed_target.netloc:
        return False

    # Allow only HTTP/HTTPS
    if parsed_target.scheme not in ["http", "https"]:
        return False

    # Skip unwanted URLs
    blocked_patterns = [
        "javascript:",
        "mailto:",
        "#",
        "/url?q=",
    ]

    for pattern in blocked_patterns:

        if pattern in target_url:
            return False

    return True

# ============================================
# ASYNC CRAWLER
# ============================================

async def crawl(session, url, depth):

    # Stop conditions
    if depth == 0:
        return

    if url in visited:
        return

    visited.add(url)

    try:

        async with semaphore:

            async with session.get(url, ssl=False) as response:

                status = response.status

                log(f"\n[+] Crawling: {url}")
                log(f"    Status: {status}")

                # Save result
                results.append({
                    "url": url,
                    "status": status
                })

                # Read page HTML
                html = await response.text(errors="ignore")

                # Parse HTML
                soup = BeautifulSoup(html, "html.parser")

                tasks = []

                # Extract links
                for link in soup.find_all("a", href=True):

                    href = link["href"]

                    # Convert relative URL → absolute URL
                    full_url = urljoin(url, href)

                    # Remove fragments
                    full_url = full_url.split("#")[0]

                    # Validate URL
                    if not is_valid_url(url, full_url):
                        continue

                    # Recursive crawling
                    tasks.append(
                        crawl(session, full_url, depth - 1)
                    )

                # Run async tasks
                await asyncio.gather(*tasks)

    except Exception as e:

        log(f"\n[-] Error on: {url}")
        log(f"    {str(e)}")

# ============================================
# SAVE RESULTS
# ============================================

def save_results():

    with open("exports/results.txt", "w", encoding="utf-8") as file:

        for item in results:

            file.write(
                f"{item['url']} | Status: {item['status']}\n"
            )

    log("\n[+] Results saved to exports/results.txt")

# ============================================
# MAIN FUNCTION
# ============================================

async def main():

    target = input("Enter URL: ").strip()

    depth = int(input("Depth: "))

    # Add HTTPS automatically
    if not target.startswith("http"):
        target = "https://" + target

    headers = {
        "User-Agent": "Hacktrek-WebCrawler/1.0"
    }

    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(
        headers=headers,
        timeout=timeout
    ) as session:

        await crawl(session, target, depth)

    save_results()

    log(f"\n[+] Total URLs Crawled: {len(visited)}")

# ============================================
# START PROGRAM
# ============================================

if __name__ == "__main__":

    asyncio.run(main())
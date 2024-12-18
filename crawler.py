### crawler.py ###
import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
from pymongo import MongoClient
import re

# MongoDB setup
DB_NAME = "biology_department"
DB_HOST = "localhost"
DB_PORT = 27017
try:
    client = MongoClient(host=DB_HOST, port=DB_PORT)
    db = client[DB_NAME]
    faculty_collection = db["faculty_pages"]
except Exception as e:
    print(f"Could not connect to database: {e}")
    exit()

visited = set()
max_faculty_pages = 10
semaphore = asyncio.Semaphore(
    10
)  # Limit concurrent requests to avoid overwhelming the server


async def fetch(session, url):
    try:
        async with semaphore:
            await asyncio.sleep(
                1
            )  # Add a politeness delay of 1 second between requests
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None


def sanitize_url(base_url, relative_url):
    sanitized_url = urljoin(base_url, relative_url.strip())
    return sanitized_url if is_valid_url(sanitized_url) else None


def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def is_target_page(url):
    return re.search(r"/faculty|staff|people/", url, re.IGNORECASE) is not None


def is_within_domain(url, base_url="https://www.cpp.edu/sci/biological-sciences/"):
    return url.startswith(base_url)


def extract_and_store_faculty_data(soup, url):
    faculty_entries = soup.find_all(
        "div", class_="card-body d-flex flex-column align-items-start"
    )
    if not faculty_entries:
        print(f"No faculty data found on: {url}")
        return

    for entry in faculty_entries:
        name = (
            entry.find("h3", class_="mb-0").text.strip()
            if entry.find("h3", class_="mb-0")
            else "N/A"
        )
        title = (
            entry.find("div", class_="mb-1 text-muted").text.strip()
            if entry.find("div", class_="mb-1 text-muted")
            else "N/A"
        )
        email = (
            entry.find("a", href=True).text.strip()
            if entry.find("a", href=True)
            else "N/A"
        )
        web_link = entry.select('a[href^="https://www.cpp.edu/faculty/"]')
        if web_link:
            for web in web_link:
                web = web.get("href")
        else:
            web = "No CPP website available."

        faculty_data = {"name": name, "title": title, "email": email, "url": web}
        try:
            faculty_collection.insert_one(faculty_data)
            print(f"Inserted: {faculty_data}")
        except Exception as e:
            print(f"Error inserting data into MongoDB: {e}")


async def crawl(seed_url):
    frontier = [seed_url]
    async with aiohttp.ClientSession() as session:
        while frontier and len(visited) < max_faculty_pages:
            url = frontier.pop(0)
            if url in visited:
                continue
            visited.add(url)

            print(f"Processing: {url}")
            html = await fetch(session, url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            if is_target_page(url):
                extract_and_store_faculty_data(soup, url)
                if len(visited) >= max_faculty_pages:
                    break

            for link in soup.find_all("a", href=True):
                absolute_url = sanitize_url(url, link["href"])
                if absolute_url and is_within_domain(absolute_url):
                    frontier.append(absolute_url)


if __name__ == "__main__":
    seed_url = "https://www.cpp.edu/sci/biological-sciences/index.shtml"
    asyncio.run(crawl(seed_url))

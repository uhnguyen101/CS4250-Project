import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
from pymongo import MongoClient

# MongoDB setup
# client = pymongo.MongoClient("mongodb+srv://nathanzamora45:al7bJQa8WRxkhfxk@cluster0.ubcxi.mongodb.net/")
# db = client["biology_department"]
# faculty_collection = db["faculty_pages"]

####################################################
# MongoDB Set-Up
DB_NAME = 'biology_department'
DB_HOST = 'localhost'
DB_PORT = 27017
try:
    client = MongoClient(host=DB_HOST, port=DB_PORT)
    db = client[DB_NAME]
    # pages = db['pages']
    faculty_collection = db['faculty_pages']
except:
    print('Could not connect to database.')
####################################################

visited = set()

async def fetch(session, url):
    try:
        url = quote(url, safe=":/")
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"HTTP {response.status}: {url}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def sanitize_url(base_url, relative_url):
    try:
        relative_url = relative_url.strip()
        sanitized_url = urljoin(base_url, relative_url)
        sanitized_url = quote(sanitized_url, safe=":/")
        if not is_valid_url(sanitized_url):
            return None
        return sanitized_url
    except Exception as e:
        print(f"Error sanitizing URL: {relative_url} - {e}")
        return None

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def is_target_page(url):
    return "faculty/index.shtml" in url

def extract_and_store_faculty_data(soup, url):
    # Find all individual faculty entries
    faculty_entries = soup.find_all('div', class_='card-body d-flex flex-column align-items-start')
    if not faculty_entries:
        print(f"No faculty data found on: {url}")
        return

    for entry in faculty_entries:
        # Extract name
        name = entry.find('h3', class_='mb-0').text.strip() if entry.find('h3', class_='mb-0') else "N/A"

        # Extract title
        title_div = entry.find_all('div', class_='mb-1 text-muted')
        title = title_div[0].text.strip() if title_div else "N/A"

        # Extract contact information
        email = "N/A"
        phone = "N/A"
        office = "N/A"

        # Extract phone and office from <li>
        contact_list = entry.find_all('li')
        for contact in contact_list:
            if contact.find('i', class_='fas fa-phone'):
                phone = contact.text.strip().replace("phone number or extension", "").strip()
            elif contact.find('i', class_='fas fa-building'):
                office = contact.text.strip().replace("office location", "").strip()

        # Extract email and clean it up
        email_link = entry.find('a', href=True)
        if email_link and "mailto:" in email_link['href']:
            email = email_link.text.strip().replace("email address", "").strip()

        web_link = entry.select('a[href^="https://www.cpp.edu/faculty/"]')
        if web_link:
            for web in web_link:
                web = web.get('href')
        else:
            web = "No CPP website available."

        # Save to MongoDB
        faculty_data = {
            "name": name,
            "title": title,
            "email": email,
            "phone": phone,
            "office": office,
            "url": web
        }
        faculty_collection.insert_one(faculty_data)
        print(f"Inserted faculty data: {faculty_data}")


async def crawl(seed_url):
    frontier = [seed_url]
    async with aiohttp.ClientSession() as session:
        while frontier:
            url = frontier.pop(0)
            if url in visited:
                continue
            visited.add(url)

            print(f"Processing: {url}")
            html = await fetch(session, url)
            if not html:
                continue

            soup = BeautifulSoup(html, 'html.parser')
            if is_target_page(url):
                print(f"Target page found: {url}")
                extract_and_store_faculty_data(soup, url)
                continue

            for link in soup.find_all('a', href=True):
                absolute_url = sanitize_url(url, link['href'])
                if absolute_url and is_valid_url(absolute_url):
                    frontier.append(absolute_url)

if __name__ == "__main__":
    seed_url = "https://www.cpp.edu/sci/biological-sciences/index.shtml"
    asyncio.run(crawl(seed_url))

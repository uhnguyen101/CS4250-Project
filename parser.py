### parser.py ###
from urllib.parse import urljoin
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
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


def get_content(url):
    try:
        response = urlopen(url)
        html = response.read().decode("utf-8")
        bs = BeautifulSoup(html, "html.parser")

        # Primary target
        div = bs.find("div", {"class": "section-intro"})
        if div:
            return div.text.strip()

        # Alternative targets
        alt1 = bs.find("div", {"class": "faculty-research"})
        if alt1:
            return alt1.text.strip()

        alt2 = bs.find("div", {"id": "research-details"})
        if alt2:
            return alt2.text.strip()

        alt3 = bs.find("div", {"class": "research-summary"})
        if alt3:
            return alt3.text.strip()

        print(f"No valid content found for {url}.")
        return None
    except Exception as e:
        print(f"Error fetching or parsing content from {url}: {e}")
        return None


# Only process documents without indexed content
urls = faculty_collection.find(
    {"prof_contents": {"$exists": False}}, {"_id": 0, "url": 1}
)

for url_in_doc in urls:
    url = url_in_doc["url"]
    if url == "No CPP website available.":
        continue
    try:
        response = urlopen(url)
        html = response.read().decode("utf-8")
        bs = BeautifulSoup(html, "html.parser")
        prof_links = []
        nav_list = bs.find("ul", class_="fac-nav")
        if nav_list:
            for a_tag in nav_list.find_all("a", href=True):
                if url == "https://www.cpp.edu/faculty/alas":
                    full_url = "https://www.cpp.edu/faculty/alas/" + str(
                        a_tag["href"]
                    )  # Edge case for 'alas' page
                else:
                    full_url = urljoin(url, a_tag["href"])
                prof_links.append(full_url)

        # Remove duplicate links
        prof_links = list(set(prof_links))

        for link in prof_links:
            content = get_content(link)
            if content:
                try:
                    faculty_collection.update_one(
                        {"url": url},
                        {"$set": {f"prof_contents.{link.replace('.','_')}": content}},
                    )
                    print("Updating content for: ", link)
                except Exception as e:
                    print(f"Exception updating {url} for {link}: {e}")
    except HTTPError as e:
        print(f"Unable to access {url}: HTTP Error {e.code}")
    except URLError as e:
        print(f"Unable to access {url}: {e.reason}")

from urllib.parse import urljoin
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
from bs4 import BeautifulSoup
from pymongo import MongoClient
import re

####################################################
# Create a database connection object using pymongo
DB_NAME = 'biology_department'
DB_HOST = 'localhost'
DB_PORT = 27017
try:
    client = MongoClient(host=DB_HOST, port=DB_PORT)
    db = client[DB_NAME]
    faculty_collection = db['faculty_pages']
except:
    print('Could not connect to database.')
####################################################

def get_content(url):
    try:
        response = urlopen(url)
        html = response.read().decode('utf-8')
        bs = BeautifulSoup(html, 'html.parser')
        div = bs.find('div', {'class': 'section-intro'})
        content = div.text
        return {
            'url': url,
            'content': content
        }
    except Exception as e:
        print(f'Unable to get content from {url}: {e}')

urls = faculty_collection.find({},{'_id': 0,'url': 1})

for url_in_doc in urls:
    url = url_in_doc['url']
    if url == "No CPP website available.":
        continue
    try:
        response = urlopen(url)
        html = response.read().decode('utf-8')
        bs = BeautifulSoup(html, 'html.parser')
        prof_links = []
        nav_list = bs.find('ul', class_='fac-nav')
        if nav_list:
            for a_tag in nav_list.find_all('a', href=True):
                if url == "https://www.cpp.edu/faculty/alas":
                    full_url = 'https://www.cpp.edu/faculty/alas/' + str(a_tag['href']) # for some reason it didn't get alas for the url
                else:
                    full_url = urljoin(url, a_tag['href'])
                prof_links.append(full_url)
        for link in prof_links:
            content = get_content(link)
            if content:
                try: 
                    result = faculty_collection.update_one(
                        {'url': url},
                        {"$set": {f"prof_contents.{link.replace('.','_')}": content}} 
                    )
                    # print("Updated result: ", result)
                except Exception as e:
                    print(f"Exception {e}")
    except HTTPError as e:
        print(f"Unable to access {url}: {e}")
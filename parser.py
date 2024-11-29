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
    # pages = db['pages']
    faculty_collection = db['faculty_pages']
except:
    print('Could not connect to database.')
####################################################


target_page = 'https://www.cpp.edu/faculty/nebuckley/research.shtml'
# html = collection.find_one({'url': target_page}).get('html')
# html = collection.find_one()
# print(html)
html = urlopen(target_page).read()
bs = BeautifulSoup(html, 'html.parser')

div = bs.find('div', {'class': 'section-intro'})  # Or use other attributes like 'id'

# Extract all <p> tags within the div
# p_tags = div.find_all('p')

# for p in p_tags:
#     print(p)
print(div.text)
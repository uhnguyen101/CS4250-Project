# Faculty Search Engine Project

## Project Overview

This project is a **Faculty Search Engine** designed to crawl, parse, index, and allow for querying faculty pages from Cal Poly Pomona's Biology Department. The objective is to create an effective tool that gathers faculty information from department websites, indexes key content, and allows users to search for relevant faculty profiles based on specific queries. The search results include a link to the faculty page and a snippet of relevant content.

## Features and Workflow

### 1. **Web Crawler**
The project starts with a **web crawler** (`crawler.py`) that uses `aiohttp` and `BeautifulSoup` to begin crawling from **seed URLs** for each of the three departments. The crawler:
- **Extracts URLs** from the seed pages and follows these links to find all individual faculty pages.
- Ensures that links stay within the department domain and handles any broken links effectively.
- **Stores faculty data** (e.g., name, title, email, page URL) into a MongoDB collection called `faculty_pages`.

### 2. **Parsing and Indexing**
After the faculty data is collected, the **parser** (`parser.py`) processes each faculty page:
- Uses `urllib` and `BeautifulSoup` to **retrieve content** from URLs stored in MongoDB.
- Extracts relevant content sections such as **Research Interests** or **Introduction**.
- **Indexes** the extracted content and stores it in the `prof_contents` field of each faculty document in MongoDB for efficient searching.

### 3. **Search Engine**
The **query module** (`query.py`) allows users to search through the indexed content:
- Uses `TfidfVectorizer` from **scikit-learn** to convert indexed content into numerical vectors for efficient comparison.
- Supports **synonym expansion** using WordNet to enhance query recall, ensuring broader matches for search terms.
- Implements **cosine similarity** to rank results based on the user's input.
- Displays search results with **paginated output** (5 results per page), including the faculty member's name, URL, and a **snippet** of matching content.

### 4. **User Interaction and Pagination**
- Users can enter a query (e.g., "genome analysis" or "marine biology") and receive **relevant faculty profiles**.
- The search engine provides pagination, allowing users to navigate through results with `'n'` for the next page or `'p'` for the previous page. Users can enter new queries at any point during pagination.

## Project Requirements Satisfied
- **Web Crawling**: The crawler collects all faculty pages starting from the given seed URLs, respecting domain boundaries.
- **Data Storage**: Crawled faculty data is saved in a MongoDB collection, allowing for further processing.
- **Content Parsing and Indexing**: The parser extracts key content from each faculty page and indexes it for easy searching.
- **Search Engine with Pagination**: Users can input arbitrary queries, and the system retrieves and ranks relevant results, displaying snippets and pagination.

## Tools and Libraries Used
- **Python Libraries**:
  - `aiohttp` and `BeautifulSoup` for web crawling and parsing.
  - `PyMongo` for storing and accessing data in MongoDB.
  - `scikit-learn` for TF-IDF vectorization and similarity computation.
  - `NLTK` for synonym expansion (using WordNet).
- **MongoDB**: Data storage for faculty pages and indexed content.

## Setup and Running the Project
1. **Prerequisites**:
   - Install Python 3.x, MongoDB, and required Python libraries (`aiohttp`, `beautifulsoup4`, `pymongo`, `scikit-learn`, `nltk`).
2. **Crawl Faculty Pages**:
   - Run `crawler.py` to begin crawling and storing faculty data in MongoDB.
3. **Parse and Index Content**:
   - Run `parser.py` to extract and index the faculty page content for searching.
4. **Search the Index**:
   - Run `query.py` to start the search engine interface, where users can enter queries and navigate results.

## Future Improvements
- **Relevance Optimization**: Further refine query expansion and scoring to improve the relevance of search results.
- **Web Interface**: Develop a simple GUI for easier interaction rather than using a command-line interface.

## Conclusion
This project successfully demonstrates an end-to-end search engine for university faculty pages, using web crawling, content parsing, and information retrieval techniques. It enables users to efficiently search for faculty profiles based on research areas or other content, making it a valuable tool for students or collaborators seeking specific expertise.


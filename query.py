### query.py ###
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import wordnet
import re
import math
import nltk

nltk.download("wordnet")

# Connect to MongoDB
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

# Domain-specific synonym dictionary
domain_synonyms = {
    "genomics": ["genetics", "genomic studies", "gene sequencing"],
    "microorganisms": ["microbes", "bacteria", "microbial life"],
    "ecology": ["ecosystem", "environmental biology"],
}


# Preprocess Content
def preprocess_content(content):
    """
    Clean and preprocess content to remove irrelevant text and normalize it.
    """
    content = re.sub(r"\n|\r", " ", content)  # Replace line breaks
    content = re.sub(r"[^\w\s]", "", content)  # Remove punctuation
    return content.lower()


# Snippet Extraction
def get_snippet(content, query, max_length=200):
    """
    Extract a snippet from the content that matches the query.
    """
    query_words = query.lower().split()
    sentences = content.split(". ")
    snippet = ""
    for sentence in sentences:
        if any(word in sentence.lower() for word in query_words):
            snippet += sentence.strip() + ". "
            if len(snippet) >= max_length:
                break
    return snippet[:max_length].strip()


# Load Data
def load_data():
    """
    Load indexed content from MongoDB and prepare it for searching.
    """
    documents = faculty_collection.find({"prof_contents": {"$exists": True}})
    content_list = []
    urls = []
    names = []

    for doc in documents:
        name = doc.get("name", "Unknown Faculty")
        url = doc.get("url", "No URL Available")
        # Combine all content into a single string
        all_content = " ".join(doc.get("prof_contents", {}).values())
        if all_content.strip():  # Skip empty content
            content_list.append(preprocess_content(all_content))
            urls.append(url)
            names.append(name)

    return content_list, urls, names


# Expand Query Using Synonyms
def expand_query(query, max_synonyms=3):
    """
    Expand the query with a limited number of synonyms to improve recall without adding too much noise.
    """
    expanded_terms = query.split()
    for word in query.split():
        # Add domain-specific synonyms
        if word in domain_synonyms:
            expanded_terms.extend(domain_synonyms[word])
        else:
            synonyms = wordnet.synsets(word)
            added_synonyms = 0
            for syn in synonyms:
                for lemma in syn.lemmas():
                    if added_synonyms >= max_synonyms:
                        break
                    expanded_terms.append(lemma.name())
                    added_synonyms += 1
                if added_synonyms >= max_synonyms:
                    break
    return " ".join(set(expanded_terms))


# Search Function
def search(query, page=1, per_page=5):
    """
    Search for relevant faculty pages based on the query.
    """
    content_list, urls, names = load_data()

    # Expand the query using synonyms
    query = expand_query(query)
    print(f"Expanded Query: {query}")  # Debug statement to analyze expanded query

    # Vectorize content and query
    vectorizer = TfidfVectorizer(
        stop_words="english", max_df=0.95, min_df=0.005, ngram_range=(1, 3)
    )
    tfidf_matrix = vectorizer.fit_transform(content_list)
    query_vec = vectorizer.transform([query])

    # Compute similarity
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()

    # Sort and filter results
    results = sorted(
        zip(names, urls, content_list, similarities), key=lambda x: x[3], reverse=True
    )
    results = [
        r for r in results if r[3] > 0.01
    ]  # Adjusted threshold to include more relevant results

    # Diversity-based Re-Ranking: Ensure diverse top results
    unique_faculty = {}
    for name, url, content, score in results:
        if name not in unique_faculty:
            unique_faculty[name] = (name, url, content, score)
    results = list(unique_faculty.values())

    # Paginate results
    start = (page - 1) * per_page
    end = start + per_page
    paginated_results = results[start:end]

    # Display results
    print(f"\nPage {page} Results:")
    for i, (name, url, content, score) in enumerate(paginated_results, start=1):
        snippet = get_snippet(content, query)
        print(f"{i}. Name: {name}")
        print(f"   URL: {url}")
        print(f"   Snippet: {snippet}...")
        print(f"   Score: {score:.4f}\n")

    # Return total pages
    total_pages = math.ceil(len(results) / per_page)
    return total_pages


# Main Function
if __name__ == "__main__":
    while True:
        query = input("Enter your search query (or 'exit' to quit): ").strip()
        if query.lower() == "exit":
            break

        page = 1
        total_pages = search(query, page)

        while True:
            print(f"Showing page {page} of {total_pages}.")
            action = (
                input(
                    "Enter 'n' for next page, 'p' for previous page, 'q' to quit pagination, or type a new query: "
                )
                .strip()
                .lower()
            )

            if action == "n" and page < total_pages:
                page += 1
                search(query, page)
            elif action == "n":
                print("No more pages.")
            elif action == "p" and page > 1:
                page -= 1
                search(query, page)
            elif action == "p":
                print("No previous pages.")
            elif action == "q":
                break
            elif len(action) > 1:  # Assuming this is a new query
                query = action
                page = 1
                total_pages = search(query, page)
            else:
                print("Invalid input. Try again.")

"""
Scraper module to fetch and analyze web pages related to Software Reliability Growth.
"""
import json
import time
import re
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# Configuration
KEYWORDS = [
    "Software Reliability Growth",
    "Software Reliability Growth Models",
    "Software Reliability"
]
NUM_RESULTS = 30  # Number of search results to fetch (DuckDuckGo limit ~30)
DELAY_SECONDS = 1  # Rate limiting between requests
OUTPUT_FILE = "scraped_data.json"
WORD_PATTERN = re.compile(r'\b\w+\b')


def search_keyword(ddg: DDGS, keyword: str, num_results: int) -> List[str]:
    """Search for a single keyword."""
    urls = []
    try:
        results = ddg.text(keyword, max_results=num_results)
        for result in results:
            href = result.get('href')
            if href:
                urls.append(href)
    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"Error searching for '{keyword}': {e}")
    return urls


def search_urls(keywords: List[str], num_results: int = 10) -> List[str]:
    """
    Search DuckDuckGo for URLs matching any keyword.
    Returns a list of unique URLs.
    """
    ddg = DDGS()
    seen = set()
    urls: List[str] = []

    for keyword in keywords:
        keyword_urls = search_keyword(ddg, keyword, num_results)
        for url in keyword_urls:
            if url not in seen:
                seen.add(url)
                urls.append(url)

    print(f"Found {len(urls)} unique URLs.")
    return urls[:num_results]  # Cap to avoid overload


def clean_text(text: str) -> str:
    """
    Clean extracted text: remove extra whitespace, scripts, styles, and short snippets.
    """
    # Remove script/style tags and common noise
    soup = BeautifulSoup(text, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
        tag.decompose()

    # Get text and clean
    text = soup.get_text()
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    # Filter out very short or irrelevant text
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
    cleaned = '. '.join(sentences).strip()
    return f"{cleaned}." if cleaned else ""


def ensure_body_has_words(soup: BeautifulSoup, text: str) -> str:
    """
    Ensure the body text has meaningful content.
    If not, try to fallback to other content sources.
    """
    if WORD_PATTERN.search(text):
        return text

    fallback_sources = [
        ' '.join(elem.get_text() for elem in soup.find_all('p')),
        soup.get_text(" ")
    ]

    for source in fallback_sources:
        cleaned = clean_text(source)
        if WORD_PATTERN.search(cleaned):
            return cleaned

    return "No meaningful body text found."


def scrape_page(url: str, delay: int = 1) -> Optional[Dict[str, str]]:
    """
    Fetch and scrape a single page: title, meta description, and main body text.
    Returns a dict with extracted data or error message.
    """
    time.sleep(delay)  # Rate limit

    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/91.0.4472.124 Safari/537.36'
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract title
        title = soup.find('title')
        title = title.get_text().strip() if title else "No title"

        # Extract meta description
        desc = soup.find('meta', attrs={'name': 'description'})
        description = desc.get('content', '').strip() if desc else "No description"

        # Extract main body (focus on <p> and <article> tags)
        body_elements = soup.find_all(
            ['p', 'article', 'div'],
            class_=re.compile(r'content|body|main|article')
        )
        body_text = ' '.join([elem.get_text() for elem in body_elements[:10]])
        cleaned_body = clean_text(body_text)
        cleaned_body = ensure_body_has_words(soup, cleaned_body)

        return {
            'url': url,
            'title': title,
            'description': description,
            'body': cleaned_body[:2000]
        }

    except requests.RequestException as e:
        print(f"Request error for {url}: {e}")
        return None


def fetch_more_urls(attempted: set) -> List[str]:
    """Fetch more URLs excluding already attempted ones."""
    extra_candidates = search_urls(KEYWORDS, NUM_RESULTS * 2)
    return [u for u in extra_candidates if u not in attempted]


def process_scraping_queue(urls: List[str]) -> List[Dict[str, str]]:
    """
    Process the list of URLs and scrape data until the target number of results is reached.
    """
    scraped_data = []
    attempted = set()
    url_queue = urls[:]  # Make a copy to act as a queue

    while len(scraped_data) < NUM_RESULTS:
        if not url_queue:
            new_urls = fetch_more_urls(attempted)
            if not new_urls:
                print("No additional URLs available to retry.")
                break
            url_queue.extend(new_urls)
            if not url_queue:
                break

        url = url_queue.pop(0)

        if url in attempted:
            continue
        attempted.add(url)

        print(f"Scraping {len(scraped_data) + 1}/{NUM_RESULTS}: {url}")
        data = scrape_page(url, DELAY_SECONDS)
        if data:
            scraped_data.append(data)
        else:
            print(f"Scrape failed for {url}. Trying a different URL.")

    return scraped_data


def main():
    """
    Main function: Search, scrape, and save data.
    """
    print("Starting scraper for Software Reliability Growth keywords...")

    urls = search_urls(KEYWORDS, NUM_RESULTS)
    scraped_data = process_scraping_queue(urls)

    # Step 3: Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, indent=2, ensure_ascii=False)

    print(f"Scraping complete! Data saved to {OUTPUT_FILE}")
    print(f"Total entries: {len(scraped_data)}")


if __name__ == "__main__":
    main()

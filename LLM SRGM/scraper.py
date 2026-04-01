"""
Scraper module to fetch and analyze web pages related to Software Reliability Growth.
"""
import json
import time
import re
import logging
from typing import List, Dict, Optional, Set
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
KEYWORDS = [
    "Software Reliability Growth",
    "Software Reliability Growth Models",
    "Software Reliability"
]
NUM_RESULTS = 30  # Number of search results to fetch (DuckDuckGo limit ~30)
DELAY_SECONDS = 1  # Rate limiting between requests
TIMEOUT_SECONDS = 10
OUTPUT_FILE = "scraped_data.json"
WORD_PATTERN = re.compile(r'\b\w+\b')


def _search_keyword(ddg: DDGS, keyword: str, num_results: int, seen: Set[str], urls: List[str]):
    """
    Search for a single keyword and update the seen set and urls list.
    """
    try:
        results = ddg.text(keyword, max_results=num_results)
        for result in results:
            href = result.get('href')
            if href and href not in seen:
                seen.add(href)
                urls.append(href)
    except Exception as e: # pylint: disable=broad-exception-caught
        logging.error("Error searching for '%s': %s", keyword, e)


def search_urls(keywords: List[str], num_results: int = 10) -> List[str]:
    """
    Search DuckDuckGo for URLs matching any keyword.
    Returns a list of unique URLs.
    """
    ddg = DDGS()
    seen = set()
    urls: List[str] = []

    # Search for each keyword separately and combine
    for keyword in keywords:
        _search_keyword(ddg, keyword, num_results, seen, urls)

    logging.info("Found %d unique URLs.", len(urls))
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
        response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
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
        logging.warning("Request error for %s: %s", url, e)
        return None


def _fetch_additional_urls(
        current_urls: List[str],
        attempted: Set[str],
        keywords: List[str],
        count: int
    ) -> bool:
    """
    Fetch more URLs and add them to the list if they haven't been attempted.
    Returns True if new URLs were added, False otherwise.
    """
    extra_candidates = search_urls(keywords, count)
    new_urls = [u for u in extra_candidates if u not in attempted]

    if not new_urls:
        return False

    current_urls.extend(new_urls)
    return True


def process_scraping_queue(urls: List[str]) -> List[Dict[str, str]]:
    """
    Process the list of URLs and scrape data until the target number of results is reached.
    """
    scraped_data = []
    attempted = set()
    url_index = 0

    while len(scraped_data) < NUM_RESULTS:
        # If we ran out of URLs, try to fetch more
        if url_index >= len(urls):
            added_more = _fetch_additional_urls(urls, attempted, KEYWORDS, NUM_RESULTS * 2)
            if not added_more:
                logging.info("No additional URLs available to retry.")
                break
            continue

        url = urls[url_index]
        url_index += 1

        if url in attempted:
            continue
        attempted.add(url)

        logging.info("Scraping %d/%d: %s", len(scraped_data) + 1, NUM_RESULTS, url)
        data = scrape_page(url, DELAY_SECONDS)

        if data:
            scraped_data.append(data)
        else:
            logging.warning("Scrape failed for %s. Trying a different URL.", url)

    return scraped_data


def main():
    """
    Main function: Search, scrape, and save data.
    """
    logging.info("Starting scraper for Software Reliability Growth keywords...")

    urls = search_urls(KEYWORDS, NUM_RESULTS)
    scraped_data = process_scraping_queue(urls)

    # Step 3: Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, indent=2, ensure_ascii=False)

    logging.info("Scraping complete! Data saved to %s", OUTPUT_FILE)
    logging.info("Total entries: %d", len(scraped_data))


if __name__ == "__main__":
    main()

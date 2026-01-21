"""
Unit tests for the scraper module.
"""
import unittest
from unittest.mock import patch
from bs4 import BeautifulSoup
from scraper import clean_text, ensure_body_has_words, process_scraping_queue

class TestScraper(unittest.TestCase):
    """Test cases for scraper functions."""

    def test_clean_text(self):
        """Test that text is cleaned and formatted correctly."""
        # clean_text splits by '.' and filters out short sentences (<20 chars).
        # "This is a test" is < 20 chars, so it might return empty.
        # Let's try a longer sentence.
        raw_text_long = (
            "   This is a longer sentence that should be kept because it is long enough.   "
        )
        cleaned = clean_text(raw_text_long)
        self.assertEqual(
            cleaned,
            "This is a longer sentence that should be kept because it is long enough."
        )

    def test_clean_text_removes_tags(self):
        """Test that HTML tags are removed from text."""
        raw_text = "<p>Clean me</p><style>body {color: red;}</style>"
        # "Clean me" is short, so it returns ""
        cleaned = clean_text(raw_text)
        self.assertEqual(cleaned, "")

    def test_ensure_body_has_words(self):
        """Test that meaningful text is returned if present."""
        soup = BeautifulSoup("<p>Some fallback text here</p>", "html.parser")
        text = "Meaningful content found here."
        result = ensure_body_has_words(soup, text)
        self.assertEqual(result, text)

    def test_ensure_body_has_words_fallback(self):
        """Test fallback to soup text if body text is empty."""
        soup = BeautifulSoup(
            "<p>Fallback content that is meaningful enough.</p>", "html.parser"
        )
        text = ""
        result = ensure_body_has_words(soup, text)
        self.assertIn("Fallback content", result)

    @patch('scraper.search_urls')
    @patch('scraper.scrape_page')
    def test_process_scraping_queue(self, mock_scrape, mock_search):
        """Test the scraping queue processing logic."""
        mock_search.return_value = ["http://example.com"]
        mock_scrape.return_value = {
            "url": "http://example.com", "title": "Test", "body": "Body"
        }

        # We need to mock NUM_RESULTS or pass it? process_scraping_queue uses global NUM_RESULTS.
        # Ideally we should be able to configure it, but for now we can mock the loop condition
        # or just run it. Since NUM_RESULTS is 30, we need to provide enough data or it will
        # try to search more.

        # Let's mock search_urls to return empty list after first call so it breaks the loop
        # (it breaks if no new urls)
        mock_search.side_effect = [["http://example.com"], []]

        # But wait, if not new_urls breaks the loop.

        results = process_scraping_queue(["http://example.com"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['url'], "http://example.com")

if __name__ == '__main__':
    unittest.main()

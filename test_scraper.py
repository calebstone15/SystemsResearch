"""
Unit tests for the scraper module.
"""
import unittest
from unittest.mock import patch
from bs4 import BeautifulSoup
from scraper import clean_text, ensure_body_has_words, process_scraping_queue

class TestScraper(unittest.TestCase):
    """
    Test suite for the scraper module.
    """

    def test_clean_text(self):
        """
        Test that clean_text correctly cleans and keeps long enough sentences.
        """
        # clean_text splits by '.' and filters out short sentences (<20 chars).
        # "This is a test" is < 20 chars, so it might return empty.
        raw_text_long = (
            "   This is a longer sentence that should be kept because it is long enough.   "
        )
        cleaned = clean_text(raw_text_long)
        self.assertEqual(
            cleaned,
            "This is a longer sentence that should be kept because it is long enough."
        )

    def test_clean_text_removes_tags(self):
        """
        Test that clean_text removes HTML tags and returns empty if text is too short.
        """
        raw_text = "<p>Clean me</p><style>body {color: red;}</style>"
        # "Clean me" is short, so it returns ""
        cleaned = clean_text(raw_text)
        self.assertEqual(cleaned, "")

    def test_ensure_body_has_words(self):
        """
        Test that ensure_body_has_words returns the text if it has meaningful content.
        """
        soup = BeautifulSoup("<p>Some fallback text here</p>", "html.parser")
        text = "Meaningful content found here."
        result = ensure_body_has_words(soup, text)
        self.assertEqual(result, text)

    def test_ensure_body_has_words_fallback(self):
        """
        Test that ensure_body_has_words falls back to soup text if primary text is empty.
        """
        soup = BeautifulSoup(
            "<p>Fallback content that is meaningful enough.</p>",
            "html.parser"
        )
        text = ""
        result = ensure_body_has_words(soup, text)
        self.assertIn("Fallback content", result)

    @patch('scraper.search_urls')
    @patch('scraper.scrape_page')
    def test_process_scraping_queue(self, mock_scrape, mock_search):
        """
        Test process_scraping_queue handles URLs and scraping correctly.
        """
        # Setup mocks
        mock_search.return_value = [] # Should not be called if we don't run out of URLs
        mock_scrape.return_value = {
            "url": "http://example.com",
            "title": "Test",
            "body": "Body"
        }

        # We pass target_results=1
        results = process_scraping_queue(
            urls=["http://example.com"],
            target_results=1,
            keywords=["test"]
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['url'], "http://example.com")

        # Verify scrape_page was called once
        mock_scrape.assert_called_once()

        # Verify search_urls was NOT called because we had enough URLs
        mock_search.assert_not_called()

if __name__ == '__main__':
    unittest.main()

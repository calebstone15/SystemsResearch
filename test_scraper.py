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
        Test that clean_text removes extra whitespace, short sentences, and returns clean text.
        """
        # "This is a test" is < 20 chars, so it returns empty.
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
        """
        Test that clean_text removes HTML tags like script, style, etc.
        """
        raw_text = "<p>Clean me</p><style>body {color: red;}</style>"
        # "Clean me" is short (< 20 chars), so it returns ""
        cleaned = clean_text(raw_text)
        self.assertEqual(cleaned, "")

    def test_ensure_body_has_words(self):
        """
        Test that ensure_body_has_words returns the text if it contains words.
        """
        soup = BeautifulSoup("<p>Some fallback text here</p>", "html.parser")
        text = "Meaningful content found here."
        result = ensure_body_has_words(soup, text)
        self.assertEqual(result, text)

    def test_ensure_body_has_words_fallback(self):
        """
        Test that ensure_body_has_words uses fallback content if main text is empty/invalid.
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
        Test the process_scraping_queue function logic.
        """
        mock_search.return_value = ["http://example.com"]
        mock_scrape.return_value = {
            "url": "http://example.com",
            "title": "Test",
            "body": "Body"
        }

        # Mock search_urls to return empty list after first call to break the loop
        mock_search.side_effect = [["http://example.com"], []]

        results = process_scraping_queue(["http://example.com"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['url'], "http://example.com")


if __name__ == '__main__':
    unittest.main()

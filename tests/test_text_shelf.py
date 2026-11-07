"""Tests for the FoxVC text shelf."""

import unittest

from engine.shelves.text import get_text_shelf


class TestTextShelf(unittest.TestCase):
    def setUp(self):
        self.text = get_text_shelf()

    def test_unicode_normalization_and_case_folding(self):
        self.assertEqual(self.text["normalizeText"]("e\\u0301"), "é")
        self.assertEqual(self.text["normalizeText"]("é", "NFD"), "e\\u0301")
        self.assertEqual(self.text["caseFold"]("Straße"), "strasse")

    def test_word_and_line_counts(self):
        self.assertEqual(self.text["wordCount"]("  one\\ttwo\\nthree  "), 3)
        self.assertEqual(self.text["lineCount"](""), 0)
        self.assertEqual(self.text["lineCount"]("one\\ntwo"), 2)

    def test_truncate_includes_suffix_in_limit(self):
        self.assertEqual(self.text["truncateText"]("FoxVC language", 8), "FoxVC l…")
        self.assertEqual(self.text["truncateText"]("Fox", 8), "Fox")
        self.assertEqual(self.text["truncateText"]("FoxVC", 2, "..."), "..")

    def test_wrap_validates_width(self):
        wrapped = self.text["wrapText"]("one two three", 7)
        self.assertEqual(wrapped, "one two\\nthree")
        with self.assertRaises(ValueError):
            self.text["wrapText"]("text", 0)

    def test_unicode_slug(self):
        self.assertEqual(self.text["slugify"]("Crème Brûlée!"), "creme-brulee")
        self.assertEqual(self.text["slugify"]("नमस्ते दुनिया"), "नमसत-दनय")

    def test_code_point_helpers(self):
        self.assertEqual(self.text["codePointAt"]("A🦊", 1), 0x1F98A)
        self.assertEqual(self.text["codePointAt"]("A", 4), -1)
        self.assertEqual(self.text["fromCodePoint"](0x1F98A), "🦊")
        with self.assertRaises(ValueError):
            self.text["fromCodePoint"](0xD800)

    def test_length_reverse_and_character_classes(self):
        self.assertEqual(self.text["textLength"]("A🦊"), 2)
        self.assertEqual(self.text["reverseText"]("fox"), "xof")
        self.assertTrue(self.text["isAlpha"]("नमस्ते"))
        self.assertTrue(self.text["isDigit"]("१२३"))
        self.assertTrue(self.text["isWhitespace"](" \\t"))
        self.assertFalse(self.text["isAlpha"](""))

    def test_public_api_is_stable(self):
        expected = {
            "normalizeText", "caseFold", "wordCount", "lineCount",
            "truncateText", "wrapText", "slugify", "textLength",
            "codePointAt", "fromCodePoint", "reverseText", "isAlpha",
            "isDigit", "isWhitespace",
        }
        self.assertEqual(set(self.text), expected)


if __name__ == "__main__":
    unittest.main()

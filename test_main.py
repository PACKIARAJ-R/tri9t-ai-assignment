
import unittest

from main import make_hash, is_heading


class TestPDFParser(unittest.TestCase):

    def test_hash_is_consistent(self):
        """Same text should produce the same hash."""
        self.assertEqual(
            make_hash("Device Overview"),
            make_hash("Device Overview")
        )

    def test_hash_ignores_extra_whitespace(self):
        """Extra whitespace should not change the hash."""
        self.assertEqual(
            make_hash("Device   Overview"),
            make_hash("Device Overview")
        )

    def test_detects_real_section_heading(self):
        """A genuine numbered heading should be recognized."""
        self.assertTrue(
            is_heading("1 Device Overview", None)
        )

    def test_rejects_classification_list_item(self):
        """Classification items should not be sections."""
        self.assertFalse(
            is_heading(
                "4 Hypertension Stage 2: systolic ≥ 140 or diastolic ≥ 90",
                None
            )
        )


if __name__ == "__main__":
    unittest.main()

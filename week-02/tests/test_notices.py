import unittest

from notices import SCHEMA_VERSION, load_corpus, load_schema, validate_notice


VALID = {
    "schema_version": "1.0",
    "notice_id": "N001",
    "domain": "example.com",
    "notice_type": "renewal",
    "severity": "info",
    "due_date": "2026-03-01",
    "summary": "Renewal is due soon.",
}


class TestNotices(unittest.TestCase):
    def test_corpus_has_50_unique_notices(self):
        corpus = load_corpus()
        notices = corpus["notices"]
        self.assertEqual(len(notices), 50)
        self.assertEqual(len({n["id"] for n in notices}), 50)

    def test_notices_have_text(self):
        for notice in load_corpus()["notices"]:
            self.assertTrue(notice["text"].strip())

    def test_corpus_is_flagged_as_synthetic(self):
        self.assertIn("synthetic", load_corpus()["source"].lower())

    def test_schema_is_versioned(self):
        schema = load_schema()
        self.assertEqual(schema["properties"]["schema_version"]["const"], SCHEMA_VERSION)

    def test_valid_record(self):
        self.assertTrue(validate_notice(VALID))

    def test_rejects_unknown_type(self):
        self.assertFalse(validate_notice({**VALID, "notice_type": "bogus"}))

    def test_rejects_missing_field(self):
        record = dict(VALID)
        del record["domain"]
        self.assertFalse(validate_notice(record))

    def test_rejects_wrong_version(self):
        self.assertFalse(validate_notice({**VALID, "schema_version": "2.0"}))


if __name__ == "__main__":
    unittest.main()

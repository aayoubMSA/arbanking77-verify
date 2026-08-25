import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "arbanking77_verify.py"
spec = importlib.util.spec_from_file_location("arbanking77_verify", MODULE_PATH)
verify = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(verify)


class VerifyUnitTests(unittest.TestCase):
    def test_git_blob_sha1_known_value(self):
        self.assertEqual(
            verify.git_blob_sha1(b"hello\n"),
            "ce013625030ba8dba906f756967f9e9ca394464a",
        )

    def test_multiset_preserves_multiplicity(self):
        result = verify.compare_multisets(
            ["a", "a", "b"], ["a", "b", "b"], "exact"
        )
        self.assertEqual(result["shared_multiset_rows"], 2)
        self.assertEqual(result["historical_unmatched"], 1)
        self.assertEqual(result["current_only"], 1)

    def test_nfkc_whitespace(self):
        self.assertEqual(verify.normalize("Ａ  \nB", "nfkc_ws"), "A B")

    def test_arabic_light(self):
        self.assertEqual(verify.normalize("إِلَى", "arabic_light"), "الي")

    def test_punctuation_layer_is_cumulative(self):
        base = verify.normalize("مرحبا، يا صديقي!", "arabic_light")
        punct = verify.normalize("مرحبا، يا صديقي!", "arabic_light_punct")
        self.assertNotEqual(base, punct)
        self.assertEqual(punct, "مرحبا يا صديقي")

    def test_utf8_bom_csv(self):
        data = "\ufeffQuery_ID,Query\n1,مرحبا\n2,أهلا\n".encode("utf-8")
        rows = verify.records_from_csv(data, "Query", "sample")
        self.assertEqual(rows, ["مرحبا", "أهلا"])

    def test_lfs_pointer_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "pointer.csv"
            path.write_bytes(
                b"version https://git-lfs.github.com/spec/v1\n"
                b"oid sha256:0123456789abcdef\n"
                b"size 123\n"
            )
            source = {"source_id": "lfs", "path": str(path)}
            with self.assertRaises(verify.VerifyError):
                verify.obtain_source_bytes(source, Path(td) / "cache", offline=False)

    def test_profile_requires_exactly_one_locator(self):
        profile = {
            "schema_version": "1.0",
            "profile_id": "x",
            "benchmark": "b",
            "state_role": "r",
            "records": {"text_column": "text"},
            "sources": [
                {
                    "source_id": "s",
                    "url": "https://example.org/a",
                    "path": "a",
                }
            ],
        }
        with self.assertRaises(verify.VerifyError):
            verify.validate_profile(profile)


if __name__ == "__main__":
    unittest.main()

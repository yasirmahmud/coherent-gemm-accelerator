"""Mutate retained passing evidence; independent mutation must remain failing."""
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("repeated", ROOT / "scripts/summarize_repeated.py")
repeated = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repeated)
FIXTURE = ROOT / "results/diagnostics/repeated_n24_reps3_base"


class RepeatedValidation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "run"
        shutil.copytree(FIXTURE, self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def change_log(self, old, new):
        p = self.path / "gem5-accel.log"
        text = p.read_text()
        self.assertIn(old, text)
        p.write_text(text.replace(old, new, 1))

    def reject(self):
        with self.assertRaises((ValueError, OSError)):
            repeated.validate_run(self.path, 3)

    def test_matched(self):
        self.assertEqual(len(repeated.validate_run(self.path, 3)["calls"]), 3)

    def test_expected_required(self):
        with self.assertRaises(ValueError):
            repeated.validate_run(self.path)

    def test_missing_call(self):
        self.change_log("GEMM call 1 passed: 0 mismatches", "")
        self.reject()

    def test_duplicate(self):
        self.change_log("GEMM call 1 passed: 0 mismatches", "GEMM call 0 passed: 0 mismatches")
        self.reject()

    def test_out_of_order(self):
        p = self.path / "gem5-accel.log"
        text = p.read_text().replace("GEMM call 0 ", "GEMM call SWAP ", 1)
        text = text.replace("GEMM call 1 ", "GEMM call 0 ", 1)
        p.write_text(text.replace("GEMM call SWAP ", "GEMM call 1 ", 1))
        self.reject()

    def test_missing_interval(self):
        p = self.path / "m5out-cache/stats.txt"
        p.write_text(p.read_text().replace("# Stats desc: gemm invocation", "", 1))
        self.reject()

    def test_missing_completion(self):
        p = self.path / "m5out-cache/stats.txt"
        p.write_text(p.read_text().replace("datapath completed.", "unexpected", 1))
        self.reject()

    def test_invalid_hash(self):
        (self.path / "trace.sha256").write_text("not-a-hash dynamic_trace.gz\n")
        self.reject()

    def test_missing_hash(self):
        (self.path / "trace.sha256").unlink()
        self.reject()

    def test_nonzero_mismatch(self):
        self.change_log("GEMM call 1 passed: 0 mismatches", "GEMM call 1 FAILED: 2 mismatches")
        self.reject()

    def test_independent_mutation(self):
        with self.assertRaisesRegex(ValueError, "Failed correctness"):
            repeated.validate_run(ROOT / "results/diagnostics/repeated_n24_reps3_base_independent", 3)

    def test_missing_exit(self):
        p = self.path / "gem5-accel.log"
        p.write_text(p.read_text().rsplit("Exiting @ tick", 1)[0])
        self.reject()

    def test_wrong_expected_count(self):
        with self.assertRaises(ValueError):
            repeated.validate_run(self.path, 4)

    def test_truncated_stats(self):
        p = self.path / "m5out-cache/stats.txt"
        p.write_text(p.read_text().rsplit("---------- End Simulation Statistics", 1)[0])
        self.reject()


if __name__ == "__main__":
    unittest.main()

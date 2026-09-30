"""Ensure real simulation evidence cannot pass validation when incomplete or altered."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from summarize_cache_bandwidth import verify


class CacheBandwidthEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ROOT / "results/cache_bandwidth/n24_20260930"
        cls.rows = verify(cls.source)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cohort = Path(self.temp.name) / "cohort"
        shutil.copytree(str(self.source), str(self.cohort))

    def test_complete_cohort_and_segment_sum(self):
        self.assertEqual(len(self.rows), 6)
        for row in self.rows:
            self.assertEqual(row["offload_ticks"], row["completion_ticks"] + row["return_segment_ticks"])
            self.assertGreater(row["return_segment_ticks"], 0)

    def test_missing_point_rejected(self):
        shutil.rmtree(str(self.cohort / "points/tiled4_bw2"))
        with self.assertRaisesRegex(ValueError, "six"):
            verify(self.cohort)

    def test_incomplete_runner_rejected(self):
        (self.cohort / "provenance/completed-at.txt").unlink()
        with self.assertRaisesRegex(ValueError, "did not complete"):
            verify(self.cohort)

    def test_wrong_effective_bandwidth_rejected(self):
        path = self.cohort / "points/base_bw1/full/m5out/config.ini"
        path.write_text(path.read_text().replace("cacheBandwidth=1", "cacheBandwidth=4"))
        with self.assertRaisesRegex(ValueError, "effective bandwidth"):
            verify(self.cohort)

    def test_uncontrolled_cpu_change_rejected(self):
        path = self.cohort / "points/base_bw2/full/m5out/config.ini"
        path.write_text(path.read_text().replace("numROBEntries=192", "numROBEntries=128"))
        with self.assertRaisesRegex(ValueError, "Uncontrolled configuration"):
            verify(self.cohort)

    def test_missing_host_completion_rejected(self):
        path = self.cohort / "points/base_bw1/invocation/m5out/stats.txt"
        path.write_text(path.read_text().replace("# Stats desc: gemm invocation", "# Stats desc: unlabelled"))
        with self.assertRaisesRegex(ValueError, "host completion"):
            verify(self.cohort)

    def test_failed_correctness_rejected(self):
        path = self.cohort / "points/base_bw1/full/gem5.log"
        path.write_text(path.read_text().replace("GEMM passed: 0 mismatches", "GEMM FAILED: 1 mismatches"))
        with self.assertRaisesRegex(ValueError, "failure"):
            verify(self.cohort)

    def test_wrong_trace_hash_rejected(self):
        path = self.cohort / "inputs/base/trace.sha256"
        path.write_text("0" * 64 + "  dynamic_trace.gz\n")
        with self.assertRaisesRegex(ValueError, "Hash mismatch"):
            verify(self.cohort)


if __name__ == "__main__":
    unittest.main()

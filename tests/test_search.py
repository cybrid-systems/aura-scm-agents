"""Tests for the swarm search harness (aura/search.aura, scripts/run_search.py).

Pure-Python tests always run. End-to-end tests need AURA_BIN + AURA_STDLIB (and AURA_LIBDIR
or docker, see README) and are skipped otherwise. The e2e run uses a tiny budget; set
SCM_TEST_COMMIT=0 to skip the (slow, single-writer) commit + rollback drills.
"""
import os, sys, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import run_search  # noqa: E402

SMALL = {"SCM_PSO_GENS": "2", "SCM_ACO_ITERS": "2", "SCM_EVAL_REPS": "1"}


class TestParse(unittest.TestCase):
    def test_parse_kv_and_prov(self):
        kv, prov = run_search.parse(
            "@@search.n=4\n@@prov=7|claim-root-cause|pso|0.2|a;b|none|pass|ok|1.5|0.7;1;2;0.5|3|\n"
            "@@front.x.member=1|2\n@@front.x.member=3|4\nnoise line\n")
        self.assertEqual(kv["search.n"], "4")
        self.assertEqual(kv["front.x.member"], ["1|2", "3|4"])
        self.assertEqual(prov[0]["policy"], "claim-root-cause")
        self.assertEqual(prov[0]["gate"], "pass")
        self.assertEqual(prov[0]["metrics"], "0.7;1;2;0.5")

    def test_short_prov_row_is_padded(self):
        _, prov = run_search.parse("@@prov=1|p|pso\n")
        self.assertEqual(prov[0]["error"], "")

    def test_summary_speedup_and_determinism(self):
        def run(n, ms, fp):
            kv = {"search.wall-ms": str(ms), "fingerprint": fp, "search.evals": "10"}
            for p in run_search.POLS:
                kv.update({f"tmpl.{p}.v1": "1;2", f"tmpl.{p}.v1-fit": "0", f"tmpl.{p}.v2": "1;2",
                           f"tmpl.{p}.v2-fit": "1", f"best.{p}.metrics": "1;2", f"best.{p}.fit": "2"})
            return {"n": n, "rc": 0, "process_s": 1.0, "kv": kv, "prov": [], "stderr_tail": []}
        s = run_search.summarize([run(0, 1000, "A"), run(4, 250, "A")], None)
        self.assertTrue(s["deterministic_across_n"])
        self.assertEqual(s["scaling"][1]["speedup_vs_serial"], 4.0)
        s2 = run_search.summarize([run(0, 1000, "A"), run(4, 250, "B")], None)
        self.assertFalse(s2["deterministic_across_n"])


@unittest.skipUnless(os.environ.get("AURA_BIN") and os.environ.get("AURA_STDLIB"), "AURA_BIN/AURA_STDLIB not set")
class TestSearchE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.update(SMALL)
        commit = os.environ.get("SCM_TEST_COMMIT", "1") == "1"
        cls.serial = run_search.run_once(0, False, 600, {})
        cls.fiber = run_search.run_once(4, commit, 1800, {})
        cls.commit = commit

    def test_both_complete(self):
        self.assertEqual(self.serial["rc"], 0, self.serial["stderr_tail"])
        self.assertEqual(self.fiber["rc"], 0, self.fiber["stderr_tail"])
        self.assertTrue(self.fiber["kv"].get("search.wall-ms"))

    def test_deterministic_across_serial_and_fibers(self):
        self.assertTrue(self.serial["kv"].get("fingerprint"))
        self.assertEqual(self.serial["kv"]["fingerprint"], self.fiber["kv"]["fingerprint"])

    def test_templates_match_hand_written_metrics(self):
        kv = self.serial["kv"]
        nums = lambda k: [round(float(x), 3) for x in kv[k].split(";")]
        self.assertEqual(nums("tmpl.should-arbitrate?.v1"), [28, 20, 0.714, 1.0])
        self.assertEqual(nums("tmpl.should-arbitrate?.v2"), [7, 0, 0.0, 0.875])
        self.assertEqual(nums("tmpl.claim-root-cause.v2"), [1.0, 9, 5210000, 1.0])
        self.assertEqual(nums("tmpl.expedite-response.v2"), [1, 6, 34, 3, 1800500, 40])  # cost model v2

    def test_every_injected_defect_rejected_and_no_clean_rejects(self):
        for r in (self.serial, self.fiber):
            for row in r["prov"]:
                if row["noise"] != "none":
                    self.assertEqual(row["gate"], "reject", row)
                elif row["gate"] == "reject":
                    self.fail(f"clean candidate rejected: {row}")

    def test_provenance_for_every_attempt(self):
        self.assertEqual(len(self.fiber["prov"]), int(self.fiber["kv"]["search.evals"]))

    def test_overlay_never_commits(self):
        ov = self.fiber["kv"]["search.overlay"]
        self.assertIn("commits=0", ov)
        self.assertIn("active=0", ov)

    def test_commit_and_rollback(self):
        if not self.commit:
            self.skipTest("SCM_TEST_COMMIT=0")
        kv = self.fiber["kv"]
        for p in run_search.POLS:
            self.assertEqual(kv[f"commit.{p}.rebind"], "ok")
            self.assertEqual(kv[f"commit.{p}.fiber-metrics-equal"], "#t")
            self.assertEqual(kv[f"commit.{p}.v1-restored-after-v2"], "#t")
            self.assertEqual(kv[f"rollback.{p}.restored-metrics-equal"], "#t")
            self.assertEqual(kv[f"rollback.{p}.restored-source-equal"], "#t")
            self.assertEqual(kv[f"rollback.{p}.broken-unchanged"], "#t")
            self.assertEqual(kv[f"rollback.{p}.broken-guard"], "rejected")


if __name__ == "__main__":
    unittest.main()

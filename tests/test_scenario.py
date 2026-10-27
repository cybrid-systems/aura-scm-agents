"""Tests for aura-scm-agents.

Pure-Python tests always run. End-to-end tests run the Aura demo and need AURA_BIN
(path to an Aura build-rel/aura; see README) -- they are skipped otherwise.
"""
import os, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import run_demo  # noqa: E402


class TestData(unittest.TestCase):
    def test_generated_data_is_deterministic_and_committed(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "data.aura"
            subprocess.run([sys.executable, str(REPO / "scripts/gen_data.py")], check=True,
                           env={**os.environ, "SCM_DATA_OUT": str(out)}, capture_output=True)
            self.assertEqual(out.read_text(), (REPO / "aura/data.aura").read_text())

    def test_policy_files_exist(self):
        for p in ("should-arbitrate", "claim-root-cause", "expedite-response"):
            for v in ("v1", "v2", "bad"):
                self.assertTrue((REPO / f"aura/policies/{p}.{v}.aura").exists(), (p, v))

    def test_parse(self):
        r = run_demo.parse("@@a=1\n@@pkg.C.action=x|y\n@@pkg.C.action=z\nnoise\n")
        self.assertEqual(r["a"], "1")
        self.assertEqual(r["pkg.C.action"], ["x|y", "z"])


@unittest.skipUnless(os.environ.get("AURA_BIN"), "AURA_BIN not set")
class TestDemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stdout, stderr, rc, _ = run_demo.run()
        cls.rc, cls.r, cls.stderr = rc, run_demo.parse(stdout), stderr

    def test_completes(self):
        self.assertEqual(self.rc, 0, self.stderr[-1000:])
        self.assertEqual(self.r.get("done"), "ok")

    def test_case1_flow(self):
        P = "pkg.CASE-1"
        self.assertEqual(self.r[f"{P}.decision"], "approved")
        self.assertEqual(self.r[f"{P}.arbitrate"], "#t")
        self.assertEqual(int(self.r[f"{P}.impacted"]), 7)
        self.assertEqual(int(self.r[f"{P}.max-hop"]), 3)
        self.assertTrue(any(a.startswith("BRK-200|expedite-review") for a in self.r[f"{P}.action"]))
        self.assertTrue(self.r.get(f"{P}.conflict"))
        self.assertIn("status=partial ok=7 err=1", self.r[f"{P}.forensics-batch"])
        # every non-monitor action executed exactly once (lost scope tasks are recovered inline)
        n_exec = sum(1 for a in self.r[f"{P}.action"] if "|monitor|" not in a)
        self.assertEqual(int(self.r[f"{P}.exec-done"]), n_exec)

    def test_case2_reject_cancels(self):
        P = "pkg.CASE-2"
        self.assertEqual(self.r[f"{P}.decision"], "rejected")
        self.assertEqual(int(self.r[f"{P}.exec-done"]), 0)
        self.assertIn("cancelled-count=", self.r[f"{P}.cancel"])

    def test_evolution(self):
        r = self.r
        for pol in ("should-arbitrate?", "claim-root-cause", "expedite-response"):
            self.assertEqual(r[f"evo.{pol}.v2.gate"], "pass", pol)
            self.assertEqual(r[f"evo.{pol}.bad.gate"], "fail", pol)
            self.assertEqual(r[f"evo.{pol}.final-equals-v2"], "#t", pol)
        self.assertLess(float(r["evo.should-arbitrate?.v2.metrics.false-arbitration-rate"]),
                        float(r["evo.should-arbitrate?.v1.false-arbitration-rate"]))
        self.assertGreater(int(r["evo.claim-root-cause.v2.metrics.recovered"]), int(r["evo.claim-root-cause.v1.recovered"]))
        self.assertLess(int(r["evo.expedite-response.v2.metrics.supplier-switches"]),
                        int(r["evo.expedite-response.v1.supplier-switches"]))
        self.assertLessEqual(int(r["evo.expedite-response.v2.metrics.stockouts"]), int(r["evo.expedite-response.v1.stockouts"]))
        self.assertTrue(r["evo.parse-gate"].startswith("rejected"))
        self.assertIn("增加市场信号不匹配作为预测误差判定条件", r["evo.mutation-log"])

    def test_case3_uses_evolved_policy(self):
        acts = self.r["pkg.CASE-3.action"]
        self.assertFalse(any("|alt-supplier|" in a for a in acts))
        self.assertLess(int(self.r["pkg.CASE-3.plan-cost"]), int(self.r["pkg.CASE-1.plan-cost"]))

    def test_audit_trail(self):
        a = self.r["trail.audit"]
        actors = {x.split("|")[2] for x in a}
        self.assertTrue({"supervisor", "demand", "risk", "forensics", "claims", "human"} <= actors)
        self.assertTrue(any("ast:restore" in x for x in a))


if __name__ == "__main__":
    unittest.main()

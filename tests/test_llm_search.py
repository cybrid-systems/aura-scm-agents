"""Tests for the LLM + swarm harness (scripts/llm_search.py, aura/llm-search.aura) with a mocked LLM.

Pure-Python tests always run (no network, no keys). The end-to-end test needs AURA_BIN + AURA_STDLIB
(see README) and is skipped otherwise; it uses `--models mock` (deterministic answers: v2, a truncated
form, a fenced threshold tweak of v1, and prose) and tiny search budgets.
"""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import llm_search as L  # noqa: E402

GOOD = "(define (claim-root-cause e) (cond ((forecast-bias? e) 'demand-forecast-error) (else 'unknown)))"


class TestParseProposal(unittest.TestCase):
    def test_plain_json(self):
        st, r, s = L.parse_proposal(json.dumps({"reason": "why", "source": GOOD}), "claim-root-cause")
        self.assertEqual((st, r, s), ("valid", "why", GOOD))

    def test_fenced_and_surrounding_prose(self):
        txt = "Here you go:\n```json\n" + json.dumps({"reason": "x", "source": GOOD}) + "\n```\nthanks"
        self.assertEqual(L.parse_proposal(txt, "claim-root-cause")[0], "valid")
        self.assertEqual(L.parse_proposal("Sure. " + json.dumps({"reason": "x", "source": GOOD}), "claim-root-cause")[0], "valid")

    def test_failures(self):
        P = "claim-root-cause"
        self.assertEqual(L.parse_proposal("", P)[0], "no-json")
        self.assertEqual(L.parse_proposal("no idea", P)[0], "no-json")
        self.assertEqual(L.parse_proposal(json.dumps({"reason": "r"}), P)[0], "no-source")
        self.assertEqual(L.parse_proposal(json.dumps({"reason": "r", "source": GOOD[:-1]}), P)[0], "unbalanced")
        self.assertEqual(L.parse_proposal(json.dumps({"reason": "r", "source": GOOD + ")"}), P)[0], "unbalanced")
        wrong = GOOD.replace("claim-root-cause e", "claim-root-cause-2 e")
        self.assertEqual(L.parse_proposal(json.dumps({"reason": "r", "source": wrong}), P)[0], "wrong-form")
        two = GOOD + " (define (helper x) x)"
        self.assertEqual(L.parse_proposal(json.dumps({"reason": "r", "source": "(begin " + two + ")"}), P)[0], "wrong-form")

    def test_balanced_ignores_parens_in_strings(self):
        self.assertTrue(L.balanced('(f "a)(" (g))'))
        self.assertFalse(L.balanced('(f "a)'))
        self.assertFalse(L.balanced("(f) ; comment )"))


class TestAuraText(unittest.TestCase):
    def test_aura_str_escapes(self):
        self.assertEqual(L.aura_str('a"b\\c\n\td\r'), '"a\\"b\\\\c\\n d"')

    def test_props_file_shape(self):
        rows = [dict(model="mock", seed=7, policy="claim-root-cause", k=1, reason='say "hi"', aura_source=GOOD)]
        txt = L.props_file(["mock"], rows)
        self.assertIn('(define LLM-MODELS (list "mock"))', txt)
        self.assertIn('(list "mock" 7 "claim-root-cause" 1 "say \\"hi\\""', txt)
        self.assertTrue(L.balanced(txt))

    def test_main_src_commits_only_when_asked(self):
        self.assertNotIn("llm-commit!", L.main_src(["glm"], False))
        m = L.main_src(["glm", "minimax"], True)
        self.assertEqual(m.count('"trial"'), 6)
        self.assertIn('(llm-restore-v1! "minimax")', m)
        self.assertIn('(dump-audit "trail")', m)


class TestPrompt(unittest.TestCase):
    def test_messages_contain_contract_and_no_secrets(self):
        ctx = {"src": GOOD, "metrics": "0.7;23;1;0.5", "fitness": "1.2", "fails": [f"row {i}" for i in range(20)]}
        msgs = L.messages("expedite-response", ctx, 20261028, 3)
        u = msgs[1]["content"]
        self.assertIn("150000", u)               # cost model is explained
        self.assertIn("(sample 20261028-3)", u)  # nonce per sample
        self.assertEqual(sum(1 for line in u.splitlines() if line.startswith("- row")), 8)
        for f in ("/home/box/.glm-key",):
            if os.path.exists(f):
                key = Path(f).read_text().strip()
                self.assertNotIn(key, json.dumps(msgs))

    def test_gate_ok(self):
        self.assertTrue(L.gate_ok("should-arbitrate?", [1, 2, 0.5, 1.0], [1, 1, 0.4, 0.8]))
        self.assertFalse(L.gate_ok("should-arbitrate?", [1, 2, 0.5, 1.0], [1, 1, 0.4, 0.7]))
        self.assertFalse(L.gate_ok("claim-root-cause", [0.7, 1, 100, 0.5], [0.8, 1, 90, 0.5]))
        self.assertTrue(L.gate_ok("expedite-response", [1, 1, 1, 5, 100, 40], [1, 1, 1, 5, 90, 40]))
        self.assertFalse(L.gate_ok("expedite-response", [1, 1, 1, 5, 100, 40], []))


HAVE_AURA = bool(os.environ.get("AURA_BIN")) and bool(os.environ.get("AURA_STDLIB"))


@unittest.skipUnless(HAVE_AURA, "needs AURA_BIN and AURA_STDLIB")
class TestEndToEndMock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = Path(tempfile.mkdtemp(prefix="llmsearch-"))
        p = subprocess.run([sys.executable, str(REPO / "scripts/llm_search.py"), "--models", "mock", "--seeds", "1", "--k", "4",
                            "--n", "4", "--small", "--out", str(cls.out), "--cache", str(cls.out / "cache")],
                           capture_output=True, text=True, timeout=900,
                           env=dict(os.environ, SCM_LLM_BUILD_TAG="test-"))
        cls.proc = p
        cls.res = json.loads((cls.out / "llm-search.json").read_text()) if p.returncode == 0 else None
        cls.prov = [json.loads(l) for l in (cls.out / "llm-search-provenance.jsonl").read_text().splitlines()] if p.returncode == 0 else []

    def test_run_ok(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stdout[-2000:] + self.proc.stderr[-2000:])

    def test_all_arms_on_holdout(self):
        for pol in L.POLS:
            for arm in ("v1", "v2", "swarm", "llm:mock", "llm+swarm:mock"):
                self.assertIn(f"{arm}|{pol}", self.res["arms"])
        # v1 and v2 are fixed policies: their hold-out fitness does not depend on the search
        self.assertAlmostEqual(self.res["arms"]["v1|claim-root-cause"]["holdout_mean"], 1.108, places=3)
        self.assertAlmostEqual(self.res["arms"]["v2|should-arbitrate?"]["holdout_mean"], 0.889, places=3)

    def test_mock_status_and_gate(self):
        m = self.res["models"]["mock"]
        self.assertEqual(m["calls"], 12)
        self.assertEqual(m["status"].get("valid"), 6)   # v2 + fenced tweak per policy
        self.assertEqual(m["gate_total"], 12)          # every proposal, broken or not, goes through the gate
        self.assertLessEqual(m["gate_pass"], 6)

    def test_llm_plus_swarm_never_worse_on_train(self):
        for pol in L.POLS:
            a = self.res["arms"][f"llm+swarm:mock|{pol}"]["per_seed"][0]["train_fit"]
            b = self.res["arms"][f"llm:mock|{pol}"]["per_seed"][0]["train_fit"]
            self.assertGreaterEqual(a + 1e-9, b)

    def test_commit_provenance(self):
        commits = [r for r in self.prov if r["kind"] == "commit"]
        self.assertEqual(len(commits), 6)   # trial + keep per policy
        for c in commits:
            self.assertEqual(c["gate"], "pass")
            self.assertEqual(c["fiber_metrics_equal"], "#t")
            self.assertIn("LLM mock:", c["reason"])
            self.assertIn("llm-proposal #", c["reason"])
        self.assertEqual(self.res["commits"]["llmcommit.restore.mock"], "v1-metrics-restored")
        self.assertTrue(self.res["audit_trail"])
        calls = [r for r in self.prov if r["kind"] == "llm-call"]
        self.assertEqual(len(calls), 12)
        self.assertTrue(all(r["attempt"] is not None for r in calls))


if __name__ == "__main__":
    unittest.main()

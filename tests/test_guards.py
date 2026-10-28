"""Domain guards (aura/policies/guards.v1.aura): workspace EDSL invariants in the business gate.

The Aura test (needs AURA_BIN + AURA_STDLIB, skipped otherwise) installs the workspace, audits
known sources against the guards, and checks that the guards are queryable and versioned
(mutate:rebind of a guard constant with a reason -> mutation log; ast:restore undoes it).
"""
import os, subprocess, sys, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import llm_search as L  # noqa: E402
from run_search import parse  # noqa: E402

# the MiniMax+swarm expedite winner of the 3-seed run (seed 20261028): high risk -> monitor
OVERFIT = ("(define (expedite-response risk-level inventory-days) (cond ((and (>= (risk-rank risk-level) (risk-rank (quote high)))) "
           "(list (quote monitor))) ((>= (risk-rank risk-level) (risk-rank (quote medium))) (list (quote alert-planner) "
           "(quote immediate-expedite-review))) (else (list (quote monitor)))))")
CLAIMS_005 = ("(define (claim-root-cause expedite-event) (cond ((and (edi-increase? expedite-event) (supplier-lead-time-miss? expedite-event)) "
              "'supplier-delay) ((or (market-signal-mismatch? expedite-event) (and (forecast-bias? expedite-event) "
              "(> (bias-amount expedite-event) 0.05))) 'demand-forecast-error) (else 'unknown)))")
ARB_NOFROZEN = "(define (should-arbitrate? edi-change inventory-exposure) (and (> (abs (change-pct edi-change)) 0.2) (> inventory-exposure 700000)))"
EXP_CRIT = ("(define (expedite-response risk-level inventory-days) (cond ((>= (risk-rank risk-level) (risk-rank 'high)) (list 'alert-planner 'immediate-expedite-review)) "
            "((>= (risk-rank risk-level) (risk-rank 'medium)) (list 'propose-internal-rebalance)) (else (list 'monitor))))")


def have_aura():
    return bool(os.environ.get("AURA_BIN") and os.environ.get("AURA_STDLIB"))


class TestPairedStats(unittest.TestCase):
    def test_identical_is_p1(self):
        r = L.paired_stats([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        self.assertEqual((r["mean_diff"], r["p_perm"], r["ties"]), (0.0, 1.0, 3))

    def test_all_positive_8_seeds(self):
        r = L.paired_stats([1.0] * 8, [0.0] * 8)
        self.assertAlmostEqual(r["p_perm"], 2 / 256, places=4)   # exact sign-flip test
        self.assertEqual(r["ci95"], [1.0, 1.0])
        self.assertEqual(r["wins"], 8)


@unittest.skipUnless(have_aura(), "needs AURA_BIN and AURA_STDLIB")
class TestGuardsAura(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        audits = [("overfit", "expedite-response", OVERFIT), ("claims005", "claim-root-cause", CLAIMS_005),
                  ("arbnofrozen", "should-arbitrate?", ARB_NOFROZEN), ("expcrit", "expedite-response", EXP_CRIT)]
        main = ["(for-each (lambda (p) (template-check! p)) POLICIES)", "(emit-guard-info!)"]
        main += [f"(guard-audit! {L.aura_str(a)} {L.aura_str(p)} {L.aura_str(s)})" for a, p, s in audits]
        main += ['(emit "q.calls" (query:calls "guard-critical-days"))',
                 '(emit "q.src" (if (string? (current-source :workspace)) (> (string-length (current-source :workspace)) 0) #f))',
                 '(define GS0 (ast:snapshot))',
                 '(define ML0 (let ((l (query :mutation-log 50))) (if (pair? l) (length l) 0)))',
                 '(emit "rb" (mutate:rebind "guard-critical-days" "(define (guard-critical-days) 4.0)" "guards.v1 -> v1.1: critical stock is 4 days"))',
                 '(eval-current)',
                 '(emit "ml.delta" (- (let ((l (query :mutation-log 50))) (if (pair? l) (length l) 0)) ML0))',
                 '(guard-audit! "expcrit4" "expedite-response" (policy-src "expedite-response" "v1"))',
                 '(ast:restore GS0)', '(eval-current)',
                 '(guard-audit! "expcrit-restored" "expedite-response" (policy-src "expedite-response" "v1"))',
                 '(emit "done" "ok")']
        tag = "test-guards"
        (REPO / "build").mkdir(exist_ok=True)
        (REPO / f"build/{tag}-props.aura").write_text("(define LLM-MODELS (list))\n(define LLM-PROPS (list))\n")
        (REPO / f"build/{tag}-main.aura").write_text("\n".join(main) + "\n")
        env = dict(os.environ, SCM_BUILD_NAME=tag, SCM_MAIN=f"build/{tag}-main.aura", SCM_SEARCH_N="0", SCM_EVAL_REPS="1",
                   SCM_EXTRA_MODULES=f"aura/llm-search.aura build/{tag}-props.aura", SCM_TIMEOUT="600")
        p = subprocess.run(["bash", str(REPO / "scripts/run_search.sh")], env=env, capture_output=True, text=True)
        cls.kv, _ = parse(p.stdout)
        cls.rc, cls.err = p.returncode, p.stderr[-2000:]

    def test_ran(self):
        self.assertEqual((self.rc, self.kv.get("done")), (0, "ok"), self.err)

    def test_registry_and_baseline(self):
        self.assertEqual(self.kv["guards.version"], "guards.v1")
        for g in ("exp.high-never-monitor", "exp.critical-alert", "arb.frozen-never", "claims.evidence-not-unknown"):
            self.assertIn(g, self.kv["guards.registry"])
        self.assertIn("exp.critical-alert=4", self.kv["guards.baseline"])      # v1 is legacy: medium < 2 days -> alt supplier
        self.assertIn("exp.high-never-monitor=0", self.kv["guards.baseline"])
        self.assertEqual(self.kv["tmpl.claim-root-cause.v2-guards"], "claims.evidence-not-unknown=0")

    def test_previous_overfit_is_rejected(self):
        a = self.kv["audit.overfit"]
        self.assertIn("business-gate=pass", a)          # the metric gate alone let it through
        self.assertIn("guards=fail:exp.high-never-monitor", a)
        self.assertIn("exp.high-never-monitor=41", a)   # every high-risk grid point

    def test_other_guards(self):
        self.assertIn("guards=fail:claims.evidence-not-unknown", self.kv["audit.claims005"])
        self.assertIn("guards=fail:arb.frozen-never", self.kv["audit.arbnofrozen"])
        # no-regress: medium below 2 days -> rebalance is no worse than v1's alternative supplier
        self.assertIn("guards=pass", self.kv["audit.expcrit"])

    def test_queryable_and_versioned(self):
        self.assertNotIn(self.kv["q.calls"], ("", "()"))
        self.assertEqual(self.kv["q.src"], "#t")
        self.assertEqual(self.kv["rb"], "#t")
        self.assertGreaterEqual(int(self.kv["ml.delta"]), 1)
        self.assertIn("exp.critical-alert=8", self.kv["audit.expcrit4"])     # 4 days: 8 grid points x medium
        self.assertIn("exp.critical-alert=4", self.kv["audit.expcrit-restored"])


if __name__ == "__main__":
    unittest.main()

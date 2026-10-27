#!/usr/bin/env python3
"""Run the deterministic demo (scripts/run.sh) and turn its @@key=value lines into
results/demo.json + results/demo.md.  Usage:  AURA_BIN=... python3 scripts/run_demo.py
"""
import json, os, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MULTI = ("priority", "action", "conflict", "leak-chain", "rule", "audit")


def run(src="aura/main.aura"):
    t0 = time.time()
    p = subprocess.run([str(REPO / "scripts/run.sh"), src], capture_output=True, text=True, cwd=REPO)
    return p.stdout, p.stderr, p.returncode, time.time() - t0


def parse(stdout):
    out = {}
    for line in stdout.splitlines():
        if not line.startswith("@@") or "=" not in line:
            continue
        k, v = line[2:].split("=", 1)
        if k.rsplit(".", 1)[-1] in MULTI:
            out.setdefault(k, []).append(v)
        else:
            out[k] = v
    return out


def evolution_table(r):
    rows = []
    spec = {"should-arbitrate?": ["arbitrations", "false-arbitrations", "false-arbitration-rate", "recall"],
            "claim-root-cause": ["accuracy", "unknown", "recovered", "recovery-rate"],
            "expedite-response": ["expedites", "supplier-switches", "rebalances", "stockouts", "cost"]}
    for pol, ms in spec.items():
        b = f"evo.{pol}"
        for m in ms:
            rows.append((pol, m, r.get(f"{b}.v1.{m}"), r.get(f"{b}.v2.metrics.{m}"), r.get(f"{b}.bad.metrics.{m}"),
                         r.get(f"{b}.bad.after-rollback.{m}")))
        rows.append((pol, "gate v2 / bad", "", r.get(f"{b}.v2.gate"), r.get(f"{b}.bad.gate"), "restored=" + str(r.get(f"{b}.final-equals-v2"))))
    return rows


def markdown(r, secs):
    L = ["# aura-scm-agents demo results", "", f"wall time: {secs:.1f}s (deterministic; fibers are serialized, see README)", ""]
    for case in ("CASE-1", "CASE-2", "CASE-3"):
        P = f"pkg.{case}"
        if f"{P}.decision" not in r:
            continue
        L += [f"## {case}: decision={r[P + '.decision']} human-required={r[P + '.human-required']}", "",
              f"- exposure {r.get(P + '.exposure')}, arbitrate={r.get(P + '.arbitrate')}, hypothesis: {r.get(P + '.hypothesis')}",
              f"- impacted nodes {r.get(P + '.impacted')} (max hop {r.get(P + '.max-hop')}), plan cost {r.get(P + '.plan-cost')}, expedites {r.get(P + '.expedites')}",
              f"- forensics batch {r.get(P + '.forensics-batch')}, total leakage {r.get(P + '.total-leak')}",
              f"- claims {r.get(P + '.claims')}, recovery opportunity {r.get(P + '.recovery-opportunity')}",
              f"- execution: done {r.get(P + '.exec-done')}, lost-and-recovered {r.get(P + '.exec-lost-recovered')}, cancel {r.get(P + '.cancel')}", "",
              "| node | action | detail | cost |", "|---|---|---|---|"]
        for a in r.get(P + ".action", []):
            L.append("| " + " | ".join(a.split("|")) + " |")
        L.append("")
        for c in r.get(P + ".conflict", []):
            L.append(f"- conflict: {c}")
        for c in r.get(P + ".rule", []):
            L.append(f"- rule: {c}")
        L.append("")
    L += ["## Policy evolution (v1 -> v2 -> bad -> rollback)", "", "| policy | metric | v1 | v2 | bad | after rollback |", "|---|---|---|---|---|---|"]
    for row in evolution_table(r):
        L.append("| " + " | ".join("" if x is None else str(x) for x in row) + " |")
    L += ["", f"parse gate: {r.get('evo.parse-gate')}", "", "## Audit trail", "", "| seq | t-ms | actor | action | detail |", "|---|---|---|---|---|"]
    for a in r.get("trail.audit", []):
        L.append("| " + " | ".join(x.replace("|", "/") for x in a.split("|", 4)) + " |")
    return "\n".join(L) + "\n"


def main():
    stdout, stderr, rc, secs = run(sys.argv[1] if len(sys.argv) > 1 else "aura/main.aura")
    r = parse(stdout)
    out = REPO / "results"
    out.mkdir(exist_ok=True)
    (out / "demo.json").write_text(json.dumps(r, ensure_ascii=False, indent=1))
    (out / "demo.md").write_text(markdown(r, secs))
    ok = rc == 0 and r.get("done") == "ok"
    print(f"rc={rc} done={r.get('done')} keys={len(r)} -> results/demo.json, results/demo.md")
    if not ok:
        print(stderr[-2000:], file=sys.stderr)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

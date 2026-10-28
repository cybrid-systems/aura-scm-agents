#!/usr/bin/env python3
"""Run the fiber-parallel swarm search at several fiber counts and write results/.

  AURA_BIN=... AURA_STDLIB=... [AURA_LIBDIR=...] python3 scripts/run_search.py [--ns 0,1,4,8,16] [--commit-n 8]

N=0 is the serial baseline (no fibers).  Every N runs in a fresh process with the same seed;
the coordinator owns all randomness, so the fingerprint must be identical across N.
The commit/rollback drills run once (at --commit-n), because they are single-writer and
independent of N.  Outputs: results/search.json, results/search.md,
results/search-provenance.jsonl (one line per evaluated candidate of the commit run).
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
POLS = ["should-arbitrate?", "claim-root-cause", "expedite-response"]
MNAMES = {
    "should-arbitrate?": ["arbitrations", "false_arbitrations", "false_alarm_rate", "recall"],
    "claim-root-cause": ["accuracy", "unknown", "recovered", "recovery_rate"],
    "expedite-response": ["expedites", "supplier_switches", "rebalances", "stockouts", "cost"],
}
PROV_FIELDS = ["id", "policy", "stage", "cont", "choices", "noise", "gate", "reason", "fitness", "metrics", "ms", "error"]


def parse(text):
    """@@key=value lines -> dict (repeated keys -> list) + provenance rows."""
    kv, prov = {}, []
    for line in text.splitlines():
        if not line.startswith("@@") or "=" not in line:
            continue
        k, v = line[2:].split("=", 1)
        if k == "prov":
            parts = v.split("|")
            parts += [""] * (len(PROV_FIELDS) - len(parts))
            prov.append(dict(zip(PROV_FIELDS, parts[: len(PROV_FIELDS)])))
            continue
        if k in kv:
            kv[k] = kv[k] + [v] if isinstance(kv[k], list) else [kv[k], v]
        else:
            kv[k] = v
    return kv, prov


def run_once(n, commit, timeout, extra_env):
    env = dict(os.environ, SCM_SEARCH_N=str(n), SCM_COMMIT="1" if commit else "0",
               SCM_TIMEOUT=str(timeout), **extra_env)
    t0 = time.time()
    p = subprocess.run(["bash", str(REPO / "scripts/run_search.sh")], env=env, capture_output=True, text=True)
    wall = time.time() - t0
    kv, prov = parse(p.stdout)
    return {"n": n, "rc": p.returncode, "process_s": round(wall, 2), "kv": kv, "prov": prov,
            "stderr_tail": p.stderr.strip().splitlines()[-3:]}


def mlist(s):
    return [float(x) for x in s.split(";")] if s else []


def summarize(runs, commit_run):
    first = next(r for r in runs if r["kv"].get("fingerprint"))
    kv = first["kv"]
    pol = {}
    for p in POLS:
        e = {"v1": mlist(kv.get(f"tmpl.{p}.v1", "")), "v1_fit": float(kv.get(f"tmpl.{p}.v1-fit", "nan")),
             "v2": mlist(kv.get(f"tmpl.{p}.v2", "")), "v2_fit": float(kv.get(f"tmpl.{p}.v2-fit", "nan")),
             "best": mlist(kv.get(f"best.{p}.metrics", "")), "best_fit": float(kv.get(f"best.{p}.fit", "nan")),
             "best_stage": kv.get(f"best.{p}.stage"), "best_src": kv.get(f"best.{p}.src"),
             "evals": int(kv.get(f"best.{p}.evals", 0)), "evals_to_best": int(kv.get(f"best.{p}.evals-to-best", -1)),
             "evals_to_v2": int(kv.get(f"best.{p}.evals-to-v2", -1)),
             "front": kv.get(f"front.{p}.member", []), "metric_names": MNAMES[p]}
        if isinstance(e["front"], str):
            e["front"] = [e["front"]]
        pol[p] = e
    scaling = []
    for r in runs:
        k = r["kv"]
        scaling.append({"n": r["n"], "rc": r["rc"], "search_ms": int(k.get("search.wall-ms", -1)),
                        "process_s": r["process_s"], "evals": int(k.get("search.evals", -1)),
                        "fingerprint": k.get("fingerprint"), "rejects": k.get("search.rejects"),
                        "noisy": k.get("search.noisy"), "overlay": k.get("search.overlay"),
                        "stderr_tail": r["stderr_tail"] if r["rc"] else []})
    base = next((s for s in scaling if s["n"] == 0 and s["search_ms"] > 0), None)
    for s in scaling:
        s["speedup_vs_serial"] = round(base["search_ms"] / s["search_ms"], 2) if base and s["search_ms"] > 0 else None
    fps = {s["fingerprint"] for s in scaling if s["fingerprint"]}
    commit = {}
    if commit_run:
        ck = commit_run["kv"]
        for p in POLS:
            commit[p] = {k.split(".", 2)[2]: v for k, v in ck.items()
                         if (k.startswith(f"commit.{p}.") or k.startswith(f"rollback.{p}.") or k.startswith(f"probe.{p}."))
                         and not k.endswith(".src")}
        commit["_ms"] = ck.get("commit.ms")
        commit["_mutation_log"] = ck.get("mutation-log")
        commit["_rc"] = commit_run["rc"]
    rej = [p for p in first["prov"] if p["gate"] == "reject"]
    return {"config": kv.get("search.config"), "policies": pol, "scaling": scaling,
            "deterministic_across_n": len(fps) == 1 and all(x["fingerprint"] for x in scaling), "fingerprints": sorted(fps),
            "gate": {"evaluated": len(first["prov"]), "rejected": len(rej),
                     "rejection_rate": round(len(rej) / max(1, len(first["prov"])), 3),
                     "noisy": kv.get("search.noisy"), "reasons": kv.get("search.rejects")},
            "commit": commit}


def fmt(v):
    return ", ".join(f"{x:g}" for x in v)


def write_md(s, path):
    L = ["# Swarm search results (PSO + ACO, fibers + per-fiber COW overlay)", "",
         f"config: `{s['config']}`", "",
         "## Best found vs hand-written v1 / v2", "",
         "| policy | metrics | v1 | v2 | search best | fitness v1 / v2 / best | evals | evals to best | evals to reach v2 |",
         "|---|---|---|---|---|---|---|---|---|"]
    for p, e in s["policies"].items():
        L.append(f"| `{p}` | {', '.join(e['metric_names'])} | {fmt(e['v1'])} | {fmt(e['v2'])} | {fmt(e['best'])} ({e['best_stage']}) | "
                 f"{e['v1_fit']:g} / {e['v2_fit']:g} / {e['best_fit']:g} | {e['evals']} | {e['evals_to_best']} | {e['evals_to_v2']} |")
    L += ["", "## Fiber scaling (same seed, separate processes; N=0 = serial, no fibers)", "",
          "| N | rc | search wall ms | speedup vs serial | process s | evals | fingerprint identical |", "|---|---|---|---|---|---|---|"]
    fp0 = s["fingerprints"][0] if s["fingerprints"] else None
    for r in s["scaling"]:
        L.append(f"| {r['n']} | {r['rc']} | {r['search_ms']} | {r['speedup_vs_serial']} | {r['process_s']} | {r['evals']} | {r['fingerprint'] == fp0} |")
    g = s["gate"]
    L += ["", f"deterministic across N: **{s['deterministic_across_n']}**", "",
          "## Gate", "", f"- evaluated {g['evaluated']}, rejected {g['rejected']} (rate {g['rejection_rate']})",
          f"- injected defects: {g['noisy']}", f"- reasons: {g['reasons']}", "", "## Commit + rollback drills (single writer)", ""]
    for p, c in s["commit"].items():
        if p.startswith("_"):
            continue
        L.append(f"- `{p}`: " + "; ".join(f"{k}={v}" for k, v in sorted(c.items()) if "\n" not in str(v)))
    L.append(f"- commit phase ms: {s['commit'].get('_ms')}, mutation-log entries: {s['commit'].get('_mutation_log')}")
    L += ["", "## Pareto fronts (id | fitness | metrics | objectives)", ""]
    for p, e in s["policies"].items():
        L.append(f"- `{p}`: " + "; ".join(e["front"]))
    Path(path).write_text("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ns", default="0,1,4,8,16")
    ap.add_argument("--commit-n", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--out", default=str(REPO / "results"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    runs = []
    for n in [int(x) for x in a.ns.split(",")]:
        r = run_once(n, False, a.timeout, {})
        print(f"N={n} rc={r['rc']} search_ms={r['kv'].get('search.wall-ms')} fp={r['kv'].get('fingerprint')}", flush=True)
        runs.append(r)
    commit_run = None
    if a.commit_n >= 0:
        commit_run = run_once(a.commit_n, True, a.timeout * 2, {})
        print(f"commit run N={a.commit_n} rc={commit_run['rc']} commit_ms={commit_run['kv'].get('commit.ms')}", flush=True)
        with open(out / "search-provenance.jsonl", "w") as f:
            for row in commit_run["prov"]:
                f.write(json.dumps(row) + "\n")
    s = summarize(runs, commit_run)
    (out / "search.json").write_text(json.dumps(s, indent=2))
    write_md(s, out / "search.md")
    print((out / "search.md").read_text())
    complete = all(r["rc"] == 0 and r["kv"].get("fingerprint") for r in runs)
    if commit_run is not None:
        complete = complete and commit_run["rc"] == 0 and commit_run["kv"].get("commit.ms") is not None
    return 0 if s["deterministic_across_n"] and complete else 1


if __name__ == "__main__":
    sys.exit(main())

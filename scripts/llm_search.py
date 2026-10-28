#!/usr/bin/env python3
"""LLM proposals + swarm local search around them, compared on the HOLD-OUT rows.

  AURA_BIN=... AURA_STDLIB=... [AURA_LIBDIR=...] python3 scripts/llm_search.py \
      --models glm,minimax --seeds 20261028,20261029,20261030 --k 4 [--env-file ~/.config/aura-build/minimax.env]
  python3 scripts/llm_search.py --models mock ...      # deterministic mock LLM (tests, no network)

1. context run (Aura): v1 source, TRAIN metrics and failure examples per policy
2. per model / seed / policy: K proposals {"reason", "source"} (cached in results/llm-cache/)
3. one Aura run per seed (aura/llm-search.aura): swarm-only, LLM-only (best of K) and
   LLM+swarm arms through the same coordinator / fiber / COW-overlay / gate path, every arm
   reported on the hold-out rows; first seed also commits (mutate:rebind with the LLM reason
   + swarm attempt ids), restores v1 between models and keeps the best LLM+swarm per policy
4. results/llm-search.{json,md} and results/llm-search-provenance.jsonl
API keys are read by llm_client.py from key files and never printed or written anywhere.
"""
import argparse, concurrent.futures as cf, hashlib, json, os, re, statistics, subprocess, sys, threading, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llm_client  # noqa: E402
from run_search import parse  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
POLS = ["should-arbitrate?", "claim-root-cause", "expedite-response"]
PFILE = {"should-arbitrate?": "should-arbitrate", "claim-root-cause": "claim-root-cause", "expedite-response": "expedite-response"}
MNAMES = {"should-arbitrate?": ["arbitrations", "false_arbitrations", "false_alarm_rate", "recall"],
          "claim-root-cause": ["accuracy", "unknown", "recovered", "recovery_rate"],
          "expedite-response": ["expedites", "supplier_switches", "rebalances", "stockouts", "cost", "events"]}
# list prices, USD per 1M tokens (input, output), checked 2026-10-28: docs.z.ai/guides/overview/pricing,
# platform.minimax.io/docs/pricing/overview.  The GLM coding-plan endpoint is a subscription; the
# list price is used as the pay-as-you-go equivalent.
PRICES = {"glm": (0.15, 0.50), "minimax": (0.15, 0.60), "deepseek": (0.0, 0.0), "mock": (0.0, 0.0)}

CONTRACT = {
    "should-arbitrate?": ("(should-arbitrate? edi-change inventory-exposure) -> #t or #f",
                          "edi-change is an event hash: (change-pct e) signed share, (frozen-horizon? e) boolean, "
                          "(hash-ref e \"confidence\") 0..1, (high-confidence? e) = confidence >= 0.7; inventory-exposure is a number (currency)",
                          "fitness = recall - false-arbitration-rate, minus 1.0 if recall < 0.8 (business gate: recall >= 0.8 and "
                          "false-arbitration-rate must not rise)"),
    "claim-root-cause": ("(claim-root-cause expedite-event) -> exactly one of 'supplier-delay 'demand-forecast-error 'unknown",
                         "helpers: (edi-increase? e) (supplier-lead-time-miss? e) (forecast-bias? e) (bias-amount e) number "
                         "(market-signal-mismatch? e); all predicates return booleans",
                         "fitness = accuracy + recovery-rate (recovered claim amount / recoverable amount); business gate: "
                         "accuracy and recovered amount must not fall"),
    "expedite-response": ("(expedite-response risk-level inventory-days) -> a list whose first element is the action",
                          "risk-level is one of the symbols 'high 'medium 'low (compare with (risk-rank level): high=3 medium=2 low=1, "
                          "symbols are not ordered); inventory-days is a number. Allowed results exactly: "
                          "(list 'alert-planner 'immediate-expedite-review) (list 'suggest-alternative-supplier) "
                          "(list 'propose-internal-rebalance) (list 'monitor)",
                          "cost model: alert-planner (premium freight) costs 35000 and always arrives in time; "
                          "suggest-alternative-supplier costs 45000 but the new supplier may arrive too late; propose-internal-rebalance "
                          "costs 6000 + 1500 per earlier rebalance in the period (sister-plant stock depletes), the transfer may arrive "
                          "too late, and without sister stock it falls back to the alternative supplier (+45000); monitor costs 0. "
                          "A stockout costs 150000 and happens only if the risk materializes before help arrives (monitor: before "
                          "the next regular delivery). fitness = -(cost per 40 events in millions) - 0.1 * stockouts per 40 events; "
                          "business gate: stockouts and cost must not rise"),
}
SYSTEM = ("You improve one supply-chain decision policy written in Aura, a Scheme-like Lisp. Reply with ONE JSON object "
          "and nothing else: {\"reason\": \"<= 60 words: the edit and why, citing the metrics or failure rows\", "
          "\"source\": \"<the complete new (define ...) form>\"}. Rules: a single (define (NAME ARGS) BODY) form with exactly "
          "the same name and parameters; use only the listed helpers plus and/or/not/cond/if/else/abs/>/</>=/<=/=/hash-ref/list "
          "and quoted symbols; numbers are never quoted; no new definitions. Make one structural edit (add, remove or reorder "
          "a condition or branch, or change an action/label) and adjust thresholds if that helps.")


def run_aura(main_src, props_src, env_extra, timeout, name):
    name = os.environ.get("SCM_LLM_BUILD_TAG", "") + name   # separate build/ files for concurrent runs
    (REPO / "build").mkdir(exist_ok=True)
    (REPO / f"build/{name}-props.aura").write_text(props_src)
    (REPO / f"build/{name}-main.aura").write_text(main_src)
    env = dict(os.environ, SCM_BUILD_NAME=name, SCM_MAIN=f"build/{name}-main.aura", SCM_TIMEOUT=str(timeout),
               SCM_EXTRA_MODULES=f"aura/llm-search.aura build/{name}-props.aura", SCM_COMMIT="0", **env_extra)
    t0 = time.time()
    p = subprocess.run(["bash", str(REPO / "scripts/run_search.sh")], env=env, capture_output=True, text=True)
    (REPO / f"build/{name}.stdout").write_text(p.stdout)   # raw @@ lines, for re-analysis
    kv, prov = parse(p.stdout)
    trail = [l[len("@@trail.audit="):] for l in p.stdout.splitlines() if l.startswith("@@trail.audit=")]
    return dict(rc=p.returncode, wall_s=round(time.time() - t0, 1), kv=kv, prov=prov, trail=trail,
                lines=p.stdout.splitlines(), stderr_tail=p.stderr.strip().splitlines()[-3:])


def aura_str(s):
    s = s.replace("\r", "").replace("\t", " ")
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def props_file(models, rows):
    L = ["(define LLM-MODELS (list " + " ".join(aura_str(m) for m in models) + "))", "(define LLM-PROPS (list"]
    for r in rows:
        L.append(f"  (list {aura_str(r['model'])} {r['seed']} {aura_str(r['policy'])} {r['k']} "
                 f"{aura_str(r['reason'][:400])} {aura_str(r['aura_source'])})")
    return "\n".join(L) + "))\n"


def context(timeout):
    r = run_aura('(for-each ctx-policy! POLICIES)\n(emit "done" "ok")\n', props_file([], []), {"SCM_SEARCH_N": "0"}, timeout, "llmctx")
    if r["rc"] != 0 or r["kv"].get("done") != "ok":
        raise SystemExit(f"context run failed rc={r['rc']} {r['stderr_tail']}")
    ctx = {}
    for pol in POLS:
        fails = [l.split("=", 1)[1] for l in r["lines"] if l.startswith(f"@@ctx.{pol}.fail=")]
        ctx[pol] = dict(src=r["kv"][f"ctx.{pol}.src"], metrics=r["kv"][f"ctx.{pol}.metrics"],
                        fitness=r["kv"][f"ctx.{pol}.fitness"], fails=fails)
    return ctx


def pick(xs, n):
    if len(xs) <= n:
        return xs
    return [xs[round(i * (len(xs) - 1) / (n - 1))] for i in range(n)]


def messages(pol, c, seed, k):
    sig, helpers, metric = CONTRACT[pol]
    helpers_src = (REPO / "aura/policies/helpers.aura").read_text()
    fails = pick(c["fails"], 8)
    user = (f"Policy: {pol}\nSignature and result contract: {sig}\nInputs/helpers: {helpers}\nHelper source:\n{helpers_src}\n"
            f"Objective: {metric}\n\nCurrent source (v1):\n{c['src']}\n\nTrain metrics of v1: {c['metrics']} (fitness {c['fitness']})\n"
            f"{len(c['fails'])} train rows where v1 is wrong or costly; examples:\n" + "\n".join("- " + f for f in fails) +
            f"\n\nPropose one improved version. (sample {seed}-{k})")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def balanced(s):
    d, ins, esc = 0, False, False
    for ch in s:
        if ins:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': ins = False
        elif ch == '"': ins = True
        elif ch == ";": return False   # comments are not expected inside a one-form answer
        elif ch == "(": d += 1
        elif ch == ")":
            d -= 1
            if d < 0: return False
    return d == 0 and not ins


def parse_proposal(text, pol):
    """-> (status, reason, source).  status: valid | no-json | no-source | wrong-form | unbalanced."""
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    obj = None
    try:
        obj = json.loads(t)
    except Exception:
        m = re.search(r"\{.*\}", t, re.S)
        if m:
            try:
                obj = json.loads(m.group(0))
            except Exception:
                obj = None
    if not isinstance(obj, dict):
        return "no-json", "", ""
    reason, src = str(obj.get("reason", "")).strip(), str(obj.get("source", "")).strip()
    if not src:
        return "no-source", reason, ""
    if not src.startswith(f"(define ({pol} "):
        return "wrong-form", reason, src
    if not balanced(src):
        return "unbalanced", reason, src
    return "valid", reason, src


def mock_text(pol, seed, k):
    """Deterministic stand-in for an LLM (tests): v2, a broken answer, a threshold tweak of v1, prose."""
    v1 = (REPO / f"aura/policies/{PFILE[pol]}.v1.aura").read_text().strip()
    v2 = (REPO / f"aura/policies/{PFILE[pol]}.v2.aura").read_text().strip()
    kinds = [lambda: json.dumps({"reason": "mock: adopt the stricter hand-written rules", "source": v2}),
             lambda: json.dumps({"reason": "mock: broken answer", "source": v1[:-2]}),
             lambda: "```json\n" + json.dumps({"reason": "mock: v1 with a tweak", "source": v1.replace("0.15", "0.2").replace("5)", "6)")}) + "\n```",
             lambda: "I think the policy is fine."]
    return kinds[(k - 1 + seed) % len(kinds)]()


SEMS, PER_PROVIDER = {}, 3   # at most 3 concurrent calls per provider


def ask(model, pol, ctx, seed, k, cache_dir, max_tokens):
    msgs = messages(pol, ctx, seed, k)
    h = hashlib.sha256(json.dumps(msgs, sort_keys=True).encode()).hexdigest()[:16]
    f = cache_dir / model / f"s{seed}-{PFILE[pol]}-k{k}-{h}.json"
    if f.exists():
        rec = json.loads(f.read_text())
        rec["cached"] = True
        return rec
    if model == "mock":
        rec = dict(model="mock", text=mock_text(pol, seed, k), finish="stop", latency_s=0.0, attempts=1,
                   prompt_tokens=sum(len(m["content"]) // 4 for m in msgs), completion_tokens=120, reasoning_tokens=0)
    else:
        try:
            with SEMS.setdefault(model, threading.BoundedSemaphore(PER_PROVIDER)):
                rec = llm_client.call(model, msgs, max_tokens=max_tokens, temperature=0.8)
        except Exception as e:  # keep going: an API failure is one failed proposal
            rec = dict(model=llm_client.model_of(model), text="", finish=f"error: {str(e)[:200]}", latency_s=0.0, attempts=1,
                       prompt_tokens=0, completion_tokens=0, reasoning_tokens=0)
    rec.update(prompt_sha=h, provider=model)
    if model != "mock" and rec["text"]:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    rec["cached"] = False
    return rec


def collect(models, seeds, K, ctx, cache_dir, max_tokens, workers):
    jobs = [(m, s, p, k) for m in models for s in seeds for p in POLS for k in range(1, K + 1)]
    out = {}
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(ask, m, p, ctx[p], s, k, cache_dir, max_tokens): (m, s, p, k) for (m, s, p, k) in jobs}
        for fu in cf.as_completed(futs):
            out[futs[fu]] = fu.result()
    rows = []
    for (m, s, p, k) in jobs:
        rec = out[(m, s, p, k)]
        status, reason, src = parse_proposal(rec["text"], p)
        if not rec["text"] and str(rec["finish"]).startswith("error"):
            status = "api-error"
        rows.append(dict(model=m, seed=s, policy=p, k=k, status=status, reason=reason, source=src,
                         aura_source=src if src else f"(define ({p} x", model_id=rec["model"], finish=rec["finish"],
                         prompt_tokens=rec["prompt_tokens"], completion_tokens=rec["completion_tokens"],
                         reasoning_tokens=rec["reasoning_tokens"], latency_s=rec["latency_s"], attempts=rec["attempts"],
                         cached=rec["cached"], prompt_sha=rec["prompt_sha"]))
    return rows


def main_src(models, commit):
    L = ["(run-llm-search)"]
    if commit:
        L.append("(llm-snapshot-v1!)")
        for m in models:
            L += [f'(llm-commit! {aura_str(m)} {i} "trial")' for i in range(3)] + [f"(llm-restore-v1! {aura_str(m)})"]
        L += [f"(llm-commit-best! {i})" for i in range(3)]
        L += ["(emit-mutation-log)", '(dump-audit "trail")']
    L.append('(emit "done" "ok")')
    return "\n".join(L) + "\n"


def mlist(s):
    return [float(x) for x in s.split(";")] if s else []


def gate_ok(pol, old, new):   # the business gates of aura/evolve.aura, on TRAIN metrics
    if not new:
        return False
    if pol == "should-arbitrate?":
        return new[3] >= 0.8 and new[2] <= old[2]
    if pol == "claim-root-cause":
        return new[0] >= old[0] and new[2] >= old[2]
    return new[3] <= old[3] and new[4] <= old[4]


def summarize(models, seeds, rows, runs):
    arms = ["v1", "v2", "swarm"] + [f"{a}:{m}" for m in models for a in ("llm", "llm+swarm")]
    table = {}
    for arm in arms:
        for pol in POLS:
            per = []
            for s in seeds:
                kv = runs[s]["kv"]
                t = f"arm.{arm}.{pol}"
                if f"{t}.holdout-fit" not in kv:
                    continue
                per.append(dict(seed=s, id=kv[f"{t}.id"], train_fit=float(kv[f"{t}.train-fit"]), holdout_fit=float(kv[f"{t}.holdout-fit"]),
                                train=mlist(kv[f"{t}.train"]), holdout=mlist(kv[f"{t}.holdout"]), gap=float(kv[f"{t}.gap"]),
                                evals=int(kv[f"{t}.evals"]), rejects=int(kv[f"{t}.rejects"]), src=kv[f"{t}.src"],
                                reason=kv.get(f"{t}.reason", ""), gate_pass=kv.get(f"{t}.gate-pass"), proposals=kv.get(f"{t}.proposals"),
                                attempts=kv.get(f"{t}.attempts", ""), base_id=kv.get(f"{t}.base-id", ""),
                                guards=kv.get(f"{t}.guards", "-"), guard_violations=kv.get(f"{t}.guard-violations", ""),
                                holdout_hard_fit=float(kv[f"{t}.holdout-hard-fit"]) if f"{t}.holdout-hard-fit" in kv else None,
                                guard_rejects=guard_rejects(runs[s]["prov"], arm, pol)))
            for p in per:   # runs before the one-line emit fix cut multi-line LLM sources: recover them from the call rows
                if not balanced(p["src"]):
                    a = next((x for x in runs[p["seed"]]["prov"] if x["id"] == str(p["id"]) and x["stage"].startswith("llm:")), None)
                    if a:
                        k = int(a["stage"].rsplit(":k", 1)[1])
                        r = next((x for x in rows if x["seed"] == p["seed"] and x["model"] == a["stage"].split(":")[1]
                                  and x["policy"] == pol and x["k"] == k), None)
                        if r and r["source"]:
                            p["src"] = " ".join(r["source"].split())
            if per:
                ho = [p["holdout_fit"] for p in per]
                hh = [p["holdout_hard_fit"] for p in per if p["holdout_hard_fit"] is not None]
                gr = {}
                for p in per:
                    for g, n in p["guard_rejects"].items():
                        gr[g] = gr.get(g, 0) + n
                table[(arm, pol)] = dict(per_seed=per, holdout_mean=round(statistics.mean(ho), 4),
                                         holdout_hard_mean=round(statistics.mean(hh), 4) if hh else None,
                                         holdout_hard_sd=round(statistics.pstdev(hh), 4) if len(hh) > 1 else (0.0 if hh else None),
                                         guards_pass=sum(p["guards"] == "pass" for p in per), guard_rejects=gr,
                                         holdout_sd=round(statistics.pstdev(ho), 4) if len(ho) > 1 else 0.0,
                                         train_mean=round(statistics.mean(p["train_fit"] for p in per), 4),
                                         gap_mean=round(statistics.mean(p["gap"] for p in per), 4),
                                         evals_mean=round(statistics.mean(p["evals"] for p in per), 1),
                                         reject_rate=round(sum(p["rejects"] for p in per) / max(1, sum(p["evals"] for p in per)), 3))
    per_model = {}
    for m in models:
        mr = [r for r in rows if r["model"] == m]
        lat = [r["latency_s"] for r in mr if r["latency_s"] > 0]   # cached rows keep the latency of their original call
        pin, pout = sum(r["prompt_tokens"] for r in mr), sum(r["completion_tokens"] for r in mr)
        usd = pin / 1e6 * PRICES.get(m, (0, 0))[0] + pout / 1e6 * PRICES.get(m, (0, 0))[1]
        passed = total = 0   # gate pass over ALL proposals, from the Aura attempts of each seed
        for s in seeds:
            for row in runs[s]["prov"]:
                if row["stage"].startswith(f"llm:{m}:"):
                    total += 1
                    passed += row["gate"] == "pass"
        acc = {"llm": 0, "llm+swarm": 0}
        acc_ho = {"llm": 0, "llm+swarm": 0}
        for a in acc:
            for pol in POLS:
                for p, v1 in zip(table[(f"{a}:{m}", pol)]["per_seed"], table[("v1", pol)]["per_seed"]):
                    if p["train_fit"] > v1["train_fit"] + 1e-9 and gate_ok(pol, v1["train"], p["train"]) and p["guards"] in ("pass", "-"):
                        acc[a] += 1
                        acc_ho[a] += p["holdout_fit"] > v1["holdout_fit"] + 1e-9
        st = {}
        for r in mr:
            st[r["status"]] = st.get(r["status"], 0) + 1
        evals = {a: sum(p["evals"] for pol in POLS for p in table[(f"{a}:{m}", pol)]["per_seed"]) for a in acc}
        per_model[m] = dict(model_id=sorted({r["model_id"] for r in mr}), calls=len(mr), calls_live=sum(not r["cached"] for r in mr),
                            retries=sum(r["attempts"] - 1 for r in mr), status=st, valid_rate=round(st.get("valid", 0) / max(1, len(mr)), 3),
                            gate_pass=passed, gate_total=total, gate_pass_rate=round(passed / max(1, total), 3),
                            prompt_tokens=pin, completion_tokens=pout, reasoning_tokens=sum(r["reasoning_tokens"] for r in mr),
                            latency_mean_s=round(statistics.mean(lat), 2) if lat else None,
                            latency_p50_s=round(statistics.median(lat), 2) if lat else None,
                            latency_max_s=round(max(lat), 2) if lat else None,
                            usd_list_price=round(usd, 5), accepted=acc, accepted_holdout_better=acc_ho, evals=evals,
                            usd_per_accepted={a: (round(usd / acc[a], 5) if acc[a] else None) for a in acc},
                            tokens_per_accepted={a: (round((pin + pout) / acc[a]) if acc[a] else None) for a in acc},
                            evals_per_accepted={a: (round(evals[a] / acc[a], 1) if acc[a] else None) for a in acc},
                            example_reasons={pol: next((r["reason"] for r in mr if r["policy"] == pol and r["status"] == "valid"), "")
                                             for pol in POLS})
    return arms, table, per_model


def arm_key(arm, pol):
    """policy key of an arm's attempts in the provenance rows"""
    if arm in ("v1", "v2", "swarm"):
        return pol
    a, m = arm.split(":")
    return f"{pol}@{m}" + ("+swarm" if a == "llm+swarm" else "")


def guard_rejects(prov, arm, pol):
    if arm in ("v1", "v2"):
        return {}
    key, out = arm_key(arm, pol), {}
    for row in prov:
        if row["policy"] == key and row["gate"] == "reject" and row["reason"] == "guard":
            out[row["error"]] = out.get(row["error"], 0) + 1
    return out


def paired_stats(a, b, n_boot=10000, seed=7):
    """paired differences a-b over seeds: mean, 95% bootstrap CI (percentile) and the exact
    two-sided sign-flip permutation p-value (all 2^n sign patterns for n <= 16)."""
    import itertools, random
    d = [x - y for x, y in zip(a, b)]
    n = len(d)
    if n == 0:
        return None
    mean = statistics.mean(d)
    R = random.Random(seed)
    boots = sorted(statistics.mean(R.choice(d) for _ in range(n)) for _ in range(n_boot))
    lo, hi = boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot) - 1]
    if all(abs(x) < 1e-12 for x in d):
        p = 1.0
    else:
        obs, ext, tot = abs(sum(d)), 0, 0
        for signs in itertools.product((1, -1), repeat=n):
            tot += 1
            ext += abs(sum(s * x for s, x in zip(signs, d))) >= obs - 1e-12
        p = ext / tot
    wins = sum(x > 1e-9 for x in d); losses = sum(x < -1e-9 for x in d)
    return dict(n=n, mean_diff=round(mean, 4), ci95=[round(lo, 4), round(hi, 4)], p_perm=round(p, 4),
                wins=wins, ties=n - wins - losses, losses=losses)


def significance(models, table):
    out = {}
    for m in models:
        for pol in POLS:
            ls = table.get((f"llm+swarm:{m}", pol)); sw = table.get(("swarm", pol)); lo = table.get((f"llm:{m}", pol))
            if not (ls and sw and lo):
                continue
            hl = lambda t: [p["holdout_fit"] for p in t["per_seed"]]
            out[f"{m}|{pol}|vs-swarm"] = paired_stats(hl(ls), hl(sw))
            out[f"{m}|{pol}|vs-llm-only"] = paired_stats(hl(ls), hl(lo))
            if ls.get("holdout_hard_mean") is not None:
                hh = lambda t: [p["holdout_hard_fit"] for p in t["per_seed"]]
                out[f"{m}|{pol}|vs-swarm|hard"] = paired_stats(hh(ls), hh(sw))
                out[f"{m}|{pol}|vs-llm-only|hard"] = paired_stats(hh(ls), hh(lo))
    return out


def write_outputs(args, models, seeds, rows, runs, arms, table, per_model, out_dir):
    first = seeds[0]
    kv0 = runs[first]["kv"]
    commits = {k: v for k, v in kv0.items() if k.startswith("llmcommit.")}
    res = dict(config=dict(models=models, seeds=seeds, k=args.k, n=args.n, reps=args.reps, max_tokens=args.max_tokens,
                           search=kv0.get("search.config"), prices_usd_per_m=PRICES),
               runs={str(s): dict(rc=runs[s]["rc"], wall_s=runs[s]["wall_s"], evals=runs[s]["kv"].get("llm.evals-total"),
                                  flakes=runs[s]["kv"].get("llm.flakes"), rejects=runs[s]["kv"].get("llm.rejects"),
                                  swarm_fingerprint=runs[s]["kv"].get("fingerprint")) for s in seeds},
               arms={f"{a}|{p}": v for (a, p), v in table.items()}, models=per_model, commits=commits,
               significance=significance(models, table),
               guards=dict(version=kv0.get("guards.version"), registry=kv0.get("guards.registry"), baseline_v1=kv0.get("guards.baseline"),
                           rejects_per_seed={str(s): runs[s]["kv"].get("llm.guard-rejects") for s in seeds}),
               audit_trail=runs[first]["trail"])
    (out_dir / "llm-search.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    with open(out_dir / "llm-search-provenance.jsonl", "w") as fh:
        for r in rows:   # every LLM call (no keys; the prompt is identified by its hash)
            att = None
            for row in runs[r["seed"]]["prov"]:
                if row["stage"] == f"llm:{r['model']}:k{r['k']}" and row["policy"] == f"{r['policy']}@{r['model']}":
                    att = dict(attempt_id=int(row["id"]), gate=row["gate"], gate_reason=row["reason"], train_fitness=row["fitness"])
            fh.write(json.dumps(dict(kind="llm-call", **{k: v for k, v in r.items() if k != "aura_source"}, attempt=att), ensure_ascii=False) + "\n")
        for s in seeds:  # every Aura attempt (all arms)
            for row in runs[s]["prov"]:
                fh.write(json.dumps(dict(kind="attempt", seed=s, **row), ensure_ascii=False) + "\n")
        for m in models:
            for tag in ("trial", "keep"):
                for pol in POLS:
                    t = f"llmcommit.{tag}.{m}.{pol}"
                    if f"{t}.gate" in kv0:
                        ls = table[(f"llm+swarm:{m}", pol)]["per_seed"][0]
                        fh.write(json.dumps(dict(kind="commit", seed=first, tag=tag, model=m, policy=pol, gate=kv0[f"{t}.gate"],
                                                 rebind=kv0[f"{t}.rebind"], best_attempt=int(kv0[f"{t}.best-id"]),
                                                 base_attempt=ls["base_id"], swarm_attempts=ls["attempts"],
                                                 fiber_metrics_equal=kv0[f"{t}.fiber-metrics-equal"], before=kv0[f"{t}.before"],
                                                 after=kv0[f"{t}.after"], reason=kv0[f"{t}.reason"]), ensure_ascii=False) + "\n")
    f4 = lambda x: f"{x:.3f}"
    L = ["# LLM + swarm search: hold-out comparison", "",
         f"Models {', '.join(models)}; seeds {', '.join(map(str, seeds))}; K={args.k} proposals per policy per seed; "
         f"fibers N={args.n}; search (first seed) {kv0.get('search.config')}; every seed reseeds the swarm (SCM_SEARCH_SEED) and has its own LLM samples. Selection uses the TRAIN rows only; hold-out = "
         "120 EDI changes / 96 claims / 80 risk events from an independent seed.", "",
         "| policy | arm | hold-out fitness (mean ± sd) | train fitness | gap train−hold-out | hard hold-out (claims) | guards pass (seeds) | guard rejects | hold-out metrics (first seed) | evals | gate reject rate |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for pol in POLS:
        for arm in arms:
            v = table.get((arm, pol))
            if not v:
                continue
            p0 = v["per_seed"][0]
            ev = "-" if arm in ("v1", "v2") else f"{v['evals_mean']:.0f}"
            rj = "-" if arm in ("v1", "v2") else f"{v['reject_rate']:.3f}"
            hard = f"{f4(v['holdout_hard_mean'])} ± {f4(v['holdout_hard_sd'])}" if v.get("holdout_hard_mean") is not None else "-"
            grj = ", ".join(f"{g} {n}" for g, n in sorted(v["guard_rejects"].items())) or "0"
            L.append(f"| {pol} | {arm} | {f4(v['holdout_mean'])} ± {f4(v['holdout_sd'])} | {f4(v['train_mean'])} | {f4(v['gap_mean'])} | "
                     f"{hard} | {v['guards_pass']}/{len(v['per_seed'])} | {grj} | "
                     f"{';'.join(str(int(x)) if x == int(x) and abs(x) >= 1 else str(x) for x in p0['holdout'])} | {ev} | {rj} |")
    sig = significance(models, table)
    L += ["", "Metrics: " + "; ".join(f"{p}: {', '.join(MNAMES[p])}" for p in POLS), "",
          f"Guards {kv0.get('guards.version')}: {kv0.get('guards.registry')}; v1 baseline violations {kv0.get('guards.baseline')}.", "",
          "## Significance (paired over seeds, hold-out fitness)", "",
          "| model | policy | comparison | mean diff | 95% bootstrap CI | sign-flip p | wins/ties/losses |", "|---|---|---|---|---|---|---|"]
    for k, v in sig.items():
        if v:
            m_, pol_, cmp_ = k.split("|", 2)
            L.append(f"| {m_} | {pol_} | LLM+swarm {cmp_.replace('|hard', ' (hard hold-out)')} | {v['mean_diff']:+.4f} | [{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}] | {v['p_perm']} | {v['wins']}/{v['ties']}/{v['losses']} |")
    L += ["",
          "## Per model", "",
          "| model | calls | valid (parse ok) | gate pass | input tok | output tok (reasoning) | latency mean / p50 / max s | list-price USD | accepted LLM-only / LLM+swarm | USD per accepted LLM-only / LLM+swarm | evals per accepted LLM+swarm |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m, v in per_model.items():
        L.append(f"| {m} ({', '.join(v['model_id'])}) | {v['calls']} | {v['valid_rate']:.2f} {v['status']} | {v['gate_pass']}/{v['gate_total']} ({v['gate_pass_rate']:.2f}) | "
                 f"{v['prompt_tokens']} | {v['completion_tokens']} ({v['reasoning_tokens']}) | {v['latency_mean_s']} / {v['latency_p50_s']} / {v['latency_max_s']} | "
                 f"{v['usd_list_price']} | {v['accepted']['llm']} / {v['accepted']['llm+swarm']} (of {3 * len(seeds)}) | "
                 f"{v['usd_per_accepted']['llm']} / {v['usd_per_accepted']['llm+swarm']} | {v['evals_per_accepted']['llm+swarm']} |")
    L += ["", "'accepted' = a (seed, policy) whose result beats v1 on TRAIN fitness and passes the business gate vs v1; "
          "the JSON also counts how many of those are better on the hold-out rows.", "", "## Example reasons", ""]
    for m, v in per_model.items():
        for pol, rsn in v["example_reasons"].items():
            L.append(f"- **{m} / {pol}**: {rsn}")
    L += ["", "## Commits (first seed)", ""]
    for k, v in commits.items():
        if k.endswith((".gate", ".reason", ".fiber-metrics-equal")) or k.startswith("llmcommit.restore"):
            L.append(f"- `{k}` = {v}")
    (out_dir / "llm-search.md").write_text("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="glm,minimax")
    ap.add_argument("--seeds", default=",".join(str(20261028 + i) for i in range(8)))
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--n", type=int, default=8, help="fibers per wave")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--max-tokens", type=int, default=8000)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--env-file", action="append", default=[])
    ap.add_argument("--out", default=str(REPO / "results"))
    ap.add_argument("--cache", default=str(REPO / "results/llm-cache"))
    ap.add_argument("--small", action="store_true", help="tiny search budgets (tests)")
    ap.add_argument("--reanalyze", action="store_true", help="re-summarize the last run without calling the LLM or Aura")
    ap.add_argument("--phase", default="all", choices=["all", "collect", "aura"], help="collect = LLM calls only (cached); aura = reuse llm-search-rows.json")
    ap.add_argument("--parallel", type=int, default=1, help="Aura seed runs in parallel (results do not depend on it)")
    ap.add_argument("--dry-run", action="store_true", help="count cache hits / misses and exit")
    args = ap.parse_args()
    for f in args.env_file:
        llm_client.load_env_file(f)
    models = [m for m in args.models.split(",") if m]
    seeds = [int(s) for s in args.seeds.split(",") if s]
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    if args.reanalyze:   # rebuild the report from build/llm<i>.stdout + results/llm-search-rows.json (no LLM, no Aura)
        rows = json.loads((out_dir / "llm-search-rows.json").read_text())
        runs = {}
        for i, s in enumerate(seeds):
            out = (REPO / f"build/{os.environ.get('SCM_LLM_BUILD_TAG', '')}llm{i}.stdout").read_text()
            kv, prov = parse(out)
            trail = [l[len("@@trail.audit="):] for l in out.splitlines() if l.startswith("@@trail.audit=")]
            runs[s] = dict(rc=0, wall_s=None, kv=kv, prov=prov, trail=trail, lines=out.splitlines(), stderr_tail=[])
        arms, table, per_model = summarize(models, seeds, rows, runs)
        write_outputs(args, models, seeds, rows, runs, arms, table, per_model, out_dir)
        print(f"re-analysed -> {out_dir}/llm-search.md")
        return 0
    if args.phase == "aura":
        rows = [r for r in json.loads((out_dir / "llm-search-rows.json").read_text()) if r["model"] in models and r["seed"] in seeds]
    else:
        ctx = context(args.timeout)
        if args.dry_run:
            hit = miss = 0
            for m in models:
                for sd in seeds:
                    for p in POLS:
                        for k in range(1, args.k + 1):
                            h = hashlib.sha256(json.dumps(messages(p, ctx[p], sd, k), sort_keys=True).encode()).hexdigest()[:16]
                            ok = (Path(args.cache) / m / f"s{sd}-{PFILE[p]}-k{k}-{h}.json").exists()
                            hit += ok; miss += not ok
            print(f"cache hits {hit}, misses {miss}")
            return 0
        t0 = time.time()
        rows = collect(models, seeds, args.k, ctx, Path(args.cache), args.max_tokens, args.workers)
        print(f"llm: {len(rows)} proposals in {time.time() - t0:.0f}s", flush=True)
        (out_dir / "llm-search-rows.json").write_text(json.dumps(rows, ensure_ascii=False, indent=0))
        if args.phase == "collect":
            return 0
    knobs = {"SCM_SEARCH_N": str(args.n), "SCM_EVAL_REPS": str(args.reps)}
    if args.small:
        knobs.update(SCM_PSO_GENS="2", SCM_ACO_ITERS="2", SCM_EVAL_REPS="1")
    runs = {}
    def one(i_s):
        i, s = i_s
        r = run_aura(main_src(models, i == 0), props_file(models, [x for x in rows if x["seed"] == s]),
                     dict(knobs, SCM_SEARCH_SEED=str(s)), args.timeout, f"llm{i}")
        print(f"seed {s}: rc={r['rc']} {r['wall_s']}s evals={r['kv'].get('llm.evals-total')} done={r['kv'].get('done')}", flush=True)
        return s, r
    with cf.ThreadPoolExecutor(max_workers=max(1, args.parallel)) as ex:
        for s, r in ex.map(one, list(enumerate(seeds))):
            runs[s] = r
    bad = [s for s in seeds if runs[s]["rc"] != 0 or runs[s]["kv"].get("done") != "ok"]
    if bad:
        raise SystemExit(f"aura run failed for seeds {bad}: {[runs[s]['stderr_tail'] for s in bad]}")
    arms, table, per_model = summarize(models, seeds, rows, runs)
    write_outputs(args, models, seeds, rows, runs, arms, table, per_model, out_dir)
    print(f"wrote {out_dir}/llm-search.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

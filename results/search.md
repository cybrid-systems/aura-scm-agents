# Swarm search results (PSO + ACO, fibers + per-fiber COW overlay)

config: `seed=20261028 pso=16x10 aco=16x8 reps=20 noise=0.1`

## Best found vs hand-written v1 / v2

| policy | metrics | v1 | v2 | search best | fitness v1 / v2 / best | evals | evals to best | evals to reach v2 |
|---|---|---|---|---|---|---|---|---|
| `should-arbitrate?` | arbitrations, false_arbitrations, false_alarm_rate, recall | 28, 20, 0.714, 1 | 7, 0, 0, 0.875 | 8, 0, 0, 1 (pso) | 0.286 / 0.875 / 1 | 215 | 170 | 153 |
| `claim-root-cause` | accuracy, unknown, recovered, recovery_rate | 0.708, 23, 3.161e+06, 0.607 | 1, 9, 5.21e+06, 1 | 1, 9, 5.21e+06, 1 (aco) | 1.315 / 2 / 2 | 211 | 220 | 220 |
| `expedite-response` | expedites, supplier_switches, rebalances, stockouts, cost | 1, 34, 0, 4, 2.15e+06 | 1, 6, 34, 4, 1.094e+06 | 0, 6, 40, 0, 510000 (aco) | -2.55 / -1.494 / -0.51 | 200 | 443 | 428 |

## Fiber scaling (same seed, separate processes; N=0 = serial, no fibers)

| N | rc | search wall ms | speedup vs serial | process s | evals | fingerprint identical |
|---|---|---|---|---|---|---|
| 0 | 0 | 106463 | 1.0 | 107.82 | 626 | True |
| 1 | 0 | 109108 | 0.98 | 110.63 | 626 | True |
| 4 | 0 | 52509 | 2.03 | 53.98 | 626 | True |
| 8 | 0 | 52193 | 2.04 | 53.69 | 626 | True |
| 16 | 0 | 44925 | 2.37 | 46.48 | 626 | True |

deterministic across N: **True**

## Gate

- evaluated 626, rejected 90 (rate 0.144)
- injected defects: injected=90 rejected=90 clean-rejected=0
- reasons: parse=29 type=42 type-lint=19 runtime=0

## Commit + rollback drills (single writer)

- `should-arbitrate?`: broken-guard=rejected; broken-rebind=rejected; broken-unchanged=#t; fiber-metrics-equal=#t; gate=pass; metrics=8;0;0.0;1.0; rebind=ok; rebind-one-paren-short=accepted(lenient); restored-metrics-equal=#t; restored-source-equal=#t; typecheck=type: Void; v1=28;20;0.714;1.0; v1-restored-after-v2=#t; v2file=7;0;0.0;0.875; worst-gate=fail; worst-metrics=5;4;0.8;0.125
- `claim-root-cause`: broken-guard=rejected; broken-rebind=accepted(!); broken-unchanged=#t; fiber-metrics-equal=#t; gate=pass; metrics=1.0;9;5210000;1.0; rebind=ok; rebind-one-paren-short=accepted(lenient); restored-metrics-equal=#t; restored-source-equal=#t; typecheck=type: Void; v1=0.708;23;3161000;0.607; v1-restored-after-v2=#t; v2file=1.0;9;5210000;1.0; worst-gate=fail; worst-metrics=0.458;0;2894000;0.555
- `expedite-response`: broken-guard=rejected; broken-rebind=accepted(!); broken-unchanged=#t; fiber-metrics-equal=#t; gate=pass; metrics=0;6;40;0;510000; rebind=ok; rebind-one-paren-short=accepted(lenient); restored-metrics-equal=#t; restored-source-equal=#t; typecheck=type: Void; v1=1;34;0;4;2150000; v1-restored-after-v2=#t; v2file=1;6;34;4;1094000; worst-gate=fail; worst-metrics=1;0;0;13;1970000
- commit phase ms: 9030, mutation-log entries: 10

## Pareto fronts (id | fitness | metrics | objectives)

- `should-arbitrate?`: 273|1.0|8;0;0.0;1.0|1.0;0.0
- `claim-root-cause`: 427|2.0|1.0;9;5210000;1.0|1.0;5210000
- `expedite-response`: 855|-0.51|0;6;40;0;510000|-510000.0;0.0;-6.0; 840|-0.716|34;0;6;0;716000|-716000.0;0.0;0.0

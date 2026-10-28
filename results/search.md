# Swarm search results (PSO + ACO, fibers + per-fiber COW overlay)

config: `seed=20261028 pso=16x10 aco=16x8 reps=20 noise=0.1`

## Best found vs hand-written v1 / v2

| policy | metrics | v1 | v2 | search best | fitness v1 / v2 / best | evals | evals to best | evals to reach v2 |
|---|---|---|---|---|---|---|---|---|
| `should-arbitrate?` | arbitrations, false_arbitrations, false_alarm_rate, recall | 28, 20, 0.714, 1 | 7, 0, 0, 0.875 | 8, 0, 0, 1 (pso) | 0.286 / 0.875 / 1 | 215 | 170 | 153 |
| `claim-root-cause` | accuracy, unknown, recovered, recovery_rate | 0.708, 23, 3.161e+06, 0.607 | 1, 9, 5.21e+06, 1 | 1, 9, 5.21e+06, 1 (aco) | 1.315 / 2 / 2 | 211 | 220 | 220 |
| `expedite-response` | expedites, supplier_switches, rebalances, stockouts, cost | 1, 34, 0, 4, 2.165e+06, 40 | 1, 6, 34, 3, 1.8005e+06, 40 | 22, 1, 13, 0, 1.01e+06, 40 (pso) | -2.565 / -2.1005 / -1.01 | 218 | 494 | 428 |

## Fiber scaling (same seed, separate processes; N=0 = serial, no fibers)

| N | rc | search wall ms | speedup vs serial | process s | evals | fingerprint identical |
|---|---|---|---|---|---|---|
| 0 | 0 | 173550 | 1.0 | 175.71 | 644 | True |
| 1 | 0 | 173720 | 1.0 | 176.01 | 644 | True |
| 4 | 0 | 111323 | 1.56 | 113.63 | 644 | True |
| 8 | 0 | 60920 | 2.85 | 63.27 | 644 | True |
| 16 | 0 | 60836 | 2.85 | 63.15 | 644 | True |

deterministic across N: **True**

## Gate

- evaluated 644, rejected 92 (rate 0.143)
- injected defects: injected=92 rejected=92 clean-rejected=0
- reasons: parse=29 type=44 type-lint=19 runtime=0

## Commit + rollback drills (single writer)

- `should-arbitrate?`: broken-guard=rejected; broken-rebind=rejected; broken-unchanged=#t; fiber-metrics-equal=#t; gate=pass; metrics=8;0;0.0;1.0; rebind=ok; rebind-one-paren-short=accepted(lenient); restored-metrics-equal=#t; restored-source-equal=#t; typecheck=type: Void; v1=28;20;0.714;1.0; v1-restored-after-v2=#t; v2file=7;0;0.0;0.875; worst-gate=fail; worst-metrics=5;4;0.8;0.125
- `claim-root-cause`: broken-guard=rejected; broken-rebind=accepted(!); broken-unchanged=#t; fiber-metrics-equal=#t; gate=pass; metrics=1.0;9;5210000;1.0; rebind=ok; rebind-one-paren-short=accepted(lenient); restored-metrics-equal=#t; restored-source-equal=#t; typecheck=type: Void; v1=0.708;23;3161000;0.607; v1-restored-after-v2=#t; v2file=1.0;9;5210000;1.0; worst-gate=fail; worst-metrics=0.458;0;2894000;0.555
- `expedite-response`: broken-guard=rejected; broken-rebind=accepted(!); broken-unchanged=#t; fiber-metrics-equal=#t; gate=pass; metrics=22;1;13;0;1010000;40; rebind=ok; rebind-one-paren-short=accepted(lenient); restored-metrics-equal=#t; restored-source-equal=#t; typecheck=type: Void; v1=1;34;0;4;2165000;40; v1-restored-after-v2=#t; v2file=1;6;34;3;1800500;40; worst-gate=fail; worst-metrics=0;35;5;4;2220000;40
- commit phase ms: 17191, mutation-log entries: 10

## Pareto fronts (id | fitness | metrics | objectives)

- `should-arbitrate?`: 273|1.0|8;0;0.0;1.0|1.0;0.0
- `claim-root-cause`: 427|2.0|1.0;9;5210000;1.0|1.0;5210000
- `expedite-response`: 1000|-1.01|22;1;13;0;1010000;40|-1010000.0;0.0;-1.0; 856|-1.756|0;0;1;7;1056000;40|-1056000.0;-7.0;0.0; 841|-1.196|34;0;1;0;1196000;40|-1196000.0;0.0;0.0

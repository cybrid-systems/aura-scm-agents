# LLM + swarm search: hold-out comparison

Models glm, minimax; seeds 20261028, 20261029, 20261030, 20261031, 20261032, 20261033, 20261034, 20261035; K=4 proposals per policy per seed; fibers N=2; search (first seed) seed=20261028 pso=16x10 aco=16x8 reps=5 noise=0.1; every seed reseeds the swarm (SCM_SEARCH_SEED) and has its own LLM samples. Selection uses the TRAIN rows only; hold-out = 120 EDI changes / 96 claims / 80 risk events from an independent seed.

| policy | arm | hold-out fitness (mean ± sd) | train fitness | gap train−hold-out | hard hold-out (claims) | guards pass (seeds) | guard rejects | hold-out metrics (first seed) | evals | gate reject rate |
|---|---|---|---|---|---|---|---|---|---|---|
| should-arbitrate? | v1 | 0.295 ± 0.000 | 0.286 | -0.009 | - | 8/8 | 0 | 61;43;0.705;1 | - | - |
| should-arbitrate? | v2 | 0.889 ± 0.000 | 0.875 | -0.014 | - | 8/8 | 0 | 16;0.0;0.0;0.889 | - | - |
| should-arbitrate? | swarm | 0.826 ± 0.191 | 0.947 | 0.121 | - | 8/8 | arb.frozen-never 96 | 16;0.0;0.0;0.889 | 211 | 0.212 |
| should-arbitrate? | llm:glm | 0.806 ± 0.073 | 0.585 | -0.221 | - | 8/8 | 0 | 24;6;0.25;1 | 4 | 0.000 |
| should-arbitrate? | llm+swarm:glm | 0.981 ± 0.035 | 0.986 | 0.006 | - | 8/8 | arb.frozen-never 90 | 20;2;0.1;1 | 201 | 0.202 |
| should-arbitrate? | llm:minimax | 0.814 ± 0.066 | 0.641 | -0.172 | - | 8/8 | 0 | 16;0.0;0.0;0.889 | 4 | 0.000 |
| should-arbitrate? | llm+swarm:minimax | 0.993 ± 0.018 | 0.986 | -0.007 | - | 8/8 | arb.frozen-never 75 | 18;0.0;0.0;1 | 195 | 0.214 |
| claim-root-cause | v1 | 1.108 ± 0.000 | 1.315 | 0.207 | 0.705 ± 0.000 | 0/8 | 0 | 0.615;53;4907000;0.493 | - | - |
| claim-root-cause | v2 | 2.000 ± 0.000 | 2.000 | 0.000 | 1.559 ± 0.000 | 8/8 | 0 | 1;16;9953000;1 | - | - |
| claim-root-cause | swarm | 2.000 ± 0.000 | 2.000 | 0.000 | 2.000 ± 0.000 | 8/8 | claims.evidence-not-unknown 89 | 1;16;9953000;1 | 222 | 0.147 |
| claim-root-cause | llm:glm | 1.108 ± 0.000 | 1.315 | 0.207 | 0.705 ± 0.000 | 0/8 | claims.evidence-not-unknown 29 | 0.615;53;4907000;0.493 | 4 | 1.000 |
| claim-root-cause | llm+swarm:glm | 1.833 ± 0.000 | 1.812 | -0.021 | 1.854 ± 0.000 | 8/8 | claims.evidence-not-unknown 279 | 0.833;0.0;9953000;1 | 256 | 0.216 |
| claim-root-cause | llm:minimax | 1.777 ± 0.386 | 1.829 | 0.052 | 1.345 ± 0.370 | 6/8 | claims.evidence-not-unknown 25 | 0.615;53;4907000;0.493 | 4 | 0.781 |
| claim-root-cause | llm+swarm:minimax | 1.958 ± 0.072 | 1.953 | -0.005 | 1.798 ± 0.194 | 8/8 | claims.evidence-not-unknown 368 | 0.833;0.0;9953000;1 | 164 | 0.389 |
| expedite-response | v1 | -1.883 ± 0.000 | -2.565 | -0.682 | - | 8/8 | 0 | 5;52;0.0;5;3265000;80 | - | - |
| expedite-response | v2 | -1.838 ± 0.000 | -2.100 | -0.263 | - | 8/8 | 0 | 5;10;52;3;3376000;80 | - | - |
| expedite-response | swarm | -1.293 ± 0.000 | -1.012 | 0.281 | - | 8/8 | exp.critical-alert 122, exp.high-never-monitor 86 | 45;2;12;3;2286000;80 | 221 | 0.258 |
| expedite-response | llm:glm | -1.409 ± 0.229 | -1.410 | -0.001 | - | 8/8 | exp.high-never-monitor 15 | 57;0.0;0.0;2;2295000;80 | 4 | 0.469 |
| expedite-response | llm+swarm:glm | -1.271 ± 0.047 | -1.098 | 0.174 | - | 8/8 | exp.critical-alert 298, exp.high-never-monitor 187 | 45;2;12;3;2286000;80 | 267 | 0.319 |
| expedite-response | llm:minimax | -1.248 ± 0.000 | -1.225 | 0.022 | - | 8/8 | exp.high-never-monitor 1 | 57;0.0;0.0;2;2295000;80 | 4 | 0.031 |
| expedite-response | llm+swarm:minimax | -1.300 ± 0.062 | -1.144 | 0.156 | - | 8/8 | exp.critical-alert 135, exp.high-never-monitor 115 | 57;0.0;0.0;2;2295000;80 | 205 | 0.286 |

Metrics: should-arbitrate?: arbitrations, false_arbitrations, false_alarm_rate, recall; claim-root-cause: accuracy, unknown, recovered, recovery_rate; expedite-response: expedites, supplier_switches, rebalances, stockouts, cost, events

Guards guards.v1: exp.high-never-monitor/expedite-response/hard;exp.critical-alert/expedite-response/no-regress;arb.frozen-never/should-arbitrate?/hard;claims.evidence-not-unknown/claim-root-cause/hard; v1 baseline violations arb.frozen-never=0;claims.evidence-not-unknown=28;exp.critical-alert=4;exp.high-never-monitor=0.

## Significance (paired over seeds, hold-out fitness)

| model | policy | comparison | mean diff | 95% bootstrap CI | sign-flip p | wins/ties/losses |
|---|---|---|---|---|---|---|
| glm | should-arbitrate? | LLM+swarm vs-swarm | +0.1545 | [+0.0512, +0.3130] | 0.0156 | 7/1/0 |
| glm | should-arbitrate? | LLM+swarm vs-llm-only | +0.1742 | [+0.1172, +0.2313] | 0.0078 | 8/0/0 |
| glm | claim-root-cause | LLM+swarm vs-swarm | -0.1670 | [-0.1670, -0.1670] | 0.0078 | 0/0/8 |
| glm | claim-root-cause | LLM+swarm vs-llm-only | +0.7250 | [+0.7250, +0.7250] | 0.0078 | 8/0/0 |
| glm | claim-root-cause | LLM+swarm vs-swarm (hard hold-out) | -0.1460 | [-0.1460, -0.1460] | 0.0078 | 0/0/8 |
| glm | claim-root-cause | LLM+swarm vs-llm-only (hard hold-out) | +1.1490 | [+1.1490, +1.1490] | 0.0078 | 8/0/0 |
| glm | expedite-response | LLM+swarm vs-swarm | +0.0216 | [-0.0062, +0.0575] | 0.25 | 3/3/2 |
| glm | expedite-response | LLM+swarm vs-llm-only | +0.1377 | [-0.0178, +0.3196] | 0.25 | 3/2/3 |
| minimax | should-arbitrate? | LLM+swarm vs-swarm | +0.1674 | [+0.0701, +0.3203] | 0.0156 | 7/1/0 |
| minimax | should-arbitrate? | LLM+swarm vs-llm-only | +0.1799 | [+0.1250, +0.2313] | 0.0078 | 8/0/0 |
| minimax | claim-root-cause | LLM+swarm vs-swarm | -0.0418 | [-0.1044, +0.0000] | 0.5 | 0/6/2 |
| minimax | claim-root-cause | LLM+swarm vs-llm-only | +0.1812 | [+0.0000, +0.4531] | 0.5 | 2/6/0 |
| minimax | claim-root-cause | LLM+swarm vs-swarm (hard hold-out) | -0.2019 | [-0.3308, -0.0734] | 0.0625 | 0/3/5 |
| minimax | claim-root-cause | LLM+swarm vs-llm-only (hard hold-out) | +0.4526 | [+0.1654, +0.7732] | 0.0625 | 5/3/0 |
| minimax | expedite-response | LLM+swarm vs-swarm | -0.0066 | [-0.0551, +0.0284] | 0.9375 | 3/3/2 |
| minimax | expedite-response | LLM+swarm vs-llm-only | -0.0521 | [-0.1006, -0.0171] | 0.0625 | 0/3/5 |

## Per model

| model | calls | valid (parse ok) | gate pass | input tok | output tok (reasoning) | latency mean / p50 / max s | list-price USD | accepted LLM-only / LLM+swarm | USD per accepted LLM-only / LLM+swarm | evals per accepted LLM+swarm |
|---|---|---|---|---|---|---|---|---|---|---|
| glm (glm-5.3-flash) | 96 | 1.00 {'valid': 96} | 49/96 (0.51) | 108054 | 261182 (242432) | 68.7 / 34.1 / 335.0 | 0.1468 | 15 / 24 (of 24) | 0.00979 / 0.00612 | 241.3 |
| minimax (MiniMax-M3.1-Flash) | 96 | 1.00 {'valid': 96} | 70/96 (0.73) | 144862 | 560698 (544022) | 56.06 / 39.27 / 198.1 | 0.35815 | 22 / 24 (of 24) | 0.01628 / 0.01492 | 187.9 |

'accepted' = a (seed, policy) whose result beats v1 on TRAIN fitness and passes the business gate vs v1; the JSON also counts how many of those are better on the hold-out rows.

## Example reasons

- **glm / should-arbitrate?**: v1's 20 false arbitrations (rate 0.714) are mostly low-confidence events (0.44-0.67). Adding (high-confidence? edi-change) gates on confidence >= 0.7, suppressing those rows; recall should hold at 1.0 since every costly row was a false positive, not a miss, and exposure/pct/frozen guards stay unchanged.
- **glm / claim-root-cause**: All 8 shown failures are demand-forecast-error labeled 'unknown': market-mismatch=#t rows have no forecast-bias, and bias rows (0.065-0.081) fall under the 0.1 cutoff. Broadening the forecast branch to fire on market-signal-mismatch and lowering the bias threshold to 0.06 covers them (~1.33M) without touching the supplier-delay rules.
- **glm / expedite-response**: All 34 alt-supplier rows cost 45000 though observed transfer-days are 2-4 and sister stock is usually present; rows like high/10.0 or high/13.2 would be fine with propose-internal-rebalance at 6000. I route medium/high with inventory-days>=5 to rebalance (fallback still times like alt), keeping the high/<5 alert and alt for tighter stock, so stockouts stay flat while cost drops.
- **minimax / should-arbitrate?**: Add the supplied high-confidence gate to the existing conditions. V1 makes 20 false arbitrations among 28 decisions (71.4%) while recall is 1.0; six of eight listed false positives have confidence below 0.7 and would be suppressed, sharply lowering false-arbitration rate while preserving the 0.8 recall requirement.
- **minimax / claim-root-cause**: v1’s accuracy is 0.708 with 23 unknowns and 3,161,000 recovered. The shown demand-forecast-error failures have either market-mismatch=true or bias amounts 0.065–0.081, below the 0.1 cutoff. Broaden that branch to market mismatch OR bias >0.05, preserving supplier-delay precedence and targeting accuracy and recovery.
- **minimax / expedite-response**: Change the medium/high branch from alternative-supplier to internal-rebalance. V1's 34 switches cost 1,530,000 and accompany 4 stockouts (2,165,000 total). Rebalance costs 6,000 with sister stock and falls back otherwise; transfer is earlier in the medium/2.8 failure (3 versus 4 days), reducing cost without raising stockouts.

## Commits (first seed)

- `llmcommit.trial.glm.should-arbitrate?.gate` = pass
- `llmcommit.trial.glm.should-arbitrate?.fiber-metrics-equal` = #t
- `llmcommit.trial.glm.should-arbitrate?.reason` = LLM glm: v1's 20 false arbitrations (rate 0.714) are mostly low-confidence events (0.44-0.67). Adding (high-confidence? edi-change) gates on confidence >= 0.7, suppressing those rows; recall should hold at 1.0 since every costly row was a false positive, not a miss, and exposure/pct/frozen guards stay unchanged. | swarm aco,pso,aco: llm-proposal #1255 -> base #1259 -> best #1470 (198 evals, train fit 0.889)
- `llmcommit.trial.glm.claim-root-cause.gate` = pass
- `llmcommit.trial.glm.claim-root-cause.fiber-metrics-equal` = #t
- `llmcommit.trial.glm.claim-root-cause.reason` = LLM glm: no proposal passed the gate: swarm starts from v1 | swarm aco,pso,aco: llm-proposal #none -> base #1680 -> best #1687 (264 evals, train fit 1.812)
- `llmcommit.trial.glm.expedite-response.gate` = pass
- `llmcommit.trial.glm.expedite-response.fiber-metrics-equal` = #t
- `llmcommit.trial.glm.expedite-response.reason` = LLM glm: All 4 stockouts came from the 34 suggest-alternative-supplier rows (alt lead 4-7d vs 2.8-5.3d inventory). Alert-planner costs 35000 vs 45000 and always arrives on time, so it strictly dominates; swapping the medium+ branch action cuts cost to ~1.225M and removes every stockout. | swarm aco,pso,aco: llm-proposal #2100 -> base #2101 -> best #2419 (300 evals, train fit -1.026)
- `llmcommit.restore.glm` = v1-metrics-restored
- `llmcommit.trial.minimax.should-arbitrate?.gate` = pass
- `llmcommit.trial.minimax.should-arbitrate?.fiber-metrics-equal` = #t
- `llmcommit.trial.minimax.should-arbitrate?.reason` = LLM minimax: Add the missing high-confidence condition and tighten materiality/exposure to 0.2 and 1,000,000. This excludes low-confidence false positives (0.60–0.67), the 0.194/680,000 case, and the -0.428/690,000/0.91 case, reducing v1’s 71.4% false-arbitration rate while targeting recall ≥0.8. | swarm aco,pso,aco: llm-proposal #2520 -> base #2522 -> best #2720 (202 evals, train fit 1.0)
- `llmcommit.trial.minimax.claim-root-cause.gate` = pass
- `llmcommit.trial.minimax.claim-root-cause.fiber-metrics-equal` = #t
- `llmcommit.trial.minimax.claim-root-cause.reason` = LLM minimax: no proposal passed the gate: swarm starts from v1 | swarm aco,pso,aco: llm-proposal #none -> base #2943 -> best #3264 (257 evals, train fit 1.812)
- `llmcommit.trial.minimax.expedite-response.gate` = pass
- `llmcommit.trial.minimax.expedite-response.fiber-metrics-equal` = #t
- `llmcommit.trial.minimax.expedite-response.reason` = LLM minimax: Change the medium/high supplier-switch branch to alert-planner. V1’s 34 switches cost 1.53M; routing all 35 non-low events to premium freight costs 1.225M and guarantees timely arrival, eliminating four stockouts, including the medium 5.3- and 2.8-day failure rows. Cost falls from 2.165M to 1.225M, stockouts fall from 4 to 0, and fitness improves from -2.565 to -1.225. | swarm aco,pso,aco: llm-proposal #3361 -> base #3364 -> best #3364 (207 evals, train fit -1.225)
- `llmcommit.restore.minimax` = v1-metrics-restored
- `llmcommit.keep.minimax.should-arbitrate?.gate` = pass
- `llmcommit.keep.minimax.should-arbitrate?.fiber-metrics-equal` = #t
- `llmcommit.keep.minimax.should-arbitrate?.reason` = LLM minimax: Add the missing high-confidence condition and tighten materiality/exposure to 0.2 and 1,000,000. This excludes low-confidence false positives (0.60–0.67), the 0.194/680,000 case, and the -0.428/690,000/0.91 case, reducing v1’s 71.4% false-arbitration rate while targeting recall ≥0.8. | swarm aco,pso,aco: llm-proposal #2520 -> base #2522 -> best #2720 (202 evals, train fit 1.0)
- `llmcommit.keep.glm.claim-root-cause.gate` = pass
- `llmcommit.keep.glm.claim-root-cause.fiber-metrics-equal` = #t
- `llmcommit.keep.glm.claim-root-cause.reason` = LLM glm: no proposal passed the gate: swarm starts from v1 | swarm aco,pso,aco: llm-proposal #none -> base #1680 -> best #1687 (264 evals, train fit 1.812)
- `llmcommit.keep.glm.expedite-response.gate` = pass
- `llmcommit.keep.glm.expedite-response.fiber-metrics-equal` = #t
- `llmcommit.keep.glm.expedite-response.reason` = LLM glm: All 4 stockouts came from the 34 suggest-alternative-supplier rows (alt lead 4-7d vs 2.8-5.3d inventory). Alert-planner costs 35000 vs 45000 and always arrives on time, so it strictly dominates; swapping the medium+ branch action cuts cost to ~1.225M and removes every stockout. | swarm aco,pso,aco: llm-proposal #2100 -> base #2101 -> best #2419 (300 evals, train fit -1.026)

# LLM + swarm search: hold-out comparison

Models glm, minimax; seeds 20261028, 20261029, 20261030; K=4 proposals per policy per seed; fibers N=8; search (first seed) seed=20261028 pso=16x10 aco=16x8 reps=5 noise=0.1; every seed reseeds the swarm (SCM_SEARCH_SEED) and has its own LLM samples. Selection uses the TRAIN rows only; hold-out = 120 EDI changes / 96 claims / 80 risk events from an independent seed.

| policy | arm | hold-out fitness (mean ± sd) | train fitness | gap train−hold-out | hold-out metrics (first seed) | evals | gate reject rate |
|---|---|---|---|---|---|---|---|
| should-arbitrate? | v1 | 0.295 ± 0.000 | 0.286 | -0.009 | 61;43;0.705;1 | - | - |
| should-arbitrate? | v2 | 0.889 ± 0.000 | 0.875 | -0.014 | 16;0.0;0.0;0.889 | - | - |
| should-arbitrate? | swarm | 0.889 ± 0.000 | 1.000 | 0.111 | 16;0.0;0.0;0.889 | 209 | 0.179 |
| should-arbitrate? | llm:glm | 0.750 ± 0.000 | 0.500 | -0.250 | 24;6;0.25;1 | 4 | 0.000 |
| should-arbitrate? | llm+swarm:glm | 0.967 ± 0.047 | 0.963 | -0.004 | 20;2;0.1;1 | 197 | 0.144 |
| should-arbitrate? | llm:minimax | 0.846 ± 0.068 | 0.701 | -0.146 | 16;0.0;0.0;0.889 | 4 | 0.000 |
| should-arbitrate? | llm+swarm:minimax | 1.000 ± 0.000 | 1.000 | 0.000 | 18;0.0;0.0;1 | 196 | 0.160 |
| claim-root-cause | v1 | 1.108 ± 0.000 | 1.315 | 0.207 | 0.615;53;4907000;0.493 | - | - |
| claim-root-cause | v2 | 2.000 ± 0.000 | 2.000 | 0.000 | 1;16;9953000;1 | - | - |
| claim-root-cause | swarm | 2.000 ± 0.000 | 2.000 | 0.000 | 1;16;9953000;1 | 219 | 0.096 |
| claim-root-cause | llm:glm | 1.896 ± 0.000 | 2.000 | 0.104 | 0.958;20;9340000;0.938 | 4 | 0.167 |
| claim-root-cause | llm+swarm:glm | 1.896 ± 0.000 | 2.000 | 0.104 | 0.958;20;9340000;0.938 | 313 | 0.085 |
| claim-root-cause | llm:minimax | 1.927 ± 0.000 | 2.000 | 0.073 | 0.969;19;9539000;0.958 | 4 | 0.000 |
| claim-root-cause | llm+swarm:minimax | 1.927 ± 0.000 | 2.000 | 0.073 | 0.969;19;9539000;0.958 | 247 | 0.107 |
| expedite-response | v1 | -1.883 ± 0.000 | -2.565 | -0.682 | 5;52;0.0;5;3265000;80 | - | - |
| expedite-response | v2 | -1.838 ± 0.000 | -2.100 | -0.263 | 5;10;52;3;3376000;80 | - | - |
| expedite-response | swarm | -1.293 ± 0.000 | -1.010 | 0.283 | 45;2;12;3;2286000;80 | 221 | 0.150 |
| expedite-response | llm:glm | -0.757 ± 0.108 | -0.450 | 0.307 | 12;4;13;3;1245000;80 | 4 | 0.000 |
| expedite-response | llm+swarm:glm | -0.569 ± 0.055 | -0.346 | 0.223 | 12;2;4;3;993000;80 | 266 | 0.113 |
| expedite-response | llm:minimax | -1.038 ± 0.297 | -0.945 | 0.092 | 57;0.0;0.0;2;2295000;80 | 4 | 0.000 |
| expedite-response | llm+swarm:minimax | -1.285 ± 0.534 | -0.703 | 0.582 | 45;0.0;0.0;7;2625000;80 | 249 | 0.120 |

Metrics: should-arbitrate?: arbitrations, false_arbitrations, false_alarm_rate, recall; claim-root-cause: accuracy, unknown, recovered, recovery_rate; expedite-response: expedites, supplier_switches, rebalances, stockouts, cost, events

## Per model

| model | calls | valid (parse ok) | gate pass | input tok | output tok (reasoning) | latency mean / p50 / max s | list-price USD | accepted LLM-only / LLM+swarm | USD per accepted LLM-only / LLM+swarm | evals per accepted LLM+swarm |
|---|---|---|---|---|---|---|---|---|---|---|
| glm (glm-5.3-flash) | 36 | 0.97 {'valid': 35, 'api-error': 1} | 34/36 (0.94) | 38480 | 92570 (85819) | 71.32 / 35.29 / 191.38 | 0.05206 | 9 / 9 (of 9) | 0.00578 / 0.00578 | 258.8 |
| minimax (MiniMax-M3.1-Flash) | 36 | 1.00 {'valid': 36} | 36/36 (1.00) | 54329 | 221086 (214814) | 58.52 / 39.4 / 198.1 | 0.1408 | 9 / 9 (of 9) | 0.01564 / 0.01564 | 230.6 |

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
- `llmcommit.trial.glm.should-arbitrate?.reason` = LLM glm: v1's 20 false arbitrations (rate 0.714) are mostly low-confidence events (0.44-0.67). Adding (high-confidence? edi-change) gates on confidence >= 0.7, suppressing those rows; recall should hold at 1.0 since every costly row was a false positive, not a miss, and exposure/pct/frozen guards stay unchanged. | swarm aco,pso,aco: llm-proposal #1255 -> base #1259 -> best #1470 (202 evals, train fit 0.889)
- `llmcommit.trial.glm.claim-root-cause.gate` = pass
- `llmcommit.trial.glm.claim-root-cause.fiber-metrics-equal` = #t
- `llmcommit.trial.glm.claim-root-cause.reason` = LLM glm: All 8 shown failures are demand-forecast-error labeled 'unknown': market-mismatch=#t rows have no forecast-bias, and bias rows (0.065-0.081) fall under the 0.1 cutoff. Broadening the forecast branch to fire on market-signal-mismatch and lowering the bias threshold to 0.06 covers them (~1.33M) without touching the supplier-delay rules. | swarm aco,pso,aco: llm-proposal #1676 -> base #1680 -> best #1680 (304 evals, train fit 2.0)
- `llmcommit.trial.glm.expedite-response.gate` = pass
- `llmcommit.trial.glm.expedite-response.fiber-metrics-equal` = #t
- `llmcommit.trial.glm.expedite-response.reason` = LLM glm: All 4 stockouts were medium-level with tiny inventory (2.8, 5.3d): alerting medium below 6 days fixes these (35000 vs 195000). Costly rows at 10-13.2d had regular-lead 4-8 covering demand, so >=9d goes to monitor (0 vs 45000, e.g. the 11.5/12.4/13.2 rows). A 6-9d rebalance branch cuts 45000 switches to 6000. | swarm aco,pso,aco: llm-proposal #2099 -> base #2101 -> best #2296 (324 evals, train fit -0.3385)
- `llmcommit.restore.glm` = v1-metrics-restored
- `llmcommit.trial.minimax.should-arbitrate?.gate` = pass
- `llmcommit.trial.minimax.should-arbitrate?.fiber-metrics-equal` = #t
- `llmcommit.trial.minimax.should-arbitrate?.reason` = LLM minimax: Add the missing high-confidence condition and tighten materiality/exposure to 0.2 and 1,000,000. This excludes low-confidence false positives (0.60–0.67), the 0.194/680,000 case, and the -0.428/690,000/0.91 case, reducing v1’s 71.4% false-arbitration rate while targeting recall ≥0.8. | swarm aco,pso,aco: llm-proposal #2520 -> base #2522 -> best #2720 (205 evals, train fit 1.0)
- `llmcommit.trial.minimax.claim-root-cause.gate` = pass
- `llmcommit.trial.minimax.claim-root-cause.fiber-metrics-equal` = #t
- `llmcommit.trial.minimax.claim-root-cause.reason` = LLM minimax: v1’s accuracy is 0.708 with 23 unknowns and 3,161,000 recovered. The shown demand-forecast-error failures have either market-mismatch=true or bias amounts 0.065–0.081, below the 0.1 cutoff. Broaden that branch to market mismatch OR bias >0.05, preserving supplier-delay precedence and targeting accuracy and recovery. | swarm aco,pso,aco: llm-proposal #2939 -> base #2943 -> best #2943 (264 evals, train fit 2.0)
- `llmcommit.trial.minimax.expedite-response.gate` = pass
- `llmcommit.trial.minimax.expedite-response.fiber-metrics-equal` = #t
- `llmcommit.trial.minimax.expedite-response.reason` = LLM minimax: Change the medium/high supplier-switch branch to alert-planner. V1’s 34 switches cost 1.53M; routing all 35 non-low events to premium freight costs 1.225M and guarantees timely arrival, eliminating four stockouts, including the medium 5.3- and 2.8-day failure rows. Cost falls from 2.165M to 1.225M, stockouts fall from 4 to 0, and fitness improves from -2.565 to -1.225. | swarm aco,pso,aco: llm-proposal #3361 -> base #3364 -> best #3670 (285 evals, train fit -0.88)
- `llmcommit.restore.minimax` = v1-metrics-restored
- `llmcommit.keep.minimax.should-arbitrate?.gate` = pass
- `llmcommit.keep.minimax.should-arbitrate?.fiber-metrics-equal` = #t
- `llmcommit.keep.minimax.should-arbitrate?.reason` = LLM minimax: Add the missing high-confidence condition and tighten materiality/exposure to 0.2 and 1,000,000. This excludes low-confidence false positives (0.60–0.67), the 0.194/680,000 case, and the -0.428/690,000/0.91 case, reducing v1’s 71.4% false-arbitration rate while targeting recall ≥0.8. | swarm aco,pso,aco: llm-proposal #2520 -> base #2522 -> best #2720 (205 evals, train fit 1.0)
- `llmcommit.keep.glm.claim-root-cause.gate` = pass
- `llmcommit.keep.glm.claim-root-cause.fiber-metrics-equal` = #t
- `llmcommit.keep.glm.claim-root-cause.reason` = LLM glm: All 8 shown failures are demand-forecast-error labeled 'unknown': market-mismatch=#t rows have no forecast-bias, and bias rows (0.065-0.081) fall under the 0.1 cutoff. Broadening the forecast branch to fire on market-signal-mismatch and lowering the bias threshold to 0.06 covers them (~1.33M) without touching the supplier-delay rules. | swarm aco,pso,aco: llm-proposal #1676 -> base #1680 -> best #1680 (304 evals, train fit 2.0)
- `llmcommit.keep.glm.expedite-response.gate` = pass
- `llmcommit.keep.glm.expedite-response.fiber-metrics-equal` = #t
- `llmcommit.keep.glm.expedite-response.reason` = LLM glm: All 4 stockouts were medium-level with tiny inventory (2.8, 5.3d): alerting medium below 6 days fixes these (35000 vs 195000). Costly rows at 10-13.2d had regular-lead 4-8 covering demand, so >=9d goes to monitor (0 vs 45000, e.g. the 11.5/12.4/13.2 rows). A 6-9d rebalance branch cuts 45000 switches to 6000. | swarm aco,pso,aco: llm-proposal #2099 -> base #2101 -> best #2296 (324 evals, train fit -0.3385)

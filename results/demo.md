# aura-scm-agents demo results

wall time: 2.1s (deterministic; agents are pumped by one supervisor, see README)

## CASE-1: decision=approved human-required=#t

- exposure 910000, arbitrate=#t, hypothesis: customer pull-in confirmed by firm release (demand-side), not a forecast miss
- impacted nodes 7 (max hop 3), plan cost 716625, expedites 1
- forensics batch status=partial ok=7 err=1, total leakage 188000
- claims supplier-delay=16 demand-forecast-error=9 unknown=23, recovery opportunity 1896000
- execution: done 6, lost 0, risk scope tasks missing 0, cancel -

| node | action | detail | cost |
|---|---|---|---|
| BRK-200 | expedite-review | alert planner: immediate expedite review (air freight) | cost=663000 |
| CST-7 | rebalance | transfer 2500 units from sister plant (supervisor override) | cost=3750 |
| RES-3 | rebalance | transfer 2350 units from sister plant (supervisor override) | cost=3525 |
| KNU-55 | rebalance | transfer 450 units from sister plant (supervisor override) | cost=675 |
| CAL-12 | rebalance | transfer 450 units from sister plant (supervisor override) | cost=675 |
| ALU-1 | alt-supplier | qualify alternative supplier SUP-T3-L | cost=45000 |
| PAD-9 | monitor | monitor coverage | cost=0 |

- conflict: CST-7: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 3750 vs 45000)
- conflict: RES-3: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 3525 vs 45000)
- conflict: KNU-55: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 675 vs 45000)
- conflict: CAL-12: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 675 vs 45000)
- rule: PREVENT: hold 10-day safety stock on CST-7 while SUP-T2-C on-time-delivery < 90%; auto-raise lead-time-miss claim
- rule: PREVENT: route EDI releases with forecast bias or market-signal mismatch to planner review before expediting
- rule: RECOVER: file supplier claim vs SUP-T2-C for unrecovered air-freight leakage 37000

## CASE-2: decision=rejected human-required=#t

- exposure 910000, arbitrate=#t, hypothesis: customer pull-in confirmed by firm release (demand-side), not a forecast miss
- impacted nodes 7 (max hop 3), plan cost 716625, expedites 1
- forensics batch status=partial ok=7 err=1, total leakage 188000
- claims supplier-delay=16 demand-forecast-error=9 unknown=23, recovery opportunity 1896000
- execution: done 0, lost 0, risk scope tasks missing 0, cancel cancelled-count=6

| node | action | detail | cost |
|---|---|---|---|
| BRK-200 | expedite-review | alert planner: immediate expedite review (air freight) | cost=663000 |
| CST-7 | rebalance | transfer 2500 units from sister plant (supervisor override) | cost=3750 |
| RES-3 | rebalance | transfer 2350 units from sister plant (supervisor override) | cost=3525 |
| KNU-55 | rebalance | transfer 450 units from sister plant (supervisor override) | cost=675 |
| CAL-12 | rebalance | transfer 450 units from sister plant (supervisor override) | cost=675 |
| ALU-1 | alt-supplier | qualify alternative supplier SUP-T3-L | cost=45000 |
| PAD-9 | monitor | monitor coverage | cost=0 |

- conflict: CST-7: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 3750 vs 45000)
- conflict: RES-3: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 3525 vs 45000)
- conflict: KNU-55: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 675 vs 45000)
- conflict: CAL-12: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 675 vs 45000)
- rule: PREVENT: hold 10-day safety stock on CST-7 while SUP-T2-C on-time-delivery < 90%; auto-raise lead-time-miss claim
- rule: PREVENT: route EDI releases with forecast bias or market-signal mismatch to planner review before expediting
- rule: RECOVER: file supplier claim vs SUP-T2-C for unrecovered air-freight leakage 37000

## CASE-3: decision=approved human-required=#t

- exposure 910000, arbitrate=#t, hypothesis: customer pull-in confirmed by firm release (demand-side), not a forecast miss
- impacted nodes 7 (max hop 3), plan cost 671625, expedites 1
- forensics batch status=partial ok=7 err=1, total leakage 188000
- claims supplier-delay=16 demand-forecast-error=23 unknown=9, recovery opportunity 1896000
- execution: done 5, lost 0, risk scope tasks missing 0, cancel -

| node | action | detail | cost |
|---|---|---|---|
| BRK-200 | expedite-review | alert planner: immediate expedite review (air freight) | cost=663000 |
| CST-7 | rebalance | transfer 2500 units from sister plant | cost=3750 |
| RES-3 | rebalance | transfer 2350 units from sister plant | cost=3525 |
| KNU-55 | rebalance | transfer 450 units from sister plant | cost=675 |
| CAL-12 | rebalance | transfer 450 units from sister plant | cost=675 |
| ALU-1 | monitor | rebalance not needed (covered over horizon) | cost=0 |
| PAD-9 | monitor | monitor coverage | cost=0 |

- rule: PREVENT: hold 10-day safety stock on CST-7 while SUP-T2-C on-time-delivery < 90%; auto-raise lead-time-miss claim
- rule: PREVENT: route EDI releases with forecast bias or market-signal mismatch to planner review before expediting
- rule: RECOVER: file supplier claim vs SUP-T2-C for unrecovered air-freight leakage 37000

## Policy evolution (v1 -> v2 -> bad -> rollback)

| policy | metric | v1 | v2 | bad | after rollback |
|---|---|---|---|---|---|
| should-arbitrate? | arbitrations | 28 | 7 | 2 | 7 |
| should-arbitrate? | false-arbitrations | 20 | 0 | 0 | 0 |
| should-arbitrate? | false-arbitration-rate | 0.714 | 0.0 | 0.0 | 0.0 |
| should-arbitrate? | recall | 1.0 | 0.875 | 0.25 | 0.875 |
| should-arbitrate? | gate v2 / bad |  | pass | fail | restored=#t |
| claim-root-cause | accuracy | 0.708 | 1.0 | 0.542 | 1.0 |
| claim-root-cause | unknown | 23 | 9 | 3 | 9 |
| claim-root-cause | recovered | 3161000 | 5210000 | 3351000 | 5210000 |
| claim-root-cause | recovery-rate | 0.607 | 1.0 | 0.643 | 1.0 |
| claim-root-cause | gate v2 / bad |  | pass | fail | restored=#t |
| expedite-response | expedites | 1 | 1 | 1 | 1 |
| expedite-response | supplier-switches | 34 | 6 | 0 | 6 |
| expedite-response | rebalances | 0 | 34 | 0 | 34 |
| expedite-response | stockouts | 4 | 3 | 7 | 3 |
| expedite-response | cost | 2165000 | 1800500 | 1085000 | 1800500 |
| expedite-response | gate v2 / bad |  | pass | fail | restored=#t |

parse gate: rejected: (parse-error expected expression, reached end of input; unclosed list: missing ')' before end of file . 0)

## Audit trail

| seq | t-ms | actor | action | detail |
|---|---|---|---|---|
| 1 | 6 | supervisor | install-policies | should-arbitrate?@v1 claim-root-cause@v1 expedite-response@v1 |
| 2 | 7 | supervisor | spawn-agent | supervisor id=1 |
| 3 | 7 | supervisor | spawn-agent | demand id=2 |
| 4 | 7 | supervisor | spawn-agent | risk id=3 |
| 5 | 7 | supervisor | spawn-agent | forensics id=4 |
| 6 | 7 | supervisor | spawn-agent | claims id=5 |
| 7 | 7 | supervisor | case-open | CASE-1 OEM-A promotion pull-in; weekly 830 release +35% |
| 8 | 209 | supervisor | run-workflow | CASE-1 validate stages-ok=2 ok=#t |
| 9 | 210 | demand | explain | CASE-1 part=BRK-200 pct=0.35 exposure=910000 should-arbitrate?=#t |
| 10 | 210 | demand | trigger-risk | CASE-1 |
| 11 | 211 | risk | recv-arbitration-signal | CASE-1 signal=arbitrate from=demand |
| 12 | 211 | risk | graph-impact | CASE-1 hops=3 nodes=7 cascade=(KNU-55) |
| 13 | 312 | risk | scope-join-all | CASE-1 status=ok spawned=7 |
| 14 | 313 | risk | propose | CASE-1 BRK-200 expedite-review cost=663000 |
| 15 | 313 | risk | propose | CASE-1 CST-7 alt-supplier cost=45000 |
| 16 | 313 | risk | propose | CASE-1 RES-3 alt-supplier cost=45000 |
| 17 | 313 | risk | propose | CASE-1 KNU-55 alt-supplier cost=45000 |
| 18 | 313 | risk | propose | CASE-1 CAL-12 alt-supplier cost=45000 |
| 19 | 313 | risk | propose | CASE-1 ALU-1 alt-supplier cost=45000 |
| 20 | 313 | risk | propose | CASE-1 PAD-9 monitor cost=0 |
| 21 | 314 | supervisor | demand-reply | arbitrate=#t;exposure=910000 |
| 22 | 414 | forensics | supervise-batch | CASE-1 status=partial ok=7 err=1 (malformed record isolated, collect-all) |
| 23 | 414 | forensics | evidence->claims | CASE-1 |
| 24 | 416 | claims | classify | CASE-1 supplier-delay=16 demand-forecast-error=9 unknown=23 recovery=1896000 |
| 25 | 416 | supervisor | forensics-reply | chains=4;leak=188000 |
| 26 | 417 | supervisor | resolve-conflict | CST-7: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 3750 vs 45000) |
| 27 | 417 | supervisor | resolve-conflict | RES-3: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 3525 vs 45000) |
| 28 | 417 | supervisor | resolve-conflict | KNU-55: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 675 vs 45000) |
| 29 | 417 | supervisor | resolve-conflict | CAL-12: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 675 vs 45000) |
| 30 | 418 | supervisor | route-human | CASE-1 arbitrate=#t expedites=1 cost=716625 |
| 31 | 418 | human | approved | CASE-1 (simulated planner) |
| 32 | 515 | supervisor | scope-join-all | CASE-1 status=ok |
| 33 | 516 | supervisor | case-open | CASE-2 OEM-A promotion pull-in; weekly 830 release +35% |
| 34 | 715 | supervisor | run-workflow | CASE-2 validate stages-ok=2 ok=#t |
| 35 | 716 | demand | explain | CASE-2 part=BRK-200 pct=0.35 exposure=910000 should-arbitrate?=#t |
| 36 | 716 | demand | trigger-risk | CASE-2 |
| 37 | 717 | risk | recv-arbitration-signal | CASE-2 signal=arbitrate from=demand |
| 38 | 717 | risk | graph-impact | CASE-2 hops=3 nodes=7 cascade=(KNU-55) |
| 39 | 817 | risk | scope-join-all | CASE-2 status=ok spawned=7 |
| 40 | 818 | risk | propose | CASE-2 BRK-200 expedite-review cost=663000 |
| 41 | 818 | risk | propose | CASE-2 CST-7 alt-supplier cost=45000 |
| 42 | 818 | risk | propose | CASE-2 RES-3 alt-supplier cost=45000 |
| 43 | 818 | risk | propose | CASE-2 KNU-55 alt-supplier cost=45000 |
| 44 | 818 | risk | propose | CASE-2 CAL-12 alt-supplier cost=45000 |
| 45 | 818 | risk | propose | CASE-2 ALU-1 alt-supplier cost=45000 |
| 46 | 818 | risk | propose | CASE-2 PAD-9 monitor cost=0 |
| 47 | 819 | supervisor | demand-reply | arbitrate=#t;exposure=910000 |
| 48 | 921 | forensics | supervise-batch | CASE-2 status=partial ok=7 err=1 (malformed record isolated, collect-all) |
| 49 | 921 | forensics | evidence->claims | CASE-2 |
| 50 | 922 | claims | classify | CASE-2 supplier-delay=16 demand-forecast-error=9 unknown=23 recovery=1896000 |
| 51 | 923 | supervisor | forensics-reply | chains=4;leak=188000 |
| 52 | 924 | supervisor | resolve-conflict | CST-7: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 3750 vs 45000) |
| 53 | 924 | supervisor | resolve-conflict | RES-3: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 3525 vs 45000) |
| 54 | 924 | supervisor | resolve-conflict | KNU-55: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 675 vs 45000) |
| 55 | 924 | supervisor | resolve-conflict | CAL-12: risk=alt-supplier vs forensics=switch-leakage 58000 -> rebalance (cost 675 vs 45000) |
| 56 | 924 | supervisor | route-human | CASE-2 arbitrate=#t expedites=1 cost=716625 |
| 57 | 924 | human | rejected | CASE-2 (simulated planner) |
| 58 | 924 | supervisor | scope-cancel-all | CASE-2 cancelled-count=6 |
| 59 | 1022 | supervisor | scope-join-all | CASE-2 status=ok |
| 60 | 1023 | demand | mutate:rebind REJECTED | should-arbitrate? broken patch -> (parse-error expected expression, reached end of input; unclosed list: missing ')' before end of file . 0) |
| 61 | 1025 | demand | locate | should-arbitrate? query:calls=(173) def-use=((96) 170) snapshot=0 |
| 62 | 1029 | demand | mutate:rebind | should-arbitrate?@v2 reason=阈值从15%调至22%，库存门槛提高，增加置信度过滤，减少误报 gate=pass before={arbitrations=28 false-arbitration-rate=0.714 false-arbitrations=20 needed=8 recall=1.0} after={arbitrations=7 false-arbitration-rate=0.0 false-arbitrations=0 needed=8 recall=0.875} |
| 63 | 1029 | supervisor | ast:snapshot | should-arbitrate?@v2 snapshot=1 |
| 64 | 1032 | demand | mutate:rebind | should-arbitrate?@bad reason=进一步把阈值提到40%以压低仲裁量（实验） gate=fail before={arbitrations=7 false-arbitration-rate=0.0 false-arbitrations=0 needed=8 recall=0.875} after={arbitrations=2 false-arbitration-rate=0.0 false-arbitrations=0 needed=8 recall=0.25} |
| 65 | 1037 | supervisor | ast:restore | should-arbitrate? rolled back to snapshot 1 (gate fail on bad) |
| 66 | 1038 | claims | locate | claim-root-cause query:calls=(178) def-use=((126) 176) snapshot=2 |
| 67 | 1042 | claims | mutate:rebind | claim-root-cause@v2 reason=增加市场信号不匹配作为预测误差判定条件 gate=pass before={accuracy=0.708 recovered=3161000 recovery-rate=0.607 unknown=23} after={accuracy=1.0 recovered=5210000 recovery-rate=1.0 unknown=9} |
| 68 | 1042 | supervisor | ast:snapshot | claim-root-cause@v2 snapshot=3 |
| 69 | 1046 | claims | mutate:rebind | claim-root-cause@bad reason=把需求侧判定前置（实验） gate=fail before={accuracy=1.0 recovered=5210000 recovery-rate=1.0 unknown=9} after={accuracy=0.542 recovered=3351000 recovery-rate=0.643 unknown=3} |
| 70 | 1049 | supervisor | ast:restore | claim-root-cause rolled back to snapshot 3 (gate fail on bad) |
| 71 | 1051 | risk | locate | expedite-response query:calls=(184) def-use=((169) 181) snapshot=4 |
| 72 | 1056 | risk | mutate:rebind | expedite-response@v2 reason=medium风险改为优先内部再平衡，降低不必要的供应商切换 gate=pass before={cost=2165000 events=40 expedites=1 rebalances=0 stockouts=4 supplier-switches=34} after={cost=1800500 events=40 expedites=1 rebalances=34 stockouts=3 supplier-switches=6} |
| 73 | 1056 | supervisor | ast:snapshot | expedite-response@v2 snapshot=5 |
| 74 | 1059 | risk | mutate:rebind | expedite-response@bad reason=medium风险只监控（实验） gate=fail before={cost=1800500 events=40 expedites=1 rebalances=34 stockouts=3 supplier-switches=6} after={cost=1085000 events=40 expedites=1 rebalances=0 stockouts=7 supplier-switches=0} |
| 75 | 1061 | supervisor | ast:restore | expedite-response rolled back to snapshot 5 (gate fail on bad) |
| 76 | 1062 | supervisor | case-open | CASE-3 OEM-A promotion pull-in; weekly 830 release +35% |
| 77 | 1223 | supervisor | run-workflow | CASE-3 validate stages-ok=2 ok=#t |
| 78 | 1223 | demand | explain | CASE-3 part=BRK-200 pct=0.35 exposure=910000 should-arbitrate?=#t |
| 79 | 1223 | demand | trigger-risk | CASE-3 |
| 80 | 1224 | risk | recv-arbitration-signal | CASE-3 signal=arbitrate from=demand |
| 81 | 1224 | risk | graph-impact | CASE-3 hops=3 nodes=7 cascade=(KNU-55) |
| 82 | 1324 | risk | scope-join-all | CASE-3 status=ok spawned=7 |
| 83 | 1325 | risk | propose | CASE-3 BRK-200 expedite-review cost=663000 |
| 84 | 1325 | risk | propose | CASE-3 CST-7 rebalance cost=3750 |
| 85 | 1325 | risk | propose | CASE-3 RES-3 rebalance cost=3525 |
| 86 | 1325 | risk | propose | CASE-3 KNU-55 rebalance cost=675 |
| 87 | 1325 | risk | propose | CASE-3 CAL-12 rebalance cost=675 |
| 88 | 1325 | risk | propose | CASE-3 ALU-1 monitor cost=0 |
| 89 | 1325 | risk | propose | CASE-3 PAD-9 monitor cost=0 |
| 90 | 1326 | supervisor | demand-reply | arbitrate=#t;exposure=910000 |
| 91 | 1426 | forensics | supervise-batch | CASE-3 status=partial ok=7 err=1 (malformed record isolated, collect-all) |
| 92 | 1426 | forensics | evidence->claims | CASE-3 |
| 93 | 1428 | claims | classify | CASE-3 supplier-delay=16 demand-forecast-error=23 unknown=9 recovery=1896000 |
| 94 | 1428 | supervisor | forensics-reply | chains=4;leak=188000 |
| 95 | 1429 | supervisor | route-human | CASE-3 arbitrate=#t expedites=1 cost=671625 |
| 96 | 1429 | human | approved | CASE-3 (simulated planner) |
| 97 | 1528 | supervisor | scope-join-all | CASE-3 status=ok |

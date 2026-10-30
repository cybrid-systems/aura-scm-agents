# validation results (aura 69d360068)

| file | done | secs | pass | fail |
|---|---|---|---|---|
| v01_mailbox.aura | yes | 1.06 | 9 | 2 |
| v01b_spawn_gate.aura | yes | 31.1 | 2 | 1 |
| v02_scope.aura | yes | 7.06 | 6 | 1 |
| v03_batch_workflow.aura | yes | 5.07 | 4 | 1 |
| v04_workspace.aura | yes | 0.33 | 15 | 1 |
| v05_rebind_concurrent.aura | yes | 0.26 | 3 | 0 |
| v06_overlay.aura | yes | 0.09 | 7 | 0 |
| v07_channels.aura | yes | 2.97 | 6 | 0 |
| v08_parallel_determinism.aura | yes | 6.19 | 3 | 0 |
| v09_shared_state.aura | yes | 0.16 | 4 | 0 |
| v10_fiber_catch.aura | yes | 3.05 | 3 | 2 |

## checks

- `mailbox.fifo-250`: **PASS**
- `mailbox.empty-nonblocking`: **PASS**
- `mailbox.wait-timeout-bounded`: **PASS**
- `mailbox.structured-payload-rejected`: **PASS**
- `mailbox.unknown-agent-raises`: **PASS**
- `mailbox.respawn-keeps-or-refuses`: **FAIL (known: https://github.com/cybrid-systems/aura/issues/4785)** — spawn returned ok=#t and mailbox now holds (queued-after) (queued-before lost)
- `mailbox.concurrent-8x32-no-loss`: **PASS**
- `mailbox.concurrent-per-sender-fifo`: **PASS**
- `mailbox.bench-all-delivered`: **PASS**
- `mailbox.backpressure-reported`: **PASS**
- `lang.equal-long-lists`: **FAIL (known: https://github.com/cybrid-systems/aura/issues/4780)** — equal? on 100-element lists differing at index 70 => #t
- `spawngate.unrelated-spawn-refused-after-storm`: **PASS**
- `spawngate.recovers`: **PASS**
- `spawngate.retry-after-hint-honest`: **FAIL (known: https://github.com/cybrid-systems/aura/issues/4785)** — retry-after-ms=50 but admission took 30103 ms (121 refused retries)
- `scope.exactly-once-50x16`: **PASS**
- `scope.runs-after-run-workflow`: **PASS**
- `scope.runs-after-supervise-batch`: **PASS**
- `scope.failed-body-visible-in-join`: **FAIL (known: https://github.com/cybrid-systems/aura/issues/4783)** — a body raised but join-all says ok=#t status=ok; failure-ish keys: (join-fail-production-default-wired join-fail-action-taken on-join-fail-effective)
- `scope.join-timeout-bounded`: **PASS**
- `scope.cancel-no-done-no-hang`: **PASS**
- `scope.join-without-scope-raises`: **PASS**
- `batch.collect-all-counts`: **PASS**
- `batch.all-ok-status`: **PASS**
- `batch.retry-n-recovers-flaky`: **FAIL (known: https://github.com/cybrid-systems/aura/issues/4784)** — 'retry-n :max-retries 2 did not recover a task that fails twice: (partial 0 1 1)
- `workflow.stage-order`: **PASS**
- `workflow.stops-at-failed-stage`: **PASS**
- `ws.set-code+eval`: **PASS**
- `ws.query-calls-finds-caller`: **PASS**
- `ws.rebind-ok`: **PASS**
- `ws.rebind-visible-to-old-callers`: **PASS**
- `ws.reason-in-mutation-log`: **PASS**
- `ws.source-reflects-rebind`: **PASS**
- `ws.broken-rebind-rejected`: **PASS**
- `ws.broken-rebind-source-unchanged`: **PASS**
- `ws.broken-rebind-behaviour-unchanged`: **PASS**
- `ws.unbalanced-lambda-raises-4736`: **PASS**
- `ws.restore-byte-identical`: **PASS**
- `ws.restore-behaviour`: **PASS**
- `ws.restore-forward`: **FAIL (known: https://github.com/cybrid-systems/aura/issues/4782)** — after ast:restore S0 then ast:restore S1 (+eval-current): source-matches-S1=#t but caller(0.15)=absorb (S1 code says arbitrate)
- `ws.restore-invalid-id-no-change`: **PASS**
- `ws.cycles-flat-4737`: **PASS**
- `ws.after-200-cycles-restored`: **PASS**
- `rebindconc.no-errors-or-torn-results`: **PASS**
- `rebindconc.all-rebinds-accepted`: **PASS**
- `rebindconc.final-state-v2`: **PASS**
- `overlay.isolation-8-fibers`: **PASS**
- `overlay.main-unchanged`: **PASS**
- `overlay.first-committer-wins`: **PASS**
- `overlay.loser-gets-cow-conflict`: **PASS**
- `overlay.disjoint-commits`: **PASS**
- `overlay.set!-in-procedure-after-commit-4757`: **PASS**
- `overlay.report-counts-exact`: **PASS**
- `chan.8x500-cap16-no-loss`: **PASS**
- `chan.per-producer-fifo`: **PASS**
- `chan.structured-payload-4763`: **PASS**
- `chan.closure-payload-rejected-loudly`: **PASS**
- `chan.try-recv-empty-vs-#f-distinguishable`: **PASS**
- `chan.ping-pong-correct`: **PASS**
- `par.identical-across-widths`: **PASS**
- `par.some-parallel-speedup`: **PASS**
- `par.fiber-closures-capture-4745`: **PASS**
- `shared.distinct-key-hash-set-4730`: **PASS**
- `shared.atomic-hash-update-4761`: **PASS**
- `shared.atomic-counter`: **PASS**
- `shared.atomic-update-global`: **PASS**
- `fibercatch.try-body-sees-captured-param`: **PASS**
- `fibercatch.catch-sees-fiber-local`: **PASS**
- `fibercatch.catch-sees-captured-param`: **FAIL (known: https://github.com/cybrid-systems/aura/issues/4781)** — join-error: 63:78: unbound variable: p
- `fibercatch.main-thread-catch-sees-param`: **PASS**
- `fibercatch.search-wave-raising-candidate-reported`: **FAIL (known: https://github.com/cybrid-systems/aura/issues/4781)** — coordinator would block forever: results=(1|ok 3|ok timeout)

## benchmarks

| id | value |
|---|---|
| `mailbox.send-us` | 16.6 us/msg |
| `mailbox.recv-us` | 24.6 us/msg |
| `spawngate.recovery-ms` | 30103 ms |
| `scope.spawn+join-us-per-task` | 6271.25 us/task |
| `scope.join-latency-1task-median-ms` | 90 ms |
| `batch.collect-all-40-ms` | 8 ms |
| `workflow.2-stage-run-ms` | 170.55 ms/workflow |
| `ws.rebind+snapshot+restore-ms` | 0.695 ms/cycle |
| `ws.rebind-ms@10-defines` | 0.3 ms |
| `ws.snapshot-ms@10-defines` | 0.2 ms |
| `ws.restore-ms@10-defines` | 0.3 ms |
| `ws.rebind-ms@100-defines` | 0.3 ms |
| `ws.snapshot-ms@100-defines` | 0.5 ms |
| `ws.restore-ms@100-defines` | 0.6 ms |
| `ws.rebind-ms@400-defines` | 0.6 ms |
| `ws.snapshot-ms@400-defines` | 2.4 ms |
| `ws.restore-ms@400-defines` | 2.8 ms |
| `rebindconc.calls-per-ms` | 93.023 calls/ms |
| `overlay.private-eval-cycle-us` | 4.5 us/cycle |
| `chan.mpsc-throughput` | 108.108 msgs/ms |
| `chan.ping-pong-rtt-us` | 36.0 us/round-trip |
| `par.32-cands-width-1-ms` | 1933 ms |
| `par.32-cands-width-2-ms` | 1083 ms |
| `par.32-cands-width-4-ms` | 581 ms |
| `par.32-cands-width-8-ms` | 580 ms |
| `par.speedup-8-vs-1` | 3.333 x |
| `shared.atomic-add-ns` | 2125.0 ns/op (8 fibers) |

## observations

- `mailbox.number-payload-arrives-as`: string "42"
- `mailbox.respawn-same-name`: second spawn ok=#t id=6; drained=(queued-after)
- `mailbox.spawn-after-bp-storm`: ok=#f quota-dimension=mailbox-bp retry-after-ms=50 error=AdmissionRejected: mailbox backpressure (bp_recent=44 >= threshold=32 override=false source=process)
- `spawngate.first-refusal`: ok=#f retry-after-ms=50 error=AdmissionRejected: mailbox backpressure (bp_recent=44 >= threshold=32 override=false source=process)
- `spawngate.refused-attempts`: 121
- `scope.join-report-with-failed-body`: ok=#t status=ok join-fail-action-taken=0 on-join-fail-effective=report-only
- `scope.join-timeout-report`: ms=300 ok=#f status=timeout reclaimed-count=4 cleanup-pending-count=4 bodies-started-before-timeout=0/4
- `scope.after-release`: ok=#t bodies-finished=0/4
- `scope.cancel-all`: cancel=<hash[5]> join-status=ok ms=103 step-states=(aborted aborted aborted aborted aborted aborted)
- `scope.join-latency-samples-ms`: (90 8 93 7 93 8 92 8 93 7)
- `batch.report`: status=partial ok-count=34 err-count=6
- `batch.has-per-task-results`: #f
- `batch.collect-all+max-retries-2`: status=partial ok=0 err=1 attempts=1 (policy echoes max-retries=2)
- `batch.retry-n+max-retries-2`: status=partial ok=0 err=1 attempts=1
- `ws.locate`: query:calls=(15) def-use=((11) 12)
- `ws.restore-forward-second-try`: arbitrate
- `ws.restore-invalid-id-returns`: #f
- `ws.cycle-ms-per-50`: (33 34 35 37)
- `rebindconc.outcomes`: fibers=4 wait(v1)=6534 expedite(v2)=5466 other=0 rebinds=60 rebind-errors=0 ms=129 raw=(1706|1294|0 1651|1349|0 1583|1417|0 1594|1406|0)
- `overlay.pending-shape`: 2
- `overlay.conflict-loser`: raised:fiber:cow-conflict: Y binding=Y winner-fiber=10474370891395145692 our-epoch=0 committed-epoch=0 our-seq=0 winner-seq=1 kind=write-write (the same binding was committed by another fiber after this overlay began)
- `overlay.report`: begins=15 commits=6 fast-forward=6 merged=0 conflicts=1 rollbacks=8 writes=23 active=0 read-conflicts=0
- `chan.try-recv-empty-returns`: ""
- `chan.try-recv-of-#f-returns`: #f
- `chan.try-recv-empty-vs-empty-string`: ambiguous: an empty channel and a queued "" both return ""
- `par.note`: box has 8 cores shared with other workers; speedup is indicative only
- `shared.plain-rmw-lost-updates`: 700 of 2400 increments survived
- `fibercatch.search-wave-results`: (1|ok 3|ok timeout)

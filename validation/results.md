# validation results (aura a029752df)

| file | done | secs | pass | fail |
|---|---|---|---|---|
| v01_mailbox.aura | yes | 1.14 | 11 | 0 |
| v01b_spawn_gate.aura | yes | 31.09 | 3 | 0 |
| v02_scope.aura | yes | 1.06 | 7 | 0 |
| v03_batch_workflow.aura | yes | 1.05 | 5 | 0 |
| v04_workspace.aura | yes | 0.33 | 16 | 0 |
| v05_rebind_concurrent.aura | yes | 0.13 | 3 | 0 |
| v06_overlay.aura | yes | 0.06 | 7 | 0 |
| v07_channels.aura | yes | 1.62 | 6 | 0 |
| v08_parallel_determinism.aura | yes | 7.51 | 3 | 0 |
| v09_shared_state.aura | yes | 0.19 | 4 | 0 |
| v10_fiber_catch.aura | yes | 0.07 | 5 | 0 |

## checks

- `mailbox.fifo-250`: **PASS**
- `mailbox.empty-nonblocking`: **PASS**
- `mailbox.wait-timeout-bounded`: **PASS**
- `mailbox.structured-payload-rejected`: **PASS**
- `mailbox.unknown-agent-raises`: **PASS**
- `mailbox.respawn-keeps-or-refuses`: **PASS**
- `mailbox.concurrent-8x32-no-loss`: **PASS**
- `mailbox.concurrent-per-sender-fifo`: **PASS**
- `mailbox.bench-all-delivered`: **PASS**
- `mailbox.backpressure-reported`: **PASS**
- `lang.equal-long-lists`: **PASS**
- `spawngate.unrelated-spawn-refused-after-storm`: **PASS**
- `spawngate.recovers`: **PASS**
- `spawngate.retry-after-hint-honest`: **PASS**
- `scope.exactly-once-50x16`: **PASS**
- `scope.runs-after-run-workflow`: **PASS**
- `scope.runs-after-supervise-batch`: **PASS**
- `scope.failed-body-visible-in-join`: **PASS**
- `scope.join-timeout-bounded`: **PASS**
- `scope.cancel-no-done-no-hang`: **PASS**
- `scope.join-without-scope-raises`: **PASS**
- `batch.collect-all-counts`: **PASS**
- `batch.all-ok-status`: **PASS**
- `batch.retry-n-recovers-flaky`: **PASS**
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
- `ws.restore-forward`: **PASS**
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
- `fibercatch.catch-sees-captured-param`: **PASS**
- `fibercatch.main-thread-catch-sees-param`: **PASS**
- `fibercatch.search-wave-raising-candidate-reported`: **PASS**

## benchmarks

| id | value |
|---|---|
| `mailbox.send-us` | 6.8 us/msg |
| `mailbox.recv-us` | 11.3 us/msg |
| `spawngate.recovery-ms` | 30090 ms |
| `scope.spawn+join-us-per-task` | 596.25 us/task |
| `scope.join-latency-1task-median-ms` | 1 ms |
| `batch.collect-all-40-ms` | 7 ms |
| `workflow.2-stage-run-ms` | 2.4 ms/workflow |
| `ws.rebind+snapshot+restore-ms` | 0.97 ms/cycle |
| `ws.rebind-ms@10-defines` | 0.2 ms |
| `ws.snapshot-ms@10-defines` | 0.0 ms |
| `ws.restore-ms@10-defines` | 0.2 ms |
| `ws.rebind-ms@100-defines` | 0.3 ms |
| `ws.snapshot-ms@100-defines` | 0.1 ms |
| `ws.restore-ms@100-defines` | 0.4 ms |
| `ws.rebind-ms@400-defines` | 0.7 ms |
| `ws.snapshot-ms@400-defines` | 0.0 ms |
| `ws.restore-ms@400-defines` | 2.2 ms |
| `rebindconc.calls-per-ms` | 162.162 calls/ms |
| `overlay.private-eval-cycle-us` | 4.5 us/cycle |
| `chan.mpsc-throughput` | 81.633 msgs/ms |
| `chan.ping-pong-rtt-us` | 26.5 us/round-trip |
| `par.32-cands-width-1-ms` | 2002 ms |
| `par.32-cands-width-2-ms` | 1542 ms |
| `par.32-cands-width-4-ms` | 961 ms |
| `par.32-cands-width-8-ms` | 1088 ms |
| `par.speedup-8-vs-1` | 1.84 x |
| `shared.atomic-add-ns` | 2750.0 ns/op (8 fibers) |

## observations

- `mailbox.number-payload-arrives-as`: string "42"
- `mailbox.respawn-same-name`: second spawn ok=#t id=6; drained=(queued-before queued-after)
- `mailbox.spawn-after-bp-storm`: ok=#f quota-dimension=mailbox-bp retry-after-ms=29991 error=AdmissionRejected: mailbox backpressure (bp_recent=44 >= threshold=32 override=false source=process)
- `spawngate.first-refusal`: ok=#f retry-after-ms=29998 error=AdmissionRejected: mailbox backpressure (bp_recent=44 >= threshold=32 override=false source=process)
- `spawngate.refused-attempts`: 121
- `scope.join-report-with-failed-body`: ok=#f status=partial join-fail-action-taken=0 on-join-fail-effective=report-only
- `scope.join-timeout-report`: ms=301 ok=#f status=timeout reclaimed-count=4 cleanup-pending-count=4 bodies-started-before-timeout=0/4
- `scope.after-release`: ok=#t bodies-finished=0/4
- `scope.cancel-all`: cancel=<hash[5]> join-status=ok ms=4 step-states=(aborted aborted aborted aborted aborted aborted)
- `scope.join-latency-samples-ms`: (2 1 1 1 2 1 2 1 2 1)
- `batch.report`: status=partial ok-count=34 err-count=6
- `batch.has-per-task-results`: #f
- `batch.collect-all+max-retries-2`: status=partial ok=0 err=1 attempts=1 (policy echoes max-retries=2)
- `batch.retry-n+max-retries-2`: status=ok ok=1 err=0 attempts=3
- `ws.locate`: query:calls=(15) def-use=((11) 12)
- `ws.restore-forward-second-try`: arbitrate
- `ws.restore-invalid-id-returns`: #f
- `ws.cycle-ms-per-50`: (33 48 53 60)
- `rebindconc.outcomes`: fibers=4 wait(v1)=11037 expedite(v2)=963 other=0 rebinds=60 rebind-errors=0 ms=74 raw=(2751|249|0 2752|248|0 2766|234|0 2768|232|0)
- `overlay.pending-shape`: 2
- `overlay.conflict-loser`: raised:fiber:cow-conflict: Y binding=Y winner-fiber=15697797662572082958 our-epoch=0 committed-epoch=0 our-seq=0 winner-seq=1 kind=write-write (the same binding was committed by another fiber after this overlay began)
- `overlay.report`: begins=15 commits=6 fast-forward=6 merged=0 conflicts=1 rollbacks=8 writes=23 active=0 read-conflicts=0
- `chan.try-recv-empty-returns`: ""
- `chan.try-recv-of-#f-returns`: #f
- `chan.try-recv-empty-vs-empty-string`: ambiguous: an empty channel and a queued "" both return ""
- `par.note`: box has 8 cores shared with other workers; speedup is indicative only
- `shared.plain-rmw-lost-updates`: 472 of 2400 increments survived
- `fibercatch.search-wave-results`: (3|ok 1|ok 2|reject|worker:candidate crashed)

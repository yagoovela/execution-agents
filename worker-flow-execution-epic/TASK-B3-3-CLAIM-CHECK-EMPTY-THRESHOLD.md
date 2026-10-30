# B3.3 — An empty claim-check threshold falls back to the default

**Goal:** an empty `CLAIM_CHECK_THRESHOLD_BYTES` means "use the default", not "offload everything".

**Card:** [868mgqxd9](https://app.clickup.com/t/9011479430/868mgqxd9), a subtask of B3. **Branch:**
`refactor/868m0vmy4`: back commit `ce84fd42`, worker commit `a6a608a`. It ships with B3's PRs (back #2036,
worker #128).

## What is wrong

Both repos read the threshold as `Number(process.env.CLAIM_CHECK_THRESHOLD_BYTES ?? 262144)`:

- back `src/app-api/flux/claim-check.ts`, used by `flux.service.ts`, `output-delivery.service.ts` and
  `temporal/single-node-legacy/node-execution-store.ts`;
- worker `src/modules/nodes/shared/persist-node-outcome.ts`.

The `.env.example` of both repos ships `CLAIM_CHECK_THRESHOLD_BYTES=` empty. An empty string is not
`undefined`, so `??` does not apply and `Number("")` gives `0`. Every payload then goes to S3 through the
claim-check. The env docs (`env-vars-audit` README and the `environment-variables.mdx` pages) already
state a default of 262144.

## The fix

Each repo gets `parseClaimCheckThresholdBytes(raw)`. If the value is a finite number above 0, it returns
that number; otherwise it returns 262144. `CLAIM_CHECK_THRESHOLD_BYTES` keeps its name and is read
through the function.

`0` now means the default, not "always offload". No code depends on `0`.

## Tests

- Back `claim-check.spec.ts` and worker `persist-node-outcome.spec.ts`: `""`, `"  "`, `"abc"`, `"0"` and
  `"-5"` give 262144; `"1000"` gives 1000; `undefined` gives 262144.
- **Negative control:** with `Number(raw ?? 262144)` restored, the five invalid cases fail in each repo.
- The docs needed no change, because they already describe the fixed behaviour.

## Dev verification (2026-10-13)

Cherry-picked to back `master` (`afca0b00`) and worker `develop` (`17e7afb`) and deployed.

- Dev does not ship the variable empty: in the 7 days before the deploy, 0 of 114 `node_executions` rows held a `__claimRef` at or under 262144 bytes. The defect shows only where `.env.example` is copied as is, such as a local stack.
- **Regression check:** after the deploy, the B3.1 and B3.2 dev runs stored every input and output inline; 0 rows in the window held a `__claimRef`.

## QA, local (2026-10-13)

The worker's real `offloadIfLarge` ran with `CLAIM_CHECK_THRESHOLD_BYTES=` empty against a local HTTP `store-payload` stand-in: 1 KB stayed inline and 300 KB was offloaded (one store call). With only the parsing line reverted to `Number(raw ?? 262144)`, the 1 KB payload was offloaded too and the check failed.

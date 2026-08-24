# S5 — Authorise the claim check, do not just guard it

**Goal:** a claim-check key can only be redeemed by the run it belongs to.

**Depends on:** nothing. **Severity:** high (review §3.1). Standalone — ship whenever.

## Why

`/worker/get-payload` validates a **prefix and nothing else**:

```
if (typeof body.key !== 'string' || !body.key.startsWith('node-exec/')) throw ...
const stream = await this.awsService.getFile(body.key);
```
(`worker.controller.ts:87–95`)

There is no check that the key belongs to the caller's run, tenant, or anything else. Any holder of
the internal API key can read **any** node output of **any** customer, by key.

The route is behind `InternalApiGuard` (`:45`), which is the right boundary and should stay. But it
is a **single shared secret**, and this epic puts that secret on every worker replica — the blast
radius grows with the fleet, and "we trust everything inside the perimeter" gets weaker with every
host added to the perimeter.

The fix is cheap because the key already encodes what is needed: `claimCheckKey(execId, nodeId, …)`
builds it (`node-execution-store.ts:45`).

## Scope

**In.** The caller states which `execId` and `nodeId` it is acting for; the endpoint parses the key
and refuses when they disagree. The worker already has both — they are in
`ExecuteNodeActivityProps`.

**In.** The same treatment for `/worker/store-payload`: a caller should not be able to write a
payload into another run's key.

**In.** Log refusals with enough context to tell a bug from an attempt. A refusal that is invisible
teaches nobody.

**Out.** Replacing `InternalApiGuard` or introducing per-worker credentials. That is a larger
identity change; this task closes the authorisation gap inside the existing boundary.

**Related, not in scope:** review §2.4 argues the worker should hold its own S3 credentials so
large payloads stop travelling through the API. That would remove these two endpoints entirely.
If that decision is taken, this task is superseded — so check before starting.

## Verification

- **Negative control (required).** With a valid internal key, request another run's payload and
  confirm it currently succeeds. That demonstration is the whole justification for the task. Then
  confirm it is refused, and that the legitimate path is unaffected.
- Confirm the worker's normal path still resolves its own claim refs — including the large-payload
  case, which is the only path that exercises this at all.
- Confirm a malformed or truncated key fails closed, not open.

## Done when

A key can only be redeemed for its own run, writes are equally bound, refusals are logged, and the
existing large-payload path still works.

## Files

`back/src/temporal/worker.controller.ts:70–95` ·
`back/src/temporal/single-node-legacy/node-execution-store.ts:43–45` (`claimCheckKey`) ·
`worker/src/modules/nodes/shared/{resolve-claim-ref,persist-node-success}.ts`

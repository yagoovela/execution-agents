# S6-b — Worker's network position, written down

**Purpose.** Answer the question the review (§3.2) says the moving tasks (A6, A8) currently do not
even ask: which subnet, which instance role, what the worker can reach — and whether moving the
URL-fetching code into the worker is a security improvement, a regression, or risk-neutral.

**Decision scope.** This document is the deliverable for S6-b. It is a lookup first (what the
network *is* today), a conclusion second (A, B or C), and a precondition for A6/A8 third (if the
conclusion is C, those tasks hold their fetchers until the compensating controls exist).

## Current state — needs to be filled in by Infra

The following fields are placeholders. Each must be filled by Infra before A6/A8 ship their first
relocated fetcher. The information is a straight lookup against AWS/Terraform; it is not an opinion.

### API (back/)

- **Subnet:** `TBD` (which subnet does the API ECS task run in? public, private-with-NAT, private
  without egress?)
- **Instance / task role ARN:** `TBD`
- **Egress — what the API can reach from this subnet:**
  - `TBD` (e.g. public internet via NAT, VPC endpoints to S3/SSM, internal RDS, …)
- **Can the API reach the EC2/ECS metadata endpoint (`169.254.169.254`)?** `TBD`

### Worker (worker/)

- **Subnet:** `TBD`
- **Instance / task role ARN:** `TBD`
- **Egress — what the worker can reach from this subnet:**
  - `TBD`
- **Can the worker reach the EC2/ECS metadata endpoint (`169.254.169.254`)?** `TBD`
- **Secrets held in-memory by the worker process:**
  - Database password (TYPEORM_PASSWORD).
  - Integrations encryption key (INTEGRATIONS_ENCRYPTION_KEY).
  - Provider API keys (OPENAI, ANTHROPIC, SCRAPINGBEE, OXYLAB, SEC_API, CENSUS_API_KEY, …).

## Conclusion — pick one

### A — The worker reaches **less** than the API (aim for this)

Fill in: *"The worker ECS task runs in subnet X with instance role Y. It can reach {list}, which is
a strict subset of what the API in subnet A with role B can reach. Specifically it cannot reach {…}.
Moving fetchers from the API into the worker therefore reduces the blast radius of a compromised
fetcher."*

If this is the conclusion: **relocation is a stated security improvement**. A6/A8 ship their
fetchers. The egress policy from S6-a is defense in depth, not the only line.

### B — The worker reaches **the same** as the API (risk-neutral)

Fill in: *"The worker ECS task runs in the same subnet and with an equivalent role as the API.
Egress reachability is identical. Moving fetchers does not change the exposure."*

If this is the conclusion: **relocation is risk-neutral**. A6/A8 ship their fetchers. The egress
policy from S6-a is the only control, and the implementer accepts that one layer has to be right.

### C — The worker reaches **more** than the API (needs compensating controls)

Fill in: *"The worker ECS task runs in subnet X with role Y. The worker can additionally reach {…}
that the API cannot. Moving fetchers from the API into the worker without further changes would
widen the blast radius of a compromised fetcher."*

If this is the conclusion: **A6 and A8 do not ship their fetchers until the compensating controls
are in place.** The compensating controls, in order of effort:

1. Tighten the worker's security group egress rules to the actual list the activities need.
2. Scope the instance/task role to the minimum resources the worker owns (no cross-service S3,
   no cross-tenant SSM).
3. Place the worker behind a dedicated egress proxy that applies the deny-list from S6-a at the
   network layer (option C of S6-a).

The implementer updates this document with the chosen control, the ticket where it lives, and the
date it ships; A6 and A8 reference this document in their own "Depends on" sections.

## Who signs this off

- **Infra** owns the subnet, security group and role definitions. Infra fills in the "Current state"
  section above.
- **Security** signs off on the chosen conclusion (A / B / C) and, if C, on the specific
  compensating controls.
- **Engineering** (the implementer of A6/A8) reads this document before shipping; if the conclusion
  is C and the compensating controls are not in place, the fetcher does not ship.

## Status

`[ ] Infra filled in current state`
`[ ] Conclusion selected (A / B / C)`
`[ ] If C: compensating control chosen and ticketed`
`[ ] Security signed off`
`[ ] A6/A8 reference this document`

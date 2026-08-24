# Worker flow-execution epic

A copy of `.specs/features/worker-flow-execution-epic/` from the
**`enhancedai-com/Workflow`** repository, placed here so it sits next to the
`execution-agents` step documentation it was built on.

That step documentation — `index.html` and the 34 pages under `passos/` — was one of the primary
inputs to this analysis. Its per-step "Observações para migração" notes were extracted and compared
against the epic; five real gaps came out of that comparison, including the discovery that
`varInputNode` performs link extraction and OCR during a run and is not inert.

## Read order

| File | What it is |
|---|---|
| [`epic-handbook.html`](./epic-handbook.html) | **Open this first.** The plan and all 32 tasks as one browsable page, each task with a one-line summary so you can find yours without reading the plan end to end |
| [`PLAN.md`](./PLAN.md) | The umbrella. Goals, conventions, the definition of done, the task index, risks and open decisions. **Start here.** |
| [`DELIVERY-PLAN.md`](./DELIVERY-PLAN.md) | The 32 tasks arranged into seven waves, each with an exit gate, a rollback and an observable outcome |
| [`ARCHITECTURE-REVIEW.md`](./ARCHITECTURE-REVIEW.md) | An adversarial review of the plan — what breaks, what costs money, what can be abused at scale, and where the analysis itself fails |
| [`MARKET-GAPS.md`](./MARKET-GAPS.md) | What comparable products offer that we do not, and which of those the epic unblocks |
| `TASK-*.md` | One file per task, sized to one ticket and one PR |
| `*.html` | Standalone pages: the handbook, the scale review, the delivery waves, the market gaps |

## Two things to know before reading

**The upstream analysis is not copied here.** `PLAN.md` and the task specs cite
`.specs/features/worker-node-migration-analysis/README.md` by section number (§1–§11). That
document lives in `enhancedai-com/Workflow` and is the evidence base for everything here — the
48-node census, the dispatch-gate findings, and the reconciliation with these step pages.

**This is a snapshot.** The living version is in `enhancedai-com/Workflow`. If the two disagree,
that one is right.

## Note on the HTML pages

The three `.html` files are self-contained pages with no dependencies. Because this repository
deploys as a static site, merging them makes them publicly reachable. `scale-readiness-review.html`
in particular describes **specific unpatched security defects with file and line references** —
see the PR description.

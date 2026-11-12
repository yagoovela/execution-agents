# Changelog

Every publish to this repository, newest first. `_assets/changelog.py add` writes each
entry from git; do not edit the generated lines by hand. The page `mudancas.html`
renders this file, and each task page shows the latest entry that changed it.

The log starts with PR #40. Earlier history is in `git log`.

## 2026-11-12 · [#50](https://github.com/yagoovela/execution-agents/pull/50) · Publish the 2026-11-12 release of A13, S4b and S8b
- Title (PT): Publicar o release de 12/11/2026 da A13, S4b e S8b
- Tasks: S8B, S4B, A13
- Pages: `progresso-refatoracao.html`, `status-tarefas.html`, `timeline/index.html`, `timeline/task-A13.html`, `timeline/task-S4B.html`, `timeline/task-S8B.html`
- No page change: E4: the spec adds the S8b rollout note; the page summary still holds
- Commits:
  - 1da5616 docs(868mn64j4): publish the 2026-11-12 release of A13, S4b and S8b

## 2026-11-11 · [#49](https://github.com/yagoovela/execution-agents/pull/49) · Publish Wave 5 progress, B7b, E4b, A9b and E5b
- Title (PT): Publicar o andamento da Wave 5, a B7b, a E4b, a A9b e a E5b
- Tasks: S2, E5, E3B, S8B, S10, S11, S4B, A13, B6, B7B, E4, E4B, A9B, E5B, A112
- Pages: `progresso-refatoracao.html`, `status-tarefas.html`, `timeline/index.html`, `timeline/task-A13.html`, `timeline/task-A9B.html`, `timeline/task-B6.html`, `timeline/task-B7B.html`, `timeline/task-E3B.html`, `timeline/task-E4.html`, `timeline/task-E4B.html`, `timeline/task-E5.html`, `timeline/task-E5B.html`, `timeline/task-S10.html`, `timeline/task-S11.html`, `timeline/task-S2.html`, `timeline/task-S4B.html`, `timeline/task-S8B.html`
- No page change: B6: the spec adds a fail-fast item from A13; the page summary still holds
- No page change: E4: the spec adds the S8b rollout note; the page summary still holds
- Commits:
  - ce23a64 docs(868mrv6cg): publish Wave 5 progress, B7b and E4b
  - e6c15bd docs(868mrv6cg): add the changelog entry for the Wave 5 publish
  - c4fa05d docs(868mn64j4): move the A13 note sentence into its English half

## 2026-11-05 · [#48](https://github.com/yagoovela/execution-agents/pull/48) · Publish A11.2 and read dotted subtask codes
- Title (PT): Publica a A11.2 e lê códigos de subtarefa com ponto
- Tasks: A11, A112
- Pages: `timeline/task-A11.html`
- Commits:
  - acf4fe4 docs(868mqc7w6): publish the A11.2 spec and read dotted subtask codes

## 2026-11-04 · [#47](https://github.com/yagoovela/execution-agents/pull/47) · Publish the Wave 5 back-replica tasks, S9 and the 2026-11-03 release
- Title (PT): Publicar as tasks de réplica do back da Wave 5, a S9 e o release de 03/11/2026
- Tasks: S4, S2, S8, E3, B3B, E1, E2, S6B, E3B, S8B, S10, S11, S4B, A11, S9, A13, B7, E4
- Pages: `progresso-refatoracao.html`, `status-tarefas.html`, `timeline/index.html`, `timeline/task-A11.html`, `timeline/task-A13.html`, `timeline/task-B7.html`, `timeline/task-E1.html`, `timeline/task-E3.html`, `timeline/task-E3B.html`, `timeline/task-E4.html`, `timeline/task-S10.html`, `timeline/task-S11.html`, `timeline/task-S2.html`, `timeline/task-S4.html`, `timeline/task-S4B.html`, `timeline/task-S6B.html`, `timeline/task-S8.html`, `timeline/task-S8B.html`, `timeline/task-S9.html`
- No page change: B3B: the 2026-10-29 production measurement and the self-loop decision are added to the mirrored spec; the page summary still holds
- No page change: E2: the 2026-10-29 production MCP cancel check is added to the mirrored spec; the page summary still holds
- No page change: S5: only S4's lede changed in the shared module w0_rest.py
- Commits:
  - 3b27b91 docs(868mrv6cg): publish the Wave 5 back-replica tasks, S9 and the 2026-11-03 release

## 2026-10-30 · [#46](https://github.com/yagoovela/execution-agents/pull/46) · Publish the held-back specs with private values removed, and set E5 to planned
- Title (PT): Publicar as specs retidas sem os valores privados, e marcar a E5 como planejada
- Tasks: S4, S2, A8, E5, A11, A5B, B3B1
- Pages: `progresso-refatoracao.html`, `status-tarefas.html`, `timeline/index.html`, `timeline/task-A11.html`, `timeline/task-A8.html`, `timeline/task-E5.html`, `timeline/task-S2.html`
- No page change: S4: the update adds the implementation, release and measurement record; the page already shows the settled ceilings
- No page change: A5B: the spec is newly mirrored; the A5 page already covers A5B
- No page change: B3B1: only a customer name changed in the spec, and the B3B page never showed it
- Commits:
  - edce176 docs(specs): publish the held-back specs with private values removed, and set E5 to planned

## 2026-10-29 · [#45](https://github.com/yagoovela/execution-agents/pull/45) · Sync the epic with the Workflow spec, and check task owners
- Title (PT): Sincroniza o épico com a spec do Workflow e confere os responsáveis das tasks
- Tasks: S7, S5, C3, S2, S3, S8, E3, A1, A1B, A1C, D2, A2, A3, A4, A5, A6, S6, A8, A9, A10, D1, B1, B2, B3, B3B, B4, E1, E2, E5, A7, B5, B6, C1, B3B1
- Pages: `status-tarefas.html`, `timeline/task-A5.html`, `timeline/task-A6.html`, `timeline/task-A9.html`, `timeline/task-B1.html`, `timeline/task-B2.html`, `timeline/task-B5.html`, `timeline/task-B6.html`, `timeline/task-C1.html`, `timeline/task-D1.html`, `timeline/task-D2.html`, `timeline/task-E2.html`, `timeline/task-E5.html`, `timeline/task-S2.html`, `timeline/task-S5.html`, `timeline/task-S8.html`, `worker-flow-execution-epic/delivery-waves.html`, `worker-flow-execution-epic/epic-handbook.html`, `worker-flow-execution-epic/market-gaps.html`, `worker-flow-execution-epic/scale-readiness-review.html`
- No page change: A1, A10, A1B, A1C, A2, A3, A4, A7, A8, B3, B3B, B3B1, B4, C3, E1, E3, E4, S3, S4, S6: the merged module rebuilds to the published page, so the page does not change
- No page change: S7: the published page keeps its hand-edited wording, which rebuild.py protects
- Commits:
  - 9a5319c docs(specs): sync the epic with the Workflow spec, and check task owners

## 2026-10-29 · [#43](https://github.com/yagoovela/execution-agents/pull/43) · Map task impact, check every restated fact, and keep a changelog
- Title (PT): Mapeia o impacto de cada task, confere todo fato repetido e mantém um changelog
- Tasks: S3, S8, A1B, D2, A2, A3, A4, A5, A6, A8, A9, A10, B3, E5, A7, A14, A6B, E4
- Pages: `status-tarefas.html`, `timeline/index.html`, `timeline/task-A14.html`, `timeline/task-A2.html`, `timeline/task-A3.html`, `timeline/task-A4.html`, `timeline/task-A5.html`, `timeline/task-A6.html`, `timeline/task-A6B.html`, `timeline/task-A7.html`, `timeline/task-A8.html`, `timeline/task-A9.html`, `timeline/task-B3.html`, `timeline/task-D2.html`, `timeline/task-E5.html`, `timeline/task-S3.html`
- No page change: A10, A1B, E4, S8: the spec mirror caught up with the Workflow spec; the pages already show it
- Commits:
  - 1227859 docs(tooling): map task impact, check every restated fact, keep a changelog

## 2026-10-29 · [#42](https://github.com/yagoovela/execution-agents/pull/42) · Show E2 shipped and A11, B7 and S6b in progress
- Title (PT): Mostra a E2 entregue e a A11, a B7 e a S6b em andamento
- Tasks: E2, S6B, A11, B7, E4
- Pages: `progresso-refatoracao.html`, `status-tarefas.html`, `timeline/index.html`, `timeline/task-A11.html`, `timeline/task-B7.html`, `timeline/task-E2.html`, `timeline/task-E4.html`, `timeline/task-S6B.html`
- Commits:
  - fbe29b9 docs(specs): show E2 shipped and A11, B7 and S6b in progress

## 2026-10-29 · [#41](https://github.com/yagoovela/execution-agents/pull/41) · Bring the A11 and C2 status lines up to date
- Title (PT): Atualiza as linhas de status da A11 e da C2
- Tasks: A11, C2
- Pages: `timeline/task-A11.html`, `timeline/task-C2.html`
- Commits:
  - b1b2620 docs(868mn64he): bring the A11 and C2 status lines up to date

## 2026-10-29 · [#40](https://github.com/yagoovela/execution-agents/pull/40) · Republish A11 with the build and review decisions
- Title (PT): Republica a A11 com as decisões de build e de revisão
- Tasks: A11, A13, A14, C2
- Pages: `timeline/task-A11.html`, `timeline/task-A13.html`, `timeline/task-A14.html`, `timeline/task-C2.html`
- Commits:
  - b2654bf docs(868mn64he): republish A11 with the build and review decisions

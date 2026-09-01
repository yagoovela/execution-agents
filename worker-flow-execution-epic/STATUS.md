# Status — the single source

**This table is the only place a task's state is written down.** The task pages and the timeline
read it at build time; nothing else records progress. Edit here, re-run the build, and every page
agrees. If you find status stated anywhere else, that copy is a bug — delete it and point at this
file. See `MAINTENANCE.md` for when to touch it.

`state` is one of:

| state | meaning |
|---|---|
| `planned` | Written down, not started. The default. |
| `blocked` | Cannot start — the `note` says what is in the way (a decision, another task, a measurement). |
| `doing` | Someone is working on it right now. |
| `review` | Code is up; the negative controls have been run and reported. |
| `shipped` | In production, with the definition of done satisfied. |
| `dropped` | Deliberately not doing it. The `note` says why, and that is a decision worth keeping. |

`ref` is the PR, branch or ClickUp id. Leave it `—` until there is one.

`note` is bilingual: `English // Português`, split on ` // ` at build time. A note without the
separator fails the build and names the task, because the pages are bilingual and the note is
rendered into them verbatim — an untranslated note would show English in both languages. Leave the
cell empty when there is nothing to say.

| task | state | ref | note |
|---|---|---|---|
| S7 | planned | — | |
| S1 | planned | — | |
| S4 | planned | — | Blocked on the D15 measurement before the ceilings can be numbers. Y and the credit balance are separate ceilings stopping the same run for different reasons, and D20 makes both behave the same way. // Bloqueada pela medição da D15 até os tetos poderem virar números. O Y e o saldo de crédito são tetos distintos que param o mesmo run por motivos diferentes, e a D20 faz os dois se comportarem igual. |
| S5 | planned | — | Check whether the worker gets its own S3 credentials first — that would supersede it. // Verifique antes se o worker vai receber credenciais S3 próprias — isso dispensaria esta task. |
| C3 | planned | — | |
| S2 | planned | — | |
| S3 | planned | — | D19 makes fluxCred exhaustion stop the run at the node boundary. D20 puts the credit check in the pre-flight gate rather than on each node. // A D19 faz o fim do fluxCred parar o run no limite do nó. A D20 coloca a checagem de crédito no gate pré-execução, não em cada nó. |
| S8 | planned | — | |
| E3 | planned | — | |
| A1 | planned | — | |
| D2 | planned | — | |
| A2 | planned | — | |
| A3 | planned | — | |
| A4 | planned | — | |
| A5 | planned | — | |
| A6 | planned | — | Needs the D3 product sign-off before it becomes a behaviour change. // Precisa do aval de produto da D3 antes de virar mudança de comportamento. |
| S6 | planned | — | |
| A8 | planned | — | |
| A9 | planned | — | |
| D1 | planned | — | |
| B1 | planned | — | |
| B2 | planned | — | Blocked on decision D1. // Bloqueada pela decisão D1. |
| B3 | planned | — | Blocked on C2's measurement, which has to be pulled forward. // Bloqueada pela medição do C2, que precisa ser antecipada. |
| B4 | planned | — | |
| E1 | planned | — | |
| E2 | planned | — | |
| B5 | planned | — | Preconditions: S1, S2, S3, E3. When the credit balance runs out with N generations already in flight, D20 lets all N finish — the overshoot is N nodes, not one, so size the headroom. D21 applies only if the queue actually chooses what runs next — confirm that first. // Pré-requisitos: S1, S2, S3, E3. Quando o saldo de crédito acaba com N gerações já em voo, a D20 deixa as N terminarem — o estouro é de N nós, não de um, então dimensione a folga. A D21 só vale se a fila realmente escolher o próximo item — confirme isso antes. |
| A7 | planned | — | |
| B6 | planned | — | Inherits D13 and D14 from S1 — do not re-open them. D23 makes container nodes cancellable rather than allowed to finish. // Herda a D13 e a D14 do S1 — não reabra as duas. A D23 torna os nós contêiner canceláveis em vez de deixá-los terminar. |
| B7 | planned | — | |
| C1 | planned | — | |
| C2 | planned | — | Owns the measurement that settles decision D2. // É dona da medição que resolve a decisão D2. |

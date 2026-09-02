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
| S4 | planned | — | Needs the D15 measurement before the ceilings can be numbers. Y and the credit balance are separate ceilings stopping the same run for different reasons, and D20 makes both behave the same way. // Precisa da medição da D15 até os tetos poderem virar números. O Y e o saldo de crédito são tetos distintos que param o mesmo run por motivos diferentes, e a D20 faz os dois se comportarem igual. |
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
| A5 | planned | — | imageReaderNode left the task — deprecated (D24); an imageGenerator module is in progress on the dev line. // O imageReaderNode saiu da task — depreciado (D24); um módulo de imageGenerator está em andamento na linha de dev. |
| A6 | planned | — | D3 answered on 2026-09-02: documentSummarizer and commandMusicNode discontinued; webAmazon and secApiNode broken today (fix or drop, per type); fileSave under review. Six types get execution. // D3 respondida em 2026-09-02: documentSummarizer e commandMusicNode descontinuados; webAmazon e secApiNode quebrados hoje (corrigir ou descartar, por tipo); fileSave em revisão. Seis tipos ganham execução. |
| S6 | planned | — | The width of the first cut is the implementer's call (D25). // A largura do primeiro corte é decisão de quem implementar (D25). |
| A8 | planned | — | |
| A9 | planned | — | |
| D1 | planned | — | |
| B1 | planned | — | |
| B2 | planned | — | Starts by answering decision D1 — the decision is inside the task, not ahead of it. // Começa respondendo a decisão D1 — a decisão está dentro da task, não antes dela. |
| B3 | planned | — | Needs D2's measurement, taken by A1 in Wave 2; B3 answers D2 with it. // Precisa da medição da D2, feita pela A1 na onda 2; a B3 responde a D2 com ela. |
| B4 | planned | — | |
| E1 | planned | — | |
| E2 | planned | — | |
| B5 | planned | — | Preconditions: S1, S2, S3, E3. When the credit balance runs out with N generations already in flight, D20 lets all N finish — the overshoot is N nodes, not one, so size the headroom. D21 applies only if the queue actually chooses what runs next — confirm that first. // Pré-requisitos: S1, S2, S3, E3. Quando o saldo de crédito acaba com N gerações já em voo, a D20 deixa as N terminarem — o estouro é de N nós, não de um, então dimensione a folga. A D21 só vale se a fila realmente escolher o próximo item — confirme isso antes. |
| A7 | planned | — | |
| B6 | planned | — | Inherits D13 and D14 from S1 — do not re-open them. D23 makes container nodes cancellable rather than allowed to finish. Ships after B5 (D17). // Herda a D13 e a D14 do S1 — não reabra as duas. A D23 torna os nós contêiner canceláveis em vez de deixá-los terminar. Sobe depois da B5 (D17). |
| B7 | planned | — | The batch screen is out of this epic (2026-09-02). // A tela de lote está fora deste épico (2026-09-02). |
| C1 | planned | — | |
| C2 | planned | — | Executes the D2 answer; the measurement is A1's (Wave 2) and the answer is B3's (Wave 4). // Executa a resposta da D2; a medição é da A1 (onda 2) e a resposta é da B3 (onda 4). |

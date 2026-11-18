# -*- coding: utf-8 -*-
TITLE = ('An async API run survives a back deploy, or ends with one outcome',
         'Um run de API assíncrono sobrevive a um deploy do back, ou termina com um só resultado')

GOAL = ('A back deploy no longer kills async <code>apiV2</code> runs in flight. When a run does lose its process, it ends with <b>exactly one outcome</b>: one status, one delivery and a recorded cost that matches what was charged. '
        'On the <code>B4</code> path the run continues in the worker, and any live back finishes it when its handler is gone.',
        'Um deploy do back não mata mais runs <code>apiV2</code> assíncronos em andamento. Quando um run perde o processo, ele termina com <b>exatamente um resultado</b>: um status, uma entrega e um custo registrado igual ao que foi cobrado. '
        'No caminho da <code>B4</code> o run continua no worker, e qualquer back vivo o finaliza quando o handler some.')

GLANCE = [
 ('crit', ('Measured cause','Causa medida'), ('15 of 15 stalled runs died in a back deploy','15 de 15 runs travados morreram num deploy do back'),
  ('The old task kept taking Bull jobs while it drained, and <code>node</code> never received SIGTERM. The double outcome the task was first written for occurred 0 times.',
   'A task antiga continuava pegando jobs do Bull enquanto drenava, e o <code>node</code> nunca recebia o SIGTERM. O resultado duplo para o qual a task foi escrita ocorreu 0 vezes.')),
 ('dep', ('Depends on','Depende de'), ('A9 · A13 · B4 · back #2086','A9 · A13 · B4 · back #2086'),
  ('<code>A9</code> made delivery a workflow, <code>A13</code> added the worker-side batch finish, <code>B4</code> is the <code>processFlow</code> path, and back PR #2086 stopped Bull from redelivering a stalled job.',
   'A <code>A9</code> fez da entrega um workflow, a <code>A13</code> trouxe o fim de batch no worker, a <code>B4</code> é o caminho do <code>processFlow</code>, e o PR #2086 do back impediu o Bull de reentregar um job travado.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('After <code>A13</code>. Blocks turning the <code>B4</code> flag on in production.',
   'Depois da <code>A13</code>. Bloqueia ligar a flag da <code>B4</code> em produção.')),
 ('ship', ('Shape','Formato'), ('Back, worker and the back task definition','Back, worker e a task definition do back'),
  ('Added on 2026-11-11 from A13, re-scoped on 2026-11-12, reviewed on 2026-11-13, in production since 2026-11-18.',
   'Adicionada em 11/11/2026 a partir da A13, escopo revisto em 12/11/2026, revisada em 13/11/2026, em produção desde 18/11/2026.')),
]

LEDE = (
 '<p>Fifteen async runs were reported stalled from 2026-11-04 to 2026-11-12, and every one fell on a back production deploy. Each run had started on the old ECS task, '
 'which kept taking Bull jobs while it drained. That task&#x27;s PID 1 was a shell that did not forward SIGTERM, so <strong>ECS killed <code>node</code> with the run in flight</strong>, '
 'and the new task then reported the stall. In 4 of the 15 runs, a node that the worker was still running finished and was charged after the stall, about 7,000 credits in total, '
 'while the run ended <code>error</code> with no outputs.</p>'
 '<p>The task was first written for a frozen process that resumes after its stall report and delivers a second time. That case occurred 0 times in 15, but stays reachable through a lost Bull lock. '
 'So on 2026-11-12 the task was re-scoped: stop deploys from killing runs first, then make every end of a run go through one claim. '
 'On the <code>B4</code> path a deploy charges the whole run and still reports <code>error</code>, which is why this task blocks the <code>B4</code> flag.</p>',
 '<p>Quinze runs assíncronos foram marcados como travados de 04/11/2026 a 12/11/2026, e todos caíram num deploy do back em produção. Cada run tinha começado na task antiga do ECS, '
 'que continuava pegando jobs do Bull enquanto drenava. O PID 1 dessa task era um shell que não repassava o SIGTERM, então <strong>o ECS matava o <code>node</code> com o run em andamento</strong>, '
 'e a task nova então reportava o travamento. Em 4 dos 15 runs, um node que o worker ainda rodava terminou e foi cobrado depois do travamento, cerca de 7.000 créditos no total, '
 'enquanto o run terminava em <code>error</code> sem saídas.</p>'
 '<p>A task foi escrita primeiro para um processo congelado que retoma depois do aviso de travamento e entrega uma segunda vez. Esse caso ocorreu 0 vezes em 15, mas continua alcançável por um lock do Bull perdido. '
 'Por isso, em 12/11/2026 o escopo foi revisto: primeiro impedir que deploys matem runs, depois fazer todo fim de run passar por um único claim. '
 'No caminho da <code>B4</code> um deploy cobra o run inteiro e ainda reporta <code>error</code>, e é por isso que esta task bloqueia a flag da <code>B4</code>.</p>')

TABLE = dict(
 head=[('When a back deploy reaches a run in flight','Quando um deploy do back alcança um run em andamento'),('Before A9b','Antes da A9b'),('After A9b','Depois da A9b')],
 rows=[
  [('SIGTERM to <code>node</code>','SIGTERM para o <code>node</code>'),
   {'t':('Never arrives: a shell is PID 1','Nunca chega: um shell é o PID 1'),'pill':'weak'},
   {'t':('Arrives; the app closes and exits 0','Chega; a aplicação fecha e sai com 0'),'pill':'ok'}],
  [('The old task while it drains','A task antiga enquanto drena'),
   {'t':('Keeps taking Bull jobs for up to 300 s','Continua pegando jobs do Bull por até 300 s'),'pill':'weak'},
   {'t':('Deregistration delay of 180 s; pauses its queues at SIGTERM','Deregistration delay de 180 s; pausa as filas no SIGTERM'),'pill':'ok'}],
  [('A legacy run in flight','Um run legado em andamento'),
   {'t':('Killed; ends <code>error</code> with a recorded cost of 0','Morto; termina em <code>error</code> com custo registrado 0'),'pill':'weak'},
   {'t':('Up to 100 s to finish; else one <code>error</code>, one callback and its real cost','Até 100 s para terminar; senão um <code>error</code>, um callback e o custo real'),'pill':'ok'}],
  [('A <code>B4</code> run whose handler died','Um run da <code>B4</code> cujo handler morreu'),
   {'t':('Every node charged, nothing writes the end; reported <code>error</code>','Todo node cobrado, nada grava o fim; reportado como <code>error</code>'),'pill':'weak'},
   {'t':('Any live back finishes it: one status, one delivery','Qualquer back vivo o finaliza: um status, uma entrega'),'pill':'ok'}],
  [('Stall report and live end both arrive','Aviso de travamento e fim vivo chegam os dois'),
   {'t':('Two deliveries; the MCP status keeps the last writer','Duas entregas; o status do MCP fica com o último escritor'),'pill':'weak'},
   {'t':('The first claim wins; the loser delivers nothing of its own','O primeiro claim vence; o perdedor não entrega nada próprio'),'pill':'ok'}],
  [('A run that no one closes','Um run que ninguém fecha'),
   {'t':('Stays <code>in_progress</code> forever','Fica <code>in_progress</code> para sempre'),'pill':'weak'},
   {'t':('A cron closes it past the run ceiling plus 30 min, behind a flag that is off in production','Um cron o fecha depois do teto do run mais 30 min, atrás de uma flag desligada em produção'),'pill':'ok'}],
 ])

PROSE = ('<p>Decided with the user on 2026-11-12 and 2026-11-13, and reviewed for implementation readiness in five rounds on 2026-11-13. '
         'These are the task&#x27;s own decisions, numbered <code>A9b-D1</code> to <code>A9b-D18</code>, not the epic&#x27;s.</p>',
         '<p>Decididas com o usuário em 12/11/2026 e 13/11/2026, e revisadas quanto à prontidão para implementar em cinco rodadas em 13/11/2026. '
         'São decisões da própria task, numeradas de <code>A9b-D1</code> a <code>A9b-D18</code>, não do épico.</p>')

DEC_TABLE = {'k':'table',
 'head':[('Decision','Decisão'),('Question','Pergunta'),('Decided','Decidido')],
 'rows':[
  [{'t':('A9b-D1','A9b-D1'),'mono':True},('Scope','Escopo'),
   ('Deploy-killed runs first, plus the one-outcome guard: the deploy is the measured cause (15 of 15), and the double outcome is cheap to close',
    'Primeiro os runs mortos por deploy, mais a guarda de um só resultado: o deploy é a causa medida (15 de 15), e o resultado duplo é barato de fechar')],
  [{'t':('A9b-D2','A9b-D2'),'mono':True},('How a deploy stops killing runs','Como um deploy para de matar runs'),
   ('Graceful shutdown now; the <code>B4</code> path, finished through any back, is the durable fix, because runs last up to 6 h',
    'Desligamento gracioso agora; o caminho da <code>B4</code>, finalizado por qualquer back, é a correção durável, porque runs duram até 6 h')],
  [{'t':('A9b-D3','A9b-D3'),'mono':True},('Which outcome wins','Qual resultado vence'),
   ('The first claim wins. A loser writes no status and delivers nothing of its own: it only starts the winner&#x27;s stored plan',
    'O primeiro claim vence. Um perdedor não grava status nem entrega nada próprio: só inicia o plano gravado do vencedor')],
  [{'t':('A9b-D4','A9b-D4'),'mono':True},('Cost of a legacy run killed by a deploy','Custo de um run legado morto por deploy'),
   ('Interrupt its steps in flight and record the real cost, with no refund; a node in progress still charges partial tokens (E2 D22)',
    'Interromper os passos em andamento e registrar o custo real, sem reembolso; um node em andamento ainda cobra tokens parciais (E2 D22)')],
  [{'t':('A9b-D5','A9b-D5'),'mono':True},('Resume a killed legacy run','Retomar um run legado morto'),
   ('No: the legacy loop keeps its state in memory, and a resume costs 3 to 5 days for a path Wave 6 deletes',
    'Não: o laço legado guarda o estado em memória, e retomar custa 3 a 5 dias para um caminho que a Onda 6 apaga')],
  [{'t':('A9b-D6','A9b-D6'),'mono':True},('Who writes the end of a <code>B4</code> run','Quem grava o fim de um run da <code>B4</code>'),
   ('The live handler, as before; at its end the run workflow calls a finish activity, and back writes a reduced end only when no live handler holds the Bull job',
    'O handler vivo, como antes; no fim o workflow do run chama uma activity de fim, e o back grava um fim reduzido só quando nenhum handler vivo segura o job do Bull')],
  [{'t':('A9b-D7','A9b-D7'),'mono':True},('How SIGTERM reaches <code>node</code>','Como o SIGTERM chega ao <code>node</code>'),
   ('<code>exec node</code> at the end of <code>dev.sh</code>, the database seed under <code>setsid</code>, and <code>initProcessEnabled</code> in the task definition',
    '<code>exec node</code> no fim do <code>dev.sh</code>, o seed do banco sob <code>setsid</code>, e <code>initProcessEnabled</code> na task definition')],
  [{'t':('A9b-D8','A9b-D8'),'mono':True},('Deregistration delay','Deregistration delay'),
   ('180 s, down from 300 s; measured over 15 days, 60 s would cut long requests every day',
    '180 s, antes 300 s; medido em 15 dias, 60 s cortaria requisições longas todo dia')],
  [{'t':('A9b-D9','A9b-D9'),'mono':True},('Runs left unfinished or running too long','Runs deixados sem fim ou rodando demais'),
   ('A cron behind <code>unfinished_run_reaper</code> closes and stops any run past the run ceiling plus 30 min, starts a stored plan no one started, and skips a run while Temporal cannot be reached; the <code>api-v2</code> Bull timeout becomes the ceiling plus 1 h',
    'Um cron atrás da <code>unfinished_run_reaper</code> fecha e para qualquer run além do teto do run mais 30 min, inicia um plano gravado que ninguém iniciou, e pula um run enquanto o Temporal não responde; o timeout do Bull do <code>api-v2</code> vira o teto mais 1 h')],
  [{'t':('A9b-D10','A9b-D10'),'mono':True},('A retried run end','Um fim de run repetido'),
   ('Keep A9&#x27;s guarantees, and give the run&#x27;s end delivery the run id as its invocation id',
    'Manter as garantias da A9, e dar à entrega de fim do run o id do run como id de invocação')],
  [{'t':('A9b-D11','A9b-D11'),'mono':True},('Child-run charges in a legacy stall','Cobranças de runs filhos num travamento legado'),
   ('Library and flow-caller children keep their own run id and add it to a Redis set of their parent, which the recompute reads',
    'Filhos de library e de flow-caller mantêm o próprio id de run e o somam a um set Redis do pai, que o recálculo lê')],
  [{'t':('A9b-D12','A9b-D12'),'mono':True},('The claim&#x27;s delivery','A entrega do claim'),
   ('The claim stores the run&#x27;s delivery plan (<code>end_delivery</code>), cleared once its delivery has started, so any later writer can start it',
    'O claim grava o plano de entrega do run (<code>end_delivery</code>), limpo quando a entrega começa, então qualquer escritor seguinte pode iniciá-la')],
  [{'t':('A9b-D13','A9b-D13'),'mono':True},('Inline child runs on the <code>B4</code> path','Runs filhos inline no caminho da <code>B4</code>'),
   ('Library and flow-caller children run on the legacy loop until B6',
    'Filhos de library e de flow-caller rodam no laço legado até a B6')],
  [{'t':('A9b-D14','A9b-D14'),'mono':True},('When to recompute a legacy stall&#x27;s cost','Quando recalcular o custo de um travamento legado'),
   ('Two passes, at 5 min and 35 min, scheduled before the claim',
    'Duas passadas, aos 5 min e aos 35 min, agendadas antes do claim')],
  [{'t':('A9b-D15','A9b-D15'),'mono':True},('Who writes a cancel request','Quem grava um pedido de cancelamento'),
   ('No one at a stall; the cron writes the chain cancel for a live legacy run past its limit',
    'Ninguém num travamento; o cron grava o cancelamento da cadeia para um run legado vivo além do limite')],
  [{'t':('A9b-D16','A9b-D16'),'mono':True},('A plain <code>Error</code> in <code>processFlow</code> code','Um <code>Error</code> comum no código do <code>processFlow</code>'),
   ('Every <code>processFlow</code> run fails with a non-retryable <code>ApplicationFailure</code>, batch rows included, instead of retrying its task forever',
    'Todo run do <code>processFlow</code> falha com um <code>ApplicationFailure</code> não repetível, linhas de batch incluídas, em vez de repetir a task para sempre')],
  [{'t':('A9b-D17','A9b-D17'),'mono':True},('Unfinished rows older than 7 days','Linhas sem fim com mais de 7 dias'),
   ('Closed with status, error and cost only, with no callback and no email; at most 100 rows per select per tick, oldest first',
    'Fechadas só com status, erro e custo, sem callback e sem email; no máximo 100 linhas por select por ciclo, as mais antigas primeiro')],
  [{'t':('A9b-D18','A9b-D18'),'mono':True},('The error text the cron writes','O texto de erro que o cron grava'),
   ('Fixed messages in the tone of <code>STALLED_RUN_MESSAGE</code>; a <code>B4</code> run past its limit reads the same as a legacy run',
    'Mensagens fixas no tom do <code>STALLED_RUN_MESSAGE</code>; um run da <code>B4</code> além do limite lê igual a um run legado')],
 ]}

DECISIONS = [DEC_TABLE]

PARTS = [
{'n':'1','title':('Graceful shutdown','Desligamento gracioso'),
 'loc':'back/dev.sh · back/src/main.ts · api-task-definition-prod',
 'purpose':('SIGTERM reaches <code>node</code>, the process takes no new job, and a legacy run gets up to 100 s to finish.',
            'O SIGTERM chega ao <code>node</code>, o processo não pega job novo, e um run legado tem até 100 s para terminar.'),
 'body':('<p><code>dev.sh</code> ends with <code>exec node</code> and starts the database seed under <code>setsid</code>; the task definition sets <code>initProcessEnabled</code>, so an init process is PID 1, forwards SIGTERM to <code>node</code> and reaps orphans (A9b-D7). '
         '<code>exitAfterClose</code> closes the app and exits with 0. A new <code>BullShutdownService</code> pauses every instance of each consumed queue, and the <code>api-v2</code> processor waits at most 100 s for its jobs that are not <code>B4</code> jobs, then closes its queue.</p>'
         '<p>The container&#x27;s <code>stopTimeout</code> is 120 s, the Fargate maximum, and the target group&#x27;s deregistration delay drops from 300 s to 180 s (A9b-D8). The <code>api-v2</code> job timeout becomes the run ceiling plus 1 h instead of 600 s.</p>',
         '<p>O <code>dev.sh</code> termina com <code>exec node</code> e inicia o seed do banco sob <code>setsid</code>; a task definition liga o <code>initProcessEnabled</code>, então um processo init é o PID 1, repassa o SIGTERM ao <code>node</code> e recolhe órfãos (A9b-D7). '
         'O <code>exitAfterClose</code> fecha a aplicação e sai com 0. Um novo <code>BullShutdownService</code> pausa toda instância de cada fila consumida, e o processor do <code>api-v2</code> espera no máximo 100 s pelos jobs que não são da <code>B4</code>, depois fecha a fila.</p>'
         '<p>O <code>stopTimeout</code> do container é 120 s, o máximo do Fargate, e o deregistration delay do target group cai de 300 s para 180 s (A9b-D8). O timeout do job do <code>api-v2</code> vira o teto do run mais 1 h em vez de 600 s.</p>'),
 'ba':(('A shell is PID 1; <code>node</code> is killed with the run in flight.','Um shell é o PID 1; o <code>node</code> é morto com o run em andamento.'),
       ('<code>node</code> pauses its queues, waits for its runs and exits with 0.','O <code>node</code> pausa as filas, espera os runs e sai com 0.'))},

{'n':'2','title':('One terminal outcome and the stored plan','Um só resultado final e o plano gravado'),
 'loc':'flow-execution-status.service.ts · mcp-run-status.service.ts',
 'purpose':('Every writer claims the run&#x27;s end through a compare-and-set on its status; the first claim wins (A9b-D3).',
            'Todo escritor reivindica o fim do run por um compare-and-set no status; o primeiro claim vence (A9b-D3).'),
 'body':('<p>The claim returns whether it won, and the MCP run status gets the same guard. The winner stores the run&#x27;s delivery plan in <code>end_delivery</code>, cleared once its delivery has started (A9b-D12). '
         'A loser writes no status and only starts the winner&#x27;s stored plan, so a winner that dies before its delivery starts is still delivered. '
         'The run&#x27;s end delivery uses the run id as its invocation id, so a retried end does not deliver twice (A9b-D10).</p>',
         '<p>O claim informa se venceu, e o status de run do MCP ganha a mesma guarda. O vencedor grava o plano de entrega do run em <code>end_delivery</code>, limpo quando a entrega começa (A9b-D12). '
         'Um perdedor não grava status e só inicia o plano gravado do vencedor, então um vencedor que morre antes de a entrega começar ainda é entregue. '
         'A entrega de fim do run usa o id do run como id de invocação, então um fim repetido não entrega duas vezes (A9b-D10).</p>'),
 'ba':(('Both ends deliver; the MCP status keeps whichever writes last.','Os dois fins entregam; o status do MCP fica com quem grava por último.'),
       ('One status and at most one delivery, whichever end comes first.','Um status e no máximo uma entrega, qualquer fim que venha primeiro.'))},

{'n':'3','title':('Legacy stall: interrupt, recorded cost, child runs','Travamento legado: interrupção, custo registrado, runs filhos'),
 'loc':'apiV2Job.processor.ts · stalled-run-cleanup.service.ts',
 'purpose':('A legacy run that lost its process interrupts its steps in flight and records its real cost, with no refund and no resume (A9b-D4, A9b-D5).',
            'Um run legado que perdeu o processo interrompe os passos em andamento e registra o custo real, sem reembolso e sem retomada (A9b-D4, A9b-D5).'),
 'body':('<p>Two recompute passes, at 5 min and 35 min, are scheduled before the claim, so a throw after the claim still leaves them (A9b-D14). '
         'Library and flow-caller child runs list their run ids in a Redis set of their parent, which the recompute reads (A9b-D11). '
         'No one writes a cancel request at a stall, because a cancel on the root run id would also stop the run&#x27;s <code>triggerOnly</code> children (A9b-D15).</p>',
         '<p>Duas passadas de recálculo, aos 5 min e aos 35 min, são agendadas antes do claim, então um erro depois do claim ainda as mantém (A9b-D14). '
         'Runs filhos de library e de flow-caller listam seus ids num set Redis do pai, que o recálculo lê (A9b-D11). '
         'Ninguém grava um pedido de cancelamento num travamento, porque um cancelamento no id do run raiz pararia também os filhos <code>triggerOnly</code> do run (A9b-D15).</p>'),
 'ba':(('The run ends <code>error</code> with a recorded cost of 0 while the ledger holds every charge.','O run termina em <code>error</code> com custo registrado 0 enquanto o ledger guarda todas as cobranças.'),
       ('After the final pass, the recorded cost equals the run&#x27;s charges.','Depois da última passada, o custo registrado é igual às cobranças do run.'))},

{'n':'4','title':('<code>B4</code>: the worker triggers the finish','<code>B4</code>: o worker dispara o fim'),
 'loc':'worker process-flow.workflow.ts · back flux.service.ts',
 'purpose':('A <code>B4</code> run keeps its live end, and any live back finishes it when its handler is gone (A9b-D6).',
            'Um run da <code>B4</code> mantém o fim escrito pelo handler vivo, e qualquer back vivo o finaliza quando o handler some (A9b-D6).'),
 'body':('<p>At its end, <code>processFlow</code> calls a finish activity. The back writes a reduced end only when no live handler holds the Bull job, so a run whose back task died is finished with no back waiting for it. '
         'Library and flow-caller children stay on the legacy loop until <code>B6</code> (A9b-D13). '
         'A plain <code>Error</code> in <code>processFlow</code> code now fails the workflow with a non-retryable <code>ApplicationFailure</code> instead of retrying its task forever (A9b-D16). '
         'A batch row whose <code>processFlow</code> child fails now finishes its run as <code>error</code>.</p>',
         '<p>No fim, o <code>processFlow</code> chama uma activity de fim. O back grava um fim reduzido só quando nenhum handler vivo segura o job do Bull, então um run cuja task do back morreu é finalizado sem nenhum back esperando por ele. '
         'Filhos de library e de flow-caller ficam no laço legado até a <code>B6</code> (A9b-D13). '
         'Um <code>Error</code> comum no código do <code>processFlow</code> agora falha o workflow com um <code>ApplicationFailure</code> não repetível em vez de repetir a task para sempre (A9b-D16). '
         'Uma linha de batch cujo filho <code>processFlow</code> falha agora finaliza o run como <code>error</code>.</p>'),
 'ba':(('The worker charges every node, nothing writes the end, and the stall report marks the run <code>error</code>.','O worker cobra todo node, nada grava o fim, e o aviso de travamento marca o run como <code>error</code>.'),
       ('Any live back writes one status, at most one delivery and a cost equal to the charges.','Qualquer back vivo grava um status, no máximo uma entrega e um custo igual às cobranças.'))},

{'n':'5','title':('No run stays unfinished','Nenhum run fica sem fim'),
 'loc':'unfinished-run-reaper.service.ts · flag unfinished_run_reaper',
 'purpose':('A cron closes any async run <code>in_progress</code> past its limit, or <code>pending</code> past 24 h, and stops its processing (A9b-D9).',
            'Um cron fecha qualquer run assíncrono <code>in_progress</code> além do limite, ou <code>pending</code> há mais de 24 h, e para o processamento (A9b-D9).'),
 'body':('<p>The limit is the run ceiling plus 30 min, or the flag&#x27;s value when it is larger. The cron also starts every stored plan that no one started, and skips a run while Temporal cannot be reached. '
         'A row older than 7 days is closed with status, error and cost only, with no callback and no email, and each tick reads at most 100 rows per select, oldest first (A9b-D17). '
         'Its error texts are fixed messages in the tone of the stall message (A9b-D18).</p>'
         '<p>A seed migration creates <code>unfinished_run_reaper</code> off, and it stays off in production after the release: turning it on is a separate decision. '
         'Production held 49 runs <code>in_progress</code> for over 7 days on 2026-11-17; the first tick after the flag goes on closes them with no callback.</p>',
         '<p>O limite é o teto do run mais 30 min, ou o valor da flag quando for maior. O cron também inicia todo plano gravado que ninguém iniciou, e pula um run enquanto o Temporal não responde. '
         'Uma linha com mais de 7 dias é fechada só com status, erro e custo, sem callback e sem email, e cada ciclo lê no máximo 100 linhas por select, as mais antigas primeiro (A9b-D17). '
         'Os textos de erro são mensagens fixas no tom da mensagem de travamento (A9b-D18).</p>'
         '<p>Uma migration de seed cria a <code>unfinished_run_reaper</code> desligada, e ela continua desligada em produção depois da liberação: ligá-la é uma decisão à parte. '
         'A produção tinha 49 runs <code>in_progress</code> há mais de 7 dias em 17/11/2026; o primeiro ciclo depois de a flag ligar os fecha sem callback.</p>')},
]

VERIF = [
 (True, ('Negative control — the production image','Controle negativo — a imagem de produção'),
  ('With the production command and no init process, the back image before the fix logs its shutdown and then stays up until it is killed (exit 137 after 121 s). After the fix it exits with 0 after 1 s, with and without the init process.',
   'Com o comando de produção e sem processo init, a imagem do back antes da correção loga o desligamento e continua no ar até ser morta (exit 137 depois de 121 s). Depois da correção ela sai com 0 depois de 1 s, com e sem o processo init.')),
 (True, ('One outcome, both orders, both run kinds','Um resultado, nos dois sentidos, nos dois tipos de run'),
  ('Processor tests for an API run and an MCP run, with the stall first and with the live end first: one status write and at most one delivery. Each new test was seen failing against a broken fix.',
   'Testes do processor para um run de API e um run do MCP, com o travamento primeiro e com o fim vivo primeiro: uma escrita de status e no máximo uma entrega. Cada teste novo foi visto falhando contra uma correção quebrada.')),
 (True, ('A local stack with two back processes','Um stack local com dois processos do back'),
  ('SIGTERM with a legacy run that ends within 100 s: the run completes and the process exits. A legacy run still going at 100 s, and a <code>B4</code> run whose back is killed: the other process writes the end. Every run ended with one status and one callback.',
   'SIGTERM com um run legado que termina em até 100 s: o run completa e o processo sai. Um run legado ainda rodando aos 100 s, e um run da <code>B4</code> cujo back é morto: o outro processo grava o fim. Todo run terminou com um status e um callback.')),
 (True, ('Dev QA on AWS (2026-11-17)','QA em dev na AWS (17/11/2026)'),
  ('Eight cases on dev with the new task definition settings: legacy and <code>B4</code> runs across back deploys, MCP runs, a batch, and the cron closing an old <code>pending</code> row and an old <code>in_progress</code> row with one callback each. Every api task replaced under the new settings exited with 0, and each recorded cost equalled the ledger after the recompute. One case is a measurement: a worker deploy killed a worker at its 30 s stop timeout and failed 1 of 10 runs, which a follow-up owns.',
   'Oito casos em dev com as novas configurações da task definition: runs legados e da <code>B4</code> atravessando deploys do back, runs do MCP, um batch, e o cron fechando uma linha <code>pending</code> antiga e uma <code>in_progress</code> antiga com um callback cada. Toda task de api substituída com as novas configurações saiu com 0, e cada custo registrado igualou o ledger depois do recálculo. Um caso é uma medição: um deploy do worker matou um worker no stop timeout de 30 s e falhou 1 de 10 runs, que uma task seguinte assume.')),
 (True, ('Query cost','Custo das queries'),
  ('<code>EXPLAIN ANALYZE</code> on a local copy with 1.2 million <code>node_executions</code> rows: the six cron selects and the recompute and interrupt reads use their indexes, with no sequential scan.',
   '<code>EXPLAIN ANALYZE</code> numa cópia local com 1,2 milhão de linhas de <code>node_executions</code>: os seis selects do cron e as leituras do recálculo e da interrupção usam os índices, sem varredura sequencial.')),
 (True, ('Production release (2026-11-18)','Liberação em produção (18/11/2026)'),
  ('Worker first, then <code>stopTimeout</code> 120 s and the 180 s deregistration delay, then back #2114, then <code>initProcessEnabled</code>. The replaced back task paused 10 queue instances, waited for 0 runs, closed its queue drained and stopped with exit code 0; the migrations ran at boot with no error.',
   'Worker primeiro, depois <code>stopTimeout</code> 120 s e o deregistration delay de 180 s, depois o back #2114, depois o <code>initProcessEnabled</code>. A task do back substituída pausou 10 instâncias de fila, esperou 0 runs, fechou a fila drenada e parou com exit code 0; as migrations rodaram no boot sem erro.')),
]

DONE = ('A back deploy does not kill an async run on the <code>B4</code> path, and a legacy run that loses its process ends with one status, at most one delivery and, after the final recompute pass, a recorded cost equal to its charges. '
        'A back task stopped by a deploy takes no new Bull job after SIGTERM, a plain <code>Error</code> in <code>processFlow</code> fails the workflow, and while the flag is on the cron closes every run past its limit.',
        'Um deploy do back não mata um run assíncrono no caminho da <code>B4</code>, e um run legado que perde o processo termina com um status, no máximo uma entrega e, depois da última passada de recálculo, um custo registrado igual às cobranças. '
        'Uma task do back parada por um deploy não pega job novo do Bull depois do SIGTERM, um <code>Error</code> comum no <code>processFlow</code> falha o workflow, e com a flag ligada o cron fecha todo run além do limite.')

FILES = [('back/dev.sh', False),
         ('back/src/main.ts', False),
         ('back/src/common/exit-after-close.ts', True),
         ('back/src/jobs/bull-shutdown.service.ts', True),
         ('back/src/jobs/apiV2Job/apiV2Job.processor.ts', False),
         ('back/src/app-api/flux/flow-execution-status.service.ts', False),
         ('back/src/app-mcp/mcp-run-status.service.ts', False),
         ('back/src/app-api/flux/run-end/run-end-delivery.service.ts', True),
         ('back/src/app-api/flux/run-children.registry.ts', True),
         ('back/src/app-api/flux/flux.service.ts', False),
         ('back/src/cronJobs/unfinishedRunReaper/unfinished-run-reaper.service.ts', True),
         ('worker/src/modules/temporal/workflows/process-flow.workflow.ts', False),
         ('worker/src/modules/temporal/workflows/process-batch.workflow.ts', False),
         ('worker/src/modules/temporal/activities/activities.service.ts', False)]

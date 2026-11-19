# -*- coding: utf-8 -*-
TITLE = ('A worker that stops mid-activity does not fail the run',
         'Um worker que para no meio de uma activity não derruba o run')

GOAL = ('A worker deploy <b>does not fail a run</b>: an activity drains for up to 100 s, and one that is still cut runs again on another worker when running it twice is safe.',
        'Um deploy do worker <b>não derruba um run</b>: uma activity drena por até 100 s, e uma que ainda é cortada roda de novo em outro worker quando rodar duas vezes é seguro.')

GLANCE = [
 ('crit', ('Customer impact','Impacto no cliente'), ('A deploy failed runs','Um deploy derrubava runs'),
  ('A worker deploy failed or truncated node activities still running: 1 run of 10 ended <code>error</code> on AWS dev, and locally 6 of 6 cut runs were truncated and reported as successes.',
   'Um deploy do worker derrubava ou cortava as activities de nó ainda em execução: 1 run de 10 terminou em <code>error</code> no dev da AWS, e no teste local 6 de 6 runs cortados saíram truncados e reportados como sucesso.')),
 ('dep', ('Depends on','Depende de'), ('A9b','A9b'),
  ('A9b found the gap; this task reuses its AWS test harness.',
   'A A9b achou a lacuna; esta task reaproveita o harness de teste dela na AWS.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Added on 2026-11-16 from A9b.','Adicionada em 16/11/2026 a partir da A9b.')),
 ('ship', ('Shape','Formato'), ('Worker and task definitions','Worker e task definitions'),
  ('In production since 2026-11-19 (worker #174, <code>worker-task-definition-prod:106</code>).',
   'Em produção desde 19/11/2026 (worker #174, <code>worker-task-definition-prod:106</code>).')),
]

LEDE = (
 '<p>No worker task definition set <code>stopTimeout</code>, so ECS killed the worker 30 s after SIGTERM, when its 30 s grace ended. '
 'At that moment the Temporal SDK cancels every activity in flight, and two helpers turned that cancel into a cancel the workflow did not ask for: '
 '<code>runCancellableNode</code> settled <code>textGenerator</code> and <code>apiCaller</code> as cancelled, and <code>runNodeActivity</code> re-threw the abort. '
 '<strong>No node activity retried</strong>: every one ran with one attempt, except <code>largeMemory</code>.</p>'
 '<p>The production query of node durations over 30 days set the values: 17 % of <code>textGenerator</code> runs (1,827 of 10,703) last over 100 s, so the drain alone does not save them, '
 'while <code>apiCaller</code> never passed 62.3 s, so the drain covers almost every activity that writes to a customer system.</p>',
 '<p>Nenhuma task definition do worker definia <code>stopTimeout</code>, então o ECS matava o worker 30 s depois do SIGTERM, quando terminava a carência de 30 s. '
 'Nesse momento o SDK do Temporal cancela toda activity em andamento, e dois helpers transformavam esse cancelamento num cancelamento que o workflow não pediu: '
 'o <code>runCancellableNode</code> encerrava <code>textGenerator</code> e <code>apiCaller</code> como cancelados, e o <code>runNodeActivity</code> relançava o abort. '
 '<strong>Nenhuma activity de nó tentava de novo</strong>: todas rodavam com uma tentativa, exceto a <code>largeMemory</code>.</p>'
 '<p>A consulta de produção das durações dos nós em 30 dias fixou os valores: 17 % das execuções do <code>textGenerator</code> (1.827 de 10.703) passam de 100 s, então só a drenagem não as salva, '
 'enquanto o <code>apiCaller</code> nunca passou de 62,3 s, então a drenagem cobre quase toda activity que grava num sistema do cliente.</p>')

TABLE = dict(
 head=[('On a worker deploy','Num deploy do worker'),('Before A9c','Antes da A9c'),('After A9c','Depois da A9c')],
 rows=[
  [('Time an activity gets to finish','Tempo que uma activity tem para terminar'),
   {'t':('30 s, then SIGKILL','30 s, depois SIGKILL'),'pill':'weak'},
   {'t':('100 s drain, stop forced at 110 s, SIGKILL at 120 s','Drenagem de 100 s, parada forçada em 110 s, SIGKILL em 120 s'),'pill':'ok'}],
  [('A cut <code>safe</code>, <code>provider-cost</code> or <code>keyed</code> activity','Uma activity <code>safe</code>, <code>provider-cost</code> ou <code>keyed</code> cortada'),
   {'t':('Fails or settles as cancelled','Falha ou é encerrada como cancelada'),'pill':'weak'},
   {'t':('Runs once more on another worker','Roda mais uma vez em outro worker'),'pill':'ok'}],
  [('A cut <code>not-safe</code> activity','Uma activity <code>not-safe</code> cortada'),
   {'t':('Settles as cancelled; the run ends <code>completed</code> with the output cut short','É encerrada como cancelada; o run termina <code>completed</code> com a saída cortada'),'pill':'weak'},
   {'t':('Fails its node with a clear message; never sent twice','Falha o nó com uma mensagem clara; nunca é enviada duas vezes'),'pill':'ok'}],
  [('Charge to the customer','Cobrança do cliente'),
   {'t':('Once per node execution','Uma vez por execução de nó'),'pill':'ok'},
   {'t':('Once per node execution, whatever the attempts','Uma vez por execução de nó, qualquer que seja o número de tentativas'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('A 100 s drain on a worker deploy','Uma drenagem de 100 s num deploy do worker'),
 'loc':'worker/src/modules/temporal/temporal.constants.ts · worker-task-definition (dev, staging, prod)',
 'purpose':('The worker sets <code>shutdownGraceTime</code> 100 s and <code>shutdownForceTime</code> 110 s, and each worker task definition sets <code>stopTimeout</code> 120 s, the Fargate maximum.',
            'O worker define <code>shutdownGraceTime</code> de 100 s e <code>shutdownForceTime</code> de 110 s, e cada task definition do worker define <code>stopTimeout</code> de 120 s, o máximo do Fargate.'),
 'body':('<p>A release script registers a revision from the live one with only <code>stopTimeout</code> changed, and refuses during a rollout or when the latest revision is not the live one. '
         'It ran on dev, staging and prod before the worker code shipped. A spec keeps grace &lt; force &lt; <code>stopTimeout</code> &le; 120 s.</p>',
         '<p>Um script de release registra uma revisão a partir da que está no ar mudando só o <code>stopTimeout</code>, e recusa durante um rollout ou quando a última revisão não é a que está no ar. '
         'Ele rodou em dev, staging e prod antes de o código do worker subir. Um spec mantém carência &lt; parada forçada &lt; <code>stopTimeout</code> &le; 120 s.</p>'),
 'ba':(('ECS kills the worker at 30 s.','O ECS mata o worker em 30 s.'),
       ('In-flight activities get up to 100 s.','As activities em andamento ganham até 100 s.'))},

{'n':'2','title':('The <code>WorkerShutdown</code> failure','A falha <code>WorkerShutdown</code>'),
 'loc':'worker/src/modules/nodes/shared/worker-shutdown.ts',
 'purpose':('One helper, <code>failIfWorkerShutdown</code>, reads the SDK\'s cancellation details when an attempt sees an abort.',
            'Um helper, o <code>failIfWorkerShutdown</code>, lê os detalhes de cancelamento do SDK quando uma tentativa vê um abort.'),
 'body':('<p>When the workflow asked for the cancel, a user cancel wins and the node ends cancelled with its partial charge, as before. '
         'Otherwise, on a worker shutdown, the attempt fails with a retryable <code>WorkerShutdown</code> failure. Both <code>runCancellableNode</code> and <code>runNodeActivity</code> call it before their own abort handling.</p>',
         '<p>Quando o workflow pediu o cancelamento, o cancelamento do usuário vence e o nó termina cancelado com a cobrança parcial, como antes. '
         'Senão, num desligamento do worker, a tentativa falha com uma falha <code>WorkerShutdown</code> que pode ser repetida. O <code>runCancellableNode</code> e o <code>runNodeActivity</code> o chamam antes do próprio tratamento de abort.</p>'),
 'ba':(('A deploy cancel looks like a user cancel.','Um cancelamento por deploy parece um cancelamento do usuário.'),
       ('A deploy cancel is a retryable failure.','Um cancelamento por deploy é uma falha que pode ser repetida.'))},

{'n':'3','title':('One retry per proxy group, only on a worker loss','Uma nova tentativa por grupo de proxy, só na perda do worker'),
 'loc':'worker/src/modules/temporal/workflows/retry-policies.ts · configs.ts',
 'purpose':('Each proxy belongs to one class: <code>safe</code>, <code>provider-cost</code>, <code>keyed</code> or <code>not-safe</code>. The long <code>safe</code> and <code>provider-cost</code> proxies and <code>largeMemory</code> get two attempts.',
            'Cada proxy pertence a uma classe: <code>safe</code>, <code>provider-cost</code>, <code>keyed</code> ou <code>not-safe</code>. Os proxies longos <code>safe</code> e <code>provider-cost</code> e a <code>largeMemory</code> ganham duas tentativas.'),
 'body':('<p>A retry fires only on <code>WorkerShutdown</code> or a heartbeat timeout: every node error category and a start-to-close timeout are non-retryable. '
         '<code>not-safe</code> proxies (<code>apiCaller</code>, <code>thirdPartyIntegration</code>, <code>mcp</code>, <code>pushData</code>, <code>fileSave</code>, <code>counter</code>, <code>sqlQuerier</code>, <code>scripting</code>, <code>completion</code>) keep one attempt, '
         'so a deploy never sends a second request to a customer system. The customer is charged once: the workflow\'s charge runs after the final attempt, and the four activities that charge inside themselves rely on the unique index on the charge.</p>',
         '<p>Uma nova tentativa só dispara em <code>WorkerShutdown</code> ou num timeout de heartbeat: toda categoria de erro de nó e um timeout de start-to-close não são repetidos. '
         'Os proxies <code>not-safe</code> (<code>apiCaller</code>, <code>thirdPartyIntegration</code>, <code>mcp</code>, <code>pushData</code>, <code>fileSave</code>, <code>counter</code>, <code>sqlQuerier</code>, <code>scripting</code>, <code>completion</code>) mantêm uma tentativa, '
         'então um deploy nunca manda um segundo pedido a um sistema do cliente. O cliente é cobrado uma vez: a cobrança do workflow roda depois da última tentativa, e as quatro activities que cobram por dentro contam com o índice único da cobrança.</p>'),
 'ba':(('Every node activity has one attempt.','Toda activity de nó tem uma tentativa.'),
       ('A cut activity that is safe to repeat runs once more.','Uma activity cortada que pode ser repetida roda mais uma vez.'))},

{'n':'4','title':('A heartbeat for <code>displayBox</code>, a retry-tolerant <code>largeMemory</code> delete','Um heartbeat para o <code>displayBox</code>, um delete da <code>largeMemory</code> que tolera nova tentativa'),
 'loc':'worker/src/modules/temporal/activities/activities.service.ts · nodes/large-memory/large-memory.service.ts',
 'purpose':('<code>displayBox</code> reached 301 s in production, so it beats through the keep-alive heartbeat with a 30 s timeout.',
            'O <code>displayBox</code> chegou a 301 s em produção, então ele bate pelo heartbeat de keep-alive com timeout de 30 s.'),
 'body':('<p>On a retry attempt, a <code>largeMemory</code> delete that finds no file counts it as already deleted; on the first attempt it fails as before. Its non-retryable list now names the category strings.</p>',
         '<p>Numa nova tentativa, um delete da <code>largeMemory</code> que não acha o arquivo o conta como já apagado; na primeira tentativa falha como antes. A lista do que não se repete agora usa os nomes das categorias.</p>')},
]

VERIF = [
 (True, ('Negative control — local, before the change','Controle negativo — local, antes da mudança'),
  ('Two workers, ten B4 runs with a 150 s generation, SIGTERM one worker: 6 of 6 cut runs stopped at the 30 s grace and ended <code>completed</code> with a truncated output.',
   'Dois workers, dez runs da B4 com uma geração de 150 s, SIGTERM num worker: 6 de 6 runs cortados pararam na carência de 30 s e terminaram <code>completed</code> com a saída truncada.')),
 (True, ('Local, after the change','Local, depois da mudança'),
  ('10 of 10 <code>completed</code>, one callback each, one charge per node; the stopped worker drained 100.1 s and the other worker finished the output. A SIGKILL case retried after the heartbeat timeout, 3 of 3 <code>completed</code>; a user cancel during a SIGTERM still ended cancelled with its partial charge.',
   '10 de 10 <code>completed</code>, um callback cada, uma cobrança por nó; o worker parado drenou 100,1 s e o outro worker terminou a saída. Um caso com SIGKILL tentou de novo depois do timeout de heartbeat, 3 de 3 <code>completed</code>; um cancelamento do usuário durante um SIGTERM ainda terminou cancelado com a cobrança parcial.')),
 (True, ('Retry triggers on the Temporal test server','Gatilhos de nova tentativa no servidor de teste do Temporal'),
  ('A start-to-close timeout runs once; a heartbeat timeout and a <code>WorkerShutdown</code> run twice; a retryable provider error runs once. Without the start-to-close entry, that case ran twice.',
   'Um timeout de start-to-close roda uma vez; um timeout de heartbeat e um <code>WorkerShutdown</code> rodam duas vezes; um erro de provedor que pode ser repetido roda uma vez. Sem a entrada de start-to-close, esse caso rodou duas vezes.')),
 (True, ('Replay','Replay'),
  ('The single-node and batch histories on disk replay against the new retry policies with no nondeterminism error.',
   'Os históricos de nó único e de lote em disco fazem replay contra as novas políticas sem erro de não determinismo.')),
 (True, ('AWS dev (2026-11-18)','Dev na AWS (18/11/2026)'),
  ('T4: 10 of 10 <code>completed</code>, one charge per node. T4b: a 290 s generation on the old task drained 100.0 s, failed as <code>WorkerShutdown</code>, and the second attempt on the new task wrote the full output; one charge.',
   'T4: 10 de 10 <code>completed</code>, uma cobrança por nó. T4b: uma geração de 290 s na task antiga drenou 100,0 s, falhou como <code>WorkerShutdown</code>, e a segunda tentativa na task nova gravou a saída inteira; uma cobrança.')),
 (True, ('Production (2026-11-19)','Produção (19/11/2026)'),
  ('<code>stopTimeout</code> 120 s applied on staging and prod, then worker #174 shipped as <code>worker-task-definition-prod:106</code>, which keeps it; no error after the rollout.',
   '<code>stopTimeout</code> de 120 s aplicado em staging e prod; depois o worker #174 subiu como <code>worker-task-definition-prod:106</code>, que o mantém; nenhum erro depois do rollout.')),
]

DONE = ('Every requirement has a test seen failing with the change reverted, the local and AWS dev runs pass, <code>stopTimeout</code> is 120 on the worker task definitions in dev, staging and prod, each <code>not-safe</code> activity has its reason recorded, and the reviews are recorded.',
        'Todo requisito tem um teste visto falhando com a mudança revertida, os testes local e no dev da AWS passam, o <code>stopTimeout</code> é 120 nas task definitions do worker em dev, staging e prod, cada activity <code>not-safe</code> tem o motivo registrado, e as revisões estão registradas.')

FILES = [('worker/src/modules/temporal/workflows/configs.ts', False),
         ('worker/src/modules/temporal/workflows/retry-policies.ts', True),
         ('worker/src/modules/nodes/shared/node-error.ts', False),
         ('worker/src/modules/temporal/worker.service.ts, temporal.constants.ts', False),
         ('worker/src/modules/nodes/shared/run-cancellable-node.ts, run-node-activity.ts', False),
         ('worker/src/modules/nodes/shared/worker-shutdown.ts', True),
         ('worker/src/modules/temporal/activities/activities.service.ts', False),
         ('worker/src/modules/nodes/large-memory/large-memory.service.ts', False)]

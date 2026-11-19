# -*- coding: utf-8 -*-
TITLE = ('Batch rows keep chat memory, a retried prepare writes once, and workflow runs keep their log steps',
         'Linhas de lote mantêm a memória do chat, um prepare repetido grava uma vez, e runs de workflow mantêm os passos no log')

GOAL = ('A batch row run through <code>processFlow</code> <b>computes and records the same thing</b> as the same row run through the API loop, a retried step writes one run, and every run whose nodes ran in the worker keeps its steps on the Logs page.',
        'Uma linha de lote rodada pelo <code>processFlow</code> <b>calcula e registra o mesmo</b> que a mesma linha rodada pelo laço da API, um passo repetido grava um run só, e todo run cujos nós rodaram no worker mantém os passos na página de Logs.')

GLANCE = [
 ('crit', ('Changes results','Muda resultados'), ('Chat memory in batch rows','Memória do chat nas linhas de lote'),
  ('A chat-memory node in a batch row ran without its history, so its answer could differ from the API run of the same row.',
   'Um nó com memória de chat numa linha de lote rodava sem o histórico, então a resposta podia diferir da execução da mesma linha pela API.')),
 ('dep', ('Depends on','Depende de'), ('A13','A13'),
  ('A13 added the batch-row finish step and the shared end of run.',
   'A A13 adicionou o passo final da linha de lote e o fim de run compartilhado.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Follow-up of the batch work.','Complemento do trabalho de lote.')),
 ('ship', ('Shape','Formato'), ('Back and worker','Back e worker'),
  ('Added on 2026-11-10 from A13 and specified on 2026-11-18; in production since 2026-11-19 (back #2121, worker #175).',
   'Adicionada em 10/11/2026 a partir da A13 e especificada em 18/11/2026; em produção desde 19/11/2026 (back #2121, worker #175).')),
]

LEDE = (
 '<p>A13 restored the batch rows\' Data Output value, callback and run logs. On the way it found <strong>three gaps it did not cause</strong>, '
 'on the paths B7 and B4 opened. Read again on 2026-11-18, two of them were wider than first written: a retried <code>prepare</code> leaves an orphan run, because each call draws its own <code>runId</code>, '
 'and the lost log steps hit <code>closeWorkerRun</code> too, the end that batch rows use in production.</p>'
 '<p>The task closes the three gaps without restating what <code>apiV2</code> already does: it calls the same session preparation, lets the workflow own the row\'s run id, and folds a worker run\'s log from its events.</p>',
 '<p>A A13 devolveu às linhas de lote o valor do Data Output, o callback e os logs do run. No caminho achou <strong>três lacunas que ela não causou</strong>, '
 'nos caminhos que a B7 e a B4 abriram. Relidas em 18/11/2026, duas eram maiores do que o escrito: um <code>prepare</code> repetido deixa um run órfão, porque cada chamada sorteia o próprio <code>runId</code>, '
 'e os passos perdidos no log atingem também o <code>closeWorkerRun</code>, o fim que as linhas de lote usam em produção.</p>'
 '<p>A task fecha as três lacunas sem reescrever o que o <code>apiV2</code> já faz: chama a mesma preparação de sessão, deixa o workflow escolher o id do run da linha, e monta o log de um run do worker a partir dos eventos.</p>')

TABLE = dict(
 head=[('Gap','Lacuna'),('Before B7b','Antes da B7b'),('After B7b','Depois da B7b')],
 rows=[
  [('Chat memory in a batch row','Memória do chat numa linha de lote'),
   {'t':('Runs without its history','Roda sem o histórico'),'pill':'weak'},
   {'t':('Same preparation as the API, in a chat session of its own','Mesma preparação da API, numa sessão de chat própria'),'pill':'ok'}],
  [('Retried <code>prepare</code>','<code>prepare</code> repetido'),
   {'t':('Leaves an orphan run','Deixa um run órfão'),'pill':'weak'},
   {'t':('Writes one run','Grava um run só'),'pill':'ok'}],
  [('Worker run, run-log flag off or shadow','Run do worker, flag de log desligada ou em shadow'),
   {'t':('Logs page shows no steps','A página de Logs mostra o run sem passos'),'pill':'weak'},
   {'t':('Steps kept in every mode','Passos mantidos em todo modo'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('One session preparation, a session per row','Uma preparação de sessão, uma sessão por linha'),
 'loc':'back/src/app-api/flux/flux.service.ts',
 'purpose':('The <code>apiV2</code> session block moves, as it is, into one method, <code>prepareRunSessionNodes</code>, that <code>apiV2</code> and the batch-row preparation both call.',
            'O bloco de sessão do <code>apiV2</code> passa, como está, para um método, o <code>prepareRunSessionNodes</code>, que o <code>apiV2</code> e a preparação da linha de lote chamam.'),
 'body':('<p>It clears memory on execution, loads the stored chat history and keeps <code>chat: true</code> on the first chat node only. '
         'Batch rows run five at a time, so sharing the <code>default</code> session would read other rows\' turns in no fixed order. Decided on 2026-11-18: each row falls back to a chat session keyed by its own <code>runId</code>, so it starts with empty memory and records its turn there. '
         'Scheduled runs keep the shared <code>default</code> session.</p>',
         '<p>Ele limpa a memória na execução, carrega o histórico salvo do chat e mantém <code>chat: true</code> só no primeiro nó de chat. '
         'As linhas de lote rodam cinco por vez, então compartilhar a sessão <code>default</code> leria os turnos de outras linhas sem ordem fixa. Decidido em 18/11/2026: cada linha cai numa sessão de chat chaveada pelo próprio <code>runId</code>, então começa com memória vazia e grava o turno nela. '
         'Execuções agendadas mantêm a sessão <code>default</code> compartilhada.</p>'),
 'ba':(('A chat-memory node answers without history.','Um nó com memória de chat responde sem histórico.'),
       ('It is prepared as through the API, in the row\'s own session.','É preparado como pela API, na sessão da própria linha.'))},

{'n':'2','title':('The workflow owns the row\'s run id','O workflow escolhe o id do run da linha'),
 'loc':'worker process-batch.workflow.ts · back batch-run-preparation.service.ts',
 'purpose':('<code>processRow</code> draws the <code>runId</code> with the workflow\'s <code>uuid4()</code> and passes it to every attempt of <code>prepareBatchRowRunActivity</code>.',
            'O <code>processRow</code> sorteia o <code>runId</code> com o <code>uuid4()</code> do workflow e o passa a toda tentativa do <code>prepareBatchRowRunActivity</code>.'),
 'body':('<p>The back takes the optional <code>runId</code>, refuses one that is not a UUID, and falls back to its own when none is sent. Each Variable Input row gets an id derived from the run and the node, inserted with <code>ON CONFLICT (id) DO NOTHING</code>, so a second call writes nothing. '
         'Deploy order: back first, then worker.</p>',
         '<p>O back aceita o <code>runId</code> opcional, recusa um que não seja UUID, e usa o próprio quando nenhum vem. Cada linha de Variable Input ganha um id derivado do run e do nó, inserido com <code>ON CONFLICT</code> no id sem sobrescrever, então uma segunda chamada não grava nada. '
         'Ordem do deploy: back primeiro, depois worker.</p>'),
 'ba':(('A retried prepare leaves an orphan run.','Um prepare repetido deixa um run órfão.'),
       ('Two calls leave one run.','Duas chamadas deixam um run só.'))},

{'n':'3','title':('Events are the log source for worker runs','Os eventos são a fonte do log para runs do worker'),
 'loc':'back flux.service.ts (openSpaceRunLog) · run-events.service.ts',
 'purpose':('A run whose nodes ran in the worker has a collector with no node entries; in <code>off</code> and <code>shadow</code> mode its end overwrote the run log with <code>nodes: []</code>.',
            'Um run cujos nós rodaram no worker tem um coletor sem entradas de nó; nos modos <code>off</code> e <code>shadow</code> o fim dele sobrescrevia o log do run com <code>nodes: []</code>.'),
 'body':('<p>A run opened for the worker now uses the <code>events</code> mode whatever the flag says, and a workflow-routed <code>apiV2</code> run switches to it when it routes. The final log is folded from events; the collector document is written only when the rebuild returns nothing or throws. Inline <code>apiV2</code> runs keep their behaviour.</p>',
         '<p>Um run aberto para o worker agora usa o modo <code>events</code> qualquer que seja a flag, e um run do <code>apiV2</code> roteado ao workflow passa para ele quando é roteado. O log final é montado a partir dos eventos; o documento do coletor só é gravado quando a reconstrução não devolve nada ou falha. Runs inline do <code>apiV2</code> mantêm o comportamento.</p>'),
 'ba':(('The Logs page shows <code>nodes: []</code>.','A página de Logs mostra <code>nodes: []</code>.'),
       ('The Logs page shows the steps.','A página de Logs mostra os passos.'))},
]

VERIF = [
 (True, ('Negative control — one per gap','Controle negativo — um por lacuna'),
  ('Seen failing without each fix: the batch-row seed had no history; with <code>uuid()</code> restored, two Variable Input rows per node; without the <code>events</code> mode, the collector log was written and nothing was folded.',
   'Visto falhando sem cada correção: o seed da linha de lote não tinha histórico; com o <code>uuid()</code> de volta, duas linhas de Variable Input por nó; sem o modo <code>events</code>, o log do coletor foi gravado e nada foi montado a partir dos eventos.')),
 (True, ('Parity','Paridade'),
  ('The same row through the API loop, with the row\'s session, and through the batch gives the same seed for the chat node.',
   'A mesma linha pelo laço da API, com a sessão da linha, e pelo lote dá o mesmo seed para o nó de chat.')),
 (True, ('Dev QA (2026-11-18)','QA em dev (18/11/2026)'),
  ('9 batch rows in 3 batches and 3 workflow-routed API runs: each row\'s seed uses its own session and the canvas session did not change; 9 of 9 Variable Input ids match the run and node; the run logs keep their nodes in <code>events</code>, <code>off</code> and <code>shadow</code> mode.',
   '9 linhas de lote em 3 lotes e 3 runs de API roteados ao workflow: o seed de cada linha usa a própria sessão e a sessão do canvas não mudou; 9 de 9 ids de Variable Input batem com o run e o nó; os logs dos runs mantêm os nós nos modos <code>events</code>, <code>off</code> e <code>shadow</code>.')),
 (True, ('Production (2026-11-19)','Produção (19/11/2026)'),
  ('Back #2121 shipped first in <code>api-task-definition-prod:858</code>, then worker #175 in <code>worker-task-definition-prod:104</code>.',
   'O back #2121 subiu primeiro em <code>api-task-definition-prod:858</code>, depois o worker #175 em <code>worker-task-definition-prod:104</code>.')),
]

DONE = ('A chat-memory node answers the same in a batch row as through the API, a retried prepare writes one run, and every run whose nodes ran in the worker shows its steps whatever the run-log flag says.',
        'Um nó com memória de chat responde igual numa linha de lote e pela API, um prepare repetido grava um run só, e todo run cujos nós rodaram no worker mostra seus passos qualquer que seja a flag de log.')

FILES = [('back/src/app-api/flux/flux.service.ts (apiV2 session block, prepareWorkflowSeedForBatchRow, seedVarInputNodeExecutions, openSpaceRunLog, closeWorkerRun)', False),
         ('back/src/app-api/flux/batch-run-preparation.service.ts (prepare)', False),
         ('back/src/app-api/space_run_logs/run-events.service.ts (persistFinishedRun)', False),
         ('worker/src/modules/temporal/workflows/process-batch.workflow.ts (processRow)', False)]

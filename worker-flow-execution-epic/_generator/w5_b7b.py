# -*- coding: utf-8 -*-
TITLE = ('Batch rows keep chat memory, a retried prepare writes once, and workflow runs keep their log steps',
         'Linhas de lote mantêm a memória do chat, um prepare repetido grava uma vez, e runs de workflow mantêm os passos no log')

GOAL = ('A batch row run through <code>processFlow</code> <b>computes and records the same thing</b> as the same row run through the API loop, and a retried step writes once.',
        'Uma linha de lote rodada pelo <code>processFlow</code> <b>calcula e registra o mesmo</b> que a mesma linha rodada pelo laço da API, e um passo repetido grava uma vez.')

GLANCE = [
 ('crit', ('Changes results','Muda resultados'), ('Chat memory in batch rows','Memória do chat nas linhas de lote'),
  ('A chat-memory node in a batch row runs without its history, so its answer can differ from the API run of the same row.',
   'Um nó com memória de chat numa linha de lote roda sem o histórico, então a resposta pode diferir da execução da mesma linha pela API.')),
 ('dep', ('Depends on','Depende de'), ('A13','A13'),
  ('A13 added the batch-row finish step and the shared end of run.',
   'A A13 adicionou o passo final da linha de lote e o fim de run compartilhado.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Follow-up of the batch work.','Complemento do trabalho de lote.')),
 ('ship', ('Shape','Formato'), ('Back only','Só o back'),
  ('Added on 2026-11-10 from the A13 batch work.',
   'Adicionada em 10/11/2026 a partir do trabalho de lote da A13.')),
]

LEDE = (
 '<p>A13 restored the batch rows\' Data Output value, callback and run logs. On the way it found <strong>three gaps it did not cause</strong>, '
 'on the paths B7 and B4 opened. None of them stops a run; the first changes what a run answers.</p>'
 '<p>The task closes the three gaps without restating what <code>apiV2</code> already does: it calls the same preparation.</p>',
 '<p>A A13 devolveu às linhas de lote o valor do Data Output, o callback e os logs do run. No caminho achou <strong>três lacunas que ela não causou</strong>, '
 'nos caminhos que a B7 e a B4 abriram. Nenhuma para um run; a primeira muda o que o run responde.</p>'
 '<p>A task fecha as três lacunas sem reescrever o que o <code>apiV2</code> já faz: chama a mesma preparação.</p>')

TABLE = dict(
 head=[('Gap','Lacuna'),('Today','Hoje'),('After B7b','Depois da B7b')],
 rows=[
  [('Chat memory in a batch row','Memória do chat numa linha de lote'),
   {'t':('Runs without its history','Roda sem o histórico'),'pill':'weak'},
   {'t':('Same preparation as the API','Mesma preparação da API'),'pill':'ok'}],
  [('Retried <code>prepare</code>','<code>prepare</code> repetido'),
   {'t':('Duplicate Variable Input rows','Linhas de Variable Input duplicadas'),'pill':'weak'},
   {'t':('Writes once','Grava uma vez'),'pill':'ok'}],
  [('API workflow run, run-log flag off or shadow','Run de workflow pela API, flag de log desligada ou em shadow'),
   {'t':('Logs page shows no steps','A página de Logs mostra o run sem passos'),'pill':'weak'},
   {'t':('Steps kept in every mode','Passos mantidos em todo modo'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('Chat memory in a batch row','Memória do chat numa linha de lote'),
 'loc':'back/src/app-api/flux/batch-run-preparation.service.ts',
 'purpose':('<code>prepareWorkflowSeedForBatchRow</code> skips the <code>fluxObject</code> preparation that <code>apiV2</code> does before a run.',
            'O <code>prepareWorkflowSeedForBatchRow</code> pula a preparação do <code>fluxObject</code> que o <code>apiV2</code> faz antes de um run.'),
 'body':('<p>The preparation clears memory on execution and loads the stored chat history. Batch-row preparation calls that same code; it does not restate it.</p>',
         '<p>A preparação limpa a memória na execução e carrega o histórico salvo do chat. A preparação da linha de lote chama esse mesmo código; não o reescreve.</p>'),
 'ba':(('A chat-memory node answers without history.','Um nó com memória de chat responde sem histórico.'),
       ('It answers as it does through the API.','Responde como responde pela API.'))},

{'n':'2','title':('A retried prepare writes once','Um prepare repetido grava uma vez'),
 'loc':'back/src/app-api/flux/batch-run-preparation.service.ts',
 'purpose':('<code>seedVarInputNodeExecutions</code> inserts new rows on every call.',
            'O <code>seedVarInputNodeExecutions</code> insere linhas novas a cada chamada.'),
 'body':('<p>A retried <code>prepare</code> leaves duplicate Variable Input rows for one run. After the change a second call finds the rows and writes nothing.</p>',
         '<p>Um <code>prepare</code> repetido deixa linhas de Variable Input duplicadas para um run. Depois da mudança, a segunda chamada acha as linhas e não grava nada.</p>'),
 'ba':(('Two calls leave two sets of rows.','Duas chamadas deixam dois conjuntos de linhas.'),
       ('Two calls leave one set.','Duas chamadas deixam um conjunto.'))},

{'n':'3','title':('Log steps on API workflow runs','Passos no log de runs de workflow pela API'),
 'loc':'back/src/app-api/flux/flux.service.ts',
 'purpose':('With <code>RUN_LOG_FROM_EVENTS</code> off or in shadow mode, the end of <code>apiV2</code> overwrites the log built from events.',
            'Com <code>RUN_LOG_FROM_EVENTS</code> desligada ou em shadow, o fim do <code>apiV2</code> sobrescreve o log montado a partir dos eventos.'),
 'body':('<p>The overwriting document has no node entries, so the Logs page shows the run without its steps. After the change an API workflow run keeps its node entries in every mode.</p>',
         '<p>O documento que sobrescreve não tem entradas de nó, então a página de Logs mostra o run sem os passos. Depois da mudança, um run de workflow pela API mantém suas entradas de nó em todo modo.</p>'),
 'ba':(('The Logs page shows <code>nodes: []</code>.','A página de Logs mostra <code>nodes: []</code>.'),
       ('The Logs page shows the steps.','A página de Logs mostra os passos.'))},
]

VERIF = [
 (True, ('Negative control — one per gap','Controle negativo — um por lacuna'),
  ('Seen failing on the current code: a chat-memory node in a batch row answers without history; <code>prepare</code> called twice leaves two Variable Input rows; an API workflow run in <code>off</code> mode shows <code>nodes: []</code> on the Logs page.',
   'Visto falhando no código atual: um nó com memória de chat numa linha de lote responde sem histórico; <code>prepare</code> chamado duas vezes deixa duas linhas de Variable Input; um run de workflow pela API em modo <code>off</code> mostra <code>nodes: []</code> na página de Logs.')),
 (True, ('Parity','Paridade'),
  ('The same row through the API loop and through the batch gives the same answer and the same memory entries.',
   'A mesma linha pelo laço da API e pelo lote dá a mesma resposta e as mesmas entradas de memória.')),
]

DONE = ('A chat-memory node answers the same in a batch row as through the API, a retried prepare writes once, and an API workflow run shows its steps whatever the run-log flag says.',
        'Um nó com memória de chat responde igual numa linha de lote e pela API, um prepare repetido grava uma vez, e um run de workflow pela API mostra seus passos qualquer que seja a flag de log.')

FILES = [('back/src/app-api/flux/batch-run-preparation.service.ts (prepareWorkflowSeedForBatchRow, seedVarInputNodeExecutions)', False),
         ('back/src/app-api/flux/flux.service.ts (the fluxObject preparation in apiV2, the end-of-run log write)', False),
         ('back/src/app-api/space_run_logs/run-events.service.ts', False)]

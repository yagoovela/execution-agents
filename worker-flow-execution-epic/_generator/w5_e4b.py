# -*- coding: utf-8 -*-
TITLE = ('Scheduled runs on Temporal Schedules finish through the back',
         'Runs agendados no Temporal Schedules terminam pelo back')

GOAL = ('With <code>temporal_schedules</code> on, a scheduled run <b>delivers and logs</b> exactly as it did through the <code>apiV2</code> job.',
        'Com <code>temporal_schedules</code> ligada, um run agendado <b>entrega e registra</b> exatamente como fazia pelo job do <code>apiV2</code>.')

GLANCE = [
 ('crit', ('Blocks','Bloqueia'), ('Turning the flag on in production','Ligar a flag em produção'),
  ('Nobody is affected today: <code>temporal_schedules</code> was off in production on 2026-11-10.',
   'Ninguém é afetado hoje: a <code>temporal_schedules</code> estava desligada em produção em 10/11/2026.')),
 ('dep', ('Depends on','Depende de'), ('E4 and A13','E4 e A13'),
  ('A13 closed the same gap for batch rows; this task reuses its finish step.',
   'A A13 fechou a mesma lacuna nas linhas de lote; esta task reaproveita o passo final dela.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Follow-up of E4.','Complemento da E4.')),
 ('ship', ('Shape','Formato'), ('Worker and back','Worker e back'),
  ('Added on 2026-11-10 from A13.','Adicionada em 10/11/2026 a partir da A13.')),
]

LEDE = (
 '<p><code>runScheduledFlow</code> starts the flow straight as a <code>processFlow</code> child. The run never reaches the back\'s end of run, '
 'so <strong>the Data Output\'s email and callbacks are not sent and the run logs are not written</strong>. Before E4 a scheduled run went through the <code>apiV2</code> job and did all of that.</p>'
 '<p>Batch rows had the same gap; A13 closed it with a worker-to-back finish call. This task gives scheduled runs the same finish.</p>',
 '<p>O <code>runScheduledFlow</code> inicia o fluxo direto como filho do <code>processFlow</code>. O run nunca chega ao fim de run do back, '
 'então <strong>o email e os callbacks do Data Output não são enviados e os logs do run não são gravados</strong>. Antes da E4, um run agendado passava pelo job do <code>apiV2</code> e fazia tudo isso.</p>'
 '<p>As linhas de lote tinham a mesma lacuna; a A13 a fechou com uma chamada de fim do worker para o back. Esta task dá o mesmo fim aos runs agendados.</p>')

TABLE = dict(
 head=[('Scheduled run','Run agendado'),('Through the apiV2 job','Pelo job do apiV2'),('On Temporal Schedules today','No Temporal Schedules hoje'),('After E4b','Depois da E4b')],
 rows=[
  [('Data Output email and callbacks','Email e callbacks do Data Output'),
   {'t':('Sent','Enviados'),'pill':'ok'},
   {'t':('Not sent','Não enviados'),'pill':'weak'},
   {'t':('Sent once','Enviados uma vez'),'pill':'ok'}],
  [('Run logs','Logs do run'),
   {'t':('Written','Gravados'),'pill':'ok'},
   {'t':('Not written','Não gravados'),'pill':'weak'},
   {'t':('Written','Gravados'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('A finish step after the child returns','Um passo final depois que o filho retorna'),
 'loc':'worker/src/workflows/run-scheduled-flow.workflow.ts',
 'purpose':('After the <code>processFlow</code> child returns, <code>runScheduledFlow</code> calls a finish activity that asks the back to settle the run.',
            'Depois que o filho <code>processFlow</code> retorna, o <code>runScheduledFlow</code> chama uma activity final que pede ao back para encerrar o run.'),
 'body':('<p>The back settles it through <code>settleRunOutputs</code>, with the schedule\'s email setting and run type, the way the batch finish does. The new step sits behind a <code>patched()</code> marker, with replay histories for both shapes.</p>',
         '<p>O back o encerra pelo <code>settleRunOutputs</code>, com a configuração de email e o tipo de run do agendamento, como o fim do lote faz. O passo novo fica atrás de um marcador <code>patched()</code>, com históricos de replay para os dois formatos.</p>'),
 'ba':(('The run ends without delivery or logs.','O run termina sem entrega nem logs.'),
       ('The run ends through the back.','O run termina pelo back.'))},

{'n':'2','title':('Delivery once per run','Entrega uma vez por run'),
 'loc':'back/src/app-api/flux/flux.service.ts',
 'purpose':('Delivery uses one workflow id per run, so a retried finish delivers once.',
            'A entrega usa um workflow id por run, então um passo final repetido entrega uma vez.'),
 'body':('<p>The run logs are written through the helpers A13 shared. Pause, backfill and last-run state stay in E4.</p>',
         '<p>Os logs do run são gravados pelos helpers que a A13 compartilhou. Pause, backfill e estado da última execução continuam na E4.</p>')},
]

VERIF = [
 (True, ('Negative control','Controle negativo'),
  ('A scheduled run of a flow with a Data Output sends nothing on the current code and delivers once after the change.',
   'Um run agendado de um fluxo com Data Output não envia nada no código atual e entrega uma vez depois da mudança.')),
 (True, ('Parity','Paridade'),
  ('Compare with a scheduled run through the <code>apiV2</code> job: same deliveries and same log records.',
   'Comparar com um run agendado pelo job do <code>apiV2</code>: mesmas entregas e mesmos registros de log.')),
 (True, ('Failure after the side effect','Falha depois do efeito colateral'),
  ('The finish retried after the delivery started delivers once.',
   'O passo final repetido depois que a entrega começou entrega uma vez.')),
]

DONE = ('A scheduled run on Temporal Schedules delivers, replies and logs like one through the <code>apiV2</code> job, once per run, and the flag can be turned on in production.',
        'Um run agendado no Temporal Schedules entrega, responde e registra como um pelo job do <code>apiV2</code>, uma vez por run, e a flag pode ser ligada em produção.')

FILES = [('worker run-scheduled-flow.workflow.ts', False),
         ('worker: the batch finish activity A13 added', False),
         ('back settleRunOutputs, finishBatchRowRun (to generalise to a worker-started run) and the worker controller', False)]

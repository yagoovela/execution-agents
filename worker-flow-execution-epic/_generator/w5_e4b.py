# -*- coding: utf-8 -*-
TITLE = ('Scheduled runs on Temporal Schedules finish through the back',
         'Runs agendados no Temporal Schedules terminam pelo back')

GOAL = ('With <code>temporal_schedules</code> on, a scheduled run <b>delivers and logs</b> exactly as it did through the <code>apiV2</code> job.',
        'Com <code>temporal_schedules</code> ligada, um run agendado <b>entrega e registra</b> exatamente como fazia pelo job do <code>apiV2</code>.')

GLANCE = [
 ('crit', ('Blocked','Bloqueava'), ('Turning the flag on in production','Ligar a flag em produção'),
  ('Nobody was affected: <code>temporal_schedules</code> is off in production. Before turning it on, run <code>POST /schedule/admin/reconcile-temporal</code>.',
   'Ninguém foi afetado: a <code>temporal_schedules</code> está desligada em produção. Antes de ligá-la, rodar <code>POST /schedule/admin/reconcile-temporal</code>.')),
 ('dep', ('Depends on','Depende de'), ('E4 and A13','E4 e A13'),
  ('A13 closed the same gap for batch rows; this task reuses its finish step.',
   'A A13 fechou a mesma lacuna nas linhas de lote; esta task reaproveita o passo final dela.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Follow-up of E4.','Complemento da E4.')),
 ('ship', ('Shape','Formato'), ('Worker and back','Worker e back'),
  ('Added on 2026-11-10 from A13; in production since 2026-11-19 (back #2122, worker #176).','Adicionada em 10/11/2026 a partir da A13; em produção desde 19/11/2026 (back #2122, worker #176).')),
]

LEDE = (
 '<p><code>runScheduledFlow</code> starts the flow straight as a <code>processFlow</code> child. The run never reaches the back\'s end of run, '
 'so <strong>the Data Output\'s email and callbacks are not sent and the run logs are not written</strong>. Before E4 a scheduled run went through the <code>apiV2</code> job and did all of that.</p>'
 '<p>Batch rows had the same gap; A13 closed it with a worker-to-back finish call. This task gives scheduled runs the same finish. '
 'On 2026-11-18 the scope widened: the Temporal path also ignored the schedule\'s <code>variableInputs</code> and seeded the run from the flow\'s saved values, so the back now seeds the run, the way it seeds a batch row.</p>',
 '<p>O <code>runScheduledFlow</code> inicia o fluxo direto como filho do <code>processFlow</code>. O run nunca chega ao fim de run do back, '
 'então <strong>o email e os callbacks do Data Output não são enviados e os logs do run não são gravados</strong>. Antes da E4, um run agendado passava pelo job do <code>apiV2</code> e fazia tudo isso.</p>'
 '<p>As linhas de lote tinham a mesma lacuna; a A13 a fechou com uma chamada de fim do worker para o back. Esta task dá o mesmo fim aos runs agendados. '
 'Em 18/11/2026 o escopo cresceu: o caminho do Temporal também ignorava os <code>variableInputs</code> do agendamento e semeava o run com os valores salvos do fluxo, então agora o back semeia o run, como semeia uma linha de lote.</p>')

TABLE = dict(
 head=[('Scheduled run','Run agendado'),('Through the apiV2 job','Pelo job do apiV2'),('On Temporal Schedules before E4b','No Temporal Schedules antes da E4b'),('After E4b','Depois da E4b')],
 rows=[
  [('Data Output email and callbacks','Email e callbacks do Data Output'),
   {'t':('Sent','Enviados'),'pill':'ok'},
   {'t':('Not sent','Não enviados'),'pill':'weak'},
   {'t':('Sent once','Enviados uma vez'),'pill':'ok'}],
  [('Run logs','Logs do run'),
   {'t':('Written','Gravados'),'pill':'ok'},
   {'t':('Not written','Não gravados'),'pill':'weak'},
   {'t':('Written','Gravados'),'pill':'ok'}],
  [('The schedule\'s variable inputs','Os inputs variáveis do agendamento'),
   {'t':('Applied','Aplicados'),'pill':'ok'},
   {'t':('Ignored','Ignorados'),'pill':'weak'},
   {'t':('Applied','Aplicados'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('The back seeds the run from the schedule','O back semeia o run a partir do agendamento'),
 'loc':'back POST /worker/scheduled-run · prepareWorkflowSeed',
 'purpose':('Behind <code>patched("e4b-scheduled-run-finish")</code>, <code>runScheduledFlow</code> calls <code>prepareScheduledRunActivity</code> in place of the old seed activity.',
            'Atrás do <code>patched("e4b-scheduled-run-finish")</code>, o <code>runScheduledFlow</code> chama o <code>prepareScheduledRunActivity</code> no lugar da activity de seed antiga.'),
 'body':('<p>The back seeds the run with the schedule\'s <code>variableInputs</code> through <code>prepareWorkflowSeed</code>, shared with batch rows, and refuses a deleted schedule. '
         'The seed rows carry the run type and the <code>runId</code>, so the Logs page lists one run per fire instead of a separate one-node run for the variable input.</p>',
         '<p>O back semeia o run com os <code>variableInputs</code> do agendamento pelo <code>prepareWorkflowSeed</code>, compartilhado com as linhas de lote, e recusa um agendamento apagado. '
         'As linhas do seed levam o tipo do run e o <code>runId</code>, então a página de Logs lista um run por disparo em vez de um run separado de um nó para o input variável.</p>'),
 'ba':(('The run uses the flow\'s saved values.','O run usa os valores salvos do fluxo.'),
       ('The run uses the schedule\'s inputs.','O run usa os inputs do agendamento.'))},

{'n':'2','title':('A finish step after the child returns','Um passo final depois que o filho retorna'),
 'loc':'worker run-scheduled-flow.workflow.ts · back POST /worker/scheduled-run-outputs',
 'purpose':('After the <code>processFlow</code> child returns, <code>finishScheduledRunActivity</code> asks the back to close the run through <code>closeWorkerRun</code>, with run type <code>cronjob</code> and email on.',
            'Depois que o filho <code>processFlow</code> retorna, o <code>finishScheduledRunActivity</code> pede ao back para fechar o run pelo <code>closeWorkerRun</code>, com tipo de run <code>cronjob</code> e email ligado.'),
 'body':('<p>When <code>processFlow</code> itself fails, the run is finished as an error and the scheduled run still fails with that error. A child cancelled on its own is finished as <code>cancelled</code>. '
         'Three replay histories, without the finish, with it and with a failed child, replay on the new code.</p>',
         '<p>Quando o próprio <code>processFlow</code> falha, o run é fechado como erro e o run agendado ainda falha com esse erro. Um filho cancelado por conta própria é fechado como <code>cancelled</code>. '
         'Três históricos de replay, sem o passo final, com ele e com um filho que falhou, fazem replay no código novo.</p>'),
 'ba':(('The run ends without delivery or logs.','O run termina sem entrega nem logs.'),
       ('The run ends through the back.','O run termina pelo back.'))},

{'n':'3','title':('Delivery once per run','Entrega uma vez por run'),
 'loc':'back flux.service.ts (closeWorkerRun)',
 'purpose':('Each delivery starts under the invocation id <code>scheduled-run</code>, so a retried finish delivers once.',
            'Cada entrega começa com o id de invocação <code>scheduled-run</code>, então um passo final repetido entrega uma vez.'),
 'body':('<p>The run writes <code>flows_logs</code>, <code>space_run_logs</code> and <code>chat_logs</code> through the helpers batch rows use. The <code>chat_logs</code> body is an explicit field list, so the schedule row and its owner are never copied. Pause, backfill and last-run state stay in E4.</p>',
         '<p>O run grava <code>flows_logs</code>, <code>space_run_logs</code> e <code>chat_logs</code> pelos helpers que as linhas de lote usam. O corpo do <code>chat_logs</code> é uma lista explícita de campos, então a linha do agendamento e o dono dela nunca são copiados. Pause, backfill e estado da última execução continuam na E4.</p>')},
]

VERIF = [
 (True, ('Negative control and parity','Controle negativo e paridade'),
  ('Against the <code>apiV2</code> loop for a scheduled run: the same delivery plan, one delivery on a retried finish, no delivery when a producer fails, the schedule inputs in the seed, and the same <code>flows_logs</code>, <code>chat_logs</code>, chat memory and space run log. Each test was seen failing first.',
   'Contra o laço do <code>apiV2</code> para um run agendado: o mesmo plano de entrega, uma entrega num passo final repetido, nenhuma entrega quando um produtor falha, os inputs do agendamento no seed, e os mesmos <code>flows_logs</code>, <code>chat_logs</code>, memória de chat e log de run do espaço. Cada teste foi visto falhando antes.')),
 (True, ('Replay','Replay'),
  ('Three histories replay on the branch; without the guard, or with the old path forced, the replay fails with a <code>DeterminismViolationError</code>.',
   'Três históricos fazem replay na branch; sem a guarda, ou forçando o caminho antigo, o replay falha com <code>DeterminismViolationError</code>.')),
 (True, ('Dev (2026-11-18)','Dev (18/11/2026)'),
  ('A new schedule fired three times every 3 minutes: each fire wrote one success row and exactly one delivery row, one space run log, and the output node received the schedule\'s input, not the saved value. After the Logs split fix, each fire is one run with all its nodes.',
   'Um agendamento novo disparou três vezes a cada 3 minutos: cada disparo gravou uma linha de sucesso e exatamente uma linha de entrega, um log de run do espaço, e o nó de saída recebeu o input do agendamento, não o valor salvo. Depois da correção da divisão em Logs, cada disparo é um run com todos os nós.')),
 (True, ('Production (2026-11-19)','Produção (19/11/2026)'),
  ('Back #2122 shipped first in <code>api-task-definition-prod:858</code>, then worker #176 in <code>worker-task-definition-prod:104</code>. <code>temporal_schedules</code> stays off.',
   'O back #2122 subiu primeiro em <code>api-task-definition-prod:858</code>, depois o worker #176 em <code>worker-task-definition-prod:104</code>. A <code>temporal_schedules</code> continua desligada.')),
]

DONE = ('A scheduled run on Temporal Schedules delivers, replies and logs like one through the <code>apiV2</code> job, once per run, and the flag can be turned on in production.',
        'Um run agendado no Temporal Schedules entrega, responde e registra como um pelo job do <code>apiV2</code>, uma vez por run, e a flag pode ser ligada em produção.')

FILES = [('worker run-scheduled-flow.workflow.ts', False),
         ('worker: prepareScheduledRunActivity and finishScheduledRunActivity', True),
         ('back: POST /worker/scheduled-run and /worker/scheduled-run-outputs, prepareWorkflowSeed, closeWorkerRun', False)]

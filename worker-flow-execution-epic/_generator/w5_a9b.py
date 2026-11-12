# -*- coding: utf-8 -*-
TITLE = ('A stalled async API run reaches one outcome and delivers once',
         'Um run de API assíncrono travado chega a um só resultado e entrega uma vez')

GOAL = ('When Bull marks a running async <code>apiV2</code> job as stalled, the run ends with <b>exactly one outcome</b>: one execution status, one MCP run status and one delivery.',
        'Quando o Bull marca um job <code>apiV2</code> assíncrono em andamento como travado, o run termina com <b>exatamente um resultado</b>: um status de execução, um status de run do MCP e uma entrega.')

GLANCE = [
 ('crit', ('Matters most','Importa mais'), ('With more than one back task','Com mais de uma task do back'),
  ('Another replica can then detect the stall while the job is still running.',
   'Outra réplica pode então detectar o travamento enquanto o job ainda roda.')),
 ('dep', ('Depends on','Depende de'), ('A9 and the stall fix','A9 e a correção do travamento'),
  ('A9 moved delivery into a workflow; back PR #2086 stopped Bull from redelivering a stalled job.',
   'A A9 levou a entrega para um workflow; o PR #2086 do back impediu o Bull de reentregar um job travado.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Follow-up of A13.','Complemento da A13.')),
 ('ship', ('Shape','Formato'), ('Back only','Só o back'),
  ('Added on 2026-11-11 from A13.','Adicionada em 11/11/2026 a partir da A13.')),
]

LEDE = (
 '<p>Since back PR #2086 a stalled async job is not redelivered. Instead <code>failStalledRun</code> marks the run failed and delivers the error callback. '
 'A job also stalls when its process is alive but its event loop is blocked. If that job then resumes, <strong>the same run reaches its normal end</strong>: '
 'the status flips from <code>error</code> to <code>completed</code> and a second delivery sends the real outputs.</p>'
 '<p>The customer receives a failure callback followed by a success callback for the same run. A fixed delivery id alone is the wrong fix: it keeps whichever delivery starts first, usually the failure.</p>',
 '<p>Desde o PR #2086 do back, um job assíncrono travado não é reentregue. Em vez disso o <code>failStalledRun</code> marca o run como falho e entrega o callback de erro. '
 'Um job também trava quando o processo está vivo mas o event loop está bloqueado. Se esse job retoma, <strong>o mesmo run chega ao seu fim normal</strong>: '
 'o status passa de <code>error</code> para <code>completed</code> e uma segunda entrega envia as saídas reais.</p>'
 '<p>O cliente recebe um callback de falha seguido de um callback de sucesso para o mesmo run. Um id de entrega fixo sozinho é a correção errada: mantém a entrega que começar primeiro, em geral a de falha.</p>')

TABLE = dict(
 head=[('When the live job finishes after the stall report','Quando o job vivo termina depois do aviso de travamento'),('Today','Hoje'),('After A9b','Depois da A9b')],
 rows=[
  [('Execution status and MCP run status','Status de execução e status de run do MCP'),
   {'t':('Flips from error to completed','Passa de error para completed'),'pill':'weak'},
   {'t':('One terminal status','Um só status final'),'pill':'ok'}],
  [('Deliveries (callback, email)','Entregas (callback, email)'),
   {'t':('Two: the failure, then the outputs','Duas: a falha, depois as saídas'),'pill':'weak'},
   {'t':('One','Uma'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('One terminal transition per run','Uma só transição final por run'),
 'loc':'back/src/jobs/apiV2Job/apiV2Job.processor.ts',
 'purpose':('The processor&#x27;s normal end and <code>failStalledRun</code> both claim the run&#x27;s end through a single compare-and-set.',
            'O fim normal do processor e o <code>failStalledRun</code> reivindicam o fim do run por um único compare-and-set.'),
 'body':('<p>Only the winner writes the final statuses and starts the delivery. The claim can be a status transition such as <code>in_progress → completed</code> or <code>in_progress → error</code>, or a claim row keyed by the job id.</p>',
         '<p>Só o vencedor grava os status finais e inicia a entrega. A reivindicação pode ser uma transição de status como <code>in_progress → completed</code> ou <code>in_progress → error</code>, ou uma linha de claim com a chave do job.</p>'),
 'ba':(('Both ends write a status and start a delivery.','Os dois fins gravam um status e iniciam uma entrega.'),
       ('One end wins; the other writes nothing.','Um fim vence; o outro não grava nada.'))},

{'n':'2','title':('Which outcome wins','Qual resultado vence'),
 'loc':'product decision',
 'purpose':('Decide, with the product owner, what happens when the live run finishes after the stall was reported.',
            'Decidir, com o dono do produto, o que acontece quando o run vivo termina depois de o travamento ser reportado.'),
 'body':('<p>Two options: the first claim wins and the live run&#x27;s result is discarded and logged, or the stall report is held for a short grace period before it claims the end.</p>',
         '<p>Duas opções: a primeira reivindicação vence e o resultado do run vivo é descartado e logado, ou o aviso de travamento espera um curto período de graça antes de reivindicar o fim.</p>')},
]

VERIF = [
 (True, ('Negative control','Controle negativo'),
  ('On the current code, a test that runs <code>failStalledRun</code> and then lets the live job finish shows two deliveries and the status flipping from <code>error</code> to <code>completed</code>. After the change it shows one delivery and one status.',
   'No código atual, um teste que roda o <code>failStalledRun</code> e depois deixa o job vivo terminar mostra duas entregas e o status passando de <code>error</code> para <code>completed</code>. Depois da mudança mostra uma entrega e um status.')),
 (True, ('Both orders','Os dois sentidos'),
  ('The reverse order, live end first and then the stall report, also gives one outcome.',
   'A ordem inversa, fim vivo primeiro e depois o aviso de travamento, também dá um só resultado.')),
 (True, ('Measure before refusing','Medir antes de recusar'),
  ('Count the stalled runs in production since 2026-11-04 and, for each, whether the live run later finished. Classify every refused second outcome as correctly refused or refused although it works.',
   'Contar os runs travados em produção desde 04/11/2026 e, para cada um, se o run vivo terminou depois. Classificar cada segundo resultado recusado como recusado corretamente ou recusado embora funcione.')),
]

DONE = ('A stalled async run produces one status and one delivery, whichever of the two ends comes first.',
        'Um run assíncrono travado produz um status e uma entrega, qualquer dos dois fins que venha primeiro.')

FILES = [('back/src/jobs/apiV2Job/apiV2Job.processor.ts (process, failStalledRun, reportRunFailure, deliverOutputs)', False),
         ('back flow_execution_status service, McpRunStatusService', False),
         ('back output-delivery.service.ts', False)]

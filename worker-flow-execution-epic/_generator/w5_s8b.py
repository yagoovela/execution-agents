# -*- coding: utf-8 -*-
TITLE = ('Finish the schedule rollout and lock the last cron',
         'Terminar o rollout dos agendamentos e travar o último cron')

GOAL = ('With any number of back replicas, every user schedule <b>fires once</b> and every cron runs once per tick.',
        'Com qualquer número de réplicas do back, todo agendamento do usuário <b>dispara uma vez</b> e todo cron roda uma vez por ciclo.')

GLANCE = [
 ('crit', ('Customer impact','Impacto no cliente'), ('A schedule can charge twice','Um agendamento pode cobrar duas vezes'),
  ('While <code>repeatable_schedules</code> is off, each back replica fires every schedule and charges for it.',
   'Enquanto <code>repeatable_schedules</code> está desligada, cada réplica do back dispara todo agendamento e cobra por ele.')),
 ('dep', ('Depends on','Depende de'), ('Nothing','Nada'),
  ('The code shipped with <code>S8</code>. What is left is the rollout, one fallback and one lock.',
   'O código saiu com a <code>S8</code>. Falta o rollout, um fallback e um lock.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('First in the wave, with the other back-replica tasks.',
   'Primeira da onda, junto com as outras tasks de réplica do back.')),
 ('ship', ('Shape','Formato'), ('Back, plus a production flag','Back, mais uma flag em produção'),
  ('Added on 2026-11-04 from the replica audit of that day.',
   'Adicionada em 04/11/2026 a partir da auditoria de réplicas daquele dia.')),
]

LEDE = (
 '<p><code>S8</code> moved user schedules to Bull repeatable jobs and put every cron under an advisory lock. The schedule path ships behind '
 '<code>repeatable_schedules</code>, seeded off. With the flag off, each back replica registers every schedule in its own memory, so '
 '<strong>N replicas fire the flow N times and charge the customer N times</strong>.</p>'
 '<p>Three gaps remain: nothing records the flag being turned on in production, a failed flag read at boot falls back to the duplicating path, '
 'and one cron, <code>negotiatedContractRenewal</code>, has no lock. <code>E4</code> is not needed for this: with the flag on, Bull already fires each schedule once.</p>',
 '<p>A <code>S8</code> levou os agendamentos do usuário para repeatable jobs do Bull e pôs todo cron sob um advisory lock. O caminho dos agendamentos saiu atrás de '
 '<code>repeatable_schedules</code>, criada desligada. Com a flag desligada, cada réplica do back registra todo agendamento na própria memória, então '
 '<strong>N réplicas disparam o fluxo N vezes e cobram o cliente N vezes</strong>.</p>'
 '<p>Faltam três coisas: nada registra a flag sendo ligada em produção, uma falha ao ler a flag no boot volta para o caminho que duplica, '
 'e um cron, o <code>negotiatedContractRenewal</code>, não tem lock. A <code>E4</code> não é necessária para isso: com a flag ligada, o Bull já dispara cada agendamento uma vez.</p>')

TABLE = dict(
 head=[('Piece','Peça'),('Today','Hoje'),('After S8b','Depois da S8b')],
 rows=[
  [('User schedules','Agendamentos do usuário'),
   {'t':('Once per replica while the flag is off','Uma vez por réplica com a flag desligada'),'pill':'weak'},
   {'t':('Flag on in production; once per tick','Flag ligada em produção; uma vez por ciclo'),'pill':'ok'}],
  [('Flag read error at boot','Erro ao ler a flag no boot'),
   {'t':('Falls back to per-replica registration','Volta para o registro por réplica'),'pill':'weak'},
   {'t':('Registers nothing and logs','Não registra nada e loga'),'pill':'ok'}],
  [('<code>negotiatedContractRenewal</code>','<code>negotiatedContractRenewal</code>'),
   {'t':('No lock; runs on every replica','Sem lock; roda em toda réplica'),'pill':'weak'},
   {'t':('Under the cron lock','Sob o lock de cron'),'pill':'ok'}],
  [('The other crons','Os outros crons'),
   {'t':('Under the lock since <code>S8</code>','Sob o lock desde a <code>S8</code>'),'pill':'ok'},
   {'t':('Unchanged','Sem mudança'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('Turn the flag on in production','Ligar a flag em produção'),
 'loc':'feature_flags',
 'purpose':('Read the flag, turn it on in dev, then in production, and restart every back task.',
            'Ler a flag, ligar em dev, depois em produção, e reiniciar todas as tasks do back.'),
 'body':('<p>The flag is read at boot, so a task that booted with it off keeps its in-memory schedules until it restarts. '
         'Confirm afterwards: one <code>api-v2</code> run per schedule tick, and no legacy registration in the boot log.</p>',
         '<p>A flag é lida no boot, então uma task que subiu com ela desligada mantém os agendamentos em memória até reiniciar. '
         'Confirmar depois: um run de <code>api-v2</code> por ciclo de agendamento, e nenhum registro legado no log de boot.</p>')},

{'n':'2','title':('Fail closed','Falhar fechado'),
 'loc':'back/src/app-api/schedule/legacy-schedule-registrar.service.ts',
 'purpose':('When the flag cannot be read at boot, register nothing.','Quando a flag não puder ser lida no boot, não registrar nada.'),
 'body':('<p>A missed fire can be recovered; a double charge cannot. Log the read error so it is visible.</p>',
         '<p>Um disparo perdido pode ser recuperado; uma cobrança dupla não. Logar o erro de leitura para que fique visível.</p>')},

{'n':'3','title':('Lock the last cron','Travar o último cron'),
 'loc':'back/src/app-api/user_product/user_product.controller.ts',
 'purpose':('Run <code>negotiatedContractRenewal</code> inside <code>CronLockService.runExclusively</code>.',
            'Rodar o <code>negotiatedContractRenewal</code> dentro do <code>CronLockService.runExclusively</code>.'),
 'body':('<p><code>S8</code> counted fourteen crons and missed this one: it reads a subscription and then writes <code>usedTokens: 0</code>, so two replicas race at midnight.</p>',
         '<p>A <code>S8</code> contou catorze crons e deixou este de fora: ele lê uma assinatura e depois grava <code>usedTokens: 0</code>, então duas réplicas disputam à meia-noite.</p>')},
]

VERIF = [
 (True, ('Negative control — two replicas','Controle negativo — duas réplicas'),
  ('Two back processes on one database and one Redis. Flag off: a schedule fires twice per tick. Flag on: once.',
   'Dois processos do back num banco e num Redis. Flag desligada: um agendamento dispara duas vezes por ciclo. Flag ligada: uma.')),
 (True, ('Negative control — fail closed and lock','Controle negativo — falhar fechado e lock'),
  ('Make the flag read throw at boot: on <code>main</code> the legacy crons register, after the change none do. Remove the new lock and watch the cron test fail.',
   'Fazer a leitura da flag falhar no boot: no <code>main</code> os crons legados registram, depois da mudança nenhum registra. Tirar o lock novo e ver o teste do cron falhar.')),
]

DONE = ('<code>repeatable_schedules</code> is on in production and every back task restarted after it, a failed flag read registers nothing, '
        '<code>negotiatedContractRenewal</code> runs under the cron lock, and the dates are recorded in the spec.',
        'A <code>repeatable_schedules</code> está ligada em produção e todas as tasks do back reiniciaram depois disso, uma falha ao ler a flag não registra nada, '
        'o <code>negotiatedContractRenewal</code> roda sob o lock de cron, e as datas estão registradas na spec.')

FILES = [('back/src/app-api/schedule/legacy-schedule-registrar.service.ts', False),
         ('back/src/app-api/schedule/schedule-registrar.service.ts', False),
         ('back/src/app-api/schedule/schedule.controller.ts', False),
         ('back/src/app-api/feature-flags/feature-flags.service.ts', False),
         ('back/src/app-api/user_product/user_product.controller.ts', False),
         ('back/src/cronJobs/cron-lock/cron-lock.service.ts', False)]

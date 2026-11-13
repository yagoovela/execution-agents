# -*- coding: utf-8 -*-
TITLE = ('One chain budget across back replicas', 'Um orçamento de cadeia entre as réplicas do back')

GOAL = ('When the execution budget is enforced, a chain of runs <b>stops at its ceiling</b> however many back replicas share the work.',
        'Quando o orçamento de execução está valendo, uma cadeia de runs <b>para no teto</b>, quantas réplicas do back dividirem o trabalho.')

GLANCE = [
 ('crit', ('Conditional','Condicional'), ('Only while <code>execution_budget</code> is on','Só com <code>execution_budget</code> ligada'),
  ('If the flag is off in production, the task is recorded and dropped until it is turned on.',
   'Se a flag estiver desligada em produção, a task é registrada e descartada até ela ser ligada.')),
 ('dep', ('Depends on','Depende de'), ('Nothing','Nada'),
  ('It revisits a decision <code>S4</code> took when production ran one back task.',
   'Revê uma decisão que a <code>S4</code> tomou quando a produção rodava uma task do back.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('With the other back-replica tasks.','Junto com as outras tasks de réplica do back.')),
 ('ship', ('Shape','Formato'), ('Back only','Só o back'),
  ('Added on 2026-11-04 from the replica audit of that day.',
   'Adicionada em 04/11/2026 a partir da auditoria de réplicas daquele dia.')),
]

LEDE = (
 '<p><code>S4</code> left the chain counter in memory because production ran one back task, so the split across processes was latent. '
 'That premise no longer holds: production runs two back tasks every day. A child run that a chain enqueues can land on any replica, '
 'and each replica counts only its own share, so <strong>a chain can pass its ceiling up to N times with N replicas</strong>.</p>'
 '<p>The counting always runs; only the breach check reads <code>execution_budget</code>. So the task matters only while that flag is on.</p>',
 '<p>A <code>S4</code> deixou o contador da cadeia em memória porque a produção rodava uma task do back, então a divisão entre processos era latente. '
 'Essa premissa não vale mais: a produção roda duas tasks do back todo dia. Um run filho que a cadeia enfileira pode cair em qualquer réplica, '
 'e cada réplica conta só a sua parte, então <strong>uma cadeia pode passar do teto até N vezes com N réplicas</strong>.</p>'
 '<p>A contagem roda sempre; só o bloqueio lê a <code>execution_budget</code>. Então a task só importa enquanto essa flag estiver ligada.</p>')

TABLE = dict(
 head=[('Back replicas','Réplicas do back'),('Today, flag on','Hoje, flag ligada'),('After S4b','Depois da S4b')],
 rows=[
  [('One','Uma'),
   {'t':('Stops at the ceiling','Para no teto'),'pill':'ok'},
   {'t':('Stops at the ceiling','Para no teto'),'pill':'ok'}],
  [('Two or three','Duas ou três'),
   {'t':('Each replica counts its share','Cada réplica conta a sua parte'),'pill':'weak'},
   {'t':('One count in Redis; stops at the ceiling','Uma contagem no Redis; para no teto'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('Read the flag first','Ler a flag primeiro'),
 'loc':'feature_flags',
 'purpose':('The user reads <code>execution_budget</code> in production.','O usuário lê a <code>execution_budget</code> em produção.'),
 'body':('<p>Off: record it and set the task to dropped. On: continue.</p>',
         '<p>Desligada: registrar e marcar a task como descartada. Ligada: seguir.</p>')},

{'n':'2','title':('One counter in Redis','Um contador no Redis'),
 'loc':'back/src/app-api/flux/chain-budget.ts',
 'purpose':('An atomic increment per chain root, with an expiry longer than the longest chain and a release that cannot go below zero.',
            'Um incremento atômico por raiz de cadeia, com expiração maior que a cadeia mais longa e uma liberação que não fica negativa.'),
 'body':('<p>A Redis error does not block runs: the check fails open and logs, like the rate limiter.</p>',
         '<p>Um erro do Redis não bloqueia runs: a checagem falha aberta e loga, como o rate limiter.</p>'),
 'ba':(('Each replica keeps its own count.','Cada réplica tem a sua contagem.'),
       ('Every replica adds to one count.','Toda réplica soma numa contagem só.'))},

{'n':'3','title':('Production check, 2026-11-13','Checagem em produção, 13/11/2026'),
 'loc':'CloudWatch Logs',
 'purpose':('Confirm, after the 2026-11-12 deploy, that no chain hit its ceiling and that Redis errors blocked no run.',
            'Confirmar, depois do deploy de 12/11/2026, que nenhuma cadeia bateu no teto e que erros do Redis não bloquearam nenhum run.'),
 'body':('<p>Zero chain ceiling stops, including the window on 2026-11-12 when production ran two back tasks (14:16 to 14:39 UTC). '
         'There were 24 <code>Chain execution count unavailable</code> lines, all <code>Redis command timed out</code> at the daily peak. '
         'Those timeouts predate S4b: the older chain-root lookup times out at the same moments, and the daily total did not rise after the deploy. '
         'Each one failed open as designed: the replica counted its own share, retried the write, and blocked nothing. '
         'Redis itself answers in under 2 ms at <code>p99</code>; the timeouts come from the back, and <code>E5b</code> now adds a Redis latency alarm.</p>',
         '<p>Zero paradas no teto da cadeia, inclusive na janela de 12/11/2026 em que a produção rodou duas tasks do back (14:16 a 14:39 UTC). '
         'Houve 24 linhas <code>Chain execution count unavailable</code>, todas <code>Redis command timed out</code> no pico diário. '
         'Esses timeouts já existiam antes da S4b: a busca mais antiga da raiz da cadeia estoura no mesmo momento, e o total diário não subiu depois do deploy. '
         'Cada um falhou aberto como previsto: a réplica contou a sua parte, tentou a escrita de novo e não bloqueou nada. '
         'O próprio Redis responde em menos de 2 ms no <code>p99</code>; os timeouts vêm do back, e a <code>E5b</code> agora adiciona um alarme de latência do Redis.</p>'),
 'ba':(('Shipped, not yet checked in production.','Em produção, ainda sem checagem.'),
       ('Checked: no chain stopped, no run blocked.','Checado: nenhuma cadeia parou, nenhum run bloqueado.'))},
]

VERIF = [
 (True, ('Negative control — two replicas','Controle negativo — duas réplicas'),
  ('Two back processes and a chain whose children land on both. With a ceiling of N, on <code>main</code> the chain runs more than N executions; after the change it stops at N. Revert and watch the test fail.',
   'Dois processos do back e uma cadeia cujos filhos caem nos dois. Com teto N, no <code>main</code> a cadeia roda mais de N execuções; depois da mudança para em N. Reverter e ver o teste falhar.')),
 (True, ('Measure before refusing','Medir antes de recusar'),
  ('Count the production chains that would have been stopped, and confirm none is a legitimate run.',
   'Contar as cadeias de produção que teriam sido paradas, e confirmar que nenhuma é um run legítimo.')),
]

DONE = ('With the flag on, a chain stops at its ceiling with two and three back replicas, and a Redis error does not block runs. Or, with the flag off, the reading is recorded and the task is dropped.',
        'Com a flag ligada, uma cadeia para no teto com duas e três réplicas do back, e um erro do Redis não bloqueia runs. Ou, com a flag desligada, a leitura fica registrada e a task é descartada.')

FILES = [('back/src/app-api/flux/chain-budget.ts', False),
         ('back/src/app-api/flux/flux.service.ts (open, chargeExecutions, release)', False),
         ('back/src/app-api/rate-limit/rate-limit.storage.ts (the fail-open pattern)', False)]

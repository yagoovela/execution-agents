# -*- coding: utf-8 -*-
TITLE = ('Move user schedules onto Temporal Schedules','Mover os agendamentos do usuário para o Temporal Schedules')

GOAL = ('Give the durable scheduler that <code>S8</code> could not reach <b>ownership of user-scheduled flow runs</b> — with pause, backfill and last-run visibility as first-class operations.',
        'Dar ao scheduler durável que a <code>S8</code> não conseguiu alcançar a <b>posse dos runs de fluxo agendados pelo usuário</b> — com pause, backfill e visibilidade da última execução como operações de primeira classe.')

GLANCE = [
 ('crit', ('Risk','Risco'), ('A double-fired schedule, not a slow one','Um agendamento disparado em dobro, não lento'),
  ('The cutover this task ships has to prove <strong>exactly one run per fire</strong> across replicas and across the migration itself — a schedule firing twice is a duplicate customer-facing run, not a latency blip.',
   'O corte que esta task entrega precisa provar <strong>exatamente um run por disparo</strong> entre réplicas e durante a própria migração — um agendamento disparando duas vezes é um run duplicado visível ao cliente, não uma oscilação de latência.')),
 ('dep', ('Depends on','Depende de'), ('B4 — hard block','B4 — bloqueio rígido'),
  ('A Temporal Schedule can only trigger a <strong>workflow</strong>. The worker exposes none today that executes a whole flow — that workflow is what <code>B4</code> builds. <strong>Blocked until B4 ships.</strong>',
   'Um Temporal Schedule só sabe disparar um <strong>workflow</strong>. O worker não expõe hoje nenhum que execute um fluxo inteiro — esse workflow é o que a <code>B4</code> constrói. <strong>Bloqueada até a B4 entrar.</strong>')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Source: <code>S8</code> Part 2, split out 2026-09-18 when decision <code>D26</code> chose Bull repeatables for now and Temporal Schedules for after <code>B4</code>.',
   'Fonte: <code>S8</code> Parte 2, separada em 18/09/2026 quando a decisão <code>D26</code> escolheu repeatables do Bull para agora e Temporal Schedules para depois da <code>B4</code>.')),
 ('ship', ('Shape','Formato'), ('Per-schedule cutover, reversible','Corte por agendamento, reversível'),
  ('Behind the same feature flag <code>S8</code> introduced, defaulting to the Bull path. Every schedule is either a Bull repeatable or a Temporal Schedule, never both.',
   'Atrás da mesma feature flag que a <code>S8</code> introduziu, com padrão no caminho do Bull. Todo agendamento é um repeatable do Bull ou um Temporal Schedule, nunca os dois.')),
]

LEDE = (
 '<p><code>S8</code> Part 2 recommended Temporal Schedules for user-scheduled flows, and the recommendation was right about the destination and wrong about the timing. Shipping it during <code>S8</code> would have needed two pieces of scaffolding invented purely to give a Temporal Schedule something to call: a <code>runScheduledFlow</code> workflow whose only job is to call back into the backend, and an internal HTTP endpoint for that activity to hit — one that, after <code>S7</code> Part 2, also has to be reasoned about against the rate-limit guards. Both are thrown away the moment <code>B4</code> lands a real flow workflow, so <code>S8</code> shipped the duplication fix on a mechanism that needs no bridge, and the durable scheduler became this task.</p>'
 '<p><code>S8</code> moved user schedules onto <strong>Bull repeatable jobs</strong> (<code>D26</code>): schedule state left the per-replica in-process <code>SchedulerRegistry</code> and moved into Redis, which Bull already manages, and <code>ApiV2Queue</code> — already in production — became the execution owner. Measured, not read from documentation: three simulated replicas registering the same schedule produced <strong>one</strong> repeatable and <strong>one</strong> execution per tick, against <strong>three per tick</strong> for the shape it replaced. That closes duplication and durability across restarts and deploys. It does not give pause/resume as a first-class operation, backfill, last-run visibility as scheduler state, or durability independent of Redis — Bull&#x27;s repeatables live in Redis, and while the <code>schedule</code> table stays the source of truth <code>S8</code> reconciles from on boot, that recovery is code this repo owns rather than a platform guarantee. Those four are what this task buys.</p>',
 '<p>A Parte 2 da <code>S8</code> recomendou Temporal Schedules para fluxos agendados pelo usuário, e a recomendação estava certa sobre o destino e errada sobre o momento. Entregar isso durante a <code>S8</code> precisaria de duas peças de andaime inventadas só para dar a um Temporal Schedule algo para chamar: um workflow <code>runScheduledFlow</code> cujo único trabalho é chamar de volta o backend, e um endpoint HTTP interno para essa activity acessar — que, depois da <code>S7</code> Parte 2, também precisa ser pensado contra os guardas de rate limit. As duas são jogadas fora no instante em que a <code>B4</code> entrega um workflow de fluxo de verdade, então a <code>S8</code> entregou a correção de duplicação num mecanismo que não precisa de ponte, e o scheduler durável virou esta task.</p>'
 '<p>A <code>S8</code> moveu os agendamentos do usuário para <strong>repeatable jobs do Bull</strong> (<code>D26</code>): o estado do agendamento saiu do <code>SchedulerRegistry</code> em processo, por réplica, e foi para o Redis, que o Bull já gerencia, e a <code>ApiV2Queue</code> — já em produção — virou dona da execução. Medido, não lido de documentação: três réplicas simuladas registrando o mesmo agendamento produziram <strong>um</strong> repeatable e <strong>uma</strong> execução por tick, contra <strong>três por tick</strong> na forma que substituiu. Isso fecha a duplicação e a durabilidade entre reinícios e deploys. Não dá pause/resume como operação de primeira classe, backfill, visibilidade da última execução como estado do scheduler, nem durabilidade independente do Redis — os repeatables do Bull moram no Redis, e embora a tabela <code>schedule</code> continue sendo a fonte de verdade que a <code>S8</code> reconcilia no boot, essa recuperação é código deste repositório, não uma garantia de plataforma. Essas quatro coisas são o que esta task compra.</p>')

TABLE = dict(
 head=[('What','O quê'),
       ('Bull repeatables today (S8)','Repeatables do Bull hoje (S8)'),
       ('Temporal Schedules add (E4)','Temporal Schedules acrescentam (E4)'),
       ('Why it matters','Por que importa')],
 rows=[
  [{'t':('Pause / resume','Pause / resume')},
   ('Not a first-class operation — a schedule is deleted and re-created',
    'Não é operação de primeira classe — um agendamento é apagado e recriado'),
   {'t':('A native schedule action','Uma ação nativa do schedule'),'pill':'ok'},
   ('Deleting and re-creating loses the schedule&#x27;s own history and invites the exact race this task exists to close',
    'Apagar e recriar perde o histórico do próprio agendamento e convida exatamente a corrida que esta task existe para fechar')],
  [{'t':('Backfill','Backfill')},
   ('Does not exist — a missed tick while the process was down is simply gone',
    'Não existe — um tick perdido com o processo fora do ar simplesmente some'),
   {'t':('A policy this task has to choose and assert','Uma política que esta task precisa escolher e afirmar'),'pill':'weak'},
   ('Temporal supports it natively; whether the product wants it is the decision below',
    'O Temporal suporta nativamente; se o produto quer isso é a decisão abaixo')],
  [{'t':('Last-run visibility','Visibilidade da última execução')},
   ('A queue artefact — reconstructed from job history, not scheduler state',
    'Um artefato de fila — reconstruído do histórico de jobs, não do estado do scheduler'),
   {'t':('Scheduler state directly','Estado do scheduler diretamente'),'pill':'ok'},
   ('One less place to reconstruct the answer from',
    'Um lugar a menos de onde reconstruir a resposta')],
  [{'t':('Durability','Durabilidade')},
   ('Independent of process restarts, dependent on Redis — the <code>schedule</code> table is the fallback, reconciled on boot',
    'Independente de reinícios de processo, dependente do Redis — a tabela <code>schedule</code> é o fallback, reconciliado no boot'),
   {'t':('Independent of Redis too','Independente também do Redis'),'pill':'ok'},
   ('The property <code>E4</code> adds over <code>S8</code> — demonstrated by killing Redis and confirming schedules still fire',
    'A propriedade que a <code>E4</code> acrescenta sobre a <code>S8</code> — demonstrada matando o Redis e confirmando que os agendamentos continuam disparando')],
 ])

PROSE = (
 'One decision this task has to make and cannot inherit from S8: what a paused or down schedule does when it resumes. Temporal supports backfill natively, which only raises the question the spec states directly — the default is not obviously the one a customer wants, so it has to be asserted, not assumed.',
 'Uma decisão que esta task precisa tomar e não pode herdar da S8: o que um agendamento pausado ou fora do ar faz ao retomar. O Temporal suporta backfill nativamente, o que só levanta a pergunta que a spec declara diretamente — o padrão não é obviamente o que um cliente quer, então precisa ser afirmado, não suposto.')

DEC_BACKFILL = {
 'k':'decision','id':'E4-a','status':'open','open':True,
 'note':(('Where it stands (2026-10-23)','Onde está (23/10/2026)'),
         ('Open: the answer depends on the case, so the policy is set per case. Proposed: a user pause skips every missed fire; a short outage or deploy runs the latest missed fire once; a long outage never replays more than one; high-frequency schedules skip to now; low-frequency ones (daily, weekly) run the latest missed fire once; flows with side effects never get more than one catch-up run; overlap policy SKIP; deleted flows and missing credit are refused and logged. Set <code>catchupWindow</code> on purpose: its default is one year. Full table in the E4 spec. Still to decide with product: the threshold between high and low frequency, and whether the missed-fire log is shown to the user.',
          'Em aberto: a resposta depende do caso, então a política é definida por caso. Proposta: pausa do usuário pula todo disparo perdido; queda curta ou deploy roda o último disparo perdido uma vez; queda longa nunca repete mais de um; agendas de alta frequência pulam para agora; as de baixa frequência (diária, semanal) rodam o último disparo perdido uma vez; fluxos com efeito colateral nunca têm mais de um run de recuperação; política de sobreposição SKIP; fluxo apagado e falta de crédito são recusados e registrados. Definir o <code>catchupWindow</code> de propósito: o padrão é um ano. Tabela completa na spec da E4. Falta decidir com produto: o limite entre alta e baixa frequência, e se o registro de disparos perdidos aparece para o usuário.')),
 'q':('When a paused or down schedule resumes, does it replay the fires it missed, or skip to now?',
      'Quando um agendamento pausado ou fora do ar retoma, ele reproduz os disparos perdidos, ou pula para agora?'),
 'intro':('Temporal Schedules support backfill as a native action, so the mechanism is not the open question — the product behaviour is. A daily report schedule and a five-minute polling schedule want opposite answers, and a default picked silently by whichever behaviour Temporal happens to ship is a default nobody chose on purpose.',
          'Temporal Schedules suportam backfill como ação nativa, então o mecanismo não é a pergunta em aberto — o comportamento de produto é. Um agendamento de relatório diário e um de polling a cada cinco minutos querem respostas opostas, e um padrão escolhido silenciosamente pelo que o Temporal por acaso entrega é um padrão que ninguém escolheu de propósito.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Skip to now, log what was missed','Pular para agora, registrar o que foi perdido'),
   'tag':('recommended','recomendada'),
   'how':('Resume runs the next scheduled fire normally; every missed occurrence is written to the schedule&#x27;s history as <em>missed</em>, visible to the user, and never executed.',
          'Retomar roda o próximo disparo agendado normalmente; toda ocorrência perdida é escrita no histórico do agendamento como <em>perdida</em>, visível ao usuário, e nunca executada.'),
   'pros':[('No surprise burst of spend or side effects the moment a paused or crashed schedule comes back',
            'Sem estouro de gasto ou efeitos colaterais surpresa no instante em que um agendamento pausado ou travado volta'),
           ('Consistent with this epic&#x27;s posture elsewhere — never record a silent zero, never fire a silent surprise (E2&#x27;s ledger rule, S3&#x27;s spend ceiling)',
            'Consistente com a postura deste épico em outros lugares — nunca registrar um zero silencioso, nunca disparar uma surpresa silenciosa (regra do extrato da E2, teto de gasto da S3)'),
           ('Simple to reason about: at most one run per resume, regardless of how long the schedule was down',
            'Simples de raciocinar: no máximo um run por retomada, não importa quanto tempo o agendamento ficou fora')],
   'cons':[('A customer whose schedule genuinely needed every occurrence (e.g. one report per missed day) loses data unless C is also offered',
            'Um cliente cujo agendamento genuinamente precisava de toda ocorrência (ex.: um relatório por dia perdido) perde dado a menos que a C também seja oferecida')],
   'cost':[('lo',('Client effort: <b>none — the missed-run log is passive</b>','Esforço do cliente: <b>nenhum — o log de execuções perdidas é passivo</b>')),
           ('lo',('Ours: <b>the simplest Temporal Schedule policy to configure</b>','Nosso: <b>a política de Temporal Schedule mais simples de configurar</b>'))]},
  {'ltr':'B','name':('Backfill every missed fire','Reproduzir todo disparo perdido'),
   'how':('Resume replays each missed occurrence in order before returning to the normal cadence.',
          'Retomar reproduz cada ocorrência perdida em ordem antes de voltar à cadência normal.'),
   'pros':[('No data is silently skipped — every scheduled occurrence eventually runs',
            'Nenhum dado é pulado silenciosamente — toda ocorrência agendada eventualmente roda')],
   'cons':[('A schedule down for days replays days of runs the instant it comes back — the exact spend/side-effect burst A avoids',
            'Um agendamento fora do ar por dias reproduz dias de runs no instante em que volta — exatamente o estouro de gasto/efeito colateral que a A evita'),
           ('Unbounded by construction: the replay size is however long the outage was, which is not a number anyone chose',
            'Sem limite por construção: o tamanho do replay é o tanto que durou a interrupção, que não é um número que alguém escolheu')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('hi',('Ours: <b>an unbounded replay burst to reason about and rate-limit</b>','Nosso: <b>um estouro de replay sem limite para raciocinar e limitar</b>'))]},
  {'ltr':'C','name':('Configurable per schedule','Configurável por agendamento'),
   'how':('Expose the choice between A and a bounded backfill (capped at N missed fires) as a per-schedule setting.',
          'Expor a escolha entre A e um backfill limitado (capado em N disparos perdidos) como configuração por agendamento.'),
   'pros':[('Covers the daily-report case that A alone loses, without B&#x27;s unbounded replay',
            'Cobre o caso de relatório diário que a A sozinha perde, sem o replay sem limite da B')],
   'cons':[('A second surface to build, document and keep honest, for a need not yet demonstrated by a real customer ask',
            'Uma segunda superfície para construir, documentar e manter honesta, para uma necessidade ainda não demonstrada por um pedido real de cliente')],
   'cost':[('',('Client effort: <b>a setting to understand</b>','Esforço do cliente: <b>uma configuração para entender</b>')),
           ('hi',('Ours: <b>the largest surface of the three</b>','Nosso: <b>a maior superfície das três</b>'))]},
 ],
 'rec':('<p><strong>A, as the default.</strong> A paused or down schedule is either deliberately paused or down because of a deploy or incident — replaying an unbounded backlog of missed fires the instant it resumes is a spend and side-effect surprise, not a service improvement, and it is exactly the shape of silent surprise this epic refuses elsewhere. Log what was missed so the gap is visible rather than swallowed.</p>'
        '<p>C is not rejected, only deferred: if a real schedule genuinely needs every missed occurrence, a bounded per-schedule override is a smaller, later addition on top of A than B would be to retrofit safety onto. Whichever is chosen, <strong>write a test that asserts it</strong> — the spec is explicit that the default is not self-evidently correct, so it must not ship unassessed.</p>',
        '<p><strong>A, como padrão.</strong> Um agendamento pausado ou fora do ar está ou deliberadamente pausado ou fora por causa de um deploy ou incidente — reproduzir um backlog sem limite de disparos perdidos no instante em que retoma é uma surpresa de gasto e efeito colateral, não uma melhoria de serviço, e é exatamente o formato de surpresa silenciosa que este épico recusa em outros lugares. Registrar o que foi perdido torna a lacuna visível em vez de engolida.</p>'
        '<p>A C não é rejeitada, só adiada: se um agendamento real genuinamente precisar de toda ocorrência perdida, uma sobreposição limitada por agendamento é uma adição menor e posterior sobre a A do que seria retrofitar segurança sobre a B. Qualquer que seja a escolha, <strong>escreva um teste que a afirme</strong> — a spec é explícita que o padrão não é evidentemente correto por si só, então não pode subir sem ser avaliado.</p>'),
 'who':[('Engineering, with product sign-off on the default','Engenharia, com aval de produto sobre o padrão')],
}

PARTS = [
 {'n':'1','title':('The schedule&#x27;s id becomes the Temporal schedule id','O id do agendamento vira o id do Temporal Schedule'),
  'loc':'back/src/app-api/schedule/schedule.controller.ts · schedule.service.ts',
  'purpose':('<code>ScheduleController</code>&#x27;s create / update / delete drive <code>ScheduleClient</code> instead of <code>ApiV2Queue</code>&#x27;s repeatable — keyed by the schedule&#x27;s <strong>id</strong>, not its name.',
             'O create / update / delete do <code>ScheduleController</code> passam a acionar o <code>ScheduleClient</code> em vez do repeatable da <code>ApiV2Queue</code> — chaveado pelo <strong>id</strong> do agendamento, não pelo nome.'),
  'body':('<p>The <code>id</code>-not-<code>name</code> rule is not new here — <code>S8</code> already made this change, because a schedule&#x27;s <code>name</code> is user-supplied and not unique. This task inherits it rather than re-deciding it: do not regress it while swapping the mechanism underneath.</p>',
          '<p>A regra <code>id</code>-e-não-<code>name</code> não é nova aqui — a <code>S8</code> já fez essa mudança, porque o <code>name</code> de um agendamento é fornecido pelo usuário e não é único. Esta task a herda em vez de redecidi-la: não regredir isso ao trocar o mecanismo por baixo.</p>'),
  'ba':(('A schedule maps to a Bull repeatable keyed by the schedule&#x27;s id, registered per replica and reconciled from the <code>schedule</code> table on boot.',
         'Um agendamento mapeia para um repeatable do Bull chaveado pelo id do agendamento, registrado por réplica e reconciliado da tabela <code>schedule</code> no boot.'),
        ('A schedule maps to a Temporal Schedule with the same id — durable in Temporal, not reconstructed from a table on every boot.',
         'Um agendamento mapeia para um Temporal Schedule com o mesmo id — durável no Temporal, não reconstruído de uma tabela a cada boot.'))},
 {'n':'2','title':('The schedule action targets B4&#x27;s flow workflow directly','A ação do agendamento aciona diretamente o workflow de fluxo da B4'),
  'loc':('the flow workflow B4 introduces','o workflow de fluxo que a B4 introduz'),
  'purpose':('No bridge workflow. If a Temporal Schedule here still needs an intermediate to call, <code>B4</code> is not done and this task is not ready.',
             'Sem workflow-ponte. Se um Temporal Schedule aqui ainda precisar de um intermediário para chamar, a <code>B4</code> não está pronta e esta task não está pronta.'),
  'body':('<p>This is the fact that made the task wait for <code>B4</code> in the first place, restated as the acceptance bar for this part: a Temporal Schedule can only trigger a workflow, and the only workflow worth triggering is the one that runs a whole flow. Anything short of that is the throwaway bridge <code>S8</code> deliberately declined to build.</p>',
          '<p>Este é o fato que fez a task esperar a <code>B4</code> em primeiro lugar, reafirmado como o critério de aceite desta parte: um Temporal Schedule só sabe disparar um workflow, e o único workflow que vale a pena disparar é o que roda um fluxo inteiro. Qualquer coisa menor que isso é a ponte descartável que a <code>S8</code> deliberadamente recusou construir.</p>'),
  'callouts':[('mig',('The fourteen framework crons are out','Os catorze crons de framework ficam fora'),
    ('<p>They stay on <code>S8</code>&#x27;s advisory lock — internal maintenance with no reason to become workflows. Settled in <code>D12</code> and not reopened here.</p>',
     '<p>Continuam no advisory lock da <code>S8</code> — manutenção interna sem motivo para virar workflow. Resolvido na <code>D12</code> e não reaberto aqui.</p>'))]},
 {'n':'3','title':('The cutover is per-schedule, reversible, and cannot double-fire','O corte é por agendamento, reversível, e não pode disparar em dobro'),
  'loc':('the feature flag S8 introduced','a feature flag que a S8 introduziu'),
  'purpose':('Behind the same flag, defaulting to Bull. Every schedule is a Bull repeatable or a Temporal Schedule, never both at once.',
             'Atrás da mesma flag, com padrão no Bull. Todo agendamento é um repeatable do Bull ou um Temporal Schedule, nunca os dois ao mesmo tempo.'),
  'body':('<p>The risky moment is the transition, not the steady state on either side of it — which is why the negative control below flips the flag with two replicas running and counts fires, rather than trusting that one mechanism is off because the other is on.</p>',
          '<p>O momento arriscado é a transição, não o estado estável de nenhum dos dois lados dela — por isso o controle negativo abaixo vira a flag com duas réplicas rodando e conta disparos, em vez de confiar que um mecanismo está desligado porque o outro está ligado.</p>')},
 {'n':'4','title':('The zombie check becomes a schedule policy','A checagem de zumbi vira política do schedule'),
  'loc':'schedule.service.ts',
  'purpose':('Stop, delete, soft-delete when the flow behind a schedule is gone — the check S8 preserved has to survive the move as a schedule policy, not a callback body.',
             'Parar, apagar, soft-delete quando o fluxo por trás de um agendamento some — a checagem que a S8 preservou precisa sobreviver à mudança como política do schedule, não como corpo de callback.'),
  'body':('<p>On Bull, this check runs inside the job&#x27;s callback body. On a Temporal Schedule it has nowhere equivalent to live unless it is written as an explicit policy the schedule action consults — the difference is structural, not cosmetic, and it is why this gets its own part rather than a line inside Part 1.</p>',
          '<p>No Bull, essa checagem roda dentro do corpo de callback do job. Num Temporal Schedule ela não tem lugar equivalente para morar a menos que seja escrita como uma política explícita que a ação do schedule consulta — a diferença é estrutural, não cosmética, e é por isso que isto ganha parte própria em vez de uma linha dentro da Parte 1.</p>')},
]

VERIF = [
 (True,('Negative control','Controle negativo'),
  ('With the flag on for one schedule and <strong>two backend replicas</strong>, confirm exactly one run per fire — and confirm it was <strong>Temporal</strong> that fired it, not a surviving Bull repeatable. A green count proves nothing if both mechanisms are live and one of them is idle.',
   'Com a flag ligada para um agendamento e <strong>duas réplicas do backend</strong>, confirme exatamente um run por disparo — e confirme que foi o <strong>Temporal</strong> que disparou, não um repeatable do Bull sobrevivente. Uma contagem verde não prova nada se os dois mecanismos estão vivos e um deles está ocioso.')),
 (False,('The rollback is clean','O rollback é limpo'),
  ('Flip the flag back and confirm the Bull repeatable resumes, with <strong>no fire lost and none doubled</strong> across the transition. The cutover is the risky part, not the steady state.',
   'Vire a flag de volta e confirme que o repeatable do Bull retoma, <strong>sem disparo perdido e nenhum dobrado</strong> durante a transição. O corte é a parte arriscada, não o estado estável.')),
 (False,('Pause, wait, resume','Pausar, esperar, retomar'),
  ('Pause a schedule, wait past a fire, resume, and confirm the <strong>chosen</strong> backfill behaviour — whichever option was picked in the decision above, assert it, because the default is not obviously the one a customer wants.',
   'Pause um agendamento, espere passar um disparo, retome, e confirme o comportamento de backfill <strong>escolhido</strong> — qualquer que seja a opção escolhida na decisão acima, afirme-a, porque o padrão não é obviamente o que um cliente quer.')),
 (False,('Kill Redis, confirm schedules still fire','Matar o Redis, confirmar que os agendamentos continuam disparando'),
  ('That is the property this task adds over <code>S8</code>, so it is the one that has to be demonstrated rather than assumed.',
   'Essa é a propriedade que esta task acrescenta sobre a <code>S8</code>, então é a que precisa ser demonstrada, não suposta.')),
]

DONE = ('User schedules are Temporal Schedules, fire <strong>exactly once</strong> regardless of replica count, <strong>survive the loss of Redis</strong>, and expose pause, resume and last-run state. The Bull repeatable path is <strong>deleted, not merely disabled</strong>.',
        'Os agendamentos do usuário são Temporal Schedules, disparam <strong>exatamente uma vez</strong> independente da contagem de réplicas, <strong>sobrevivem à perda do Redis</strong>, e expõem pause, resume e estado da última execução. O caminho do repeatable do Bull é <strong>apagado, não apenas desligado</strong>.')

FILES = [('back/src/app-api/schedule/schedule.controller.ts',False),
         ('back/src/app-api/schedule/schedule.service.ts',False),
         ('back/src/temporal/temporal.service.ts (a ScheduleClient beside the existing WorkflowClient)',False),
         ('the flow workflow B4 introduces',True),
         ('back/src/jobs/apiV2Job/ (the repeatable registration S8 adds, deleted here)',False)]

# -*- coding: utf-8 -*-
TITLE = ('One fire per schedule, one run per cron', 'Um disparo por agendamento, um run por cron')

GOAL = ('Running a second backend replica stops <b>multiplying scheduled work</b> — crons, user schedules and the email poll alike.',
        'Rodar uma segunda réplica de backend para de <b>multiplicar trabalho agendado</b> — crons, agendamentos de usuário e o poll de e-mail, todos.')

GLANCE = [
 ('crit', ('Severity', 'Severidade'), ('High', 'Alta'),
  ('Thirteen crons with no leader election, and schedules held in an in-process registry. Review §9.3, §9.4, §9.5.',
   'Treze crons sem eleição de líder, e agendamentos guardados num registro em processo. Review §9.3, §9.4, §9.5.')),
 ('dep', ('Depends on', 'Depende de'), ('Nothing', 'Nada'),
  ('But it <strong>blocks running more than one backend replica</strong> — and it blocks B5.',
   'Mas <strong>bloqueia rodar mais de uma réplica de backend</strong> — e bloqueia a B5.')),
 ('wave', ('Wave', 'Onda'), ('Wave 1', 'Onda 1'),
  ('Same wave as S2 for the same reason: it is one of the things standing between here and a second replica.',
   'Mesma onda da S2 pelo mesmo motivo: é uma das coisas entre aqui e uma segunda réplica.')),
 ('ship', ('Blast radius today', 'Raio de impacto hoje'), ('Every schedule, per replica', 'Todo agendamento, por réplica'),
  ('N replicas means N runs of the same schedule, <strong>each charged to the customer</strong>.',
   'N réplicas significam N runs do mesmo agendamento, <strong>cada um cobrado do cliente</strong>.')),
]

LEDE = (
 """<p><code>@Cron</code> is registered <strong>thirteen times</strong> across <code>back/src</code> (a fourteenth site, in <code>updateTechnologiesFromSheets.service.ts</code>, is commented out — corrected 2026-09-02), and there is no leader election: greps for <code>leader</code>, <code>isLeader</code>, <code>CRON_ENABLED</code> or an advisory-lock guard return nothing. <strong>Every cron fires on every replica.</strong></p>
<p>User schedules are worse, because they cost money. They are registered in NestJS&#x27;s in-process registry — <code>schedulerRegistry.addCronJob</code> at two sites in <code>schedule.controller.ts</code> (<code>create()</code>, <code>getAllSchedules()</code>) — so each replica holds its own copy and fires it independently. <strong>N replicas means N runs of the same schedule, each charged to the customer.</strong></p>""",
 """<p>O <code>@Cron</code> está registrado <strong>treze vezes</strong> em <code>back/src</code> (um décimo quarto ponto, em <code>updateTechnologiesFromSheets.service.ts</code>, está comentado — corrigido em 2026-09-02), e não há eleição de líder: buscas por <code>leader</code>, <code>isLeader</code>, <code>CRON_ENABLED</code> ou uma guarda de advisory lock não retornam nada. <strong>Todo cron dispara em toda réplica.</strong></p>
<p>Os agendamentos de usuário são piores, porque custam dinheiro. Eles são registrados no registro em processo do NestJS — <code>schedulerRegistry.addCronJob</code> em dois pontos de <code>schedule.controller.ts</code> (<code>create()</code>, <code>getAllSchedules()</code>) — então cada réplica guarda sua própria cópia e dispara sozinha. <strong>N réplicas significam N runs do mesmo agendamento, cada um cobrado do cliente.</strong></p>""")

TABLE = {
 'k': 'table',
 'head': [('What multiplies', 'O que multiplica'), ('Where', 'Onde'),
          ('Per replica today', 'Por réplica hoje'), ('What it costs', 'O que custa')],
 'rows': [
  [{'t': ('Thirteen <code>@Cron</code> sites', 'Treze pontos com <code>@Cron</code>')},
   ('<code>back/src/cronJobs/**</code>', '<code>back/src/cronJobs/**</code>'),
   {'t': ('fires everywhere', 'dispara em todas'), 'pill': 'no'},
   ('Five purges at <code>EVERY_DAY_AT_3AM</code> hitting the same tables in the same minute',
    'Cinco purges em <code>EVERY_DAY_AT_3AM</code> batendo nas mesmas tabelas no mesmo minuto')],
  [{'t': ('User schedules', 'Agendamentos de usuário')},
   ('<code>schedule.controller.ts</code> · <code>create()</code>, <code>getAllSchedules()</code>', '<code>schedule.controller.ts</code> · <code>create()</code>, <code>getAllSchedules()</code>'),
   {'t': ('one copy per replica', 'uma cópia por réplica'), 'pill': 'no'},
   ('<strong>N runs of the same schedule, each charged to the customer</strong>',
    '<strong>N runs do mesmo agendamento, cada um cobrado do cliente</strong>')],
  [{'t': ('The POP3 poll', 'O poll POP3')},
   ('<code>mail.service.ts</code>', '<code>mail.service.ts</code>'),
   {'t': ('every ten seconds', 'a cada dez segundos'), 'pill': 'no'},
   ('8,640 connections a day at one replica, with no message-id dedup and no lock',
    '8.640 conexões por dia com uma réplica, sem dedup por id de mensagem e sem lock')],
  [{'t': ('<code>markStuckSpaceRunLogs</code>', '<code>markStuckSpaceRunLogs</code>')},
   ('One of the thirteen', 'Um dos treze'),
   {'t': ('every ten minutes', 'a cada dez minutos'), 'pill': 'weak'},
   ('Waste rather than corruption — but it is the same missing mechanism',
    'Desperdício, não corrupção — mas é o mesmo mecanismo faltando')],
  [{'t': ('Redis dedup keys', 'Chaves de dedup no Redis')},
   ('<code>flux.service.ts</code>', '<code>flux.service.ts</code>'),
   {'t': ('correct pattern', 'padrão correto'), 'pill': 'ok'},
   ('<code>SET key &#x27;1&#x27; EX 86400 NX</code>, run-scoped — correctness state, and evictable under a cache policy',
    '<code>SET key &#x27;1&#x27; EX 86400 NX</code>, com escopo de run — estado de correção, e descartável sob uma política de cache')],
 ]}

DEC_CRON = {
 'k': 'decision', 'id': 'S8-a', 'plan': 'D12', 'status': 'rec', 'open': True,
 'q': ('What makes a cron fire once, when thirteen of them fire on every replica?',
       'O que faz um cron disparar uma vez, quando treze deles disparam em toda réplica?'),
 'intro': (
  'Greps for <code>leader</code>, <code>isLeader</code>, <code>CRON_ENABLED</code> and an advisory-lock guard return nothing, so today the answer is “nothing”. '
  'The requirement is <strong>one mechanism for all thirteen, not thirteen guards</strong> — and the property worth optimising for is that '
  '<strong>nothing has to know how many replicas exist</strong>, because that is the number a deploy is allowed to change without telling anyone.',
  'Buscas por <code>leader</code>, <code>isLeader</code>, <code>CRON_ENABLED</code> e uma guarda de advisory lock não retornam nada, então hoje a resposta é “nada”. '
  'O requisito é <strong>um mecanismo para os treze, não treze guardas</strong> — e a propriedade a otimizar é que '
  '<strong>nada precise saber quantas réplicas existem</strong>, porque esse é o número que um deploy pode mudar sem avisar ninguém.'),
 'opts': [
  {'ltr': 'A', 'pick': True, 'name': ('An advisory lock per job name', 'Um advisory lock por nome de job'),
   'tag': ('recommended', 'recomendada'),
   'how': ('Each job takes a lock named after itself at the top of its run and releases it at the end. A replica that cannot take the lock simply skips.',
           'Cada job toma um lock com o próprio nome no início do run e o libera no fim. A réplica que não consegue o lock simplesmente pula.'),
   'pros': [('<strong>Nothing has to know the replica count</strong> — the mechanism is correct at one replica and at ten',
             '<strong>Nada precisa saber a contagem de réplicas</strong> — o mecanismo é correto com uma réplica e com dez'),
            ('<code>pg_advisory_xact_lock</code> is already used in the codebase (<code>oauth-token.repo.ts</code>), so there is no new dependency',
             'O <code>pg_advisory_xact_lock</code> já é usado no código (<code>oauth-token.repo.ts</code>), então não há dependência nova'),
            ('It degrades correctly: the loser skips, and can say in a log line that it skipped',
             'Degrada corretamente: quem perde pula, e pode dizer numa linha de log que pulou'),
            ('One mechanism covers all thirteen, including the POP3 poll in Part 4',
             'Um mecanismo cobre os treze, incluindo o poll POP3 da Parte 4')],
   'cons': [('It puts a lock acquisition on the database this epic is already worried about — thirteen jobs, one of them every ten seconds',
             'Coloca uma aquisição de lock no banco com que este épico já se preocupa — treze jobs, um deles a cada dez segundos'),
            ('A transaction-scoped lock means the job runs inside the transaction that holds it, which is a real constraint for a long purge',
             'Um lock com escopo de transação faz o job rodar dentro da transação que o segura, o que é uma restrição real para um purge longo')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('lo', ('Ours: <b>one guard, no new dependency</b>', 'Nosso: <b>uma guarda, nenhuma dependência nova</b>'))]},
  {'ltr': 'B', 'name': ('A dedicated scheduler replica', 'Uma réplica dedicada a scheduler'),
   'how': ('One replica has cron enabled by environment; the others do not run crons at all.',
           'Uma réplica tem cron ligado por ambiente; as outras não rodam cron nenhum.'),
   'pros': [('The simplest thing that works, and trivially explainable',
             'A coisa mais simples que funciona, e trivial de explicar'),
            ('No per-tick database work at all', 'Nenhum trabalho de banco por tick')],
   'cons': [('<strong>It makes that replica special</strong>, and a deploy that loses it loses every cron <em>silently</em>',
             '<strong>Torna aquela réplica especial</strong>, e um deploy que a perde perde todo cron <em>em silêncio</em>'),
            ('Scaling and rescheduling now have to preserve an invariant the platform does not know about',
             'Escalar e reagendar passam a ter de preservar um invariante que a plataforma desconhece'),
            ('Nothing detects the failure — the symptom is maintenance work that quietly stops happening',
             'Nada detecta a falha — o sintoma é trabalho de manutenção que simplesmente para de acontecer')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>a silent single point of failure</b>', 'Nosso: <b>um ponto único de falha silencioso</b>'))]},
  {'ltr': 'C', 'name': ('Leader election', 'Eleição de líder'),
   'how': ('The replicas elect a leader and the leader runs the crons — the shape the review named first.',
           'As réplicas elegem um líder e o líder roda os crons — o formato que a review nomeou primeiro.'),
   'pros': [('It survives losing the leader, unlike a designated replica',
             'Sobrevive à perda do líder, ao contrário de uma réplica designada'),
            ('A standard, well-understood pattern', 'Um padrão conhecido e bem compreendido')],
   'cons': [('It is a distributed-systems component to run and reason about, for thirteen maintenance jobs',
             'É um componente de sistemas distribuídos para rodar e raciocinar, por causa de treze jobs de manutenção'),
            ('An advisory lock <strong>is</strong> leader election, scoped to one job and expiring by itself — with none of the machinery',
             'Um advisory lock <strong>é</strong> eleição de líder, com escopo de um job e expirando sozinho — sem nada dessa maquinaria')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>machinery out of proportion to the problem</b>', 'Nosso: <b>maquinaria desproporcional ao problema</b>'))]},
  {'ltr': 'D', 'name': ('Temporal Schedules for all thirteen', 'Temporal Schedules para os treze'),
   'tag': ('right for Part 2', 'certa para a Parte 2'),
   'how': ('Move every cron onto the platform&#x27;s native scheduling — the same mechanism Part 2 adopts for user schedules.',
           'Mover todo cron para o agendamento nativo da plataforma — o mesmo mecanismo que a Parte 2 adota para agendamentos de usuário.'),
   'pros': [('One fire per schedule by construction, with pause, backfill and last-run visibility',
             'Um disparo por agendamento por construção, com pausa, backfill e visibilidade da última execução'),
            ('It <em>is</em> the right answer for the user-facing schedules, and Part 2 uses it',
             'É <em>de fato</em> a resposta certa para os agendamentos visíveis ao cliente, e a Parte 2 a usa')],
   'cons': [('<strong>These thirteen are internal maintenance and have no reason to become workflows</strong>',
             '<strong>Estes treze são manutenção interna e não têm motivo para virar workflows</strong>'),
            ('Each cron would have to be reachable as a workflow or an activity — a large restructuring for a set of purges',
             'Cada cron teria de ser alcançável como workflow ou activity — uma reestruturação grande para um conjunto de purges')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>thirteen jobs restructured for no user-facing gain</b>', 'Nosso: <b>treze jobs reestruturados sem ganho para o cliente</b>'))]},
 ],
 'rec': (
  '<p><strong>A for the thirteen framework crons, D for the user-facing schedules in Part 2.</strong> That split is the review&#x27;s amendment (§11.3), and it is deliberate: the crons are internal maintenance and Temporal Schedules buy them nothing they need, while the user schedules are customer-visible, durable, and want pause, backfill and last-run visibility an in-process registry cannot offer.</p>'
  '<p>Whichever wins, <strong>the replica that skips must log that it skipped</strong>. A guard that silently does nothing is indistinguishable from a cron that stopped working, and the second one is discovered months later.</p>'
  '<p>And <strong>stagger the 3AM cluster while you are there</strong> — five purges starting in the same minute is a self-inflicted load spike on the database <code>S2</code> is already sizing.</p>',
  '<p><strong>A para os treze crons de framework, D para os agendamentos de usuário da Parte 2.</strong> Essa divisão é a emenda da review (§11.3), e é deliberada: os crons são manutenção interna e os Temporal Schedules não lhes dão nada de que precisem, enquanto os agendamentos de usuário são visíveis ao cliente, duráveis, e querem pausa, backfill e visibilidade da última execução que um registro em processo não oferece.</p>'
  '<p>Seja qual for a escolha, <strong>a réplica que pula precisa logar que pulou</strong>. Uma guarda que silenciosamente não faz nada é indistinguível de um cron que parou de funcionar, e o segundo caso é descoberto meses depois.</p>'
  '<p>E <strong>escalone o bloco das 3h enquanto estiver lá</strong> — cinco purges começando no mesmo minuto é um pico de carga autoinfligido no banco que a <code>S2</code> já está dimensionando.</p>'),
 'who': [('Engineering', 'Engenharia'),
         ('Infra confirms the lock is acceptable on the database', 'Infra confirma que o lock é aceitável no banco')],
}

DEC_REDIS = {
 'k': 'decision', 'id': 'S8-b', 'status': 'open',
 'q': ('How are the dedup keys protected from eviction — by a policy, or by a separate instance?',
       'Como as chaves de dedup são protegidas de despejo — por uma política, ou por uma instância separada?'),
 'intro': (
  'Redis backs three unrelated things: the Bull queues, the worker→backend pub/sub, and the delivery dedup keys. '
  'The dedup pattern itself is correct — <code>SET key &#x27;1&#x27; EX 86400 NX</code>, run-scoped (<code>flux.service.ts</code>) — and it is what stops a retried run from emailing a customer twice. '
  '<strong>Dedup keys are correctness state, not cache</strong>, and under <code>allkeys-lru</code> or <code>allkeys-random</code> they are evictable. '
  'This cannot be read from the repository; it has to be confirmed from infrastructure.',
  'O Redis sustenta três coisas sem relação entre si: as filas do Bull, o pub/sub worker→backend, e as chaves de dedup de entrega. '
  'O padrão de dedup em si está correto — <code>SET key &#x27;1&#x27; EX 86400 NX</code>, com escopo de run (<code>flux.service.ts</code>) — e é o que impede um run com retry de mandar e-mail duas vezes para o cliente. '
  '<strong>Chaves de dedup são estado de correção, não cache</strong>, e sob <code>allkeys-lru</code> ou <code>allkeys-random</code> elas são despejáveis. '
  'Isso não dá para ler do repositório; tem de ser confirmado com a infraestrutura.'),
 'opts': [
  {'ltr': 'A', 'pick': True, 'name': ('Separate the correctness state from the cache', 'Separar o estado de correção do cache'),
   'tag': ('recommended', 'recomendada'),
   'how': ('Dedup keys move to their own instance, with a policy that cannot evict them. The queues and the bus keep theirs.',
           'As chaves de dedup vão para uma instância própria, com uma política que não pode despejá-las. As filas e o barramento ficam na delas.'),
   'pros': [('<strong>The only shape in which a cache filling up cannot cause a duplicate customer email</strong>',
             '<strong>O único formato em que um cache enchendo não pode causar um e-mail duplicado ao cliente</strong>'),
            ('It also splits the availability story the review flags — losing one instance stops costing admission, visibility and duplicate suppression at once',
             'Também separa a história de disponibilidade que a review aponta — perder uma instância deixa de custar admissão, visibilidade e supressão de duplicatas de uma vez'),
            ('Sizing for post-<code>B5</code> pub/sub becomes a separate number from sizing for dedup',
             'Dimensionar o pub/sub pós-<code>B5</code> vira um número separado de dimensionar o dedup')],
   'cons': [('Another instance to run, connect to and monitor', 'Mais uma instância para rodar, conectar e monitorar'),
            ('A second connection string in every service that dedups', 'Uma segunda string de conexão em todo serviço que faz dedup')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('', ('Ours: <b>one more instance to run</b>', 'Nosso: <b>mais uma instância para rodar</b>'))]},
  {'ltr': 'B', 'name': ('One instance, with a policy that cannot evict them', 'Uma instância, com uma política que não pode despejá-las'),
   'how': ('Keep everything on one instance and set an eviction policy that refuses to discard the dedup keys.',
           'Manter tudo numa instância e definir uma política de despejo que se recuse a descartar as chaves de dedup.'),
   'pros': [('No new infrastructure, and one thing to monitor', 'Nenhuma infraestrutura nova, e uma coisa só para monitorar'),
            ('The fastest to apply — it is a configuration change', 'A mais rápida de aplicar — é uma mudança de configuração')],
   'cons': [('<strong>The dedup keys carry a TTL (<code>EX 86400</code>), so every <code>volatile-*</code> policy can evict them too</strong> — the only single-instance policy that protects them is <code>noeviction</code>',
             '<strong>As chaves de dedup têm TTL (<code>EX 86400</code>), então toda política <code>volatile-*</code> também pode despejá-las</strong> — a única política de instância única que as protege é <code>noeviction</code>'),
            ('Under <code>noeviction</code> a full instance starts refusing writes, which takes the queues and the bus down with it — the failure moves rather than disappearing',
             'Sob <code>noeviction</code> uma instância cheia passa a recusar escritas, e leva junto as filas e o barramento — a falha se desloca em vez de sumir')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>one full instance stops everything</b>', 'Nosso: <b>uma instância cheia para tudo</b>'))]},
  {'ltr': 'C', 'name': ('Move the dedup into Postgres', 'Mover o dedup para o Postgres'),
   'how': ('Keep the dedup key as a uniquely-constrained row instead of a Redis key, so it cannot be evicted at all.',
           'Guardar a chave de dedup como uma linha com restrição de unicidade em vez de chave no Redis, de modo que não possa ser despejada.'),
   'pros': [('Eviction stops being a question — the guarantee comes from a constraint',
             'Despejo deixa de ser uma pergunta — a garantia vem de uma restrição'),
            ('It is durable across a Redis restart, which a key with a 24-hour TTL is not',
             'É durável a um restart do Redis, o que uma chave com TTL de 24 horas não é')],
   'cons': [('It adds a write and a lookup per delivery to the database <code>S2</code> is sizing, in the path <code>B5</code> is about to multiply',
             'Adiciona uma escrita e uma leitura por entrega no banco que a <code>S2</code> está dimensionando, no caminho que a <code>B5</code> vai multiplicar'),
            ('The existing pattern is correct and already in production — replacing a working guard is a larger change than protecting it',
             'O padrão existente está correto e já em produção — trocar uma guarda que funciona é uma mudança maior do que protegê-la')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>more load on the wall S2 is measuring</b>', 'Nosso: <b>mais carga no teto que a S2 está medindo</b>'))]},
 ],
 'rec': (
  '<p><strong>A, and the sizing question travels with it.</strong> Parallel dispatch raises the pub/sub rate substantially, so today&#x27;s headroom is not evidence for post-<code>B5</code>. Splitting the instances is what lets those two numbers be set independently instead of as one compromise.</p>'
  '<p><code>E3</code> lands in the same wave and adds socket fan-out to the same bus — <strong>the two tasks have to produce one Redis sizing number together, not two.</strong></p>'
  '<p>Whichever is chosen, prove it: fill the instance past <code>maxmemory</code> and confirm a dedup key survives. <strong>An assumption about eviction is worth exactly as much as the test that proves it.</strong></p>',
  '<p><strong>A, e a questão do dimensionamento vai junto.</strong> O dispatch paralelo aumenta bastante a taxa de pub/sub, então a folga de hoje não é evidência para o pós-<code>B5</code>. Separar as instâncias é o que permite definir esses dois números de forma independente em vez de como um único meio-termo.</p>'
  '<p>A <code>E3</code> entra na mesma onda e soma o fan-out de socket ao mesmo barramento — <strong>as duas tasks têm de produzir um número único de dimensionamento do Redis, não dois.</strong></p>'
  '<p>Seja qual for a escolha, prove: encha a instância além do <code>maxmemory</code> e confirme que uma chave de dedup sobrevive. <strong>Uma suposição sobre despejo vale exatamente o que vale o teste que a prova.</strong></p>'),
 'who': [('Infra owns the policy', 'Infra decide a política'),
         ('Engineering confirms the key layout', 'Engenharia confirma o layout das chaves')],
}

PARTS = [
{'n': '1',
 'title': ('The thirteen crons', 'Os treze crons'),
 'loc': 'back/src/cronJobs/** · oauth-token.repo.ts',
 'purpose': ('One mechanism for all thirteen, so a second replica stops multiplying maintenance work.',
             'Um mecanismo para os treze, para que uma segunda réplica pare de multiplicar trabalho de manutenção.'),
 'body': (
  '<p><code>@Cron</code> is registered thirteen times across <code>back/src</code>, and there is no leader election. Every cron fires on every replica.</p>'
  '<p>Some of that is waste: five separate purges all at <code>EVERY_DAY_AT_3AM</code>, each running per replica, against the same tables in the same minute. <strong>Some of it is not:</strong> <code>mail.service.ts</code> polls POP3 <code>EVERY_10_SECONDS</code> per replica, and <code>markStuckSpaceRunLogs</code> runs every ten minutes per replica.</p>',
  '<p>O <code>@Cron</code> está registrado treze vezes em <code>back/src</code>, e não há eleição de líder. Todo cron dispara em toda réplica.</p>'
  '<p>Parte disso é desperdício: cinco purges separados, todos em <code>EVERY_DAY_AT_3AM</code>, cada um rodando por réplica, contra as mesmas tabelas no mesmo minuto. <strong>Parte não é:</strong> o <code>mail.service.ts</code> faz poll POP3 <code>EVERY_10_SECONDS</code> por réplica, e o <code>markStuckSpaceRunLogs</code> roda a cada dez minutos por réplica.</p>'),
 'body2': (
  '<p><strong>Stagger the 3AM cluster while you are there.</strong> Five purges starting in the same minute is a self-inflicted load spike on the database this epic is already worried about.</p>',
  '<p><strong>Escalone o bloco das 3h enquanto estiver lá.</strong> Cinco purges começando no mesmo minuto é um pico de carga autoinfligido no banco com que este épico já se preocupa.</p>'),
 'ba': (('Every cron fires on every replica, so maintenance work is multiplied by the replica count — and the POP3 poll is multiplied every ten seconds.',
         'Todo cron dispara em toda réplica, então o trabalho de manutenção é multiplicado pela contagem de réplicas — e o poll POP3 é multiplicado a cada dez segundos.'),
        ('One guard, taken per job name, so each cron runs once per tick regardless of how many replicas exist — and the replica that skipped <strong>says</strong> it skipped.',
         'Uma guarda, tomada por nome de job, para que cada cron rode uma vez por tick independentemente de quantas réplicas existam — e a réplica que pulou <strong>diz</strong> que pulou.'))},
{'n': '2',
 'title': ('User-scheduled flows', 'Fluxos agendados pelo usuário'),
 'loc': 'schedule.controller.ts',
 'purpose': ('Make a schedule fire once, and make the queue actually own the execution it appears to own.',
             'Fazer um agendamento disparar uma vez, e fazer a fila de fato ser dona da execução que ela aparenta ser.'),
 'body': (
  '<p>Scheduled runs do not use a durable scheduler. They are registered in NestJS&#x27;s in-process registry — <code>schedulerRegistry.addCronJob</code> in <code>create()</code> and <code>getAllSchedules()</code> — so each replica holds its own copy and fires it independently. <strong>N replicas means N runs of the same schedule, each charged to the customer.</strong></p>'
  '<p>Two defects live in the same code, and both are fixed here:</p>',
  '<p>Runs agendados não usam um scheduler durável. Eles são registrados no registro em processo do NestJS — <code>schedulerRegistry.addCronJob</code> em <code>create()</code> e <code>getAllSchedules()</code> — então cada réplica guarda a própria cópia e dispara sozinha. <strong>N réplicas significam N runs do mesmo agendamento, cada um cobrado do cliente.</strong></p>'
  '<p>Dois defeitos vivem no mesmo código, e os dois são corrigidos aqui:</p>'),
 'list': [
  ('<strong>The re-registration hides in a getter.</strong> <code>getAllSchedules()</code> is a plain method with no route decorator that walks every active schedule and registers crons <em>as a side effect</em>. Whatever calls it registers crons on that replica.',
   '<strong>O re-registro se esconde num getter.</strong> O <code>getAllSchedules()</code> é um método comum, sem decorator de rota, que percorre todos os agendamentos ativos e registra crons <em>como efeito colateral</em>. Quem quer que o chame registra crons naquela réplica.'),
  ('<strong>The queue is not doing the work.</strong> The callback does <code>await this.scheduleQueue.add(&#x27;schedule-job&#x27;, { … job: await this.fluxService.apiV2({ … }) })</code> — the run is <strong>awaited as an argument to the enqueue call</strong>, so the flow already executed synchronously inside the cron callback and only its <em>result</em> reaches the queue.',
   '<strong>A fila não está fazendo o trabalho.</strong> O callback faz <code>await this.scheduleQueue.add(&#x27;schedule-job&#x27;, { … job: await this.fluxService.apiV2({ … }) })</code> — o run é <strong>aguardado como argumento da chamada de enfileiramento</strong>, então o fluxo já executou de forma síncrona dentro do callback do cron e só o <em>resultado</em> dele chega na fila.'),
 ],
 'body2': (
  '<p>Fixing the duplication without fixing the second one just duplicates it more efficiently. Either way, the callback <strong>stops awaiting the run</strong> — the scheduler owns the trigger and the workflow owns the execution.</p>'
  '<p><strong>Keep the zombie-cron check</strong> inside <code>getAllSchedules()</code> — stop, delete, soft-delete when the flow is gone. It is the one part of this code already doing the right thing.</p>',
  '<p>Corrigir a duplicação sem corrigir o segundo defeito só duplica com mais eficiência. De todo modo, o callback <strong>para de aguardar o run</strong> — o scheduler é dono do gatilho e o workflow é dono da execução.</p>'
  '<p><strong>Mantenha a checagem de cron zumbi</strong> dentro de <code>getAllSchedules()</code> — parar, apagar, apagar logicamente quando o fluxo já não existe. É a única parte deste código que já faz a coisa certa.</p>'),
 'ba': (('Each replica holds its own copy of every active schedule and fires it independently — and the run happens inside the cron callback rather than in the queue.',
         'Cada réplica guarda a própria cópia de todo agendamento ativo e dispara sozinha — e o run acontece dentro do callback do cron, não na fila.'),
        ('One fire per schedule regardless of replica count, on Temporal Schedules — with pause, backfill and last-run visibility the in-process registry cannot offer — and a callback that returns without waiting for the run.',
         'Um disparo por agendamento independentemente da contagem de réplicas, sobre Temporal Schedules — com pausa, backfill e visibilidade da última execução que o registro em processo não oferece — e um callback que retorna sem esperar o run.')),
 'callouts': [('decide', ('Why Temporal Schedules here and a lock there', 'Por que Temporal Schedules aqui e um lock lá'),
   ('<p>Greps for <code>ScheduleClient</code>, <code>scheduleClient</code> and <code>createSchedule</code> across the worker and <code>back/src/temporal</code> return nothing, so the platform&#x27;s native scheduling is entirely unused. It gives by construction exactly what this part would otherwise build by hand.</p>'
    '<p>The advisory lock stays the right answer for the <strong>thirteen framework crons</strong>, which are internal maintenance and have no reason to become workflows (review §11.3).</p>',
    '<p>Buscas por <code>ScheduleClient</code>, <code>scheduleClient</code> e <code>createSchedule</code> no worker e em <code>back/src/temporal</code> não retornam nada, então o agendamento nativo da plataforma está totalmente sem uso. Ele dá por construção exatamente o que esta parte construiria à mão.</p>'
    '<p>O advisory lock continua sendo a resposta certa para os <strong>treze crons de framework</strong>, que são manutenção interna e não têm motivo para virar workflows (review §11.3).</p>'))]},
{'n': '3',
 'title': ('Redis carries three unrelated responsibilities', 'O Redis carrega três responsabilidades sem relação'),
 'loc': 'flux.service.ts · Redis/infra',
 'purpose': ('Confirm from infrastructure what cannot be read from this repository, before parallelism raises the rate.',
             'Confirmar com a infraestrutura o que não dá para ler deste repositório, antes de o paralelismo aumentar a taxa.'),
 'body': (
  '<p>Redis backs the Bull queues, the worker→backend pub/sub, and the delivery dedup keys. The dedup is already a correct pattern — <code>SET key &#x27;1&#x27; EX 86400 NX</code>, run-scoped.</p>'
  '<p>Two things to confirm, and neither of them can be read from this repository:</p>',
  '<p>O Redis sustenta as filas do Bull, o pub/sub worker→backend, e as chaves de dedup de entrega. O dedup já é um padrão correto — <code>SET key &#x27;1&#x27; EX 86400 NX</code>, com escopo de run.</p>'
  '<p>Duas coisas a confirmar, e nenhuma delas pode ser lida deste repositório:</p>'),
 'list': [
  ('<strong>Eviction policy.</strong> Under <code>allkeys-lru</code> or <code>allkeys-random</code>, dedup keys are evictable, and the failure mode is <strong>duplicate customer emails and duplicate outbound webhooks</strong>.',
   '<strong>Política de despejo.</strong> Sob <code>allkeys-lru</code> ou <code>allkeys-random</code>, chaves de dedup são despejáveis, e o modo de falha é <strong>e-mails duplicados para o cliente e webhooks de saída duplicados</strong>.'),
  ('<strong>Sizing for after <code>B5</code>.</strong> Parallel dispatch raises the pub/sub rate substantially. Today&#x27;s headroom is not evidence for post-parallelism — and losing Redis loses admission, visibility and duplicate suppression at once.',
   '<strong>Dimensionamento para depois da <code>B5</code>.</strong> O dispatch paralelo aumenta bastante a taxa de pub/sub. A folga de hoje não é evidência para o pós-paralelismo — e perder o Redis perde admissão, visibilidade e supressão de duplicatas de uma vez.'),
 ],
 'ba': (('Three responsibilities with different correctness requirements share one instance and one eviction policy — and nobody working in this repository can say which policy it is.',
         'Três responsabilidades com requisitos de correção diferentes dividem uma instância e uma política de despejo — e ninguém trabalhando neste repositório sabe dizer qual política é.'),
        ('The dedup keys are proven to survive memory pressure, and the bus is sized for the event rate parallel dispatch will produce.',
         'As chaves de dedup são provadas sobreviver à pressão de memória, e o barramento é dimensionado para a taxa de eventos que o dispatch paralelo vai produzir.'))},
{'n': '4',
 'title': ('The POP3 poll', 'O poll POP3'),
 'loc': 'mail.service.ts · deleteEmailsSequentially()',
 'purpose': ('Make one delivered message produce exactly one run, without depending on a lock this code cannot see.',
             'Fazer uma mensagem entregue produzir exatamente um run, sem depender de um lock que este código não enxerga.'),
 'body': (
  '<p>The email poll is one of the thirteen crons, so it fires every ten seconds <strong>per replica</strong>. There is no message-id dedup and no lock — greps for <code>messageId</code>, <code>dedup</code>, <code>lock</code> and <code>NX</code> return nothing. Messages are fetched, processed and only then deleted (<code>deleteEmailsSequentially</code>), so the window between fetch and delete spans the whole batch, <strong>including enqueueing the runs</strong>.</p>'
  '<p><strong>Be fair about today&#x27;s risk.</strong> POP3 requires the server to lock the maildrop exclusively for the session, so a well-behaved provider refuses the second replica and duplicates may not occur now. That is exactly the problem: <strong>correctness depends on a lock this code does not take and cannot observe.</strong> Move the mailbox to IMAP or an API, or use a provider that permits concurrent sessions, and the failure becomes duplicate runs charged to the customer, with nothing to catch it.</p>',
  '<p>O poll de e-mail é um dos treze crons, então dispara a cada dez segundos <strong>por réplica</strong>. Não há dedup por id de mensagem nem lock — buscas por <code>messageId</code>, <code>dedup</code>, <code>lock</code> e <code>NX</code> não retornam nada. As mensagens são buscadas, processadas e só então apagadas (<code>deleteEmailsSequentially</code>), então a janela entre buscar e apagar cobre o lote inteiro, <strong>incluindo o enfileiramento dos runs</strong>.</p>'
  '<p><strong>Seja justo sobre o risco de hoje.</strong> O POP3 exige que o servidor trave a maildrop com exclusividade durante a sessão, então um provedor bem-comportado recusa a segunda réplica e duplicatas podem não ocorrer agora. É exatamente esse o problema: <strong>a correção depende de um lock que este código não toma e não consegue observar.</strong> Mova a caixa para IMAP ou uma API, ou use um provedor que permita sessões concorrentes, e a falha passa a ser runs duplicados cobrados do cliente, sem nada para pegá-los.</p>'),
 'body2': (
  '<p><strong>Two independent guards</strong>, because the failure they prevent is a charge to a customer: Part 1&#x27;s advisory lock covers the polling, and — independently of it — dedup by message id before enqueueing, using the same <code>SET … NX</code> pattern already used for delivery (<code>flux.service.ts</code>).</p>'
  '<p>Reconsider the ten-second interval while you are there. It is a poll against a mailbox, and at one replica it is <strong>8,640 connections a day</strong>.</p>',
  '<p><strong>Duas guardas independentes</strong>, porque a falha que elas evitam é uma cobrança ao cliente: o advisory lock da Parte 1 cobre o polling e — independentemente dele — dedup por id de mensagem antes de enfileirar, usando o mesmo padrão <code>SET … NX</code> já usado na entrega (<code>flux.service.ts</code>).</p>'
  '<p>Reconsidere o intervalo de dez segundos enquanto estiver lá. É um poll contra uma caixa de correio, e com uma réplica são <strong>8.640 conexões por dia</strong>.</p>'),
 'ba': (('Every replica past the first fails to acquire the maildrop lock every ten seconds — and nothing in the code would notice if one of them succeeded.',
         'Toda réplica depois da primeira falha em adquirir o lock da maildrop a cada dez segundos — e nada no código perceberia se uma delas conseguisse.'),
        ('The poll runs on one replica per tick, and a message that is somehow fetched twice still produces one run, because its message id was seen before.',
         'O poll roda numa réplica por tick, e uma mensagem que de algum jeito seja buscada duas vezes ainda produz um run, porque o id dela já foi visto antes.'))},
]

VERIF = [
 (True, ('Negative control — Part 2', 'Controle negativo — Parte 2'),
  ('Run <strong>two backend replicas locally</strong>, create one schedule, and count the runs. <strong>Two is the bug — see it before fixing it.</strong> Then confirm exactly one.',
   'Rode <strong>duas réplicas de backend localmente</strong>, crie um agendamento, e conte os runs. <strong>Dois é o bug — veja-o antes de corrigir.</strong> Depois confirme exatamente um.')),
 (False, ('Negative control — Part 1', 'Controle negativo — Parte 1'),
  ('Two replicas, one purge cron: confirm it executes <strong>once</strong>, and that the replica which skipped <strong>logged that it skipped</strong> rather than failing silently.',
   'Duas réplicas, um cron de purge: confirme que ele executa <strong>uma vez</strong>, e que a réplica que pulou <strong>logou que pulou</strong> em vez de falhar em silêncio.')),
 (False, ('The callback returns without waiting', 'O callback retorna sem esperar'),
  ('Confirm the schedule callback returns without waiting for the run — <strong>and that the run still happens</strong>. The failure mode of fixing this carelessly is a schedule that enqueues nothing.',
   'Confirme que o callback do agendamento retorna sem esperar o run — <strong>e que o run ainda acontece</strong>. O modo de falha de corrigir isto sem cuidado é um agendamento que não enfileira nada.')),
 (True, ('Negative control — Part 4', 'Controle negativo — Parte 4'),
  ('Deliver one message and confirm exactly one run, with <strong>two replicas polling</strong>. Then <strong>bypass the maildrop lock deliberately</strong> — process the same message twice — and confirm the message-id dedup still yields one run. The second half is the test that matters, because it is the one that survives a change of mail provider.',
   'Entregue uma mensagem e confirme exatamente um run, com <strong>duas réplicas fazendo poll</strong>. Depois <strong>burle o lock da maildrop de propósito</strong> — processe a mesma mensagem duas vezes — e confirme que o dedup por id de mensagem ainda produz um run. A segunda metade é o teste que importa, porque é o que sobrevive a uma troca de provedor de e-mail.')),
 (False, ('Redis survives memory pressure', 'O Redis sobrevive à pressão de memória'),
  ('With the eviction policy set, fill the instance past <code>maxmemory</code> and confirm a <strong>dedup key survives</strong>. An assumption about eviction is worth exactly as much as the test that proves it.',
   'Com a política de despejo definida, encha a instância além do <code>maxmemory</code> e confirme que uma <strong>chave de dedup sobrevive</strong>. Uma suposição sobre despejo vale exatamente o que vale o teste que a prova.')),
]

DONE = ('Each cron runs <strong>once per tick regardless of replica count</strong>, each schedule fires once and <strong>the queue owns the execution</strong>, the 3AM cluster is staggered, and the dedup keys are <strong>proven</strong> to survive memory pressure.',
        'Cada cron roda <strong>uma vez por tick independentemente da contagem de réplicas</strong>, cada agendamento dispara uma vez e <strong>a fila é dona da execução</strong>, o bloco das 3h está escalonado, e as chaves de dedup são <strong>provadas</strong> sobreviver à pressão de memória.')

FILES = [
 ('back/src/cronJobs/** (thirteen @Cron sites)', False),
 ('back/src/app-api/mail/mail.service.ts', False),
 ('back/src/app-api/schedule/schedule.controller.ts (create() · getAllSchedules())', False),
 ('back/src/app-api/flux/flux.service.ts (the email-sent: dedup)', False),
 ('Redis/infra configuration', True),
]

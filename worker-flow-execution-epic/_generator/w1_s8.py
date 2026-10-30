# -*- coding: utf-8 -*-
TITLE = ('One fire per schedule, one run per cron', 'Um disparo por agendamento, um run por cron')

GOAL = ('Running a second backend replica stops <b>multiplying scheduled work</b> — crons, user schedules and the email poll alike.',
        'Rodar uma segunda réplica de backend para de <b>multiplicar trabalho agendado</b> — crons, agendamentos de usuário e o poll de e-mail, todos.')

GLANCE = [
 ('crit', ('Severity', 'Severidade'), ('High', 'Alta'),
  ('Fourteen crons with no leader election, and schedules held in an in-process registry. Review §9.3, §9.4, §9.5.',
   'Catorze crons sem eleição de líder, e agendamentos guardados num registro em processo. Review §9.3, §9.4, §9.5.')),
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
 """<p><code>@Cron</code> is registered <strong>fourteen times</strong> across <code>back/src</code> — a fifteenth site, in <code>updateTechnologiesFromSheets.service.ts</code>, is commented out, and <code>syncAiModelsFromGateway</code> (<code>EVERY_DAY_AT_4AM</code>) is the one that landed after the first draft, corrected 2026-09-18 — and there is no leader election: greps for <code>leader</code>, <code>isLeader</code>, <code>CRON_ENABLED</code> or an advisory-lock guard return nothing. <strong>Every cron fires on every replica.</strong></p>
<p>User schedules are worse, because they cost money. They are registered in NestJS&#x27;s in-process registry — <code>schedulerRegistry.addCronJob</code> at two sites in <code>schedule.controller.ts</code> (<code>create()</code>, <code>getAllSchedules()</code>) — so each replica holds its own copy and fires it independently. <strong>N replicas means N runs of the same schedule, each charged to the customer.</strong></p>""",
 """<p>O <code>@Cron</code> está registrado <strong>catorze vezes</strong> em <code>back/src</code> — um décimo quinto ponto, em <code>updateTechnologiesFromSheets.service.ts</code>, está comentado, e o <code>syncAiModelsFromGateway</code> (<code>EVERY_DAY_AT_4AM</code>) é o que chegou depois do primeiro rascunho, corrigido em 2026-09-18 — e não há eleição de líder: buscas por <code>leader</code>, <code>isLeader</code>, <code>CRON_ENABLED</code> ou uma guarda de advisory lock não retornam nada. <strong>Todo cron dispara em toda réplica.</strong></p>
<p>Os agendamentos de usuário são piores, porque custam dinheiro. Eles são registrados no registro em processo do NestJS — <code>schedulerRegistry.addCronJob</code> em dois pontos de <code>schedule.controller.ts</code> (<code>create()</code>, <code>getAllSchedules()</code>) — então cada réplica guarda sua própria cópia e dispara sozinha. <strong>N réplicas significam N runs do mesmo agendamento, cada um cobrado do cliente.</strong></p>""")

TABLE = {
 'k': 'table',
 'head': [('What multiplies', 'O que multiplica'), ('Where', 'Onde'),
          ('Per replica today', 'Por réplica hoje'), ('What it costs', 'O que custa')],
 'rows': [
  [{'t': ('Fourteen <code>@Cron</code> sites', 'Catorze pontos com <code>@Cron</code>')},
   ('<code>back/src/cronJobs/**</code>', '<code>back/src/cronJobs/**</code>'),
   {'t': ('fires everywhere', 'dispara em todas'), 'pill': 'no'},
   ('Six purges at <code>EVERY_DAY_AT_3AM</code> hitting the same tables in the same minute, and <code>chargeUsersPerClonedVoice</code> debiting customers with no guard at all',
    'Seis purges em <code>EVERY_DAY_AT_3AM</code> batendo nas mesmas tabelas no mesmo minuto, e o <code>chargeUsersPerClonedVoice</code> debitando clientes sem guarda nenhuma')],
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
   ('One of the fourteen', 'Um dos catorze'),
   {'t': ('every ten minutes', 'a cada dez minutos'), 'pill': 'weak'},
   ('Waste rather than corruption — but it is the same missing mechanism',
    'Desperdício, não corrupção — mas é o mesmo mecanismo faltando')],
 ]}

DEC_CRON = {
 'k': 'decision', 'id': 'S8-a', 'plan': 'D12', 'status':'set', 'open': True,
 'q': ('What makes a cron fire once, when fourteen of them fire on every replica?',
       'O que faz um cron disparar uma vez, quando catorze deles disparam em toda réplica?'),
 'intro': (
  'Greps for <code>leader</code>, <code>isLeader</code>, <code>CRON_ENABLED</code> and an advisory-lock guard return nothing, so today the answer is “nothing”. '
  'The requirement is <strong>one mechanism for all fourteen, not fourteen guards</strong> — and the property worth optimising for is that '
  '<strong>nothing has to know how many replicas exist</strong>, because that is the number a deploy is allowed to change without telling anyone.',
  'Buscas por <code>leader</code>, <code>isLeader</code>, <code>CRON_ENABLED</code> e uma guarda de advisory lock não retornam nada, então hoje a resposta é “nada”. '
  'O requisito é <strong>um mecanismo para os catorze, não catorze guardas</strong> — e a propriedade a otimizar é que '
  '<strong>nada precise saber quantas réplicas existem</strong>, porque esse é o número que um deploy pode mudar sem avisar ninguém.'),
 'opts': [
  {'ltr': 'A', 'pick':True,'name': ('An advisory lock per job name', 'Um advisory lock por nome de job'),
   'tag': ('recommended', 'recomendada'),
   'how': ('Each job takes a <strong>non-blocking</strong> advisory lock — <code>pg_try_advisory_xact_lock</code>, named after itself — at the top of its run, and it releases automatically when the transaction ends. A replica that cannot take the lock returns immediately and skips.',
           'Cada job toma um advisory lock <strong>não bloqueante</strong> — <code>pg_try_advisory_xact_lock</code>, nomeado como o próprio job — no início do run, e ele é liberado automaticamente quando a transação termina. A réplica que não consegue o lock retorna na hora e pula.'),
   'pros': [('<strong>Nothing has to know the replica count</strong> — the mechanism is correct at one replica and at ten',
             '<strong>Nada precisa saber a contagem de réplicas</strong> — o mecanismo é correto com uma réplica e com dez'),
            ('It is the non-blocking sibling of a lock already used at three sites — <code>flow-node.service.ts</code> (×2) and <code>session-state.service.ts</code> — so there is no new dependency, only the right variant: those three call <code>pg_advisory_xact_lock</code>, which <strong>blocks</strong> and would make a losing replica wait for the winner and run the job anyway. <code>pg_try_advisory_xact_lock</code> is used nowhere yet, so this choice has to be made deliberately, not copied',
             'É a irmã não bloqueante de um lock já usado em três pontos — <code>flow-node.service.ts</code> (×2) e <code>session-state.service.ts</code> — então não há dependência nova, só a variante certa: os três chamam <code>pg_advisory_xact_lock</code>, que <strong>bloqueia</strong> e faria uma réplica perdedora esperar a vencedora e rodar o job assim mesmo. O <code>pg_try_advisory_xact_lock</code> não é usado em lugar nenhum ainda, então esta escolha precisa ser deliberada, não copiada'),
            ('It degrades correctly: the loser skips, and can say in a log line that it skipped',
             'Degrada corretamente: quem perde pula, e pode dizer numa linha de log que pulou'),
            ('One mechanism covers all fourteen, including the POP3 poll in Part 4, and it absorbs <code>DISABLE_CRONS</code> — today an all-or-nothing flag checked at the top of six of the fourteen — instead of sitting beside it as a second guard',
             'Um mecanismo cobre os catorze, incluindo o poll POP3 da Parte 4, e absorve o <code>DISABLE_CRONS</code> — hoje uma flag tudo-ou-nada checada no início de seis dos catorze — em vez de ficar ao lado dele como uma segunda guarda')],
   'cons': [('It puts a lock acquisition on the database this epic is already worried about — fourteen jobs, one of them every ten seconds',
             'Coloca uma aquisição de lock no banco com que este épico já se preocupa — catorze jobs, um deles a cada dez segundos'),
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
   'cons': [('It is a distributed-systems component to run and reason about, for fourteen maintenance jobs',
             'É um componente de sistemas distribuídos para rodar e raciocinar, por causa de catorze jobs de manutenção'),
            ('An advisory lock <strong>is</strong> leader election, scoped to one job and expiring by itself — with none of the machinery',
             'Um advisory lock <strong>é</strong> eleição de líder, com escopo de um job e expirando sozinho — sem nada dessa maquinaria')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>machinery out of proportion to the problem</b>', 'Nosso: <b>maquinaria desproporcional ao problema</b>'))]},
  {'ltr': 'D', 'name': ('Temporal Schedules for all fourteen', 'Temporal Schedules para os catorze'),
   'tag': ('the eventual answer for Part 2 — see E4', 'a resposta eventual da Parte 2 — ver E4'),
   'how': ('Move every cron onto the platform&#x27;s native scheduling instead of an advisory lock.',
           'Mover todo cron para o agendamento nativo da plataforma em vez de um advisory lock.'),
   'pros': [('One fire per schedule by construction, with pause, backfill and last-run visibility',
             'Um disparo por agendamento por construção, com pausa, backfill e visibilidade da última execução'),
            ('It <em>is</em> the right destination for the user-facing schedules too — just not yet: <code>E4</code> takes it once <code>B4</code> gives the worker a whole-flow workflow to trigger. Part 2 ships <code>D26</code>&#x27;s Bull repeatable jobs first, because today there is nothing for a Temporal Schedule to call',
             'É <em>de fato</em> o destino certo também para os agendamentos visíveis ao cliente — só que ainda não: a <code>E4</code> o adota quando a <code>B4</code> der ao worker um workflow de fluxo inteiro para disparar. A Parte 2 embarca os Bull repeatable jobs da <code>D26</code> primeiro, porque hoje não há nada para um Temporal Schedule chamar')],
   'cons': [('<strong>These fourteen are internal maintenance and have no reason to become workflows</strong>',
             '<strong>Estes catorze são manutenção interna e não têm motivo para virar workflows</strong>'),
            ('Each cron would have to be reachable as a workflow or an activity — a large restructuring for a set of purges',
             'Cada cron teria de ser alcançável como workflow ou activity — uma reestruturação grande para um conjunto de purges')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>fourteen jobs restructured for no user-facing gain</b>', 'Nosso: <b>catorze jobs reestruturados sem ganho para o cliente</b>'))]},
 ],
 'rec': (
  '<p><strong>A for the fourteen framework crons — recorded as <code>D12</code>.</strong> The crons are internal maintenance and Temporal Schedules buy them nothing they need (review §11.3). Part 2 does not take Option D either, despite the first draft recommending Temporal Schedules there: <strong><code>D26</code> settled Bull repeatable jobs instead</strong>, because a Temporal Schedule can only trigger a workflow and the worker has none that runs a whole flow yet — that is <code>B4</code>. Option D is the right answer for the user-facing schedules, it is just <code>E4</code>&#x27;s answer, not today&#x27;s.</p>'
  '<p>Whichever wins, <strong>the replica that skips must log that it skipped</strong>. A guard that silently does nothing is indistinguishable from a cron that stopped working, and the second one is discovered months later.</p>'
  '<p>And <strong>stagger the 3AM cluster while you are there</strong> — six purges starting in the same minute is a self-inflicted load spike on the database <code>S2</code> is already sizing.</p>',
  '<p><strong>A para os catorze crons de framework — registrada como <code>D12</code>.</strong> Os crons são manutenção interna e os Temporal Schedules não lhes dão nada de que precisem (review §11.3). A Parte 2 também não adota a opção D, apesar de o primeiro rascunho ter recomendado Temporal Schedules ali: <strong>a <code>D26</code> definiu Bull repeatable jobs no lugar</strong>, porque um Temporal Schedule só consegue disparar um workflow e o worker ainda não tem nenhum que rode um fluxo inteiro — isso é a <code>B4</code>. A opção D é a resposta certa para os agendamentos visíveis ao cliente, só que é a resposta da <code>E4</code>, não a de hoje.</p>'
  '<p>Seja qual for a escolha, <strong>a réplica que pula precisa logar que pulou</strong>. Uma guarda que silenciosamente não faz nada é indistinguível de um cron que parou de funcionar, e o segundo caso é descoberto meses depois.</p>'
  '<p>E <strong>escalone o bloco das 3h enquanto estiver lá</strong> — seis purges começando no mesmo minuto é um pico de carga autoinfligido no banco que a <code>S2</code> já está dimensionando.</p>'),
 'who': [('Engineering', 'Engenharia'),
         ('Infra confirms the lock is acceptable on the database', 'Infra confirma que o lock é aceitável no banco')],
}

PARTS = [
{'n': '1',
 'title': ('The fourteen crons', 'Os catorze crons'),
 'loc': 'back/src/cronJobs/** · flow-node.service.ts · session-state.service.ts',
 'purpose': ('One mechanism for all fourteen, so a second replica stops multiplying maintenance work.',
             'Um mecanismo para os catorze, para que uma segunda réplica pare de multiplicar trabalho de manutenção.'),
 'body': (
  '<p><code>@Cron</code> is registered fourteen times across <code>back/src</code>, and there is no leader election. Every cron fires on every replica.</p>'
  '<p>Some of that is waste: six purges all at <code>EVERY_DAY_AT_3AM</code> — <code>purgeCanceledSubscriptions</code>, <code>purgeMcpIdempotencyKeys</code>, <code>purgeMcpTokens</code>, <code>purgeNodeExecutions</code>, <code>purgeSpaceRunLogs</code>, <code>purgeZapierWebhookPayloads</code> — each running per replica against the same tables in the same minute. <strong>Some of it is not waste at all:</strong> <code>chargeUsersPerClonedVoice</code> (08:00 daily) debits customers through <code>productService.chargeUserProduct</code>, with no guard whatsoever — duplicated, it is not waste, it is a refund. <code>mail.service.ts</code> polls POP3 <code>EVERY_10_SECONDS</code> per replica, and <code>markStuckSpaceRunLogs</code> runs every ten minutes per replica.</p>'
  '<p><strong>A partial guard already exists.</strong> <code>DISABLE_CRONS</code> is checked at the top of six of the fourteen — <code>purgeCanceledSubscriptions</code>, <code>purgeMcpIdempotencyKeys</code>, <code>purgeMcpTokens</code>, <code>purgeNodeExecutions</code>, <code>purgeZapierWebhookPayloads</code>, <code>syncAiModelsFromGateway</code> — and is declared twice in <code>.env.example</code>, which is its own small bug. It is all-or-nothing: it can turn every cron off, never one replica only.</p>',
  '<p>O <code>@Cron</code> está registrado catorze vezes em <code>back/src</code>, e não há eleição de líder. Todo cron dispara em toda réplica.</p>'
  '<p>Parte disso é desperdício: seis purges, todos em <code>EVERY_DAY_AT_3AM</code> — <code>purgeCanceledSubscriptions</code>, <code>purgeMcpIdempotencyKeys</code>, <code>purgeMcpTokens</code>, <code>purgeNodeExecutions</code>, <code>purgeSpaceRunLogs</code>, <code>purgeZapierWebhookPayloads</code> — cada um rodando por réplica contra as mesmas tabelas no mesmo minuto. <strong>Parte não é desperdício nenhum:</strong> o <code>chargeUsersPerClonedVoice</code> (08:00 diariamente) debita clientes via <code>productService.chargeUserProduct</code>, sem guarda nenhuma — duplicado, não é desperdício, é um reembolso. O <code>mail.service.ts</code> faz poll POP3 <code>EVERY_10_SECONDS</code> por réplica, e o <code>markStuckSpaceRunLogs</code> roda a cada dez minutos por réplica.</p>'
  '<p><strong>Uma guarda parcial já existe.</strong> O <code>DISABLE_CRONS</code> é checado no início de seis dos catorze — <code>purgeCanceledSubscriptions</code>, <code>purgeMcpIdempotencyKeys</code>, <code>purgeMcpTokens</code>, <code>purgeNodeExecutions</code>, <code>purgeZapierWebhookPayloads</code>, <code>syncAiModelsFromGateway</code> — e é declarado duas vezes no <code>.env.example</code>, o que já é um bug pequeno em si. É tudo-ou-nada: pode desligar todo cron, nunca uma réplica só.</p>'),
 'body2': (
  '<p><strong>Stagger the 3AM cluster while you are there.</strong> Six purges starting in the same minute is a self-inflicted load spike on the database this epic is already worried about.</p>'
  '<p>The lock is <strong><code>pg_try_advisory_xact_lock</code></strong>, not its blocking sibling. The three existing advisory-lock sites in the codebase — <code>flow-node.service.ts</code> (×2) and <code>session-state.service.ts</code> — all use <code>pg_advisory_xact_lock</code>, which <strong>blocks</strong>: it waits for the holder and then proceeds anyway. Copying that precedent produces a losing replica that waits for the winner&#x27;s transaction and runs the job regardless — the exact defect this part exists to remove. <code>pg_try_advisory_xact_lock</code> is used nowhere in the codebase today, so there is no precedent to copy and the choice has to be made deliberately. The new lock <strong>absorbs</strong> <code>DISABLE_CRONS</code> rather than sitting beside it as a second guard.</p>',
  '<p><strong>Escalone o bloco das 3h enquanto estiver lá.</strong> Seis purges começando no mesmo minuto é um pico de carga autoinfligido no banco com que este épico já se preocupa.</p>'
  '<p>O lock é o <strong><code>pg_try_advisory_xact_lock</code></strong>, não a irmã bloqueante dele. Os três pontos existentes de advisory lock no código — <code>flow-node.service.ts</code> (×2) e <code>session-state.service.ts</code> — usam todos <code>pg_advisory_xact_lock</code>, que <strong>bloqueia</strong>: espera quem segura o lock e prossegue de qualquer jeito. Copiar esse precedente produz uma réplica perdedora que espera a transação da vencedora e roda o job mesmo assim — o exato defeito que esta parte existe para remover. O <code>pg_try_advisory_xact_lock</code> não é usado em lugar nenhum do código hoje, então não há precedente a copiar e a escolha precisa ser deliberada. O novo lock <strong>absorve</strong> o <code>DISABLE_CRONS</code> em vez de ficar ao lado dele como uma segunda guarda.</p>'),
 'ba': (('Every cron fires on every replica, so maintenance work is multiplied by the replica count — and the POP3 poll is multiplied every ten seconds.',
         'Todo cron dispara em toda réplica, então o trabalho de manutenção é multiplicado pela contagem de réplicas — e o poll POP3 é multiplicado a cada dez segundos.'),
        ('One non-blocking guard (<code>pg_try_advisory_xact_lock</code>), taken per job name, so each cron runs once per tick regardless of how many replicas exist — and the replica that skipped <strong>says</strong> it skipped.',
         'Uma guarda não bloqueante (<code>pg_try_advisory_xact_lock</code>), tomada por nome de job, para que cada cron rode uma vez por tick independentemente de quantas réplicas existam — e a réplica que pulou <strong>diz</strong> que pulou.'))},
{'n': '2',
 'title': ('User-scheduled flows', 'Fluxos agendados pelo usuário'),
 'loc': 'schedule.controller.ts · schedule.consumer.ts',
 'purpose': ('Make a schedule fire once, and make the queue actually own the execution it appears to own.',
             'Fazer um agendamento disparar uma vez, e fazer a fila de fato ser dona da execução que ela aparenta ser.'),
 'body': (
  '<p>Scheduled runs do not use a durable scheduler. They are registered in NestJS&#x27;s in-process registry — <code>schedulerRegistry.addCronJob</code> — at two sites in <code>schedule.controller.ts</code>: <code>create()</code>, and <code>getAllSchedules()</code>, which has exactly <strong>one caller</strong> — the controller&#x27;s own constructor, as a fire-and-forget promise at boot. Each replica still ends up with its own copy of every schedule and fires it independently: <strong>N replicas means N runs of the same schedule, each charged to the customer.</strong></p>'
  '<p>Four defects live in this code, all in scope:</p>',
  '<p>Runs agendados não usam um scheduler durável. Eles são registrados no registro em processo do NestJS — <code>schedulerRegistry.addCronJob</code> — em dois pontos de <code>schedule.controller.ts</code>: <code>create()</code>, e <code>getAllSchedules()</code>, que tem exatamente <strong>um chamador</strong> — o próprio construtor do controller, como uma promise fire-and-forget no boot. Cada réplica ainda assim acaba com a própria cópia de todo agendamento e dispara sozinha: <strong>N réplicas significam N runs do mesmo agendamento, cada um cobrado do cliente.</strong></p>'
  '<p>Quatro defeitos vivem neste código, todos no escopo:</p>'),
 'list': [
  ('<strong>The queue is not doing the work.</strong> The callback does <code>await this.scheduleQueue.add(&#x27;schedule-job&#x27;, { … job: await this.fluxService.apiV2({ … }) })</code> — the run is <strong>awaited as an argument to the enqueue call</strong>, so the flow already executed synchronously inside the callback and only its <em>result</em> reaches the queue. Fixing the duplication without fixing this just duplicates it more efficiently.',
   '<strong>A fila não está fazendo o trabalho.</strong> O callback faz <code>await this.scheduleQueue.add(&#x27;schedule-job&#x27;, { … job: await this.fluxService.apiV2({ … }) })</code> — o run é <strong>aguardado como argumento da chamada de enfileiramento</strong>, então o fluxo já executou de forma síncrona dentro do callback e só o <em>resultado</em> dele chega na fila. Corrigir a duplicação sem corrigir isto só duplica com mais eficiência.'),
  ('<strong><code>update()</code> never re-registers the cron.</strong> Changing a schedule&#x27;s interval does nothing until the process restarts.',
   '<strong>O <code>update()</code> nunca re-registra o cron.</strong> Mudar o intervalo de um agendamento não faz nada até o processo reiniciar.'),
  ('<strong>The registry is keyed by <code>schedule.name</code></strong>, which is user-supplied and not unique. Two schedules with the same name collide, and <code>create()</code> throws for a name already registered at boot — the durable id has to be <code>schedule.id</code>.',
   '<strong>O registro é indexado por <code>schedule.name</code></strong>, que é definido pelo usuário e não é único. Dois agendamentos com o mesmo nome colidem, e o <code>create()</code> lança erro para um nome já registrado no boot — o id durável precisa ser o <code>schedule.id</code>.'),
  ('<strong>The two registration sites send different payloads.</strong> <code>create()</code> sends <code>{...body, spaceId}</code> with a <code>userId</code>; <code>getAllSchedules()</code> sends <code>{...schedule, webhook: true, spaceId}</code> with a <code>socketId</code>. The same schedule behaves one way before the first restart and another way after — the entity shape is the survivor.',
   '<strong>Os dois pontos de registro mandam payloads diferentes.</strong> O <code>create()</code> manda <code>{...body, spaceId}</code> com um <code>userId</code>; o <code>getAllSchedules()</code> manda <code>{...schedule, webhook: true, spaceId}</code> com um <code>socketId</code>. O mesmo agendamento se comporta de um jeito antes do primeiro restart e de outro depois — o formato da entidade é o que sobrevive.'),
 ],
 'body2': (
  '<p>And a fifth thing, which is why "the queue owns the execution" needed a decision and not just a fix: <code>ScheduleConsumer</code> only emits a socket event, and only when <code>data.userId</code> is set — which only <code>create()</code> sets. Boot-registered schedules therefore notify nobody. The queue does not execute and does not reliably notify.</p>'
  '<p><strong>Settled 2026-09-18 as <code>D26</code>: Bull repeatable jobs, not Temporal Schedules.</strong> Bull 4.16.5 is already a dependency and <code>ApiV2Queue</code> / <code>ApiV2QueueProcessor</code> are already in production (<code>src/jobs/apiV2Job/</code>), with <code>ApiV2QueueModel.params</code> already carrying exactly the fields the callback passes today. The schedule state moves out of the per-replica <code>SchedulerRegistry</code> and into Redis, which Bull already manages and which dedupes a repeatable by its repeat key regardless of how many replicas registered it — keyed by <strong><code>schedule.id</code></strong>, not <code>name</code>.</p>'
  '<p>What that buys, beyond stopping the duplication: the "callback stops awaiting the run" fix becomes <strong>structural</strong> rather than a discipline, because there is no callback left — the processor <em>is</em> the execution. <code>getAllSchedules()</code> leaves the codebase, taking defects 2, 3 and 4 with it. <strong>Corrected 2026-09-19, after implementation:</strong> the <code>schedule</code> queue is the mechanism, not a casualty of it — a repeatable job lives in a queue, so it now carries one repeatable per user schedule and <code>ScheduleConsumer</code> processes them; what is retired is the old shape, the callback that awaited a run and the boot-time socket emit. <code>SchedulerRegistry</code> survives in <code>legacy-schedule-registrar.service.ts</code> because §3.2 ships this behind a flag seeded disabled, so the old path is the one that runs while <code>repeatable_schedules</code> is off; it leaves when the flag is on everywhere. <code>update()</code> and <code>delete()</code> become <code>removeRepeatable</code> + <code>add</code>. Boot notification is deliberately dropped: the socket emit was already dead for every boot-registered schedule, so preserving it would mean building behaviour that never worked rather than keeping behaviour that did.</p>'
  '<p><strong>Keep the zombie-cron check</strong> — stop, delete, soft-delete when the flow is gone. It is the one part of this code already doing the right thing. It becomes a reconciliation over the <code>schedule</code> table at boot, which is also what recovers the repeatables if Redis is ever lost: <strong>the table stays the source of truth</strong>, Redis only holds the timer.</p>',
  '<p>E uma quinta coisa, que é o motivo pelo qual "a fila ser dona da execução" precisava de uma decisão, não só de uma correção: o <code>ScheduleConsumer</code> só emite um evento de socket, e só quando <code>data.userId</code> está definido — o que só o <code>create()</code> define. Agendamentos registrados no boot, portanto, não notificam ninguém. A fila não executa e não notifica de forma confiável.</p>'
  '<p><strong>Decidido em 2026-09-18 como <code>D26</code>: Bull repeatable jobs, não Temporal Schedules.</strong> O Bull 4.16.5 já é uma dependência e o <code>ApiV2Queue</code> / <code>ApiV2QueueProcessor</code> já estão em produção (<code>src/jobs/apiV2Job/</code>), com o <code>ApiV2QueueModel.params</code> já carregando exatamente os campos que o callback passa hoje. O estado do agendamento sai do <code>SchedulerRegistry</code> por réplica e vai para o Redis, que o Bull já gerencia e que faz dedup de um repeatable pela sua repeat key independentemente de quantas réplicas o registraram — indexado pelo <strong><code>schedule.id</code></strong>, não pelo <code>name</code>.</p>'
  '<p>O que isso compra, além de parar a duplicação: a correção "o callback para de aguardar o run" vira <strong>estrutural</strong> em vez de disciplina, porque não sobra callback nenhum — o processor <em>é</em> a execução. O <code>getAllSchedules()</code> sai do código, levando junto os defeitos 2, 3 e 4. <strong>Corrigido em 2026-09-19, depois da implementação:</strong> a fila <code>schedule</code> é o mecanismo, não uma baixa dele — um repeatable job vive numa fila, então ela agora carrega um repeatable por agendamento de usuário e o <code>ScheduleConsumer</code> os processa; o que se aposenta é o formato antigo, o callback que aguardava a execução e o emit de socket no boot. O <code>SchedulerRegistry</code> sobrevive em <code>legacy-schedule-registrar.service.ts</code> porque a §3.2 entrega isto atrás de um flag semeado desligado, então o caminho antigo é o que roda enquanto o <code>repeatable_schedules</code> estiver off; ele sai quando o flag estiver ligado em todos os ambientes. O <code>update()</code> e o <code>delete()</code> viram <code>removeRepeatable</code> + <code>add</code>. A notificação no boot é abandonada deliberadamente: o emit de socket já estava morto para todo agendamento registrado no boot, então preservá-lo seria construir um comportamento que nunca funcionou, não manter um que funcionava.</p>'
  '<p><strong>Mantenha a checagem de cron zumbi</strong> — parar, apagar, apagar logicamente quando o fluxo já não existe. É a única parte deste código que já faz a coisa certa. Ela vira uma reconciliação sobre a tabela <code>schedule</code> no boot, que também é o que recupera os repeatables se o Redis for perdido: <strong>a tabela continua sendo a fonte da verdade</strong>, o Redis só guarda o timer.</p>'),
 'ba': (('Each replica holds its own copy of every active schedule and fires it independently — and the run happens inside the cron callback rather than in the queue.',
         'Cada réplica guarda a própria cópia de todo agendamento ativo e dispara sozinha — e o run acontece dentro do callback do cron, não na fila.'),
        ('One fire per schedule regardless of replica count, on Bull repeatable jobs keyed by <code>schedule.id</code> — with the queue structurally owning the execution — and the zombie check surviving as a boot reconciliation over the <code>schedule</code> table.',
         'Um disparo por agendamento independentemente da contagem de réplicas, sobre Bull repeatable jobs indexados pelo <code>schedule.id</code> — com a fila sendo estruturalmente dona da execução — e a checagem de zumbi sobrevivendo como uma reconciliação no boot sobre a tabela <code>schedule</code>.')),
 'callouts': [('decide', ('Why Bull now and Temporal later', 'Por que Bull agora e Temporal depois'),
   ('<p>A Temporal Schedule can only trigger a workflow, and the worker exposes three today — <code>processSingleNode</code>, <code>processAgent</code>, <code>completionWorkflow</code> — none of which executes a whole flow; that workflow is what <code>B4</code> builds. Shipping Temporal here would have meant a bridge workflow plus an internal HTTP endpoint invented purely to give the schedule something to call, both thrown away the moment <code>B4</code> lands. Building a bridge in order to demolish it is not a reason to delay this replica-safety fix, so <code>S8</code> ships the mechanism that needs no bridge, and the durable scheduler becomes <code>E4</code>, blocked on <code>B4</code>.</p>'
    '<p>The advisory lock stays the right answer for the <strong>fourteen framework crons</strong> — internal maintenance with no reason to become workflows, settled in <code>D12</code> and not reopened.</p>',
    '<p>Um Temporal Schedule só consegue disparar um workflow, e o worker expõe três hoje — <code>processSingleNode</code>, <code>processAgent</code>, <code>completionWorkflow</code> — nenhum deles executa um fluxo inteiro; esse workflow é o que a <code>B4</code> constrói. Embarcar Temporal aqui teria significado um workflow-ponte mais um endpoint HTTP interno inventados só para dar ao agendamento algo para chamar, os dois jogados fora no momento em que a <code>B4</code> chegar. Construir uma ponte para demoli-la não é motivo para atrasar esta correção de segurança de réplica, então a <code>S8</code> embarca o mecanismo que não precisa de ponte, e o scheduler durável vira a <code>E4</code>, bloqueada pela <code>B4</code>.</p>'
    '<p>O advisory lock continua sendo a resposta certa para os <strong>catorze crons de framework</strong> — manutenção interna sem motivo para virar workflows, decidido na <code>D12</code> e não reaberto.</p>'))]},
{'n': '3',
 'title': ('Redis — split into its own task', 'Redis — separado em task própria'),
 'loc': 'split out 2026-09-18 — see E5',
 'purpose': ('Record why this half of the original scope now ships on its own, instead of blocking the replica-safety fix.',
             'Registrar por que esta metade do escopo original agora embarca sozinha, em vez de bloquear a correção de segurança de réplica.'),
 'body': (
  '<p><strong>Split out on 2026-09-18 into <code>E5</code>.</strong> It is an infrastructure change with no application code in it, and the measurement says it is debt rather than an incident: production runs <code>volatile-lru</code>, which <em>can</em> evict the TTL-bearing dedup keys (<code>flux.service.ts</code>), but there have been <strong>zero evictions in fourteen days</strong> at 1.9% memory and 1.8% engine CPU. Holding this replica-safety fix for a defect that has never fired would have been the wrong trade.</p>',
  '<p><strong>Separado em 2026-09-18 para a <code>E5</code>.</strong> É uma mudança de infraestrutura sem código de aplicação nenhum, e a medição diz que é dívida, não um incidente: a produção roda <code>volatile-lru</code>, que <em>pode</em> despejar as chaves de dedup com TTL (<code>flux.service.ts</code>), mas houve <strong>zero despejos em catorze dias</strong> a 1,9% de memória e 1,8% de CPU do engine. Segurar esta correção de segurança de réplica por causa de um defeito que nunca disparou seria a troca errada.</p>'),
 'ba': None},
{'n': '4',
 'title': ('The POP3 poll', 'O poll POP3'),
 'loc': 'mail.service.ts · deleteEmailsSequentially()',
 'purpose': ('Make one delivered message produce exactly one run, without depending on a lock this code cannot see.',
             'Fazer uma mensagem entregue produzir exatamente um run, sem depender de um lock que este código não enxerga.'),
 'body': (
  '<p>The email poll is one of the fourteen crons, so it fires every ten seconds <strong>per replica</strong>. There is no message-id dedup and no lock — greps for <code>messageId</code>, <code>dedup</code>, <code>lock</code> and <code>NX</code> return nothing. Messages are fetched, processed and only then deleted (<code>deleteEmailsSequentially</code>), so the window between fetch and delete spans the whole batch, <strong>including enqueueing the runs</strong>.</p>'
  '<p><strong>Be fair about today&#x27;s risk.</strong> POP3 requires the server to lock the maildrop exclusively for the session, so a well-behaved provider refuses the second replica and duplicates may not occur now. That is exactly the problem: <strong>correctness depends on a lock this code does not take and cannot observe.</strong> Move the mailbox to IMAP or an API, or use a provider that permits concurrent sessions, and the failure becomes duplicate runs charged to the customer, with nothing to catch it.</p>',
  '<p>O poll de e-mail é um dos catorze crons, então dispara a cada dez segundos <strong>por réplica</strong>. Não há dedup por id de mensagem nem lock — buscas por <code>messageId</code>, <code>dedup</code>, <code>lock</code> e <code>NX</code> não retornam nada. As mensagens são buscadas, processadas e só então apagadas (<code>deleteEmailsSequentially</code>), então a janela entre buscar e apagar cobre o lote inteiro, <strong>incluindo o enfileiramento dos runs</strong>.</p>'
  '<p><strong>Seja justo sobre o risco de hoje.</strong> O POP3 exige que o servidor trave a maildrop com exclusividade durante a sessão, então um provedor bem-comportado recusa a segunda réplica e duplicatas podem não ocorrer agora. É exatamente esse o problema: <strong>a correção depende de um lock que este código não toma e não consegue observar.</strong> Mova a caixa para IMAP ou uma API, ou use um provedor que permita sessões concorrentes, e a falha passa a ser runs duplicados cobrados do cliente, sem nada para pegá-los.</p>'),
 'body2': (
  '<p><strong>Two independent guards</strong>, because the failure they prevent is a charge to a customer: Part 1&#x27;s advisory lock covers the polling, and — independently of it — a claim on the message id. <strong>Corrected 2026-09-19, after implementation:</strong> the deterministic Bull <code>jobId</code> alone does not hold, because the enqueue sets <code>removeOnComplete</code> and Bull frees the id once the job is cleaned up, so a later redelivery enqueues a second run. The claim is a Redis <code>SET &lt;key&gt; &#x27;1&#x27; EX 86400 NX</code> keyed on <code>Message-ID</code> (sha256 of the raw message when the header is absent), <strong>and</strong> the same key rides along as the <code>api-v2</code> <code>jobId</code> — one guard durable for 24 hours, one for as long as the job exists.</p>'
  '<p>Reconsider the ten-second interval while you are there. It is a poll against a mailbox, and at one replica it is <strong>8,640 connections a day</strong>.</p>',
  '<p><strong>Duas guardas independentes</strong>, porque a falha que elas evitam é uma cobrança ao cliente: o advisory lock da Parte 1 cobre o polling e — independentemente dele — uma reivindicação sobre o id da mensagem. <strong>Corrigido em 2026-09-19, depois da implementação:</strong> o <code>jobId</code> determinístico do Bull sozinho não se sustenta, porque o enqueue define <code>removeOnComplete</code> e o Bull libera o id assim que o job é limpo, então uma reentrega posterior enfileira uma segunda execução. A reivindicação é um <code>SET &lt;chave&gt; &#x27;1&#x27; EX 86400 NX</code> no Redis a partir do <code>Message-ID</code> (sha256 da mensagem crua quando não há o cabeçalho), <strong>e</strong> a mesma chave vai junto como <code>jobId</code> do <code>api-v2</code> — uma guarda durável por 24 horas, outra enquanto o job existir.</p>'
  '<p>Reconsidere o intervalo de dez segundos enquanto estiver lá. É um poll contra uma caixa de correio, e com uma réplica são <strong>8.640 conexões por dia</strong>.</p>'),
 'ba': (('Every replica past the first fails to acquire the maildrop lock every ten seconds — and nothing in the code would notice if one of them succeeded.',
         'Toda réplica depois da primeira falha em adquirir o lock da maildrop a cada dez segundos — e nada no código perceberia se uma delas conseguisse.'),
        ('The poll runs on one replica per tick, and a message that is somehow fetched twice still produces one run, because its claim key was already taken.',
         'O poll roda numa réplica por tick, e uma mensagem que de algum jeito seja buscada duas vezes ainda produz um run, porque a chave de reivindicação dela já estava tomada.'))},
]

VERIF = [
 (True, ('Negative control — Part 2', 'Controle negativo — Parte 2'),
  ('Run <strong>two backend replicas locally</strong>, create one schedule, and count the runs. <strong>Two is the bug — see it before fixing it.</strong> Then confirm exactly one. <strong>Count runs that completed, not jobs enqueued</strong> — after S3, a scheduled run also passes the spend ceiling and the tenant concurrency cap, so an enqueued-job count measures the wrong thing.',
   'Rode <strong>duas réplicas de backend localmente</strong>, crie um agendamento, e conte os runs. <strong>Dois é o bug — veja-o antes de corrigir.</strong> Depois confirme exatamente um. <strong>Conte os runs que completaram, não os jobs enfileirados</strong> — depois da S3, um run agendado também passa pelo teto de gasto e pelo limite de concorrência por tenant, então uma contagem de jobs enfileirados mede a coisa errada.')),
 (False, ('Negative control — Part 1', 'Controle negativo — Parte 1'),
  ('Two replicas, one purge cron: confirm it executes <strong>once</strong>, and that the replica which skipped <strong>logged that it skipped</strong> rather than failing silently. Then plant the blocking variant (<code>pg_advisory_xact_lock</code>) and confirm the control goes <strong>red</strong> — that is the specific way this fix gets written wrong.',
   'Duas réplicas, um cron de purge: confirme que ele executa <strong>uma vez</strong>, e que a réplica que pulou <strong>logou que pulou</strong> em vez de falhar em silêncio. Depois plante a variante bloqueante (<code>pg_advisory_xact_lock</code>) e confirme que o controle fica <strong>vermelho</strong> — essa é a forma específica de esta correção ser escrita errada.')),
 (False, ('The callback returns without waiting', 'O callback retorna sem esperar'),
  ('Confirm the schedule callback returns without waiting for the run — <strong>and that the run still happens</strong>. The failure mode of fixing this carelessly is a schedule that enqueues nothing.',
   'Confirme que o callback do agendamento retorna sem esperar o run — <strong>e que o run ainda acontece</strong>. O modo de falha de corrigir isto sem cuidado é um agendamento que não enfileira nada.')),
 (False, ('update() and delete() stay correct', 'update() e delete() continuam corretos'),
  ('Change a live schedule&#x27;s interval through <code>update()</code> without restarting the process, and confirm the new interval takes effect. Then <code>delete()</code> a schedule and confirm it leaves <strong>no orphaned repeatable</strong> behind.',
   'Mude o intervalo de um agendamento ativo via <code>update()</code> sem reiniciar o processo, e confirme que o novo intervalo passa a valer. Depois faça <code>delete()</code> de um agendamento e confirme que <strong>nenhum repeatable órfão</strong> fica para trás.')),
 (True, ('Negative control — Part 4', 'Controle negativo — Parte 4'),
  ('Deliver one message and confirm exactly one run, with <strong>two replicas polling</strong>. Then <strong>bypass the maildrop lock deliberately</strong> — process the same message twice — and confirm the message-id dedup still yields one run. The second half is the test that matters, because it is the one that survives a change of mail provider.',
   'Entregue uma mensagem e confirme exatamente um run, com <strong>duas réplicas fazendo poll</strong>. Depois <strong>burle o lock da maildrop de propósito</strong> — processe a mesma mensagem duas vezes — e confirme que o dedup por id de mensagem ainda produz um run. A segunda metade é o teste que importa, porque é o que sobrevive a uma troca de provedor de e-mail.')),
]

DONE = ('Each cron runs <strong>once per tick regardless of replica count</strong>, each schedule fires once with <strong>the queue owning the execution</strong>, the 3AM cluster is staggered, the POP3 poll is deduped by message id, and the two-replica harness exists in the repo so the next person can re-run every control above.',
        'Cada cron roda <strong>uma vez por tick independentemente da contagem de réplicas</strong>, cada agendamento dispara uma vez com <strong>a fila sendo dona da execução</strong>, o bloco das 3h está escalonado, o poll POP3 tem dedup por id de mensagem, e o harness de duas réplicas existe no repositório para a próxima pessoa re-rodar todo controle acima.')

FILES = [
 ('back/src/cronJobs/** (fourteen @Cron sites)', False),
 ('back/src/app-api/mail/mail.service.ts', False),
 ('back/src/app-api/schedule/schedule.controller.ts (create() · update() · delete() · getAllSchedules())', False),
 ('back/src/app-api/schedule/schedule.consumer.ts (retired)', False),
 ('back/src/jobs/apiV2Job/ (the repeatable registration)', False),
 ('back/src/app-api/feature-flags/ (the §3.2 flag — already in production)', False),
 ('docker/devdb/docker-compose.devdb.yaml + the two-replica override', True),
]

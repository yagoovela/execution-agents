# -*- coding: utf-8 -*-
TITLE = ('Make run notifications distributed', 'Tornar as notificações de run distribuídas')

GOAL = ('<b>One delivery mechanism</b> for run events, working across backend replicas.',
        '<b>Um único mecanismo de entrega</b> para eventos de run, funcionando entre réplicas de backend.')

GLANCE = [
 ('crit', ('Severity', 'Severidade'), ('Medium, already latent', 'Média, já latente'),
  ('<code>chatbotSocketByRun</code> is a process-local <code>Map</code>. It blocks horizontal scale, and it does not need the migration to bite. PLAN §6 R11.',
   'O <code>chatbotSocketByRun</code> é um <code>Map</code> local ao processo. Ele bloqueia escala horizontal, e não precisa da migração para morder. PLAN §6 R11.')),
 ('dep', ('Depends on', 'Depende de'), ('Nothing technically', 'Tecnicamente nada'),
  ('But it <strong>must land before B5</strong> — parallel execution multiplies the event rate.',
   'Mas <strong>tem de entrar antes da B5</strong> — a execução paralela multiplica a taxa de eventos.')),
 ('wave', ('Wave', 'Onda'), ('Wave 1', 'Onda 1'),
  ('Wave 1 is the one that makes a second backend replica possible. This is one of the reasons it is not, today.',
   'A onda 1 é a que torna possível uma segunda réplica de backend. Isto é um dos motivos de hoje não ser.')),
 ('ship', ('Rollback', 'Rollback'), ('Behind a flag', 'Atrás de uma flag'),
  ('<strong>The riskiest change in the wave</strong> — a transport change — so the old path stays intact for one cycle.',
   '<strong>A mudança mais arriscada da onda</strong> — troca de transporte — então o caminho antigo fica intacto por um ciclo.')),
]

LEDE = (
 """<p><strong>The socket path is process-local.</strong> <code>chatbotSocketByRun</code> is a plain <code>Map</code> in the backend process (<code>flux.service.ts:2288</code>, registered at <code>:5293–5307</code>, cleaned up at <code>:5392–5395</code>). A run whose socket was registered on replica A <strong>cannot be notified from replica B</strong>.</p>
<p><strong>And there are two mechanisms.</strong> The worker publishes to Redis — <code>room_status_updated</code>, <code>room_stream_chunk</code>, <code>completion_stream_chunk</code> — which the backend relays via <code>@EventPattern</code> to Socket.io; the inline path writes to the socket directly. Two paths to maintain, two places to fix a bug, and they will drift — the same failure this epic is trying to end for dispatch lists.</p>""",
 """<p><strong>O caminho de socket é local ao processo.</strong> O <code>chatbotSocketByRun</code> é um <code>Map</code> comum dentro do processo do backend (<code>flux.service.ts:2288</code>, registrado em <code>:5293–5307</code>, limpo em <code>:5392–5395</code>). Um run cujo socket foi registrado na réplica A <strong>não pode ser notificado a partir da réplica B</strong>.</p>
<p><strong>E existem dois mecanismos.</strong> O worker publica no Redis — <code>room_status_updated</code>, <code>room_stream_chunk</code>, <code>completion_stream_chunk</code> — e o backend repassa via <code>@EventPattern</code> para o Socket.io; o caminho inline escreve direto no socket. Dois caminhos para manter, dois lugares para corrigir um bug, e eles vão divergir — a mesma falha que este épico tenta encerrar nas listas de dispatch.</p>""")

TABLE = {
 'k': 'table',
 'head': [('Piece of the transport', 'Peça do transporte'), ('How it works today', 'Como funciona hoje'),
          ('Verdict', 'Veredito'), ('What that means', 'O que isso significa')],
 'rows': [
  [{'t': ('The inline path', 'O caminho inline')},
   ('Writes straight into the socket held in <code>chatbotSocketByRun</code>',
    'Escreve direto no socket guardado em <code>chatbotSocketByRun</code>'),
   {'t': ('process-local', 'local ao processo'), 'pill': 'no'},
   ('A run registered on replica A cannot be notified from replica B',
    'Um run registrado na réplica A não pode ser notificado a partir da réplica B')],
  [{'t': ('Worker → Redis → <code>@EventPattern</code>', 'Worker → Redis → <code>@EventPattern</code>')},
   ('<code>room_status_updated</code>, <code>room_stream_chunk</code>, <code>completion_stream_chunk</code> (<code>temporal.controller.ts:88–97</code>)',
    '<code>room_status_updated</code>, <code>room_stream_chunk</code>, <code>completion_stream_chunk</code> (<code>temporal.controller.ts:88–97</code>)'),
   {'t': ('crosses processes, not replicas', 'cruza processos, não réplicas'), 'pill': 'weak'},
   ('It is the survivor — but the <em>last</em> hop still ends in one process&#x27;s memory',
    'É o sobrevivente — mas o <em>último</em> salto ainda termina na memória de um processo')],
  [{'t': ('The status strings', 'As strings de status')},
   ('<code>PENDING</code>, <code>RUNNING</code>, <code>COMPLETED</code>, <code>FAILED</code>, <code>CANCELLED</code> as free strings on both sides',
    '<code>PENDING</code>, <code>RUNNING</code>, <code>COMPLETED</code>, <code>FAILED</code>, <code>CANCELLED</code> como strings livres dos dois lados'),
   {'t': ('untyped', 'sem tipo'), 'pill': 'no'},
   ('A typo fails silently, as a status the UI does not recognise',
    'Um erro de digitação falha em silêncio, como um status que a UI não reconhece')],
 ]}

DEC_FANOUT = {
 'k': 'decision', 'id': 'E3-a', 'status': 'open', 'open': True,
 'q': ('What makes any replica able to deliver to a client connected to another?',
       'O que torna qualquer réplica capaz de entregar a um cliente conectado em outra?'),
 'intro': (
  'The spec settles the <em>publish</em> side: everything publishes to Redis, the socket layer only consumes, and the worker&#x27;s existing mechanism is the survivor because it already works across processes. '
  'It does not settle the <em>last hop</em> — it asks for “a Redis adapter for Socket.io, <strong>or an equivalent</strong>”. '
  'That is the open call, and it is the one that decides whether unifying on Redis <strong>solves</strong> the problem or merely <strong>moves</strong> it.',
  'A spec resolve o lado da <em>publicação</em>: tudo publica no Redis, a camada de socket só consome, e o mecanismo existente do worker é o sobrevivente porque já funciona entre processos. '
  'Ela não resolve o <em>último salto</em> — pede “um adapter Redis para Socket.io, <strong>ou equivalente</strong>”. '
  'Essa é a decisão em aberto, e é ela que define se unificar no Redis <strong>resolve</strong> o problema ou apenas o <strong>desloca</strong>.'),
 'opts': [
  {'ltr': 'A', 'pick': True, 'name': ('The Socket.io Redis adapter', 'O adapter Redis do Socket.io'),
   'tag': ('recommended', 'recomendada'),
   'how': ('Every backend replica subscribes through the adapter, so an emit to a room reaches the client whichever replica holds its connection. Rooms replace the hand-rolled map.',
           'Toda réplica de backend assina pelo adapter, então um emit para uma sala alcança o cliente esteja a conexão em que réplica estiver. As salas substituem o mapa feito à mão.'),
   'pros': [('It is the mechanism the socket library ships <strong>for exactly this problem</strong> — there is nothing to design',
             'É o mecanismo que a biblioteca de socket já traz <strong>exatamente para este problema</strong> — não há nada a projetar'),
            ('Redis is already in the path — queues, worker→backend pub/sub, dedup — so there is no new dependency',
             'O Redis já está no caminho — filas, pub/sub worker→backend, dedup — então não há dependência nova'),
            ('It <strong>deletes</strong> the process-local <code>Map</code> rather than distributing it. The map is the bug',
             'Ele <strong>apaga</strong> o <code>Map</code> local ao processo em vez de distribuí-lo. O mapa é o bug')],
   'cons': [('Every replica receives every event and filters, so cost grows with replicas × event rate — and <code>B5</code> raises the event rate on purpose',
             'Toda réplica recebe todo evento e filtra, então o custo cresce com réplicas × taxa de eventos — e a <code>B5</code> aumenta a taxa de propósito'),
            ('It lands on the same Redis instance <code>S8</code> Part 3 is already being asked to size',
             'Cai na mesma instância de Redis que a Parte 3 da <code>S8</code> já está sendo chamada a dimensionar')],
   'cost': [('lo', ('Client effort: <b>none — no payload changes</b>', 'Esforço do cliente: <b>nenhum — sem mudança de payload</b>')),
            ('', ('Ours: <b>one adapter, plus Redis headroom to confirm</b>', 'Nosso: <b>um adapter, mais folga de Redis a confirmar</b>'))]},
  {'ltr': 'B', 'name': ('A run→replica routing table', 'Uma tabela de roteamento run→réplica'),
   'how': ('Keep our own map, but store <em>which replica</em> holds each run&#x27;s socket in Redis, and forward each event to that replica only.',
           'Manter nosso próprio mapa, mas guardar no Redis <em>qual réplica</em> segura o socket de cada run, e encaminhar cada evento só para aquela réplica.'),
   'pros': [('Only the replica that can deliver receives the event, so traffic does not grow with replica count',
             'Só a réplica que pode entregar recebe o evento, então o tráfego não cresce com a contagem de réplicas'),
            ('The shape is familiar — it is <code>chatbotSocketByRun</code> with the process boundary made explicit',
             'O formato é familiar — é o <code>chatbotSocketByRun</code> com a fronteira de processo explícita')],
   'cons': [('<strong>It is writing the adapter ourselves</strong> — reconnection, replica death, stale entries and a client that reconnects elsewhere mid-run all become our bugs',
             '<strong>É escrever o adapter nós mesmos</strong> — reconexão, morte de réplica, entradas obsoletas e um cliente que reconecta em outro lugar no meio do run viram bugs nossos'),
            ('More state to keep correct, for a saving that only matters at a replica count we do not have yet',
             'Mais estado para manter correto, por uma economia que só importa numa contagem de réplicas que ainda não temos')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>an adapter we maintain</b>', 'Nosso: <b>um adapter que nós mantemos</b>'))]},
  {'ltr': 'C', 'name': ('Postgres <code>LISTEN</code>/<code>NOTIFY</code> as the bus', 'Postgres <code>LISTEN</code>/<code>NOTIFY</code> como barramento'),
   'how': ('Publish run events through the database instead of Redis, and have each replica listen on it.',
           'Publicar os eventos de run pelo banco em vez do Redis, e ter cada réplica escutando nele.'),
   'pros': [('One less system in the correctness path, and Postgres is already the system of record',
             'Um sistema a menos no caminho de correção, e o Postgres já é o sistema de registro'),
            ('Events would survive a Redis outage', 'Os eventos sobreviveriam a uma queda do Redis')],
   'cons': [('It puts a high-rate event stream on the database <code>S2</code> calls the first thing that breaks',
             'Coloca um fluxo de eventos de alta taxa no banco que a <code>S2</code> chama de primeira coisa a quebrar'),
            ('<code>NOTIFY</code> payloads are capped, and <code>room_stream_chunk</code> is a stream of content',
             'Payloads de <code>NOTIFY</code> têm limite, e o <code>room_stream_chunk</code> é um fluxo de conteúdo'),
            ('<code>LISTEN</code> holds a <strong>session-level</strong> connection per replica — exactly what the transaction-mode pooler <code>S2</code> recommends does not support',
             'O <code>LISTEN</code> segura uma conexão de <strong>nível de sessão</strong> por réplica — exatamente o que o pooler em modo transação recomendado pela <code>S2</code> não suporta')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>load and a session on the wall S2 is sizing</b>', 'Nosso: <b>carga e uma sessão no teto que a S2 está dimensionando</b>'))]},
  {'ltr': 'D', 'no': True, 'name': ('Sticky sessions', 'Sessões fixadas'),
   'tag': ('not sufficient', 'insuficiente'),
   'how': ('Pin each client to the replica holding its run, so the process-local map keeps working as it does today.',
           'Fixar cada cliente na réplica que segura o run dele, para o mapa local ao processo continuar funcionando como hoje.'),
   'pros': [('No transport change at all — the cheapest thing that appears to work',
             'Nenhuma mudança de transporte — a coisa mais barata que aparenta funcionar')],
   'cons': [('It does not survive a deploy or a restart mid-run, which is precisely when a long run still needs its events',
             'Não sobrevive a um deploy ou restart no meio do run, que é justamente quando um run longo ainda precisa dos eventos dele'),
            ('It makes the load balancer part of the correctness argument, where nothing tests it',
             'Torna o balanceador parte do argumento de correção, num lugar onde nada o testa'),
            ('It does nothing for the worker→backend direction, which is where most events already originate',
             'Não faz nada pela direção worker→backend, que é de onde a maioria dos eventos já vem')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>correctness moves into the load balancer</b>', 'Nosso: <b>a correção migra para o balanceador</b>'))]},
 ],
 'rec': (
  '<p><strong>A.</strong> The rest of this task is already settled — one publish path, the worker&#x27;s mechanism survives, payloads do not change. The only reason this is a decision at all is that the adapter is what makes “publish to Redis” actually <em>reach a client</em>; choosing wrong here ships the transport change without the property it was bought for.</p>'
  '<p><strong>Size it with <code>S8</code>, not after it.</strong> Both tasks are in this wave, both add traffic to the same Redis, and <code>B5</code> multiplies what they add. One number, agreed once.</p>'
  '<p>And it ships <strong>behind a flag with the old path intact for one cycle</strong>. This is the riskiest change in the wave, because a transport that silently drops one class of event looks exactly like a slow run.</p>',
  '<p><strong>A.</strong> O resto desta task já está resolvido — um caminho de publicação, o mecanismo do worker sobrevive, os payloads não mudam. O único motivo de isto ser uma decisão é que o adapter é o que faz “publicar no Redis” de fato <em>chegar a um cliente</em>; escolher errado aqui entrega a troca de transporte sem a propriedade pela qual ela foi comprada.</p>'
  '<p><strong>Dimensione junto com a <code>S8</code>, não depois.</strong> As duas tasks estão nesta onda, as duas somam tráfego ao mesmo Redis, e a <code>B5</code> multiplica o que elas somam. Um número, acordado uma vez.</p>'
  '<p>E entra <strong>atrás de uma flag, com o caminho antigo intacto por um ciclo</strong>. Esta é a mudança mais arriscada da onda, porque um transporte que descarta em silêncio uma classe de evento parece exatamente um run lento.</p>'),
 'who': [('Engineering', 'Engenharia'),
         ('Infra confirms the Redis headroom', 'Infra confirma a folga do Redis')],
}

PARTS = [
{'n': '1',
 'title': ('One publish path, and a socket layer that only consumes', 'Um caminho de publicação, e uma camada de socket que só consome'),
 'loc': 'flux.service.ts:2288, 5293–5307, 5392–5395',
 'purpose': ('Collapse two mechanisms into one, so a bug has one place to be fixed instead of two places to drift.',
             'Colapsar dois mecanismos em um, para que um bug tenha um lugar para ser corrigido em vez de dois para divergir.'),
 'body': (
  '<p>Two mechanisms exist today. The worker publishes to Redis — <code>room_status_updated</code>, <code>room_stream_chunk</code>, <code>completion_stream_chunk</code> — which the backend relays via <code>@EventPattern</code> to Socket.io. The inline path writes to the socket directly.</p>'
  '<p>Two paths means two places to maintain and two places to fix a bug, and <strong>they will drift</strong> — the same failure this epic is trying to end for dispatch lists.</p>',
  '<p>Hoje existem dois mecanismos. O worker publica no Redis — <code>room_status_updated</code>, <code>room_stream_chunk</code>, <code>completion_stream_chunk</code> — e o backend repassa via <code>@EventPattern</code> para o Socket.io. O caminho inline escreve direto no socket.</p>'
  '<p>Dois caminhos significam dois lugares para manter e dois para corrigir um bug, e <strong>eles vão divergir</strong> — a mesma falha que este épico tenta encerrar nas listas de dispatch.</p>'),
 'body2': (
  '<p><strong>The worker&#x27;s mechanism is the survivor.</strong> It already works across processes, which is the property being bought. Everything publishes to Redis; the socket layer only consumes.</p>',
  '<p><strong>O mecanismo do worker é o sobrevivente.</strong> Ele já funciona entre processos, e é essa a propriedade que está sendo comprada. Tudo publica no Redis; a camada de socket só consome.</p>'),
 'ba': (('Two mechanisms. <code>chatbotSocketByRun</code> is a plain <code>Map</code> in the backend process (<code>:2288</code>), registered at <code>:5293–5307</code> and cleaned up at <code>:5392–5395</code>, and the inline path writes into it directly.',
         'Dois mecanismos. O <code>chatbotSocketByRun</code> é um <code>Map</code> comum no processo do backend (<code>:2288</code>), registrado em <code>:5293–5307</code> e limpo em <code>:5392–5395</code>, e o caminho inline escreve nele direto.'),
        ('One publish path. The inline path&#x27;s direct socket writes are <strong>gone, not merely unused</strong>, and the socket layer has one job.',
         'Um caminho de publicação. As escritas diretas no socket do caminho inline estão <strong>apagadas, não apenas sem uso</strong>, e a camada de socket tem uma função só.'))},
{'n': '2',
 'title': ('The last hop is the part that is still process-local', 'O último salto é a parte que continua local ao processo'),
 'loc': 'back/src/app-api/gateway/gateway.ts:69, 76',
 'purpose': ('Make the delivery step replica-independent, so unifying on Redis solves the problem instead of moving it.',
             'Tornar o passo de entrega independente de réplica, para que unificar no Redis resolva o problema em vez de deslocá-lo.'),
 'body': (
  '<p>Publishing to Redis crosses the <strong>worker → backend</strong> boundary. It does not cross the <strong>backend replica → client</strong> one: a run whose socket was registered on replica A still cannot be notified from replica B, because the connection lives in one process&#x27;s memory.</p>'
  '<p>That is why the spec asks for an adapter, or an equivalent, in the same breath: <em>without it, unifying on Redis moves the problem rather than solving it.</em></p>',
  '<p>Publicar no Redis cruza a fronteira <strong>worker → backend</strong>. Não cruza a fronteira <strong>réplica de backend → cliente</strong>: um run cujo socket foi registrado na réplica A continua sem poder ser notificado a partir da réplica B, porque a conexão vive na memória de um processo.</p>'
  '<p>É por isso que a spec pede um adapter, ou equivalente, no mesmo fôlego: <em>sem ele, unificar no Redis desloca o problema em vez de resolvê-lo.</em></p>'),
 'ba': (('A run registered on replica A cannot be notified from replica B. It is a blocker for horizontal scale, and it is <strong>already latent</strong> — it does not need the worker migration to bite.',
         'Um run registrado na réplica A não pode ser notificado a partir da réplica B. É um bloqueio para escala horizontal, e já está <strong>latente</strong> — não precisa da migração do worker para morder.'),
        ('Any replica can deliver to any connected client, and the process-local map stops being the thing that decides who can be reached.',
         'Qualquer réplica pode entregar a qualquer cliente conectado, e o mapa local ao processo deixa de ser o que decide quem pode ser alcançado.'))},
{'n': '3',
 'title': ('Type the status strings', 'Tipar as strings de status'),
 'loc': 'worker/src/modules/notification/notification.service.ts · temporal.controller.ts:88–97',
 'purpose': ('Make a typo across the process boundary a compile error instead of a status the UI silently ignores.',
             'Fazer de um erro de digitação atravessando a fronteira de processo um erro de compilação em vez de um status que a UI ignora em silêncio.'),
 'body': (
  '<p><code>&#x27;PENDING&#x27; | &#x27;RUNNING&#x27; | &#x27;COMPLETED&#x27; | &#x27;FAILED&#x27; | &#x27;CANCELLED&#x27;</code> are free strings on <strong>both sides of a process boundary</strong> today — the worst place for a typo, because it fails silently as a status the UI does not recognise.</p>',
  '<p><code>&#x27;PENDING&#x27; | &#x27;RUNNING&#x27; | &#x27;COMPLETED&#x27; | &#x27;FAILED&#x27; | &#x27;CANCELLED&#x27;</code> são strings livres nos <strong>dois lados de uma fronteira de processo</strong> hoje — o pior lugar para um erro de digitação, porque falha em silêncio como um status que a UI não reconhece.</p>'),
 'ba': (('A misspelled status crosses the boundary, is relayed, is delivered, and disappears at the last step — with no error raised anywhere along the way.',
         'Um status escrito errado cruza a fronteira, é repassado, é entregue, e some no último passo — sem nenhum erro levantado no caminho.'),
        ('One shared union on both sides. A misspelled status does not compile.',
         'Uma união compartilhada nos dois lados. Um status escrito errado não compila.')),
 'callouts': [('mig', ('Out of scope — the payloads', 'Fora de escopo — os payloads'),
   ('<p>Changing the event payloads the front consumes. <strong>This is a transport change</strong>; a payload change in the same task would make a regression impossible to attribute.</p>',
    '<p>Mudar os payloads de evento que o front consome. <strong>Isto é uma troca de transporte</strong>; uma mudança de payload na mesma task tornaria impossível atribuir uma regressão.</p>'))]},
]

VERIF = [
 (True, ('Negative control', 'Controle negativo'),
  ('Register a run&#x27;s socket on one replica and emit from another; assert the client receives it. Run that test <strong>before</strong> the change and watch it fail — <strong>that failure is the bug</strong>, and demonstrating it is what justifies the work.',
   'Registre o socket de um run numa réplica e emita de outra; verifique que o cliente recebe. Rode esse teste <strong>antes</strong> da mudança e veja-o falhar — <strong>essa falha é o bug</strong>, e demonstrá-la é o que justifica o trabalho.')),
 (False, ('Ordering per node under parallel dispatch', 'Ordenação por node sob dispatch paralelo'),
  ('A node&#x27;s <code>RUNNING</code> must never arrive after its <code>COMPLETED</code>. Worth asserting explicitly, because <strong>parallelism is what makes it possible</strong>.',
   'O <code>RUNNING</code> de um node nunca pode chegar depois do <code>COMPLETED</code> dele. Vale afirmar explicitamente, porque <strong>é o paralelismo que torna isso possível</strong>.')),
 (False, ('No lost events with several nodes streaming', 'Nenhum evento perdido com vários nodes transmitindo'),
  ('With several nodes streaming at once, <strong>count emitted versus received</strong>. A transport that drops under load looks exactly like a slow run, which is why the count has to be explicit.',
   'Com vários nodes transmitindo ao mesmo tempo, <strong>conte emitidos contra recebidos</strong>. Um transporte que descarta sob carga parece exatamente um run lento, e é por isso que a contagem precisa ser explícita.')),
 (False, ('The inline writes are gone, not merely unused', 'As escritas inline foram apagadas, não apenas deixadas sem uso'),
  ('Confirm the inline path&#x27;s direct socket writes were <strong>deleted</strong>. A second path that is unreachable today is a second path someone reaches tomorrow.',
   'Confirme que as escritas diretas no socket do caminho inline foram <strong>apagadas</strong>. Um segundo caminho inalcançável hoje é um segundo caminho que alguém alcança amanhã.')),
]

DONE = ('<strong>One publish path</strong>, delivery works across replicas, statuses are <strong>typed</strong>, and ordering holds under parallel dispatch.',
        '<strong>Um caminho de publicação</strong>, a entrega funciona entre réplicas, os status são <strong>tipados</strong>, e a ordenação se mantém sob dispatch paralelo.')

FILES = [
 ('back/src/app-api/gateway/gateway.ts:69, 76', False),
 ('back/src/temporal/temporal.controller.ts:88–97', False),
 ('back/src/app-api/flux/flux.service.ts:2288, 5293–5307, 5392–5395', False),
 ('worker/src/modules/notification/notification.service.ts', False),
 ('a shared run-status union', True),
]

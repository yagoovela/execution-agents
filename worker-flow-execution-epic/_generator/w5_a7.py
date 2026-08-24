# -*- coding: utf-8 -*-
TITLE = ('Migrate <code>nodesBox</code> (Object Caller)', 'Migrar o <code>nodesBox</code> (Object Caller)')

GOAL = ('Migrate the one mutating node whose logic is actually extractable — behind two new callbacks and an <b>explicit ordering guarantee</b>.',
        'Migrar o único node mutante cuja lógica é de fato extraível — atrás de dois novos callbacks e de uma <b>garantia explícita de ordem</b>.')

GLANCE = [
 ('crit', ('Severity','Severidade'), ('High — R5','Alta — R5'),
  ('The engine serialises object access through one in-memory array today; parallel activities do not. PLAN §6, R5.',
   'Hoje o motor serializa o acesso ao objeto por um array em memória; activities paralelas não. PLAN §6, R5.')),
 ('dep', ('Depends on','Depende de'), ('A1 · B1','A1 · B1'),
  ('<strong>Do not start before B1</strong> — this node&#x27;s correctness depends on knowing which execution a write belongs to.',
   '<strong>Não comece antes da B1</strong> — a corretude deste node depende de saber a qual execução uma escrita pertence.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('It sits with the parallel model, because ordering only becomes a problem once siblings run concurrently.',
   'Fica junto do modelo paralelo, porque a ordem só vira problema quando irmãos rodam concorrentemente.')),
 ('ship', ('Shape','Formato'), ('~130 lines + two contracts','~130 linhas + dois contratos'),
  ('Its own logic is about 130 lines. <strong>The work is entirely in what has to exist around it.</strong>',
   'A lógica própria tem cerca de 130 linhas. <strong>O trabalho está inteiro no que precisa existir ao redor.</strong>')),
]

LEDE = (
 '<p>Today <code>nodesBox</code> reads <code>data.selectedId</code> against <code>objectCallerData</code> — the engine&#x27;s in-memory array for the run — '
 'reads the latest session state for <code>{scopeType:&#x27;object&#x27;, scopeId, sessionKey, ownerUserId}</code>, then reads and/or writes the object&#x27;s '
 'content and publishes the change back through <code>onMutateObjectCallerData</code> so later nodes see it. '
 'Handler at <code>flux.service.ts:6834</code>; call sites <code>:1370</code>, <code>:2580</code>, <code>:3575</code>, <code>:4146</code>.</p>'
 '<p>It is the only one of the five mutating nodes with extractable logic. <code>conditionNode</code>, <code>arrayNode</code>, <code>fluxBox</code> and '
 '<code>libraryNode</code> are <strong>control flow</strong> — they decide what runs next, and belong in the workflow (<code>B6</code>). '
 '<strong><code>nodesBox</code> mutates data, not control</strong> (analysis §3.5).</p>',
 '<p>Hoje o <code>nodesBox</code> resolve <code>data.selectedId</code> contra o <code>objectCallerData</code> — o array em memória do motor para aquele run — '
 'lê o estado de sessão mais recente para <code>{scopeType:&#x27;object&#x27;, scopeId, sessionKey, ownerUserId}</code>, e então lê e/ou escreve o conteúdo '
 'do objeto e publica a mudança de volta via <code>onMutateObjectCallerData</code> para que nodes posteriores a enxerguem. '
 'Handler em <code>flux.service.ts:6834</code>; pontos de chamada <code>:1370</code>, <code>:2580</code>, <code>:3575</code>, <code>:4146</code>.</p>'
 '<p>É o único dos cinco nodes mutantes com lógica extraível. <code>conditionNode</code>, <code>arrayNode</code>, <code>fluxBox</code> e '
 '<code>libraryNode</code> são <strong>controle de fluxo</strong> — decidem o que roda em seguida, e pertencem ao workflow (<code>B6</code>). '
 '<strong>O <code>nodesBox</code> muta dado, não controle</strong> (análise §3.5).</p>')

TABLE = dict(
 head=[('Mutating node','Node mutante'),('What it changes','O que ele muda'),('Where it goes','Para onde vai'),('Why','Por quê')],
 rows=[
  [{'t':'conditionNode','mono':True},
   ('The engine&#x27;s work queue','A fila de trabalho do motor'),
   {'t':('B6 — workflow control flow','B6 — controle de fluxo no workflow'),'pill':'weak'},
   ('An activity&#x27;s return value cannot reshape the caller&#x27;s iteration.','O retorno de uma activity não consegue remodelar a iteração de quem a chamou.')],
  [{'t':'arrayNode','mono':True},
   ('Which slice of the node list re-executes','Qual fatia da lista de nodes re-executa'),
   {'t':('B6 — a workflow loop','B6 — um laço de workflow'),'pill':'weak'},
   ('Same reason: it decides what runs next, it does not compute a value.','Mesma razão: decide o que roda em seguida, não calcula um valor.')],
  [{'t':'fluxBox','mono':True},
   ('Runs another whole flow','Roda um outro fluxo inteiro'),
   {'t':('B6 — a child workflow','B6 — um child workflow'),'pill':'weak'},
   ('It is a run inside a run, with its own logs, cancel key and counters.','É um run dentro de um run, com logs, chave de cancelamento e contadores próprios.')],
  [{'t':'libraryNode','mono':True},
   ('Structurally the same as <code>fluxBox</code>','Estruturalmente igual ao <code>fluxBox</code>'),
   {'t':('B6 — with <code>fluxBox</code>, as one unit','B6 — junto do <code>fluxBox</code>, como uma unidade'),'pill':'weak'},
   ('The engine already treats them together; splitting them writes the contract twice.','O motor já os trata juntos; separá-los escreve o contrato duas vezes.')],
  [{'t':'nodesBox','mono':True},
   ('<strong>Object content and object-scoped session state</strong>','<strong>Conteúdo de objeto e estado de sessão com escopo de objeto</strong>'),
   {'t':('A7 — an activity','A7 — uma activity'),'pill':'ok'},
   ('<strong>It mutates data, not control</strong> — so it has a return value, and a contract can be written for it.','<strong>Ele muta dado, não controle</strong> — então tem valor de retorno, e um contrato pode ser escrito para ele.')],
 ])

PROSE = (
 'One call, and the spec names it outright: <em>pick one and state why</em>. It is the item the analysis says will be underestimated, '
 'and the one PLAN §6 tracks as risk <code>R5</code>.',
 'Uma decisão, e a spec a nomeia sem rodeios: <em>escolha uma e diga por quê</em>. É o item que a análise diz que será subestimado, '
 'e o que o PLAN §6 acompanha como risco <code>R5</code>.')

DEC_ORDERING = {
 'k':'decision','id':'A7-a','status':'rec','open':True,
 'q':('Advisory lock, or an idempotent activity, for two Object Callers on the same object?',
      'Advisory lock, ou activity idempotente, para dois Object Callers no mesmo objeto?'),
 'intro':(
  'Today the engine serialises <strong>every</strong> Object Caller in a run through one in-memory array. Once they are independent activities that '
  'serialisation is gone, and two callers touching the same object have no order at all. The spec offers exactly two acceptable answers and says '
  '<strong>“pick one and state why — do not ship without addressing it and hope the ordering holds.”</strong> '
  'One constraint narrows the menu before it opens: <strong>changing object semantics is explicitly out of scope</strong>.',
  'Hoje o motor serializa <strong>todo</strong> Object Caller de um run por um único array em memória. Quando eles viram activities independentes essa '
  'serialização some, e dois callers tocando o mesmo objeto não têm ordem alguma. A spec oferece exatamente duas respostas aceitáveis e diz '
  '<strong>“escolha uma e diga por quê — não entregue sem tratar isso e torcer para a ordem se manter.”</strong> '
  'Uma restrição estreita o menu antes de ele abrir: <strong>mudar a semântica de objeto está explicitamente fora de escopo</strong>.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('<code>pg_advisory_xact_lock</code> per object','<code>pg_advisory_xact_lock</code> por objeto'),
   'tag':('recommended','recomendada'),
   'how':('The activity takes a transaction-scoped advisory lock keyed by the object before its read-modify-write, so two Object Callers on the same '
          'object serialise. The pattern is already in the worker — <code>third-party-integration/oauth-token.repo.ts:7</code>.',
          'A activity toma um advisory lock com escopo de transação, chaveado pelo objeto, antes do read-modify-write, de modo que dois Object Callers '
          'no mesmo objeto serializam. O padrão já existe no worker — <code>third-party-integration/oauth-token.repo.ts:7</code>.'),
   'pros':[('It is a <strong>working pattern already in this codebase</strong>, not a design — review §6 lists it as something to keep',
            'É um <strong>padrão que já funciona neste código</strong>, não um projeto — a review §6 o lista como algo a preservar'),
           ('It becomes the ordering authority the in-memory array used to be, which is precisely what is being removed',
            'Torna-se a autoridade de ordem que o array em memória era, que é exatamente o que está sendo removido'),
           ('It can be tested <strong>deterministically</strong> — hold the lock explicitly in the test instead of racing on timing',
            'Pode ser testado <strong>deterministicamente</strong> — segure o lock explicitamente no teste em vez de correr contra o relógio'),
           ('Object semantics are untouched: read, transform, write back still means what it means today',
            'A semântica de objeto fica intocada: ler, transformar e escrever de volta continua significando o que significa hoje')],
   'cons':[('It holds a database lock inside an activity, so a slow write holds a connection — the resource <code>S2</code> just finished sizing',
            'Segura um lock de banco dentro de uma activity, então uma escrita lenta segura uma conexão — o recurso que a <code>S2</code> acabou de dimensionar'),
           ('Held around an external call it becomes a fleet-wide stall, so the boundary has to be drawn tightly and on purpose',
            'Segurado em volta de uma chamada externa vira uma parada em toda a frota, então a fronteira precisa ser desenhada de forma estreita e deliberada')],
   'cost':[('lo',('Client sees: <b>the order they have today</b>','Cliente vê: <b>a ordem que ele já tem hoje</b>')),
           ('',('Ours: <b>one lock on the S2 budget</b>','Nosso: <b>um lock sobre o orçamento da S2</b>'))]},
  {'ltr':'B','name':('An idempotent activity','Uma activity idempotente'),
   'how':('Express the write so repeating it or re-ordering it converges to the same object — an append or a keyed merge rather than a read-modify-write.',
          'Expressar a escrita de modo que repeti-la ou reordená-la convirja para o mesmo objeto — um append ou um merge chaveado em vez de read-modify-write.'),
   'pros':[('No lock, no held connection, and activity retries stop being a hazard — the platform retries by design',
            'Sem lock, sem conexão presa, e os retries de activity deixam de ser um perigo — a plataforma tenta de novo por projeto'),
           ('It is the answer that scales without a coordination point, if the node can be expressed that way',
            'É a resposta que escala sem ponto de coordenação, se o node puder ser expresso assim')],
   'cons':[('<strong>Object Caller reads the object, transforms it and writes it back</strong> — that composition is not idempotent, and making it so '
            'means changing what the node does',
            '<strong>O Object Caller lê o objeto, transforma e escreve de volta</strong> — essa composição não é idempotente, e torná-la idempotente '
            'significa mudar o que o node faz'),
           ('Changing object semantics is <strong>explicitly out of scope</strong> for this task, so this option needs its own product decision first',
            'Mudar a semântica de objeto está <strong>explicitamente fora de escopo</strong> nesta task, então esta opção precisa antes de uma decisão de produto própria')],
   'cost':[('hi',('Client risk: <b>the node changes meaning</b>','Risco do cliente: <b>o node muda de significado</b>')),
           ('hi',('Ours: <b>a product decision first</b>','Nosso: <b>uma decisão de produto antes</b>'))]},
  {'ltr':'C','no':True,'name':('Ship it and hope the ordering holds','Entregar e torcer para a ordem se manter'),
   'tag':('rejected by the spec','rejeitada pela spec'),
   'how':('Migrate the node without an ordering answer, on the grounds that two Object Callers on one object in one flow is rare.',
          'Migrar o node sem resposta de ordem, sob o argumento de que dois Object Callers no mesmo objeto num mesmo fluxo é raro.'),
   'pros':[('Ships the fastest, and most flows will never notice','Entrega mais rápido, e a maioria dos fluxos nunca vai notar')],
   'cons':[('The spec forbids it in as many words, and <code>R5</code> exists because someone already predicted this failure',
            'A spec proíbe isso com todas as letras, e o <code>R5</code> existe porque alguém já previu essa falha'),
           ('The failure is a <strong>silently wrong object</strong>, discovered later by a customer, with no error to trace back',
            'A falha é um <strong>objeto silenciosamente errado</strong>, descoberto depois por um cliente, sem erro para rastrear')],
   'cost':[('hi',('Client risk: <b>a silently wrong object</b>','Risco do cliente: <b>um objeto silenciosamente errado</b>')),
           ('hi',('Ours: <b>an unreproducible bug report</b>','Nosso: <b>um relato de bug irreproduzível</b>'))]},
 ],
 'rec':(
  '<p><strong>A — the advisory lock — and write the rationale into the task file, because the spec&#x27;s definition of done asks for exactly that.</strong> '
  'The deciding argument is not that locks are elegant; it is that <code>B</code> requires changing what Object Caller means, and this task says it will not.</p>'
  '<p>Draw the lock boundary on purpose: <strong>around the read-modify-write only, never around a provider call.</strong> '
  'A lock held across an external request turns a slow API into a fleet-wide stall, and it consumes a connection from the budget <code>S2</code> just sized.</p>',
  '<p><strong>A — o advisory lock — e escreva a justificativa no arquivo da task, porque a definição de pronto da spec pede exatamente isso.</strong> '
  'O argumento decisivo não é que locks sejam elegantes; é que a <code>B</code> exige mudar o que o Object Caller significa, e esta task diz que não vai.</p>'
  '<p>Desenhe a fronteira do lock de propósito: <strong>só em volta do read-modify-write, nunca em volta de uma chamada a provedor.</strong> '
  'Um lock segurado durante uma requisição externa transforma uma API lenta numa parada de frota inteira, e consome uma conexão do orçamento que a <code>S2</code> acabou de dimensionar.</p>'),
 'who':[('Engineering','Engenharia'),('Product only if B is reopened','Produto apenas se a B for reaberta')],
}

PARTS = [
{'n':'1','title':('An object-state callback','Um callback de estado de objeto'),
 'loc':'back/src/temporal/worker.controller.ts',
 'purpose':('Give the worker read and write access to object content without inventing a new contract shape.',
            'Dar ao worker acesso de leitura e escrita ao conteúdo do objeto sem inventar um novo formato de contrato.'),
 'body':('<p>The first of the two contracts that have to exist before the node can move: a read-and-write callback exposing '
         '<code>objectsService</code>. The spec is specific about the shape — <strong>model it on the existing <code>/worker/store-payload</code> '
         'contract rather than inventing one</strong>. A new shape here is a fifth thing for the next person to learn.</p>',
         '<p>O primeiro dos dois contratos que precisam existir antes de o node se mover: um callback de leitura e escrita expondo o '
         '<code>objectsService</code>. A spec é específica sobre o formato — <strong>espelhe o contrato existente do <code>/worker/store-payload</code> '
         'em vez de inventar um</strong>. Um formato novo aqui é mais uma coisa para a próxima pessoa aprender.</p>'),
 'ba':(('The handler reaches <code>objectsService</code> directly, in process, through the engine&#x27;s <code>objectCallerData</code> array.',
        'O handler alcança o <code>objectsService</code> diretamente, no mesmo processo, pelo array <code>objectCallerData</code> do motor.'),
       ('The activity reads and writes object content through a callback with a stated contract — the same boundary every other worker node already uses.',
        'A activity lê e escreve conteúdo de objeto por um callback com contrato declarado — a mesma fronteira que todo outro node do worker já usa.'))},

{'n':'2','title':('A session-state callback','Um callback de estado de sessão'),
 'loc':'back/src/app-api/session_state/',
 'purpose':('Mirror <code>readLatest</code> and <code>appendEntries</code> for the <code>object</code> scope, with the same semantics the inline path has.',
            'Espelhar <code>readLatest</code> e <code>appendEntries</code> para o escopo <code>object</code>, com a mesma semântica do caminho inline.'),
 'body':('<p>The second contract mirrors <code>sessionStateService.readLatest</code> and <code>appendEntries</code> for the <code>object</code> scope. '
         'The key the node reads with today is <code>{scopeType:&#x27;object&#x27;, scopeId, sessionKey, ownerUserId}</code>, and all four parts of it have '
         'to survive the crossing — a callback that drops <code>ownerUserId</code> reads someone else&#x27;s session.</p>'
         '<p>Parity here is checkable against real data, and the verification section says to check it that way: the callback must produce '
         '<strong>the same rows the inline path produces, on real stored objects</strong>.</p>',
         '<p>O segundo contrato espelha <code>sessionStateService.readLatest</code> e <code>appendEntries</code> para o escopo <code>object</code>. '
         'A chave com que o node lê hoje é <code>{scopeType:&#x27;object&#x27;, scopeId, sessionKey, ownerUserId}</code>, e as quatro partes dela precisam '
         'sobreviver à travessia — um callback que perde o <code>ownerUserId</code> lê a sessão de outra pessoa.</p>'
         '<p>A paridade aqui é verificável contra dado real, e a seção de verificação manda checar assim: o callback precisa produzir '
         '<strong>as mesmas linhas que o caminho inline produz, em objetos reais já armazenados</strong>.</p>'),
 'ba':(('Session state is read and appended in the same process that runs the node, so scoping is whatever the call site passed.',
        'O estado de sessão é lido e anexado no mesmo processo que roda o node, então o escopo é o que o ponto de chamada passou.'),
       ('The scope is carried explicitly across the callback, and parity with the inline path is proved on stored objects rather than assumed.',
        'O escopo atravessa o callback explicitamente, e a paridade com o caminho inline é provada em objetos armazenados em vez de suposta.'))},

{'n':'3','title':('Ordering — the part that will be underestimated','Ordem — a parte que será subestimada'),
 'loc':'flux.service.ts:6834 · oauth-token.repo.ts:7',
 'purpose':('Whatever replaces <code>objectCallerData</code> has to be the ordering authority, or the node has to become idempotent.',
            'O que substituir o <code>objectCallerData</code> precisa ser a autoridade de ordem, ou o node precisa se tornar idempotente.'),
 'body':('<p>The in-memory array was doing more than caching. It was <strong>the run&#x27;s ordering authority</strong>: every Object Caller in the run went '
         'through it, one at a time, in the process that owned the loop. That property is not written down anywhere and it disappears silently the moment '
         'the node becomes an activity.</p>'
         '<p>The analysis is direct about it: of the three things a worker activity would need here, <strong>item 3 is the one that will be '
         'underestimated</strong> (§3.5). The two callbacks are contracts; this is a concurrency property.</p>',
         '<p>O array em memória fazia mais que cachear. Ele era <strong>a autoridade de ordem do run</strong>: todo Object Caller daquele run passava '
         'por ele, um de cada vez, no processo dono do laço. Essa propriedade não está escrita em lugar nenhum e desaparece em silêncio no momento em '
         'que o node vira uma activity.</p>'
         '<p>A análise é direta: das três coisas que uma activity de worker precisaria aqui, <strong>o item 3 é o que será subestimado</strong> (§3.5). '
         'Os dois callbacks são contratos; este é uma propriedade de concorrência.</p>'),
 'ba':(('Two Object Callers on the same object are ordered by accident — because one process holds one array and runs one node at a time.',
        'Dois Object Callers no mesmo objeto são ordenados por acidente — porque um processo segura um array e roda um node por vez.'),
       ('The chosen mechanism is the ordering authority, it is <strong>written down with its rationale</strong>, and a deterministic test proves it holds.',
        'O mecanismo escolhido é a autoridade de ordem, está <strong>registrado com sua justificativa</strong>, e um teste determinístico prova que vale.')),
 'callouts':[('mig',('Out of scope','Fora de escopo'),
   ('<p>Changing object semantics, session-state scoping, or the chat behaviour built on it. '
    'The chat path — <code>fluxObject</code> / <code>nodesBox</code> with chat enabled — is written at <strong>run finalisation</strong> '
    '(<code>flux.service.ts:5222</code>), outside this node, and must be unaffected.</p>',
    '<p>Mudar a semântica de objeto, o escopo do estado de sessão, ou o comportamento de chat construído sobre isso. '
    'O caminho de chat — <code>fluxObject</code> / <code>nodesBox</code> com chat habilitado — é escrito na <strong>finalização do run</strong> '
    '(<code>flux.service.ts:5222</code>), fora deste node, e precisa ficar intacto.</p>'))]},
]

VERIF = [
 (True, ('Negative control — remove the guarantee first','Controle negativo — remova a garantia primeiro'),
  ('Remove the ordering guarantee and write a test that runs <strong>two Object Callers against the same object concurrently</strong>, asserting the final content. '
   'Watch it go red. An intermittent test is not acceptable here, so <strong>make the race deterministic by holding the lock explicitly in the test</strong> '
   'rather than relying on timing.',
   'Remova a garantia de ordem e escreva um teste que roda <strong>dois Object Callers no mesmo objeto de forma concorrente</strong>, afirmando o conteúdo final. '
   'Veja o teste ficar vermelho. Um teste intermitente não é aceitável aqui, então <strong>torne a corrida determinística segurando o lock explicitamente no teste</strong> '
   'em vez de depender do relógio.')),
 (True, ('Session-state parity, on real objects','Paridade de estado de sessão, em objetos reais'),
  ('<code>readLatest</code> and <code>appendEntries</code> through the callback must produce <strong>the same rows the inline path produces</strong>, '
   'checked on real stored objects — not on a fixture built to match.',
   'O <code>readLatest</code> e o <code>appendEntries</code> pelo callback precisam produzir <strong>as mesmas linhas que o caminho inline produz</strong>, '
   'verificado em objetos reais já armazenados — não numa fixture montada para casar.')),
 (False, ('The chat path is untouched','O caminho de chat fica intocado'),
  ('<code>fluxObject</code> / <code>nodesBox</code> with chat enabled is written at run finalisation (<code>flux.service.ts:5222</code>), outside this node. '
   'Confirm it still behaves identically — it is the easiest thing on this page to break without noticing.',
   'O <code>fluxObject</code> / <code>nodesBox</code> com chat habilitado é escrito na finalização do run (<code>flux.service.ts:5222</code>), fora deste node. '
   'Confirme que continua idêntico — é a coisa mais fácil desta página de quebrar sem perceber.')),
 (False, ('The inline handler is deleted, not parked','O handler inline é apagado, não estacionado'),
  ('Per <code>C1</code>: the handler at <code>:6834</code> and its four dispatch sites go, and the <code>A1</code> registry entry loses <code>hasInlineTwin</code>. '
   'A node with two implementations is a double-execution risk, not a safety net.',
   'Conforme a <code>C1</code>: o handler em <code>:6834</code> e seus quatro pontos de dispatch saem, e a entrada no registro da <code>A1</code> perde o <code>hasInlineTwin</code>. '
   'Um node com duas implementações é risco de dupla execução, não rede de segurança.')),
]

DONE = ('<code>nodesBox</code> satisfies <code>PLAN §3.4</code>; both callbacks exist and are documented in <code>D1</code>; '
        'the <strong>ordering decision is recorded with its rationale</strong>; and the inline handler is deleted.',
        'O <code>nodesBox</code> satisfaz o <code>PLAN §3.4</code>; os dois callbacks existem e estão documentados na <code>D1</code>; '
        'a <strong>decisão de ordem está registrada com sua justificativa</strong>; e o handler inline foi apagado.')

FILES = [('back/src/app-api/flux/flux.service.ts:6834 (+ call sites :1370, :2580, :3575, :4146)', False),
         ('back/src/temporal/worker.controller.ts (new callbacks)', True),
         ('back/src/app-api/objects/', False),
         ('back/src/app-api/session_state/', False),
         ('worker/src/modules/nodes/object-caller/', True),
         ('the A1 registry', False)]

# -*- coding: utf-8 -*-
TITLE = ('Migrate <code>nodesBox</code> (Object Caller)', 'Migrar o <code>nodesBox</code> (Object Caller)')

GOAL = ('Migrate the one mutating node whose logic is actually extractable, with an execution record and an explicit ordering guarantee — '
        'and make every <code>worker</code> type reachable from both back loops.',
        'Migrar o único node mutante cuja lógica é de fato extraível, com registro de execução e garantia explícita de ordem — '
        'e tornar todo tipo <code>worker</code> alcançável pelos dois laços do back.')

GLANCE = [
 ('crit', ('Found in review','Achado da revisão'), ('No write, no record','Sem escrita, sem registro'),
  ('<code>objectCaller</code> never writes <code>flow_objects</code>, and <code>node_executions</code> holds no <code>nodesBox</code> row. Scope widened 2026-10-23.',
   '<code>objectCaller</code> nunca escreve em <code>flow_objects</code>, e <code>node_executions</code> não tem linha de <code>nodesBox</code>. Escopo ampliado em 2026-10-23.')),
 ('dep', ('Depends on','Depende de'), ('A1 · B1 · B4','A1 · B1 · B4'),
  ('B1 is in production. The B4 flag is in back <code>main</code>; <strong>A7&#x27;s worker PR waits for B4 worker on <code>main</code></strong> (A7-D4).',
   'A B1 está em produção. A flag da B4 está no <code>main</code> do back; <strong>o PR de worker da A7 espera a B4 worker no <code>main</code></strong> (A7-D4).')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('It sits with the parallel model: once B5 dispatches a batch, two callers of one object need a defined order.',
   'Fica junto do modelo paralelo: quando a B5 despachar um lote, dois callers do mesmo objeto precisam de ordem definida.')),
 ('ship', ('Estimate','Estimativa'), ('96 h proposed — was 40 h','96 h propostas — eram 40 h'),
  ('The 40 hours assumed two callbacks only. The widened scope adds the record, the implicit edges, the read switch and the registry-driven dispatch. The 96 hours are proposed and not yet in ClickUp.',
   'As 40 horas supunham só dois callbacks. O escopo ampliado soma o registro, as arestas implícitas, a troca de leitura e o dispatch pelo registro. As 96 horas são uma proposta e ainda não estão no ClickUp.')),
]

LEDE = (
 '<p>Today <code>nodesBox</code> reads <code>data.selectedId</code> against <code>objectCallerData</code> — the engine&#x27;s in-memory array for the run — '
 'reads the latest session state for <code>{scopeType:&#x27;object&#x27;, scopeId, sessionKey, ownerUserId}</code>, then writes the object&#x27;s content and '
 'publishes it through <code>onMutateObjectCallerData</code>. It mutates <strong>data, not control</strong>, unlike <code>conditionNode</code>, <code>arrayNode</code>, '
 '<code>fluxBox</code> and <code>libraryNode</code>, which belong in the workflow (B6).</p>'
 '<p>The review on 2026-10-23 found that <strong>no object write exists</strong> — a write lives only in that array — and that no execution record exists either, '
 'so the value a run used cannot be recovered. It found four entry paths, not three, and a race <strong>across runs</strong>, not only across branches. '
 'It also found that the back&#x27;s loops skip or inline several <code>worker</code> types, so that work moved here from the coverage audit&#x27;s A12.</p>',
 '<p>Hoje o <code>nodesBox</code> resolve <code>data.selectedId</code> contra o <code>objectCallerData</code> — o array em memória do motor para o run — '
 'lê o estado de sessão mais recente para <code>{scopeType:&#x27;object&#x27;, scopeId, sessionKey, ownerUserId}</code>, escreve o conteúdo do objeto e '
 'o publica via <code>onMutateObjectCallerData</code>. Ele muta <strong>dado, não controle</strong>, ao contrário de <code>conditionNode</code>, <code>arrayNode</code>, '
 '<code>fluxBox</code> e <code>libraryNode</code>, que pertencem ao workflow (B6).</p>'
 '<p>A revisão de 2026-10-23 mostrou que <strong>não existe escrita de objeto</strong> — a escrita vive só naquele array — e que também não existe registro de execução, '
 'então o valor que um run usou não pode ser recuperado. Achou quatro caminhos de entrada, não três, e uma corrida <strong>entre runs</strong>, não só entre ramos. '
 'Achou também que os laços do back pulam ou rodam inline vários tipos <code>worker</code>, e esse trabalho veio para cá a partir da A12 da auditoria de cobertura.</p>')

TABLE = dict(
 head=[('Change','Mudança'),('How','Como')],
 rows=[
  [{'t':('1 · Record every <code>nodesBox</code> execution','1 · Registrar toda execução de <code>nodesBox</code>')},
   ('The activity writes the <code>node_executions</code> row like every worker node: <code>input</code> holds <code>selectedId</code>, session key and element inputs; <code>outputData</code> holds the element values after the write; <code>execId</code> is set.',
    'A activity grava a linha em <code>node_executions</code> como todo node do worker: <code>input</code> guarda <code>selectedId</code>, a chave de sessão e as entradas dos elementos; <code>outputData</code> guarda os valores dos elementos depois da escrita; <code>execId</code> é preenchido.')],
  [{'t':('2 · Make run-scoped object state durable','2 · Tornar durável o estado de objeto do run')},
   ('The source of truth is the run&#x27;s <code>nodesBox</code> rows: the latest completed write to that object in the run, else the stored template in <code>flow_objects</code>.',
    'A fonte da verdade são as linhas de <code>nodesBox</code> do run: a última escrita concluída naquele objeto no run, senão o modelo salvo em <code>flow_objects</code>.')],
  [{'t':('3 · Feed the worker projection','3 · Alimentar a projeção do worker')},
   ('<code>getOutputByType</code> resolves a <code>nodesBox</code> source from item 2, not from <code>objectCallerData</code>. Remove <code>nodesBox</code> from <code>BACK_ONLY_PROJECTION_NODE_TYPES</code> in back and worker.',
    '<code>getOutputByType</code> resolve uma origem <code>nodesBox</code> pelo item 2, e não pelo <code>objectCallerData</code>. Tirar <code>nodesBox</code> de <code>BACK_ONLY_PROJECTION_NODE_TYPES</code> no back e no worker.')],
  [{'t':('4 · Order session writes (A7-D3)','4 · Ordenar as escritas de sessão (A7-D3)')},
   ('One advisory lock per <code>objectId:sessionKey:ownerUserId</code> for read, merge and append in one transaction in <code>sessionStateService</code>, with <code>SET LOCAL lock_timeout</code>.',
    'Um advisory lock por <code>objectId:sessionKey:ownerUserId</code> para ler, mesclar e anexar numa só transação no <code>sessionStateService</code>, com <code>SET LOCAL lock_timeout</code>.')],
  [{'t':('5 · Stamp session rows','5 · Carimbar as linhas de sessão')},
   ('Pass <code>execId</code> and <code>flowId</code> on every object-scope append.',
    'Passar <code>execId</code> e <code>flowId</code> em todo append de escopo <code>object</code>.')],
  [{'t':('6 · Owner resolved once (A7-D7)','6 · Dono resolvido uma vez (A7-D7)')},
   ('The back resolves the object owner once per run and puts it in the run seed, keeping each path&#x27;s current rule.',
    'O back resolve o dono do objeto uma vez por run e o põe na semente do run, mantendo a regra atual de cada caminho.')],
  [{'t':('7 · Cover all four paths','7 · Cobrir os quatro caminhos')},
   ('Delete the inline handler from the full run, loop body, single node and prefetch paths. Set <code>prefetchSafe</code> from what the activity really needs.',
    'Apagar o handler inline da execução completa, do corpo do laço, do node único e do prefetch. Definir <code>prefetchSafe</code> pelo que a activity de fato precisa.')],
  [{'t':('8 · Characterise before deleting','8 · Caracterizar antes de apagar')},
   ('No test covers <code>objectCaller</code> or <code>clearObjects</code> today. Add parity tests on the back first, then run them against the worker path.',
    'Nenhum teste cobre <code>objectCaller</code> ou <code>clearObjects</code> hoje. Criar testes de paridade no back primeiro, e depois rodá-los contra o caminho do worker.')],
  [{'t':('9 · Negative controls','9 · Controles negativos')},
   ('Downstream node under <code>processFlow</code> gets non-empty text (red before item 3). Two concurrent session writes keep both updates (red without item 4).',
    'O node seguinte sob <code>processFlow</code> recebe texto não vazio (vermelho antes do item 3). Duas escritas de sessão concorrentes mantêm as duas atualizações (vermelho sem o item 4).')],
  [{'t':('10 · Callback shape','10 · Formato do callback')},
   ('If any callback remains, model it on <code>/node-credit-gate</code> or <code>/run-events</code> (DTO class, <code>@HttpCode</code>), not on <code>/store-payload</code>.',
    'Se algum callback continuar, espelhe <code>/node-credit-gate</code> ou <code>/run-events</code> (classe DTO, <code>@HttpCode</code>), e não <code>/store-payload</code>.')],
 ])

PROSE = (
 'Nine decisions. Six are settled (2026-10-23), A7-D4 is agreed, A7-D6 has a direction, and <strong>A7-D9 is still pending approval</strong>. '
 'A7-D3 — the ordering question the original scope asked to answer — is open below with its rationale, and so is the A7-D9 proposal.',
 'Nove decisões. Seis estão fechadas (2026-10-23), a A7-D4 está combinada, a A7-D6 tem uma direção, e <strong>a A7-D9 ainda aguarda aprovação</strong>. '
 'A A7-D3 — a questão de ordem que o escopo original pedia para responder — aparece aberta abaixo com a justificativa, assim como a proposta da A7-D9.')

_SET = {'t':('Settled','Decidida'),'pill':'ok'}

DEC_TABLE = {'k':'table',
 'head':[('Decision','Decisão'),('Question','Pergunta'),('Status','Status'),('Answer','Resposta')],
 'rows':[
  [{'t':'A7-D1','mono':True}, ('Projection and execution record in A7, or deferred to B6?','Projeção e registro de execução na A7, ou adiados para a B6?'), _SET,
   ('<strong>A7.</strong> Solving it outranks the estimate. A7 works without B4: legacy loop, loop body, single node and prefetch.',
    '<strong>A7.</strong> Resolver isso pesa mais que a estimativa. A A7 funciona sem a B4: laço legado, corpo do laço, node único e prefetch.')],
  [{'t':'A7-D2','mono':True}, ('Session reads and writes from the worker directly, or through a back callback?','Leituras e escritas de sessão direto do worker, ou por um callback do back?'), _SET,
   ('<strong>Back callback.</strong> One implementation in <code>sessionStateService</code>, idempotent per <code>execId</code> + <code>nodeId</code>, so a Temporal retry after a lost response does not append twice.',
    '<strong>Callback do back.</strong> Uma implementação no <code>sessionStateService</code>, idempotente por <code>execId</code> + <code>nodeId</code>, para que um retry do Temporal após uma resposta perdida não anexe duas vezes.')],
  [{'t':'A7-D3','mono':True}, ('Advisory lock or idempotent activity?','Advisory lock ou activity idempotente?'), _SET,
   ('<strong>Advisory lock</strong>, in <code>sessionStateService</code>. See below.','<strong>Advisory lock</strong>, no <code>sessionStateService</code>. Veja abaixo.')],
  [{'t':'A7-D4','mono':True}, ('Does A7&#x27;s worker PR wait for B4 worker on <code>main</code>?','O PR de worker da A7 espera a B4 worker no <code>main</code>?'), {'t':('Agreed','Combinada'),'pill':'ok'},
   ('Yes. Coordinate the order with the B4 owner.','Sim. Combinar a ordem com o responsável pela B4.')],
  [{'t':'A7-D5','mono':True}, ('Unify the two session flags, or keep today&#x27;s behaviour?','Unificar as duas flags de sessão, ou manter o comportamento atual?'), _SET,
   ('<strong>Keep it, for parity.</strong> Unifying is a product change, not part of A7.','<strong>Manter, por paridade.</strong> Unificar é mudança de produto, fora da A7.')],
  [{'t':'A7-D6','mono':True}, ('Under B5, two <code>nodesBox</code> nodes on one object in one run: serialise, or accept arrival order?','Sob a B5, dois <code>nodesBox</code> no mesmo objeto no mesmo run: serializar, ou aceitar a ordem de chegada?'), {'t':('Direction','Direção'),'pill':'weak'},
   ('<strong>The DAG orders them.</strong> <code>buildSchedulerState</code> derives implicit edges from object access in today&#x27;s tie-break order.',
    '<strong>O DAG os ordena.</strong> <code>buildSchedulerState</code> deriva arestas implícitas do acesso ao objeto, na ordem de desempate atual.')],
  [{'t':'A7-D7','mono':True}, ('Unify the object owner rule across paths?','Unificar a regra de dono do objeto entre os caminhos?'), _SET,
   ('<strong>Keep each path&#x27;s rule</strong>, resolved once by the back and carried in the run seed.','<strong>Manter a regra de cada caminho</strong>, resolvida uma vez pelo back e levada na semente do run.')],
  [{'t':'A7-D8','mono':True}, ('Read side while the B4 flag exists?','Lado da leitura enquanto a flag da B4 existir?'), _SET,
   ('<strong>The B4 flag switches it.</strong> Off: the back&#x27;s loop reads <code>objectCallerData</code>, fed by the activity&#x27;s result. On: the worker reads by reference.',
    '<strong>A flag da B4 decide.</strong> Desligada: o laço do back lê o <code>objectCallerData</code>, alimentado pelo resultado da activity. Ligada: o worker lê por referência.')],
  [{'t':'A7-D9','mono':True}, ('Protection on the internal callback?','Proteção no callback interno?'), {'t':('Pending','Pendente'),'pill':'weak'},
   ('Proposed, awaiting approval. See below.','Proposta, aguardando aprovação. Veja abaixo.')],
 ]}

DEC_LOCK = {
 'k':'decision','id':'A7-D3','status':'set','open':True,
 'q':('Advisory lock, or an idempotent activity, for concurrent session writes on one object?',
      'Advisory lock, ou activity idempotente, para escritas de sessão concorrentes no mesmo objeto?'),
 'intro':(
  'Within one run, calls are serial today and under B4. <strong>Across runs of one flow</strong>, <code>readLatest</code> then append has no lock, '
  'so the later stale snapshot wins. The original scope said: <strong>pick one and state why — do not ship without addressing it and hope the ordering holds.</strong>',
  'Dentro de um run, as chamadas são seriais hoje e sob a B4. <strong>Entre runs do mesmo fluxo</strong>, <code>readLatest</code> seguido de append não tem lock, '
  'então o snapshot velho que chega por último vence. O escopo original dizia: <strong>escolha uma e diga por quê — não entregue sem tratar isso e torcer para a ordem se manter.</strong>'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Advisory lock in <code>sessionStateService</code>','Advisory lock no <code>sessionStateService</code>'),
   'tag':('settled','decidida'),
   'how':('One lock per <code>objectId:sessionKey:ownerUserId</code>, held for read, merge and append in one transaction. Both object-scope writers take it: '
          '<code>objectCaller()</code> (through the callback) and <code>clearObjects()</code>, both in <code>flux.service.ts</code>. '
          'The pattern already exists in <code>worker/src/modules/nodes/third-party-integration/oauth-token.repo.ts</code> (<code>pg_advisory_xact_lock</code>).',
          'Um lock por <code>objectId:sessionKey:ownerUserId</code>, segurado para ler, mesclar e anexar numa só transação. Os dois escritores de escopo <code>object</code> o tomam: '
          '<code>objectCaller()</code> (pelo callback) e <code>clearObjects()</code>, ambos em <code>flux.service.ts</code>. '
          'O padrão já existe em <code>worker/src/modules/nodes/third-party-integration/oauth-token.repo.ts</code> (<code>pg_advisory_xact_lock</code>).'),
   'pros':[('It closes the lost update between two runs','Fecha a atualização perdida entre dois runs'),
           ('The race can be made deterministic in a test by holding the lock explicitly','A corrida pode ficar determinística num teste segurando o lock explicitamente')],
   'cons':[('A waiting transaction holds a back pool connection, so the wait is bounded with <code>SET LOCAL lock_timeout</code>',
            'Uma transação em espera segura uma conexão do pool do back, então a espera é limitada com <code>SET LOCAL lock_timeout</code>')]},
  {'ltr':'B','name':('An idempotent activity alone','Só uma activity idempotente'),
   'how':('Make the write safe to repeat, with no lock.','Tornar a escrita segura para repetir, sem lock.'),
   'pros':[('A retry does not append twice — kept anyway, through the idempotent callback (A7-D2)','Um retry não anexa duas vezes — mantido de todo modo, pelo callback idempotente (A7-D2)')],
   'cons':[('It <strong>does not prevent a lost update between two runs</strong>','<strong>Não impede a atualização perdida entre dois runs</strong>')]},
  {'ltr':'C','no':True,'name':('Ship it and hope the ordering holds','Entregar e torcer para a ordem se manter'),
   'tag':('rejected by the spec','rejeitada pela spec'),
   'how':('Migrate the node with no answer on ordering.','Migrar o node sem resposta sobre a ordem.'),
   'cons':[('The spec forbids it in as many words','A spec proíbe isso com todas as letras')]},
 ],
 'rec':(
  '<p><strong>A.</strong> The chat scope (<code>scopeType: &#x27;chat&#x27;</code>, appended in <code>apiV2</code>&#x27;s finalisation) is not involved: '
  'A14 needs no lock, because it derives Small Memory content from stored executions instead of writing it.</p>',
  '<p><strong>A.</strong> O escopo de chat (<code>scopeType: &#x27;chat&#x27;</code>, anexado na finalização do <code>apiV2</code>) não entra: '
  'a A14 não precisa de lock, porque deriva o conteúdo da Small Memory das execuções salvas em vez de escrevê-lo.</p>'),
}

DEC_PROTECT = {
 'k':'decision','id':'A7-D9','status':'open',
 'q':('How is the internal callback protected?','Como o callback interno é protegido?'),
 'intro':('Proposed 2026-10-23 and <strong>still pending approval</strong>. Confirming it is on the list of what is needed before implementation.',
          'Proposta em 2026-10-23 e <strong>ainda aguardando aprovação</strong>. Confirmá-la está na lista do que falta antes da implementação.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Bound, cap and alert','Limitar, restringir e alertar'),
   'tag':('proposed','proposta'),
   'how':('No requests-per-minute limit. Bound the lock wait, cap concurrent callbacks per back instance with a retryable <code>503</code>, '
          'and alert on lock wait and refusals.',
          'Sem limite de requisições por minuto. Limitar a espera pelo lock, restringir callbacks concorrentes por instância do back com um <code>503</code> que permite retry, '
          'e alertar sobre espera de lock e recusas.')},
 ],
}

DECISIONS = [DEC_TABLE, DEC_LOCK, DEC_PROTECT]

PARTS = [
{'n':'1','title':('An execution record, and consumers by reference','Um registro de execução, e consumidores por referência'),
 'loc':'worker/src/modules/nodes/object-caller/',
 'purpose':('Every <code>nodesBox</code> execution has a <code>node_executions</code> row on both engines, and a consumer can say which write it read.',
            'Toda execução de <code>nodesBox</code> tem linha em <code>node_executions</code> nos dois motores, e um consumidor sabe dizer qual escrita leu.'),
 'body':('<p>The activity writes the row like every worker node. A consumer records <strong>which writer execution it read</strong>, not a copy of the object text, '
         'so object text a run produces is stored once, in the writer&#x27;s row, under a retention policy decided in this task.</p>'
         '<p><strong>Read rule:</strong> a consumer reads the writes that completed before it was scheduled, not the latest at read time, so a Temporal retry reads the same value.</p>',
         '<p>A activity grava a linha como todo node do worker. Um consumidor registra <strong>qual execução escritora leu</strong>, e não uma cópia do texto do objeto, '
         'então o texto que um run produz fica salvo uma vez, na linha do escritor, sob uma política de retenção decidida nesta task.</p>'
         '<p><strong>Regra de leitura:</strong> um consumidor lê as escritas concluídas antes de ser agendado, e não a mais recente no momento da leitura, para que um retry do Temporal leia o mesmo valor.</p>'),
 'ba':(('A write lives only in the run&#x27;s in-memory <code>objectCallerData</code>; the value a run used cannot be recovered afterwards.',
        'A escrita vive só no <code>objectCallerData</code> em memória do run; o valor que um run usou não pode ser recuperado depois.'),
       ('The run&#x27;s <code>nodesBox</code> rows are the source of truth, else the stored template in <code>flow_objects</code>.',
        'As linhas de <code>nodesBox</code> do run são a fonte da verdade, senão o modelo salvo em <code>flow_objects</code>.'))},

{'n':'2','title':('Implicit ordering edges','Arestas implícitas de ordem'),
 'loc':'back/src/app-api/flux/scheduler.ts',
 'purpose':('Two callers of one object have no edge between them, so the scheduler derives one (A7-D6).',
            'Dois callers do mesmo objeto não têm aresta entre si, então o scheduler deriva uma (A7-D6).'),
 'body':('<p><code>buildSchedulerState</code> derives ordering edges from object access — writer to writer, writer to reader — in today&#x27;s tie-break order. '
         'Both engines use it: the back&#x27;s loop is the same DAG scheduler run one node at a time, so the order does not change there and stays defined when B5 dispatches a batch. '
         'It reaches the worker through B2&#x27;s sync.</p>',
         '<p><code>buildSchedulerState</code> deriva arestas de ordem do acesso ao objeto — escritor para escritor, escritor para leitor — na ordem de desempate atual. '
         'Os dois motores a usam: o laço do back é o mesmo scheduler de DAG rodando um node por vez, então a ordem não muda ali e continua definida quando a B5 despachar um lote. '
         'Ela chega ao worker pela sincronização da B2.</p>')},

{'n':'3','title':('Session writes through one locked callback','Escritas de sessão por um callback com lock'),
 'loc':'back/src/app-api/session_state/',
 'purpose':('One implementation, in the back, idempotent per <code>execId</code> + <code>nodeId</code> (A7-D2), ordered by an advisory lock (A7-D3).',
            'Uma implementação, no back, idempotente por <code>execId</code> + <code>nodeId</code> (A7-D2), ordenada por um advisory lock (A7-D3).'),
 'body':('<p>The callback calls <code>sessionStateService</code> for the <code>object</code> scope. One lock per <code>objectId:sessionKey:ownerUserId</code> covers read, merge and append '
         'in one transaction, with <code>SET LOCAL lock_timeout</code>; <code>clearObjects</code> takes the same lock. Every append carries <code>execId</code> and <code>flowId</code>. '
         'The back resolves the object owner once per run and carries it in the run seed (A7-D7).</p>',
         '<p>O callback chama o <code>sessionStateService</code> para o escopo <code>object</code>. Um lock por <code>objectId:sessionKey:ownerUserId</code> cobre ler, mesclar e anexar '
         'numa só transação, com <code>SET LOCAL lock_timeout</code>; o <code>clearObjects</code> toma o mesmo lock. Todo append leva <code>execId</code> e <code>flowId</code>. '
         'O back resolve o dono do objeto uma vez por run e o leva na semente do run (A7-D7).</p>'),
 'ba':(('<code>readLatest</code> then append has no lock across runs, and session rows have no <code>execId</code> or <code>flowId</code>.',
        '<code>readLatest</code> seguido de append não tem lock entre runs, e as linhas de sessão não têm <code>execId</code> nem <code>flowId</code>.'),
       ('Two concurrent session writes keep both updates, and each row says which run wrote it.',
        'Duas escritas de sessão concorrentes mantêm as duas atualizações, e cada linha diz qual run a escreveu.'))},

{'n':'4','title':('Read side switched by the B4 flag','Lado da leitura trocado pela flag da B4'),
 'loc':'back/src/app-api/flux/node-input-projection.ts',
 'purpose':('Flipping <code>nodesBox</code> to <code>flowDispatch: &#x27;worker&#x27;</code> must not hand downstream nodes empty text (A7-D8).',
            'Virar o <code>nodesBox</code> para <code>flowDispatch: &#x27;worker&#x27;</code> não pode entregar texto vazio aos nodes seguintes (A7-D8).'),
 'body':('<p>With the flag off, the back&#x27;s loop keeps feeding downstream nodes from <code>objectCallerData</code>, now updated from the activity&#x27;s result. '
         'With the flag on, the worker projection reads by reference: <code>getOutputByType</code> resolves a <code>nodesBox</code> source from the run&#x27;s rows. '
         'A shadow comparison on the back&#x27;s loop logs any difference before the flag is turned on, as B3b did.</p>',
         '<p>Com a flag desligada, o laço do back segue alimentando os nodes seguintes pelo <code>objectCallerData</code>, agora atualizado pelo resultado da activity. '
         'Com a flag ligada, a projeção do worker lê por referência: <code>getOutputByType</code> resolve uma origem <code>nodesBox</code> pelas linhas do run. '
         'Uma comparação sombra no laço do back registra qualquer diferença antes de a flag ser ligada, como fez a B3b.</p>'),
 'ba':(('Under <code>processFlow</code>, the worker projection passes <code>undefined</code> as <code>objectCallerData</code>, so downstream nodes get empty text.',
        'Sob o <code>processFlow</code>, a projeção do worker passa <code>undefined</code> como <code>objectCallerData</code>, e os nodes seguintes recebem texto vazio.'),
       ('Both engines feed the same value, and the shadow proves it before the flag flips.',
        'Os dois motores entregam o mesmo valor, e a sombra prova isso antes de a flag virar.'))},

{'n':'5','title':('Delete the inline handler on all four paths','Apagar o handler inline nos quatro caminhos'),
 'loc':'back/src/app-api/flux/flux.service.ts',
 'purpose':('Characterise first, then delete <code>objectCaller()</code> from the full run, loop body, single node and prefetch paths.',
            'Caracterizar primeiro, depois apagar <code>objectCaller()</code> da execução completa, do corpo do laço, do node único e do prefetch.'),
 'body':('<p>No test covers <code>objectCaller</code> or <code>clearObjects</code> today, so parity tests go on the back first and then run against the worker path. '
         'Set <code>prefetchSafe</code> from what the activity really needs. If any callback remains, model it on <code>/node-credit-gate</code> or <code>/run-events</code>, not on <code>/store-payload</code>.</p>',
         '<p>Nenhum teste cobre <code>objectCaller</code> ou <code>clearObjects</code> hoje, então os testes de paridade entram no back primeiro e depois rodam contra o caminho do worker. '
         'Definir <code>prefetchSafe</code> pelo que a activity de fato precisa. Se algum callback continuar, espelhe <code>/node-credit-gate</code> ou <code>/run-events</code>, e não <code>/store-payload</code>.</p>'),
 'callouts':[('mig',('Out of scope','Fora de escopo'),
   ('<p>Changing object semantics, session-state scoping, or the chat behaviour built on it. Unifying the object owner rule (A7-D7), the two session flags (A7-D5), '
    'the chat scope (A14) and the Data Output sink (A13).</p>',
    '<p>Mudar a semântica de objeto, o escopo do estado de sessão, ou o comportamento de chat construído sobre ele. Unificar a regra de dono do objeto (A7-D7), as duas flags de sessão (A7-D5), '
    'o escopo de chat (A14) e o destino Data Output (A13).</p>'))]},

{'n':'6','title':('Every worker type reachable from both loops','Todo tipo worker alcançável pelos dois laços'),
 'loc':'back/src/app-api/flux/flux.service.ts',
 'purpose':('Replace the per-type <code>if</code> branches in the full-run loop and the <code>arrayNode</code> loop body with one branch derived from the registry (<code>dispatchesToWorker</code>).',
            'Trocar os <code>if</code> por tipo no laço da execução completa e no corpo do laço do <code>arrayNode</code> por um só ramo derivado do registro (<code>dispatchesToWorker</code>).'),
 'list':[
  ('<code>animationNode</code>, <code>secApiNode</code>, <code>usCensusNode</code> and <code>webAmazon</code> are never executed by a full run in production (STATUS A6, open since 2026-10-15).',
   '<code>animationNode</code>, <code>secApiNode</code>, <code>usCensusNode</code> e <code>webAmazon</code> nunca são executados por uma execução completa em produção (STATUS A6, aberto desde 2026-10-15).'),
  ('The loop body also misses <code>thirdPartyIntegration</code>, <code>hubSpotCRM</code>, <code>outputController</code>, <code>reportBuilder</code>, <code>counterNode</code> and <code>fileSave</code>.',
   'O corpo do laço também deixa de fora <code>thirdPartyIntegration</code>, <code>hubSpotCRM</code>, <code>outputController</code>, <code>reportBuilder</code>, <code>counterNode</code> e <code>fileSave</code>.'),
  ('<code>sqlQuerier</code> still runs inline through <code>sqlQuerierNode()</code> in both loops on <code>main</code>, contrary to A3&#x27;s Done-when.',
   '<code>sqlQuerier</code> segue rodando inline por <code>sqlQuerierNode()</code> nos dois laços no <code>main</code>, contrariando o critério de pronto da A3.'),
 ],
 'callouts':[
  ('mig',('<code>sqlQuerier</code> is not redone here','<code>sqlQuerier</code> não é refeito aqui'),
   ('<p>Back branch <code>feat/sql-node</code> (commit <code>196df420</code>, 2026-10-22) already routes both loops through <code>processNodeViaTemporal</code> and deletes '
    '<code>sqlQuerierNode()</code>. It has no PR yet and is 63 commits behind <code>main</code>. Assumption (2026-10-23): it ships in the Monday 2026-10-26 deploy with E1 and B4, '
    'before A7&#x27;s code, so A7&#x27;s generic branch replaces that per-type branch.</p>',
    '<p>A branch do back <code>feat/sql-node</code> (commit <code>196df420</code>, 2026-10-22) já leva os dois laços por <code>processNodeViaTemporal</code> e apaga '
    '<code>sqlQuerierNode()</code>. Ela ainda não tem PR e está 63 commits atrás do <code>main</code>. Premissa (2026-10-23): ela sai no deploy de segunda, 2026-10-26, junto com E1 e B4, '
    'antes do código da A7, então o ramo genérico da A7 substitui esse ramo por tipo.</p>')),
  ('mig',('Branches','Branches'),
   ('<p>Cut the back and worker branches from <code>origin/main</code>. The worker branch merges <code>origin/feat/wave-4-b4</code> locally so the B4 flag can be validated with A7; '
    'the PR body says so, and A7&#x27;s worker PR to <code>main</code> waits for B4&#x27;s (A7-D4).</p>',
    '<p>Criar as branches de back e worker a partir de <code>origin/main</code>. A branch do worker faz merge local de <code>origin/feat/wave-4-b4</code> para validar a flag da B4 com a A7; '
    'o corpo do PR diz isso, e o PR de worker da A7 para o <code>main</code> espera o da B4 (A7-D4).</p>')),
  ('decide',('Still needed before implementation','Ainda falta antes da implementação'),
   ('<p>1. Production counts: run <code>a7-q1</code> to <code>a7-q3</code> in DBeaver. 2. Confirm A7-D9. 3. Rewrite the ClickUp description — its spec link points at '
    '<code>.specs/features/...</code>, which does not exist on <code>main</code>. 4. Re-estimate.</p>',
    '<p>1. Contagens de produção: rodar <code>a7-q1</code> a <code>a7-q3</code> no DBeaver. 2. Confirmar a A7-D9. 3. Reescrever a descrição no ClickUp — o link da spec aponta para '
    '<code>.specs/features/...</code>, que não existe no <code>main</code>. 4. Refazer a estimativa.</p>')),
 ]},
]

VERIF = [
 (True, ('Negative control — ordering','Controle negativo — ordem'),
  ('Remove the ordering guarantee and run <strong>two concurrent session writes on the same object</strong>, asserting both updates survive. Watch it go red. '
   'An intermittent test is not acceptable, so <strong>make the race deterministic by holding the lock explicitly in the test</strong>.',
   'Remova a garantia de ordem e rode <strong>duas escritas de sessão concorrentes no mesmo objeto</strong>, afirmando que as duas atualizações sobrevivem. Veja ficar vermelho. '
   'Um teste intermitente não é aceitável, então <strong>torne a corrida determinística segurando o lock explicitamente no teste</strong>.')),
 (True, ('Negative control — worker projection','Controle negativo — projeção do worker'),
  ('A downstream node under <code>processFlow</code> gets non-empty text. It must be red before <code>getOutputByType</code> reads the run&#x27;s <code>nodesBox</code> rows.',
   'Um node seguinte sob <code>processFlow</code> recebe texto não vazio. O teste precisa estar vermelho antes de <code>getOutputByType</code> ler as linhas de <code>nodesBox</code> do run.')),
 (True, ('Every worker type is dispatched by both loops','Todo tipo worker é despachado pelos dois laços'),
  ('A test asserts that every <code>worker</code> type in the registry is dispatched by the full-run loop and by the loop body, and it has been seen red.',
   'Um teste afirma que todo tipo <code>worker</code> do registro é despachado pelo laço da execução completa e pelo corpo do laço, e ele já foi visto vermelho.')),
 (False, ('Characterisation and session parity','Caracterização e paridade de sessão'),
  ('Parity tests for <code>objectCaller</code> and <code>clearObjects</code> pass on the back, then on the worker path. <code>readLatest</code> / <code>appendEntries</code> through the callback '
   'produce the same rows the inline path produces, on real stored objects.',
   'Os testes de paridade de <code>objectCaller</code> e <code>clearObjects</code> passam no back, depois no caminho do worker. <code>readLatest</code> / <code>appendEntries</code> pelo callback '
   'produzem as mesmas linhas que o caminho inline, em objetos reais já armazenados.')),
 (False, ('The chat path is untouched','O caminho de chat fica intocado'),
  ('<code>fluxObject</code> / <code>nodesBox</code> with chat enabled is written at run finalisation (<code>flux.service.ts</code>), outside this node, and must be unaffected.',
   'O <code>fluxObject</code> / <code>nodesBox</code> com chat habilitado é escrito na finalização do run (<code>flux.service.ts</code>), fora deste node, e precisa ficar intacto.')),
]

DONE = ('<code>nodesBox</code> satisfies <code>PLAN §3.4</code>; both callbacks exist and are documented in D1; the ordering decision is recorded with its rationale; '
        'the inline handler is deleted. Widened: every <code>nodesBox</code> execution has a <code>node_executions</code> row on both engines; the registry dispatch test '
        'has been seen red; <code>sqlQuerierNode()</code> is deleted (by <code>feat/sql-node</code> or by A7, whichever lands first).',
        'O <code>nodesBox</code> satisfaz o <code>PLAN §3.4</code>; os dois callbacks existem e estão documentados na D1; a decisão de ordem está registrada com a justificativa; '
        'o handler inline foi apagado. Ampliado: toda execução de <code>nodesBox</code> tem linha em <code>node_executions</code> nos dois motores; o teste de dispatch pelo registro '
        'já foi visto vermelho; <code>sqlQuerierNode()</code> foi apagado (pela <code>feat/sql-node</code> ou pela A7, o que entrar primeiro).')

FILES = [('back/src/app-api/flux/flux.service.ts (objectCaller() + dispatch sites)', False),
         ('back/src/temporal/worker.controller.ts (callbacks)', True),
         ('back/src/app-api/objects/', False),
         ('back/src/app-api/session_state/', False),
         ('worker/src/modules/nodes/object-caller/', True),
         ('the A1 registry', False),
         ('back/src/app-api/flux/scheduler.ts', False),
         ('back/src/app-api/flux/edge-projection + worker getOutputByType', False),
         ('back/src/app-api/flux/node-input-projection.ts + worker copy', False)]

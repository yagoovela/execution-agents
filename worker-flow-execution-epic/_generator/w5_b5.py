# -*- coding: utf-8 -*-
TITLE = ('Turn on parallel dispatch', 'Ligar o dispatch paralelo')

GOAL = ('A flow whose nodes all run on the worker runs its <b>ready nodes at once</b>, up to a per-run cap (<code>maxInFlight</code>), so its wall-clock time approaches its slowest path instead of the sum of its nodes.',
        'Um fluxo cujos nós rodam todos no worker roda seus <b>nós prontos ao mesmo tempo</b>, até um limite por run (<code>maxInFlight</code>), então o tempo de relógio se aproxima do caminho mais lento em vez da soma dos nós.')

GLANCE = [
 ('crit', ('Customer impact','Impacto no cliente'), ('Sum of nodes → slowest path','Soma dos nós → caminho mais lento'),
  ('In dev, at <code>maxInFlight</code> 2, a 4-wide fan-out ran 1.84x faster and the reference shape 1.90x. The reference customer chain is mostly width 1, so its end-to-end gain stays about 1.2-1.5x.',
   'Em dev, com <code>maxInFlight</code> 2, um fan-out de largura 4 rodou 1,84x mais rápido e o formato de referência 1,90x. A cadeia do cliente de referência tem quase sempre largura 1, então o ganho de ponta a ponta fica em cerca de 1,2-1,5x.')),
 ('dep', ('Depends on','Depende de'), ('B6 · S1 · S2 · S3 · E3','B6 · S1 · S2 · S3 · E3'),
  ('Built on B6&#x27;s <code>processFlow</code>; B6 ships first, still sequential (D17 reversed). Production gate: B6 in production and B4 soaked with <code>engine_in_workflow</code> on.',
   'Construída sobre o <code>processFlow</code> da B6; a B6 sobe antes, ainda sequencial (D17 invertida). Gate de produção: a B6 em produção e a B4 rodando um período com a <code>engine_in_workflow</code> ligada.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('This settles risk <strong>R4</strong> (PLAN §6): the latency the A track added is paid back here, with numbers.',
   'Aqui se resolve o risco <strong>R4</strong> (PLAN §6): a latência que a trilha A acrescentou é paga de volta, com números.')),
 ('ship', ('Rollout','Rollout'), ('By company, behind two flags','Por empresa, atrás de duas flags'),
  ('<code>parallel_dispatch</code> (company allowlist, value = cap) and <code>parallel_fail_fast</code>. Turning the flag off restores sequential dispatch for new runs.',
   '<code>parallel_dispatch</code> (allowlist de empresas, valor = limite) e <code>parallel_fail_fast</code>. Desligar a flag volta ao dispatch sequencial para runs novos.')),
]

LEDE = (
 '<p><code>processFlow</code>, the Temporal workflow that runs a flow on the worker, <strong>runs one node at a time</strong>: '
 'it takes one ready node, waits for it to finish, and only then takes the next. A flow with eight independent image generations '
 'therefore takes the sum of the eight. The engine was built to run independent nodes together, but nothing dispatches more than one.</p>'
 '<p>Parallel nodes cannot overwrite each other. <code>apiV2</code> sends a flow to the workflow only when it has no <strong>inline node</strong> '
 '(a type that runs inside the back); on the workflow path every node writes only its own row; and <code>addConnectToNodes</code>, '
 'which writes into another node&#x27;s data, runs only before the run starts. The platform runs at most 10 nodes at once '
 '(1 worker replica, 10 activity slots), so B5 also caps each run.</p>',
 '<p>O <code>processFlow</code>, o workflow do Temporal que roda um fluxo no worker, <strong>roda um nó por vez</strong>: '
 'pega um nó pronto, espera ele terminar e só então pega o próximo. Um fluxo com oito gerações de imagem independentes '
 'leva, portanto, a soma das oito. O motor foi feito para rodar nós independentes juntos, mas nada despacha mais de um.</p>'
 '<p>Nós em paralelo não sobrescrevem um ao outro. O <code>apiV2</code> só manda um fluxo para o workflow quando ele não tem <strong>nó inline</strong> '
 '(um tipo que roda dentro do back); no caminho do workflow cada nó escreve só na própria linha; e o <code>addConnectToNodes</code>, '
 'que escreve no dado de outro nó, só roda antes de o run começar. A plataforma roda no máximo 10 nós ao mesmo tempo '
 '(1 réplica do worker, 10 slots de activity), então a B5 também limita cada run.</p>')

TABLE = dict(
 head=[('Run','Run'),
       ('What B5 does','O que a B5 faz'),
       ('Parallel?','Paralelo?')],
 rows=[
  [{'t':('<code>apiV2</code> run, every node on the worker, company on the allowlist','Run do <code>apiV2</code>, todos os nós no worker, empresa na allowlist')},
   ('Ready nodes run at once, up to <code>maxInFlight</code> (default 2, ceiling 4)',
    'Os nós prontos rodam ao mesmo tempo, até o <code>maxInFlight</code> (padrão 2, teto 4)'),
   {'t':('Yes','Sim'),'pill':'ok'}],
  [{'t':('Temporal-schedule run that passes the same gate','Run de schedule do Temporal que passa no mesmo gate')},
   ('The back returns <code>maxInFlight</code> and <code>failFast</code> with the prepared run',
    'O back devolve <code>maxInFlight</code> e <code>failFast</code> junto com o run preparado'),
   {'t':('Yes','Sim'),'pill':'ok'}],
  [{'t':('<code>fluxBox</code> or <code>libraryNode</code> sub-flow','Sub-flow de <code>fluxBox</code> ou <code>libraryNode</code>')},
   ('Runs with the parent&#x27;s <code>maxInFlight</code> and keeps its own S1 chain',
    'Roda com o <code>maxInFlight</code> do pai e mantém a própria cadeia da S1'),
   {'t':('Yes','Sim'),'pill':'ok'}],
  [{'t':('Batch rows','Linhas de batch')},
   ('Rows already run 5 at once; the nodes inside a row stay sequential in v1',
    'As linhas já rodam 5 por vez; os nós dentro de uma linha seguem sequenciais na v1'),
   {'t':('Not in v1','Não na v1'),'pill':'weak'}],
  [{'t':('Company not on the allowlist','Empresa fora da allowlist')},
   ('Runs as today, with the same node order and history events (B5-R1)',
    'Roda como hoje, com a mesma ordem de nós e os mesmos eventos de histórico (B5-R1)'),
   {'t':('No','Não'),'pill':'no'}],
  [{'t':('Flow with an inline node','Fluxo com um nó inline')},
   ('Goes to the legacy loop in the back, as today',
    'Vai para o loop legado no back, como hoje'),
   {'t':('No','Não'),'pill':'no'}],
  [{'t':('Iterations of one <code>arrayNode</code>','Iterações de um <code>arrayNode</code>')},
   ('Stay sequential: every iteration writes the current item onto the array&#x27;s single row',
    'Seguem sequenciais: cada iteração escreve o item atual na única linha do array'),
   {'t':('No','Não'),'pill':'no'}],
 ])

PROSE = (
 'Eight decisions, settled on 2026-11-19 when B5 was re-specified, except <code>B5-c</code>, which stays open until its production count runs. '
 'Each one opens to the answer and to the options it rejected, with the reason.',
 'Oito decisões, tomadas em 19/11/2026 quando a B5 foi reespecificada, exceto a <code>B5-c</code>, que fica em aberto até a contagem dela rodar em produção. '
 'Cada uma abre com a resposta e com as opções rejeitadas, com o motivo.')

REJ = ('rejected','rejeitada')

DEC_GATE = {
 'k':'decision','id':'B5-a','status':'set','open':True,
 'q':('What turns parallelism on for a run?','O que liga o paralelismo para um run?'),
 'intro':('The worker reads no feature flag, and <code>FeatureFlagTargetType</code> targets only <code>USER</code>, <code>COMPANY</code> or <code>SCHEDULE</code>. '
          'So the back decides once per run and passes the cap in the run input.',
          'O worker não lê feature flag, e o <code>FeatureFlagTargetType</code> só mira <code>USER</code>, <code>COMPANY</code> ou <code>SCHEDULE</code>. '
          'Então o back decide uma vez por run e passa o limite na entrada do run.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('The back decides, with a company allowlist','O back decide, com uma allowlist de empresas'),
   'how':('The existing gate (<code>canUseWorkflowForFlow</code>) and the <code>parallel_dispatch</code> flag through <code>isEnabledFor</code> with a <code>COMPANY</code> allowlist. '
          'Rollout: internal companies, then a group of customers named in the rollout plan, then everyone.',
          'O gate que já existe (<code>canUseWorkflowForFlow</code>) e a flag <code>parallel_dispatch</code> pelo <code>isEnabledFor</code> com uma allowlist <code>COMPANY</code>. '
          'Rollout: empresas internas, depois um grupo de clientes definido no plano de rollout, depois todos.')},
  {'ltr':'B','no':True,'tag':REJ,'name':('A <code>FLOW</code> target or a percentage rollout','Um alvo <code>FLOW</code> ou um rollout por porcentagem'),
   'how':('Neither exists in <code>FeatureFlagTargetType</code>.','Nenhum dos dois existe no <code>FeatureFlagTargetType</code>.')},
  {'ltr':'C','no':True,'tag':REJ,'name':('A decision in the worker','Uma decisão no worker'),
   'how':('The worker reads no flags.','O worker não lê flags.')},
 ],
 'outcome':('Settled 2026-11-19. Turning the flag off restores sequential dispatch for <strong>new</strong> runs; runs already started keep their <code>maxInFlight</code>. '
            'Found in the implementation: the allowlist targets the company that owns the flow, not the caller&#x27;s selected company; and <code>isEnabledFor</code> is true only when an allowlist row matches, '
            'so the "everyone" stage needs a second flag read with <code>isEnabled</code>.',
            'Decidida em 19/11/2026. Desligar a flag volta ao dispatch sequencial para runs <strong>novos</strong>; runs já iniciados mantêm o próprio <code>maxInFlight</code>. '
            'Achado na implementação: a allowlist mira a empresa dona do fluxo, não a empresa selecionada por quem chama; e o <code>isEnabledFor</code> só é verdadeiro quando uma linha da allowlist bate, '
            'então a etapa "todos" precisa de uma segunda flag lida com <code>isEnabled</code>.'),
}

DEC_CANCEL = {
 'k':'decision','id':'B5-b','status':'set',
 'q':('What does a cancelled node do?','O que um nó cancelado faz?'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Today&#x27;s settlement','O encerramento de hoje'),
   'how':('D20, D23 and <code>resolveCancelSettlement</code> apply: <code>textGenerator</code> and <code>apiCaller</code> stop, and text generation is charged for the tokens it used; '
          'every other activity keeps running under <code>TRY_CANCEL</code> and its result is discarded.',
          'Valem a D20, a D23 e o <code>resolveCancelSettlement</code>: <code>textGenerator</code> e <code>apiCaller</code> param, e a geração de texto é cobrada pelos tokens que usou; '
          'toda outra activity continua rodando sob <code>TRY_CANCEL</code> e o resultado é descartado.')},
 ],
 'outcome':('Settled 2026-11-19: no new cancel behaviour. On the parallel path, <code>processFlow</code> reads each child&#x27;s <code>status</code>, so a <code>CANCELLED</code> result is a cancellation, never a completion (B5-R8); '
            'with the flag off a cancelled child still counts as completed, as today.',
            'Decidida em 19/11/2026: nenhum comportamento novo de cancelamento. No caminho paralelo, o <code>processFlow</code> lê o <code>status</code> de cada filho, então um resultado <code>CANCELLED</code> é um cancelamento, nunca uma conclusão (B5-R8); '
            'com a flag desligada um filho cancelado ainda conta como concluído, como hoje.'),
}

DEC_ORDER = {
 'k':'decision','id':'B5-c','status':'open',
 'q':('Is graph order between two independent side-effect nodes a contract?','A ordem do grafo entre dois nós independentes com efeito colateral é um contrato?'),
 'intro':('With parallel dispatch, two independent side-effect nodes no longer fire in graph order, and a failure no longer prevents an independent side effect that already started. '
          'A Data Output that ran in a failed run still sends its email and callback, so a failed parallel run can deliver outputs that a sequential run stopped before.',
          'Com o dispatch paralelo, dois nós independentes com efeito colateral deixam de disparar na ordem do grafo, e uma falha deixa de impedir um efeito colateral independente que já começou. '
          'Um Data Output que rodou num run com falha ainda envia o email e o callback, então um run paralelo com falha pode entregar saídas que um run sequencial teria parado antes.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Order comes from the dependencies','A ordem vem das dependências'),
   'how':('Before the rollout widens past internal companies, count the production flows with two or more independent side-effect nodes in one ready level; then prefer an explicit edge.',
          'Antes de o rollout passar das empresas internas, contar os fluxos de produção com dois ou mais nós independentes com efeito colateral num mesmo nível pronto; depois, preferir uma aresta explícita.')},
  {'ltr':'B','no':True,'tag':REJ,'name':('A side-effect-only dispatch lane','Uma fila de dispatch só para efeitos colaterais'),
   'how':('A second per-type classification before the count exists.','Uma segunda classificação por tipo antes de a contagem existir.')},
 ],
 'note':(('Where it stands (2026-11-23)','Onde está (23/11/2026)'),
         ('Open. The count runs in production before the rollout widens past internal companies (B5-R10).',
          'Em aberto. A contagem roda em produção antes de o rollout passar das empresas internas (B5-R10).')),
}

DEC_FAIL = {
 'k':'decision','id':'B5-d','status':'set',
 'q':('What happens when a parallel node fails?','O que acontece quando um nó paralelo falha?'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Fail-fast, behind its own flag','Fail-fast, atrás da própria flag'),
   'how':('The first genuine failure cancels every leaf sibling in flight, except when that failure is a <code>WorkerShutdown</code> (then the run drains). '
          'An in-flight <code>fluxBox</code> or <code>libraryNode</code> child is never cancelled: a library flow can hold half-done external writes. '
          'Each cancelled sibling records the reason ("stopped because node X failed"), and the genuine failure with the lowest dispatch index names the run. '
          'With <code>parallel_fail_fast</code> off, the run drains instead.',
          'A primeira falha genuína cancela todo irmão folha em voo, exceto quando essa falha é um <code>WorkerShutdown</code> (aí o run drena). '
          'Um filho <code>fluxBox</code> ou <code>libraryNode</code> em voo nunca é cancelado: um library flow pode ter escritas externas pela metade. '
          'Cada irmão cancelado registra o motivo ("parado porque o nó X falhou"), e a falha genuína com o menor índice de dispatch dá nome ao run. '
          'Com a <code>parallel_fail_fast</code> desligada, o run drena.')},
  {'ltr':'B','no':True,'tag':REJ,'name':('Drain only','Só drenar'),
   'how':('Reports a failure only when the slowest sibling ends.','Só informa a falha quando o irmão mais lento termina.')},
  {'ltr':'C','no':True,'tag':REJ,'name':('A list of failures','Uma lista de falhas'),
   'how':('A cross-repo DTO change.','Uma mudança de DTO entre repositórios.')},
  {'ltr':'D','no':True,'tag':REJ,'name':('Cancel sub-flows too','Cancelar também os sub-flows'),
   'how':('Stops a library flow between two external writes.','Para um library flow entre duas escritas externas.')},
 ],
 'outcome':('Settled 2026-11-19. The contract stays singular: no DTO changes. A genuine failure is a node outcome <code>failed</code>; a cancellation is not a failure.',
            'Decidida em 19/11/2026. O contrato continua singular: nenhum DTO muda. Uma falha genuína é um resultado de nó <code>failed</code>; um cancelamento não é falha.'),
}

DEC_B6 = {
 'k':'decision','id':'B5-e','status':'set',
 'q':('How do B5 and B6 relate?','Como a B5 e a B6 se relacionam?'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Build B5 on B6','Construir a B5 sobre a B6'),
   'how':('B5 is built on B6&#x27;s <code>processFlow</code> (<code>feat/868m0vmvr</code>). B6 ships first, sequential.',
          'A B5 é construída sobre o <code>processFlow</code> da B6 (<code>feat/868m0vmvr</code>). A B6 sobe antes, sequencial.')},
  {'ltr':'B','no':True,'tag':REJ,'name':('Build on <code>main</code>','Construir sobre o <code>main</code>'),
   'how':('Rewrites the loop twice, and dev differs from <code>develop</code>.','Reescreve o loop duas vezes, e o dev fica diferente do <code>develop</code>.')},
  {'ltr':'C','no':True,'tag':REJ,'name':('Ship together','Subir juntas'),
   'how':('One bigger deploy, harder rollback.','Um deploy maior, rollback mais difícil.')},
 ],
 'outcome':('Settled 2026-11-19. It reverses D17&#x27;s order, which had B5 ship before B6.',
            'Decidida em 19/11/2026. Inverte a ordem da D17, que punha a B5 antes da B6.'),
}

DEC_CONTROL = {
 'k':'decision','id':'B5-f','status':'set',
 'q':('How do the control-flow nodes run?','Como rodam os nós de controle de fluxo?'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Concurrently, under per-type rules','Em paralelo, com regras por tipo'),
   'how':('<code>conditionNode</code>, <code>arrayNode</code>, <code>fluxBox</code> and <code>libraryNode</code> run concurrently with their siblings. '
          'A sub-flow inherits the <strong>same</strong> <code>maxInFlight</code> as its parent.',
          '<code>conditionNode</code>, <code>arrayNode</code>, <code>fluxBox</code> e <code>libraryNode</code> rodam em paralelo com os irmãos. '
          'Um sub-flow herda o <strong>mesmo</strong> <code>maxInFlight</code> do pai.')},
  {'ltr':'B','no':True,'tag':REJ,'name':('Barriers','Barreiras'),
   'how':('Give up the speedup of array- and sub-flow-heavy flows.','Abrem mão do ganho dos fluxos com muitos arrays e sub-flows.')},
  {'ltr':'C','no':True,'tag':REJ,'name':('Halving per level','Metade por nível'),
   'how':('At the default 2, a depth-2 agent flow runs sequentially, which removes the gain in the reference use case.',
          'Com o padrão 2, um fluxo de agente de profundidade 2 roda sequencial, o que tira o ganho do caso de uso de referência.')},
  {'ltr':'D','no':True,'tag':REJ,'name':('A shared tree budget in Redis','Um orçamento compartilhado da árvore no Redis'),
   'how':('A new lease for a bound the worker&#x27;s 10 activity slots already give.','Um lease novo para um limite que os 10 slots de activity do worker já dão.')},
 ],
 'outcome':('Settled 2026-11-19.','Decidida em 19/11/2026.'),
}

DEC_LIMITS = {
 'k':'decision','id':'B5-g','status':'set',
 'q':('Which concurrency limits ship?','Quais limites de concorrência saem?'),
 'opts':[
  {'ltr':'A','pick':True,'name':('The per-run cap now; the per-provider budget in B5b','O limite por run agora; o orçamento por provedor na B5b'),
   'how':('B5 ships the per-run cap. B5b ships the fleet-wide per-provider budget before the worker scales past 1 replica or the rollout reaches customers, whichever comes first: '
          'one flag per provider (<code>provider_cap_&lt;key&gt;</code>, <code>value</code> = cap), read by the worker with a 60 s cache, failing open.',
          'A B5 entrega o limite por run. A B5b entrega o orçamento por provedor da frota inteira antes de o worker passar de 1 réplica ou de o rollout chegar a clientes, o que vier primeiro: '
          'uma flag por provedor (<code>provider_cap_&lt;key&gt;</code>, <code>value</code> = limite), lida pelo worker com cache de 60 s, falhando aberta.')},
  {'ltr':'B','no':True,'tag':REJ,'name':('Ship the budget in B5','Entregar o orçamento na B5'),
   'how':('No provider limit is known, so it would limit nothing on day one.','Nenhum limite de provedor é conhecido, então não limitaria nada no primeiro dia.')},
  {'ltr':'C','no':True,'tag':REJ,'name':('An env var','Uma variável de ambiente'),
   'how':('Every change needs a deploy.','Toda mudança precisa de deploy.')},
  {'ltr':'D','no':True,'tag':REJ,'name':('An adaptive limiter','Um limitador adaptativo'),
   'how':('More state, and one noisy tenant lowers the cap for everyone.','Mais estado, e um tenant barulhento baixa o limite para todos.')},
 ],
 'outcome':('Settled 2026-11-19. B5b is estimated separately.','Decidida em 19/11/2026. A B5b tem estimativa própria.'),
}

DEC_VALUES = {
 'k':'decision','id':'B5-h','status':'set',
 'q':('What cap values ship?','Que valores de limite saem?'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Default 2, ceiling 4','Padrão 2, teto 4'),
   'how':('<code>maxInFlight</code> = <code>clamp(floor(flag value ?? 2), 1, 4)</code>. Batch rows run sequentially in v1. '
          'Raising the ceiling needs a scaled worker (with the DB pool checked against S2 and S11) and B5b.',
          '<code>maxInFlight</code> = <code>clamp(floor(valor da flag ?? 2), 1, 4)</code>. As linhas de batch rodam sequenciais na v1. '
          'Subir o teto exige um worker escalado (com o pool do banco conferido contra a S2 e a S11) e a B5b.')},
  {'ltr':'B','no':True,'tag':REJ,'name':('Default 4, ceiling 8','Padrão 4, teto 8'),
   'how':('One run could hold 8 of the platform&#x27;s 10 slots.','Um run poderia ocupar 8 dos 10 slots da plataforma.')},
 ],
 'outcome':('Settled 2026-11-19.','Decidida em 19/11/2026.'),
}

DECISIONS = [DEC_GATE, DEC_CANCEL, DEC_ORDER, DEC_FAIL, DEC_B6, DEC_CONTROL, DEC_LIMITS, DEC_VALUES]

PARTS = [
{'n':'1','title':('A parallel loop in <code>processFlow</code>','Um loop paralelo no <code>processFlow</code>'),
 'loc':'worker/src/modules/temporal/workflows/process-flow.workflow.ts',
 'purpose':('On B6&#x27;s version of the loop, the in-flight set fills up to <code>maxInFlight</code> and refills as each node settles.',
            'Na versão do loop da B6, o conjunto em voo enche até o <code>maxInFlight</code> e volta a encher conforme cada nó termina.'),
 'body':('<p>The patch marker <code>b5-parallel</code> is recorded only when <code>maxInFlight</code> &gt; 1; otherwise the current loop runs unchanged, '
         'with the same node order and history events, and histories recorded on B6 replay (B5-R1). The parallel loop calls <code>nextReady</code> until the set holds '
         '<code>maxInFlight</code> nodes, waits for the first to settle with <code>Promise.race</code>, applies its outcome (<code>ok</code>, <code>failed</code> or <code>cancelled</code>) '
         'in one synchronous step, and fills again (B5-R2). <code>maxInFlight</code> and <code>failFast</code> are optional fields of <code>ProcessFlowInput</code> and '
         '<code>ChildFlowInput</code>, and survive continue-as-new.</p>',
         '<p>O marcador de patch <code>b5-parallel</code> só é gravado quando o <code>maxInFlight</code> é &gt; 1; senão o loop atual roda sem mudança, '
         'com a mesma ordem de nós e os mesmos eventos de histórico, e os históricos gravados na B6 fazem replay (B5-R1). O loop paralelo chama o <code>nextReady</code> até o conjunto ter '
         '<code>maxInFlight</code> nós, espera o primeiro terminar com <code>Promise.race</code>, aplica o resultado dele (<code>ok</code>, <code>failed</code> ou <code>cancelled</code>) '
         'num único passo síncrono e enche de novo (B5-R2). <code>maxInFlight</code> e <code>failFast</code> são campos opcionais do <code>ProcessFlowInput</code> e do '
         '<code>ChildFlowInput</code>, e sobrevivem ao continue-as-new.</p>'),
 'ba':(('One node at a time: a flow with eight independent image generations takes the sum of the eight.',
        'Um nó por vez: um fluxo com oito gerações de imagem independentes leva a soma das oito.'),
       ('Up to <code>maxInFlight</code> ready nodes run together; in dev a 4-wide fan-out ran 1.84x faster at 2.',
        'Até <code>maxInFlight</code> nós prontos rodam juntos; em dev um fan-out de largura 4 rodou 1,84x mais rápido com 2.'))},

{'n':'2','title':('Rules per control-flow type','Regras por tipo de controle de fluxo'),
 'loc':'process-flow.workflow.ts · child-flow.workflow.ts',
 'purpose':('<code>arrayNode</code>, <code>conditionNode</code>, <code>fluxBox</code> and <code>libraryNode</code> run next to their siblings without breaking the loop&#x27;s state.',
            '<code>arrayNode</code>, <code>conditionNode</code>, <code>fluxBox</code> e <code>libraryNode</code> rodam ao lado dos irmãos sem quebrar o estado do loop.'),
 'list':[('<strong><code>arrayNode</code></strong> holds its body nodes while it runs. Iterations write the current item onto the array&#x27;s single row, so they stay sequential; '
          'a body node never runs outside the loop (<code>isHeldByArray</code>), and two arrays whose bodies overlap run one after the other (B5-R3).',
          '<strong><code>arrayNode</code></strong> reserva os nós do corpo enquanto roda. As iterações escrevem o item atual na única linha do array, então seguem sequenciais; '
          'um nó do corpo nunca roda fora do loop (<code>isHeldByArray</code>), e dois arrays cujos corpos se sobrepõem rodam um depois do outro (B5-R3).'),
         ('<strong><code>conditionNode</code></strong>: a dead-branch target has the condition as a gating predecessor, so a dead branch is never dispatched.',
          '<strong><code>conditionNode</code></strong>: o alvo de um ramo morto tem a condição como predecessor que bloqueia, então um ramo morto nunca é despachado.'),
         ('<strong><code>fluxObject</code> (Small Memory, A14)</strong> never runs; <code>processFlow</code> skips it like a <code>source</code> node, and its readers wait for its producers through ordinary edges. '
          'A flow in which a non-chat Small Memory is fed across a back edge of a cycle runs sequentially, because a reader dispatched beside that producer would miss its entry (B5-R12).',
          '<strong><code>fluxObject</code> (Small Memory, A14)</strong> nunca roda; o <code>processFlow</code> o pula como um nó <code>source</code>, e os leitores esperam os produtores por arestas comuns. '
          'Um flow em que uma Small Memory que não é de chat é alimentada por uma aresta de retorno de um ciclo roda em sequência, porque um leitor despachado ao lado desse produtor perderia a entrada (B5-R12).'),
         ('<strong><code>fluxBox</code> / <code>libraryNode</code></strong>: each call has its own run id, seed and workflow id, runs with the parent&#x27;s <code>maxInFlight</code> and keeps its own S1 chain (B5-R4). '
          'A continue-as-new inside a sub-flow now resumes as a sub-flow, which fixes a B6 bug.',
          '<strong><code>fluxBox</code> / <code>libraryNode</code></strong>: cada chamada tem o próprio run id, seed e workflow id, roda com o <code>maxInFlight</code> do pai e mantém a própria cadeia da S1 (B5-R4). '
          'Um continue-as-new dentro de um sub-flow agora retoma como sub-flow, o que corrige um bug da B6.')]},

{'n':'3','title':('Fail-fast, drain and continue-as-new','Fail-fast, drenagem e continue-as-new'),
 'loc':'process-flow.workflow.ts · activities.service.ts',
 'purpose':('The first genuine failure stops the run quickly without cancelling a sub-flow or a worker&#x27;s drain.',
            'A primeira falha genuína para o run rápido sem cancelar um sub-flow nem a drenagem de um worker.'),
 'body':('<p><strong>Fail-fast</strong> (<code>failFast</code> on, failure not a <code>WorkerShutdown</code>) cancels the scope that holds every in-flight leaf node, '
         'records the reason on each cancelled node&#x27;s row and its <code>node_finished</code> event, and waits for all of them to settle; '
         '<code>fluxBox</code> and <code>libraryNode</code> children run outside that scope and are awaited (B5-R5). '
         '<strong>Drain</strong> (flag off, or a <code>WorkerShutdown</code>) stops filling, lets every in-flight node finish, then fails the run; once a drain starts, a later failure cannot cancel. '
         '<strong>Continue-as-new</strong> happens only with no node in flight (B5-R6), and a failure during the drain wins over the continuation.</p>',
         '<p>O <strong>fail-fast</strong> (<code>failFast</code> ligado, falha que não é <code>WorkerShutdown</code>) cancela o escopo que guarda todo nó folha em voo, '
         'grava o motivo na linha de cada nó cancelado e no evento <code>node_finished</code> dele, e espera todos terminarem; '
         'os filhos <code>fluxBox</code> e <code>libraryNode</code> rodam fora desse escopo e são aguardados (B5-R5). '
         'A <strong>drenagem</strong> (flag desligada, ou um <code>WorkerShutdown</code>) para de encher, deixa todo nó em voo terminar e depois falha o run; depois que uma drenagem começa, uma falha posterior não cancela. '
         'O <strong>continue-as-new</strong> só acontece sem nó em voo (B5-R6), e uma falha durante a drenagem vence a continuação.</p>'),
 'callouts':[('mig',('A scale-in drains, it does not cancel','Um scale-in drena, não cancela'),
              ('A stopped worker gives its activities 100 s, then fails them with <code>WorkerShutdown</code> and retries once on another worker (A9c). '
               'Because B5 drains on <code>WorkerShutdown</code>, a scale-in never cancels healthy siblings (B5-R11).',
               'Um worker parado dá 100 s às activities, depois as falha com <code>WorkerShutdown</code> e tenta de novo uma vez em outro worker (A9c). '
               'Como a B5 drena em <code>WorkerShutdown</code>, um scale-in nunca cancela irmãos saudáveis (B5-R11).'))]},

{'n':'4','title':('The back decides the cap per run','O back decide o limite por run'),
 'loc':'back/src/app-api/flux/engine-selector.ts · flux.service.ts',
 'purpose':('<code>resolveParallelDispatchArgs</code> returns <code>maxInFlight</code> and <code>failFast</code> for the <code>apiV2</code> and Temporal-schedule starts; batch rows get neither in v1 (B5-R7).',
            'O <code>resolveParallelDispatchArgs</code> devolve <code>maxInFlight</code> e <code>failFast</code> para os inícios do <code>apiV2</code> e do schedule do Temporal; as linhas de batch não recebem nenhum dos dois na v1 (B5-R7).'),
 'body':('<p>It returns <code>clamp(floor(value ?? 2), 1, 4)</code> when the flow passes <code>canUseWorkflowForFlow</code> and the company that owns the flow is on <code>parallel_dispatch</code>. '
         'One seed migration (<code>SeedParallelDispatchFlags</code>) creates <code>parallel_dispatch</code> (off, value 2) and <code>parallel_fail_fast</code> (on). '
         'The worker deploys first: it ignores absent fields.</p>',
         '<p>Ele devolve <code>clamp(floor(valor ?? 2), 1, 4)</code> quando o fluxo passa no <code>canUseWorkflowForFlow</code> e a empresa dona do fluxo está na <code>parallel_dispatch</code>. '
         'Uma migration de seed (<code>SeedParallelDispatchFlags</code>) cria a <code>parallel_dispatch</code> (desligada, valor 2) e a <code>parallel_fail_fast</code> (ligada). '
         'O worker sobe antes: ele ignora campos ausentes.</p>')},

{'n':'5','title':('The run list shows every node in flight','A lista de runs mostra todo nó em voo'),
 'loc':'back/src/app-api/executions_logs/execution_logs.service.ts · FlowRunDto',
 'purpose':('Two places assumed one in-flight node: the run list and <code>settleAbandonedRuns</code>.',
            'Dois lugares supunham um só nó em voo: a lista de runs e o <code>settleAbandonedRuns</code>.'),
 'body':('<p><code>FlowRunDto.inFlightSteps</code> lists every in-flight node (<code>nodeId</code>, <code>execId</code>, <code>workflowId</code>) from one <code>json_agg</code>; '
         '<code>stepInterruptible</code> is true only when every in-flight node can stop, and <code>settleAbandonedRuns</code> checks every in-flight workflow (B5-R9). '
         'The query measured at parity with the old one on a local 1-million-row copy; it was not measured on a production-sized copy.</p>',
         '<p>O <code>FlowRunDto.inFlightSteps</code> lista todo nó em voo (<code>nodeId</code>, <code>execId</code>, <code>workflowId</code>) a partir de um único <code>json_agg</code>; '
         'o <code>stepInterruptible</code> só é verdadeiro quando todo nó em voo pode parar, e o <code>settleAbandonedRuns</code> confere todo workflow em voo (B5-R9). '
         'A consulta mediu igual à antiga numa cópia local de 1 milhão de linhas; não foi medida numa cópia do tamanho de produção.</p>')},

{'n':'6','title':('Ready for more replicas','Pronta para mais réplicas'),
 'loc':('ECS and RDS, read-only, 2026-11-19','ECS e RDS, só leitura, 19/11/2026'),
 'purpose':('B5 keeps no per-replica state, so it behaves the same with any number of worker and back replicas (B5-R11). '
            'Autoscaling for the worker, the back and the MCP server comes after B5; the Temporal server stays at 1 replica.',
            'A B5 não guarda estado por réplica, então se comporta igual com qualquer número de réplicas do worker e do back (B5-R11). '
            'O autoscaling do worker, do back e do MCP server vem depois da B5; o servidor do Temporal fica em 1 réplica.'),
 'list':[('<strong>Cap and decision</strong> travel in the run input and live in workflow state; any back replica returns the same value.',
          '<strong>Limite e decisão</strong> viajam na entrada do run e vivem no estado do workflow; qualquer réplica do back devolve o mesmo valor.'),
         ('<strong>DB connections</strong>: each worker replica opens a pool of 10 (S2). Check <code>max_connections</code> before raising the worker maximum.',
          '<strong>Conexões do banco</strong>: cada réplica do worker abre um pool de 10 (S2). Confira o <code>max_connections</code> antes de subir o máximo do worker.'),
         ('<strong>Provider limits</strong>: B5b ships before the worker maximum goes above 1.',
          '<strong>Limites de provedor</strong>: a B5b sobe antes de o máximo do worker passar de 1.'),
         ('<strong>The Temporal database is the real ceiling</strong>: a <code>db.t3.micro</code> whose CPU credit balance fell to 40 of 288 over 14 days. '
          'Resize it before the internal rollout, and lower the cap or pause the rollout if CPU, credits or free memory degrade.',
          '<strong>O banco do Temporal é o teto real</strong>: um <code>db.t3.micro</code> cujo saldo de créditos de CPU caiu para 40 de 288 em 14 dias. '
          'Redimensione antes do rollout interno, e baixe o limite ou pause o rollout se CPU, créditos ou memória livre piorarem.'),
         ('<strong>Cap ceiling</strong>: 4 is a code constant sized for 1 replica; raise it in the release that raises the worker maximum.',
          '<strong>Teto do limite</strong>: 4 é uma constante do código dimensionada para 1 réplica; suba no mesmo release que sobe o máximo do worker.')],
 'callouts':[('decide',('Open risk: tenant fairness with 1 replica','Risco aberto: justiça entre tenants com 1 réplica'),
              ('One run holds up to <code>maxInFlight</code> of the platform&#x27;s 10 slots, and each sub-flow level asks for up to that many more '
               '(16 slot requests at 2 and depth 3, which queue and do not fail). Mitigation: default 2, batch sequential, internal allowlist; '
               'revisit with the queue wait measured in the internal rollout.',
               'Um run ocupa até <code>maxInFlight</code> dos 10 slots da plataforma, e cada nível de sub-flow pede até esse tanto a mais '
               '(16 pedidos de slot com 2 e profundidade 3, que entram na fila e não falham). Mitigação: padrão 2, batch sequencial, allowlist interna; '
               'rever com a espera na fila medida no rollout interno.')),
             ('decide',('Accepted: fail-fast and side effects','Aceito: fail-fast e efeitos colaterais'),
              ('A cancelled <code>TRY_CANCEL</code> sibling (integrations, <code>pushData</code>, <code>sqlQuerier</code>, <code>mcp</code>, <code>largeMemory</code>, <code>fileSave</code>) '
               'finishes its write and is recorded cancelled; a re-run repeats the write. The cancel reason on the Logs page and <code>parallel_fail_fast</code> are the mitigation.',
               'Um irmão <code>TRY_CANCEL</code> cancelado (integrações, <code>pushData</code>, <code>sqlQuerier</code>, <code>mcp</code>, <code>largeMemory</code>, <code>fileSave</code>) '
               'termina a escrita e é registrado como cancelado; rodar de novo repete a escrita. O motivo do cancelamento na página de Logs e a <code>parallel_fail_fast</code> são a mitigação.'))]},
]

VERIF = [
 (True, ('Local: determinism and replay','Local: determinismo e replay'),
  ('Five histories recorded on B6 plus main, and a sixth with <code>maxInFlight</code> 2 that carries the patch marker; all 8 <code>process-flow-*</code> histories replay. '
   'Negative control: breaking determinism makes all 8 fail.',
   'Cinco históricos gravados na B6 mais o main, e um sexto com <code>maxInFlight</code> 2 que leva o marcador do patch; os 8 históricos <code>process-flow-*</code> fazem replay. '
   'Controle negativo: quebrar o determinismo faz os 8 falharem.')),
 (True, ('Local: cap, array hold, control flow, fail-fast, child status, drain','Local: limite, reserva do array, controle de fluxo, fail-fast, status do filho, drenagem'),
  ('30 parallel tests, each seen failing before it passed. Measured overlap in an 8-node fan-out: 3 at <code>maxInFlight</code> 3, 4 at 9 (ceiling), 1 at 1.9.',
   '30 testes do caminho paralelo, cada um visto falhando antes de passar. Sobreposição medida num fan-out de 8 nós: 3 com <code>maxInFlight</code> 3, 4 com 9 (teto), 1 com 1,9.')),
 (True, ('Dev: gate refusal and parallel run (2026-11-23)','Dev: recusa do gate e run paralelo (23/11/2026)'),
  ('Outside the allowlist or with an inline node: concurrency 1, no overlap. With the company added: concurrency 2, never above, in 6 runs of a 4-wide fan-out. Removing the company brings it back to 1.',
   'Fora da allowlist ou com um nó inline: concorrência 1, sem sobreposição. Com a empresa adicionada: concorrência 2, nunca acima, em 6 runs de um fan-out de largura 4. Tirar a empresa volta para 1.')),
 (True, ('Dev: determinism and events','Dev: determinismo e eventos'),
  ('10 of 10 runs of a no-AI fan-out have the same statuses and outputs. At <code>maxInFlight</code> 3 the run list returned 3 in-flight steps; the builder&#x27;s <code>room_status_updated</code> was not observed.',
   '10 de 10 runs de um fan-out sem IA têm os mesmos status e saídas. Com <code>maxInFlight</code> 3 a lista de runs devolveu 3 passos em voo; o <code>room_status_updated</code> do builder não foi observado.')),
 (True, ('Dev: two worker replicas','Dev: duas réplicas do worker'),
  ('Runs spread across both replicas and kept the cap of 2. With the replica running <code>processFlow</code> stopped, the workflow continued on the other with no nondeterminism error. '
   'Two long AI nodes on a stopped replica failed with <code>WorkerShutdown</code> after the 100 s grace, retried on the other replica and succeeded, with no sibling cancelled. '
   'The dev negative control was skipped; the local one stands.',
   'Os runs se espalharam pelas duas réplicas e mantiveram o limite de 2. Com a réplica que rodava o <code>processFlow</code> parada, o workflow continuou na outra sem erro de não determinismo. '
   'Dois nós de IA longos numa réplica parada falharam com <code>WorkerShutdown</code> depois da carência de 100 s, tentaram de novo na outra réplica e deram certo, sem nenhum irmão cancelado. '
   'O controle negativo em dev foi pulado; vale o local.')),
 (True, ('Dev: latency, which settles R4','Dev: latência, que resolve o R4'),
  ('Fan-out: p50 20.9 s off and 11.4 s on (1.84x). Reference shape (2 text generations next to 4 sub-flow calls): p50 71.5 s off and 37.7 s on (1.90x). '
   'The reference customer chain is mostly width 1, so its end-to-end gain stays about 1.2-1.5x.',
   'Fan-out: p50 de 20,9 s desligada e 11,4 s ligada (1,84x). Formato de referência (2 gerações de texto ao lado de 4 chamadas de sub-flow): p50 de 71,5 s desligada e 37,7 s ligada (1,90x). '
   'A cadeia do cliente de referência tem quase sempre largura 1, então o ganho de ponta a ponta fica em cerca de 1,2-1,5x.')),
 (True, ('Dev: schedule and batch (2026-11-24)','Dev: schedule e batch (24/11/2026)'),
  ('Schedule: a Temporal schedule fired the fan-out twice (<code>runType</code> <code>cronjob</code>): concurrency 2 in both runs, 11.3 s and 12.2 s against 20.9 s sequential; the schedule was then deleted. '
   'Batch: 3 rows of a fan-out in the allowlisted company: concurrency 1 inside every row, 22 to 23 s each, while the rows themselves ran at the same time. '
   'A batch needs a Variable Input node in the flow, or it fails before the first row.',
   'Schedule: um schedule do Temporal disparou o fan-out duas vezes (<code>runType</code> <code>cronjob</code>): concorrência 2 nos dois runs, 11,3 s e 12,2 s contra 20,9 s sequencial; depois o schedule foi apagado. '
   'Batch: 3 linhas de um fan-out na empresa da allowlist: concorrência 1 dentro de cada linha, 22 a 23 s cada, enquanto as linhas em si rodaram ao mesmo tempo. '
   'Um batch precisa de um nó Variable Input no fluxo, senão falha antes da primeira linha.')),
 (True, ('Production: measure before refusing','Produção: medir antes de recusar'),
  ('After B6 ships and B4 has soaked: classify every production flow as eligible or ineligible, name the type that disqualifies it, '
   'count the flows with a ready level wider than 1, and run the B5-c count before widening past internal companies. '
   'The count is an upper bound: on dev it never missed a flow that the scheduler flags (13 against 10 independent writer pairs among 2,432 worker flows). '
   'The docs page for parallel dispatch (docs#66) merges in the same release.',
   'Depois que a B6 subir e a B4 rodar o período de observação: classificar todo fluxo de produção como elegível ou inelegível, nomear o tipo que o desqualifica, '
   'contar os fluxos com um nível pronto de largura maior que 1, e rodar a contagem da B5-c antes de passar das empresas internas. '
   'A contagem é um teto: em dev ela nunca deixou de fora um fluxo que o scheduler marca (13 contra 10 pares de escrita independentes em 2.432 fluxos do worker). '
   'A página de docs do dispatch paralelo (docs#66) entra no mesmo release.')),
]

DONE = ('Eligible flows of allowlisted companies run their ready nodes concurrently up to <code>maxInFlight</code>; everything else runs as today; '
        'every local and dev check passed after being seen to fail; latency is measured on the fan-out flow and the reference use case.',
        'Fluxos elegíveis de empresas na allowlist rodam os nós prontos em paralelo até o <code>maxInFlight</code>; todo o resto roda como hoje; '
        'todo check local e de dev passou depois de ser visto falhando; a latência é medida no fluxo de fan-out e no caso de uso de referência.')

FILES = [('worker/src/modules/temporal/workflows/process-flow.workflow.ts', False),
         ('worker/src/modules/temporal/workflows/child-flow.types.ts, child-flow.workflow.ts', False),
         ('worker/src/modules/temporal/workflows/run-scheduled-flow.workflow.ts', False),
         ('worker/src/modules/temporal/activities/activities.service.ts', False),
         ('worker/src/modules/temporal/workflows/process-flow.parallel.spec.ts, replay-histories/', True),
         ('back/src/app-api/flux/engine-selector.ts', False),
         ('back/src/app-api/flux/flux.service.ts', False),
         ('back/src/shared/responses/scheduled-run.response.dto.ts', False),
         ('back/src/database/migrations/…-SeedParallelDispatchFlags.ts', True),
         ('back/src/app-api/executions_logs/execution_logs.service.ts', False)]

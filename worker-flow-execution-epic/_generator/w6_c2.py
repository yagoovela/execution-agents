# -*- coding: utf-8 -*-
TITLE = ('Retire the legacy surfaces, and settle the prefetch question',
         'Aposentar as superfícies legadas, e resolver a questão do prefetch')

GOAL = ('Remove the entry points and the flags that only existed to bridge the migration — and <b>decide the prefetch executor&#x27;s fate on evidence</b>.',
        'Remover as entradas e as flags que só existiam para atravessar a migração — e <b>decidir o destino do executor de prefetch com base em evidência</b>.')

GLANCE = [
 ('crit', ('Severity','Severidade'), ('Medium','Média'),
  ('Nothing here is a live outage — except <code>thirdPartyIntegration</code> taking two different paths depending on how it was started (§9.4).',
   'Nada aqui é uma queda ao vivo — exceto o <code>thirdPartyIntegration</code> tomando dois caminhos diferentes conforme foi iniciado (§9.4).')),
 ('dep', ('Depends on','Depende de'), ('C1 · B4','C1 · B4'),
  ('The endpoint can only be retired once <strong>every executable type runs in the worker</strong>.',
   'A entrada só pode ser aposentada quando <strong>todo tipo executável rodar no worker</strong>.')),
 ('wave', ('Wave','Onda'), ('Wave 6','Onda 6'),
  ('Last. <strong>This is where the old road is removed</strong> — the legacy endpoint, the second execution path, and every flag this epic created.',
   'Por último. <strong>É aqui que a estrada velha é removida</strong> — a entrada legada, a segunda via de execução, e toda flag que este épico criou.')),
 ('ship', ('Executes','Executa'), ('Decision D2','Decisão D2'),
  ('And it owns the measurement that answers it — <strong>the decision cannot be made anywhere else</strong>.',
   'E é dona da medição que a responde — <strong>a decisão não pode ser tomada em outro lugar</strong>.')),
]

LEDE = (
 '<p>Three separable pieces, all of them things that only existed to bridge the migration: the <strong>legacy single-node endpoint</strong> and its allowlist, '
 'the <strong>prefetch executor</strong> and its 17-type whitelist, and <strong>every migration flag this epic created</strong>.</p>'
 '<p>The middle one is the reason this task carries a decision rather than a checklist. Either answer about the prefetch executor is fine. '
 '<strong>Leaving it undecided is not: a dormant second execution path is a maintenance tax nobody is paying attention to.</strong></p>',
 '<p>Três peças separáveis, todas coisas que só existiam para atravessar a migração: a <strong>entrada legada de node único</strong> e sua allowlist, '
 'o <strong>executor de prefetch</strong> e seu whitelist de 17 tipos, e <strong>toda flag de migração que este épico criou</strong>.</p>'
 '<p>A do meio é a razão de esta task carregar uma decisão em vez de um checklist. Qualquer resposta sobre o executor de prefetch serve. '
 '<strong>Deixá-la sem resposta não serve: uma segunda via de execução dormente é um imposto de manutenção que ninguém está pagando atenção.</strong></p>')

TABLE = dict(
 head=[('Piece','Peça'),('Where','Onde'),('What removing it buys','O que remover traz'),('Blocked until','Bloqueada até')],
 rows=[
  [{'t':('The legacy single-node endpoint','A entrada legada de node único')},
   {'t':'temporal.controller.ts','mono':True},
   ('One less way for the same node to take a different path depending on how it was started',
    'Uma forma a menos de o mesmo node tomar um caminho diferente conforme foi iniciado'),
   {'t':('Every executable type runs in the worker','Todo tipo executável roda no worker'),'pill':'weak'}],
  [{'t':('The prefetch executor and its whitelist','O executor de prefetch e seu whitelist')},
   {'t':'app-api/flux/prefetch/','mono':True},
   ('A <strong>fourth list</strong> describing “what the worker can handle” leaves the world — if the measurement says retire',
    'Uma <strong>quarta lista</strong> descrevendo “o que o worker aguenta” sai do mundo — se a medição disser para aposentar'),
   {'t':('The measurement below, and <code>B3</code>','A medição abaixo, e a <code>B3</code>'),'pill':'weak'}],
  [{'t':('The migration flags','As flags de migração')},
   {'t':'PLAN §3.2','mono':True},
   ('Each removed flag is <strong>a branch of production behaviour nobody tests</strong>, gone',
    'Cada flag removida é <strong>um ramo de comportamento em produção que ninguém testa</strong>, eliminado'),
   {'t':('Each flag&#x27;s own node has soaked','O node de cada flag ter soakado'),'pill':'ok'}],
 ])

PROSE = (
 'One decision this task exists to <em>execute</em> — <code>D2</code>, the prefetch executor — and one smaller either/or the spec names outright. '
 '<code>D2</code>&#x27;s measurement is <code>A1</code>&#x27;s (Wave 2) and its answer is <code>B3</code>&#x27;s (Wave 4); this task carries out whichever answer won.',
 'Uma decisão que esta task existe para <em>executar</em> — a <code>D2</code>, o executor de prefetch — e um menor “ou isto ou aquilo” que a spec nomeia diretamente. '
 'A medição da <code>D2</code> é da <code>A1</code> (onda 2) e a resposta é da <code>B3</code> (onda 4); esta task executa a resposta que venceu.')

DEC_PREFETCH = {
 'k':'decision','id':'C2-a','plan':'D2','status':'open','open':True,
 'q':('Is the prefetch executor the destination for worker-side input resolution, or a stopgap to retire?',
      'O executor de prefetch é o destino da resolução de entrada no worker, ou um paliativo a aposentar?'),
 'intro':(
  '<strong>This is where <code>D2</code>&#x27;s answer is executed. The measurement is <code>A1</code>&#x27;s (Wave 2) and the answer is <code>B3</code>&#x27;s (Wave 4) — ownership split on 2026-09-02.</strong> '
  '<code>back/src/app-api/flux/prefetch/</code> is in production behind <code>FLUX_EXEC_MEMORY_MODE</code>, defaulting to <code>legacy</code>, with a '
  '17-type whitelist that <code>canUsePrefetchForFlow</code> requires <em>every</em> node in a flow to satisfy. '
  '<strong>Nothing below can be chosen before the measurement runs.</strong> Two numbers decide it: '
  '<em>how many production flows satisfy the whitelist</em>, and <em>of those, how many actually ran with the flag on — and what did it save, in memory, latency or row size</em>.',
  '<strong>É aqui que a resposta da <code>D2</code> é executada. A medição é da <code>A1</code> (onda 2) e a resposta é da <code>B3</code> (onda 4) — divisão de responsabilidade feita em 2026-09-02.</strong> '
  'O <code>back/src/app-api/flux/prefetch/</code> está em produção atrás do <code>FLUX_EXEC_MEMORY_MODE</code>, com padrão <code>legacy</code>, e um '
  'whitelist de 17 tipos que o <code>canUsePrefetchForFlow</code> exige que <em>todo</em> node do fluxo satisfaça. '
  '<strong>Nada abaixo pode ser escolhido antes de a medição rodar.</strong> Dois números decidem: '
  '<em>quantos fluxos em produção satisfazem o whitelist</em>, e <em>desses, quantos de fato rodaram com a flag ligada — e o que isso economizou, em memória, latência ou tamanho de linha</em>.'),
 'opts':[
  {'ltr':'A','name':('Destination — widen the whitelist and keep it','Destino — ampliar o whitelist e manter'),
   'tag':('if the numbers are real','se os números forem reais'),
   'how':('It is the model <code>B3</code> generalises: <code>scanPlaceholderRefs</code> finds only the refs a node uses, <code>loadOutputsByRefs</code> fetches only '
          'those rows. Widen the whitelist as the A track lands, and the prefetch path becomes the default.',
          'É o modelo que a <code>B3</code> generaliza: o <code>scanPlaceholderRefs</code> acha só as refs que o node usa, o <code>loadOutputsByRefs</code> busca só '
          'aquelas linhas. Amplie o whitelist conforme a trilha A entra, e o caminho de prefetch vira o padrão.'),
   'pros':[('The code exists, is in production, and has specs — promoting it is cheaper than building the same idea again',
            'O código existe, está em produção e tem specs — promovê-lo é mais barato que construir a mesma ideia de novo'),
           ('Reference-based input resolution is exactly what <code>B3</code> wants; this would be the same idea, already shipped',
            'Resolução de entrada por referência é exatamente o que a <code>B3</code> quer; seria a mesma ideia, já entregue')],
   'cons':[('<strong>Only defensible if the measurement shows real flows and a real saving.</strong> Promoting a path that never ran is promoting an untested path',
            '<strong>Só se defende se a medição mostrar fluxos reais e economia real.</strong> Promover um caminho que nunca rodou é promover um caminho não testado'),
           ('The whitelist stays a list, so the fourth “what can the worker handle” list survives the epic that existed to collapse them',
            'O whitelist continua sendo uma lista, então a quarta lista de “o que o worker aguenta” sobrevive ao épico que existia para colapsá-las')],
   'cost':[('lo',('Client sees: <b>nothing, either way</b>','Cliente vê: <b>nada, de todo modo</b>')),
           ('',('Ours: <b>a fourth list survives</b>','Nosso: <b>uma quarta lista sobrevive</b>'))]},
  {'ltr':'B','pick':True,'name':('Stopgap — retire the executor and its whitelist','Paliativo — aposentar o executor e o whitelist'),
   'tag':('most likely, on the evidence','mais provável, pela evidência'),
   'how':('<code>B3</code>&#x27;s worker-side resolution supersedes it. Delete <code>prefetch/</code>, delete <code>canUsePrefetchForFlow</code>, delete the flag — '
          'and <strong>a fourth list leaves the world</strong>.',
          'A resolução no worker da <code>B3</code> o substitui. Apague o <code>prefetch/</code>, apague o <code>canUsePrefetchForFlow</code>, apague a flag — '
          'e <strong>uma quarta lista sai do mundo</strong>.'),
   'pros':[('The whitelist has <strong>no LLM node in it</strong>, so a flow with a <code>commandTextNode</code> falls back to legacy — which may make the eligible count near zero',
            'O whitelist <strong>não tem nenhum node de LLM</strong>, então um fluxo com <code>commandTextNode</code> cai no legado — o que pode deixar a contagem de elegíveis perto de zero'),
           ('A second execution path that is dormant is worse than one that is used: nobody tests it and nobody notices when it rots',
            'Uma segunda via de execução dormente é pior que uma usada: ninguém a testa e ninguém percebe quando ela apodrece'),
           ('It is the outcome that matches goal <code>G3</code> — one implementation, one registry, one engine',
            'É o desfecho que corresponde à meta <code>G3</code> — uma implementação, um registro, um motor')],
   'cons':[('If the measurement shows a real saving on a real cohort of flows, this throws away working code that was already paid for',
            'Se a medição mostrar economia real numa coorte real de fluxos, isto joga fora código que funciona e já foi pago'),
           ('<code>B3</code> has to actually land first, or retiring the executor removes a capability before its replacement exists',
            'A <code>B3</code> precisa realmente entrar antes, senão aposentar o executor remove uma capacidade antes de o substituto existir')],
   'cost':[('lo',('Client sees: <b>nothing, either way</b>','Cliente vê: <b>nada, de todo modo</b>')),
           ('lo',('Ours: <b>one fewer execution path</b>','Nosso: <b>uma via de execução a menos</b>'))]},
  {'ltr':'C','name':('Keep it flag-gated, for a named narrow set','Manter atrás da flag, para um conjunto estreito e nomeado'),
   'tag':('needs an owner and an expiry','precisa de dono e de validade'),
   'how':('Keep the executor for the specific shape of flow the measurement proves it helps — and only that shape — with the whitelist frozen rather than widened.',
          'Manter o executor para o formato específico de fluxo em que a medição provar que ele ajuda — e só esse formato — com o whitelist congelado em vez de ampliado.'),
   'pros':[('Honest when the numbers are mixed: a real saving on a narrow set is a real saving',
            'Honesto quando os números são mistos: uma economia real num conjunto estreito é uma economia real'),
           ('Cheapest to do nothing about, which is exactly why it needs the two conditions below',
            'É a mais barata de não fazer nada a respeito, que é exatamente por isso que ela precisa das duas condições abaixo')],
   'cons':[('<strong>It is the status quo with a better story</strong> — the dormant second path stays, which is the tax the spec names',
            '<strong>É o status quo com uma história melhor</strong> — a segunda via dormente continua, que é o imposto que a spec nomeia'),
           ('Without a named owner and an expiry date, “narrow set” becomes “nobody remembers why this exists”',
            'Sem um dono nomeado e uma data de validade, “conjunto estreito” vira “ninguém lembra por que isto existe”')],
   'cost':[('lo',('Client sees: <b>nothing, either way</b>','Cliente vê: <b>nada, de todo modo</b>')),
           ('hi',('Ours: <b>two execution paths, permanently</b>','Nosso: <b>duas vias de execução, permanentemente</b>'))]},
 ],
 'rec':(
  '<p><strong>Run the measurement first, and let it pick.</strong> The evidence available today points at <code>B</code>: the whitelist requires <em>every</em> node in a '
  'flow to be on it, and no LLM node is on it — so a flow with a <code>commandTextNode</code> is ineligible by construction. If that makes the eligible count near '
  'zero, there is nothing to promote and nothing to keep.</p>'
  '<p>Two conditions on whichever answer wins. <strong>If <code>A</code>:</strong> the whitelist has to stop being a hand-maintained list and become derived from the '
  '<code>A1</code> registry, or the epic ends with the fourth list it set out to remove. <strong>If <code>C</code>:</strong> a named owner and an expiry date, '
  'or it is <code>A</code> by neglect.</p>'
  '<p>Sequencing, corrected 2026-09-02: <code>D2</code> gates <strong>Wave 4</strong> because <code>B3</code> needs the answer. The measurement is no longer pulled forward from here — '
  'it is <code>A1</code>&#x27;s, in Wave 2, where <code>canUsePrefetchForFlow</code> is already run against every stored flow. This task executes the answer in <strong>Wave 6</strong>.</p>',
  '<p><strong>Rode a medição primeiro, e deixe que ela escolha.</strong> A evidência disponível hoje aponta para a <code>B</code>: o whitelist exige que <em>todo</em> node de um '
  'fluxo esteja nele, e nenhum node de LLM está — então um fluxo com <code>commandTextNode</code> é inelegível por construção. Se isso deixar a contagem de elegíveis perto '
  'de zero, não há o que promover nem o que manter.</p>'
  '<p>Duas condições sobre qualquer resposta que vencer. <strong>Se for <code>A</code>:</strong> o whitelist precisa deixar de ser uma lista mantida à mão e passar a ser derivado do '
  'registro da <code>A1</code>, ou o épico termina com a quarta lista que ele se propôs a remover. <strong>Se for <code>C</code>:</strong> um dono nomeado e uma data de validade, '
  'ou vira <code>A</code> por descuido.</p>'
  '<p>Sequenciamento, corrigido em 2026-09-02: a <code>D2</code> bloqueia a <strong>onda 4</strong> porque a <code>B3</code> precisa da resposta. A medição não é mais antecipada a partir daqui — '
  'é da <code>A1</code>, na onda 2, onde o <code>canUsePrefetchForFlow</code> já é rodado contra todo fluxo guardado. Esta task executa a resposta na <strong>onda 6</strong>.</p>'),
 'who':[('A1 measures (Wave 2)','A A1 mede (onda 2)'),('B3 answers (Wave 4)','A B3 responde (onda 4)'),('C2 executes (Wave 6)','A C2 executa (onda 6)')],
}

DEC_TPI = {
 'k':'decision','id':'C2-b','status':'rec',
 'q':('<code>thirdPartyIntegration</code> takes two different paths. Fix it now, or carry it knowingly?',
      'O <code>thirdPartyIntegration</code> toma dois caminhos diferentes. Corrigir agora, ou carregar conscientemente?'),
 'intro':(
  'It is worker-routed <strong>inside a flow</strong>, via the integration gate — but it is still listed in <code>LEGACY_SINGLE_RUN_NODE_TYPES</code>, so '
  '<code>/process/single-node-legacy</code> runs it <strong>inline</strong>. <strong>The same node takes a different path depending on how it was started</strong> '
  '(analysis §9.4). The spec offers exactly two answers: fix it in <code>A1</code>&#x27;s wake, or record it here as knowingly carried until retirement. '
  'The one thing not on the menu is discovering it again later.',
  'Ele é roteado ao worker <strong>dentro de um fluxo</strong>, pelo gate de integração — mas ainda está listado em <code>LEGACY_SINGLE_RUN_NODE_TYPES</code>, então '
  'o <code>/process/single-node-legacy</code> o roda <strong>inline</strong>. <strong>O mesmo node toma um caminho diferente conforme foi iniciado</strong> '
  '(análise §9.4). A spec oferece exatamente duas respostas: corrigir na esteira da <code>A1</code>, ou registrar aqui como carregado conscientemente até a aposentadoria. '
  'A única coisa fora do cardápio é descobrir isso de novo mais tarde.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Fix it in <code>A1</code>&#x27;s wake','Corrigir na esteira da <code>A1</code>'),
   'tag':('recommended','recomendada'),
   'how':('Remove it from <code>LEGACY_SINGLE_RUN_NODE_TYPES</code> so <code>validateNode</code> refuses it and points the caller at the worker path — which is '
          'exactly what that allowlist already does for every other migrated type.',
          'Remover de <code>LEGACY_SINGLE_RUN_NODE_TYPES</code> para que o <code>validateNode</code> o recuse e aponte quem chamou para o caminho do worker — que é '
          'exatamente o que aquela allowlist já faz com todo outro tipo migrado.'),
   'pros':[('One node, one path. The inconsistency stops being something a reader has to know about',
            'Um node, um caminho. A inconsistência deixa de ser algo que o leitor precisa saber'),
           ('It is the behaviour the allowlist already implements for the other migrated types — this is a missing entry, not a new rule',
            'É o comportamento que a allowlist já implementa para os outros tipos migrados — é uma entrada faltando, não uma regra nova'),
           ('<code>A1</code> is the moment the lists are being reconciled anyway, so the cost is a line in work already happening',
            'A <code>A1</code> é o momento em que as listas estão sendo reconciliadas de qualquer forma, então o custo é uma linha num trabalho que já acontece')],
   'cons':[('A caller running that node from the single-node path today gets a refusal instead of a result, so it needs the same deprecation care as any refusing change',
            'Quem hoje roda esse node pelo caminho de node único passa a receber uma recusa em vez de um resultado, então precisa do mesmo cuidado de depreciação de qualquer mudança que recusa')],
   'cost':[('',('Client sees: <b>the worker result, consistently</b>','Cliente vê: <b>o resultado do worker, de forma consistente</b>')),
           ('lo',('Ours: <b>one allowlist entry</b>','Nosso: <b>uma entrada de allowlist</b>'))]},
  {'ltr':'B','name':('Record it as knowingly carried','Registrar como carregado conscientemente'),
   'how':('Leave the behaviour as it is, write the inconsistency down in this task with the reason, and delete it together with the endpoint at retirement.',
          'Deixar o comportamento como está, registrar a inconsistência nesta task com a razão, e apagá-la junto com a entrada na aposentadoria.'),
   'pros':[('Changes nothing for a caller that works today, which is the whole argument for it',
            'Não muda nada para quem chama e funciona hoje, que é o argumento inteiro a favor'),
           ('The endpoint is going away regardless, so the divergence has a known end date',
            'A entrada vai sumir de qualquer jeito, então a divergência tem uma data de fim conhecida')],
   'cons':[('Until then, the same node has <strong>two behaviours and two error taxonomies</strong> depending on which button started it',
            'Até lá, o mesmo node tem <strong>dois comportamentos e duas taxonomias de erro</strong> conforme o botão que o iniciou'),
           ('“Knowingly carried” is only true if it is actually written down — otherwise it is the same defect with a nicer name',
            '“Carregado conscientemente” só é verdade se estiver de fato registrado — do contrário é o mesmo defeito com um nome mais bonito')],
   'cost':[('hi',('Client risk: <b>two behaviours for one node</b>','Risco do cliente: <b>dois comportamentos para um node</b>')),
           ('lo',('Ours: <b>a paragraph, not a change</b>','Nosso: <b>um parágrafo, não uma mudança</b>'))]},
 ],
 'rec':(
  '<p><strong>A, because it is a missing allowlist entry rather than a design decision.</strong> The allowlist already refuses every other migrated type and points '
  'the caller at <code>/process/single-node</code>; <code>thirdPartyIntegration</code> is simply absent from that treatment.</p>'
  '<p>If <code>A</code> cannot be scheduled with <code>A1</code>, then <code>B</code> — but <strong>write it into this file</strong>, with the date and the reason. '
  'The failure mode being avoided is a third person finding it in six months and treating it as a new bug.</p>',
  '<p><strong>A, porque é uma entrada de allowlist faltando e não uma decisão de projeto.</strong> A allowlist já recusa todo outro tipo migrado e aponta '
  'quem chama para o <code>/process/single-node</code>; o <code>thirdPartyIntegration</code> apenas está ausente desse tratamento.</p>'
  '<p>Se a <code>A</code> não puder ser agendada junto com a <code>A1</code>, então a <code>B</code> — mas <strong>escreva isso neste arquivo</strong>, com a data e a razão. '
  'O modo de falha que se quer evitar é uma terceira pessoa achar isso em seis meses e tratar como bug novo.</p>'),
 'who':[('Engineering','Engenharia'),('A1&#x27;s owner, if it goes there','O dono da A1, se for para lá')],
}

DECISIONS = [DEC_PREFETCH, DEC_TPI]

PARTS = [
{'n':'1','title':('The legacy single-node endpoint','A entrada legada de node único'),
 'loc':'temporal.controller.ts · single-node-legacy.service.ts',
 'purpose':('Retire a router whose destination set becomes empty the moment every executable type runs in the worker.',
            'Aposentar um roteador cujo conjunto de destinos fica vazio no momento em que todo tipo executável roda no worker.'),
 'body':('<p><code>/process/single-node-legacy</code> lives at <code>back/src/temporal/temporal.controller.ts</code>, backed by '
         '<code>single-node-legacy/single-node-legacy.service.ts</code>. Its <code>validateNode</code> does three things: it '
         '<strong>refuses migrated types</strong>, it <strong>refuses mutating types</strong>, and it accepts only <code>LEGACY_SINGLE_RUN_NODE_TYPES</code>.</p>'
         '<p>Follow that to its conclusion. Once every executable type runs in the worker, <strong>this endpoint accepts nothing</strong> — '
         'it becomes a router with an empty destination set. Retire it, and retire the allowlist that feeds it.</p>',
         '<p>O <code>/process/single-node-legacy</code> vive em <code>back/src/temporal/temporal.controller.ts</code>, apoiado no '
         '<code>single-node-legacy/single-node-legacy.service.ts</code>. O <code>validateNode</code> dele faz três coisas: '
         '<strong>recusa tipos migrados</strong>, <strong>recusa tipos mutantes</strong>, e aceita apenas o <code>LEGACY_SINGLE_RUN_NODE_TYPES</code>.</p>'
         '<p>Leve isso à conclusão. Quando todo tipo executável rodar no worker, <strong>esta entrada não aceita mais nada</strong> — '
         'ela vira um roteador com conjunto de destinos vazio. Aposente a entrada, e aposente a allowlist que a alimenta.</p>'),
 'body2':('<p>The front side is a hard prerequisite, not a courtesy: <code>ProcessService.responseLegacy</code> '
          '(<code>front/src/service/processService.ts</code>) must have <strong>no callers</strong> before the endpoint goes. '
          '<strong>A silently-dead endpoint the front still calls is worse than keeping it.</strong></p>',
          '<p>O lado do front é pré-requisito duro, não cortesia: o <code>ProcessService.responseLegacy</code> '
          '(<code>front/src/service/processService.ts</code>) precisa estar <strong>sem chamadores</strong> antes de a entrada sair. '
          '<strong>Uma entrada silenciosamente morta que o front ainda chama é pior que mantê-la.</strong></p>'),
 'ba':(('One node type can be executed through two different endpoints with two different implementations, and which one you get depends on how the run was started.',
        'Um mesmo tipo de node pode ser executado por duas entradas diferentes com duas implementações diferentes, e qual delas você recebe depende de como o run foi iniciado.'),
       ('One way to run a node. The legacy endpoint returns a clear <code>404</code>/<code>410</code>, and the front has already stopped calling it.',
        'Uma forma de rodar um node. A entrada legada retorna um <code>404</code>/<code>410</code> claro, e o front já parou de chamá-la.'))},

{'n':'2','title':('What this task must not remove','O que esta task não pode remover'),
 'loc':('D18 · flux.controller.ts','D18 · flux.controller.ts'),
 'purpose':('Name the endpoints that look legacy and are not, before a sweep takes them with the ones that are.',
            'Nomear os endpoints que parecem legados e não são, antes que uma varredura os leve junto com os que são.'),
 'body':('<p><strong><code>D18</code> keeps the whole batch-process family.</strong> None of the five is deprecated: '
         '<code>POST /batch-process</code>, <code>GET /batch-process/:id/status</code>, '
         '<code>GET /batch-process/all</code>, <code>POST /batch-process/:id/stop</code> and '
         '<code>GET /batch-process/:ids/download</code>.</p>'
         '<p>The route stays as the entry point and its body moves into <code>B7</code>&#x27;s durable workflow. The status, listing, stop and download endpoints '
         'are the batch&#x27;s only surface; the screen that would read them is <strong>not built in this epic</strong> (B7, 2026-09-02), and they stay regardless.</p>',
         '<p><strong>A <code>D18</code> mantém toda a família batch-process.</strong> Nenhum dos cinco é depreciado: '
         '<code>POST /batch-process</code>, <code>GET /batch-process/:id/status</code>, '
         '<code>GET /batch-process/all</code>, <code>POST /batch-process/:id/stop</code> e '
         '<code>GET /batch-process/:ids/download</code>.</p>'
         '<p>A rota permanece como porta de entrada e o miolo dela vai para o workflow durável da <code>B7</code>. Os endpoints de status, listagem, stop e download '
         'são a única superfície do lote; a tela que os leria <strong>não é construída neste épico</strong> (B7, 2026-09-02), e eles ficam de qualquer forma.</p>'),
 'callouts':[('warn',('They look like the legacy endpoint and are not','Eles parecem o endpoint legado e não são'),
   ('<p>Both are older routes on the same controller, and both predate the worker. The difference is that one has no caller left and the other is the batch&#x27;s only surface. <strong>Check the list above before deleting anything named <code>batch</code>.</strong></p>',
    '<p>Os dois são rotas antigas no mesmo controller, e os dois são anteriores ao worker. A diferença é que um não tem mais chamador e o outro é a única superfície do lote. <strong>Confira a lista acima antes de apagar qualquer coisa chamada <code>batch</code>.</strong></p>'))]},

{'n':'3','title':('The prefetch executor — measure, then decide','O executor de prefetch — medir, e então decidir'),
 'loc':'app-api/flux/prefetch/ · flux.service.ts',
 'purpose':('Execute D2&#x27;s answer — the two numbers behind it were A1&#x27;s to report, and whatever could not be determined stays unverifiable, not zero.',
            'Executar a resposta da D2 — os dois números por trás dela eram da A1 reportar, e o que não pôde ser determinado continua não verificável, não zero.'),
 'body':('<p><code>back/src/app-api/flux/prefetch/</code> is <strong>in production</strong>, behind <code>FLUX_EXEC_MEMORY_MODE</code>, which defaults to '
         '<code>legacy</code>. <code>canUsePrefetchForFlow</code> then requires <strong>every</strong> node in a flow to be in this 17-type whitelist:</p>',
         '<p>O <code>back/src/app-api/flux/prefetch/</code> está <strong>em produção</strong>, atrás do <code>FLUX_EXEC_MEMORY_MODE</code>, cujo padrão é '
         '<code>legacy</code>. O <code>canUsePrefetchForFlow</code> então exige que <strong>todo</strong> node de um fluxo esteja neste whitelist de 17 tipos:</p>'),
 'code':('imageGenerator   webSearch      voiceBoxNode   audioReaderNode   commandContentNode\n'
         'pullData         pushData       mcpNode        thirdPartyIntegration\n'
         'libraryNode      webCrawling    reportBuilder  sqlQuerier        nodesBox\n'
         'comment          label          group',
         'imageGenerator   webSearch      voiceBoxNode   audioReaderNode   commandContentNode\n'
         'pullData         pushData       mcpNode        thirdPartyIntegration\n'
         'libraryNode      webCrawling    reportBuilder  sqlQuerier        nodesBox\n'
         'comment          label          group'),
 'body2':('<p>Read that list against the requirement that <em>every</em> node must be on it. <strong>There is no LLM node in it</strong> — a flow containing a '
          '<code>commandTextNode</code> is ineligible by construction. That is why the spec warns the eligible count <strong>may be near zero</strong>, and why '
          'the decision above cannot be made without running the query.</p>'
          '<p>Two measurements, then: how many production flows satisfy <code>canUsePrefetchForFlow</code>, and — of those — how many actually ran with the flag on, '
          'and what it saved in memory, latency or row size.</p>',
          '<p>Leia essa lista contra a exigência de que <em>todo</em> node esteja nela. <strong>Não há nenhum node de LLM ali</strong> — um fluxo com um '
          '<code>commandTextNode</code> é inelegível por construção. É por isso que a spec avisa que a contagem de elegíveis <strong>pode ser perto de zero</strong>, e por isso '
          'a decisão acima não pode ser tomada sem rodar a consulta.</p>'
          '<p>Duas medições, então: quantos fluxos em produção satisfazem o <code>canUsePrefetchForFlow</code>, e — desses — quantos de fato rodaram com a flag ligada, '
          'e o que isso economizou em memória, latência ou tamanho de linha.</p>'),
 'ba':(('A second execution path is live in production, dormant by default, and nobody can say how many flows it would even apply to.',
        'Uma segunda via de execução está viva em produção, dormente por padrão, e ninguém sabe dizer a quantos fluxos ela sequer se aplicaria.'),
       ('<code>D2</code>&#x27;s answer is <strong>executed, with A1&#x27;s numbers behind it</strong> — and whichever answer won, there is one execution path fewer to explain.',
        'A resposta da <code>D2</code> é <strong>executada, com os números da A1 por trás</strong> — e qualquer que tenha sido a resposta vencedora, há uma via de execução a menos para explicar.')),
 'callouts':[('decide',('Unknown is not zero','Desconhecido não é zero'),
   ('<p><code>PLAN §3.3.2</code> applied to the measurement itself: report flows whose eligibility you <strong>could not determine</strong> as '
    '<em>unverifiable</em>, not as ineligible. <strong>The prefetch decision must not rest on a count that quietly rounded unknowns to zero.</strong></p>',
    '<p><code>PLAN §3.3.2</code> aplicado à própria medição: reporte os fluxos cuja elegibilidade <strong>não pôde ser determinada</strong> como '
    '<em>não verificáveis</em>, não como inelegíveis. <strong>A decisão do prefetch não pode se apoiar numa contagem que arredondou desconhecidos para zero em silêncio.</strong></p>'))]},

{'n':'4','title':('The migration flags','As flags de migração'),
 'loc':'PLAN §3.2',
 'purpose':('Remove each flag once its node has soaked, because a flag that outlives its migration is untested production behaviour.',
            'Remover cada flag quando o node dela tiver soakado, porque uma flag que sobrevive à sua migração é comportamento de produção não testado.'),
 'body':('<p>Every flag from <code>PLAN §3.2</code> is <strong>temporary by construction</strong>. They exist so that a routing change can be added disabled, proved, '
         'and flipped in a separate deploy — which is what makes each task independently revertible.</p>'
         '<p>That justification expires. <strong>A flag that outlives its migration is a branch of production behaviour nobody tests</strong>, and it is the '
         'mechanism behind <code>R1</code>: two live paths and a switch between them.</p>',
         '<p>Toda flag do <code>PLAN §3.2</code> é <strong>temporária por construção</strong>. Elas existem para que uma mudança de roteamento possa ser adicionada desligada, provada, '
         'e virada num deploy separado — que é o que torna cada task reversível de forma independente.</p>'
         '<p>Essa justificativa vence. <strong>Uma flag que sobrevive à sua migração é um ramo de comportamento em produção que ninguém testa</strong>, e é o '
         'mecanismo por trás do <code>R1</code>: dois caminhos vivos e uma chave entre eles.</p>'),
 'ba':(('Every migration leaves a switch behind, and each switch is a production behaviour that has an owner only while somebody remembers it.',
        'Toda migração deixa uma chave para trás, e cada chave é um comportamento de produção que tem dono só enquanto alguém se lembra dela.'),
       ('<strong>No migration flag from this epic remains.</strong> One implementation of each node, one dispatch registry, one engine.',
        '<strong>Nenhuma flag de migração deste épico permanece.</strong> Uma implementação de cada node, um registro de dispatch, um motor.'))},
]

VERIF = [
 (True, ('Negative control — record the responses before removing','Controle negativo — registre as respostas antes de remover'),
  ('Call <code>/process/single-node-legacy</code> with <strong>each node type</strong> before retirement and record the response. After retirement, confirm the '
   'removal is a clear <code>404</code>/<code>410</code> and that <strong>the front never calls it</strong>. '
   'A silently-dead endpoint the front still calls is worse than keeping it.',
   'Chame o <code>/process/single-node-legacy</code> com <strong>cada tipo de node</strong> antes da aposentadoria e registre a resposta. Depois da aposentadoria, confirme que a '
   'remoção é um <code>404</code>/<code>410</code> claro e que <strong>o front nunca a chama</strong>. '
   'Uma entrada silenciosamente morta que o front ainda chama é pior que mantê-la.')),
 (True, ('Measure before refusing — applied to the measurement itself','Medir antes de recusar — aplicado à própria medição'),
  ('<strong>PLAN §3.3.2.</strong> Report flows whose eligibility you <strong>could not determine</strong> as <em>unverifiable</em>, not as ineligible. '
   '<strong>The prefetch decision must not rest on a count that quietly rounded unknowns to zero.</strong>',
   '<strong>PLAN §3.3.2.</strong> Reporte os fluxos cuja elegibilidade <strong>não pôde ser determinada</strong> como <em>não verificáveis</em>, não como inelegíveis. '
   '<strong>A decisão do prefetch não pode se apoiar numa contagem que arredondou desconhecidos para zero em silêncio.</strong>')),
 (False, ('Front check, before the endpoint goes','Checagem no front, antes de a entrada sair'),
  ('<code>ProcessService.responseLegacy</code> (<code>front/src/service/processService.ts</code>) must have <strong>no callers</strong>. '
   'This is the one item on this page that fails in a repo the backend PR does not touch.',
   'O <code>ProcessService.responseLegacy</code> (<code>front/src/service/processService.ts</code>) precisa estar <strong>sem chamadores</strong>. '
   'Este é o único item desta página que falha num repositório que o PR do backend não toca.')),
 (False, ('No flag from this epic survives it','Nenhuma flag deste épico sobrevive a ele'),
  ('Enumerate the flags from <code>PLAN §3.2</code> and confirm each one is gone once its node has soaked. '
   'A leftover flag is the mechanism behind <code>R1</code>, still armed.',
   'Enumere as flags do <code>PLAN §3.2</code> e confirme que cada uma sumiu quando o node dela soakou. '
   'Uma flag esquecida é o mecanismo por trás do <code>R1</code>, ainda armado.')),
]

DONE = ('The legacy endpoint and its allowlist are gone; <strong><code>D2</code>&#x27;s answer is executed, with the numbers behind it recorded</strong>; '
        'and <strong>no migration flag from this epic remains</strong>.',
        'A entrada legada e sua allowlist sumiram; <strong>a resposta da <code>D2</code> está executada, com os números por trás registrados</strong>; '
        'e <strong>nenhuma flag de migração deste épico permanece</strong>.')

FILES = [('back/src/temporal/temporal.controller.ts (/process/single-node-legacy)', False),
         ('back/src/temporal/single-node-legacy/**', False),
         ('back/src/app-api/flux/prefetch/** (memory-mode.ts owns FLUX_EXEC_MEMORY_MODE)', False),
         ('back/src/app-api/flux/flux.service.ts (PREFETCH_SUPPORTED_NODE_TYPES · canUsePrefetchForFlow · the isPrefetchMode() switch)', False),
         ('front/src/service/processService.ts', False)]

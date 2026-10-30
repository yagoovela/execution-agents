# -*- coding: utf-8 -*-
# A2 — Promote the finished modules and providers.
# Source: TASK-A2-PROMOTE-FINISHED-MODULES.md, corrected 2026-09-21 (all six node types shipped;
# provider queue rescoped: mcp done, clickup moved to TASK-A10, quickbooks dropped per PLAN §9);
# corrected again 2026-09-23 (done-when rewritten as a per-§3.4-point record with named owners).

TITLE=('Promote the finished modules and providers','Promover os módulos e provedores prontos')
GOAL=('Produce a <b>checkable record</b> that the six node types already in production are wired end to end, <b>point by point against PLAN §3.4</b> — each point either proved here or handed to the task that owns it, by name. <b>Verification, not a build</b>: nothing ships from this task.',
      'Produzir um <b>registro verificável</b> de que os seis tipos de node que já estão em produção estão ligados ponta a ponta, <b>ponto a ponto contra a PLAN §3.4</b> — cada ponto provado aqui ou entregue, pelo nome, à task dona dele. <b>Verificação, não uma construção</b>: nada sobe a partir desta task.')

GLANCE=[
 ('crit',('Severity','Severidade'),('Low — the risk this task named already resolved','Baixa — o risco que esta task nomeava já se resolveu'),
  ('<strong>Corrected 2026-09-21.</strong> All six node types and <code>mcp</code> are confirmed in production. What remains is confirming the wiring, not shipping anything.',
   '<strong>Corrigido em 21/09/2026.</strong> Os seis tipos de node e o <code>mcp</code> estão confirmados em produção. O que resta é confirmar a fiação, não subir nada.')),
 ('dep',('Depends on','Depende de'),('A1','A1'),
  ('A1 has shipped. Blocks nothing. <code>clickup</code>&#x27;s worker adapter — the one piece of this task&#x27;s original scope still undone — moved to <strong>TASK-A10</strong>.',
   'A A1 já subiu. Não bloqueia nada. O adaptador de worker do <code>clickup</code> — a única parte do escopo original desta task ainda não feita — foi para a <strong>TASK-A10</strong>.')),
 ('wave',('Wave','Onda'),('Wave 2','Onda 2'),
  ('Stays here because verifying the six is still the cheapest coverage-confirming work in the epic, even after the promotion itself is no longer this task&#x27;s to do.',
   'Continua aqui porque confirmar os seis ainda é o trabalho de confirmação de cobertura mais barato do épico, mesmo depois de a promoção em si não ser mais desta task.')),
 ('ship',('Watch out','Atenção'),('Three of the six still have an inline twin','Três dos seis ainda têm gêmeo inline'),
  ('<strong>Corrected 2026-09-23.</strong> <code>voiceBoxNode</code>, <code>webSearch</code> and <code>commandContentNode</code> run on the worker in a flow but inline on <code>/process/single-node-legacy</code>. A1 pins them with <code>it.failing</code>; <strong>C1</strong> removes them. A2 records this — it does not fix it.',
   '<strong>Corrigido em 23/09/2026.</strong> <code>voiceBoxNode</code>, <code>webSearch</code> e <code>commandContentNode</code> rodam no worker dentro de um fluxo, mas inline no <code>/process/single-node-legacy</code>. A A1 os fixa com <code>it.failing</code>; a <strong>C1</strong> os remove. A A2 registra isso — não conserta.')),
]

LEDE=(
 '<p><strong>Updated 2026-08-24.</strong> <code>mcpNode</code> shipped completely — worker enum, <code>mcp</code> module, <code>isTemporalNode</code>, legacy allowlist, and <code>mcp</code> as a migrated integration provider. It is done and out of this task.</p>'
 '<p><strong>Corrected 2026-09-21 — re-validated against <code>back@origin/production</code> <code>3804a524</code> and <code>worker@origin/main</code> <code>3e4c93a</code>. All six remaining node types have now shipped.</strong> <code>voice-generator</code>, <code>web-crawling</code>, <code>web-search</code>, <code>large-memory</code>, <code>pull-data</code>, <code>push-data</code> are all present in production with modules and registration: the worker&#x27;s <code>NodeType</code> enum has 20 entries, <code>node-activities.ts</code> dispatches 14 of them, and <code>process-single-node.workflow.ts</code> handles them as workflow cases. <code>flux.service.ts</code>&#x27;s <code>isTemporalNode</code> now lists all fourteen (§ TASK-A1). <strong>This task&#x27;s node-type half is done; only its evidence trail needed writing down.</strong></p>'
 '<p><strong>The integration-provider queue is the correction that still had open work — and it split into two different stories.</strong> <code>mcp</code> shipped 2026-08-24. <code>clickup</code>&#x27;s product feature shipped 2026-08-27 (back PR #1922, front PR #2134, ClickUp task 868j988uj) — <strong>entirely on the inline OAuth-connection path</strong>, not the worker-routed one this task promotes. No <code>clickup</code> adapter exists under <code>worker/src/modules/nodes/third-party-integration/adapters/</code>, and it is absent from <code>MIGRATED_INTEGRATION_PROVIDERS</code>. That gap is <strong>not a promotion</strong> — nothing about the worker half is finished — so it moved to <strong>TASK-A10</strong>, under the new standing rule (<code>PLAN.md</code> §3.6) this exact gap produced. <code>quickbooks</code> has <strong>zero presence</strong> in any repo — the only two string hits are prose and unrelated sample text, not code — so it is dropped until it is built (PLAN §9).</p>'
 '<p><strong>Corrected 2026-09-23 — re-validated against <code>back@origin/production</code> <code>a90d1ae6</code> and <code>worker@origin/main</code> <code>d9d7170</code>.</strong> The facts above hold. Two clauses of the 2026-09-21 done-when did not: <strong>“no <code>hasInlineTwin</code>” is false for three of the six by design</strong> — A1 derives it, pins <code>voiceBoxNode</code>, <code>webSearch</code> and <code>commandContentNode</code> with <code>it.failing</code>, and names C1 as their fixer — and <strong>“against PLAN §3.4” asks for points 3, 4 and 7, which other tasks own</strong>. The done-when is now a record in which every §3.4 point is either proved here or handed to its owner by name.</p>'
 '<p><strong>Two decisions, 2026-09-23.</strong> PLAN §3.4 point 4 keeps its wording: the three twins above live on <code>/process/single-node-legacy</code> and stay <strong>C1&#x27;s</strong>, not folded into §3.4. <strong>The title is kept although it no longer describes the task</strong> — A2 promotes nothing now; it verifies. Renaming would ripple through the pages, <code>TITLES_ALL.py</code> and ClickUp for a task that ships nothing. Read the goal, not the title.</p>',
 '<p><strong>Atualizado em 24/08/2026.</strong> O <code>mcpNode</code> subiu por completo — enum do worker, módulo <code>mcp</code>, <code>isTemporalNode</code>, allowlist legada, e <code>mcp</code> como provedor de integração migrado. Está pronto e fora desta task.</p>'
 '<p><strong>Corrigido em 21/09/2026 — revalidado contra <code>back@origin/production</code> <code>3804a524</code> e <code>worker@origin/main</code> <code>3e4c93a</code>. Os seis tipos de node restantes subiram.</strong> O <code>voice-generator</code>, <code>web-crawling</code>, <code>web-search</code>, <code>large-memory</code>, <code>pull-data</code>, <code>push-data</code> estão todos presentes em produção com módulo e registro: o enum <code>NodeType</code> do worker tem 20 entradas, o <code>node-activities.ts</code> despacha 14 delas, e o <code>process-single-node.workflow.ts</code> os trata como cases de workflow. O <code>isTemporalNode</code> do <code>flux.service.ts</code> agora lista os quatorze (§ TASK-A1). <strong>A metade de tipos de node desta task está pronta; só faltava escrever a trilha de evidência.</strong></p>'
 '<p><strong>A fila de provedores de integração é a correção que ainda tinha trabalho em aberto — e ela se dividiu em duas histórias diferentes.</strong> O <code>mcp</code> subiu em 24/08/2026. A funcionalidade de produto do <code>clickup</code> subiu em 27/08/2026 (PR #1922 do back, PR #2134 do front, task ClickUp 868j988uj) — <strong>inteiramente pelo caminho inline de conexão OAuth</strong>, não pelo roteado pelo worker que esta task promove. Não existe adaptador do <code>clickup</code> em <code>worker/src/modules/nodes/third-party-integration/adapters/</code>, e ele está ausente do <code>MIGRATED_INTEGRATION_PROVIDERS</code>. Essa lacuna <strong>não é uma promoção</strong> — nada da metade do worker está pronto — então foi para a <strong>TASK-A10</strong>, sob a nova regra permanente (<code>PLAN.md</code> §3.6) que essa mesma lacuna gerou. O <code>quickbooks</code> tem <strong>presença zero</strong> em qualquer repositório — as únicas duas ocorrências da string são prosa e texto de exemplo sem relação, não código — então fica fora até ser construído (PLAN §9).</p>'
 '<p><strong>Corrigido em 23/09/2026 — revalidado contra <code>back@origin/production</code> <code>a90d1ae6</code> e <code>worker@origin/main</code> <code>d9d7170</code>.</strong> Os fatos acima se mantêm. Duas cláusulas do critério de pronto de 21/09/2026 não: <strong>“sem <code>hasInlineTwin</code>” é falso para três dos seis, por projeto</strong> — a A1 deriva esse fato, fixa <code>voiceBoxNode</code>, <code>webSearch</code> e <code>commandContentNode</code> com <code>it.failing</code> e nomeia a C1 como quem os corrige — e <strong>“contra a PLAN §3.4” pede os pontos 3, 4 e 7, que são de outras tasks</strong>. O critério de pronto agora é um registro em que cada ponto da §3.4 é provado aqui ou entregue, pelo nome, à task dona.</p>'
 '<p><strong>Duas decisões, 23/09/2026.</strong> O ponto 4 da PLAN §3.4 mantém a redação: os três gêmeos acima ficam no <code>/process/single-node-legacy</code> e continuam sendo <strong>da C1</strong>, sem serem incorporados à §3.4. <strong>O título é mantido, embora não descreva mais a task</strong> — a A2 não promove mais nada; ela verifica. Renomear se espalharia pelas páginas, pelo <code>TITLES_ALL.py</code> e pelo ClickUp por uma task que não sobe nada. Leia o objetivo, não o título.</p>')

TABLE={'k':'table',
 'head':[('Node type','Tipo de node'),('Worker module','Módulo no worker'),
         ('In worker@origin/main, 2026-09-02?','Em worker@origin/main, 02/09/2026?'),('In production, 2026-09-21?','Em produção, 21/09/2026?')],
 'rows':[
  [{'t':'voiceBoxNode','mono':True},{'t':'voice-generator','mono':True},
   {'t':('no','não'),'pill':'no'},{'t':('yes','sim'),'pill':'ok'}],
  [{'t':'webCrawling','mono':True},{'t':'web-crawling','mono':True},
   {'t':('no','não'),'pill':'no'},
   ('<strong>yes</strong> (but see TASK-A1: not in either legacy allowlist, wrong refusal message on the legacy endpoint)',
    '<strong>sim</strong> (mas ver TASK-A1: não está em nenhum dos dois legacy allowlists, mensagem de recusa errada no endpoint legado)')],
  [{'t':'webSearch','mono':True},{'t':'web-search','mono':True},
   {'t':('no','não'),'pill':'no'},{'t':('yes','sim'),'pill':'ok'}],
  [{'t':'commandContentNode','mono':True},{'t':'large-memory','mono':True},
   {'t':('no','não'),'pill':'no'},{'t':('yes','sim'),'pill':'ok'}],
  [{'t':'pullData','mono':True},{'t':'pull-data','mono':True},
   {'t':('no','não'),'pill':'no'},{'t':('yes','sim'),'pill':'ok'}],
  [{'t':'pushData','mono':True},{'t':'push-data','mono':True},
   {'t':('no','não'),'pill':'no'},{'t':('yes','sim'),'pill':'ok'}],
 ]}

PROSE_PROVIDERS={'k':'prose','t':(
 '<strong>The table is kept for history</strong> — what it said on 2026-09-02, and what is true now. <code>mcpNode</code> is still the template: enum, module, <code>isTemporalNode</code>, allowlist and the provider list all moved together, which is what a finished migration looks like in this codebase. '
 'The six above now match that template too. <strong>The provider queue does not</strong>: <code>clickup</code> shipped its product feature without its worker half — new work, routed to TASK-A10 — and <code>quickbooks</code> has nothing built at all. <strong>A2&#x27;s provider queue is empty</strong>: <code>mcp</code> is done, <code>clickup</code> moved to A10, <code>quickbooks</code> stays in PLAN §9 until it exists.',
 '<strong>A tabela é mantida para histórico</strong> — o que ela dizia em 02/09/2026, e o que é verdade agora. O <code>mcpNode</code> continua o gabarito: enum, módulo, <code>isTemporalNode</code>, allowlist e a lista de provedores se moveram juntos, e é assim que uma migração concluída se parece neste código. '
 'Os seis acima agora também batem com esse gabarito. <strong>A fila de provedores não bate</strong>: o <code>clickup</code> subiu a funcionalidade de produto sem a metade do worker — trabalho novo, roteado para a TASK-A10 — e o <code>quickbooks</code> não tem nada construído. <strong>A fila de provedores da A2 está vazia</strong>: o <code>mcp</code> está pronto, o <code>clickup</code> foi para a A10, o <code>quickbooks</code> fica na PLAN §9 até existir.')}

DOD_TABLE={'k':'table',
 'head':[('PLAN §3.4 point','Ponto da PLAN §3.4'),('What A2 does','O que a A2 faz'),('Owner of any gap','Dono de qualquer lacuna')],
 'rows':[
  [('1. Registration chain','1. Cadeia de registro'),
   ('Prove per type, by file and symbol, including the workflow dispatch — a <code>switch</code> case (<code>LARGE_MEMORY</code>, <code>WEB_SEARCH</code>, <code>VOICE</code>) <strong>or</strong> an entry in <code>node-activities.ts</code>&#x27;s table resolved in the <code>default</code> branch (<code>PULL_DATA</code>, <code>PUSH_DATA</code>, <code>WEB_CRAWLING</code>)',
    'Provar por tipo, por arquivo e símbolo, inclusive o dispatch do workflow — um <code>case</code> no <code>switch</code> (<code>LARGE_MEMORY</code>, <code>WEB_SEARCH</code>, <code>VOICE</code>) <strong>ou</strong> uma entrada na tabela do <code>node-activities.ts</code> resolvida no ramo <code>default</code> (<code>PULL_DATA</code>, <code>PUSH_DATA</code>, <code>WEB_CRAWLING</code>)'),
   {'t':('A2','A2'),'pill':'ok'}],
  [('2. Dispatch registry','2. Registro de dispatch'),
   ('Prove the entry exists with <code>flowDispatch: &#x27;worker&#x27;</code> and <code>workerModule: true</code>','Provar que a entrada existe com <code>flowDispatch: &#x27;worker&#x27;</code> e <code>workerModule: true</code>'),
   {'t':('A2','A2'),'pill':'ok'}],
  [('3. Both entry paths','3. Os dois caminhos de entrada'),
   ('Prove a flow run and a single-node run (<code>executeSingleNode</code>) both reach the worker','Provar que um run de fluxo e um run de node único (<code>executeSingleNode</code>) chegam ao worker'),
   {'t':('Legacy endpoint: C3 (webCrawling) · C1 (three inline accepts)','Endpoint legado: C3 (webCrawling) · C1 (três aceites inline)'),'pill':'weak'}],
  [('4. No inline twin','4. Sem gêmeo inline'),
   ('Record the three <code>it.failing</code> pins as the known state','Registrar os três <code>it.failing</code> como o estado conhecido'),
   {'t':('C1','C1'),'pill':'weak'}],
  [('5. NodeError subclasses','5. Subclasses de NodeError'),
   ('Read each module&#x27;s error paths and record the subclass thrown','Ler os caminhos de erro de cada módulo e registrar a subclasse lançada'),
   {'t':('A failure becomes its own task','Uma falha vira task própria'),'pill':'weak'}],
  [('6. Negative control','6. Controle negativo'),
   ('Run one per dispatch mechanism (below)','Rodar um por mecanismo de dispatch (abaixo)'),
   {'t':('A2','A2'),'pill':'ok'}],
  [('7. Documentation','7. Documentação'),
   ('Record whether the node&#x27;s page and contract row exist','Registrar se a página do node e a linha do contrato existem'),
   {'t':('D1','D1'),'pill':'weak'}],
 ]}

PROSE_DOD={'k':'prose','t':(
 '<strong>No cell of the record is left blank.</strong> A point A2 cannot close is not a failure of A2 — it is a hand-off, and the hand-off is only real when it names the task that receives it. Keeping A2 open until C1, C3 and D1 land would make the cheapest task in the wave wait on three of the most expensive; fixing them here would break the Out clause that keeps this task revertible.',
 '<strong>Nenhuma célula do registro fica em branco.</strong> Um ponto que a A2 não consegue fechar não é falha da A2 — é uma entrega, e a entrega só é real quando nomeia a task que a recebe. Manter a A2 aberta até a C1, a C3 e a D1 entrarem faria a task mais barata da onda esperar por três das mais caras; consertá-los aqui quebraria a cláusula de fora-de-escopo que mantém esta task reversível.')}

DEC_STAGING={
 'k':'decision','id':'A2-a','status':'set','open':False, 'outcome':('Closed without a choice (2026-10-23). A2 became verification only, the <code>clickup</code> adapter shipped through A10, and back <code>staging</code> now has the same ten worker-routed providers as <code>main</code>.', 'Fechada sem escolha (23/10/2026). A A2 virou só verificação, o adaptador <code>clickup</code> foi entregue pela A10, e o <code>staging</code> do back agora tem os mesmos dez provedores roteados ao worker que o <code>main</code>.'),
 'q':('Staging was behind production for this file. Do we fix staging, route around it, or promote through it as it is?',
      'O staging estava atrás da produção para este arquivo. Consertamos o staging, contornamos, ou promovemos por ele como está?'),
 'intro':('<strong>Not re-measured in this correction.</strong> As of 2026-08-21 <code>back@origin/staging</code> still carried the pre-release <strong>six</strong> providers while production carried <strong>eight</strong> — staging was <em>behind</em> its own destination for this file. This decision governed the six-node-type and <code>mcp</code> promotion, which has since shipped by whatever route was actually taken. '
          '<strong>It stays relevant forward, not backward</strong>: the same staging-lag risk applies to any new worker-side change, including <strong>TASK-A10&#x27;s <code>clickup</code> adapter promotion</strong> — confirm staging again before that one ships.',
          '<strong>Não remedido nesta correção.</strong> Em 2026-08-21 o <code>back@origin/staging</code> ainda carregava os <strong>seis</strong> provedores pré-release enquanto a produção carregava <strong>oito</strong> — o staging estava <em>atrás</em> do próprio destino para este arquivo. Esta decisão regia a promoção dos seis tipos de node e do <code>mcp</code>, que desde então subiu pela rota que de fato foi tomada. '
          '<strong>Ela continua relevante para frente, não para trás</strong>: o mesmo risco de defasagem do staging vale para qualquer mudança nova do lado do worker, inclusive a <strong>promoção do adaptador <code>clickup</code> da TASK-A10</strong> — reconfira o staging antes de aquela subir.'),
 'opts':[
  {'ltr':'A','name':('Bring staging up to production first','Trazer o staging ao nível da produção primeiro'),
   'tag':('recommended','recomendada'),
   'how':('Reconcile <code>staging</code> with <code>production</code> for the touched file <em>before</em> the promotion branch touches it, so the soak happens against a real pre-production state.',
          'Reconciliar o <code>staging</code> com a <code>production</code> para o arquivo tocado <em>antes</em> de a branch de promoção encostar nele, para o soak acontecer contra um estado real de pré-produção.'),
   'pros':[('The soak means something again, and the “re-break or silently pass” fork simply disappears',
            'O soak volta a significar alguma coisa, e a bifurcação “quebra de novo ou passa em silêncio” simplesmente some')],
   'cons':[('It is a reconciliation stacked on top of whatever the promotion already needs',
            'É uma reconciliação empilhada sobre o que a promoção já precisa')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('',('Ours: <b>one extra reconciliation, up front</b>','Nosso: <b>uma reconciliação extra, no começo</b>'))]},
  {'ltr':'C','no':True,'name':('Promote through staging exactly as it is','Promover pelo staging exatamente como ele está'),
   'tag':('rejected','rejeitada'),
   'how':('Merge the promotion into the stale branch and ship from there, treating the soak as green because it was green.',
          'Mesclar a promoção na branch defasada e subir de lá, tratando o soak como verde porque ele ficou verde.'),
   'pros':[('Nothing to decide and nothing extra to do','Nada a decidir e nada a mais a fazer')],
   'cons':[('The older list travels forward and re-breaks production, or the merge resolves in production&#x27;s favour and the soak proves nothing — reported as green either way',
            'A lista antiga segue adiante e quebra a produção de novo, ou o merge resolve a favor da produção e o soak não prova nada — reportado como verde nos dois casos')],
   'cost':[('hi',('Client cost: <b>a possible production regression</b>','Custo do cliente: <b>uma possível regressão em produção</b>')),
           ('hi',('Ours: <b>a gate we can no longer trust</b>','Nosso: <b>um gate em que não dá mais para confiar</b>'))]},
 ],
 'rec':('<p><strong>A, applied forward.</strong> Whatever route the six-and-<code>mcp</code> promotion actually took is now history; the live application of this decision is TASK-A10&#x27;s <code>clickup</code> adapter, which faces the identical staging-lag question and should not assume it was already answered.</p>',
        '<p><strong>A, aplicada para a frente.</strong> Seja qual for a rota que a promoção dos seis mais o <code>mcp</code> de fato tomou, isso agora é histórico; a aplicação viva desta decisão é o adaptador <code>clickup</code> da TASK-A10, que enfrenta exatamente a mesma pergunta sobre defasagem do staging e não deve supor que ela já foi respondida.</p>'),
 'who':[('Engineering','Engenharia'),('Whoever owns the release route','Quem é dono da rota de release')],
}

PARTS=[
{'n':'1','title':('Fill the record, point by point','Preencher o registro, ponto a ponto'),
 'loc':'worker/src/modules/** · back/src/shared/node-dispatch/',
 'purpose':('Read-only against every repo. Each cell holds evidence — file and symbol, a test run, a run id — or the owner task.',
            'Somente leitura em todos os repositórios. Cada célula guarda evidência — arquivo e símbolo, um teste rodado, um id de run — ou a task dona.'),
 'body':('<p>For each of the six, fill points 1, 2 and 5 from the code, point 3 from the local Docker stack (a flow run and a single-node run: activity in Temporal, <code>node_executions</code> PENDING → COMPLETED, downstream node receives the output), and points 4 and 7 with their current state and owner. A node whose provider credential is not available locally is <strong>unverifiable</strong>, not passed.</p>',
         '<p>Para cada um dos seis, preencher os pontos 1, 2 e 5 a partir do código, o ponto 3 na stack Docker local (um run de fluxo e um run de node único: activity no Temporal, <code>node_executions</code> PENDING → COMPLETED, node seguinte recebe a saída), e os pontos 4 e 7 com o estado atual e o dono. Um node cuja credencial de provedor não está disponível localmente é <strong>não verificável</strong>, não aprovado.</p>'),
 'ba':(('The six were believed wired because they shipped; nothing had checked them against §3.4, and the old done-when asked for points other tasks own.',
        'Os seis eram tidos como ligados porque subiram; nada os tinha checado contra a §3.4, e o critério antigo pedia pontos que são de outras tasks.'),
       ('Every point of §3.4 has, for every one of the six, either evidence or a named owner.',
        'Todo ponto da §3.4 tem, para cada um dos seis, evidência ou um dono nomeado.')),
 'callouts':[('mig',('Scope — what this task does not do','Escopo — o que esta task não faz'),
   ('<p>No change to what a module does. The three inline twins are C1&#x27;s, <code>webCrawling</code>&#x27;s refusal message is C3&#x27;s, documentation is D1&#x27;s, <code>clickup</code>&#x27;s adapter is A10&#x27;s. <strong>A module that fails a point A2 owns becomes its own task.</strong></p>',
    '<p>Nenhuma mudança no que um módulo faz. Os três gêmeos inline são da C1, a mensagem de recusa do <code>webCrawling</code> é da C3, a documentação é da D1, o adaptador do <code>clickup</code> é da A10. <strong>Um módulo que falhar um ponto que é da A2 vira task própria.</strong></p>'))]},

{'n':'2','title':('Stop citing what is already done as open work','Parar de citar o que já está pronto como trabalho em aberto'),
 'loc':('this task file · STATUS.md · ClickUp','o arquivo desta task · STATUS.md · ClickUp'),
 'purpose':('The next reader must not re-open a closed question, nor mistake a hand-off for a gap.',
            'O próximo leitor não pode reabrir uma questão fechada, nem confundir uma entrega com uma lacuna.'),
 'body':('<p><code>clickup</code>&#x27;s worker adapter is <strong>explicitly routed to TASK-A10</strong>; <code>quickbooks</code> is <strong>explicitly out of scope</strong> (PLAN §9). <code>mcp</code> is confirmed done. The spec, <code>STATUS.md</code> and the ClickUp task must say the same thing when this task closes.</p>',
         '<p>O adaptador de worker do <code>clickup</code> está <strong>explicitamente roteado para a TASK-A10</strong>; o <code>quickbooks</code> está <strong>explicitamente fora de escopo</strong> (PLAN §9). O <code>mcp</code> está confirmado pronto. A spec, o <code>STATUS.md</code> e a task no ClickUp precisam dizer a mesma coisa quando esta task fechar.</p>'),
 'ba':(('The provider queue read as two items of the same shape, and the done-when mixed A2&#x27;s points with C1&#x27;s, C3&#x27;s and D1&#x27;s.',
        'A fila de provedores lia como dois itens do mesmo formato, e o critério de pronto misturava os pontos da A2 com os da C1, da C3 e da D1.'),
       ('Each item sits where its real state puts it, and the three documents agree.',
        'Cada item está onde o estado real dele o coloca, e os três documentos concordam.'))},
]

VERIF=[
 (True,('Negative control — one per dispatch mechanism','Controle negativo — um por mecanismo de dispatch'),
  ('Remove <code>LARGE_MEMORY</code>&#x27;s <code>switch</code> case from <code>process-single-node.workflow.ts</code>, and separately remove <code>PULL_DATA</code> from <code>node-activities.ts</code>&#x27;s table. Run their specs and record the failure: in both cases the <code>default</code> branch throws <code>Node type X not supported</code>, <strong>the exact failure a missing registration produces in production</strong>. A spec that stays green with the entry removed is vacuous — record it as a finding, do not count it.',
   'Remova o <code>case</code> de <code>LARGE_MEMORY</code> do <code>switch</code> em <code>process-single-node.workflow.ts</code> e, separadamente, remova <code>PULL_DATA</code> da tabela do <code>node-activities.ts</code>. Rode os testes e registre a falha: nos dois casos o ramo <code>default</code> lança <code>Node type X not supported</code>, <strong>exatamente a falha que um registro faltante produz em produção</strong>. Um teste que continua verde sem a entrada é vazio — registre como achado, não conte como cobertura.')),
 (True,('Per node, in the local Docker stack','Por node, na stack Docker local'),
  ('Run it in a flow <strong>and</strong> as a single node, and confirm: the <strong>activity appears in Temporal</strong>, <code>node_executions</code> goes <strong>PENDING → COMPLETED</strong>, and the <strong>downstream node receives the output</strong>. No provider credential locally means <strong>unverifiable</strong>, not passed.',
   'Rode em um fluxo <strong>e</strong> como node único, e confirme: a <strong>activity aparece no Temporal</strong>, o <code>node_executions</code> vai de <strong>PENDING → COMPLETED</strong>, e o <strong>node seguinte recebe a saída</strong>. Sem credencial do provedor localmente é <strong>não verificável</strong>, não aprovado.')),
]

DONE=('The record has a cell for <strong>every PLAN §3.4 point × each of the six types</strong>, each holding evidence or the named owner task; both negative controls were observed failing; <code>mcp</code> is confirmed done; <code>clickup</code> is routed to <strong>TASK-A10</strong> and <code>quickbooks</code> to PLAN §9; the spec, <code>STATUS.md</code> and ClickUp agree.',
      'O registro tem uma célula para <strong>cada ponto da PLAN §3.4 × cada um dos seis tipos</strong>, cada uma com evidência ou a task dona nomeada; os dois controles negativos foram vistos falhando; o <code>mcp</code> está confirmado pronto; o <code>clickup</code> está roteado para a <strong>TASK-A10</strong> e o <code>quickbooks</code> para a PLAN §9; a spec, o <code>STATUS.md</code> e o ClickUp concordam.')

FILES=[('worker/src/modules/nodes/{voice-generator,web-crawling,web-search,large-memory,pull-data,push-data}/ (verification only — already shipped)',False),
       ('worker/src/modules/nodes/nodes.types.ts',False),
       ('worker/src/modules/temporal/**',False),
       ('back/src/shared/node-dispatch/ (the A1 registry and its invariant spec)',False)]

BLOCKS=[
 {'k':'label','n':'1','t':('What was finished, and what is true now','O que estava pronto, e o que é verdade agora')},
 TABLE, PROSE_PROVIDERS,
 {'k':'label','n':'2','t':('What done means now — every §3.4 point, proved or handed off','O que pronto significa agora — cada ponto da §3.4, provado ou entregue')},
 DOD_TABLE, PROSE_DOD,
 {'k':'label','n':'3','t':('The decision this task raised — now forward-looking','A decisão que esta task levantou — agora olhando para frente')},
 DEC_STAGING,
 {'k':'label','n':'4','t':('What the task does, in two parts','O que a task faz, em duas partes')},
]
for p in PARTS:
    BLOCKS.append({'k':'part', **p})

TASK={'code':'A2','vnum':'6','title':TITLE,'goal':GOAL,'glance':GLANCE,'lede':LEDE,
      'blocks':BLOCKS,'verif':VERIF,'done':DONE,'files':FILES}

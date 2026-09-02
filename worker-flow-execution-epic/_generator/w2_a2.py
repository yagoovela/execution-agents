# -*- coding: utf-8 -*-

TITLE=('Promote the finished modules and providers','Promover os módulos e provedores prontos')
GOAL=('Get the <b>six node types and two providers</b> that are already finished into production. This is <b>release work, not engineering</b>: verify what is in test against the definition of done, and promote it.',
      'Levar para produção os <b>seis tipos de node e dois provedores</b> que já estão prontos. Isto é <b>trabalho de release, não de engenharia</b>: conferir o que está em teste contra a definição de pronto, e promover.')

GLANCE=[
 ('crit',('Severity','Severidade'),('Nothing is broken','Nada está quebrado'),
  ('Six finished worker modules and two finished providers are simply <strong>not in production</strong>.',
   'Seis módulos de worker prontos e dois provedores prontos simplesmente <strong>não estão em produção</strong>.')),
 ('dep',('Depends on','Depende de'),('A1','A1'),
  ('Blocks nothing — but it is the <strong>cheapest coverage in the epic</strong>. The work is already written.',
   'Não bloqueia nada — mas é a <strong>cobertura mais barata do épico</strong>. O trabalho já está escrito.')),
 ('wave',('Wave','Onda'),('Wave 2','Onda 2'),
  ('Rollback is “do not promote”, which is why it can sit next to A1 without adding risk to the wave.',
   'O rollback é “não promover”, e é por isso que ela pode ficar ao lado da A1 sem somar risco à onda.')),
 ('ship',('Watch out','Atenção'),('The gap widened','A distância aumentou'),
  ('The <code>mcpNode</code> line went all the way to production while these six stayed parked. <strong>Find out what is blocking that merge before starting</strong> (analysis §12.4).',
   'A linha do <code>mcpNode</code> foi até produção enquanto estes seis ficaram parados. <strong>Descubra o que trava esse merge antes de começar</strong> (análise §12.4).')),
]

LEDE=(
 '<p><strong>Updated 2026-08-24.</strong> <code>mcpNode</code> shipped completely — worker enum, <code>mcp</code> module, <code>isTemporalNode</code>, legacy allowlist, and <code>mcp</code> as a migrated integration provider. '
 'It is done and out of this task. <strong>Six</strong> node types remain, and — corrected 2026-09-02, only production counts — they are <strong>not in <code>worker@origin/main</code></strong>; they are in test on the dev environment (analysis §12).</p>'
 '<p>The first draft framed this as reconciling a chore branch that had reached no environment; that framing is dropped. Where the six sit before production is the release pipeline&#x27;s business. If the dev line and production have diverged, resolving it is a step of the promotion, not the task&#x27;s premise.</p>',
 '<p><strong>Atualizado em 2026-08-24.</strong> O <code>mcpNode</code> subiu por completo — enum do worker, módulo <code>mcp</code>, <code>isTemporalNode</code>, allowlist legada, e <code>mcp</code> como provedor de integração migrado. '
 'Está pronto e fora desta task. Restam <strong>seis</strong> tipos de node, e — corrigido em 2026-09-02, só produção conta — <strong>não estão em <code>worker@origin/main</code></strong>; estão em teste no ambiente de dev (análise §12).</p>'
 '<p>A primeira versão tratava isto como reconciliar uma branch chore que não tinha chegado a nenhum ambiente; esse enquadramento foi descartado. Onde os seis estão antes da produção é assunto do pipeline de release. Se a linha de dev e a produção divergiram, resolver isso é um passo da promoção, não a premissa da task.</p>')

TABLE={'k':'table',
 'head':[('Finished work','Trabalho pronto'),('Worker module / adapter','Módulo / adaptador no worker'),
         ('Where it is today','Onde está hoje'),('Reached production?','Chegou à produção?')],
 'rows':[
  [{'t':'voiceBoxNode','mono':True},{'t':'voice-generator','mono':True},
   ('In test (dev)','Em teste (dev)'),{'t':('Not in production','Não está em produção'),'pill':'no'}],
  [{'t':'webCrawling','mono':True},{'t':'web-crawling','mono':True},
   ('In test (dev)','Em teste (dev)'),{'t':('Not in production','Não está em produção'),'pill':'no'}],
  [{'t':'webSearch','mono':True},{'t':'web-search','mono':True},
   ('In test (dev)','Em teste (dev)'),{'t':('Not in production','Não está em produção'),'pill':'no'}],
  [{'t':'commandContentNode','mono':True},{'t':'large-memory','mono':True},
   ('In test (dev)','Em teste (dev)'),{'t':('Not in production','Não está em produção'),'pill':'no'}],
  [{'t':'pullData','mono':True},{'t':'pull-data','mono':True},
   ('In test (dev)','Em teste (dev)'),{'t':('Not in production','Não está em produção'),'pill':'no'}],
  [{'t':'pushData','mono':True},{'t':'push-data','mono':True},
   ('In test (dev)','Em teste (dev)'),{'t':('Not in production','Não está em produção'),'pill':'no'}],
  [{'t':'clickup (provider)','mono':True},{'t':'clickup.adapter.ts','mono':True},
   ('<code>worker@origin/develop</code> and <code>MIGRATED_INTEGRATION_PROVIDERS</code> on <code>back@origin/master</code>',
    '<code>worker@origin/develop</code> e <code>MIGRATED_INTEGRATION_PROVIDERS</code> em <code>back@origin/master</code>'),
   {'t':('Dev only','Só em dev'),'pill':'weak'}],
  [{'t':'quickbooks (provider)','mono':True},{'t':'quickbooks.adapter.ts','mono':True},
   ('<code>worker@origin/develop</code> and <code>MIGRATED_INTEGRATION_PROVIDERS</code> on <code>back@origin/master</code>',
    '<code>worker@origin/develop</code> e <code>MIGRATED_INTEGRATION_PROVIDERS</code> em <code>back@origin/master</code>'),
   {'t':('Dev only','Só em dev'),'pill':'weak'}],
  [{'t':'mcpNode + mcp (provider)','mono':True},{'t':'mcp/ · mcp.adapter.ts','mono':True},
   ('Shipped 2026-08-24, through every gate at once','Subiu em 2026-08-24, por todos os gates de uma vez'),
   {'t':('Yes — out of this task','Sim — fora desta task'),'pill':'ok'}],
 ]}

PROSE_QUEUE={'k':'prose','t':(
 'The last row is not filler. <strong><code>mcpNode</code> is the template</strong>: enum, module, <code>isTemporalNode</code>, allowlist and the provider list all moved together, which is what a finished migration looks like in this codebase. '
 'Everything above it has the worker half and is missing the trip. <strong>The two providers are a second queue of the same shape</strong> — the promotion mechanics are identical, and splitting them would mean reconciling the same branches twice.',
 'A última linha não é enfeite. <strong>O <code>mcpNode</code> é o gabarito</strong>: enum, módulo, <code>isTemporalNode</code>, allowlist e a lista de provedores se moveram juntos, e é assim que uma migração concluída se parece neste código. '
 'Tudo acima dele tem a metade do worker e não tem a viagem. <strong>Os dois provedores são uma segunda fila com o mesmo formato</strong> — a mecânica de promoção é idêntica, e separá-los significaria reconciliar as mesmas branches duas vezes.')}

DEC_STAGING={
 'k':'decision','id':'A2-a','status':'open','open':True,
 'q':('Staging is behind production for this file. Do we fix staging, route around it, or promote through it as it is?',
      'O staging está atrás da produção para este arquivo. Consertamos o staging, contornamos, ou promovemos por ele como está?'),
 'intro':('The spec makes this a precondition, not an afterthought. As of 2026-08-21 <code>back@origin/staging</code> still carried the pre-release <strong>six</strong> providers while production carried <strong>eight</strong> — '
          'staging is <em>behind</em> its own destination for this file. A promotion routed through it is not a rehearsal: it will either <strong>re-break production</strong> by carrying the older list forward, or <strong>silently pass</strong> and prove nothing. '
          'This set is six node types and two providers at once, so it is the worst possible release to rehearse badly.',
          'A spec trata isto como pré-condição, não como detalhe. Em 2026-08-21 o <code>back@origin/staging</code> ainda carregava os <strong>seis</strong> provedores pré-release enquanto a produção carregava <strong>oito</strong> — '
          'o staging está <em>atrás</em> do próprio destino para este arquivo. Uma promoção que passa por ele não é ensaio: ou <strong>quebra a produção de novo</strong> levando a lista antiga adiante, ou <strong>passa em silêncio</strong> e não prova nada. '
          'Este conjunto são seis tipos de node e dois provedores de uma vez, ou seja, o pior release possível para ensaiar mal.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Bring staging up to production first','Trazer o staging ao nível da produção primeiro'),
   'tag':('recommended','recomendada'),
   'how':('Reconcile <code>staging</code> with <code>production</code> for this file <em>before</em> the promotion branch touches it, so the soak happens against a real pre-production state.',
          'Reconciliar o <code>staging</code> com a <code>production</code> para este arquivo <em>antes</em> de a branch de promoção encostar nele, para o soak acontecer contra um estado real de pré-produção.'),
   'pros':[('The soak means something again, and the “re-break or silently pass” fork simply disappears',
            'O soak volta a significar alguma coisa, e a bifurcação “quebra de novo ou passa em silêncio” simplesmente some'),
           ('Whatever made staging drift is found <strong>now</strong>, while one file is involved, instead of during a release with eight changes in flight',
            'O que fez o staging defasar é descoberto <strong>agora</strong>, com um arquivo envolvido, em vez de durante um release com oito mudanças em voo'),
           ('Every later task in the epic inherits a staging that can be trusted',
            'Toda task posterior do épico herda um staging em que se pode confiar')],
   'cons':[('It is a second reconciliation stacked on the one this task already owns',
            'É uma segunda reconciliação empilhada sobre a que esta task já carrega'),
           ('It needs whoever owns the release route to confirm the drift was not deliberate — that is a person, not a command',
            'Exige que o dono da rota de release confirme que a defasagem não foi deliberada — isso é uma pessoa, não um comando')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('',('Ours: <b>one extra reconciliation, up front</b>','Nosso: <b>uma reconciliação extra, no começo</b>'))]},
  {'ltr':'B','name':('Route around staging, as the <code>mcpNode</code> line evidently did',
                     'Contornar o staging, como a linha do <code>mcpNode</code> evidentemente fez'),
   'how':('Promote <code>develop</code> → PR to production, and accept that staging is not on this path. Analysis §10.3 is explicit that whatever route the 2026-08-21 release took, <strong>it did not go through staging</strong>.',
          'Promover <code>develop</code> → PR para produção, aceitando que o staging não está neste caminho. A análise §10.3 é explícita: qualquer que tenha sido a rota do release de 2026-08-21, <strong>ela não passou pelo staging</strong>.'),
   'pros':[('Demonstrably a route that works — a complete node type reached production through it',
            'É comprovadamente uma rota que funciona — um tipo de node completo chegou à produção por ela'),
           ('No second reconciliation, so the task stays the size the plan assumed',
            'Sem segunda reconciliação, então a task fica do tamanho que o plano supôs')],
   'cons':[('The promotion loses its rehearsal, on the <strong>largest single coverage change in the epic</strong>',
            'A promoção perde o ensaio, justamente na <strong>maior mudança de cobertura do épico</strong>'),
           ('It makes the drift permanent: the next task inherits a staging that is further behind than this one found it',
            'Torna a defasagem permanente: a próxima task herda um staging mais atrasado do que esta encontrou'),
           ('If it is the real route, it is undocumented — and an undocumented route is one person&#x27;s knowledge',
            'Se for a rota real, ela não está documentada — e uma rota não documentada é o conhecimento de uma pessoa só')],
   'cost':[('hi',('Client cost: <b>an unrehearsed release of eight changes</b>','Custo do cliente: <b>um release sem ensaio, com oito mudanças</b>')),
           ('lo',('Ours: <b>nothing extra</b>','Nosso: <b>nada a mais</b>'))]},
  {'ltr':'C','no':True,'name':('Promote through staging exactly as it is','Promover pelo staging exatamente como ele está'),
   'tag':('rejected','rejeitada'),
   'how':('Merge the promotion into the stale branch and ship from there, treating the soak as green because it was green.',
          'Mesclar a promoção na branch defasada e subir de lá, tratando o soak como verde porque ele ficou verde.'),
   'pros':[('Nothing to decide and nothing extra to do','Nada a decidir e nada a mais a fazer')],
   'cons':[('This is the case the spec names: the older provider list travels forward and <strong>re-breaks production</strong>',
            'É o caso que a spec nomeia: a lista antiga de provedores segue adiante e <strong>quebra a produção de novo</strong>'),
           ('Or the merge resolves in production&#x27;s favour and <strong>the soak proved nothing</strong> — reported as a green gate either way',
            'Ou o merge resolve a favor da produção e <strong>o soak não provou nada</strong> — reportado como gate verde nos dois casos'),
           ('A green gate that means nothing is worse than no gate, because the next release trusts it more',
            'Um gate verde que não significa nada é pior que gate nenhum, porque o próximo release confia mais nele')],
   'cost':[('hi',('Client cost: <b>a possible production regression</b>','Custo do cliente: <b>uma possível regressão em produção</b>')),
           ('hi',('Ours: <b>a gate we can no longer trust</b>','Nosso: <b>um gate em que não dá mais para confiar</b>'))]},
 ],
 'rec':('<p><strong>A — and confirm the cause before choosing, because the confirmation is one conversation.</strong> “Is staging deliberately out of the path for this file?” has an owner, and asking is cheaper than discovering.</p>'
        '<p>If the answer turns out to be yes, then <strong>B is not a workaround — it is the documented route</strong>, and this task should write it down as one. What must not happen is C by default: merging into a branch that is behind production and calling the result a soak.</p>',
        '<p><strong>A — e confirme a causa antes de escolher, porque a confirmação é uma conversa só.</strong> “O staging está deliberadamente fora do caminho para este arquivo?” tem um dono, e perguntar é mais barato que descobrir.</p>'
        '<p>Se a resposta for sim, então <strong>a B não é gambiarra — é a rota documentada</strong>, e esta task deveria registrá-la como tal. O que não pode acontecer é a C por omissão: mesclar numa branch atrás da produção e chamar o resultado de soak.</p>'),
 'who':[('Engineering','Engenharia'),('Whoever owns the release route','Quem é dono da rota de release')],
}

PARTS=[
{'n':'1','title':('Find out what is blocking the merge, before merging',
                  'Descobrir o que trava o merge, antes de mesclar'),
 'loc':'worker@origin/develop (in test) → main',
 'purpose':('A branch that has survived a whole release cycle unmerged is telling you something. Assume “merge conflict” only after looking.',
            'Uma branch que sobreviveu a um ciclo de release inteiro sem ser mesclada está dizendo alguma coisa. Suponha “conflito de merge” só depois de olhar.'),
 'body':('<p>Take the dev line as it is in test. If it and production have diverged, merge — and <strong>expect conflicts</strong>, because the lines moved while the migration was in flight.</p>'
         '<p><strong>Union resolution — keep both sides, lose no code.</strong> <code>-X ours</code> is banned here; it produces a clean merge that silently discards a side, which is the one failure mode this reconciliation cannot survive. '
         'The policy was already paid for once and written down: <code>worker-thirdparty-integration-migration/DEV-RECONCILIATION.md</code>. Follow it rather than rediscovering it.</p>',
         '<p>Pegue a linha de dev como está em teste. Se ela e a produção divergiram, mescle — e <strong>espere conflitos</strong>, porque as linhas andaram enquanto a migração estava em voo.</p>'
         '<p><strong>Resolução por união — manter os dois lados, não perder código.</strong> O <code>-X ours</code> está proibido aqui; ele produz um merge limpo que descarta um lado em silêncio, que é o único modo de falha que esta reconciliação não sobrevive. '
         'A política já foi paga uma vez e está escrita: <code>worker-thirdparty-integration-migration/DEV-RECONCILIATION.md</code>. Siga-a em vez de redescobri-la.</p>'),
 'ba':(('Six finished modules are in test and not in production; production is the only environment this spec counts.',
        'Seis módulos prontos estão em teste e não em produção; produção é o único ambiente que esta spec conta.'),
       ('Whatever diverged is reconciled with <strong>every side kept</strong>, and the six are on the branch that ships.',
        'O que divergiu é reconciliado com <strong>todos os lados preservados</strong>, e os seis ficam na branch que sobe.')),
 'callouts':[('mig',('Scope — what this task does not do','Escopo — o que esta task não faz'),
   ('<p>No change to what those modules do. <strong>If a module fails the definition of done, that failure becomes its own task</strong> — do not fix it inside the promotion. '
    'A promotion that also repairs things cannot be reverted by not promoting, and “revert by not promoting” is the entire reason this task is cheap.</p>',
    '<p>Nenhuma mudança no que esses módulos fazem. <strong>Se um módulo falhar a definição de pronto, essa falha vira uma task própria</strong> — não conserte dentro da promoção. '
    'Uma promoção que também conserta coisas não pode ser revertida deixando de promover, e “reverter deixando de promover” é a razão inteira de esta task ser barata.</p>'))]},

{'n':'2','title':('Verify the registration chain — then verify the back side exists',
                  'Verificar a cadeia de registro — e depois verificar que o lado do back existe'),
 'loc':'worker/src/modules/nodes/nodes.types.ts',
 'purpose':('A worker module with no registry entry on the back is a stranded module — the exact defect <code>A3</code> exists to clear. Do not create two more of them.',
            'Um módulo de worker sem entrada no registro do back é um módulo encalhado — exatamente o defeito que a <code>A3</code> existe para limpar. Não crie mais dois.'),
 'body':('<p>Confirm the merged <code>nodes.types.ts</code> has every enum entry, and that each one has its <strong>full registration chain</strong>:</p>',
         '<p>Confirme que o <code>nodes.types.ts</code> mesclado tem cada entrada do enum, e que cada uma tem a <strong>cadeia de registro completa</strong>:</p>'),
 'list':[('The worker module itself','O módulo do worker em si'),
         ('The activity','A activity'),
         ('The binding','O binding'),
         ('The workflow proxy','O proxy do workflow'),
         ('The case in <code>process-single-node.workflow.ts</code>','O case em <code>process-single-node.workflow.ts</code>')],
 'body2':('<p>Then the half that is easy to skip: <strong>confirm the back actually routes it</strong>. If it does not, the registry entry is added here, <strong>behind the flag from PLAN §3.2</strong> — added disabled, proved, and flipped in a separate deploy.</p>'
          '<p>Each of the six, and both providers, is measured against <strong>PLAN §3.4&#x27;s seven-point definition of done</strong>. A node is not done when its activity exists.</p>',
          '<p>Depois a metade fácil de pular: <strong>confirme que o back de fato roteia o node</strong>. Se não roteia, a entrada no registro entra aqui, <strong>atrás da flag do PLAN §3.2</strong> — adicionada desligada, provada, e ligada num deploy separado.</p>'
          '<p>Cada um dos seis, e os dois provedores, é medido contra a <strong>definição de pronto de sete pontos do PLAN §3.4</strong>. Um node não está pronto quando a activity dele existe.</p>'),
 'ba':(('The worker half exists and was presumably tested when written. Nothing has ever checked whether the back would route to it.',
        'A metade do worker existe e presumivelmente foi testada quando escrita. Nada nunca checou se o back rotearia para ela.'),
       ('Every one of the eight is checked on <strong>both</strong> sides, and the check is the A1 registry rather than a reviewer&#x27;s memory.',
        'Cada um dos oito é checado nos <strong>dois</strong> lados, e o checador é o registro da A1, não a memória de um revisor.'))},

{'n':'3','title':('Ship it — and prove the inline twin does not also fire',
                  'Subir — e provar que o gêmeo inline não dispara junto'),
 'loc':('develop → staging → PR to main', 'develop → staging → PR para main'),
 'purpose':('The failure mode of a promotion is not “it does not run”. It is “it runs twice”.',
            'O modo de falha de uma promoção não é “não roda”. É “roda duas vezes”.'),
 'body':('<p>The route is <code>develop</code> → soak → <code>staging</code> → soak → PR to <code>main</code>, with the staging question answered first.</p>'
         '<p><strong>PLAN §6 R1 names the risk in this exact shape</strong>: a node routed to the worker whose inline twin still fires — a duplicated charge, a duplicated message. It is rated critical, and this task turns on six node types and two providers at once. '
         'With the flag on, the inline handler must not fire, and that has to be <strong>log-asserted rather than assumed</strong>.</p>',
         '<p>A rota é <code>develop</code> → soak → <code>staging</code> → soak → PR para <code>main</code>, com a questão do staging respondida antes.</p>'
         '<p><strong>O PLAN §6 R1 nomeia o risco exatamente nesta forma</strong>: um node roteado ao worker cujo gêmeo inline ainda dispara — uma cobrança duplicada, uma mensagem duplicada. Está classificado como crítico, e esta task liga seis tipos de node e dois provedores de uma vez. '
         'Com a flag ligada, o handler inline não pode disparar, e isso precisa ser <strong>afirmado por log, não suposto</strong>.</p>'),
 'ba':(('Six finished modules exist and never run. The nodes execute inline, exactly as they did before the modules were written.',
        'Seis módulos prontos existem e nunca rodam. Os nodes executam inline, exatamente como antes de os módulos serem escritos.'),
       ('They run in the worker — <strong>once</strong> — with the activity visible in Temporal and the inline path proven silent.',
        'Eles rodam no worker — <strong>uma vez</strong> — com a activity visível no Temporal e o caminho inline comprovadamente calado.'))},
]

VERIF=[
 (True,('Negative control','Controle negativo'),
  ('For one of the six, <strong>remove its case from <code>process-single-node.workflow.ts</code></strong>, run its spec, and record the failure. The workflow&#x27;s default branch throws <code>Node type X not supported</code> — confirm that is what you see, <strong>because that is the exact failure mode a missing registration produces in production</strong>.',
   'Para um dos seis, <strong>remova o case dele de <code>process-single-node.workflow.ts</code></strong>, rode o teste, e registre a falha. O ramo padrão do workflow lança <code>Node type X not supported</code> — confirme que é isso que você vê, <strong>porque é exatamente o modo de falha que um registro faltante produz em produção</strong>.')),
 (True,('Per node, in the local Docker stack','Por node, na stack Docker local'),
  ('Run it in a flow and confirm four things in order: the <strong>activity appears in Temporal</strong>, <code>node_executions</code> goes <strong>PENDING → COMPLETED</strong>, the <strong>downstream node receives the output</strong>, and the run finishes. Anything less proves the module loaded, not that it works.',
   'Rode em um fluxo e confirme quatro coisas, nesta ordem: a <strong>activity aparece no Temporal</strong>, o <code>node_executions</code> vai de <strong>PENDING → COMPLETED</strong>, o <strong>node seguinte recebe a saída</strong>, e o run termina. Menos que isso prova que o módulo carregou, não que ele funciona.')),
 (True,('No double execution','Sem execução dupla'),
  ('With the flag on, <strong>the inline handler must not fire</strong>. Log-assert it, per node. <strong>PLAN §6 R1</strong> rates this critical for a reason: the observable symptom is a duplicated charge or a duplicated message, not an error.',
   'Com a flag ligada, <strong>o handler inline não pode disparar</strong>. Afirme por log, por node. O <strong>PLAN §6 R1</strong> classifica isto como crítico por um motivo: o sintoma observável é uma cobrança ou mensagem duplicada, não um erro.')),
 (False,('Check staging before shipping','Checar o staging antes de subir'),
  ('As of 2026-08-21, <code>back@origin/staging</code> still carried the pre-release <strong>six</strong> providers while production carried <strong>eight</strong>. <strong>Confirm whether that is deliberate</strong> — promoting through a stale staging will either re-break production or silently pass, and both are reported as success.',
   'Em 2026-08-21, o <code>back@origin/staging</code> ainda carregava os <strong>seis</strong> provedores pré-release enquanto a produção carregava <strong>oito</strong>. <strong>Confirme se isso é deliberado</strong> — promover por um staging defasado ou quebra a produção de novo ou passa em silêncio, e os dois são reportados como sucesso.')),
]

DONE=('All six node types are in <code>main</code>, the two pending providers are in production, and each of them satisfies <strong>PLAN §3.4</strong> — what is in test is in <code>main</code>.',
      'Os seis tipos de node estão na <code>main</code>, os dois provedores pendentes estão em produção, e cada um satisfaz o <strong>PLAN §3.4</strong> — o que está em teste está na <code>main</code>.')

FILES=[('worker/src/modules/nodes/{voice-generator,web-crawling,web-search,large-memory,pull-data,push-data}/',False),
       ('worker/src/modules/nodes/nodes.types.ts',False),
       ('worker/src/modules/temporal/**',False),
       ('worker adapters: clickup.adapter.ts · quickbooks.adapter.ts',False),
       ('the A1 registry',False),
       ('the promotion branch',False)]

BLOCKS=[
 {'k':'label','n':'1','t':('What is finished, and where it is parked','O que está pronto, e onde está parado')},
 TABLE, PROSE_QUEUE,
 {'k':'label','n':'2','t':('The decision this task needs','A decisão que esta task precisa')},
 {'k':'prose','t':(
   'One call has to be made <strong>before the first merge</strong>, and it is about the route rather than the code. It opens below with the options, what each costs the customer and costs us, and the recommendation.',
   'Uma decisão precisa ser tomada <strong>antes do primeiro merge</strong>, e é sobre a rota, não sobre o código. Ela abre abaixo com as opções, quanto cada uma custa ao cliente e a nós, e a recomendação.')},
 DEC_STAGING,
 {'k':'label','n':'3','t':('What the task does, in three parts','O que a task faz, em três partes')},
]
for p in PARTS:
    BLOCKS.append({'k':'part', **p})

TASK={'code':'A2','vnum':'4','title':TITLE,'goal':GOAL,'glance':GLANCE,'lede':LEDE,
      'blocks':BLOCKS,'verif':VERIF,'done':DONE,'files':FILES}

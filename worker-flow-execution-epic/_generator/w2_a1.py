# -*- coding: utf-8 -*-

TITLE=('One dispatch registry','Um registro de dispatch')
GOAL=('Replace the four uncoordinated lists that answer <b>“can the worker run this node type?”</b> with <b>one derived source</b>.',
      'Substituir as quatro listas descoordenadas que respondem <b>“o worker consegue rodar este tipo de node?”</b> por <b>uma fonte derivada</b>.')

GLANCE=[
 ('crit',('Severity','Severidade'),('High — two live inconsistencies','Alta — duas inconsistências vivas'),
  ('<code>thirdPartyIntegration</code> takes two different paths depending on how it was started, and two worker modules are reachable by nothing (§9.4).',
   'O <code>thirdPartyIntegration</code> toma dois caminhos diferentes conforme como foi iniciado, e dois módulos do worker não são alcançáveis por nada (§9.4).')),
 ('dep',('Depends on','Depende de'),('Nothing','Nada'),
  ('But it <strong>blocks all of Track A, plus D2</strong>. Every other task in the epic writes to this registry, so it goes first.',
   'Mas <strong>bloqueia toda a trilha A, mais a D2</strong>. Toda outra task do épico escreve neste registro, por isso ela vem primeiro.')),
 ('wave',('Wave','Onda'),('Wave 2','Onda 2'),
  ('This task <em>is</em> the wave&#x27;s stated outcome: one place answers “does the worker run this?”, and it is true.',
   'Esta task <em>é</em> o resultado declarado da onda: um lugar responde “o worker roda isto?”, e a resposta é verdadeira.')),
 ('ship',('Shape','Formato'),('Behaviour-neutral','Neutra em comportamento'),
  ('Same types dispatched, same refusals, same prefetch eligibility. The inconsistencies it exposes are fixed by <strong>A2, A3 and C1</strong>.',
   'Mesmos tipos despachados, mesmas recusas, mesma elegibilidade de prefetch. As inconsistências que ela expõe são corrigidas por <strong>A2, A3 e C1</strong>.')),
]

LEDE=(
 '<p>Four independent lists answer “can the worker run this node type?”, and <strong>none of them references another</strong> (analysis §9.2.3): <code>isTemporalNode</code> with seven types, '
 '<code>isWorkerRoutedIntegration</code> with nine providers, <code>MIGRATED_TEMPORAL_NODE_TYPES</code> with the same seven, and a 17-type prefetch whitelist.</p>'
 '<p>Two consequences are <strong>already live</strong>: <code>thirdPartyIntegration</code> takes the worker path inside a flow and the inline path from the legacy endpoint, and the worker&#x27;s '
 '<code>sqlQuerier</code> and <code>audioReaderNode</code> modules are reachable by nothing (§9.4). Neither is a bug in any one list — they are what four lists that never look at each other produce.</p>',
 '<p>Quatro listas independentes respondem “o worker consegue rodar este tipo de node?”, e <strong>nenhuma delas referencia outra</strong> (análise §9.2.3): <code>isTemporalNode</code> com sete tipos, '
 '<code>isWorkerRoutedIntegration</code> com nove provedores, <code>MIGRATED_TEMPORAL_NODE_TYPES</code> com os mesmos sete, e uma whitelist de prefetch com 17 tipos.</p>'
 '<p>Duas consequências <strong>já estão em produção</strong>: o <code>thirdPartyIntegration</code> toma o caminho do worker dentro de um fluxo e o caminho inline pelo endpoint legado, e os módulos '
 '<code>sqlQuerier</code> e <code>audioReaderNode</code> do worker não são alcançáveis por nada (§9.4). Nenhuma das duas é um bug de uma lista específica — são o que quatro listas que nunca se olham produzem.</p>')

TABLE={'k':'table',
 'head':[('List','Lista'),('Where','Onde'),('Contents','Conteúdo'),
         ('What it actually governs','O que ela de fato governa'),('Does anything check it?','Algo confere?')],
 'rows':[
  [{'t':'isTemporalNode(type)','mono':True},
   ('<code>flux.service.ts</code>','<code>flux.service.ts</code>'),
   ('7 types','7 tipos'),
   ('The flow loop <strong>and</strong> <code>executeSingleNode</code>','O laço do fluxo <strong>e</strong> o <code>executeSingleNode</code>'),
   {'t':('Nothing','Nada'),'pill':'no'}],
  [{'t':'isWorkerRoutedIntegration(node)','mono':True},
   ('<code>integration-executable-node.ts</code>','<code>integration-executable-node.ts</code>'),
   ('provider ∈ {stripe, wordpress, slack, notion, zapier, hubspot, supabase, pinecone, mcp}',
    'provedor ∈ {stripe, wordpress, slack, notion, zapier, hubspot, supabase, pinecone, mcp}'),
   ('The same two paths, in addition','Os mesmos dois caminhos, em adição'),
   {'t':('Nothing','Nada'),'pill':'no'}],
  [{'t':'MIGRATED_TEMPORAL_NODE_TYPES','mono':True},
   ('<code>temporal/single-node-legacy/legacy-allowlist.ts</code>','<code>temporal/single-node-legacy/legacy-allowlist.ts</code>'),
   ('The same 7','Os mesmos 7'),
   ('Only <code>/process/single-node-legacy</code> validation','Apenas a validação de <code>/process/single-node-legacy</code>'),
   {'t':('Nothing','Nada'),'pill':'no'}],
  [{'t':'PREFETCH_SUPPORTED_NODE_TYPES','mono':True},
   ('<code>flux.service.ts</code>','<code>flux.service.ts</code>'),
   ('17 types','17 tipos'),
   ('Whether a flow may use the prefetch executor at all','Se um fluxo pode sequer usar o executor de prefetch'),
   {'t':('Nothing','Nada'),'pill':'no'}],
  [{'t':'basedOnType','mono':True},
   ('<code>node-reference-substitution.service.ts</code>','<code>node-reference-substitution.service.ts</code>'),
   ('Per node type, which fields a placeholder may reference','Por tipo de node, quais campos um placeholder pode referenciar'),
   ('Whether a node&#x27;s field can be referenced at all','Se um campo do node pode sequer ser referenciado'),
   {'t':('Nothing','Nada'),'pill':'no'}],
 ]}

PROSE_BASED={'k':'prose','t':(
 '<code>basedOnType</code> is <strong>not a dispatch list</strong>, and it is in the table anyway because it is the same failure mode: adding a node type with a referenceable field means editing it by hand, '
 'with nothing checking that you did (analysis §11.2). It is also <strong>load-bearing for B3</strong> — when the consumer resolves its own input, this map is what says which fields it may resolve. '
 'A registry that collapses four lists and leaves the fifth is a registry that will grow a sixth.',
 'O <code>basedOnType</code> <strong>não é uma lista de dispatch</strong>, e está na tabela mesmo assim porque é o mesmo modo de falha: adicionar um tipo de node com campo referenciável exige editá-lo à mão, '
 'sem nada conferindo que você editou (análise §11.2). E ele é <strong>estrutural para a B3</strong> — quando o consumidor resolve a própria entrada, é esse mapa que diz quais campos ele pode resolver. '
 'Um registro que colapsa quatro listas e deixa a quinta é um registro que vai criar uma sexta.')}

DEC_D5={
 'k':'decision','id':'A1-a','plan':'D5','status':'open','open':True,
 'q':('What are <code>comment</code>, <code>label</code> and <code>group</code>?',
      'O que são <code>comment</code>, <code>label</code> e <code>group</code>?'),
 'intro':('These three sit in <code>PREFETCH_SUPPORTED_NODE_TYPES</code> (<code>flux.service.ts</code>) and are <strong>not among the 48 registered front node types</strong> (analysis §9.2). '
          'The plan is blunt about why that blocks this task: <em>the registry cannot be authoritative while three types in a live whitelist are unaccounted for</em>. '
          'And the whitelist is all-or-nothing — <code>canUsePrefetchForFlow</code> requires <strong>every</strong> node in a flow to be in it — so whatever these three are, they decide whether a flow containing one gets the prefetch executor at all.',
          'Os três estão em <code>PREFETCH_SUPPORTED_NODE_TYPES</code> (<code>flux.service.ts</code>) e <strong>não estão entre os 48 tipos de node registrados no front</strong> (análise §9.2). '
          'O plano é direto sobre por que isso bloqueia esta task: <em>o registro não pode ser autoritativo enquanto três tipos numa whitelist viva estiverem sem explicação</em>. '
          'E a whitelist é tudo-ou-nada — o <code>canUsePrefetchForFlow</code> exige que <strong>todo</strong> node do fluxo esteja nela — então, sejam o que forem, esses três decidem se um fluxo que contém um deles usa o executor de prefetch.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Decorative canvas objects — put them on an explicit ignore list',
                                 'Objetos decorativos de canvas — numa lista de ignorados explícita'),
   'tag':('recommended','recomendada'),
   'how':('They are annotations on the builder canvas, not executable nodes. Each gets a registry entry that says exactly that, and the prefetch whitelist keeps trusting them — now for a stated reason instead of by inheritance.',
          'São anotações no canvas do builder, não nodes executáveis. Cada um ganha uma entrada no registro dizendo exatamente isso, e a whitelist de prefetch continua confiando neles — agora por um motivo declarado, não por herança.'),
   'pros':[('Keeps A1 <strong>behaviour-neutral</strong>, which is its mandate: a flow containing one of the three keeps the prefetch path it has today',
            'Mantém a A1 <strong>neutra em comportamento</strong>, que é seu mandato: um fluxo com um dos três mantém o caminho de prefetch que tem hoje'),
           ('Makes the registry authoritative — every entry in the whitelist has a row naming what it is',
            'Torna o registro autoritativo — toda entrada da whitelist tem uma linha dizendo o que ela é'),
           ('Gives the next decorative type a place to be declared, instead of a fourth list to be added to',
            'Dá ao próximo tipo decorativo um lugar para ser declarado, em vez de uma quarta lista onde ser adicionado')],
   'cons':[('It is only true <strong>after the greps</strong>. Written before them, it is an assertion the drift spec cannot check — the spec catches a missing worker module, not a wrong classification',
            'Só é verdade <strong>depois dos greps</strong>. Escrita antes deles, é uma afirmação que o teste de drift não consegue checar — ele pega módulo de worker faltando, não classificação errada')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('lo',('Ours: <b>three entries and one test</b>','Nosso: <b>três entradas e um teste</b>'))]},
  {'ltr':'B','name':('Real node types that were never registered in the front',
                     'Tipos de node reais que nunca foram registrados no front'),
   'how':('They exist in stored flows and something executes them; the census of 48 counted <em>registered front components</em>, so it would have missed them. They get real registry entries with their real dispatch.',
          'Eles existem em fluxos guardados e algo os executa; o censo de 48 contou <em>componentes registrados no front</em>, então teria passado por eles. Ganham entradas reais no registro, com o dispatch real.'),
   'pros':[('If any of the three does execute, classifying it as decorative is the worst available outcome — this option is the one that cannot be quietly wrong',
            'Se algum dos três de fato executa, classificá-lo como decorativo é o pior resultado possível — esta é a opção que não pode estar errada em silêncio'),
           ('The registry states what is true rather than what is convenient',
            'O registro declara o que é verdade, não o que é conveniente')],
   'cons':[('It turns A1 into the discoverer of a migration, and <strong>A1 is behaviour-neutral by mandate</strong> — the work would belong to a Track A task, not to this one',
            'Transforma a A1 na descobridora de uma migração, e <strong>a A1 é neutra em comportamento por mandato</strong> — o trabalho seria de uma task da trilha A, não desta'),
           ('Nothing in the analysis found an executor for any of the three; this option needs evidence it does not yet have',
            'Nada na análise encontrou um executor para nenhum dos três; esta opção precisa de evidência que ainda não tem')],
   'cost':[('',('Client cost: <b>unknown until measured</b>','Custo do cliente: <b>desconhecido até medir</b>')),
           ('hi',('Ours: <b>a new Track A task</b>','Nosso: <b>uma nova task da trilha A</b>'))]},
  {'ltr':'C','no':True,'name':('Dead entries — delete them from the whitelist',
                               'Entradas mortas — apagar da whitelist'),
   'tag':('rejected','rejeitada'),
   'how':('Nobody can name them, so remove the three from <code>PREFETCH_SUPPORTED_NODE_TYPES</code> and let the registry cover only what exists.',
          'Ninguém sabe nomeá-los, então remover os três de <code>PREFETCH_SUPPORTED_NODE_TYPES</code> e deixar o registro cobrir só o que existe.'),
   'pros':[('The shortest list is the easiest to trust, and a whitelist entry with no owner is exactly what rots',
            'A lista mais curta é a mais fácil de confiar, e uma entrada de whitelist sem dono é exatamente o que apodrece')],
   'cons':[('<strong>This is a behaviour change wearing a cleanup&#x27;s clothes.</strong> Any stored flow containing one of the three stops satisfying <code>canUsePrefetchForFlow</code> and silently drops to the legacy path',
            '<strong>É uma mudança de comportamento vestida de limpeza.</strong> Qualquer fluxo guardado com um dos três deixa de satisfazer o <code>canUsePrefetchForFlow</code> e cai em silêncio no caminho legado'),
           ('It is a refusal, so <strong>PLAN §3.3.2</strong> applies: measure it against the stored flows first and drive false refusals to zero. Deleting first and measuring never is the pattern that rule exists to stop',
            'É uma recusa, então vale o <strong>PLAN §3.3.2</strong>: medir contra os fluxos guardados antes e zerar as falsas recusas. Apagar primeiro e nunca medir é justamente o padrão que essa regra existe para impedir'),
           ('A1 is behaviour-neutral by mandate, so this cannot land in A1 in any case',
            'A A1 é neutra em comportamento por mandato, então isto não pode entrar na A1 de forma alguma')],
   'cost':[('hi',('Client cost: <b>flows silently lose the prefetch path</b>','Custo do cliente: <b>fluxos perdem o prefetch em silêncio</b>')),
           ('hi',('Ours: <b>an unmeasured refusal</b>','Nosso: <b>uma recusa não medida</b>'))]},
 ],
 'rec':('<p><strong>A — and the three things that settle it are an afternoon of work, not a research project.</strong></p>'
        '<p><strong>1.</strong> Grep the three type strings across <code>front/</code>. If they render as canvas annotations and never reach a submit or a run handler, they are decorative and A is simply true. '
        '<strong>2.</strong> Count the stored flows whose nodes carry those types — the same query also measures option C&#x27;s blast radius, which is the number nobody has. '
        '<strong>3.</strong> Check the prefetch executor&#x27;s own <code>is-non-executable.ts</code> (analysis §9.2): if it already classifies them, the answer has been written down once and just never made it into the whitelist&#x27;s reasoning.</p>'
        '<p>Whichever way it lands, <strong>the answer goes into the registry, not into a review comment</strong>. That is the entire point of this task: the next person to ask should read a row, not repeat the greps.</p>',
        '<p><strong>A — e as três coisas que resolvem isso são uma tarde de trabalho, não um projeto de pesquisa.</strong></p>'
        '<p><strong>1.</strong> Faça grep das três strings de tipo em <code>front/</code>. Se elas renderizam como anotações de canvas e nunca chegam a um submit ou a um handler de run, são decorativas e a A é simplesmente verdade. '
        '<strong>2.</strong> Conte os fluxos guardados cujos nodes carregam esses tipos — a mesma consulta mede o raio de impacto da opção C, que é o número que ninguém tem. '
        '<strong>3.</strong> Cheque o <code>is-non-executable.ts</code> do próprio executor de prefetch (análise §9.2): se ele já os classifica, a resposta já foi escrita uma vez e só não chegou ao raciocínio da whitelist.</p>'
        '<p>Seja qual for o resultado, <strong>a resposta vai para o registro, não para um comentário de revisão</strong>. É esse o ponto inteiro da task: a próxima pessoa que perguntar deve ler uma linha, não repetir os greps.</p>'),
 'who':[('Engineering, from the greps','Engenharia, a partir dos greps')],
}

PARTS=[
{'n':'1','title':('One registry, and six predicates that read it','Um registro, e seis predicados que o leem'),
 'loc':'flux.service.ts · integration-executable-node.ts',
 'purpose':('One entry per node type, carrying the facts each caller already needs — so the callers stop carrying their own copy.',
            'Uma entrada por tipo de node, carregando os fatos de que cada chamador já precisa — para os chamadores pararem de carregar a própria cópia.'),
 'body':('<p>The registry module lives in <code>back</code>, keyed by node type, and holds exactly what the existing callers ask for:</p>',
         '<p>O módulo do registro fica no <code>back</code>, com chave por tipo de node, e guarda exatamente o que os chamadores existentes pedem:</p>'),
 'code':('{ workerModule, dispatch, integrationProviders?, prefetchSafe, mutating, hasInlineTwin }',
         '{ workerModule, dispatch, integrationProviders?, prefetchSafe, mutating, hasInlineTwin }'),
 'body2':('<p>Then all four predicates are <strong>re-expressed as reads of the registry</strong>, six functions in total: <code>isTemporalNode</code>, <code>isWorkerRoutedIntegration</code>, '
          '<code>isMigratedTemporalNode</code>, <code>isLegacyRunnableNode</code>, <code>isMutatingNodeType</code> and <code>canUsePrefetchForFlow</code>.</p>'
          '<p><strong>The function names stay.</strong> Call sites do not change, which keeps the diff reviewable — a refactor that touches every caller cannot be reviewed for behaviour neutrality, and behaviour neutrality is the whole claim.</p>',
          '<p>Depois os quatro predicados são <strong>reescritos como leituras do registro</strong>, seis funções ao todo: <code>isTemporalNode</code>, <code>isWorkerRoutedIntegration</code>, '
          '<code>isMigratedTemporalNode</code>, <code>isLegacyRunnableNode</code>, <code>isMutatingNodeType</code> e <code>canUsePrefetchForFlow</code>.</p>'
          '<p><strong>Os nomes das funções permanecem.</strong> Os pontos de chamada não mudam, o que mantém o diff revisável — um refactor que toca todo chamador não pode ser revisado quanto a neutralidade de comportamento, e neutralidade de comportamento é a afirmação inteira.</p>'),
 'ba':(('Adding a node type means remembering four edits in four files, and <strong>nothing tells you when you forgot one</strong>. Two types are already wrong because of it.',
        'Adicionar um tipo de node significa lembrar de quatro edições em quatro arquivos, e <strong>nada avisa quando você esqueceu uma</strong>. Dois tipos já estão errados por causa disso.'),
       ('One entry per type. The six predicates read it, so forgetting becomes <strong>a test failure instead of a production surprise</strong>.',
        'Uma entrada por tipo. Os seis predicados a leem, então esquecer vira <strong>um teste vermelho, não uma surpresa em produção</strong>.'))},

{'n':'2','title':('<code>basedOnType</code> becomes a projection, with its contents unchanged',
                  'O <code>basedOnType</code> vira uma projeção, com o conteúdo inalterado'),
 'loc':'node-reference-substitution.service.ts',
 'purpose':('Fold the fifth list in now, while it is only a projection — before B3 makes it the thing that decides what a consumer may resolve.',
            'Trazer a quinta lista agora, enquanto ela é só uma projeção — antes de a B3 torná-la a coisa que decide o que um consumidor pode resolver.'),
 'body':('<p>It stops being a parallel hand-maintained map and becomes a view over the registry. <strong>Its contents must not change in this task</strong>: the same fields referenceable, the same behaviour, node for node.</p>'
         '<p>That constraint is what makes it safe to do here rather than inside B3. A projection whose output is byte-for-byte the old map is provable in a test; a projection that also improves the map is a behaviour change nobody asked for in a task that promised none.</p>',
         '<p>Ele deixa de ser um mapa paralelo mantido à mão e vira uma visão sobre o registro. <strong>Seu conteúdo não pode mudar nesta task</strong>: os mesmos campos referenciáveis, o mesmo comportamento, node por node.</p>'
         '<p>Essa restrição é o que torna seguro fazer isto aqui, e não dentro da B3. Uma projeção cuja saída é idêntica ao mapa antigo é provável num teste; uma projeção que também melhora o mapa é uma mudança de comportamento que ninguém pediu, numa task que prometeu nenhuma.</p>'),
 'ba':(('A hand-maintained whitelist of referenceable fields, edited from memory, with nothing checking the edit.',
        'Uma whitelist de campos referenciáveis mantida à mão, editada de memória, sem nada conferindo a edição.'),
       ('The same whitelist, derived. When B3 moves input resolution to the consumer, <strong>it reads one source instead of inheriting a second</strong>.',
        'A mesma whitelist, derivada. Quando a B3 mover a resolução de entrada para o consumidor, <strong>ele lê uma fonte em vez de herdar uma segunda</strong>.'))},

{'n':'3','title':('A contract fixture two repos can share without a build graph',
                  'Um fixture de contrato que dois repositórios compartilham sem build graph'),
 'loc':'worker/src/modules/nodes/nodes.types.ts',
 'purpose':('Make the worker&#x27;s enum the authority on which modules exist, without pretending the two repos can import each other.',
            'Tornar o enum do worker a autoridade sobre quais módulos existem, sem fingir que os dois repositórios podem se importar.'),
 'body':('<p>A <code>node_types.contract.json</code> lands in <code>back</code>, <strong>generated from the worker&#x27;s <code>NodeType</code> enum</strong>, plus a spec that fails when the registry claims a '
         '<code>workerModule</code> the enum does not have.</p>'
         '<p><strong>The repos are separate submodules with no shared build graph</strong>, so this is a committed fixture with a regeneration script — not an import. That is a deliberate limitation: the fixture is only as fresh as the last regeneration, and the spec is what makes staleness loud instead of silent.</p>',
         '<p>Um <code>node_types.contract.json</code> entra no <code>back</code>, <strong>gerado a partir do enum <code>NodeType</code> do worker</strong>, mais um teste que falha quando o registro alega um '
         '<code>workerModule</code> que o enum não tem.</p>'
         '<p><strong>Os repositórios são submódulos separados sem build graph compartilhado</strong>, então isto é um fixture commitado com um script de regeneração — não um import. É uma limitação deliberada: o fixture é tão fresco quanto a última regeneração, e o teste é o que torna a defasagem barulhenta em vez de silenciosa.</p>'),
 'ba':(('The worker&#x27;s enum and the back&#x27;s lists are two independent claims about the same fact, and nothing has ever compared them.',
        'O enum do worker e as listas do back são duas afirmações independentes sobre o mesmo fato, e nada nunca as comparou.'),
       ('A registry entry naming a module the worker does not have <strong>fails a spec by name</strong>. This fixture is also the artefact <code>D2</code> publishes for agents to read.',
        'Uma entrada do registro que nomeia um módulo que o worker não tem <strong>falha um teste, com nome</strong>. Este fixture é também o artefato que a <code>D2</code> publica para agentes lerem.'))},

{'n':'4','title':('The invariant that turns stranding into a test failure',
                  'A invariante que transforma encalhe em teste vermelho'),
 'purpose':('State the epic&#x27;s rule once, as a spec: a node type may not have a worker module and inline dispatch at the same time.',
            'Declarar a regra do épico uma vez, como teste: um tipo de node não pode ter módulo no worker e dispatch inline ao mesmo tempo.'),
 'body':('<p>The spec asserts it directly: <strong>no type may have <code>workerModule: true</code> and <code>dispatch: &#x27;inline&#x27;</code></strong> without an explicit <code>strandedReason</code>.</p>'
         '<p>That is not an abstract rule looking for a violation. It is <code>sqlQuerier</code> and <code>audioReaderNode</code> today, and clearing them is exactly what <strong>A3</strong> is for. '
         'The registry does not fix them — it makes them impossible to forget again.</p>',
         '<p>O teste afirma isso diretamente: <strong>nenhum tipo pode ter <code>workerModule: true</code> e <code>dispatch: &#x27;inline&#x27;</code></strong> sem um <code>strandedReason</code> explícito.</p>'
         '<p>Não é uma regra abstrata à procura de uma violação. São o <code>sqlQuerier</code> e o <code>audioReaderNode</code> hoje, e limpá-los é exatamente para o que serve a <strong>A3</strong>. '
         'O registro não os conserta — ele os torna impossíveis de esquecer de novo.</p>'),
 'ba':(('Two worker modules ship to production on every deploy and nothing routes to them. It took a document to notice.',
        'Dois módulos do worker vão para produção a cada deploy e nada roteia para eles. Foi preciso um documento para perceber.'),
       ('The same state fails a spec that names the type, and clearing it is a task with an owner rather than a paragraph in an analysis.',
        'O mesmo estado falha um teste que nomeia o tipo, e limpá-lo é uma task com dono em vez de um parágrafo numa análise.')),
 'callouts':[('mig',('Scope — what A1 must not do','Escopo — o que a A1 não pode fazer'),
   ('<p><strong>A1 changes nothing about what any node type does.</strong> Same types dispatched, same refusals, same prefetch eligibility. '
    'The inconsistencies it exposes belong to the tasks that own them — <code>A2</code>, <code>A3</code> and <code>C1</code>. This task only makes them visible in one place.</p>',
    '<p><strong>A A1 não muda nada sobre o que qualquer tipo de node faz.</strong> Mesmos tipos despachados, mesmas recusas, mesma elegibilidade de prefetch. '
    'As inconsistências que ela expõe pertencem às tasks que são donas delas — <code>A2</code>, <code>A3</code> e <code>C1</code>. Esta task apenas as torna visíveis num lugar só.</p>'))]},
]

VERIF=[
 (True,('Negative control','Controle negativo'),
  ('<strong>Two observed failures, both stated in the PR.</strong> Delete one type from the registry, run the suite, and record which test went red and with what message. Then flip a <code>dispatch</code> value and confirm the behaviour-neutrality spec catches it. A registry whose tests do not fail when it is wrong is a fifth list with better formatting.',
   '<strong>Duas falhas observadas, ambas declaradas no PR.</strong> Apague um tipo do registro, rode a suíte, e registre qual teste ficou vermelho e com qual mensagem. Depois troque um valor de <code>dispatch</code> e confirme que o teste de neutralidade pega. Um registro cujos testes não falham quando ele está errado é uma quinta lista com formatação melhor.')),
 (True,('Behaviour neutrality, one case per type','Neutralidade de comportamento, um caso por tipo'),
  ('For all <strong>48 registered types plus the 3 unaccounted ones</strong>, assert the new predicates return exactly what the old lists returned. Table-driven, one case per type — <strong>this is the test that makes the refactor safe</strong>, and it is the only artefact that can prove the claim in the fourth glance tile.',
   'Para todos os <strong>48 tipos registrados mais os 3 sem explicação</strong>, afirme que os novos predicados retornam exatamente o que as listas antigas retornavam. Dirigido por tabela, um caso por tipo — <strong>é este o teste que torna o refactor seguro</strong>, e é o único artefato capaz de provar a afirmação do quarto card.')),
 (True,('Measure before refusing','Medir antes de recusar'),
  ('<strong>PLAN §3.3.2.</strong> <code>canUsePrefetchForFlow</code> is a refusing rule. Run the new implementation against real stored flows and confirm the set of flows it accepts is <strong>identical</strong> to today&#x27;s. Report any difference <strong>as a defect in this task, not as an improvement</strong> — a refactor that quietly accepts one more flow has changed behaviour, whichever direction it changed it in. While that run is open, <strong>record <code>D2</code>&#x27;s numbers</strong>: how many stored flows satisfy the whitelist, how many ran with <code>FLUX_EXEC_MEMORY_MODE=prefetch</code>, and what it saved. Report them in the PR — <code>B3</code> answers <code>D2</code> with them (Wave 4) and <code>C2</code> executes the answer (Wave 6).',
   '<strong>PLAN §3.3.2.</strong> O <code>canUsePrefetchForFlow</code> é uma regra que recusa. Rode a nova implementação contra fluxos reais guardados e confirme que o conjunto de fluxos aceitos é <strong>idêntico</strong> ao de hoje. Reporte qualquer diferença <strong>como defeito desta task, não como melhoria</strong> — um refactor que aceita um fluxo a mais em silêncio mudou o comportamento, em qualquer direção que tenha mudado. Com essa rodada aberta, <strong>registre os números da <code>D2</code></strong>: quantos fluxos guardados satisfazem a whitelist, quantos rodaram com <code>FLUX_EXEC_MEMORY_MODE=prefetch</code>, e o que isso economizou. Informe-os no PR — a <code>B3</code> responde a <code>D2</code> com eles (onda 4) e a <code>C2</code> executa a resposta (onda 6).')),
 (False,('No second source survives','Nenhuma segunda fonte sobrevive'),
  ('“Done when” says the registry is the <strong>only</strong> place a node type&#x27;s dispatch is declared. After the refactor, grep for the old list names: a predicate that still keeps its own copy makes the registry advisory rather than authoritative, and advisory is how this started.',
   'O “pronto quando” diz que o registro é o <strong>único</strong> lugar onde o dispatch de um tipo de node é declarado. Depois do refactor, faça grep dos nomes das listas antigas: um predicado que ainda guarda a própria cópia torna o registro consultivo em vez de autoritativo, e consultivo é como isto começou.')),
]

DONE=('The registry is the <strong>only</strong> place a node type&#x27;s dispatch is declared; the six predicates read from it; the drift spec is green; the behaviour-neutrality table covers every type; and <strong>no production behaviour changed</strong>.',
      'O registro é o <strong>único</strong> lugar onde o dispatch de um tipo de node é declarado; os seis predicados leem dele; o teste de drift está verde; a tabela de neutralidade cobre todo tipo; e <strong>nenhum comportamento de produção mudou</strong>.')

FILES=[('back/src/app-api/flux/flux.service.ts (isTemporalNode · PREFETCH_SUPPORTED_NODE_TYPES · canUsePrefetchForFlow)',False),
       ('back/src/shared/integration/integration-executable-node.ts (MIGRATED_INTEGRATION_PROVIDERS · isWorkerRoutedIntegration)',False),
       ('back/src/temporal/single-node-legacy/legacy-allowlist.ts',False),
       ('back/src/app-api/.../node-reference-substitution.service.ts',False),
       ('new registry module + node_types.contract.json + specs',True),
       ('worker/src/modules/nodes/nodes.types.ts (read only)',False)]

BLOCKS=[
 {'k':'label','n':'1','t':('The five lists, and what each one actually governs','As cinco listas, e o que cada uma de fato governa')},
 TABLE, PROSE_BASED,
 {'k':'label','n':'2','t':('The decision this task needs','A decisão que esta task precisa')},
 {'k':'prose','t':(
   'One call has to be made before the registry can claim to be authoritative, and it is not an engineering trade-off — it is <strong>a fact nobody has looked up</strong>. '
   'It opens below with the options, what each costs the customer and costs us, and the three checks that settle it.',
   'Uma decisão precisa ser tomada antes de o registro poder se dizer autoritativo, e não é um trade-off de engenharia — é <strong>um fato que ninguém foi conferir</strong>. '
   'Ela abre abaixo com as opções, quanto cada uma custa ao cliente e a nós, e as três checagens que a resolvem.')},
 DEC_D5,
 {'k':'label','n':'3','t':('What the task does, in four parts','O que a task faz, em quatro partes')},
]
for p in PARTS:
    BLOCKS.append({'k':'part', **p})

TASK={'code':'A1','vnum':'4','title':TITLE,'goal':GOAL,'glance':GLANCE,'lede':LEDE,
      'blocks':BLOCKS,'verif':VERIF,'done':DONE,'files':FILES}

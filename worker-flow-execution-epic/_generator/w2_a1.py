# -*- coding: utf-8 -*-
# A1 — One dispatch registry.
# Source: TASK-A1-DISPATCH-REGISTRY.md, corrected 2026-09-21 (nine dispatch lists, not four;
# basedOnType split out to TASK-A1B the same day).

TITLE=('One dispatch registry','Um registro de dispatch')
GOAL=('Replace the uncoordinated lists that answer <b>“can the worker run this node type?”</b> with <b>one derived source</b> — <b>nine lists today, not the four originally scoped.</b>',
      'Substituir as listas descoordenadas que respondem <b>“o worker consegue rodar este tipo de node?”</b> por <b>uma fonte derivada</b> — <b>nove listas hoje, não as quatro originalmente escopadas.</b>')

GLANCE=[
 ('crit',('Severity','Severidade'),('High — nine lists, not four','Alta — nove listas, não quatro'),
  ('<strong>Corrected 2026-09-21.</strong> The dispatch split-brain grew too: <code>isTemporalNode</code> minus <code>MIGRATED_TEMPORAL_NODE_TYPES</code> is four types now, not one, and three of them are worker-routed <em>and</em> legacy-runnable at once.',
   '<strong>Corrigido em 21/09/2026.</strong> O split-brain de dispatch também cresceu: <code>isTemporalNode</code> menos <code>MIGRATED_TEMPORAL_NODE_TYPES</code> são quatro tipos hoje, não um, e três deles são roteados pelo worker <em>e</em> executáveis pelo legado ao mesmo tempo.')),
 ('dep',('Depends on','Depende de'),('Nothing','Nada'),
  ('But it <strong>blocks TASK-A1B, all of Track A, plus D2</strong>. Every other task in the epic writes to this registry, so it goes first.',
   'Mas <strong>bloqueia a TASK-A1B, toda a trilha A, mais a D2</strong>. Toda outra task do épico escreve neste registro, por isso ela vem primeiro.')),
 ('wave',('Wave','Onda'),('Wave 2','Onda 2'),
  ('This task <em>is</em> the wave&#x27;s stated outcome: one place answers “does the worker run this?”, and it is true.',
   'Esta task <em>é</em> o resultado declarado da onda: um lugar responde “o worker roda isto?”, e a resposta é verdadeira.')),
 ('ship',('Shape','Formato'),('Behaviour-neutral, with one fixed message','Neutra em comportamento, com uma mensagem corrigida'),
  ('Same types dispatched, same refusals, same prefetch eligibility — except <code>webCrawling</code>&#x27;s wrong refusal message, fixed as a bounded sub-item. The rest of what this task exposes is fixed by <strong>A2, A3 and C1</strong>.',
   'Mesmos tipos despachados, mesmas recusas, mesma elegibilidade de prefetch — exceto a mensagem de recusa errada do <code>webCrawling</code>, corrigida como item pontual. O resto do que esta task expõe é corrigido pela <strong>A2, A3 e C1</strong>.')),
]

LEDE=(
 '<p><strong>Corrected 2026-09-21</strong>, re-validated against <code>back@origin/production</code> <code>3804a524</code>. The original count of &quot;four lists&quot; was read at <code>back@3be1ea8e</code> (2026-08-21) and was already wrong when A1&#x27;s readiness review re-verified the rest of the plan on 2026-09-02 without re-checking this file. '
 '<strong>There are nine dispatch lists today, not four.</strong> The size of the gap between what was planned and what exists is itself the reason this task&#x27;s scope grows in this correction.</p>'
 '<p><strong><code>basedOnType</code> moved out to its own task, TASK-A1B, the same day.</strong> A same-day re-measurement found the first cut of this correction had overstated <code>basedOnType</code>&#x27;s problem — TASK-A1B carries the corrected facts (one dead copy, two live copies diverging in five lines, not &quot;three divergent copies&quot; needing a large reconciliation). That work is not behaviour-neutral, so it does not belong inside a task that must stay small and behaviour-neutral to safely gate A2/A3/C1/D2. This task no longer scopes <code>basedOnType</code> at all.</p>'
 '<p><strong>The dispatch split-brain also grew, not just the list count.</strong> <code>isTemporalNode</code> minus <code>MIGRATED_TEMPORAL_NODE_TYPES</code> is <code>commandContentNode</code>, <code>voiceBoxNode</code>, <code>webSearch</code>, <code>webCrawling</code> — four types, not the one (<code>thirdPartyIntegration</code>) the epic was scoped against. Three of them run on the worker inside a flow <strong>and</strong> the legacy single-node endpoint accepts and runs them inline — the exact <code>thirdPartyIntegration</code> defect, now replicated three more times. <code>webCrawling</code> is in <strong>neither</strong> allowlist, so it gets the wrong refusal message instead.</p>',
 '<p><strong>Corrigido em 21/09/2026</strong>, revalidado contra <code>back@origin/production</code> <code>3804a524</code>. A contagem original de &quot;quatro listas&quot; foi lida em <code>back@3be1ea8e</code> (21/08/2026) e já estava errada quando a revisão de prontidão da A1 reverificou o resto do plano em 02/09/2026 sem reconferir este arquivo. '
 '<strong>Existem nove listas de dispatch hoje, não quatro.</strong> O tamanho da diferença entre o que foi planejado e o que existe é, em si, o motivo de o escopo desta task crescer nesta correção.</p>'
 '<p><strong>O <code>basedOnType</code> saiu para a própria task, a TASK-A1B, no mesmo dia.</strong> Uma remedição no mesmo dia achou que o primeiro corte desta correção tinha superestimado o problema do <code>basedOnType</code> — a TASK-A1B carrega os fatos corrigidos (uma cópia morta, duas cópias vivas divergindo em cinco linhas, não &quot;três cópias divergentes&quot; precisando de uma reconciliação grande). Esse trabalho não é neutro em comportamento, então não pertence a uma task que precisa continuar pequena e neutra em comportamento para travar A2/A3/C1/D2 com segurança. Esta task não escopa mais o <code>basedOnType</code>.</p>'
 '<p><strong>O split-brain de dispatch também cresceu, não só a contagem de listas.</strong> <code>isTemporalNode</code> menos <code>MIGRATED_TEMPORAL_NODE_TYPES</code> é <code>commandContentNode</code>, <code>voiceBoxNode</code>, <code>webSearch</code>, <code>webCrawling</code> — quatro tipos, não o único (<code>thirdPartyIntegration</code>) contra o qual o épico foi escopado. Três deles rodam no worker dentro de um fluxo <strong>e</strong> o endpoint legado de node único os aceita e roda inline — o mesmo defeito do <code>thirdPartyIntegration</code>, agora replicado mais três vezes. O <code>webCrawling</code> não está em <strong>nenhum</strong> dos dois allowlists, então recebe a mensagem de recusa errada em vez disso.</p>')

TABLE={'k':'table',
 'head':[('List','Lista'),('Where','Onde'),('Contents','Conteúdo'),('Actually governs','O que de fato governa')],
 'rows':[
  [{'t':'isTemporalNode(type)','mono':True},
   ('<code>flux.service.ts</code>','<code>flux.service.ts</code>'),
   ('14 types','14 tipos'),
   ('The flow loop <strong>and</strong> <code>executeSingleNode</code>','O laço do fluxo <strong>e</strong> o <code>executeSingleNode</code>')],
  [{'t':'MIGRATED_TEMPORAL_NODE_TYPES','mono':True},
   ('<code>legacy-allowlist.ts</code>','<code>legacy-allowlist.ts</code>'),
   ('10 types — <strong>a different set</strong> from isTemporalNode&#x27;s','10 tipos — <strong>um conjunto diferente</strong> do do isTemporalNode'),
   ('Only <code>/process/single-node-legacy</code> validation (refuses these as &quot;migrated&quot;)','Apenas a validação de <code>/process/single-node-legacy</code> (recusa estes como &quot;migrados&quot;)')],
  [{'t':'LEGACY_SINGLE_RUN_NODE_TYPES','mono':True},
   ('<code>legacy-allowlist.ts</code>','<code>legacy-allowlist.ts</code>'),
   ('7 types','7 tipos'),
   ('Which types <code>/process/single-node-legacy</code> accepts and runs inline','Quais tipos o <code>/process/single-node-legacy</code> aceita e roda inline')],
  [{'t':'MUTATING_NODE_TYPES','mono':True},
   ('<code>legacy-allowlist.ts</code>','<code>legacy-allowlist.ts</code>'),
   ('5 types','5 tipos'),
   ('Which types the legacy endpoint refuses outright','Quais tipos o endpoint legado recusa de cara')],
  [{'t':'PREFETCH_SUPPORTED_NODE_TYPES','mono':True},
   ('<code>flux.service.ts</code>','<code>flux.service.ts</code>'),
   ('17 types — unchanged','17 tipos — sem mudança'),
   ('Whether a flow may use the prefetch executor at all','Se um fluxo pode sequer usar o executor de prefetch')],
  [{'t':'MIGRATED_INTEGRATION_PROVIDERS','mono':True},
   ('<code>integration-executable-node.ts</code>','<code>integration-executable-node.ts</code>'),
   ('9 providers — unchanged','9 provedores — sem mudança'),
   ('<code>isWorkerRoutedIntegration</code>, the flow loop and <code>executeSingleNode</code>','<code>isWorkerRoutedIntegration</code>, o laço do fluxo e o <code>executeSingleNode</code>')],
  [{'t':'DEDICATED_INTEGRATION_PROVIDER_BY_NODE_TYPE','mono':True},
   ('<code>integration-executable-node.ts</code>','<code>integration-executable-node.ts</code>'),
   ('<code>{ hubSpotCRM: &#x27;hubspot&#x27; }</code>','<code>{ hubSpotCRM: &#x27;hubspot&#x27; }</code>'),
   ('Which provider a non-<code>thirdPartyIntegration</code> node type resolves to','A qual provedor um tipo de node que não é <code>thirdPartyIntegration</code> resolve')],
  [{'t':'isIntegrationExecutableNodeType','mono':True},
   ('<code>integration-executable-node.ts</code>','<code>integration-executable-node.ts</code>'),
   ('2 hard-coded types','2 tipos fixos no código'),
   ('Which node types even look up a provider','Quais tipos de node sequer consultam um provedor')],
  [{'t':'dispatchLegacyHandler switch','mono':True},
   ('<code>legacy-node-dispatch.ts</code>','<code>legacy-node-dispatch.ts</code>'),
   ('9 case arms','9 ramos de case'),
   ('Which types the legacy endpoint can actually execute, once past the two allowlists above','Quais tipos o endpoint legado consegue de fato executar, depois dos dois allowlists acima')],
 ]}

PROSE_A1B={'k':'prose','t':(
 '<code>basedOnType</code> is a related failure mode — adding a node type with a referenceable field means editing it by hand in more than one place, with nothing checking that you did — but it is <strong>not</strong> part of this task&#x27;s scope. It moved to <strong>TASK-A1B</strong> the same day this correction was written, once a re-measurement showed it needed a measurement-backed decision, not a projection this behaviour-neutral task could make on its own. '
 'This task&#x27;s registry does not model <code>basedOnType</code> and does not gain a projection of it; TASK-A1B&#x27;s only remaining connection to this one is temporal — it depends on A1, because its eventual registry entry needs this registry to project from.',
 'O <code>basedOnType</code> é um modo de falha parecido — adicionar um tipo de node com campo referenciável exige editá-lo à mão em mais de um lugar, sem nada conferindo que você editou — mas <strong>não</strong> faz parte do escopo desta task. Ele saiu para a <strong>TASK-A1B</strong> no mesmo dia em que esta correção foi escrita, assim que uma remedição mostrou que ele precisava de uma decisão apoiada em medição, não de uma projeção que esta task, neutra em comportamento, pudesse fazer sozinha. '
 'O registro desta task não modela o <code>basedOnType</code> e não ganha uma projeção dele; a única ligação restante da TASK-A1B com esta é temporal — ela depende da A1, porque a eventual entrada de registro dela precisa deste registro para projetar.')}

DEC_D5={
 'k':'decision','id':'A1-a','plan':'D5','status':'set','open':False,
 'q':('What are <code>comment</code>, <code>label</code>, <code>group</code> — and now <code>voiceNode</code>?',
      'O que são <code>comment</code>, <code>label</code>, <code>group</code> — e agora o <code>voiceNode</code>?'),
 'intro':('<strong>Corrected 2026-09-22, after the implementation.</strong> This block used to read &quot;D5 is now decided by measurement&quot; and call for removing all four. No measurement had been run when that was written; running it <strong>inverted the answer for three of the four</strong>. The original three — <code>comment</code>, <code>label</code>, <code>group</code>, sitting in <code>PREFETCH_SUPPORTED_NODE_TYPES</code> with no counterpart among the 48 registered front node types — turned out decorative, confirmed by the greps this decision called for. '
          'This correction adds a <strong>fourth</strong> unaccounted type: <code>voiceNode</code>, which is in <code>LEGACY_SINGLE_RUN_NODE_TYPES</code> and shares a <code>dispatchLegacyHandler</code> case arm with <code>voiceBoxNode</code>, but is registered in <strong>no</strong> node-type source — not the front&#x27;s 46 types, not the back&#x27;s 50-entry MCP metadata.',
          '<strong>Corrigido em 22/09/2026, depois da implementação.</strong> Este bloco dizia &quot;a D5 agora está decidida por medição&quot; e pedia a remoção dos quatro. Nenhuma medição tinha sido feita quando isso foi escrito; fazer a medição <strong>inverteu a resposta para três dos quatro</strong>. Os três originais — <code>comment</code>, <code>label</code>, <code>group</code>, dentro de <code>PREFETCH_SUPPORTED_NODE_TYPES</code> sem contrapartida entre os 48 tipos de node registrados no front — se confirmaram decorativos, pelos greps que esta decisão pedia. '
          'Esta correção acrescenta um <strong>quarto</strong> tipo sem explicação: o <code>voiceNode</code>, que está em <code>LEGACY_SINGLE_RUN_NODE_TYPES</code> e compartilha um ramo de <code>case</code> do <code>dispatchLegacyHandler</code> com o <code>voiceBoxNode</code>, mas não está registrado em <strong>nenhuma</strong> fonte de tipo de node — nem nos 46 tipos do front, nem nos 50 registros do MCP metadata do back.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Keep the three decorations whitelisted; hand voiceNode to A1c','Manter as três decorações na whitelist; passar o voiceNode para a A1c'),
   'tag':('decided by measurement, 2026-09-22','decidida por medição, 22/09/2026'),
   'how':('All four get a registry entry marked <code>phantom</code>. <code>comment</code>/<code>label</code>/<code>group</code> <strong>stay</strong> on the prefetch whitelist, bound by a spec to the canonical <code>NON_EXECUTABLE_NODE_TYPES</code>. <code>voiceNode</code> is left untouched and handed to <strong>A1c</strong>.',
          'Os quatro ganham entrada no registro marcada como <code>phantom</code>. <code>comment</code>/<code>label</code>/<code>group</code> <strong>permanecem</strong> na whitelist de prefetch, amarrados por spec ao <code>NON_EXECUTABLE_NODE_TYPES</code> canônico. O <code>voiceNode</code> fica intocado e vai para a <strong>A1c</strong>.'),
   'pros':[('A registry entry names the type and records that nothing can create it, which is what makes it authoritative — the list stays permissive, the knowledge stops being missing',
            'Uma entrada no registro nomeia o tipo e registra que nada consegue criá-lo, que é o que o torna autoritativo — a lista segue permissiva, o conhecimento deixa de faltar'),
           ('Measured against production before shipping: removing the three would have been a <strong>false refusal</strong>, because the prefetch executor already skips them via <code>NON_EXECUTABLE_NODE_TYPES</code>',
            'Medido contra produção antes de subir: remover os três teria sido uma <strong>recusa falsa</strong>, porque o executor de prefetch já os pula via <code>NON_EXECUTABLE_NODE_TYPES</code>')],
   'cons':[('The legacy endpoint still accepts <code>voiceNode</code> — this decision does not close that, it names an owner for it (A1c) rather than guessing',
            'O endpoint legado ainda aceita o <code>voiceNode</code> — esta decisão não fecha isso; ela nomeia um dono (A1c) em vez de chutar')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('lo',('Ours: <b>four registry entries added, nothing removed</b>','Nosso: <b>quatro entradas adicionadas ao registro, nada removido</b>'))]},
 ],
 'rec':('<p><strong>Decided: A, and not what this page first said.</strong> Production, last 4 months, live canvases: 15984 flows, 78 prefetch-eligible, <strong>0</strong> would have lost prefetch — with a control run returning rows (<code>commandTextNode</code>: 9207 nodes / 4134 flows), so the zero is measured rather than an empty result set. The zero does not by itself make removal correct: the next flow someone decorated with a comment would have silently lost prefetch. The registry carries a <code>phantom</code> entry for all four and removes none of them. Whichever way a future fifth phantom type turns up, the same three checks that settled this one apply again: grep the front for whether it renders as more than a canvas annotation, count the stored flows carrying it, and check whether the relevant executor already classifies it.</p>',
        '<p><strong>Decidido: A, e não o que esta página dizia antes.</strong> Produção, últimos 4 meses, canvases vivos: 15984 fluxos, 78 elegíveis a prefetch, <strong>0</strong> perderiam prefetch — com uma rodada de controle devolvendo linhas (<code>commandTextNode</code>: 9207 nodes / 4134 fluxos), então o zero é medido e não um resultado vazio. O zero sozinho não torna a remoção correta: o próximo fluxo que alguém decorasse com um comentário perderia prefetch em silêncio. O registro carrega uma entrada <code>phantom</code> para os quatro e não remove nenhum. Seja qual for o jeito que um futuro quinto tipo fantasma aparecer, as mesmas três checagens que resolveram este caso valem de novo: grep no front para ver se ele renderiza como mais que uma anotação de canvas, contar os fluxos guardados que o carregam, e checar se o executor relevante já o classifica.</p>'),
 'who':[('Engineering, from the greps and the flow count','Engenharia, a partir dos greps e da contagem de fluxos')],
}

PARTS=[
{'n':'1','title':('One registry, with two fields this correction adds','Um registro, com dois campos que esta correção acrescenta'),
 'loc':'flux.service.ts · integration-executable-node.ts · legacy-allowlist.ts · legacy-node-dispatch.ts',
 'purpose':('One entry per node type, keyed by node type, carrying the facts each of the nine lists currently answers separately.',
            'Uma entrada por tipo de node, com chave por tipo de node, carregando os fatos que cada uma das nove listas hoje responde separadamente.'),
 'body':('<p>The registry holds: <code>{ workerModule, dispatch, integrationProviders?, prefetchSafe, mutating, hasInlineTwin, dispatchConflict? }</code>. <strong><code>hasInlineTwin</code> and <code>dispatchConflict</code> are new, added by this correction.</strong> <code>hasInlineTwin</code> carries what A3&#x27;s invariant already needed (<code>workerModule: true</code> with <code>dispatch: &#x27;inline&#x27;</code>). <code>dispatchConflict.legacyRunnable</code> names the second, larger defect this correction found: a type can have <code>dispatch: &#x27;worker&#x27;</code> and simultaneously be accepted by <code>/process/single-node-legacy</code> — two different code paths for the same node type, chosen by which endpoint the caller happened to hit. Today that is true for exactly three types: <code>voiceBoxNode</code>, <code>webSearch</code>, <code>commandContentNode</code>.</p>',
         '<p>O registro guarda: <code>{ workerModule, dispatch, integrationProviders?, prefetchSafe, mutating, hasInlineTwin, dispatchConflict? }</code>. <strong>O <code>hasInlineTwin</code> e o <code>dispatchConflict</code> são novos, acrescentados por esta correção.</strong> O <code>hasInlineTwin</code> carrega o que a invariante da A3 já precisava (<code>workerModule: true</code> com <code>dispatch: &#x27;inline&#x27;</code>). O <code>dispatchConflict.legacyRunnable</code> nomeia o segundo defeito, maior, que esta correção achou: um tipo pode ter <code>dispatch: &#x27;worker&#x27;</code> e ao mesmo tempo ser aceito por <code>/process/single-node-legacy</code> — dois caminhos de código diferentes para o mesmo tipo de node, escolhidos por qual endpoint o chamador acertou. Hoje isso é verdade para exatamente três tipos: <code>voiceBoxNode</code>, <code>webSearch</code>, <code>commandContentNode</code>.</p>'),
 'body2':('<p>Re-express all <strong>nine predicates</strong> as reads of the registry. Keep the function names — call sites should not need to change, which keeps the diff reviewable.</p>',
          '<p>Reescrever <strong>os nove predicados</strong> como leituras do registro. Manter os nomes das funções — os call sites não precisam mudar, o que mantém o diff revisável.</p>'),
 'ba':(('Nine lists answer the same question independently, and two live inconsistencies already exist because none of them references another.',
        'Nove listas respondem à mesma pergunta de forma independente, e duas inconsistências já existem porque nenhuma delas referencia outra.'),
       ('One registry, read by nine predicates whose names do not change. Adding or fixing a type is one edit instead of up to nine.',
        'Um registro, lido por nove predicados cujos nomes não mudam. Adicionar ou corrigir um tipo é uma edição em vez de até nove.'))},

{'n':'2','title':('Register the four phantom types — D5, decided by measurement','Registrar os quatro tipos fantasma — D5, decidida por medição'),
 'loc':'flux.service.ts · legacy-allowlist.ts · legacy-node-dispatch.ts',
 'purpose':('Naming them in the registry is what makes them accounted for. Removing them from the lists that trusted them would have been a false refusal for three, and an unmeasured guess for the fourth.',
            'Nomeá-los no registro é o que os torna explicados. Removê-los das listas que os confiavam teria sido uma recusa falsa para três, e um chute não medido para o quarto.'),
 'body':('<p><code>comment</code>, <code>label</code>, <code>group</code> were the original three (decision D5, PLAN §7). This correction adds a fourth: <code>voiceNode</code>, present in <code>LEGACY_SINGLE_RUN_NODE_TYPES</code> and in <code>legacy-node-dispatch.ts</code>&#x27;s shared <code>case &#x27;voiceBoxNode&#x27;: case &#x27;voiceNode&#x27;:</code> arm, but registered in no node-type source. <strong>All four get a registry entry marked <code>phantom</code>; none is removed.</strong> <code>comment</code>/<code>label</code>/<code>group</code> stay prefetch-safe, bound by a spec to <code>NON_EXECUTABLE_NODE_TYPES</code> so neither set can grow alone; <code>voiceNode</code> goes to <strong>A1c</strong>, because its own measurement was never run and it sits on a live endpoint&#x27;s accept list rather than a permissive whitelist.</p>',
         '<p>O <code>comment</code>, o <code>label</code> e o <code>group</code> eram os três originais (decisão D5, PLAN §7). Esta correção acrescenta um quarto: o <code>voiceNode</code>, presente em <code>LEGACY_SINGLE_RUN_NODE_TYPES</code> e no ramo compartilhado <code>case &#x27;voiceBoxNode&#x27;: case &#x27;voiceNode&#x27;:</code> do <code>legacy-node-dispatch.ts</code>, mas não registrado em nenhuma fonte de tipo de node. <strong>Os quatro ganham entrada no registro marcada como <code>phantom</code>; nenhum é removido.</strong> <code>comment</code>/<code>label</code>/<code>group</code> seguem prefetch-safe, amarrados por spec ao <code>NON_EXECUTABLE_NODE_TYPES</code> para que nenhum dos conjuntos cresça sozinho; o <code>voiceNode</code> vai para a <strong>A1c</strong>, porque a medição dele nunca foi feita e ele está na lista de aceite de um endpoint vivo, não numa whitelist permissiva.</p>'),
 'ba':(('Four types sit in live whitelists with no owner and no registration anywhere a developer would look.',
        'Quatro tipos estão em whitelists vivas sem dono e sem registro em lugar nenhum que um desenvolvedor olharia.'),
       ('The registry names all four and records that nothing can create them. Nobody has to re-derive it, and no list quietly lost a type it was relying on.',
        'O registro nomeia os quatro e anota que nada consegue criá-los. Ninguém precisa redescobrir isso, e nenhuma lista perdeu em silêncio um tipo do qual dependia.'))},

{'n':'3','title':('Fix <code>webCrawling</code>&#x27;s refusal message — bounded sub-item','Corrigir a mensagem de recusa do <code>webCrawling</code> — item pontual'),
 'loc':'single-node-legacy.service.ts (validateNode)',
 'purpose':('One line, so the caller sees the right refusal instead of a generic one that happens to be wrong for this type.',
            'Uma linha, para o chamador ver a recusa certa em vez de uma genérica que por acaso está errada para este tipo.'),
 'body':('<p><code>webCrawling</code> is in neither <code>MIGRATED_TEMPORAL_NODE_TYPES</code> nor <code>LEGACY_SINGLE_RUN_NODE_TYPES</code>, so <code>validateNode</code>&#x27;s <code>isLegacyRunnableNode</code> check falls through to the generic refusal instead of the correct &quot;is migrated to Temporal&quot; message every other worker-routed type gets. Add it to whichever check <code>isMigratedTemporalNode</code> reads once the registry exists, so it takes the same branch as the other thirteen <code>isTemporalNode</code> types.</p>'
         '<p>This is naturally C3&#x27;s territory — a pre-existing defect in code being touched, not new behaviour — and the default is to carry it there so this task stays behaviour-neutral. It is written here as a bounded, explicit sub-item because fixing it in the same PR that builds the registry costs less than a second coordinated deploy through C3. Whoever picks up this task decides which PR it lands in; either way it must land.</p>',
         '<p>O <code>webCrawling</code> não está nem em <code>MIGRATED_TEMPORAL_NODE_TYPES</code> nem em <code>LEGACY_SINGLE_RUN_NODE_TYPES</code>, então a checagem <code>isLegacyRunnableNode</code> do <code>validateNode</code> cai na recusa genérica em vez da mensagem correta &quot;is migrated to Temporal&quot; que todo outro tipo roteado pelo worker recebe. Adicioná-lo a qualquer checagem que o <code>isMigratedTemporalNode</code> leia assim que o registro existir, para que ele tome o mesmo ramo que os outros treze tipos <code>isTemporalNode</code>.</p>'
         '<p>Isto é naturalmente território da C3 — um defeito pré-existente em código que está sendo tocado, não comportamento novo — e o padrão é levá-lo para lá para esta task continuar neutra em comportamento. Está escrito aqui como um item pontual e explícito porque corrigi-lo no mesmo PR que constrói o registro custa menos que um segundo deploy coordenado pela C3. Quem pegar esta task decide em qual PR isso entra; de qualquer forma, precisa entrar.</p>'),
 'ba':(('A caller hitting <code>webCrawling</code> through the legacy endpoint sees the wrong refusal message — generic, not the one every other worker-routed type gets.',
        'Um chamador que acerta o <code>webCrawling</code> pelo endpoint legado vê a mensagem de recusa errada — genérica, não a que todo outro tipo roteado pelo worker recebe.'),
       ('<code>webCrawling</code> gets the same &quot;is migrated to Temporal&quot; message as the other thirteen <code>isTemporalNode</code> types.',
        'O <code>webCrawling</code> recebe a mesma mensagem &quot;is migrated to Temporal&quot; que os outros treze tipos <code>isTemporalNode</code>.'))},

{'n':'4','title':('A machine-readable contract, reusing an existing precedent','Um contrato legível por máquina, reaproveitando um precedente existente'),
 'loc':'worker/src/modules/nodes/nodes.types.ts',
 'purpose':('Make the worker&#x27;s enum the authority on which modules exist, shaped exactly like the node-handle-registry precedent already in this repo.',
            'Tornar o enum do worker a autoridade sobre quais módulos existem, no mesmo formato do precedente node-handle-registry que já existe neste repositório.'),
 'body':('<p>A <code>node_types.contract.json</code> lands in <code>back</code>, generated from the worker&#x27;s <code>NodeType</code> enum, plus a spec that fails when the registry claims a <code>workerModule</code> the enum does not have. <strong>Reuse the existing precedent instead of inventing a new fixture format</strong>: <code>back/src/app-mcp/node-types/node-handle-registry.ts</code> + its <code>.spec.ts</code> + the <code>pnpm generate:node-handle-registry</code> script are already exactly this shape — generated committed fixture, regeneration script, drift spec.</p>',
         '<p>Um <code>node_types.contract.json</code> entra no <code>back</code>, gerado a partir do enum <code>NodeType</code> do worker, mais um teste que falha quando o registro alega um <code>workerModule</code> que o enum não tem. <strong>Reaproveitar o precedente existente em vez de inventar um novo formato de fixture</strong>: o <code>back/src/app-mcp/node-types/node-handle-registry.ts</code> + o próprio <code>.spec.ts</code> + o script <code>pnpm generate:node-handle-registry</code> já têm exatamente este formato — fixture gerada e commitada, script de regeneração, teste de drift.</p>'),
 'ba':(('The worker&#x27;s enum and the back&#x27;s lists are independent claims about the same fact, and nothing has ever compared them.',
        'O enum do worker e as listas do back são afirmações independentes sobre o mesmo fato, e nada nunca as comparou.'),
       ('A registry entry naming a module the worker does not have fails a spec by name, shaped like the handle-registry precedent this task borrows from.',
        'Uma entrada do registro que nomeia um módulo que o worker não tem falha um teste, com nome, no mesmo formato do precedente do handle-registry de onde esta task pega emprestado.'))},

{'n':'5','title':('The <code>dispatchConflict</code> invariant, pinned to <code>it.failing()</code>','A invariante <code>dispatchConflict</code>, fixada em <code>it.failing()</code>'),
 'loc':'back — jest 29.3.1',
 'purpose':('State the rule once, as a spec that stays green on arrival instead of red — because back has no CI running jest, and a red spec on arrival poisons every local run before this PR even lands.',
            'Declarar a regra uma vez, como um teste que continua verde na chegada em vez de vermelho — porque o back não tem CI rodando jest, e um teste vermelho na chegada envenena toda rodada local antes mesmo de este PR chegar.'),
 'body':('<p>The invariant: <strong>no type may be in both <code>isTemporalNode</code> and <code>LEGACY_SINGLE_RUN_NODE_TYPES</code></strong>. As of <code>back@origin/production</code> <code>3804a524</code> this is false for exactly three types. Two things, not one spec: <strong>three named <code>it.failing()</code> cases</strong>, one per known-broken type (<code>voiceBoxNode</code>, <code>webSearch</code>, <code>commandContentNode</code>) — <code>it.failing</code> inverts reporting, so an assertion that genuinely fails today is reported as <strong>passing</strong>, keeping the suite green on arrival; the moment C1 deletes that type&#x27;s inline twin, the assertion starts succeeding and <code>it.failing</code> reports that as a <strong>failure</strong>, which is the cue to drop that case. Plus <strong>one plain <code>it()</code></strong> asserting the invariant for every other type, so a fourth type falling into the same trap later does not pass silently.</p>',
         '<p>A invariante: <strong>nenhum tipo pode estar ao mesmo tempo em <code>isTemporalNode</code> e em <code>LEGACY_SINGLE_RUN_NODE_TYPES</code></strong>. Em <code>back@origin/production</code> <code>3804a524</code> isso é falso para exatamente três tipos. Duas coisas, não um teste só: <strong>três casos <code>it.failing()</code> nomeados</strong>, um por tipo já conhecido como quebrado (<code>voiceBoxNode</code>, <code>webSearch</code>, <code>commandContentNode</code>) — o <code>it.failing</code> inverte o relato, então uma asserção que hoje de fato falha é relatada como <strong>passando</strong>, mantendo a suíte verde na chegada; no momento em que a C1 apagar o gêmeo inline daquele tipo, a asserção passa a ter sucesso e o <code>it.failing</code> relata isso como <strong>falha</strong>, que é o sinal para remover aquele caso. Mais <strong>um <code>it()</code> simples</strong> afirmando a invariante para todo outro tipo, para que um quarto tipo caindo na mesma armadilha depois não passe em silêncio.</p>'),
 'ba':(('The same inline-twin defect that <code>thirdPartyIntegration</code> has exists silently for three more types, with nothing naming it.',
        'O mesmo defeito de gêmeo inline que o <code>thirdPartyIntegration</code> tem existe em silêncio para mais três tipos, sem nada os nomeando.'),
       ('Three named <code>it.failing()</code> cases document exactly which types have the defect today, and turn red — loudly — the moment each one is actually fixed.',
        'Três casos <code>it.failing()</code> nomeados documentam exatamente quais tipos têm o defeito hoje, e ficam vermelhos — alto — no momento em que cada um for de fato corrigido.'))},
]

VERIF=[
 (True,('Negative control','Controle negativo'),
  ('Delete one type from the registry, run the suite, and record which test went red and with what message. Then flip a <code>dispatch</code> value and confirm the behaviour-neutrality spec catches it. State both observed failures in the PR.',
   'Apague um tipo do registro, rode a suíte, e registre qual teste ficou vermelho e com qual mensagem. Depois troque um valor de <code>dispatch</code> e confirme que o teste de neutralidade de comportamento pega. Declare as duas falhas observadas no PR.')),
 (True,('Behaviour neutrality against the reconciled source, not a hard-coded count','Neutralidade de comportamento contra a fonte reconciliada, não uma contagem fixa'),
  ('Replace the old fixed target (&quot;48 registered types&quot;) with the <strong>defined canonical source</strong>: the worker&#x27;s <code>NodeType</code> enum, reconciled against <code>back/src/app-mcp/node-types/node-type-metadata.ts</code> — the same reconciliation the contract fixture encodes. For every type in that set, assert the new predicates return exactly what the old lists returned. <strong>Do not hard-code a new count</strong> — the count is whatever the reconciled source contains on the day the test runs, and a hard-coded number is exactly the kind of restated fact that drifted the first time (&quot;48&quot; matched no real source when re-checked).',
   'Substitua o alvo fixo antigo (&quot;48 tipos registrados&quot;) pela <strong>fonte canônica definida</strong>: o enum <code>NodeType</code> do worker, reconciliado contra o <code>back/src/app-mcp/node-types/node-type-metadata.ts</code> — a mesma reconciliação que a fixture do contrato codifica. Para todo tipo desse conjunto, afirme que os novos predicados retornam exatamente o que as listas antigas retornavam. <strong>Não fixe uma nova contagem no código</strong> — a contagem é o que a fonte reconciliada contiver no dia em que o teste rodar, e um número fixo é exatamente o tipo de fato restatado que já causou o drift da primeira vez (&quot;48&quot; não batia com nenhuma fonte real quando reconferido).')),
 (True,('<code>dispatchConflict</code> invariant, with its own negative control','Invariante <code>dispatchConflict</code>, com o próprio controle negativo'),
  ('Confirm the suite is green on arrival with the three <code>it.failing()</code> cases passing (each assertion inside genuinely fails, because the type really is in both lists) and the plain <code>it()</code> also passing. State both in the PR. Then, as a negative control for the invariant itself: temporarily fix one type&#x27;s conflict in a scratch change and confirm its <code>it.failing</code> case turns red — proving the mechanism actually watches the thing it claims to.',
   'Confirme que a suíte está verde na chegada com os três casos <code>it.failing()</code> passando (cada asserção interna de fato falha, porque o tipo realmente está nas duas listas) e o <code>it()</code> simples também passando. Declare os dois no PR. Depois, como controle negativo da própria invariante: corrija temporariamente o conflito de um tipo numa mudança de rascunho e confirme que o caso <code>it.failing</code> dele fica vermelho — provando que o mecanismo de fato observa o que alega observar.')),
 (True,('Measure before refusing, and report D2&#x27;s numbers','Medir antes de recusar, e reportar os números da D2'),
  ('<strong>PLAN §3.3.2.</strong> <code>canUsePrefetchForFlow</code> is a refusing rule. Run the new implementation against real stored flows and confirm the set of flows it accepts is <strong>identical</strong> to today&#x27;s. Report any difference as a defect in this task, not as an improvement. While that run is open, record how many flows satisfy the whitelist, how many ran with <code>FLUX_EXEC_MEMORY_MODE=prefetch</code>, and what it saved — <strong>B3 answers D2 with them</strong> (Wave 4) and <strong>C2 executes the answer</strong> (Wave 6). Unknown is unverifiable, not zero.',
   '<strong>PLAN §3.3.2.</strong> O <code>canUsePrefetchForFlow</code> é uma regra que recusa. Rode a nova implementação contra fluxos reais guardados e confirme que o conjunto de fluxos aceitos é <strong>idêntico</strong> ao de hoje. Reporte qualquer diferença como defeito desta task, não como melhoria. Com essa rodada aberta, registre quantos fluxos satisfazem a whitelist, quantos rodaram com <code>FLUX_EXEC_MEMORY_MODE=prefetch</code>, e o que isso economizou — a <strong>B3 responde à D2</strong> com eles (onda 4) e a <strong>C2 executa a resposta</strong> (onda 6). Desconhecido é não-verificável, não zero.')),
 (False,('No second source survives','Nenhuma segunda fonte sobrevive'),
  ('“Done when” says the registry is the <strong>only</strong> place a node type&#x27;s dispatch is declared. After the refactor, grep for the old list names: a predicate that still keeps its own copy makes the registry advisory rather than authoritative, and advisory is how this started.',
   'O “pronto quando” diz que o registro é o <strong>único</strong> lugar onde o dispatch de um tipo de node é declarado. Depois do refactor, faça grep dos nomes das listas antigas: um predicado que ainda guarda a própria cópia torna o registro consultivo em vez de autoritativo, e consultivo é como isto começou.')),
]

DONE=('The registry is the source every dispatch <em>predicate</em> reads — eight of the nine lists derive from it, and the ninth (<code>dispatchLegacyHandler</code>&#x27;s literal <code>case</code> arms, which select a handler rather than a dispatch verdict) is pinned to it by a drift spec; the drift spec is green; the <code>dispatchConflict</code> invariant exists as three named <code>it.failing()</code> cases plus one plain <code>it()</code> for every other type, the suite is green on arrival, and the PR states that; all four phantom types (D5) carry a <code>phantom</code>-marked registry entry and none is removed — <code>comment</code>/<code>label</code>/<code>group</code> stay prefetch-safe with a spec binding them to <code>NON_EXECUTABLE_NODE_TYPES</code>, and <code>voiceNode</code> is handed to A1c; <code>webCrawling</code>&#x27;s refusal message is fixed (in this task or explicitly handed to C3, not left unresolved); the behaviour-neutrality table covers every type in the reconciled worker-enum/MCP-metadata source; <strong>no other production behaviour changed</strong>. <code>basedOnType</code> is explicitly out — TASK-A1B&#x27;s done-when, not this task&#x27;s.',
      'O registro é a fonte que todo <em>predicado</em> de dispatch lê — oito das nove listas derivam dele, e a nona (os <code>case</code> literais do <code>dispatchLegacyHandler</code>, que escolhem um handler e não um veredito de dispatch) está amarrada a ele por um teste de drift; o teste de drift está verde; a invariante <code>dispatchConflict</code> existe como três casos <code>it.failing()</code> nomeados mais um <code>it()</code> simples para todo outro tipo, a suíte está verde na chegada, e o PR declara isso; os quatro tipos fantasma (D5) carregam entrada no registro marcada como <code>phantom</code> e nenhum foi removido — <code>comment</code>/<code>label</code>/<code>group</code> seguem prefetch-safe, com um teste amarrando-os ao <code>NON_EXECUTABLE_NODE_TYPES</code>, e o <code>voiceNode</code> foi passado para a A1c; a mensagem de recusa do <code>webCrawling</code> está corrigida (nesta task ou explicitamente passada para a C3, não deixada sem resolver); a tabela de neutralidade de comportamento cobre todo tipo da fonte reconciliada enum-do-worker/metadata-do-MCP; <strong>nenhum outro comportamento de produção mudou</strong>. O <code>basedOnType</code> está explicitamente fora — é o “pronto quando” da TASK-A1B, não desta task.')

FILES=[('back/src/app-api/flux/flux.service.ts (isTemporalNode · PREFETCH_SUPPORTED_NODE_TYPES · canUsePrefetchForFlow)',False),
       ('back/src/shared/integration/integration-executable-node.ts (MIGRATED_INTEGRATION_PROVIDERS · DEDICATED_INTEGRATION_PROVIDER_BY_NODE_TYPE · isIntegrationExecutableNodeType · isWorkerRoutedIntegration)',False),
       ('back/src/temporal/single-node-legacy/legacy-allowlist.ts (MIGRATED_TEMPORAL_NODE_TYPES · LEGACY_SINGLE_RUN_NODE_TYPES · MUTATING_NODE_TYPES)',False),
       ('back/src/temporal/single-node-legacy/legacy-node-dispatch.ts (dispatchLegacyHandler switch)',False),
       ('back/src/temporal/single-node-legacy/single-node-legacy.service.ts (validateNode, the webCrawling refusal message)',False),
       ('back/src/app-mcp/node-types/node-handle-registry.ts + .spec.ts (shape precedent, not modified here)',False),
       ('new registry module + node_types.contract.json + specs',True),
       ('worker/src/modules/nodes/nodes.types.ts (read only)',False)]

BLOCKS=[
 {'k':'label','n':'1','t':('The nine lists, and what each one actually governs','As nove listas, e o que cada uma de fato governa')},
 TABLE, PROSE_A1B,
 {'k':'label','n':'2','t':('Decision D5 — the four phantom types','Decisão D5 — os quatro tipos fantasma')},
 DEC_D5,
 {'k':'label','n':'3','t':('What the task does, in five parts','O que a task faz, em cinco partes')},
]
for p in PARTS:
    BLOCKS.append({'k':'part', **p})

TASK={'code':'A1','vnum':'5','title':TITLE,'goal':GOAL,'glance':GLANCE,'lede':LEDE,
      'blocks':BLOCKS,'verif':VERIF,'done':DONE,'files':FILES}

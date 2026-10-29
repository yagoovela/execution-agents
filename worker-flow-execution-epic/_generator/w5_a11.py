# -*- coding: utf-8 -*-
TITLE = ('Give every node type an execution class', 'Dar uma classe de execução a todo tipo de node')

GOAL = ('Every node type the product can put on a canvas has <b>one entry in the dispatch registry that says where it executes</b>, '
        'and every hand-kept dispatch list is derived from that entry.',
        'Todo tipo de node que o produto consegue pôr num canvas tem <b>uma entrada no registro de dispatch que diz onde ele executa</b>, '
        'e toda lista de dispatch mantida à mão é derivada dessa entrada.')

GLANCE = [
 ('crit', ('Blocks','Bloqueia'), ('B4 flag in production · B5','Flag da B4 em produção · B5'),
  ('Turning the B4 flag on in production, and B5&#x27;s measurement. Both read the class this task adds.',
   'Ligar a flag da B4 em produção, e a medição da B5. As duas leem a classe que esta task adiciona.')),
 ('dep', ('Depends on','Depende de'), ('A1','A1'),
  ('The dispatch registry and its contract. Added 2026-10-23 from <code>NODE-COVERAGE-AUDIT-2026-10-23.md</code>; '
   'revised 2026-10-28 against <code>main</code>, and again 2026-10-29 during the build and review.',
   'O registro de dispatch e o contrato dele. Adicionada em 2026-10-23 a partir do <code>NODE-COVERAGE-AUDIT-2026-10-23.md</code>; '
   'revisada em 2026-10-28 contra a <code>main</code>, e de novo em 2026-10-29 durante a construção e a revisão.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('First in the wave: A11 → A13 → B4 flag on in production → A7 → A14 → B5 → B6 and B7.',
   'Primeira da onda: A11 → A13 → flag da B4 ligada em produção → A7 → A14 → B5 → B6 e B7.')),
 ('ship', ('Deploy order','Ordem de deploy'), ('Worker → front → back','Worker → front → back'),
  ('The back refuses <code>thirdPartyIntegration</code> on the legacy single-node endpoint, which the old front still calls. '
   '<strong>No node execution moves</strong>: the task classifies, and fixes what the classification exposed.',
   'O back passa a recusar o <code>thirdPartyIntegration</code> na entrada legada de node único, que o front antigo ainda chama. '
   '<strong>Nenhuma execução de node muda de lugar</strong>: a task classifica, e corrige o que a classificação expôs.')),
]

LEDE = (
 '<p>The registry can say <code>worker</code> or <code>inline</code>, but it cannot say &quot;does not execute&quot;. B4&#x27;s gate '
 '(<code>canUseWorkflowForFlow</code>, <code>back/src/app-api/flux/engine-selector.ts</code>) accepts a flow only when every node has '
 '<code>flowDispatch: &#x27;worker&#x27;</code> or is one of five hard-coded passive types. An unregistered type fails the gate. So a Data Input, '
 'a sticky note or a Small Memory node keeps <strong>the whole flow on the back&#x27;s loop</strong>, and the loop can never be deleted.</p>'
 '<p>Eighteen front or MCP types have no registry entry. The front&#x27;s <code>nodeTypes</code> has 46 keys; the MCP&#x27;s '
 '<code>NODE_TYPE_METADATA</code> has 50, the 46 plus four MCP-only types. The &quot;does not execute&quot; rule lives in '
 '<strong>four hand-kept copies that do not agree</strong>: the prefetch copy has three types on purpose, and the gate, the '
 '<code>apiV2</code> log and the worker&#x27;s <code>NON_EXECUTABLE_TYPES</code> (behind a &quot;Keep in sync&quot; comment) have five. '
 'A spec binds the registry to the prefetch copy; nothing binds the three five-type copies.</p>',
 '<p>O registro consegue dizer <code>worker</code> ou <code>inline</code>, mas não consegue dizer &quot;não executa&quot;. O gate da B4 '
 '(<code>canUseWorkflowForFlow</code>, <code>back/src/app-api/flux/engine-selector.ts</code>) aceita um fluxo só quando todo node tem '
 '<code>flowDispatch: &#x27;worker&#x27;</code> ou é um de cinco tipos passivos fixos no código. Um tipo sem registro reprova no gate. Por isso um Data Input, '
 'uma sticky note ou um node Small Memory prende <strong>o fluxo inteiro no laço do back</strong>, e o laço nunca pode ser apagado.</p>'
 '<p>Dezoito tipos do front ou do MCP não têm entrada no registro. O <code>nodeTypes</code> do front tem 46 chaves; o '
 '<code>NODE_TYPE_METADATA</code> do MCP tem 50, as 46 mais quatro tipos que só existem no MCP. A regra &quot;não executa&quot; vive em '
 '<strong>quatro cópias mantidas à mão que não concordam</strong>: a cópia do prefetch tem três tipos de propósito, e o gate, o log do '
 '<code>apiV2</code> e a <code>NON_EXECUTABLE_TYPES</code> do worker (atrás de um comentário &quot;Keep in sync&quot;) têm cinco. '
 'Uma spec amarra o registro à cópia do prefetch; nada amarra as três cópias de cinco tipos.</p>')

TABLE = dict(
 head=[('Class','Classe'),('Types','Tipos'),('B4 gate','Gate da B4'),('Dev evidence (live canvas, 2026-10-28)','Evidência em dev (canvas vivo, 2026-10-28)')],
 rows=[
  [{'t':('<code>worker</code>','<code>worker</code>')},
   ('Every entry with <code>flowDispatch: &#x27;worker&#x27;</code> today, plus <code>thirdPartyIntegration</code> and <code>hubSpotCRM</code>',
    'Toda entrada com <code>flowDispatch: &#x27;worker&#x27;</code> hoje, mais <code>thirdPartyIntegration</code> e <code>hubSpotCRM</code>'),
   {'t':('accepts','aceita'),'pill':'ok'},
   ('The worker executes it in a flow run and in the single-node Run.','O worker o executa num run de fluxo e no Run de node único.')],
  [{'t':('<code>source</code>, value','<code>source</code>, valor')},
   ('<code>textBox</code>, <code>richTextBox</code>, <code>storedDataCaller</code>, <code>deepRefNode</code>, <code>nodesAdd</code>, '
    '<code>outputTable</code>, <code>tableProcessor</code>, <code>dynamicSettingsNode</code> and <code>mediaBox</code>',
    '<code>textBox</code>, <code>richTextBox</code>, <code>storedDataCaller</code>, <code>deepRefNode</code>, <code>nodesAdd</code>, '
    '<code>outputTable</code>, <code>tableProcessor</code>, <code>dynamicSettingsNode</code> e o <code>mediaBox</code>'),
   {'t':('accepts','aceita'),'pill':'ok'},
   ('<code>textBox</code>: 5646 nodes, 6264 data edges out (5549 into <code>commandTextNode</code>). <code>richTextBox</code>: 1216 nodes, 856 edges.',
    '<code>textBox</code>: 5646 nodes, 6264 arestas de dados saindo (5549 para o <code>commandTextNode</code>). <code>richTextBox</code>: 1216 nodes, 856 arestas.')],
  [{'t':('<code>source</code>, run entry','<code>source</code>, entrada do run')},
   ('<code>varInputNode</code>, <code>globalStarter</code>','<code>varInputNode</code>, <code>globalStarter</code>'),
   {'t':('accepts','aceita'),'pill':'ok'},
   ('<code>varInputNode</code>: 1155 nodes, 1327 data edges out. Its run input is bound into the seed before the workflow starts.',
    '<code>varInputNode</code>: 1155 nodes, 1327 arestas de dados saindo. A entrada do run é gravada na semente antes de o workflow começar.')],
  [{'t':('<code>visual</code>','<code>visual</code>')},
   ('<code>stickyNote</code>, <code>nodesGroup</code>, <code>comment</code>, <code>label</code>, <code>group</code>',
    '<code>stickyNote</code>, <code>nodesGroup</code>, <code>comment</code>, <code>label</code>, <code>group</code>'),
   {'t':('accepts','aceita'),'pill':'ok'},
   ('<code>stickyNote</code>: 2221 nodes, 6 control edges out. <code>nodesGroup</code>: 28, no edges.',
    '<code>stickyNote</code>: 2221 nodes, 6 arestas de controle saindo. <code>nodesGroup</code>: 28, sem arestas.')],
  [{'t':('<code>visual</code>, deprecated','<code>visual</code>, descontinuado')},
   ('<code>webNews</code>, <code>webMedia</code>, <code>webLocations</code>, <code>varInputForm</code>',
    '<code>webNews</code>, <code>webMedia</code>, <code>webLocations</code>, <code>varInputForm</code>'),
   {'t':('accepts','aceita'),'pill':'ok'},
   ('47 saved nodes (25 <code>webNews</code>, 11 <code>webLocations</code>, 6 <code>varInputForm</code>, 5 <code>webMedia</code>). No code executes them. See part 5.',
    '47 nodes salvos (25 <code>webNews</code>, 11 <code>webLocations</code>, 6 <code>varInputForm</code>, 5 <code>webMedia</code>). Nenhum código os executa. Veja a parte 5.')],
  [{'t':('<code>sink</code>','<code>sink</code>')},
   ('<code>outputObjectNode</code> (A13)','<code>outputObjectNode</code> (A13)'),
   {'t':('refuses until A13','recusa até a A13'),'pill':'weak'},
   ('The API reply, the chatbot answer and A9&#x27;s delivery read it.','A resposta da API, a resposta do chatbot e a entrega da A9 leem esse node.')],
  [{'t':('<code>state</code>','<code>state</code>')},
   ('<code>fluxObject</code> (A14)','<code>fluxObject</code> (A14)'),
   {'t':('refuses until A14','recusa até a A14'),'pill':'weak'},
   ('<code>persistSmallMemoryEntries</code> writes after every node; chat sessions load before the run.',
    'O <code>persistSmallMemoryEntries</code> grava depois de cada node; as sessões de chat carregam antes do run.')],
  [{'t':('<code>back</code>','<code>back</code>')},
   ('<code>webTrends</code> (A6b), <code>nodesBox</code> (A7), <code>arrayNode</code>, <code>conditionNode</code>, <code>fluxBox</code>, <code>libraryNode</code> (B6)',
    '<code>webTrends</code> (A6b), <code>nodesBox</code> (A7), <code>arrayNode</code>, <code>conditionNode</code>, <code>fluxBox</code>, <code>libraryNode</code> (B6)'),
   {'t':('refuses','recusa'),'pill':'no'},
   ('Each has a task that moves it to <code>worker</code>. <code>webTrends</code> runs nowhere in a run: the browser calls <code>POST /trends</code>.',
    'Cada um tem uma task que o leva para <code>worker</code>. O <code>webTrends</code> não roda em run nenhum: o navegador chama o <code>POST /trends</code>.')],
 ])

PARTS = [
{'n':'1','title':('An <code>execution</code> field on every entry','Um campo <code>execution</code> em toda entrada'),
 'loc':'back/src/shared/node-dispatch/node-dispatch-registry.ts',
 'purpose':('Give every registry entry one of six values, classified from the code that reads or writes the type at run time, not from its name.',
            'Dar a toda entrada do registro um de seis valores, classificados pelo código que lê ou escreve o tipo em tempo de execução, não pelo nome.'),
 'body':('<p><strong>In a run, every value comes from one of two places, and no node writes into another:</strong> the run seed '
         '(<code>run_seed_nodes</code>, the canvas snapshot plus the bound run inputs) and the <code>node_executions</code> rows of that '
         '<code>runId</code>. A <code>source</code> has a value that the projection resolves, from the seed when nothing feeds it or from '
         'its upstream producer when it is a pass-through. A <code>visual</code> node has no value, and its edges carry nothing.</p>'
         '<p><code>sink</code> and <code>state</code> are roles, not a location. They stay true after A13 and A14 move the work into the '
         'workflow; each of those tasks changes the gate to accept its class, and nothing else. <strong>Every <code>back</code>, '
         '<code>sink</code> or <code>state</code> entry names its owner task in <code>handoffOwner</code></strong>, and the drift spec fails '
         'on one without it, so a new exception cannot land without an owner.</p>'
         '<p><code>execution</code> sits next to <code>flowDispatch</code>; it does not replace it. C2 removes <code>flowDispatch</code> when '
         'it deletes the back&#x27;s loop. The class is registry metadata: node data stays as it is, and the projection resolves through the edge, '
         'not through a display node&#x27;s cached <code>textData</code>.</p>',
         '<p><strong>Num run, todo valor vem de um de dois lugares, e nenhum node escreve em outro:</strong> a semente do run '
         '(<code>run_seed_nodes</code>, o retrato do canvas mais as entradas do run) e as linhas de <code>node_executions</code> daquele '
         '<code>runId</code>. Um <code>source</code> tem um valor que a projeção resolve, a partir da semente quando nada o alimenta ou a partir '
         'do produtor acima dele quando ele só repassa. Um node <code>visual</code> não tem valor, e as arestas dele não carregam nada.</p>'
         '<p><code>sink</code> e <code>state</code> são papéis, não um lugar. Continuam valendo depois que a A13 e a A14 levarem o trabalho para o '
         'workflow; cada uma dessas tasks muda o gate para aceitar a sua classe, e nada mais. <strong>Toda entrada <code>back</code>, '
         '<code>sink</code> ou <code>state</code> nomeia a task dona em <code>handoffOwner</code></strong>, e a spec de drift falha '
         'se faltar, então uma nova exceção não entra sem dono.</p>'
         '<p>O <code>execution</code> fica ao lado do <code>flowDispatch</code>; não o substitui. A C2 remove o <code>flowDispatch</code> quando '
         'apagar o laço do back. A classe é metadado do registro: os dados do node ficam como estão, e a projeção resolve pela aresta, '
         'não pelo <code>textData</code> guardado num node de exibição.</p>'),
 'ba':(('The registry says <code>worker</code> or <code>inline</code>. A type that does not execute has no value to say so, and 18 types have no entry.',
        'O registro diz <code>worker</code> ou <code>inline</code>. Um tipo que não executa não tem valor para dizer isso, e 18 tipos não têm entrada.'),
       ('Every canvas and MCP type has a class, and every exception names its owner.',
        'Todo tipo de canvas e do MCP tem uma classe, e toda exceção nomeia a sua dona.')),
 'callouts':[('mig',('Out of scope — later steps of the same model','Fora de escopo — passos seguintes do mesmo modelo'),
   ('<p><strong>The scheduler stops scheduling <code>source</code> and <code>visual</code> nodes</strong> and links a consumer straight to the producer '
    'behind a pass-through. It changes <code>classifyEdge</code> and <code>buildSchedulerState</code> in both engines together, and a '
    '<code>conditionNode</code> that prunes a branch must also prune the consumer behind it.</p>'
    '<p><strong>A display node shows its producer&#x27;s value instead of a copy.</strong> It reads the producer&#x27;s canvas row, not '
    '<code>node_executions</code>, because production slims run rows after 7 days and deletes them after 30. C1 needs this in place first.</p>',
    '<p><strong>O agendador deixa de agendar nodes <code>source</code> e <code>visual</code></strong> e liga o consumidor direto ao produtor '
    'por trás de um repasse. Muda o <code>classifyEdge</code> e o <code>buildSchedulerState</code> nos dois motores juntos, e um '
    '<code>conditionNode</code> que poda um ramo precisa podar também o consumidor por trás dele.</p>'
    '<p><strong>Um node de exibição mostra o valor do produtor em vez de uma cópia.</strong> Ele lê a linha do produtor no canvas, não o '
    '<code>node_executions</code>, porque produção enxuga as linhas de run depois de 7 dias e as apaga depois de 30. A C1 precisa disso pronto antes.</p>'))]},

{'n':'2','title':('A <code>source</code> that feeds a node fails today — fix the projection','Um <code>source</code> que alimenta um node falha hoje — corrigir a projeção'),
 'loc':'worker process-flow.workflow.ts · project-node-input.ts',
 'purpose':('Make a <code>source</code> deliver its value under B4, fixed or pass-through, before the gate accepts it.',
            'Fazer um <code>source</code> entregar o seu valor na B4, fixo ou repassado, antes de o gate aceitá-lo.'),
 'body':('<p>The workflow skips a passive node and marks it completed without a <code>node_executions</code> row. The projection then puts it in '
         '<code>completedSourceIds</code>, and <code>project-node-input.ts</code> throws <code>missingSourceError</code> before it reaches '
         '<code>fromSeed</code>, which would have delivered the right value. A spec pinned the throw with a <code>textBox</code> source. '
         '<strong>So under B4, <code>textBox → commandTextNode</code> already fails</strong>; dev has <code>engine_in_workflow</code> off, so nobody hit it.</p>'
         '<p>The fix keeps skipped <code>source</code> and <code>visual</code> nodes out of the <code>completed</code> set given to the projection, '
         'so the projection walks past them: to the producer&#x27;s row for a pass-through, or to <code>fromSeed</code> for a fixed value.</p>'
         '<p><strong><code>tableProcessor</code> and <code>dynamicSettingsNode</code> leave the back-only projection list</strong> (changed 2026-10-29). '
         'The worker projection test serves both from the run seed and matches the back&#x27;s <code>modifyData</code>, and a dev read '
         '(<code>a11-q5-backonly-shape.sql</code>) confirmed the shapes the tests use. The gate keeps only the class check, and a drift test fails '
         'if a type still flagged <code>backOnlyProjection</code> is ever accepted by class.</p>',
         '<p>O workflow pula um node passivo e o marca como concluído sem linha em <code>node_executions</code>. A projeção então o põe em '
         '<code>completedSourceIds</code>, e o <code>project-node-input.ts</code> lança <code>missingSourceError</code> antes de chegar ao '
         '<code>fromSeed</code>, que teria entregado o valor certo. Uma spec fixava esse erro com um <code>textBox</code> como origem. '
         '<strong>Por isso, na B4, <code>textBox → commandTextNode</code> já falha</strong>; dev está com <code>engine_in_workflow</code> desligado, então ninguém viu.</p>'
         '<p>A correção tira os nodes <code>source</code> e <code>visual</code> pulados do conjunto <code>completed</code> entregue à projeção, '
         'que passa por eles: até a linha do produtor num repasse, ou até o <code>fromSeed</code> num valor fixo.</p>'
         '<p><strong>O <code>tableProcessor</code> e o <code>dynamicSettingsNode</code> saem da lista de projeção só-back</strong> (mudou em 2026-10-29). '
         'O teste de projeção do worker serve os dois a partir da semente do run e bate com o <code>modifyData</code> do back, e uma leitura em dev '
         '(<code>a11-q5-backonly-shape.sql</code>) confirmou os formatos usados nos testes. O gate fica só com a checagem de classe, e um teste de drift falha '
         'se um tipo ainda marcado <code>backOnlyProjection</code> for aceito pela classe.</p>'),
 'callouts':[('mig',('Open item — display nodes under B4','Item em aberto — nodes de exibição na B4'),
   ('<p>Under B4 nothing copies a producer&#x27;s output into a display <code>textBox</code> or <code>richTextBox</code>, so the canvas may stop '
    'showing it once the flag is on. Check this on the local stack before the flag goes on in production. The fix is the second later step in part 1, '
    'and C1 is its natural owner.</p>',
    '<p>Na B4 nada copia a saída de um produtor para um <code>textBox</code> ou <code>richTextBox</code> de exibição, então o canvas pode parar '
    'de mostrá-la quando a flag ligar. Confira isso no stack local antes de a flag ligar em produção. A correção é o segundo passo seguinte da parte 1, '
    'e a C1 é a dona natural.</p>'))]},

{'n':'3','title':('No path runs an integration node inline','Nenhum caminho roda um node de integração inline'),
 'loc':('flux.service.ts · legacy-node-dispatch.ts · worker payload builder','flux.service.ts · legacy-node-dispatch.ts · montador do payload no worker'),
 'purpose':('Class <code>thirdPartyIntegration</code> and <code>hubSpotCRM</code> as <code>worker</code>, and replace every inline fallback with a refusal.',
            'Dar a classe <code>worker</code> ao <code>thirdPartyIntegration</code> e ao <code>hubSpotCRM</code>, e trocar todo fallback inline por uma recusa.'),
 'body':('<p>Every real provider already goes to the worker. The front offers ten providers and nine are in the registry&#x27;s '
         '<code>integrationProviders</code>; the tenth, <code>microsoft</code>, is only the account connection card, and its Excel, Word, '
         'PowerPoint, OneDrive and Outlook work already runs in the worker. What fell inline was a node with an empty, unknown or '
         'differently-cased provider: it got <code>Unknown provider</code>, and the next node received empty text. On dev, 7 of 37 nodes did.</p>',
         '<p>Todo provider real já vai para o worker. O front oferece dez providers e nove estão em <code>integrationProviders</code> no registro; '
         'o décimo, <code>microsoft</code>, é só o cartão de conexão da conta, e o trabalho com Excel, Word, PowerPoint, OneDrive e Outlook já roda no worker. '
         'O que caía inline era um node com provider vazio, desconhecido ou com outra caixa de letra: ele recebia <code>Unknown provider</code>, e o '
         'node seguinte recebia texto vazio. Em dev, 7 de 37 nodes caíam ali.</p>'),
 'list':[
  ('Both types get <code>flowDispatch: &#x27;worker&#x27;</code> and <code>execution: &#x27;worker&#x27;</code>, and the contract is regenerated.',
   'Os dois tipos recebem <code>flowDispatch: &#x27;worker&#x27;</code> e <code>execution: &#x27;worker&#x27;</code>, e o contrato é gerado de novo.'),
  ('The inline fallback in the main loop and in <code>executeSingleNode</code> becomes a user-facing error that names the missing provider.',
   'O fallback inline no laço principal e no <code>executeSingleNode</code> vira um erro para o usuário que nomeia o provider ausente.'),
  ('Both get <code>legacyEndpoint: &#x27;refuse-migrated&#x27;</code>, and the <code>thirdPartyIntegration</code> case in <code>dispatchLegacyHandler</code> is deleted.',
   'Os dois recebem <code>legacyEndpoint: &#x27;refuse-migrated&#x27;</code>, e o caso do <code>thirdPartyIntegration</code> em <code>dispatchLegacyHandler</code> é apagado.'),
  ('The worker trims and lowercases the provider in the payload builder, so the adapter lookup and <code>payload.provider</code> see one value. '
   'A spec binds the worker&#x27;s adapter keys to the registry&#x27;s providers.',
   'O worker apara e põe em minúsculas o provider no montador do payload, para a busca do adapter e o <code>payload.provider</code> verem um valor só. '
   'Uma spec amarra as chaves de adapter do worker aos providers do registro.'),
  ('The <code>apiV2</code> loop keeps its literal <code>node.type === &#x27;thirdPartyIntegration&#x27;</code> branch, because '
   '<code>flux.service.worker-dispatch.spec.ts</code> finds each worker type by that literal. C2 deletes the loop.',
   'O laço do <code>apiV2</code> mantém o ramo literal <code>node.type === &#x27;thirdPartyIntegration&#x27;</code>, porque a '
   '<code>flux.service.worker-dispatch.spec.ts</code> acha cada tipo do worker por esse literal. A C2 apaga o laço.'),
 ],
 'callouts':[('mig',('Owned elsewhere','Fica com outra task'),
   ('<p><strong>A7</strong> owns the <code>arrayNode</code> loop body, which has no branch for either type and writes a false success; once A11 sets them to '
    '<code>worker</code>, A7&#x27;s registry-driven dispatch reaches them. <strong>S9</strong> (<code>868mpn1h3</code>) owns runtime credential '
    'authorization: the worker resolves an <code>integrationId</code> without checking that the executing user may use it.</p>',
    '<p>A <strong>A7</strong> cuida do corpo do laço do <code>arrayNode</code>, que não tem ramo para nenhum dos dois tipos e grava um falso sucesso; quando a A11 os '
    'marca como <code>worker</code>, o dispatch guiado pelo registro da A7 passa a alcançá-los. A <strong>S9</strong> (<code>868mpn1h3</code>) cuida da '
    'autorização da credencial em execução: o worker resolve um <code>integrationId</code> sem conferir se o usuário que executa pode usá-lo.</p>'))]},

{'n':'4','title':('Derive every dispatch list from the field','Derivar toda lista de dispatch do campo'),
 'loc':'engine-selector.ts · is-non-executable.ts · node-input-projection.ts · sync-ported-engine.ts',
 'purpose':('Replace the hand-kept dispatch lists and the gate&#x27;s literal types with values read from the registry.',
            'Trocar as listas de dispatch mantidas à mão e os tipos literais do gate por valores lidos do registro.'),
 'body':('<p>Derived from <code>execution</code>: the three five-type passive copies, the worker&#x27;s <code>NON_EXECUTABLE_TYPES</code>, '
         '<code>BACK_ONLY_PROJECTION_NODE_TYPES</code> in back and in the worker&#x27;s port, and the B4 gate, which accepts a flow when every node is '
         '<code>worker</code>, <code>source</code> or <code>visual</code>. The worker imports nothing from back: it gets the class map as a '
         'dependency-free back file in <code>PORTED_ENGINE_FILES</code>, checked by the ported-engine drift spec.</p>'
         '<p><strong>Every <code>visual</code> type is prefetch-safe</strong> (changed 2026-10-29). <code>stickyNote</code>, <code>nodesGroup</code> '
         'and the four deprecated types join <code>comment</code>, <code>label</code> and <code>group</code>, so a decoration no longer costs a flow its '
         'prefetch eligibility. <code>NON_EXECUTABLE_NODE_TYPES</code> is now the <code>visual</code> class, and the production oracle declares the '
         'six additions in <code>MEASURED_PREFETCH_ADDITIONS</code>.</p>',
         '<p>Derivados do <code>execution</code>: as três cópias passivas de cinco tipos, a <code>NON_EXECUTABLE_TYPES</code> do worker, '
         'a <code>BACK_ONLY_PROJECTION_NODE_TYPES</code> no back e na cópia portada do worker, e o gate da B4, que aceita um fluxo quando todo node é '
         '<code>worker</code>, <code>source</code> ou <code>visual</code>. O worker não importa nada do back: recebe o mapa de classes como um '
         'arquivo do back sem dependências em <code>PORTED_ENGINE_FILES</code>, conferido pela spec de drift do motor portado.</p>'
         '<p><strong>Todo tipo <code>visual</code> é seguro para o prefetch</strong> (mudou em 2026-10-29). O <code>stickyNote</code>, o <code>nodesGroup</code> '
         'e os quatro tipos descontinuados se juntam a <code>comment</code>, <code>label</code> e <code>group</code>, então uma decoração não tira mais do fluxo a '
         'elegibilidade ao prefetch. A <code>NON_EXECUTABLE_NODE_TYPES</code> passa a ser a classe <code>visual</code>, e o oráculo de produção declara as '
         'seis inclusões em <code>MEASURED_PREFETCH_ADDITIONS</code>.</p>'),
 'ba':(('Four copies of the passive list, one of them in another repository behind a &quot;Keep in sync&quot; comment.',
        'Quatro cópias da lista de passivos, uma delas em outro repositório atrás de um comentário &quot;Keep in sync&quot;.'),
       ('No hand-kept dispatch list remains. The gate, the log, the prefetch check and the worker read one source.',
        'Nenhuma lista de dispatch mantida à mão sobra. O gate, o log, a checagem do prefetch e o worker leem uma fonte só.')),
 'callouts':[('mig',('Out of scope','Fora de escopo'),
   ('<p>Type lists that answer other questions are not dispatch verdicts and stay: <code>DATA_SINK_TYPES</code>, <code>SIDE_EFFECT_TYPES</code>, '
    '<code>node-output-reset.ts</code>, <code>node-abort-capability.ts</code>, <code>agent-node-catalog.ts</code> and the worker&#x27;s <code>TEXT_PASSTHROUGH_TYPES</code>.</p>',
    '<p>Listas de tipos que respondem outras perguntas não são veredito de dispatch e ficam: <code>DATA_SINK_TYPES</code>, <code>SIDE_EFFECT_TYPES</code>, '
    '<code>node-output-reset.ts</code>, <code>node-abort-capability.ts</code>, <code>agent-node-catalog.ts</code> e a <code>TEXT_PASSTHROUGH_TYPES</code> do worker.</p>'))]},

{'n':'5','title':('Remove the four deprecated types, and never let a saved one block a flow','Remover os quatro tipos descontinuados, sem deixar um node salvo travar um fluxo'),
 'loc':('node_types.enum.ts · node-type-metadata.ts · flow-node.service.ts · the front placeholder','node_types.enum.ts · node-type-metadata.ts · flow-node.service.ts · o placeholder do front'),
 'purpose':('Take <code>webNews</code>, <code>webMedia</code>, <code>webLocations</code> and <code>varInputForm</code> out of the product, while the 47 saved nodes on dev keep working.',
            'Tirar <code>webNews</code>, <code>webMedia</code>, <code>webLocations</code> e <code>varInputForm</code> do produto, com os 47 nodes salvos em dev ainda funcionando.'),
 'body':('<p><strong>Changed 2026-10-29: the four leave the back&#x27;s <code>NodeType</code> enum</strong> as well as the MCP metadata, the per-type tables '
         'in back, front and the worker&#x27;s ports, and the seeder&#x27;s &quot;Sales funnel&quot; flow. They stay in one deprecated list in the '
         'dispatch registry, as <code>visual</code> entries. No front component renders them and no code executes them.</p>'
         '<p>A saved node of these types must not stop anyone from opening, reading, editing, saving, copying or restoring a flow:</p>',
         '<p><strong>Mudou em 2026-10-29: os quatro saem do enum <code>NodeType</code> do back</strong>, além dos metadados do MCP, das tabelas por tipo '
         'no back, no front e nas cópias portadas do worker, e do fluxo &quot;Sales funnel&quot; do seeder. Ficam numa lista de descontinuados no '
         'registro de dispatch, como entradas <code>visual</code>. Nenhum componente do front os desenha e nenhum código os executa.</p>'
         '<p>Um node salvo desses tipos não pode impedir ninguém de abrir, ler, editar, salvar, copiar ou restaurar um fluxo:</p>'),
 'list':[
  ('<strong>Front.</strong> A placeholder says the node type was removed and lets the user delete it, instead of hiding it. '
   'It uses the back&#x27;s wording, and a back drift spec fails if the two diverge.',
   '<strong>Front.</strong> Um placeholder diz que o tipo de node foi removido e deixa o usuário apagá-lo, em vez de escondê-lo. '
   'Ele usa o mesmo texto do back, e uma spec de drift do back falha se os dois divergirem.'),
  ('<strong>Back.</strong> <code>PATCH /flow/add-node</code> refuses a new node of a deprecated type; every update, copy, version and import path, '
   '<code>POST /flow</code> and the external <code>api-flows</code> create included, keeps accepting an existing one.',
   '<strong>Back.</strong> O <code>PATCH /flow/add-node</code> recusa um node novo de tipo descontinuado; todo caminho de atualização, cópia, versão e importação, '
   'inclusive o <code>POST /flow</code> e a criação externa do <code>api-flows</code>, continua aceitando um node já existente.'),
  ('<strong>MCP.</strong> <code>get_agent</code> and <code>get_run_nodes</code> mark the node as deprecated, <code>check_agent_integrity</code> lists it without failing '
   '<code>ok</code>, and <code>add_node</code>, <code>update_node</code> and <code>connect_nodes</code> refuse it. Every other edit works, <code>remove_node</code> included.',
   '<strong>MCP.</strong> O <code>get_agent</code> e o <code>get_run_nodes</code> marcam o node como descontinuado, o <code>check_agent_integrity</code> o lista sem reprovar o '
   '<code>ok</code>, e o <code>add_node</code>, o <code>update_node</code> e o <code>connect_nodes</code> o recusam. Toda outra edição funciona, inclusive o <code>remove_node</code>.'),
  ('<strong>Runs</strong> keep skipping it, on both engines. The back <code>CLAUDE.md</code> section &quot;Removed node types&quot; describes every path that carries one.',
   '<strong>Runs</strong> continuam pulando o node, nos dois motores. A seção &quot;Removed node types&quot; do <code>CLAUDE.md</code> do back descreve cada caminho que o carrega.'),
 ],
 'body2':('<p><strong>Bug found on <code>main</code> and fixed here.</strong> <code>toNodeEntity</code> (<code>flow-node.service.ts</code>) resolves every node '
          'type through the MCP catalog, which already hid the four. So a full save of a flow that holds one failed with &quot;Unknown node type: webNews&quot;, '
          'and the front, which filtered the node out on load, then deleted it on its next full-graph save without telling the user. A11 keeps a deprecated '
          'type as stored, and <code>deprecated-node-persistence.spec.ts</code> covers the full save, the data-only save and the version paths.</p>',
          '<p><strong>Bug achado na <code>main</code> e corrigido aqui.</strong> O <code>toNodeEntity</code> (<code>flow-node.service.ts</code>) resolve todo tipo '
          'de node pelo catálogo do MCP, que já escondia os quatro. Por isso salvar por completo um fluxo que tivesse um deles falhava com &quot;Unknown node type: webNews&quot;, '
          'e o front, que filtrava o node ao carregar, o apagava no salvamento completo seguinte sem avisar o usuário. A A11 mantém o tipo descontinuado '
          'como foi gravado, e a <code>deprecated-node-persistence.spec.ts</code> cobre o salvamento completo, o salvamento só de dados e os caminhos de versão.</p>'),
 'callouts':[('mig',('Later — owned by C2 (wave 6)','Depois — fica com a C2 (onda 6)'),
   ('<p>C2&#x27;s section 4 counts the saved nodes live and in version history on production, deletes them and their edges through an internal endpoint with a '
    'dry run, and only then removes the deprecated list, the validator rule, the MCP marker and the front placeholder.</p>',
    '<p>A seção 4 da C2 conta os nodes salvos no canvas vivo e no histórico de versões em produção, apaga esses nodes e as arestas por um endpoint interno com '
    'simulação, e só então remove a lista de descontinuados, a regra do validador, a marca do MCP e o placeholder do front.</p>'))]},

{'n':'6','title':('Editor chain runs reach the next node','Os runs em cadeia do editor chegam ao node seguinte'),
 'loc':'front useTemporalFlowExecution.ts · flowTriggerTokens.ts · Node.tsx',
 'purpose':('Make the node menu&#x27;s chain runs work, through one driver and one route.',
            'Fazer os runs em cadeia do menu do node funcionarem, por um condutor só e uma rota só.'),
 'body':('<p>The node menu&#x27;s two chain commands write <code>data.flowTrigger</code> on a node; the node runs, and its completion writes the trigger on the next '
         'node. <strong>The local E2E on 2026-10-29 found that this chain stopped after the first node for every runnable type except '
         '<code>outputController</code>, on <code>main</code> too.</strong></p>',
         '<p>Os dois comandos de cadeia do menu do node gravam <code>data.flowTrigger</code> num node; o node roda, e a conclusão dele grava o gatilho no node '
         'seguinte. <strong>O E2E local de 2026-10-29 achou que essa cadeia parava depois do primeiro node para todo tipo executável menos o '
         '<code>outputController</code>, também na <code>main</code>.</strong></p>'),
 'list':[
  ('The hook types dispatched to <code>POST /process/single-node</code>, which passes no <code>execId</code>; the worker cast <code>&#x27;&#x27;::uuid</code> and threw, '
   'so the hand-off never fired. Seven other types went to the legacy single-node endpoint, which refuses <code>webSearch</code>, <code>mcpNode</code>, '
   '<code>reportBuilder</code>, <code>audioReaderNode</code> and, since A11, <code>thirdPartyIntegration</code> with a 422.',
   'Os tipos do hook despachavam para o <code>POST /process/single-node</code>, que não passa <code>execId</code>; o worker convertia <code>&#x27;&#x27;::uuid</code> e lançava erro, '
   'então a passagem nunca disparava. Sete outros tipos iam para a entrada legada de node único, que recusa <code>webSearch</code>, <code>mcpNode</code>, '
   '<code>reportBuilder</code>, <code>audioReaderNode</code> e, desde a A11, <code>thirdPartyIntegration</code> com um 422.'),
  ('<code>AiTextGenerator</code>, <code>WebSearch</code> and <code>ProcessCounter</code> ran a step but never handed off; <code>McpClient</code> had no chain run; '
   'Large Memory dispatched twice; the voice node never ran; the run-from-here command skipped the node after the clicked one.',
   'O <code>AiTextGenerator</code>, o <code>WebSearch</code> e o <code>ProcessCounter</code> rodavam um passo mas nunca passavam adiante; o <code>McpClient</code> não tinha cadeia; '
   'o Large Memory despachava duas vezes; o node de voz nunca rodava; o comando de rodar a partir deste node pulava o node depois do clicado.'),
 ],
 'body2':('<p><strong>Decision:</strong> <code>useTemporalFlowExecution</code> is the only chain driver of the 18 components that call it. It dispatches through '
          '<code>/flux/execute-single-node</code>, the route the Run button uses, which checks access, writes the <code>node_executions</code> row, returns an '
          '<code>execId</code> and honours the open version. A component with its own Run handler passes it as <code>runNode</code>, so a chain step flushes local '
          'edits like its Run button. Every new trigger gets a <code>dispatchToken</code> that only the tab that created it can claim, once, so a stale trigger saved '
          'in the database or a second open tab runs nothing. A removed node type is walked through, not run. The legacy run list was left empty and deleted. '
          'The server-side &quot;run from node&quot; was rejected as one to two days of change to both schedulers.</p>',
          '<p><strong>Decisão:</strong> o <code>useTemporalFlowExecution</code> é o único condutor de cadeia dos 18 componentes que o chamam. Ele despacha pelo '
          '<code>/flux/execute-single-node</code>, a rota do botão Run, que confere o acesso, grava a linha em <code>node_executions</code>, devolve um '
          '<code>execId</code> e respeita a versão aberta. Um componente com handler próprio de Run o passa como <code>runNode</code>, então um passo da cadeia salva as '
          'edições locais como o botão Run dele. Todo gatilho novo recebe um <code>dispatchToken</code> que só a aba que o criou pode reivindicar, uma vez, então um gatilho '
          'velho gravado no banco ou uma segunda aba aberta não roda nada. Um tipo de node removido é atravessado, não executado. A lista legada de run ficou vazia e foi apagada. '
          'O &quot;rodar a partir do node&quot; no servidor foi rejeitado por custar de um a dois dias de mudança nos dois agendadores.</p>'),
 'callouts':[('mig',('Left as on main','Fica como na main'),
   ('<p>Twelve other components still run their own chain step from a <code>flowTrigger</code> effect, without the token check, among them '
    '<code>OutputControllerNode</code>, <code>DecisionPaths</code>, <code>FlowCaller</code> and <code>TableProcessor</code>. They are not in the D3 scope, and '
    'moving them needs the same per-component proof. A follow-up task decides it.</p>',
    '<p>Doze outros componentes ainda rodam o seu próprio passo de cadeia a partir de um efeito de <code>flowTrigger</code>, sem a checagem de token, entre eles '
    '<code>OutputControllerNode</code>, <code>DecisionPaths</code>, <code>FlowCaller</code> e <code>TableProcessor</code>. Estão fora do escopo da D3, e '
    'levá-los exige a mesma prova por componente. Uma task de acompanhamento decide.</p>'))]},

{'n':'7','title':('A drift spec, and the end state as tests','Uma spec de drift, e o estado final como testes'),
 'loc':'front/src/util/nodeTypes.tsx · node-type-metadata.ts · node_types.enum.ts',
 'purpose':('Make the next unregistered type fail a test instead of quietly keeping flows on the back&#x27;s loop.',
            'Fazer o próximo tipo sem registro reprovar um teste em vez de prender fluxos em silêncio no laço do back.'),
 'body':('<p><strong>The rule that prevents the next gap.</strong> A drift spec fails when a type exists in the front&#x27;s <code>nodeTypes.tsx</code>, in '
         '<code>node-type-metadata.ts</code> or in the <code>NodeType</code> enum without a registry entry, when a derived list disagrees with the registry, and '
         'when a <code>back</code>, <code>sink</code> or <code>state</code> entry has no <code>handoffOwner</code>. Back CI checks out one repository, so the spec '
         'reads the committed <code>NODE_HANDLE_REGISTRY</code> and reads the live front only when <code>FRONT_REPO_PATH</code> or <code>../front</code> exists.</p>'
         '<p><strong>The end state as tests.</strong> Three expected-failure tests (<code>it.failing</code>), each with the task that turns it into a plain test:</p>',
         '<p><strong>A regra que impede a próxima lacuna.</strong> Uma spec de drift falha quando um tipo existe no <code>nodeTypes.tsx</code> do front, no '
         '<code>node-type-metadata.ts</code> ou no enum <code>NodeType</code> sem entrada no registro, quando uma lista derivada discorda do registro, e '
         'quando uma entrada <code>back</code>, <code>sink</code> ou <code>state</code> não tem <code>handoffOwner</code>. A CI do back baixa um repositório só, então a spec '
         'lê o <code>NODE_HANDLE_REGISTRY</code> commitado e lê o front vivo só quando o <code>FRONT_REPO_PATH</code> ou o <code>../front</code> existe.</p>'
         '<p><strong>O estado final como testes.</strong> Três testes de falha esperada (<code>it.failing</code>), cada um com a task que o transforma em teste comum:</p>'),
 'list':[
  ('No type is classed <code>back</code> — turned plain by C2, when the last one leaves.',
   'Nenhum tipo tem a classe <code>back</code> — vira teste comum pela C2, quando o último sair.'),
  ('The gate accepts a flow that holds a <code>sink</code> — turned plain by A13.',
   'O gate aceita um fluxo que tem um <code>sink</code> — vira teste comum pela A13.'),
  ('The gate accepts a flow that holds a <code>state</code> node — turned plain by A14.',
   'O gate aceita um fluxo que tem um node <code>state</code> — vira teste comum pela A14.'),
 ]},

{'n':'8','title':('Two fixes found on the way','Duas correções achadas no caminho'),
 'loc':'flow-version.controller.ts · back/scripts/generate-node-handle-registry.ts',
 'purpose':('Fix two defects that the local E2E and the A11 front imports exposed.',
            'Corrigir dois defeitos que o E2E local e os novos imports do front da A11 expuseram.'),
 'body':('<p><strong>The versions list no longer fails without paging parameters.</strong> <code>GET /flow/:flowId/versions</code> declared '
         '<code>page: number = 1</code>, but the global <code>ValidationPipe</code> turned a missing value into <code>NaN</code>, so TypeORM failed with a 500. '
         '<code>DefaultValuePipe</code> plus <code>ParseIntPipe</code> now give page 1 and page size 10. The front always sends both values, so users did not see it.</p>'
         '<p><strong>The handle registry generator no longer depends on import order.</strong> It followed every relative import from a node component and cut each '
         'closure at 80 files or depth 8, so the voice node&#x27;s import of the settings modal broke <code>node-handle-registry.spec.ts</code>. The closure now stops at '
         '<code>src/views</code>, <code>Modals</code>, <code>settings</code> and <code>Integrations</code>, the limits are 400 files and depth 20, and a closure that '
         'reaches them throws instead of being cut. The largest is 199 files. The base front and the A11 front generate the same registry, so '
         '<code>connect_nodes</code> accepts the same handles as before.</p>',
         '<p><strong>A lista de versões não falha mais sem parâmetros de paginação.</strong> O <code>GET /flow/:flowId/versions</code> declarava '
         '<code>page: number = 1</code>, mas o <code>ValidationPipe</code> global transformava o valor ausente em <code>NaN</code>, e o TypeORM falhava com um 500. '
         'O <code>DefaultValuePipe</code> com o <code>ParseIntPipe</code> agora dão a página 1 e o tamanho 10. O front sempre manda os dois valores, então os usuários não viram.</p>'
         '<p><strong>O gerador do registro de handles não depende mais da ordem dos imports.</strong> Ele seguia todo import relativo a partir de um componente de node e cortava '
         'cada fecho em 80 arquivos ou profundidade 8, então o import do modal de configurações pelo node de voz quebrou a <code>node-handle-registry.spec.ts</code>. O fecho agora para em '
         '<code>src/views</code>, <code>Modals</code>, <code>settings</code> e <code>Integrations</code>, os limites são 400 arquivos e profundidade 20, e um fecho que '
         'chega a eles lança erro em vez de ser cortado. O maior tem 199 arquivos. O front de base e o front da A11 geram o mesmo registro, então o '
         '<code>connect_nodes</code> aceita os mesmos handles de antes.</p>')},

{'n':'9','title':('Deploy order: worker, then front, then back','Ordem de deploy: worker, depois front, depois back'),
 'loc':'worker · front · back',
 'purpose':('Ship the three repositories in the one order where no step breaks a run.',
            'Publicar os três repositórios na única ordem em que nenhum passo quebra um run.'),
 'body':('<p><strong>Worker first</strong>: a back without the A11 worker would send <code>source</code> and <code>visual</code> types that the old worker does not skip. '
         '<strong>Front before back</strong>: the back moves <code>thirdPartyIntegration</code> to <code>refuse-migrated</code> on the legacy single-node endpoint, and '
         'the front on <code>main</code> sends chain steps of that type there. The new front only calls <code>/flux/execute-single-node</code>, which the back on '
         '<code>main</code> already serves.</p>',
         '<p><strong>Primeiro o worker</strong>: um back sem o worker da A11 mandaria tipos <code>source</code> e <code>visual</code> que o worker antigo não pula. '
         '<strong>O front antes do back</strong>: o back passa o <code>thirdPartyIntegration</code> para <code>refuse-migrated</code> na entrada legada de node único, e '
         'o front da <code>main</code> manda para lá os passos de cadeia desse tipo. O front novo só chama o <code>/flux/execute-single-node</code>, que o back da '
         '<code>main</code> já atende.</p>'),
 'callouts':[('mig',('Known effect','Efeito conhecido'),
   ('<p>A tab that still runs the old bundle after the back deploy gets a refusal on a <code>thirdPartyIntegration</code> chain step until it reloads.</p>',
    '<p>Uma aba que ainda roda o bundle antigo depois do deploy do back recebe uma recusa num passo de cadeia de <code>thirdPartyIntegration</code> até recarregar.</p>'))]},
]

VERIF = [
 (True, ('Negative control — see each check go red','Controle negativo — veja cada checagem ficar vermelha'),
  ('Add a type to the front list without a registry entry, restore a literal copy of a derived list, and remove one <code>handoffOwner</code>: the drift spec goes red each time. '
   'Revert the projection fix and the <code>textBox → commandTextNode</code> workflow case goes red; restore the inline fallback and the integration refusal test goes red. '
   'For the chain runs, ten deliberate mutations each fail at least one test.',
   'Adicione um tipo à lista do front sem entrada no registro, restaure uma cópia literal de uma lista derivada e remova um <code>handoffOwner</code>: a spec de drift fica vermelha a cada vez. '
   'Desfaça a correção da projeção e o caso de workflow <code>textBox → commandTextNode</code> fica vermelho; restaure o fallback inline e o teste de recusa da integração fica vermelho. '
   'Nos runs em cadeia, dez mutações de propósito reprovam pelo menos um teste cada.')),
 (False, ('Projection fix','Correção da projeção'),
  ('The pinned throw now expects seed delivery, and <code>process-flow.workflow</code> cases cover both <code>source</code> roles: a fixed <code>textBox</code>, a '
   '<code>varInputNode</code> and a <code>tableProcessor</code> feeding a worker node, and a pass-through <code>commandTextNode → textBox → commandTextNode</code>.',
   'O erro fixado agora espera a entrega pela semente, e casos de <code>process-flow.workflow</code> cobrem os dois papéis de <code>source</code>: um <code>textBox</code> fixo, um '
   '<code>varInputNode</code> e um <code>tableProcessor</code> alimentando um node do worker, e um repasse <code>commandTextNode → textBox → commandTextNode</code>.')),
 (False, ('Deprecated types','Tipos descontinuados'),
  ('With a flow that holds a saved <code>webNews</code> node: the editor shows the placeholder, a full save, a copy and a version restore succeed, <code>get_agent</code> marks the node, '
   '<code>add_node</code> with <code>webNews</code> is refused, and B4&#x27;s gate accepts the flow.',
   'Com um fluxo que tem um node <code>webNews</code> salvo: o editor mostra o placeholder, o salvamento completo, a cópia e a restauração de versão funcionam, o <code>get_agent</code> marca o node, '
   'o <code>add_node</code> com <code>webNews</code> é recusado, e o gate da B4 aceita o fluxo.')),
 (False, ('Local E2E, 2026-10-29 — passed','E2E local, 2026-10-29 — passou'),
  ('Both chain commands sent one <code>POST /flux/execute-single-node</code> per step, in order, wrote one <code>node_executions</code> row per step, passed each output on, '
   'and walked past the <code>webNews</code> placeholder. A stored trigger did not run after a reload, and a second tab sent nothing. Full runs of a dev flow copy that holds '
   '<code>webNews</code> passed with <code>engine_in_workflow</code> off (legacy loop) and on (B4 workflow, except a flow kept on the loop by its <code>outputObjectNode</code>).',
   'Os dois comandos de cadeia mandaram um <code>POST /flux/execute-single-node</code> por passo, em ordem, gravaram uma linha em <code>node_executions</code> por passo, repassaram cada saída '
   'e atravessaram o placeholder do <code>webNews</code>. Um gatilho gravado não rodou depois de recarregar, e uma segunda aba não mandou nada. Runs completos de uma cópia de fluxo de dev com '
   '<code>webNews</code> passaram com <code>engine_in_workflow</code> desligado (laço legado) e ligado (workflow da B4, menos um fluxo preso no laço pelo seu <code>outputObjectNode</code>).')),
 (True, ('Measure before refusing','Medir antes de recusar'),
  ('Per PLAN §3.3.2: classify every stored production flow as eligible or ineligible for B4&#x27;s gate <strong>before and after</strong> this task. '
   'Every flow that stays ineligible names the type that keeps it there, and that type has a task. Run <code>a11-q2</code>, <code>a11-q3</code> and <code>a11-q4</code> on production; '
   'the user runs production queries.',
   'Conforme o PLAN §3.3.2: classifique todo fluxo de produção armazenado como elegível ou inelegível para o gate da B4 <strong>antes e depois</strong> desta task. '
   'Todo fluxo que continua inelegível nomeia o tipo que o prende ali, e esse tipo tem uma task. Rode a <code>a11-q2</code>, a <code>a11-q3</code> e a <code>a11-q4</code> em produção; '
   'o usuário roda as consultas de produção.')),
]

DONE = ('Every canvas and MCP type has an <code>execution</code> class, and every <code>back</code>, <code>sink</code> and <code>state</code> entry names its owner; '
        'no hand-kept dispatch list remains; a <code>source</code> delivers its value under B4, fixed or pass-through; no path runs <code>thirdPartyIntegration</code> or '
        '<code>hubSpotCRM</code> inline; the four deprecated types are out of the MCP metadata, the per-type tables, the seeder and the <code>NodeType</code> enum, and a saved one '
        'never blocks a flow; editor chain runs reach the next node; the drift spec is green and <strong>has been seen red</strong>; the before/after eligibility counts are '
        'recorded in the task file; and the workspace <code>CLAUDE.md</code> checklist &quot;Adding or changing a node type&quot; names the <code>execution</code> field.',
        'Todo tipo de canvas e do MCP tem uma classe <code>execution</code>, e toda entrada <code>back</code>, <code>sink</code> e <code>state</code> nomeia a sua dona; '
        'nenhuma lista de dispatch mantida à mão sobra; um <code>source</code> entrega o seu valor na B4, fixo ou repassado; nenhum caminho roda <code>thirdPartyIntegration</code> ou '
        '<code>hubSpotCRM</code> inline; os quatro tipos descontinuados saíram dos metadados do MCP, das tabelas por tipo, do seeder e do enum <code>NodeType</code>, e um node salvo '
        'nunca trava um fluxo; os runs em cadeia do editor chegam ao node seguinte; a spec de drift está verde e <strong>já foi vista vermelha</strong>; as contagens de elegibilidade de antes e '
        'depois estão registradas no arquivo da task; e o checklist &quot;Adding or changing a node type&quot; do <code>CLAUDE.md</code> do workspace cita o campo <code>execution</code>.')

FILES = [('back/src/shared/node-dispatch/node-dispatch-registry.ts', False),
         ('back/src/shared/node-dispatch/node-dispatch-registry.types.ts', False),
         ('back/src/shared/node-dispatch/node-dispatch-contract.json', False),
         ('back/src/app-api/flux/engine-selector.ts', False),
         ('back/src/app-api/flux/prefetch/is-non-executable.ts', False),
         ('back/src/app-api/flux/flux.service.ts (the logging copy, the inline fallbacks)', False),
         ('back/src/app-api/flux/node-input-projection.ts', False),
         ('back/src/shared/integration/integration-executable-node.ts', False),
         ('back/src/temporal/single-node-legacy/legacy-node-dispatch.ts', False),
         ('back/scripts/sync-ported-engine.ts', False),
         ('back/src/enums/node_types.enum.ts (four members removed)', False),
         ('back/src/app-mcp/node-types/node-type-metadata.ts (four entries removed)', False),
         ('back/src/app-api/folw/flow-node.service.ts (toNodeEntity)', False),
         ('back/src/app-api/folw/flow-version.controller.ts (versions list)', False),
         ('back/scripts/generate-node-handle-registry.ts', False),
         ('back/src/database/seeders/flow/data.ts', False),
         ('worker process-flow.workflow.ts, project-node-input.ts and the ported files', False),
         ('front/src/hooks/useTemporalFlowExecution.ts', False),
         ('front/src/util/flowTriggerTokens.ts', True),
         ('front/src/components/UI/Node/Node.tsx', False),
         ('front/src/util/nodeTypes.tsx', False),
         ('front/src/views/CoreNodeDisplay.tsx · CoreNodeDisplaySpaces.tsx', False),
         ('CLAUDE.md (node-type checklist)', False)]

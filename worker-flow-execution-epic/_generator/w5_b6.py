# -*- coding: utf-8 -*-
TITLE = ('Control flow and sub-flows in the workflow', 'Controle de fluxo e sub-fluxos no workflow')

GOAL = ('<code>conditionNode</code> and <code>arrayNode</code> become workflow control flow; <code>fluxBox</code> and <code>libraryNode</code> become child workflows. <b>The last four node types leave the back.</b>',
        'O <code>conditionNode</code> e o <code>arrayNode</code> viram controle de fluxo no workflow; o <code>fluxBox</code> e o <code>libraryNode</code> viram child workflows. <b>Os últimos quatro tipos de node saem do back.</b>')

GLANCE = [
 ('crit', ('Severity','Severidade'), ('High','Alta'),
  ('<strong>A child workflow started without the run chain is a child workflow with no ceilings at all.</strong>',
   '<strong>Um child workflow iniciado sem a cadeia do run é um child workflow sem teto algum.</strong>')),
 ('dep', ('Depends on','Depende de'), ('B4 · S1','B4 · S1'),
  ('Can run alongside <code>B5</code>. <code>S1</code>&#x27;s guard has to exist before sub-flows become child workflows.',
   'Pode andar junto da <code>B5</code>. A guarda da <code>S1</code> precisa existir antes de sub-fluxos virarem child workflows.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Once <code>B4</code> exists these stop being blocked and become the natural content of the workflow.',
   'Uma vez que a <code>B4</code> existe, estes deixam de estar bloqueados e viram o conteúdo natural do workflow.')),
 ('ship', ('Shape','Formato'), ('Two constructs','Duas construções'),
  ('Control flow for two types, child workflows for two — and one run chain that has to cross the boundary.',
   'Controle de fluxo para dois tipos, child workflows para dois — e uma cadeia de run que precisa atravessar a fronteira.')),
]

LEDE = (
 '<p>These four do not compute values. <strong>They decide what runs next, or they run whole flows</strong> — and '
 'an activity&#x27;s return value cannot reshape the caller&#x27;s iteration (analysis §3.3–§3.7). That is why they were the four left behind '
 'while everything else migrated.</p>'
 '<p>Once <code>B4</code> exists, they stop being blocked and become the natural content of the workflow. '
 '<strong>That is the inversion this epic is built on:</strong> the thing that could not be an activity turns out to be the thing the workflow is <em>for</em>.</p>',
 '<p>Estes quatro não calculam valores. <strong>Eles decidem o que roda em seguida, ou rodam fluxos inteiros</strong> — e '
 'o retorno de uma activity não consegue remodelar a iteração de quem a chamou (análise §3.3–§3.7). Por isso foram os quatro que ficaram para trás '
 'enquanto todo o resto migrava.</p>'
 '<p>Uma vez que a <code>B4</code> existe, eles deixam de estar bloqueados e viram o conteúdo natural do workflow. '
 '<strong>É esta a inversão sobre a qual o épico é construído:</strong> aquilo que não podia ser activity acaba sendo aquilo para o que o workflow <em>serve</em>.</p>')

TABLE = dict(
 head=[('Type','Tipo'),('What it actually does','O que ele de fato faz'),('Where it belongs','Onde ele pertence')],
 rows=[
  [{'t':'conditionNode  (:6742)','mono':True},
   ('Evaluates <code>conditions[]</code>, mutates <code>currentLoopCounter</code> in place, and <strong>rewrites the engine&#x27;s work queue</strong> via <code>newIds = findConnectedNodes(...)</code>',
    'Avalia <code>conditions[]</code>, muta <code>currentLoopCounter</code> no lugar, e <strong>reescreve a fila de trabalho do motor</strong> via <code>newIds = findConnectedNodes(...)</code>'),
   ('Workflow control flow, calling <code>completeCondition(state, id, handle)</code>',
    'Controle de fluxo no workflow, chamando <code>completeCondition(state, id, handle)</code>')],
  [{'t':'arrayNode  (inline :3738)','mono':True},
   ('Slices a sub-range of the ordered node list between <code>firstId</code> and <code>loopingToId</code> and re-executes it per array item',
    'Fatia um sub-intervalo da lista ordenada de nodes entre <code>firstId</code> e <code>loopingToId</code> e o re-executa por item do array'),
   ('A workflow loop; <strong>possibly a child workflow per iteration</strong>',
    'Um laço de workflow; <strong>possivelmente um child workflow por iteração</strong>')],
  [{'t':'fluxBox  (:5400)','mono':True},
   ('Executes another whole flow inside the node, inheriting the parent&#x27;s run-log collector, cancel key and trigger counters',
    'Executa um outro fluxo inteiro dentro do node, herdando o coletor de run-log, a chave de cancelamento e os contadores de gatilho do pai'),
   ('Child workflow','Child workflow')],
  [{'t':'libraryNode  (:5717)','mono':True},
   ('Structurally the same as <code>fluxBox</code>; the engine already treats them together (<code>:2660</code>, <code>:3287</code>)',
    'Estruturalmente igual ao <code>fluxBox</code>; o motor já os trata juntos (<code>:2660</code>, <code>:3287</code>)'),
   ('Child workflow — <strong>migrate as one unit with <code>fluxBox</code></strong>, or the contract gets written twice',
    'Child workflow — <strong>migrar como uma unidade com o <code>fluxBox</code></strong>, ou o contrato é escrito duas vezes')],
 ])

PROSE = (
 'One call is genuinely open here — the shape of an array iteration. The two below it are <strong>already settled</strong> and are recorded on this page '
 'only so that a reader of B6 does not re-open them: they were decided in <code>S1</code>, and three rules in this epic read their answers.',
 'Uma decisão está de fato em aberto aqui — o formato de uma iteração de array. As duas abaixo dela já estão <strong>decididas</strong> e ficam registradas nesta página '
 'apenas para que quem lê a B6 não as reabra: foram decididas na <code>S1</code>, e três regras deste épico leem as respostas delas.')

DEC_ARRAY = {
 'k':'decision','id':'B6-a','status':'open','open':True,
 'q':('Is an array iteration a loop inside the workflow, or a child workflow per item?',
      'Uma iteração de array é um laço dentro do workflow, ou um child workflow por item?'),
 'intro':(
  'The spec leaves this one open in as many words: <code>arrayNode</code> becomes <em>“a workflow loop; possibly a child workflow per iteration”</em>. '
  'The reason it is a real fork is <strong>review §4.1</strong>: a Temporal workflow&#x27;s history is bounded in both event count and size, the worker uses '
  '<code>continueAsNew</code> nowhere today, and <em>“an <code>arrayNode</code> iterating a big list”</em> is named there as one of the shapes that will hit the limit — '
  'on the biggest, most valuable customer runs first.',
  'A spec deixa esta em aberto com todas as letras: o <code>arrayNode</code> vira <em>“um laço de workflow; possivelmente um child workflow por iteração”</em>. '
  'A razão de ser uma bifurcação real é a <strong>review §4.1</strong>: o histórico de um workflow do Temporal é limitado em contagem de eventos e em tamanho, o worker '
  'não usa <code>continueAsNew</code> em lugar nenhum hoje, e <em>“um <code>arrayNode</code> iterando uma lista grande”</em> é citado lá como uma das formas que baterão no limite — '
  'primeiro nos runs maiores e mais valiosos dos clientes.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('A loop inside the flow workflow','Um laço dentro do workflow do fluxo'),
   'tag':('recommended','recomendada'),
   'how':('The workflow iterates the array itself, re-dispatching the loop body per item, and reuses the <code>continueAsNew</code> boundary <code>B4</code> already had to define.',
          'O próprio workflow itera o array, re-despachando o corpo do laço por item, e reaproveita a fronteira de <code>continueAsNew</code> que a <code>B4</code> já teve de definir.'),
   'pros':[('The loop body already exists as <code>computeLoopBody</code> in the scheduler — no new derivation, and no per-item indices to re-derive',
            'O corpo do laço já existe como <code>computeLoopBody</code> no scheduler — sem nova derivação, e sem índices por item para re-derivar'),
           ('<code>continueAsNew</code> at an iteration boundary is exactly what review §4.1 asks <code>B4</code> for, so there is one mechanism, not two',
            '<code>continueAsNew</code> numa fronteira de iteração é exatamente o que a review §4.1 pede à <code>B4</code>, então há um mecanismo, não dois'),
           ('One workflow per run keeps the run identity, the run log and the billing attribution where <code>E1</code> put them',
            'Um workflow por run mantém a identidade do run, o run log e a atribuição de cobrança onde a <code>E1</code> os colocou')],
   'cons':[('The history grows with every iteration, so the <code>continueAsNew</code> boundary is load-bearing rather than a nicety — get it wrong and the biggest runs die',
            'O histórico cresce a cada iteração, então a fronteira de <code>continueAsNew</code> é estrutural e não um detalhe — errar nela mata os maiores runs'),
           ('A failing item is retried inside the parent&#x27;s history, so a pathological item makes the parent&#x27;s history grow faster',
            'Um item que falha é repetido dentro do histórico do pai, então um item patológico faz o histórico do pai crescer mais rápido')],
   'cost':[('lo',('Client sees: <b>the loop they have today</b>','Cliente vê: <b>o laço que ele já tem hoje</b>')),
           ('',('Ours: <b>the <code>continueAsNew</code> boundary matters</b>','Nosso: <b>a fronteira de <code>continueAsNew</code> importa</b>'))]},
  {'ltr':'B','name':('A child workflow per item','Um child workflow por item'),
   'how':('Each array item runs as its own child workflow; the parent holds one pair of events per item instead of the whole body.',
          'Cada item do array roda como seu próprio child workflow; o pai guarda um par de eventos por item em vez do corpo inteiro.'),
   'pros':[('Each item&#x27;s history is its own, so one huge item cannot exhaust the parent',
            'O histórico de cada item é dele, então um item enorme não esgota o pai'),
           ('Per-item cancellation and per-item retry come from the platform rather than from our loop',
            'Cancelamento e retry por item vêm da plataforma, não do nosso laço'),
           ('It composes with the same child-workflow machinery <code>fluxBox</code> needs anyway',
            'Compõe com a mesma maquinaria de child workflow de que o <code>fluxBox</code> precisa de qualquer jeito')],
   'cons':[('A hundred-thousand-item <code>processorArray</code> becomes a hundred thousand workflows — <code>S4</code>&#x27;s per-node ceiling is what stands between that and the fleet',
            'Um <code>processorArray</code> de cem mil itens vira cem mil workflows — o teto por node da <code>S4</code> é o que separa isso da frota'),
           ('Per-item start latency is paid on every item, including the trivial ones',
            'A latência de início por item é paga em todo item, inclusive nos triviais'),
           ('The run log, the cancel key and the billing attribution have to be threaded per item, not once per loop',
            'O run log, a chave de cancelamento e a atribuição de cobrança precisam ser passados por item, não uma vez por laço')],
   'cost':[('hi',('Client waits: <b>a start per item</b>','Cliente espera: <b>um início por item</b>')),
           ('hi',('Ours: <b>N workflows per array</b>','Nosso: <b>N workflows por array</b>'))]},
  {'ltr':'C','name':('A loop by default, a child above a threshold','Laço por padrão, child acima de um limiar'),
   'tag':('hybrid','híbrida'),
   'how':('Iterate inside the workflow for ordinary arrays and switch to a child workflow per item once the item count or the body size crosses a line.',
          'Iterar dentro do workflow para arrays comuns e trocar para child workflow por item quando a contagem de itens ou o tamanho do corpo cruzar uma linha.'),
   'pros':[('Keeps A&#x27;s cost for the common case and B&#x27;s isolation for the case that actually breaks',
            'Mantém o custo da A no caso comum e o isolamento da B no caso que de fato quebra')],
   'cons':[('<strong>Two control-flow paths in a workflow that has to be replay-deterministic</strong>, and the replay test has to cover both',
            '<strong>Dois caminhos de controle de fluxo num workflow que precisa ser determinístico no replay</strong>, e o teste de replay precisa cobrir os dois'),
           ('The threshold is a number nobody can defend until the history measurement from <code>B4</code> exists',
            'O limiar é um número que ninguém consegue defender enquanto a medição de histórico da <code>B4</code> não existir')],
   'cost':[('lo',('Client sees: <b>nothing, either way</b>','Cliente vê: <b>nada, nos dois casos</b>')),
           ('hi',('Ours: <b>two replay paths to prove</b>','Nosso: <b>dois caminhos de replay para provar</b>'))]},
 ],
 'rec':(
  '<p><strong>A, decided against <code>B4</code>&#x27;s history measurement rather than against taste.</strong> <code>B4</code> already owes a <code>continueAsNew</code> boundary '
  'and a measurement of how much history a real run produces; an array loop is the same mechanism, at a different granularity. Adding a second construct before that '
  'measurement exists is guessing.</p>'
  '<p>Keep <code>B</code> named and available. If the measurement shows a real corpus of arrays whose body alone exhausts a history segment, that is the evidence for '
  'the switch — and it is <code>C</code>, not a rewrite.</p>',
  '<p><strong>A, decidida contra a medição de histórico da <code>B4</code> e não contra o gosto de ninguém.</strong> A <code>B4</code> já deve uma fronteira de <code>continueAsNew</code> '
  'e uma medição de quanto histórico um run real produz; um laço de array é o mesmo mecanismo, com outra granularidade. Somar uma segunda construção antes de essa '
  'medição existir é chute.</p>'
  '<p>Mantenha a <code>B</code> nomeada e disponível. Se a medição mostrar um conjunto real de arrays cujo corpo sozinho esgota um segmento de histórico, essa é a evidência para '
  'a troca — e ela é a <code>C</code>, não uma reescrita.</p>'),
 'who':[('Engineering, after B4&#x27;s history measurement','Engenharia, depois da medição de histórico da B4')],
}

DEC_IDENTITY = {
 'k':'decision','id':'B6-b','plan':'D13','status':'set',
 'q':('Does a sub-flow share the parent&#x27;s execution identity, get a disconnected one, or a chained one?',
      'Um sub-fluxo compartilha a identidade de execução do pai, ganha uma desconectada, ou uma encadeada?'),
 'intro':(
  '<strong>Settled — decided in <a href="task-S1.html">TASK-S1</a>, and inherited here.</strong> It is recorded on this page because B6 is the boundary where the answer '
  'stops being a field in one process and becomes something that has to cross into a child workflow. '
  'A sub-flow gets <strong>its own run identity plus an explicit <code>parentRunId</code></strong>, forming a chain back to the origin run.',
  '<strong>Decidida — resolvida na <a href="task-S1.html">TASK-S1</a>, e herdada aqui.</strong> Fica registrada nesta página porque a B6 é a fronteira em que a resposta '
  'deixa de ser um campo dentro de um processo e passa a ser algo que precisa atravessar para um child workflow. '
  'Um sub-fluxo ganha <strong>identidade de run própria mais um <code>parentRunId</code> explícito</strong>, formando uma cadeia até o run de origem.'),
 'opts':[
  {'ltr':'A','no':True,'name':('Absorb into the parent&#x27;s run','Absorver no run do pai'),
   'tag':('rejected','rejeitada'),
   'how':('The sub-flow&#x27;s nodes join the parent&#x27;s run — one execution id, one scheduler state, one run.',
          'Os nodes do sub-fluxo entram no run do pai — um id de execução, um estado de scheduler, um run.'),
   'pros':[('Budget and cancellation are trivially one thing','Orçamento e cancelamento viram trivialmente uma coisa só')],
   'cons':[('It is a <strong>different graph</strong> — one scheduler state would hold two node sets and two termination conditions',
            'É um <strong>grafo diferente</strong> — um estado de scheduler teria dois conjuntos de nodes e duas condições de término'),
           ('The nested run-log timeline this task is required to preserve would be lost',
            'A linha do tempo aninhada de run-log que esta task precisa preservar seria perdida')],
   'cost':[('hi',('Client loses: <b>the nested run log</b>','Cliente perde: <b>o run log aninhado</b>')),
           ('hi',('Ours: <b>rewrite the scheduler</b>','Nosso: <b>reescrever o scheduler</b>'))]},
  {'ltr':'B','no':True,'name':('A disconnected run','Um run desconectado'),
   'tag':('rejected','rejeitada'),
   'how':('The child workflow starts a fresh, independent run with no link back to its caller.',
          'O child workflow inicia um run novo e independente, sem vínculo com quem o chamou.'),
   'pros':[('Simplest to implement — it is nearly what happens today','Mais simples de implementar — é quase o que acontece hoje')],
   'cons':[('There is no visited set, so <strong>the cycle refusal becomes impossible</strong> at this boundary',
            'Não existe conjunto de visitados, então <strong>a recusa de ciclo fica impossível</strong> nesta fronteira'),
           ('Every nesting level buys a fresh budget and a fresh cost ceiling — nesting becomes the way to defeat <code>S3</code>',
            'Cada nível de aninhamento compra orçamento novo e teto de custo novo — aninhar vira a forma de derrotar a <code>S3</code>'),
           ('Cancelling the parent leaves the children running, which is the opposite of what child workflows give for free',
            'Cancelar o pai deixa os filhos rodando, o oposto do que child workflows dão de graça')],
   'cost':[('hi',('Client risk: <b>an uncapped nested run</b>','Risco do cliente: <b>um run aninhado sem teto</b>')),
           ('hi',('Ours: <b>defeats S1, S3 and E2</b>','Nosso: <b>derrota S1, S3 e E2</b>'))]},
  {'ltr':'C','pick':True,'name':('Its own run, chained by <code>parentRunId</code>','Run próprio, encadeado por <code>parentRunId</code>'),
   'tag':('settled','decidida'),
   'how':('The child gets its own run identity plus an explicit <code>parentRunId</code>, and the visited-flow set and depth counter travel with it across the boundary.',
          'O filho ganha identidade de run própria mais um <code>parentRunId</code> explícito, e o conjunto de fluxos visitados e o contador de profundidade viajam com ele pela fronteira.'),
   'pros':[('<strong>Depth and cycle read the chain</strong> — it <em>is</em> the visited set','<strong>Profundidade e ciclo leem a cadeia</strong> — ela <em>é</em> o conjunto de visitados'),
           ('<strong>Cancellation propagates along it</strong>, which Temporal child workflows give natively','<strong>O cancelamento propaga por ela</strong>, o que child workflows do Temporal dão nativamente'),
           ('<strong><code>S3</code>&#x27;s spend ceiling applies to the chain root</strong>, so nesting cannot reset it','<strong>O teto de gasto da <code>S3</code> se aplica à raiz da cadeia</strong>, então aninhar não o zera'),
           ('The nested run-log timeline the product already shows is preserved','A linha do tempo aninhada de run-log que o produto já exibe é preservada')],
   'cons':[('The chain has to be threaded through state that survives the crossing into a child workflow, not held in a closure',
            'A cadeia precisa atravessar um estado que sobreviva à travessia para um child workflow, não ficar num closure')],
   'cost':[('lo',('Client sees: <b>the nested timeline, intact</b>','Cliente vê: <b>a linha do tempo aninhada, intacta</b>')),
           ('lo',('Ours: <b>one field, carried across</b>','Nosso: <b>um campo, carregado adiante</b>'))]},
 ],
 'rec':(
  '<p><strong>C, and it is decided — B6 inherits it rather than revisiting it.</strong> What B6 owes is not the choice but the plumbing: '
  'the chain has to exist <em>at this boundary</em> and not only inside one process.</p>'
  '<p>The consequence to keep in view: <strong>a child workflow started without the chain is a child workflow with no ceilings at all</strong> — '
  'and unlike today, a durable platform will sustain that result across the whole fleet.</p>',
  '<p><strong>C, e está decidida — a B6 herda em vez de revisitar.</strong> O que a B6 deve não é a escolha, e sim o encanamento: '
  'a cadeia precisa existir <em>nesta fronteira</em>, e não apenas dentro de um processo.</p>'
  '<p>A consequência a não perder de vista: <strong>um child workflow iniciado sem a cadeia é um child workflow sem teto algum</strong> — '
  'e, diferente de hoje, uma plataforma durável vai sustentar esse resultado por toda a frota.</p>'),
 'who':[('Engineering — settled in S1','Engenharia — decidida na S1')],
}

DEC_CYCLE = {
 'k':'decision','id':'B6-c','plan':'D14','status':'set',
 'q':('Is calling a flow already on the chain refused outright, or merely depth-limited?',
      'Chamar um fluxo que já está na cadeia é recusado de imediato, ou apenas limitado por profundidade?'),
 'intro':(
  '<strong>Settled — decided in <a href="task-S1.html">TASK-S1</a>, and inherited here.</strong> A flow already on the chain is <em>awaiting a return</em>; '
  'asking it to start again from the top has no coherent semantics. The refusal applies at <strong>any depth</strong> and to the whole chain, '
  'not only the direct parent. B6 is where the guard has to keep working after sub-flows become child workflows — which is the reason '
  '<code>S1</code> was scheduled in Wave 0 rather than next to this task.',
  '<strong>Decidida — resolvida na <a href="task-S1.html">TASK-S1</a>, e herdada aqui.</strong> Um fluxo que já está na cadeia está <em>aguardando um retorno</em>; '
  'pedir que ele comece de novo do topo não tem semântica coerente. A recusa vale em <strong>qualquer profundidade</strong> e para a cadeia inteira, '
  'não só para o pai direto. A B6 é onde a guarda precisa continuar funcionando depois de sub-fluxos virarem child workflows — que é a razão de a '
  '<code>S1</code> ter sido agendada na onda 0 em vez de ao lado desta task.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Refused outright, at any depth','Recusado de imediato, em qualquer profundidade'),
   'tag':('settled','decidida'),
   'how':('If the flow being called is already on the call chain, the child workflow is not started — no configuration, no depth at which it becomes allowed.',
          'Se o fluxo chamado já está na cadeia de chamadas, o child workflow não é iniciado — sem configuração, sem profundidade em que passe a ser permitido.'),
   'pros':[('<strong>A flow on the chain is awaiting a return</strong>, so restarting it from the top is not a deep call, it is an incoherent one',
            '<strong>Um fluxo na cadeia está aguardando um retorno</strong>, então recomeçá-lo do topo não é uma chamada profunda, é uma chamada incoerente'),
           ('Covers <code>A → B → C → A</code>, not only the direct parent — A is still waiting either way',
            'Cobre <code>A → B → C → A</code>, não só o pai direto — A continua esperando de qualquer forma'),
           ('The refusal message can name the chain, so the author sees which link closed the loop',
            'A mensagem de recusa pode nomear a cadeia, para o autor ver qual elo fechou o laço')],
   'cons':[('A flow that legitimately re-enters itself with different inputs is refused too — no known real case',
            'Um fluxo que legitimamente reentra em si com entradas diferentes também é recusado — nenhum caso real conhecido')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('lo',('Ours: <b>the visited set, carried</b>','Nosso: <b>o conjunto de visitados, carregado</b>'))]},
  {'ltr':'B','no':True,'name':('Allow it, capped by depth','Permitir, limitado por profundidade'),
   'tag':('rejected','rejeitada'),
   'how':('Treat a cycle as ordinary deep nesting and let the depth ceiling catch it a few child workflows down.',
          'Tratar um ciclo como aninhamento profundo comum e deixar o teto de profundidade pegá-lo alguns child workflows abaixo.'),
   'pros':[('One control instead of two','Um controle em vez de dois')],
   'cons':[('It spends real money and real child workflows before refusing something that was never valid',
            'Gasta dinheiro real e child workflows reais antes de recusar algo que nunca foi válido'),
           ('The error says “too deep” when the truth is “this is circular” — the author fixes the wrong thing',
            'O erro diz “fundo demais” quando a verdade é “isto é circular” — o autor conserta a coisa errada')],
   'cost':[('hi',('Client pays: <b>for a call that was never valid</b>','Cliente paga: <b>por uma chamada que nunca foi válida</b>')),
           ('hi',('Ours: <b>the wrong diagnosis, at fleet scale</b>','Nosso: <b>o diagnóstico errado, em escala de frota</b>'))]},
 ],
 'rec':(
  '<p><strong>A, and it is not a tunable</strong> — there is no depth at which calling back into a waiting ancestor becomes correct. '
  'The depth ceiling stays as a separate, weaker guard for the legitimate case: composition that is genuinely nested but not circular.</p>'
  '<p>What B6 has to prove is only that the guard <em>survived the boundary</em>: the visited set and the depth counter must live in state that '
  'crosses into the child workflow, not in a closure that stayed behind in the parent process.</p>',
  '<p><strong>A, e não é configurável</strong> — não existe profundidade em que chamar de volta um ancestral que está esperando passe a ser correto. '
  'O teto de profundidade permanece como guarda separada e mais fraca para o caso legítimo: composição genuinamente aninhada, mas não circular.</p>'
  '<p>O que a B6 precisa provar é apenas que a guarda <em>sobreviveu à fronteira</em>: o conjunto de visitados e o contador de profundidade têm de viver num estado que '
  'atravessa para o child workflow, não num closure que ficou para trás no processo pai.</p>'),
 'who':[('Engineering — settled in S1','Engenharia — decidida na S1')],
}

DECISIONS = [DEC_ARRAY, DEC_IDENTITY, DEC_CYCLE]

PARTS = [
{'n':'1','title':('Condition and loop as deterministic control flow','Condição e laço como controle de fluxo determinístico'),
 'loc':'back/src/app-api/flux/scheduler.ts',
 'purpose':('Express the two control-flow types as workflow constructs that replay to the same answer every time.',
            'Expressar os dois tipos de controle de fluxo como construções de workflow que, no replay, chegam sempre à mesma resposta.'),
 'body':('<p>Temporal workflows must be <strong>deterministic on replay</strong>. That is not a style preference here — it is the constraint that decides how the '
         'code is written: <strong>loop counters and condition results must come from activity results or from workflow state, never from ambient time or randomness</strong>.</p>'
         '<p>Two pieces of the scheduler already carry the semantics and should be used rather than re-derived:</p>',
         '<p>Workflows do Temporal precisam ser <strong>determinísticos no replay</strong>. Isso não é preferência de estilo aqui — é a restrição que decide como o '
         'código é escrito: <strong>contadores de laço e resultados de condição precisam vir de resultados de activity ou do estado do workflow, nunca de tempo ambiente ou aleatoriedade</strong>.</p>'
         '<p>Duas peças do scheduler já carregam a semântica e devem ser usadas em vez de re-derivadas:</p>'),
 'list':[('<code>completeCondition(state, id, handle)</code> — the condition marks the handle it took, and the scheduler decides what that means for the work queue. '
          'The node stops rewriting the queue; it reports which branch it chose.',
          '<code>completeCondition(state, id, handle)</code> — a condição marca o handle que tomou, e o scheduler decide o que isso significa para a fila de trabalho. '
          'O node para de reescrever a fila; ele relata qual ramo escolheu.'),
         ('<code>computeLoopBody</code> — <strong>the loop body already exists</strong>. Use it instead of re-deriving the body from indices, which is what the '
          'inline <code>arrayNode</code> does today between <code>firstId</code> and <code>loopingToId</code>.',
          '<code>computeLoopBody</code> — <strong>o corpo do laço já existe</strong>. Use-o em vez de re-derivar o corpo a partir de índices, que é o que o '
          '<code>arrayNode</code> inline faz hoje entre <code>firstId</code> e <code>loopingToId</code>.')],
 'body2':('<p><strong>Out of scope:</strong> changing what a condition means or how a loop terminates. The <code>evaluateLoopCondition</code> behaviour, '
          '<strong>including the maximum-iteration guard</strong>, ports as-is.</p>',
          '<p><strong>Fora de escopo:</strong> mudar o que uma condição significa ou como um laço termina. O comportamento do <code>evaluateLoopCondition</code>, '
          '<strong>inclusive a guarda de iteração máxima</strong>, é portado como está.</p>'),
 'ba':(('<code>conditionNode</code> mutates <code>currentLoopCounter</code> in place and rewrites the engine&#x27;s work queue via <code>newIds = findConnectedNodes(...)</code>. The queue is whatever the node last wrote into it.',
        'O <code>conditionNode</code> muta o <code>currentLoopCounter</code> no lugar e reescreve a fila de trabalho do motor via <code>newIds = findConnectedNodes(...)</code>. A fila é o que o node escreveu nela por último.'),
       ('The condition reports a handle, the scheduler owns the queue, and the whole thing replays to the same answer — which a test asserts, not a person.',
        'A condição relata um handle, o scheduler é dono da fila, e o conjunto inteiro replaya para a mesma resposta — o que um teste afirma, não uma pessoa.'))},

{'n':'2','title':('Child workflows for <code>fluxBox</code> and <code>libraryNode</code>','Child workflows para <code>fluxBox</code> e <code>libraryNode</code>'),
 'loc':'flux.service.ts:5400, 5717 · :2660, :3287',
 'purpose':('Carry across the boundary everything the parameter list carries today — and lose none of the three things that can be lost independently.',
            'Levar pela fronteira tudo o que a lista de parâmetros carrega hoje — e não perder nenhuma das três coisas que podem se perder independentemente.'),
 'body':('<p><code>fluxBox</code> executes another whole flow inside the node, <strong>inheriting the parent&#x27;s run-log collector, cancel key and trigger counters</strong>. '
         '<code>libraryNode</code> is structurally the same, and the engine already treats them together (<code>:2660</code>, <code>:3287</code>) — so they '
         '<strong>migrate as one unit</strong>, or the contract gets written twice and the two copies drift.</p>'
         '<p>Three properties travel today because everything shares a process. Each is carried by a different parameter, and <strong>each can be lost independently</strong>:</p>',
         '<p>O <code>fluxBox</code> executa um outro fluxo inteiro dentro do node, <strong>herdando o coletor de run-log, a chave de cancelamento e os contadores de gatilho do pai</strong>. '
         'O <code>libraryNode</code> é estruturalmente igual, e o motor já os trata juntos (<code>:2660</code>, <code>:3287</code>) — então eles '
         '<strong>migram como uma unidade</strong>, ou o contrato é escrito duas vezes e as duas cópias divergem.</p>'
         '<p>Três propriedades viajam hoje porque tudo compartilha um processo. Cada uma é carregada por um parâmetro diferente, e <strong>cada uma pode se perder sozinha</strong>:</p>'),
 'list':[('<strong>Cancellation propagation</strong> — native to Temporal child workflows, so this one gets easier, not harder.',
          '<strong>Propagação de cancelamento</strong> — nativa em child workflows do Temporal, então esta fica mais fácil, não mais difícil.'),
         ('<strong>Nested run logs</strong> — a child&#x27;s node logs still have to appear under the parent, which is the timeline the product already shows.',
          '<strong>Run logs aninhados</strong> — os logs de node do filho ainda têm de aparecer sob o pai, que é a linha do tempo que o produto já exibe.'),
         ('<strong>Billing attribution</strong> — tokens are attributed to the parent&#x27;s <code>billingFlowId</code>, not to the sub-flow&#x27;s own id.',
          '<strong>Atribuição de cobrança</strong> — os tokens são atribuídos ao <code>billingFlowId</code> do pai, não ao id próprio do sub-fluxo.')],
 'ba':(('A sub-flow is a function call inside the same process, so the collector, the cancel key and the counters are simply in scope.',
        'Um sub-fluxo é uma chamada de função no mesmo processo, então o coletor, a chave de cancelamento e os contadores estão simplesmente em escopo.'),
       ('A sub-flow is a child workflow, and each of those three is an explicit part of the child&#x27;s input — verified one by one, because they fail one by one.',
        'Um sub-fluxo é um child workflow, e cada uma dessas três coisas é parte explícita da entrada do filho — verificadas uma a uma, porque falham uma a uma.'))},

{'n':'3','title':('The run chain has to cross the boundary','A cadeia do run precisa atravessar a fronteira'),
 'loc':'TASK-S1 · TASK-S3',
 'purpose':('Three ceilings read the chain, and none of them can be expressed if the chain stops at the process edge.',
            'Três tetos leem a cadeia, e nenhum deles pode ser expresso se a cadeia parar na borda do processo.'),
 'body':('<p>The child carries a <code>parentRunId</code> back to its caller, and <strong>the visited-flow set and the depth counter travel with it</strong> '
         '(<code>TASK-S1</code>). Three things depend on that chain existing <em>at this boundary</em> and not only inside one process:</p>',
         '<p>O filho carrega um <code>parentRunId</code> de volta a quem o chamou, e <strong>o conjunto de fluxos visitados e o contador de profundidade viajam junto</strong> '
         '(<code>TASK-S1</code>). Três coisas dependem de essa cadeia existir <em>nesta fronteira</em>, e não apenas dentro de um processo:</p>'),
 'list':[('The <strong>cycle refusal</strong> — it needs a visited set, and the visited set is the chain.',
          'A <strong>recusa de ciclo</strong> — ela precisa de um conjunto de visitados, e o conjunto de visitados é a cadeia.'),
         ('The <strong>depth ceiling</strong> — a counter that resets at the boundary is not a ceiling.',
          'O <strong>teto de profundidade</strong> — um contador que zera na fronteira não é um teto.'),
         ('The <strong>spend ceiling</strong> that <code>TASK-S3</code> applies to the <strong>chain root</strong> — without the chain, five levels of nesting buy five ceilings.',
          'O <strong>teto de gasto</strong> que a <code>TASK-S3</code> aplica à <strong>raiz da cadeia</strong> — sem a cadeia, cinco níveis de aninhamento compram cinco tetos.')],
 'body2':('<p>Which is why the sentence in the spec is phrased the way it is: <strong>a child workflow started without the chain is a child workflow with no ceilings at all</strong> — '
          'and unlike today, a durable platform will faithfully sustain the result across the fleet, retrying each level.</p>',
          '<p>Por isso a frase da spec está escrita como está: <strong>um child workflow iniciado sem a cadeia é um child workflow sem teto algum</strong> — '
          'e, diferente de hoje, uma plataforma durável vai sustentar o resultado fielmente por toda a frota, com retry em cada nível.</p>'),
 'ba':(('Recursion degrades one backend process. Somebody restarts something, and the run never returns.',
        'A recursão degrada um processo de backend. Alguém reinicia alguma coisa, e o run nunca retorna.'),
       ('The chain crosses into every child workflow, so the cycle refusal, the depth ceiling and <code>S3</code>&#x27;s spend ceiling all still apply — at fleet scale.',
        'A cadeia atravessa para todo child workflow, então a recusa de ciclo, o teto de profundidade e o teto de gasto da <code>S3</code> continuam valendo — em escala de frota.')),
 'callouts':[('mig',('This is why S1 shipped in Wave 0','Por isso a S1 saiu na onda 0'),
   ('<p>The guard has to exist <strong>before</strong> the platform learns to sustain the recursion reliably. What is a crash today becomes a '
    'self-healing, fleet-wide, billed loop the day this task ships.</p>',
    '<p>A guarda precisa existir <strong>antes</strong> de a plataforma aprender a sustentar a recursão de forma confiável. O que hoje é um crash vira um '
    'laço auto-recuperável, distribuído pela frota e cobrado, no dia em que esta task subir.</p>'))]},
]

VERIF = [
 (True, ('Negative control — the loop that never ends, and the dead branch','Controle negativo — o laço que nunca acaba, e o ramo morto'),
  ('Make a loop&#x27;s termination condition never fire and confirm the guard stops it — <strong>then confirm the workflow surfaces it as a real failure, '
   'not as a workflow that runs until its timeout</strong>. Do the same for a condition branch that marks the wrong handle: assert the dead branch '
   'is marked dead and its downstream nodes do not run.',
   'Faça a condição de término de um laço nunca disparar e confirme que a guarda o para — <strong>depois confirme que o workflow expõe isso como falha real, '
   'não como um workflow que roda até o timeout</strong>. Faça o mesmo com um ramo de condição que marca o handle errado: afirme que o ramo morto '
   'é marcado como morto e que os nodes a jusante dele não rodam.')),
 (True, ('Replay determinism','Determinismo de replay'),
  ('Take a completed workflow history and replay it. <strong>Any non-determinism shows up here and nowhere else</strong>; '
   'this test is not optional for a control-flow workflow.',
   'Pegue um histórico de workflow concluído e faça o replay. <strong>Qualquer não determinismo aparece aqui e em nenhum outro lugar</strong>; '
   'este teste não é opcional para um workflow de controle de fluxo.')),
 (False, ('Nested runs — all three properties, separately','Runs aninhados — as três propriedades, separadamente'),
  ('A <code>fluxBox</code> inside a flow must produce nested run logs, propagate cancellation from the parent, and attribute tokens to the parent. '
   '<strong>Verify all three</strong>, since each is carried by a different parameter today and each can be lost independently.',
   'Um <code>fluxBox</code> dentro de um fluxo precisa produzir run logs aninhados, propagar o cancelamento do pai e atribuir os tokens ao pai. '
   '<strong>Verifique as três</strong>, já que cada uma é carregada hoje por um parâmetro diferente e cada uma pode se perder sozinha.')),
 (False, ('Loop billing matches the pre-migration totals','A cobrança de laço bate com os totais pré-migração'),
  ('Per iteration, using the execution identity from <code>B1</code>. A loop is where an identity bug turns into a billing bug, and it is the '
   'cheapest place to catch one.',
   'Por iteração, usando a identidade de execução da <code>B1</code>. Um laço é onde um bug de identidade vira um bug de cobrança, e é o '
   'lugar mais barato para pegar um.')),
]

DONE = ('All four types run in the worker; a <strong>replay test passes</strong>; nested runs keep their logs, cancellation and billing; '
        'and <strong>no executable node type remains inline</strong>.',
        'Os quatro tipos rodam no worker; um <strong>teste de replay passa</strong>; runs aninhados mantêm seus logs, cancelamento e cobrança; '
        'e <strong>nenhum tipo de node executável continua inline</strong>.')

FILES = [('back/src/app-api/flux/flux.service.ts:3540, 3738, 4013, 5400, 5717, 6742', False),
         ('back/src/app-api/flux/scheduler.ts (completeCondition, computeLoopBody)', False),
         ('worker flow workflow + new child workflow', True),
         ('the A1 registry', False)]

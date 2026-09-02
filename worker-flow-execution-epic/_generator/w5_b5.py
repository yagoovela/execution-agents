# -*- coding: utf-8 -*-
TITLE = ('Turn on parallel dispatch', 'Ligar o dispatch paralelo')

GOAL = ('Raise the batch size above one — and <b>only for the flows where that is provably safe</b>.',
        'Elevar o tamanho do lote acima de um — e <b>só para os fluxos onde isso é comprovadamente seguro</b>.')

GLANCE = [
 ('crit', ('Severity','Severidade'), ('High','Alta'),
  ('It removes the back-pressure three accidents were providing. Review §4.5, §4.2.',
   'Remove a contrapressão que três acidentes forneciam. Review §4.5, §4.2.')),
 ('dep', ('Depends on','Depende de'), ('B4 · A track · S2 · S3','B4 · trilha A · S2 · S3'),
  ('Wave 5&#x27;s preconditions are <strong>S1, S2, S3 and E3</strong> — plus B5&#x27;s own per-provider budget.',
   'As precondições da onda 5 são <strong>S1, S2, S3 e E3</strong> — mais o orçamento por provedor da própria B5.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('This is where <strong>Wave 3&#x27;s latency regression is paid back</strong> — with numbers or not at all.',
   'É aqui que a <strong>regressão de latência da onda 3 é paga de volta</strong> — com números ou não vale.')),
 ('ship', ('Rollout','Rollout'), ('By cohort, not by switch','Por coorte, não por chave'),
  ('The eligibility gate means most flows simply stay sequential until their nodes are covered.',
   'O gate de elegibilidade faz a maioria dos fluxos simplesmente continuar sequencial até seus nodes estarem cobertos.')),
]

LEDE = (
 '<p>The persistence model <strong>already supports parallel siblings</strong> (analysis §7.3): '
 '<code>node_executions</code> is one row per execution, and <code>persistNodeSuccess</code> only merges into rows '
 'the activity owns. Two siblings cannot lose each other&#x27;s writes.</p>'
 '<p>What is <strong>not</strong> safe is mixed mode. A node still running inline in the back does not write to its own row — '
 'it ends with <code>addConnectToNodes</code>, which merges the producer&#x27;s output straight into the <strong>target</strong> '
 'node&#x27;s data (<code>folw/contants.ts</code>, via <code>modifyData</code>). '
 '<strong>The gate is not a precaution, it is the correctness condition.</strong></p>',
 '<p>O modelo de persistência <strong>já suporta irmãos em paralelo</strong> (análise §7.3): '
 '<code>node_executions</code> é uma linha por execução, e o <code>persistNodeSuccess</code> só faz merge em linhas '
 'que a activity possui. Dois irmãos não conseguem perder a escrita um do outro.</p>'
 '<p>O que <strong>não</strong> é seguro é o modo misto. Um node que ainda roda inline no back não escreve na própria linha — '
 'ele termina com <code>addConnectToNodes</code>, que faz merge da saída do produtor direto no dado do node '
 '<strong>alvo</strong> (<code>folw/contants.ts</code>, via <code>modifyData</code>). '
 '<strong>O gate não é precaução, é a condição de corretude.</strong></p>')

TABLE = dict(
 head=[('Mode','Modo'),
       ('How a node&#x27;s output reaches the next one','Como a saída de um node chega ao próximo'),
       ('Parallel-safe?','Seguro em paralelo?'),
       ('Why','Por quê')],
 rows=[
  [{'t':('All in the back','Tudo no back')},
   ('<code>addConnectToNodes</code> merges it into the <strong>target</strong> node&#x27;s data',
    'O <code>addConnectToNodes</code> faz merge no dado do node <strong>alvo</strong>'),
   {'t':('Safe — because it is serial','Seguro — porque é serial'),'pill':'ok'},
   ('The engine holds the whole node array in memory and runs one node at a time.',
    'O motor mantém o array inteiro de nodes em memória e roda um node por vez.')],
  [{'t':('All in the worker','Tudo no worker')},
   ('<code>persistNodeSuccess</code> merges it into the node&#x27;s <strong>own</strong> row',
    'O <code>persistNodeSuccess</code> faz merge na <strong>própria</strong> linha do node'),
   {'t':('Safe — because every write is own-row','Seguro — porque toda escrita é na própria linha'),'pill':'ok'},
   ('One <code>node_executions</code> row per execution; two siblings cannot collide (§7.3).',
    'Uma linha de <code>node_executions</code> por execução; dois irmãos não colidem (§7.3).')],
  [{'t':('Mixed, sequential','Misto, sequencial')},
   ('Both mechanisms, one node at a time','Os dois mecanismos, um node por vez'),
   {'t':('Safe today','Seguro hoje'),'pill':'weak'},
   ('This is production right now. The serial engine is the only reason it holds.',
    'Isto é a produção agora. O motor serial é a única razão de funcionar.')],
  [{'t':('Mixed, parallel','Misto, paralelo')},
   ('Both mechanisms, at the same time, on the same row','Os dois mecanismos, ao mesmo tempo, na mesma linha'),
   {'t':('A lost update','Uma escrita perdida'),'pill':'no'},
   ('<strong>Appears rarely and reproduces badly</strong> (§7.4b). This is the row the gate exists to prevent.',
    '<strong>Aparece raramente e reproduz mal</strong> (§7.4b). É esta linha que o gate existe para impedir.')],
 ])

PROSE = (
 'Four calls this task forces and must therefore make. The first decides how parallelism reaches production; '
 'the other three are the parallel-execution UX that review §5 says will otherwise be decided by accident. '
 'Each one opens to the options, what each costs the customer and costs us, and the option we would pick.',
 'Quatro decisões que esta task força e portanto precisa tomar. A primeira decide como o paralelismo chega à produção; '
 'as outras três são a UX de execução paralela que a review §5 diz que, do contrário, será decidida por acidente. '
 'Cada uma abre com as opções, quanto cada uma custa ao cliente e a nós, e a que escolheríamos.')

DEC_ROLLOUT = {
 'k':'decision','id':'B5-a','status':'rec','open':True,
 'q':('What turns parallelism on for a flow — the gate alone, or the gate plus a cohort?',
      'O que liga o paralelismo para um fluxo — só o gate, ou o gate mais uma coorte?'),
 'intro':(
  'Three controls are on the table and they are <strong>not alternatives</strong>: the eligibility gate is a '
  '<em>correctness</em> condition, a cohort is a <em>blast-radius</em> control, and a global switch is a '
  '<em>rollback</em> control. The open question is which of them is load-bearing. Someone will argue — reasonably — '
  'that an eligible flow is provably safe, so the cohort is ceremony. '
  'Note what the gate does <strong>not</strong> prove: it proves no lost update. It does not prove the per-provider budgets '
  'hold, that <code>S3</code>&#x27;s tenancy cap is sized right, or that the three UX decisions below were answered well.',
  'Três controles estão na mesa e <strong>não são alternativas</strong>: o gate de elegibilidade é uma condição de '
  '<em>corretude</em>, a coorte é um controle de <em>raio de impacto</em>, e a chave global é um controle de '
  '<em>rollback</em>. A pergunta aberta é qual deles é estrutural. Alguém vai argumentar — com razão — '
  'que um fluxo elegível é comprovadamente seguro, logo a coorte é cerimônia. '
  'Repare no que o gate <strong>não</strong> prova: ele prova que não há escrita perdida. Não prova que os orçamentos por '
  'provedor aguentam, que o teto de tenancy da <code>S3</code> está dimensionado, nem que as três decisões de UX abaixo '
  'foram bem respondidas.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('All three, layered','As três, em camadas'),
   'tag':('recommended','recomendada'),
   'how':('Eligibility gates correctness, a cohort gates exposure — internal flows, then a small customer cohort, then '
          'general — and a global switch is the way back. Rollback is per flow first, then global.',
          'A elegibilidade limita a corretude, a coorte limita a exposição — fluxos internos, depois uma coorte pequena '
          'de clientes, depois geral — e a chave global é o caminho de volta. O rollback é por fluxo primeiro, depois global.'),
   'pros':[('Each control answers a different failure, so none of them is redundant',
            'Cada controle responde a uma falha diferente, então nenhum é redundante'),
           ('The provider budgets and the UX answers get exercised on flows we own before a customer meets them',
            'Os orçamentos por provedor e as respostas de UX são exercitados em fluxos nossos antes de um cliente encontrá-los'),
           ('Both rollback levels leave Wave 4&#x27;s sequential workflow running — nothing has to be reverted to recover',
            'Os dois níveis de rollback deixam o workflow sequencial da onda 4 rodando — nada precisa ser revertido para recuperar')],
   'cons':[('Two more surfaces to build and to keep honest: cohort membership and a switch that is actually tested',
            'Duas superfícies a mais para construir e manter honestas: a lista da coorte e uma chave que é de fato testada')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('',('Ours: <b>cohort list + kill switch</b>','Nosso: <b>lista de coorte + kill switch</b>'))]},
  {'ltr':'B','name':('The gate alone, then general availability','Só o gate, e depois disponibilidade geral'),
   'how':('Ship the eligibility predicate, and every flow that satisfies it runs in parallel from day one.',
          'Entregar o predicado de elegibilidade, e todo fluxo que o satisfaz roda em paralelo desde o primeiro dia.'),
   'pros':[('Simplest thing that is defensible — the gate really is the correctness condition',
            'A coisa mais simples que se defende — o gate é de fato a condição de corretude'),
           ('No cohort list to maintain, and no second surface to get wrong',
            'Sem lista de coorte para manter, e sem uma segunda superfície para errar')],
   'cons':[('The first flow to exercise a provider burst is a customer&#x27;s, and the symptom is 429s shown as node failures',
            'O primeiro fluxo a exercitar um pico contra um provedor é o de um cliente, e o sintoma são 429s exibidos como falhas de node'),
           ('The three UX decisions land on customers on the same day they land in code',
            'As três decisões de UX chegam aos clientes no mesmo dia em que chegam ao código')],
   'cost':[('',('Client effort: <b>none, but they are the pilot</b>','Esforço do cliente: <b>nenhum, mas ele é o piloto</b>')),
           ('lo',('Ours: <b>one predicate</b>','Nosso: <b>um predicado</b>'))]},
  {'ltr':'C','no':True,'name':('A global flag, flipped per environment','Uma flag global, virada por ambiente'),
   'tag':('not viable','inviável'),
   'how':('One environment variable turns parallel dispatch on for everything running in that environment.',
          'Uma variável de ambiente liga o dispatch paralelo para tudo que roda naquele ambiente.'),
   'pros':[('One line of configuration','Uma linha de configuração')],
   'cons':[('It runs mixed-mode flows in parallel, which is the exact corruption this task exists to prevent',
            'Ela roda fluxos em modo misto em paralelo, que é exatamente a corrupção que esta task existe para impedir'),
           ('There is no per-flow way back, so the only rollback is “turn parallelism off for everyone”',
            'Não existe caminho de volta por fluxo, então o único rollback é “desligar o paralelismo para todo mundo”')],
   'cost':[('hi',('Client risk: <b>a silent lost update</b>','Risco do cliente: <b>uma escrita perdida silenciosa</b>')),
           ('hi',('Ours: <b>no per-flow rollback</b>','Nosso: <b>sem rollback por fluxo</b>'))]},
 ],
 'rec':(
  '<p><strong>A.</strong> The gate is not negotiable — it is the correctness condition and B is not wrong about that. '
  'The cohort is what buys the time to be wrong about <em>the other three decisions on this page</em> without a customer paying for it.</p>'
  '<p>Order the ladder deliberately: <strong>eligibility first</strong> (it refuses nothing a customer can see), '
  '<strong>cohort second</strong> (internal flows have no support cost), <strong>global switch always</strong>. '
  'And keep the switch on a path someone has actually exercised — an untested kill switch is a story, not a control.</p>',
  '<p><strong>A.</strong> O gate não é negociável — é a condição de corretude, e a B não está errada nisso. '
  'A coorte é o que compra tempo para errarmos <em>as outras três decisões desta página</em> sem que um cliente pague por isso.</p>'
  '<p>Ordene a escada de propósito: <strong>elegibilidade primeiro</strong> (não recusa nada que o cliente veja), '
  '<strong>coorte depois</strong> (fluxos internos não têm custo de suporte), <strong>chave global sempre</strong>. '
  'E mantenha a chave num caminho que alguém realmente exercitou — um kill switch não testado é uma história, não um controle.</p>'),
 'who':[('Engineering','Engenharia'),('Product owns the cohort','Produto define a coorte')],
}

DEC_CANCEL = {
 'k':'decision','id':'B5-b','status':'rec',
 'q':('What does a <em>cancelled</em> run mean once several nodes are running at once?',
      'O que significa um run <em>cancelado</em> quando vários nodes rodam ao mesmo tempo?'),
 'intro':(
  'Today cancellation has one meaning because there is one node in flight. Under fan-out, cancelling leaves '
  '<strong>some siblings completed, some aborted, and some never started</strong> (review §5) — and the product already shows a '
  'cancel footprint that assumes a single answer. This is a product decision with an engineering floor: whatever is chosen, '
  '<code>E2</code> aligns it with Temporal&#x27;s native cancellation rather than a poller.',
  'Hoje o cancelamento tem um significado só porque há um node em voo. Com fan-out, cancelar deixa '
  '<strong>alguns irmãos concluídos, alguns abortados e alguns nunca iniciados</strong> (review §5) — e o produto já exibe um '
  'rastro de cancelamento que pressupõe uma resposta única. É uma decisão de produto com um piso de engenharia: seja qual for '
  'a escolha, a <code>E2</code> a alinha ao cancelamento nativo do Temporal em vez de um poller.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Stop scheduling and cancel what is in flight','Parar de agendar e cancelar o que está em voo'),
   'tag':('recommended','recomendada'),
   'how':('The run ends <code>CANCELLED</code> immediately. Per-node states stay literally true: completed, aborted, never started.',
          'O run termina <code>CANCELLED</code> imediatamente. Os estados por node continuam literalmente verdadeiros: concluído, abortado, nunca iniciado.'),
   'pros':[('Stop means stop — the customer pressed it because they wanted the spending to end',
            'Parar significa parar — o cliente apertou porque queria que o gasto acabasse'),
           ('It is what Temporal cancellation does natively, including into child workflows',
            'É o que o cancelamento do Temporal faz nativamente, inclusive para dentro de child workflows'),
           ('The run page can show exactly what happened instead of a single misleading label',
            'A página do run pode mostrar exatamente o que aconteceu em vez de um rótulo único e enganoso')],
   'cons':[('A push node cancelled mid-call leaves an outcome nobody can state — it may or may not have fired',
            'Um push node cancelado no meio da chamada deixa um resultado que ninguém sabe declarar — pode ou não ter disparado')],
   'cost':[('lo',('Client sees: <b>an honest partial run</b>','Cliente vê: <b>um run parcial honesto</b>')),
           ('',('Ours: <b>per-node states in the UI</b>','Nosso: <b>estados por node na UI</b>'))]},
  {'ltr':'B','name':('Stop scheduling, let in-flight siblings finish','Parar de agendar, deixar os irmãos em voo terminarem'),
   'how':('No new node starts, but the ones already dispatched run to completion before the run is marked cancelled.',
          'Nenhum node novo inicia, mas os já despachados rodam até o fim antes de o run ser marcado como cancelado.'),
   'pros':[('No node is left in an unknown state, which is the honest problem with A',
            'Nenhum node fica em estado desconhecido, que é o problema honesto da A'),
           ('Side effects already started are allowed to complete rather than half-applied',
            'Efeitos colaterais já iniciados podem concluir em vez de ficar meio aplicados')],
   'cons':[('Cancelling a wide run can take as long as its slowest node — the customer pressed stop and the bill kept going',
            'Cancelar um run largo pode demorar o tempo do node mais lento — o cliente apertou parar e a conta continuou'),
           ('Under fan-out “in flight” can be the whole ready set, so this is close to not cancelling at all',
            'Com fan-out, “em voo” pode ser o conjunto pronto inteiro, então isto é quase não cancelar')],
   'cost':[('hi',('Client waits: <b>up to the slowest node</b>','Cliente espera: <b>até o node mais lento</b>')),
           ('lo',('Ours: <b>no partial-node story</b>','Nosso: <b>sem história de node parcial</b>'))]},
  {'ltr':'C','no':True,'name':('Present the run as if it had not happened','Apresentar o run como se não tivesse acontecido'),
   'tag':('rejected','rejeitada'),
   'how':('Hide the partial outputs and show the run as cancelled with nothing produced.',
          'Esconder as saídas parciais e mostrar o run como cancelado sem nada produzido.'),
   'pros':[('One label, nothing to explain','Um rótulo, nada a explicar')],
   'cons':[('The side effects already happened — an email was sent, a row was written, tokens were charged',
            'Os efeitos colaterais já aconteceram — um e-mail foi enviado, uma linha foi escrita, tokens foram cobrados'),
           ('It hides output the customer paid for, which turns a support question into a trust problem',
            'Esconde uma saída pela qual o cliente pagou, o que transforma uma dúvida de suporte num problema de confiança')],
   'cost':[('hi',('Client loses: <b>output already paid for</b>','Cliente perde: <b>saída já paga</b>')),
           ('hi',('Ours: <b>the run log stops being true</b>','Nosso: <b>o log do run deixa de ser verdadeiro</b>'))]},
 ],
 'rec':(
  '<p><strong>A, and say so in the UI.</strong> A cancelled parallel run is <em>partial by definition</em>, and the product should state that '
  'rather than pick a label that pretends otherwise. The per-node states already exist; what is missing is the sentence next to them.</p>'
  '<p>The one place B is right is push-type nodes. Handle it there, not globally: a node with an external side effect either '
  'completes or is recorded as <strong>unknown</strong> — never silently as aborted.</p>',
  '<p><strong>A, e diga isso na UI.</strong> Um run paralelo cancelado é <em>parcial por definição</em>, e o produto deveria declarar isso '
  'em vez de escolher um rótulo que finge o contrário. Os estados por node já existem; o que falta é a frase ao lado deles.</p>'
  '<p>O único ponto em que a B está certa são os nodes de push. Trate isso lá, não globalmente: um node com efeito colateral externo '
  'ou conclui ou é registrado como <strong>desconhecido</strong> — nunca silenciosamente como abortado.</p>'),
 'who':[('Product','Produto'),('Engineering — E2 owns the mechanism','Engenharia — a E2 é dona do mecanismo')],
}

DEC_ORDER = {
 'k':'decision','id':'B5-c','status':'rec',
 'q':('Two independent push nodes fire in graph order today. Is that a contract?',
      'Dois push nodes independentes disparam na ordem do grafo hoje. Isso é um contrato?'),
 'intro':(
  'Nobody promised it, and nobody wrote it down — it falls out of the engine being sequential. Under fan-out it stops being true, '
  'and <strong>any customer who relied on the incidental ordering will experience it as a regression</strong> (review §5). '
  'This is a refusing-shaped change without a refusal: nothing errors, the order simply differs.',
  'Ninguém prometeu, e ninguém registrou — é consequência de o motor ser sequencial. Com fan-out deixa de ser verdade, '
  'e <strong>qualquer cliente que dependia dessa ordenação incidental vai sentir isso como regressão</strong> (review §5). '
  'É uma mudança com formato de recusa, sem recusa: nada dá erro, a ordem simplesmente muda.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('It was incidental — document it and let it go','Era incidental — documentar e deixar ir'),
   'tag':('recommended','recomendada'),
   'how':('Independent nodes are explicitly unordered. The scheduler&#x27;s dependency edges are the <em>only</em> ordering guarantee, '
          'and a customer who needs an order expresses it as an edge.',
          'Nodes independentes são explicitamente sem ordem. As arestas de dependência do scheduler são a <em>única</em> garantia de ordem, '
          'e o cliente que precisa de uma ordem a expressa como uma aresta.'),
   'pros':[('It is the truth, and it is a rule a customer can act on — draw the edge',
            'É a verdade, e é uma regra sobre a qual o cliente pode agir — desenhe a aresta'),
           ('Preserving the accident means serialising exactly the nodes parallelism was bought for',
            'Preservar o acidente significa serializar justamente os nodes pelos quais o paralelismo foi comprado'),
           ('The dependency edges already are the answer — review §4.4 says so; this states it instead of assuming it',
            'As arestas de dependência já são a resposta — a review §4.4 diz isso; aqui declaramos em vez de supor')],
   'cons':[('A flow that works today can start doing its two side effects in the other order, with no error to point at',
            'Um fluxo que funciona hoje pode passar a fazer seus dois efeitos colaterais na outra ordem, sem erro para apontar')],
   'cost':[('',('Client effort: <b>draw an edge, once</b>','Esforço do cliente: <b>desenhar uma aresta, uma vez</b>')),
           ('lo',('Ours: <b>documentation and a count</b>','Nosso: <b>documentação e uma contagem</b>'))]},
  {'ltr':'B','name':('Preserve it — side-effect nodes run in a serialised lane','Preservar — nodes com efeito colateral numa via serializada'),
   'how':('Nodes classified as side-effecting keep running one at a time, in scheduler order, while pure nodes fan out.',
          'Nodes classificados como de efeito colateral continuam rodando um por vez, na ordem do scheduler, enquanto nodes puros abrem em leque.'),
   'pros':[('No customer-visible regression at all','Nenhuma regressão visível para o cliente'),
           ('Keeps the parallelism where most of the time is actually spent — LLM and search nodes',
            'Mantém o paralelismo onde a maior parte do tempo é gasta — nodes de LLM e de busca')],
   'cons':[('Somebody has to define which types count as side-effecting, and that list will be wrong at the edges',
            'Alguém precisa definir quais tipos contam como efeito colateral, e essa lista vai errar nas bordas'),
           ('It preserves an ordering nobody specified, which makes it a contract by accident — permanently',
            'Preserva uma ordem que ninguém especificou, o que a torna um contrato por acidente — permanentemente')],
   'cost':[('lo',('Client sees: <b>no change</b>','Cliente vê: <b>nenhuma mudança</b>')),
           ('hi',('Ours: <b>a fifth list to maintain</b>','Nosso: <b>uma quinta lista para manter</b>'))]},
  {'ltr':'C','name':('Per-flow opt-out','Opt-out por fluxo'),
   'tag':('escape hatch','válvula de escape'),
   'how':('A flow can declare “keep my side effects ordered” and is then run with the serialised lane from B.',
          'Um fluxo pode declarar “mantenha meus efeitos colaterais ordenados” e passa a rodar com a via serializada da B.'),
   'pros':[('The customer who genuinely depends on the order says so, and pays the latency for it',
            'O cliente que realmente depende da ordem declara isso, e paga a latência por isso'),
           ('Composes with A — it is A plus a named exception, not a different model',
            'Compõe com a A — é a A mais uma exceção nomeada, não outro modelo')],
   'cons':[('Invisible until somebody is already bitten, because nobody sets a switch for a problem they have not had',
            'Invisível até alguém já ter se queimado, porque ninguém liga um switch para um problema que ainda não teve'),
           ('Another per-flow setting to explain, document and support',
            'Mais uma configuração por fluxo para explicar, documentar e suportar')],
   'cost':[('',('Client effort: <b>one toggle</b>','Esforço do cliente: <b>um toggle</b>')),
           ('',('Ours: <b>B&#x27;s machinery, opt-in</b>','Nosso: <b>a maquinaria da B, opcional</b>'))]},
 ],
 'rec':(
  '<p><strong>A — but measure before declaring the regression theoretical.</strong> <code>PLAN §3.3.2</code> applies even though nothing is refused: '
  'count the production flows that have <strong>two or more independent side-effect nodes in one ready set</strong>. '
  'If that count is zero, A is free. If it is not, those owners are the cohort to talk to before the switch is thrown.</p>'
  '<p>Keep C in the drawer. Ship it if the count says somebody needs it — not before.</p>',
  '<p><strong>A — mas meça antes de declarar a regressão teórica.</strong> O <code>PLAN §3.3.2</code> se aplica mesmo sem recusa: '
  'conte os fluxos em produção que têm <strong>dois ou mais nodes de efeito colateral independentes num mesmo conjunto pronto</strong>. '
  'Se essa contagem for zero, a A sai de graça. Se não for, esses donos são a coorte com quem falar antes de virar a chave.</p>'
  '<p>Deixe a C na gaveta. Entregue se a contagem disser que alguém precisa — não antes.</p>'),
 'who':[('Product','Produto'),('Engineering runs the count','Engenharia faz a contagem')],
}

DEC_ERROR = {
 'k':'decision','id':'B5-d','status':'rec',
 'q':('When several siblings fail at once, which failure names the run?',
      'Quando vários irmãos falham ao mesmo tempo, qual falha dá nome ao run?'),
 'intro':(
  'Fail-fast stops at the first error today, so “the run&#x27;s error” has one candidate. With a batch in flight several nodes '
  'can fail simultaneously (review §5), and every consumer of that field — the run page, the notification, the webhook payload — '
  'still expects exactly one. Note the interaction with this task&#x27;s own determinism check: '
  '<strong>if the name is chosen by whichever failure landed first, the same flow failing the same way can name a different node on each run.</strong>',
  'O fail-fast para no primeiro erro hoje, então “o erro do run” tem um único candidato. Com um lote em voo, vários nodes '
  'podem falhar ao mesmo tempo (review §5), e todo consumidor desse campo — a página do run, a notificação, o payload do webhook — '
  'continua esperando exatamente um. Repare na interação com a checagem de determinismo desta própria task: '
  '<strong>se o nome for escolhido pela falha que chegou primeiro, o mesmo fluxo falhando do mesmo jeito pode nomear um node diferente a cada run.</strong>'),
 'opts':[
  {'ltr':'A','name':('First to fail, by time','A primeira a falhar, por tempo'),
   'how':('The earliest failure to arrive names the run; the others are recorded on their own nodes.',
          'A primeira falha a chegar nomeia o run; as outras ficam registradas em seus próprios nodes.'),
   'pros':[('Closest to today&#x27;s wording, so nothing downstream has to change',
            'Mais próximo do texto de hoje, então nada a jusante muda'),
           ('Trivial to implement — it is what a race already produces',
            'Trivial de implementar — é o que uma corrida já produz')],
   'cons':[('Non-deterministic: two runs of the same broken flow can blame different nodes',
            'Não determinístico: dois runs do mesmo fluxo quebrado podem culpar nodes diferentes'),
           ('Support cannot reproduce a report, and a test cannot assert the message',
            'O suporte não consegue reproduzir um relato, e um teste não consegue afirmar a mensagem')],
   'cost':[('hi',('Client sees: <b>a different cause each time</b>','Cliente vê: <b>uma causa diferente a cada vez</b>')),
           ('lo',('Ours: <b>nothing to build</b>','Nosso: <b>nada a construir</b>'))]},
  {'ltr':'B','pick':True,'name':('Deterministic tie-break, in scheduler order','Desempate determinístico, na ordem do scheduler'),
   'tag':('recommended','recomendada'),
   'how':('Among the nodes that failed, the first in the scheduler&#x27;s own ordering names the run — the same answer on every replay.',
          'Entre os nodes que falharam, o primeiro na ordenação do próprio scheduler nomeia o run — a mesma resposta em todo replay.'),
   'pros':[('The same flow failing the same way names the same node, every time',
            'O mesmo fluxo falhando do mesmo jeito nomeia o mesmo node, sempre'),
           ('Makes the failure message assertable in a test and reproducible in support',
            'Torna a mensagem de falha afirmável num teste e reproduzível no suporte'),
           ('Reuses the ordering the scheduler already owns — no new notion of “first”',
            'Reaproveita a ordenação que o scheduler já possui — sem uma nova noção de “primeiro”')],
   'cons':[('The named node is not necessarily the one that failed first in time, which reads oddly in a log',
            'O node nomeado não é necessariamente o que falhou primeiro no tempo, o que soa estranho num log')],
   'cost':[('lo',('Client sees: <b>the same cause every time</b>','Cliente vê: <b>a mesma causa sempre</b>')),
           ('lo',('Ours: <b>a sort, not a subsystem</b>','Nosso: <b>uma ordenação, não um subsistema</b>'))]},
  {'ltr':'C','name':('The run carries the whole failure set','O run carrega o conjunto inteiro de falhas'),
   'tag':('pairs with B','combina com a B'),
   'how':('Every simultaneous failure is stored, and the run exposes a set plus one summary line.',
          'Toda falha simultânea é guardada, e o run expõe um conjunto mais uma linha de resumo.'),
   'pros':[('Honest — when four nodes fail, four nodes failed','Honesto — quando quatro nodes falham, quatro nodes falharam'),
           ('Diagnosis stops depending on which failure won a race','O diagnóstico deixa de depender de qual falha ganhou a corrida')],
   'cons':[('Every consumer of “the run&#x27;s error” has to learn a new shape — UI, notification, webhook payload',
            'Todo consumidor de “o erro do run” precisa aprender um formato novo — UI, notificação, payload de webhook'),
           ('Alone it does not answer the question: something still has to pick the summary line',
            'Sozinha não responde a pergunta: algo ainda precisa escolher a linha de resumo')],
   'cost':[('',('Client sees: <b>all the causes</b>','Cliente vê: <b>todas as causas</b>')),
           ('hi',('Ours: <b>every consumer changes</b>','Nosso: <b>todo consumidor muda</b>'))]},
 ],
 'rec':(
  '<p><strong>B for the name, C for the record.</strong> Store every simultaneous failure, and let the scheduler&#x27;s ordering pick which one is shown. '
  'They are not competing answers: C makes the data honest and B makes the summary stable.</p>'
  '<p>The reason to care is one row up on this page: this task has to prove that <strong>the same flow run twice produces the same result</strong>. '
  'A run whose error message is decided by a race fails that check for a reason that has nothing to do with the outputs.</p>',
  '<p><strong>B para o nome, C para o registro.</strong> Guarde toda falha simultânea, e deixe a ordenação do scheduler escolher qual é exibida. '
  'Não são respostas concorrentes: a C torna o dado honesto e a B torna o resumo estável.</p>'
  '<p>O motivo para se importar está uma linha acima nesta página: esta task precisa provar que <strong>o mesmo fluxo rodado duas vezes produz o mesmo resultado</strong>. '
  'Um run cuja mensagem de erro é decidida por uma corrida falha essa checagem por um motivo que nada tem a ver com as saídas.</p>'),
 'who':[('Engineering','Engenharia'),('Product owns what the run page shows','Produto define o que a página do run exibe')],
}

DECISIONS = [DEC_ROLLOUT, DEC_CANCEL, DEC_ORDER, DEC_ERROR]

PARTS = [
{'n':'1','title':('The eligibility gate is the whole task','O gate de elegibilidade é a task inteira'),
 'loc':('A1 registry · folw/contants.ts', 'registro da A1 · folw/contants.ts'),
 'purpose':('Run a flow in parallel only when every executable node in it is a migrated type — read from one registry, not guessed.',
            'Rodar um fluxo em paralelo só quando todo node executável dele é de um tipo migrado — lido de um registro, não adivinhado.'),
 'body':('<p>The check is <strong>per flow</strong>, and it is a conjunction: parallel dispatch is allowed only when '
         '<strong>every</strong> executable node in that flow is a migrated type, read from the <code>A1</code> registry. '
         '<code>isMigratedTemporalNode</code>&#x27;s successor is exactly this predicate.</p>'
         '<p>The spec is blunt about the boundary. <strong>Out of scope: anything that widens eligibility by relaxing the gate.</strong> '
         'If a flow is not eligible, the answer is to migrate its remaining nodes — never to make the check lenient.</p>',
         '<p>A checagem é <strong>por fluxo</strong>, e é uma conjunção: o dispatch paralelo só é permitido quando '
         '<strong>todo</strong> node executável daquele fluxo é de um tipo migrado, lido do registro da <code>A1</code>. '
         'O sucessor do <code>isMigratedTemporalNode</code> é exatamente esse predicado.</p>'
         '<p>A spec é direta sobre a fronteira. <strong>Fora de escopo: qualquer coisa que amplie a elegibilidade afrouxando o gate.</strong> '
         'Se um fluxo não é elegível, a resposta é migrar os nodes que faltam — nunca tornar a checagem permissiva.</p>'),
 'ba':(('Batch size is one. A ready set of six independent nodes runs as six sequential round trips, and no gate exists because nothing needs one.',
        'O lote é de tamanho um. Um conjunto pronto de seis nodes independentes roda como seis idas e voltas sequenciais, e nenhum gate existe porque nada precisa dele.'),
       ('A flow whose nodes are all migrated dispatches its ready set as one batch. A flow with one inline node stays sequential and is <strong>counted</strong>, with the node type that disqualified it named.',
        'Um fluxo cujos nodes são todos migrados despacha seu conjunto pronto como um lote. Um fluxo com um node inline continua sequencial e é <strong>contado</strong>, com o tipo de node que o desqualificou nomeado.')),
 'callouts':[('mig',('Ineligible is a measurement, not a refusal','Inelegível é medição, não recusa'),
   ('<p>Nothing a customer does changes when a flow is ineligible — it runs the way it runs today. The list of ineligible flows, '
    'with the disqualifying type named for each, is <strong>the work queue for the A track</strong>.</p>',
    '<p>Nada que o cliente faz muda quando um fluxo é inelegível — ele roda como roda hoje. A lista de fluxos inelegíveis, '
    'com o tipo desqualificador nomeado em cada um, é <strong>a fila de trabalho da trilha A</strong>.</p>'))]},

{'n':'2','title':('Concurrency budgets, per provider and per tenant','Orçamentos de concorrência, por provedor e por tenant'),
 'loc':'review §4.2 · S3',
 'purpose':('A global cap does not stop one wide graph from spending the whole budget on one provider.',
            'Um teto global não impede um grafo largo de gastar o orçamento inteiro num único provedor.'),
 'body':('<p>The gate is about correctness. It says nothing about <strong>capacity</strong>. Unbounded fan-out produces bursts against '
         'OpenAI, Anthropic, Replicate and the integration APIs, and <strong>the first symptom is 429s surfaced to the customer as node failures</strong> — '
         'an error that looks like our platform breaking and is in fact us calling too fast.</p>',
         '<p>O gate é sobre corretude. Ele não diz nada sobre <strong>capacidade</strong>. Fan-out sem limite produz picos contra '
         'OpenAI, Anthropic, Replicate e as APIs de integração, e <strong>o primeiro sintoma são 429s exibidos ao cliente como falhas de node</strong> — '
         'um erro que parece a nossa plataforma quebrando e que na verdade somos nós chamando rápido demais.</p>'),
 'list':[('<strong>Per provider</strong> — a concurrency budget derived from that provider&#x27;s real rate limit, and <strong>shared across the fleet</strong> '
          'rather than counted per replica. A per-replica budget multiplies by the replica count, which is the number this epic exists to raise.',
          '<strong>Por provedor</strong> — um orçamento de concorrência derivado do limite real daquele provedor, e <strong>compartilhado por toda a frota</strong> '
          'em vez de contado por réplica. Um orçamento por réplica multiplica pela contagem de réplicas, que é justamente o número que este épico existe para aumentar.'),
         ('<strong>Per tenant</strong> — enforced by <code>S3</code>, which this task depends on. Without it, fan-out is a fairness bug: '
          'one customer&#x27;s wide graph consumes the parallelism everyone else was going to use.',
          '<strong>Por tenant</strong> — imposto pela <code>S3</code>, da qual esta task depende. Sem ela, o fan-out é um bug de justiça: '
          'o grafo largo de um cliente consome o paralelismo que todos os outros iam usar.')],
 'ba':(('One node in flight per run, so a burst is impossible and no budget is needed. The throttle is the sequential loop, and nobody chose it.',
        'Um node em voo por run, então um pico é impossível e nenhum orçamento é necessário. A trava é o laço sequencial, e ninguém a escolheu.'),
       ('Fan-out is bounded by the provider&#x27;s real limit and by the tenant&#x27;s share. Excess is queued by us, not refused by the provider and shown to the customer as a failed node.',
        'O fan-out é limitado pelo limite real do provedor e pela fatia do tenant. O excesso é enfileirado por nós, não recusado pelo provedor e mostrado ao cliente como um node que falhou.')),
 'callouts':[('decide',('A global cap is not the same control','Um teto global não é o mesmo controle'),
   ('<p>One number for the whole fleet still lets a single wide graph spend all of it on one provider, while the other providers sit idle and '
    'that customer&#x27;s calls get 429s. Review §4.2 is explicit that this needs a <strong>per-provider, per-tenant</strong> budget — '
    '<strong>not just “pick a cap”</strong>.</p>',
    '<p>Um número só para toda a frota ainda permite que um único grafo largo gaste tudo num provedor, enquanto os outros ficam ociosos e '
    'as chamadas daquele cliente tomam 429. A review §4.2 é explícita: isto precisa de um orçamento <strong>por provedor e por tenant</strong> — '
    '<strong>não apenas “escolher um teto”</strong>.</p>'))]},

{'n':'3','title':('The preconditions, and why the order is not optional','As precondições, e por que a ordem não é opcional'),
 'loc':'review §4.5',
 'purpose':('The blocking wait was providing back-pressure nobody designed. Removing it before the ceilings exist replaces a slow system with an unstable one.',
            'A espera bloqueante fornecia uma contrapressão que ninguém projetou. Removê-la antes de os tetos existirem troca um sistema lento por um instável.'),
 'body':('<p><code>await handle.result()</code> was treated as pure waste. It is also back-pressure: '
         '<strong>while the backend blocks, it is not starting more work</strong>. The removal is still right; the ordering is not optional.</p>'
         '<p>Wave 5&#x27;s preconditions, all shipped in earlier waves:</p>',
         '<p>O <code>await handle.result()</code> era tratado como puro desperdício. Ele também é contrapressão: '
         '<strong>enquanto o backend bloqueia, ele não está começando mais trabalho</strong>. Remover continua certo; a ordem é que não é opcional.</p>'
         '<p>As precondições da onda 5, todas entregues em ondas anteriores:</p>'),
 'list':[('<strong><code>S1</code></strong> — the recursion ceiling. <code>B6</code> turns sub-flows into child workflows, and a durable platform will sustain a cycle across the whole fleet.',
          '<strong><code>S1</code></strong> — o teto de recursão. A <code>B6</code> transforma sub-fluxos em child workflows, e uma plataforma durável sustenta um ciclo por toda a frota.'),
         ('<strong><code>S2</code></strong> — the connection ceiling. The worker pool sets no <code>max</code>, so connections scale linearly with replicas against a <code>max_connections</code> shared with the API.',
          '<strong><code>S2</code></strong> — o teto de conexões. O pool do worker não define <code>max</code>, então as conexões crescem linearmente com as réplicas contra um <code>max_connections</code> compartilhado com a API.'),
         ('<strong><code>S3</code></strong> — spend and tenancy: the per-run cost ceiling and the per-tenant concurrency cap, which is what makes the per-tenant half of Part 2 enforceable at all.',
          '<strong><code>S3</code></strong> — gasto e tenancy: o teto de custo por run e o teto de concorrência por tenant, que é o que torna a metade “por tenant” da Parte 2 aplicável.'),
         ('<strong><code>E3</code></strong> — notifications that cross replicas, shipped <em>before</em> parallelism multiplies the event rate.',
          '<strong><code>E3</code></strong> — notificações que atravessam réplicas, entregues <em>antes</em> de o paralelismo multiplicar a taxa de eventos.'),
         ('<strong>B5&#x27;s own per-provider budget</strong> — the one precondition this task owns itself.',
          '<strong>O orçamento por provedor da própria B5</strong> — a única precondição que esta task possui.')],
 'ba':(('Three accidents provide the ceilings: one sequential engine loop, five queued runs per backend replica (<code>AGENT_CONCURRENCY</code>; one until 2026-08-21), and a blocking wait on every Temporal node. None of them was designed as a per-tenant safeguard.',
        'Três acidentes fornecem os tetos: um laço de motor sequencial, cinco runs enfileirados por réplica de backend (<code>AGENT_CONCURRENCY</code>; um até 2026-08-21), e uma espera bloqueante em todo node do Temporal. Nenhum deles foi projetado como proteção por tenant.'),
       ('All three are gone, and every ceiling they were accidentally providing has an explicit owner that shipped first.',
        'Os três desaparecem, e todo teto que eles forneciam por acidente tem um dono explícito que foi entregue antes.'))},

{'n':'4','title':('What a parallel run looks like from the outside','Como um run paralelo se parece por fora'),
 'loc':'review §5 · PLAN §6 R4',
 'purpose':('Several nodes are RUNNING at once, and “which node is the run on” stops having one answer.',
            'Vários nodes ficam RUNNING ao mesmo tempo, e “em que node o run está” deixa de ter uma resposta única.'),
 'body':('<p>The builder shows per-node status today. With fan-out, several nodes are <code>RUNNING</code> at the same time — '
         'including in the <strong>cancel footprint the product already shows</strong>. That is a UI change, and it is the visible half of this task.</p>'
         '<p>The other visible half is the number this epic was funded on:</p>',
         '<p>O builder mostra status por node hoje. Com fan-out, vários nodes ficam <code>RUNNING</code> ao mesmo tempo — '
         'inclusive no <strong>rastro de cancelamento que o produto já exibe</strong>. Isso é uma mudança de UI, e é a metade visível desta task.</p>'
         '<p>A outra metade visível é o número pelo qual este épico foi aprovado:</p>'),
 'list':[('Wide flows finish in the time of their <strong>slowest path</strong> rather than the <strong>sum</strong> of their nodes.',
          'Fluxos largos terminam no tempo do seu <strong>caminho mais lento</strong> em vez da <strong>soma</strong> dos seus nodes.'),
         ('<code>R4</code> in <code>PLAN §6</code> predicted a latency regression from the A track — every migrated node is a blocking round trip until this task. '
          '<strong>This is where that claim is settled with numbers or not at all.</strong>',
          'O <code>R4</code> do <code>PLAN §6</code> previu uma regressão de latência vinda da trilha A — todo node migrado é uma ida e volta bloqueante até esta task. '
          '<strong>É aqui que essa afirmação é resolvida com números, ou não vale.</strong>'),
         ('Determinism has to hold: the same flow run twice in parallel must produce the same final outputs.',
          'O determinismo precisa valer: o mesmo fluxo rodado duas vezes em paralelo tem de produzir as mesmas saídas finais.')],
 'ba':(('A flow with six independent nodes takes the sum of six round trips, and every node the A track migrated made that sum larger, not smaller.',
        'Um fluxo com seis nodes independentes leva a soma de seis idas e voltas, e todo node que a trilha A migrou tornou essa soma maior, não menor.'),
       ('The same flow takes the time of its slowest node, and the regression the A track introduced is measured against the pre-epic baseline.',
        'O mesmo fluxo leva o tempo do seu node mais lento, e a regressão que a trilha A introduziu é medida contra a linha de base anterior ao épico.'))},
]

VERIF = [
 (True, ('Negative control — the corruption test','Controle negativo — o teste de corrupção'),
  ('Force an <strong>ineligible</strong> flow — one containing an inline node — through the parallel path and <strong>demonstrate the lost update</strong>: '
   'two writers on one <code>flows_nodes</code> row, one write disappearing. Then confirm the gate refuses that flow. '
   '<strong>This is the test that justifies the gate</strong>; without having seen the corruption, nobody will keep the gate strict.',
   'Force um fluxo <strong>inelegível</strong> — um que contenha um node inline — pelo caminho paralelo e <strong>demonstre a escrita perdida</strong>: '
   'dois escritores numa linha de <code>flows_nodes</code>, uma escrita sumindo. Depois confirme que o gate recusa esse fluxo. '
   '<strong>É este teste que justifica o gate</strong>; sem ter visto a corrupção, ninguém vai manter o gate rígido.')),
 (True, ('Measure before refusing','Medir antes de recusar'),
  ('<strong>PLAN §3.3.2.</strong> The eligibility check is a refusing rule. Classify <strong>every production flow</strong> as eligible or ineligible and, '
   'for each ineligible one, <strong>name the node type that disqualified it</strong>. Refused-although-it-works must be zero.',
   '<strong>PLAN §3.3.2.</strong> A checagem de elegibilidade é uma regra que recusa. Classifique <strong>todo fluxo em produção</strong> como elegível ou inelegível e, '
   'para cada inelegível, <strong>nomeie o tipo de node que o desqualificou</strong>. “Recusado embora funcione” tem de ser zero.')),
 (False, ('Determinism, with a count','Determinismo, com uma contagem'),
  ('The same flow run twice in parallel must produce the same final outputs. Run it enough times to mean something, and <strong>record the count</strong> — '
   '“we ran it a few times” is not a result.',
   'O mesmo fluxo rodado duas vezes em paralelo tem de produzir as mesmas saídas finais. Rode vezes suficientes para significar algo, e <strong>registre a contagem</strong> — '
   '“rodamos algumas vezes” não é um resultado.')),
 (False, ('The latency claim, settled','A afirmação de latência, resolvida'),
  ('Measure the latency the epic bought back against the <strong>pre-epic baseline</strong>. <code>R4</code> in <code>PLAN §6</code> predicted the regression from the A track; '
   'this is where the claim is settled with numbers.',
   'Meça a latência que o épico recuperou contra a <strong>linha de base anterior ao épico</strong>. O <code>R4</code> do <code>PLAN §6</code> previu a regressão da trilha A; '
   'é aqui que a afirmação é resolvida com números.')),
]

DONE = ('Eligible flows run their ready set concurrently; ineligible flows run sequentially and <strong>are counted</strong>; '
        'the corruption case is a passing test; and latency is measured against the pre-epic baseline.',
        'Fluxos elegíveis rodam seu conjunto pronto de forma concorrente; fluxos inelegíveis rodam sequencialmente e <strong>são contados</strong>; '
        'o caso de corrupção é um teste que passa; e a latência é medida contra a linha de base anterior ao épico.')

FILES = [('new eligibility predicate over the A1 registry', True),
         ('the flow workflow from B4', False),
         ('back/src/app-api/folw/contants.ts (documented as the reason for the gate)', False),
         ('per-provider concurrency budget (review §4.2)', True)]

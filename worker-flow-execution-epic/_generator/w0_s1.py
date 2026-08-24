# -*- coding: utf-8 -*-
TITLE=('Depth ceiling and cycle detection for sub-flows','Teto de profundidade e detecção de ciclo em sub-fluxos')
GOAL=('Make a self-referencing flow <b>fail fast</b> instead of recursing until something dies.',
      'Fazer um fluxo auto-referente <b>falhar rápido</b> em vez de recursar até alguma coisa morrer.')
GLANCE=[
 ('crit',('Severity','Severidade'),('Critical','Crítica'),
  ('Two people composing reusable flows produce this by accident. Review §1.1.',
   'Duas pessoas compondo fluxos reutilizáveis produzem isto por acidente. Review §1.1.')),
 ('dep',('Depends on','Depende de'),('Nothing','Nada'),
  ('But it <strong>blocks B6</strong> — the guard has to exist before sub-flows become child workflows.',
   'Mas <strong>bloqueia a B6</strong> — a guarda tem de existir antes de sub-fluxos virarem child workflows.')),
 ('wave',('Wave','Onda'),('Wave 0','Onda 0'),
  ('Best done with S4 — same class of guard, same test harness.',
   'Melhor feita junto da S4 — mesma classe de guarda, mesmo aparato de teste.')),
 ('ship',('Blast radius today','Raio de impacto hoje'),('One process','Um processo'),
  ('After B6, Temporal will faithfully sustain the recursion across the whole fleet, retrying each level.',
   'Depois da B6, o Temporal vai sustentar a recursão fielmente por toda a frota, com retry em cada nível.')),
]
LEDE=(
 '<p><code>flowCallerNode</code> calls <code>this.apiV2()</code> — the whole orchestrator — for the selected flow (<code>flux.service.ts:5611–5622</code>); <code>libraryNode</code> does the same. '
 '<strong>There is no depth limit and no cycle detection</strong>: <code>parentFlowId</code> is threaded for billing attribution only.</p>'
 '<p>Flow A pointing at B and B pointing back at A recurses until the process dies — and <strong>each level is a complete run</strong>, with its own scheduler state, its own <code>node_executions</code> rows, its own run-log tree and its own token spend.</p>',
 '<p>O <code>flowCallerNode</code> chama <code>this.apiV2()</code> — o orquestrador inteiro — para o fluxo selecionado (<code>flux.service.ts:5611–5622</code>); o <code>libraryNode</code> faz o mesmo. '
 '<strong>Não há limite de profundidade nem detecção de ciclo</strong>: o <code>parentFlowId</code> é passado só para atribuição de cobrança.</p>'
 '<p>Um fluxo A apontando para B e B apontando de volta para A recursa até o processo morrer — e <strong>cada nível é um run completo</strong>, com seu próprio estado de scheduler, suas linhas em <code>node_executions</code>, sua árvore de run-log e seu próprio gasto de tokens.</p>')

DEC_IDENTITY={
 'k':'decision','id':'S1-a','plan':'D13','status':'set','open':True,
 'q':('Does a sub-flow share the parent&#x27;s execution identity, get a disconnected one, or a chained one?',
      'Um sub-fluxo compartilha a identidade de execução do pai, ganha uma desconectada, ou uma encadeada?'),
 'intro':('This one is <strong>settled</strong>, and it is recorded here because three other rules in this epic read the answer. '
          'Whatever identity a sub-flow gets determines how depth, cancellation and the spend ceiling can even be expressed.',
          'Esta está <strong>decidida</strong>, e fica registrada aqui porque outras três regras deste épico leem a resposta. '
          'A identidade que um sub-fluxo recebe determina como profundidade, cancelamento e teto de gasto podem sequer ser expressos.'),
 'opts':[
  {'ltr':'A','name':('Absorb into the parent&#x27;s run','Absorver no run do pai'),'no':True,
   'tag':('rejected','rejeitada'),
   'how':('The sub-flow&#x27;s nodes join the parent&#x27;s run — one <code>execId</code>, one scheduler state, one run.',
          'Os nodes do sub-fluxo entram no run do pai — um <code>execId</code>, um estado de scheduler, um run.'),
   'pros':[('Budget and cancellation are trivially one thing','Orçamento e cancelamento viram trivialmente uma coisa só')],
   'cons':[('It is a <strong>different graph</strong> — one <code>SchedulerState</code> would hold two node sets and two termination conditions','É um <strong>grafo diferente</strong> — um <code>SchedulerState</code> teria dois conjuntos de nodes e duas condições de término'),
           ('The nested run-log timeline the product already shows would be lost','A linha do tempo aninhada de run-log que o produto já mostra seria perdida')],
   'cost':[('hi',('Rework: <b>the scheduler</b>','Retrabalho: <b>o scheduler</b>')),
           ('hi',('Loses: <b>nested run log</b>','Perde: <b>run log aninhado</b>'))]},
  {'ltr':'B','name':('A disconnected run','Um run desconectado'),'no':True,
   'tag':('rejected','rejeitada'),
   'how':('The sub-flow starts a fresh, independent run with no link back to its caller.',
          'O sub-fluxo inicia um run novo e independente, sem vínculo com quem o chamou.'),
   'pros':[('Simplest to implement — it is nearly what happens today','Mais simples de implementar — é quase o que acontece hoje')],
   'cons':[('There is no visited set, so <strong>cycle detection becomes impossible</strong>','Não existe conjunto de visitados, então <strong>detectar ciclo fica impossível</strong>'),
           ('Every nesting level buys a <strong>fresh budget and a fresh cost ceiling</strong> — recursion becomes the way to defeat the limit','Cada nível de aninhamento compra um <strong>orçamento novo e um teto de custo novo</strong> — recursão vira a forma de derrotar o limite'),
           ('Cancelling the parent leaves the children running','Cancelar o pai deixa os filhos rodando')],
   'cost':[('lo',('Effort: <b>none</b>','Esforço: <b>nenhum</b>')),
           ('hi',('Defeats: <b>S3 and S4</b>','Derrota: <b>S3 e S4</b>'))]},
  {'ltr':'C','pick':True,'name':('Its own run, chained by <code>parentRunId</code>','Run próprio, encadeado por <code>parentRunId</code>'),
   'tag':('settled','decidida'),
   'how':('The sub-flow gets its own run identity plus an explicit <code>parentRunId</code>, forming a chain back to the origin run.',
          'O sub-fluxo ganha identidade de run própria mais um <code>parentRunId</code> explícito, formando uma cadeia até o run de origem.'),
   'pros':[('<strong>Depth and cycle read the chain</strong> — it <em>is</em> the visited set','<strong>Profundidade e ciclo leem a cadeia</strong> — ela <em>é</em> o conjunto de visitados'),
           ('<strong>Cancellation propagates along it</strong>, which Temporal child workflows give natively','<strong>Cancelamento propaga por ela</strong>, o que child workflows do Temporal dão nativamente'),
           ('<strong>Budget aggregates over it</strong>, so nesting cannot reset the ceiling','<strong>O orçamento agrega sobre ela</strong>, então aninhar não zera o teto'),
           ('The nested run-log timeline is preserved','A linha do tempo aninhada de run-log é preservada')],
   'cons':[('A chain has to be threaded through state that survives the move to child workflows','A cadeia precisa atravessar um estado que sobreviva à mudança para child workflows')],
   'cost':[('',('Effort: <b>run context field</b>','Esforço: <b>campo no contexto do run</b>')),
           ('lo',('Enables: <b>S1, S3, S4, E2</b>','Habilita: <b>S1, S3, S4, E2</b>'))]},
 ],
 'rec':('<p><strong>C, and it is decided.</strong> The easy-to-miss consequence is the third bullet: with a per-run ceiling and a sub-flow creating a new run, '
        '<strong>five levels of nesting would buy five ceilings</strong>. Recursion becomes the way around the limit. <code>TASK-S3</code> is amended so the ceiling applies to the chain.</p>',
        '<p><strong>C, e está decidida.</strong> A consequência fácil de passar batido é o terceiro item: com um teto por run e um sub-fluxo criando um run novo, '
        '<strong>cinco níveis de aninhamento comprariam cinco tetos</strong>. Recursão vira o atalho para furar o limite. A <code>TASK-S3</code> foi emendada para o teto valer para a cadeia.</p>'),
 'who':[('Engineering — settled','Engenharia — decidida')],
}

DEC_CYCLE={
 'k':'decision','id':'S1-b','plan':'D14','status':'set',
 'q':('Is calling a flow already on the chain refused outright, or merely depth-limited?',
      'Chamar um fluxo que já está na cadeia é recusado de imediato, ou apenas limitado por profundidade?'),
 'intro':('The depth ceiling and the cycle rule are <strong>different rules with different justifications</strong>, and the second is stronger. '
          'Treating them as one control is the mistake this decision exists to prevent.',
          'O teto de profundidade e a regra de ciclo são <strong>regras diferentes com justificativas diferentes</strong>, e a segunda é mais forte. '
          'Tratar as duas como um controle só é o erro que esta decisão existe para evitar.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Refused outright, at any depth','Recusado de imediato, em qualquer profundidade'),
   'tag':('settled','decidida'),
   'how':('If the flow being called is already on the call chain, the call is refused — no configuration, no tunable depth at which it becomes allowed.',
          'Se o fluxo chamado já está na cadeia de chamadas, a chamada é recusada — sem configuração, sem profundidade ajustável em que passe a ser permitida.'),
   'pros':[('<strong>A flow on the chain is awaiting a return.</strong> Asking it to start again from the top has no coherent semantics','<strong>Um fluxo na cadeia está aguardando um retorno.</strong> Pedir que ele comece de novo do topo não tem semântica coerente'),
           ('Covers <code>A → B → C → A</code>, not only the direct parent — A is still waiting either way','Cobre <code>A → B → C → A</code>, não só o pai direto — A continua esperando de qualquer forma'),
           ('The message can name the chain, so the author sees which link closed the loop','A mensagem pode nomear a cadeia, para o autor ver qual elo fechou o laço')],
   'cons':[('A flow that legitimately re-enters itself with different inputs is refused too — no known real case','Um fluxo que legitimamente reentra em si com entradas diferentes também é recusado — nenhum caso real conhecido')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('lo',('Ours: <b>a visited set</b>','Nosso: <b>um conjunto de visitados</b>'))]},
  {'ltr':'B','no':True,'name':('Allow it, capped by depth','Permitir, limitado por profundidade'),
   'how':('Treat a cycle as ordinary deep nesting and let the depth ceiling catch it a few levels down.',
          'Tratar um ciclo como aninhamento profundo comum e deixar o teto de profundidade pegá-lo alguns níveis abaixo.'),
   'pros':[('One control instead of two','Um controle em vez de dois')],
   'cons':[('Spends real money and real runs before refusing something that was never valid','Gasta dinheiro e runs reais antes de recusar algo que nunca foi válido'),
           ('The error says “too deep” when the truth is “this is circular” — the author fixes the wrong thing','O erro diz “fundo demais” quando a verdade é “isto é circular” — o autor conserta a coisa errada')],
   'cost':[('',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('hi',('Ours: <b>wrong diagnosis</b>','Nosso: <b>diagnóstico errado</b>'))]},
 ],
 'rec':('<p><strong>A — refused always, and it is not a tunable</strong>, because there is no depth at which calling back into a waiting ancestor becomes correct.</p>'
        '<p>The depth ceiling stays as a separate, weaker guard for the legitimate case: composition that is genuinely nested but not circular.</p>',
        '<p><strong>A — recusado sempre, e não é configurável</strong>, porque não existe profundidade em que chamar de volta um ancestral que está esperando passe a ser correto.</p>'
        '<p>O teto de profundidade permanece como guarda separada e mais fraca para o caso legítimo: composição genuinamente aninhada, mas não circular.</p>'),
 'who':[('Engineering — settled','Engenharia — decidida')],
}

DEC_DEPTH={
 'k':'decision','id':'S1-c','plan':'D6','status':'rec',
 'q':('What is the depth ceiling, and can it be raised without a deploy?',
      'Qual é o teto de profundidade, e ele pode ser elevado sem deploy?'),
 'intro':('Unlike the cycle rule, this one <strong>refuses flows that might work</strong>. That makes it subject to <strong>PLAN §3.3.2</strong>: '
          'measure it against the stored flows first, and drive false refusals to zero before shipping.',
          'Ao contrário da regra de ciclo, esta <strong>recusa fluxos que podem funcionar</strong>. Isso a sujeita ao <strong>PLAN §3.3.2</strong>: '
          'medir contra os fluxos guardados primeiro, e zerar as falsas recusas antes de entregar.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('3, as an env var','3, como variável de ambiente'),
   'tag':('assumption','premissa'),
   'how':('A default of three levels, readable from the environment so it can be raised without a deploy when a real flow needs more.',
          'Um padrão de três níveis, lido do ambiente para poder ser elevado sem deploy quando um fluxo real precisar de mais.'),
   'pros':[('Covers composition of reusable building blocks without allowing accidental deep nesting','Cobre composição de blocos reutilizáveis sem permitir aninhamento profundo acidental'),
           ('A wrong guess is a config change, not an incident','Um chute errado é mudança de config, não um incidente')],
   'cons':[('<strong>If real flows already nest deeper than three, this number is wrong</strong> — the measurement decides, not the default','<strong>Se fluxos reais já aninham mais que três, este número está errado</strong> — quem decide é a medição, não o padrão')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('lo',('Ours: <b>one env var</b>','Nosso: <b>uma env var</b>'))]},
  {'ltr':'B','name':('Per-plan or per-tenant','Por plano ou por tenant'),
   'how':('The ceiling varies by customer tier, the way quota limits do.',
          'O teto varia por tier do cliente, como fazem os limites de cota.'),
   'pros':[('A large customer with a deep legitimate composition is not blocked by a global number','Um cliente grande com composição profunda legítima não é bloqueado por um número global')],
   'cons':[('A safety guard that varies by billing tier is a safety guard nobody can reason about','Uma guarda de segurança que varia por tier de cobrança é uma guarda que ninguém consegue raciocinar'),
           ('Needs a plan-limits surface that does not exist yet for this','Exige uma superfície de limites por plano que ainda não existe para isso')],
   'cost':[('',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('hi',('Ours: <b>plan-limit plumbing</b>','Nosso: <b>encanamento de limites por plano</b>'))]},
  {'ltr':'C','name':('No ceiling — rely on the cycle rule alone','Sem teto — confiar só na regra de ciclo'),
   'how':('Refuse cycles, and let legitimate nesting go as deep as it likes.',
          'Recusar ciclos, e deixar o aninhamento legítimo ir tão fundo quanto quiser.'),
   'pros':[('No false refusals at all','Nenhuma falsa recusa'),
           ('Nothing to measure, nothing to tune','Nada a medir, nada a ajustar')],
   'cons':[('A non-circular chain can still be arbitrarily deep and arbitrarily expensive','Uma cadeia não circular ainda pode ser arbitrariamente profunda e cara'),
           ('Under B6 each level is a child workflow with its own retries — depth multiplies fleet load','Sob a B6 cada nível é um child workflow com seus próprios retries — profundidade multiplica carga da frota')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('hi',('Ours: <b>unbounded nesting cost</b>','Nosso: <b>custo de aninhamento ilimitado</b>'))]},
 ],
 'rec':('<p><strong>A, with the number decided by the measurement and not by this document.</strong> Walk the stored flows: for every flow containing a <code>fluxBox</code> or <code>libraryNode</code>, '
        'compute the real maximum nesting depth. Classify each as <em>would still work</em> or <em>would now be refused</em>, and <strong>drive the second count to zero</strong>.</p>'
        '<p>A ceiling that refuses working customer flows is worse than the recursion it prevents.</p>',
        '<p><strong>A, com o número decidido pela medição e não por este documento.</strong> Percorra os fluxos guardados: para todo fluxo com um <code>fluxBox</code> ou <code>libraryNode</code>, '
        'calcule a profundidade máxima real de aninhamento. Classifique cada um como <em>continuaria funcionando</em> ou <em>passaria a ser recusado</em>, e <strong>zere a segunda contagem</strong>.</p>'
        '<p>Um teto que recusa fluxos de cliente que funcionam é pior que a recursão que ele previne.</p>'),
 'who':[('Engineering, after the measurement','Engenharia, depois da medição')],
}

PARTS=[
{'n':'1','title':('Why now, rather than with B6','Por que agora, e não junto da B6'),
 'loc':'flux.service.ts:5611–5622',
 'purpose':('The guard has to exist before the platform learns to sustain the recursion reliably.',
            'A guarda tem de existir antes de a plataforma aprender a sustentar a recursão de forma confiável.'),
 'body':('<p>Today the blast radius is <strong>one backend process</strong>. It degrades, the run never returns, and somebody restarts something.</p>'
         '<p><strong>B6 turns sub-flows into Temporal child workflows</strong> — and a durable platform will faithfully sustain the recursion across the whole fleet, retrying each level. What is a crash today becomes a self-healing, fleet-wide, billed loop tomorrow.</p>',
         '<p>Hoje o raio de impacto é <strong>um processo de backend</strong>. Ele degrada, o run nunca retorna, e alguém reinicia alguma coisa.</p>'
         '<p><strong>A B6 transforma sub-fluxos em child workflows do Temporal</strong> — e uma plataforma durável vai sustentar a recursão fielmente por toda a frota, com retry em cada nível. O que hoje é um crash vira, amanhã, um laço auto-recuperável, distribuído pela frota, e cobrado.</p>'),
 'ba':(('Two flows referencing each other recurse until the process dies. Each level is a full run with its own rows, its own log tree and its own token spend.',
        'Dois fluxos referenciando um ao outro recursam até o processo morrer. Cada nível é um run completo, com suas linhas, sua árvore de log e seu gasto de tokens.'),
       ('The second entry into a flow already on the chain is refused with a message naming the chain, before anything is spent.',
        'A segunda entrada num fluxo que já está na cadeia é recusada com uma mensagem que nomeia a cadeia, antes de qualquer gasto.'))},
{'n':'2','title':('Pre-flight validation, before anything is spent','Validação prévia, antes de qualquer gasto'),
 'loc':('flux.service.ts — v2 phase 2', 'flux.service.ts — fase 2 da v2'),
 'purpose':('Where the answer is knowable before the run, give it before the run — and turn a bill into an error message.',
            'Onde a resposta é conhecível antes do run, dê-a antes do run — e transforme uma cobrança numa mensagem de erro.'),
 'body':('<p>The chain guard is a <strong>run-time</strong> refusal: it fires after the run has started. Some of the same answers are provable earlier, in the gate the v2 already runs between building the DAG and starting to spend.</p>'
         '<p>What is provable statically:</p>',
         '<p>A guarda de cadeia é uma recusa em <strong>tempo de execução</strong>: ela dispara depois que o run começou. Algumas dessas respostas são prováveis antes, no gate que a v2 já roda entre montar o DAG e começar a gastar.</p>'
         '<p>O que é provável estaticamente:</p>'),
 'list':[('A cycle <strong>inside</strong> the flow&#x27;s own graph — the v2 already checks this','Um ciclo <strong>dentro</strong> do próprio grafo do fluxo — a v2 já checa isso'),
         ('A cycle in the <strong>flow-call graph</strong> reachable from this flow: <code>A → B → C → A</code>, walking <code>fluxBox</code>/<code>libraryNode</code> targets transitively. This is new, and it is the combinatorial case — B must not be reachable from C, and C must not reach A or B, all the way down','Um ciclo no <strong>grafo de chamadas entre fluxos</strong> alcançável a partir deste: <code>A → B → C → A</code>, percorrendo alvos de <code>fluxBox</code>/<code>libraryNode</code> transitivamente. Isto é novo, e é o caso combinatório — B não pode ser alcançável a partir de C, e C não pode alcançar A nem B, e assim por diante'),
         ('A chain that would exceed the depth ceiling before it runs a single node','Uma cadeia que estouraria o teto de profundidade antes de rodar um único node')],
 'body2':('<p><strong>What it cannot prove is termination in general</strong> — the loop conditions read data that does not exist until the run happens. That is why the static check <strong>does not replace</strong> the runtime budget in <code>S4</code>; the two answer different questions.</p>',
          '<p><strong>O que ela não consegue provar é término em geral</strong> — as condições de loop leem dados que não existem até o run acontecer. Por isso a checagem estática <strong>não substitui</strong> o orçamento em tempo de execução da <code>S4</code>; as duas respondem perguntas diferentes.</p>'),
 'callouts':[('mig',('Scope — what this task does not do','Escopo — o que esta task não faz'),
   ('<p>It does not change what a sub-flow does when it runs legitimately. <strong>This task only refuses.</strong></p>',
    '<p>Ela não muda o que um sub-fluxo faz quando roda legitimamente. <strong>Esta task apenas recusa.</strong></p>'))]},
]

VERIF=[
 (True,('Negative control','Controle negativo'),
  ('Build two flows referencing each other, run one, and <strong>watch the recursion happen on <code>main</code></strong> — the process degrades and the run never returns. Then add the guard and confirm it refuses on the second entry with the cycle message. Seeing the failure first is what makes the ceiling defensible.',
   'Monte dois fluxos referenciando um ao outro, rode um, e <strong>veja a recursão acontecer na <code>main</code></strong> — o processo degrada e o run nunca retorna. Depois adicione a guarda e confirme que ela recusa na segunda entrada com a mensagem de ciclo. Ver a falha primeiro é o que torna o teto defensável.')),
 (True,('Measure before refusing','Medir antes de recusar'),
  ('<strong>PLAN §3.3.2, and not optional here.</strong> Walk the stored flows: for every flow containing a <code>fluxBox</code> or <code>libraryNode</code>, compute the real maximum nesting depth and detect existing cycles. Classify each as <em>would still work</em> or <em>would now be refused</em>, and <strong>drive the second count to zero</strong> — by raising the ceiling or by contacting the owners.',
   '<strong>PLAN §3.3.2, e aqui não é opcional.</strong> Percorra os fluxos guardados: para todo fluxo com um <code>fluxBox</code> ou <code>libraryNode</code>, calcule a profundidade máxima real de aninhamento e detecte ciclos existentes. Classifique cada um como <em>continuaria funcionando</em> ou <em>passaria a ser recusado</em>, e <strong>zere a segunda contagem</strong> — elevando o teto ou contatando os donos.')),
 (False,('Report existing cycles separately','Reportar ciclos existentes à parte'),
  ('Those flows are <strong>already broken</strong>. The guard makes the breakage legible instead of fatal — but their owners should be told, not silently refused.',
   'Esses fluxos <strong>já estão quebrados</strong>. A guarda torna a quebra legível em vez de fatal — mas os donos devem ser avisados, não recusados em silêncio.')),
 (False,('The guard survives the boundary','A guarda sobrevive à fronteira'),
  ('The chain, the visited set and the depth counter must live in the <strong>run context that already crosses into child workflows</strong>, not in a closure. Confirm they are still there after B6 moves sub-flows to Temporal.',
   'A cadeia, o conjunto de visitados e o contador de profundidade precisam viver no <strong>contexto de run que já atravessa para child workflows</strong>, não num closure. Confirme que continuam lá depois de a B6 mover sub-fluxos para o Temporal.')),
]
DONE=('Cycles are refused with a clear message, depth is capped by an <strong>env-configurable</strong> ceiling, the <strong>stored flows were measured and no working flow is refused</strong>, and the guard lives in state that survives the move to child workflows.',
      'Ciclos são recusados com mensagem clara, a profundidade é limitada por um teto <strong>configurável por ambiente</strong>, os <strong>fluxos guardados foram medidos e nenhum fluxo que funciona é recusado</strong>, e a guarda vive num estado que sobrevive à mudança para child workflows.')
FILES=[('back/src/app-api/flux/flux.service.ts:5400, 5611–5622, 5717, 5732, 5815',False),
       ('the run context threaded through apiV2',True),
       ('new env var + env-vars-sync',True)]

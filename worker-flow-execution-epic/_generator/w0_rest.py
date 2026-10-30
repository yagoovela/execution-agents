# -*- coding: utf-8 -*-
S4=dict(
 TITLE=('Execution budget: per node, per run, per chain','Orçamento de execução: por node, por run, por cadeia'),
 GOAL=('Make it <b>impossible for a run to execute without bound</b>, whatever shape the loop takes.',
       'Tornar <b>impossível um run executar sem limite</b>, qualquer que seja a forma do laço.'),
 GLANCE=[
  ('crit',('Severity','Severidade'),('High','Alta'),
   ('An always-true condition on a node whose behaviour is not <code>continue</code> loops with no ceiling. Review §1.2.',
    'Uma condição sempre verdadeira num node cujo comportamento não é <code>continue</code> roda sem teto. Review §1.2.')),
  ('dep',('Depends on','Depende de'),('Nothing','Nada'),
   ('Best done with S1 — same class of guard, same test harness, and the chain total is shared.',
    'Melhor feita com a S1 — mesma classe de guarda, mesmo aparato de teste, e o total da cadeia é compartilhado.')),
  ('wave',('Wave','Onda'),('Wave 0','Onda 0'),
   ('Also bounds Temporal history growth — the other half of what B4&#x27;s <code>continueAsNew</code> is for.',
    'Também limita o crescimento do histórico do Temporal — a outra metade do que o <code>continueAsNew</code> da B4 faz.')),
  ('ship',('Shape','Formato'),('Three limits','Três limites'),
   ('X per node, Y per run, and a chain total. None of them subsumes the others.',
    'X por node, Y por run, e um total de cadeia. Nenhum deles engloba os outros.')),
 ],
 LEDE=('<p><code>evaluateLoopCondition</code> (<code>folw/helpers/helpers.ts</code>) applies the limit <strong>on one branch only</strong>. On the other branch the limit is computed, reported to the UI through <code>loopStatus</code> and the <code>condition-loop-status</code> socket event — and then <strong>not applied</strong>.</p>'
       '<p>Worse, on the capped branch the limit itself is <code>node.data.loopCount</code> — <strong>user data</strong>. A system-level maximum should not be reachable from node configuration.</p>',
       '<p>O <code>evaluateLoopCondition</code> (<code>folw/helpers/helpers.ts</code>) aplica o limite <strong>em apenas um ramo</strong>. No outro ramo o limite é calculado, reportado à UI via <code>loopStatus</code> e pelo evento de socket <code>condition-loop-status</code> — e então <strong>não é aplicado</strong>.</p>'
       '<p>Pior: no ramo limitado, o limite em si é <code>node.data.loopCount</code> — <strong>dado do usuário</strong>. Um máximo de sistema não deveria ser alcançável pela configuração de um node.</p>'),
 TABLE=dict(head=[('Limit','Limite'),('Catches','Pega'),('Misses','Não pega'),('Why it cannot be dropped','Por que não pode sair')],
  rows=[
   [{'t':('X — iterations per node','X — iterações por node')},('The runaway loop on one node','O laço desgovernado num node'),
    ('A loop that walks across many nodes','Um laço que caminha por vários nodes'),
    ('The common case, and the cheapest to catch','O caso comum, e o mais barato de pegar')],
   [{'t':('Y — node executions per run','Y — execuções de node por run')},('Every shape, including ones nobody predicted','Toda forma, inclusive as que ninguém previu'),
    ('Nothing — but only within one run','Nada — mas só dentro de um run'),
    ('<strong>The only real guarantee.</strong> Termination is not decidable by looking at the graph','<strong>A única garantia real.</strong> Término não é decidível olhando o grafo')],
   [{'t':('Chain total','Total da cadeia')},('Recursion that resets Y by starting a new run','Recursão que zera Y iniciando um run novo'),
    ('—','—'),
    ('A sub-flow is a new run (<code>S1</code>), so nesting would buy a fresh Y','Um sub-fluxo é um run novo (<code>S1</code>), então aninhar compraria um Y novo')],
  ]),
 PARTS=[
  {'n':'1','title':('Why the static check is not enough','Por que a checagem estática não basta'),
   'loc':'flux.service.ts · inline arrayNode branch',
   'purpose':('Three defences, in this order — and the third is the only one that answers the question that matters at 3 a.m.',
              'Três defesas, nesta ordem — e a terceira é a única que responde a pergunta que importa às 3 da manhã.'),
   'body':('<p><strong>1. Before the run — graph validation.</strong> Refuse what can be proven wrong without spending anything: cycles inside the graph, and a flow already on the call chain (<code>S1</code>).</p>'
           '<p><strong>2. During the run — X, per node.</strong> Stops the common case: one node looping on a condition that never turns false.</p>'
           '<p><strong>3. During the run — Y, per run, and the chain total.</strong> The backstop.</p>'
           '<p><strong>The third is not redundant, it is the only guarantee.</strong> Whether a flow terminates is not decidable by looking at it — the loop condition reads data that does not exist until the run happens. A static check can prove <em>some</em> flows wrong; it can never prove the rest right.</p>',
           '<p><strong>1. Antes do run — validação de grafo.</strong> Recusar o que se prova errado sem gastar nada: ciclos dentro do grafo, e um fluxo já na cadeia de chamadas (<code>S1</code>).</p>'
           '<p><strong>2. Durante o run — X, por node.</strong> Detém o caso comum: um node em laço sobre uma condição que nunca fica falsa.</p>'
           '<p><strong>3. Durante o run — Y, por run, e o total da cadeia.</strong> A última barreira.</p>'
           '<p><strong>A terceira não é redundante, é a única garantia.</strong> Se um fluxo termina não é decidível olhando para ele — a condição do laço lê dados que não existem até o run acontecer. Uma checagem estática prova <em>alguns</em> fluxos errados; nunca prova os demais certos.</p>'),
   'ba':(('A node whose <code>loopBehavior</code> is not <code>continue</code> loops forever with an always-true condition, and the limit that was computed is discarded.',
          'Um node cujo <code>loopBehavior</code> não é <code>continue</code> roda para sempre com uma condição sempre verdadeira, e o limite que foi calculado é descartado.'),
         ('X applies on <strong>both</strong> branches, independent of <code>loopBehavior</code> and of <code>loopCount</code>. The node&#x27;s own limit still applies where it is lower — this is a ceiling, not a replacement.',
          'X se aplica nos <strong>dois</strong> ramos, independente de <code>loopBehavior</code> e de <code>loopCount</code>. O limite do próprio node continua valendo onde for menor — isto é um teto, não um substituto.')),
   'callouts':[('mig',('Say which ceiling stopped it','Diga qual teto parou'),
     ('<p><code>loopStatus.reason</code> already carries a human-readable reason — <code>Loop limit exceeded (n/m)</code>. The new case <strong>needs its own wording</strong>, or a user will read “limit exceeded” and go looking for a limit they never set.</p>'
      '<p>X also applies to <code>arrayNode</code>, which iterates a list rather than a condition. A <code>processorArray</code> of a hundred thousand items is the same runaway with a different shape.</p>',
      '<p>O <code>loopStatus.reason</code> já carrega uma razão legível — <code>Loop limit exceeded (n/m)</code>. O caso novo <strong>precisa de texto próprio</strong>, senão o usuário lê “limite excedido” e vai procurar um limite que ele nunca definiu.</p>'
      '<p>X vale também para o <code>arrayNode</code>, que itera uma lista em vez de uma condição. Um <code>processorArray</code> de cem mil itens é o mesmo descontrole com outra forma.</p>'))]},
  {'n':'2','title':('Y terminates the run, it does not merely stop scheduling','Y termina o run, não apenas para de agendar'),
   'loc':'flux/scheduler.ts',
   'purpose':('A run that ends ambiguously is worse than one that ends refused, because nobody can tell it from a hang.',
              'Um run que termina de forma ambígua é pior que um recusado, porque ninguém consegue distingui-lo de um travamento.'),
   'body':('<p>Y counts <strong>executions, not distinct nodes</strong>: a node that runs forty times spends forty. When the budget is exhausted the run <strong>terminates deterministically</strong>, with a terminal state naming the budget.</p>'
           '<p>The chain total resolves the chain root and accounts against it — <strong>the same mechanism <code>S3</code> needs for cost</strong>. One counter carrying two limits, resolved at the same place, rather than two independent accountants that can disagree.</p>',
           '<p>Y conta <strong>execuções, não nodes distintos</strong>: um node que roda quarenta vezes gasta quarenta. Quando o orçamento acaba, o run <strong>termina de forma determinística</strong>, com um estado terminal que nomeia o orçamento.</p>'
           '<p>O total da cadeia resolve a raiz da cadeia e contabiliza contra ela — <strong>o mesmo mecanismo que a <code>S3</code> precisa para custo</strong>. Um contador carregando dois limites, resolvido no mesmo lugar, em vez de dois contadores independentes que podem discordar.</p>'),
   'ba':(('Nothing counts how much a run has executed. A loop across several nodes is invisible to any per-node limit.',
          'Nada conta quanto um run já executou. Um laço que caminha por vários nodes é invisível a qualquer limite por node.'),
         ('One counter bounds the run and the chain. As a side effect it bounds <strong>Temporal history growth</strong>, which is the other half of what <code>B4</code>&#x27;s <code>continueAsNew</code> is for.',
          'Um contador limita o run e a cadeia. Como efeito colateral, limita o <strong>crescimento do histórico do Temporal</strong>, que é a outra metade do que o <code>continueAsNew</code> da <code>B4</code> faz.'))},
 ],
 VERIF=[
  (True,('Negative control — X','Controle negativo — X'),
   ('A condition node with an always-true condition and <code>loopBehavior</code> set to <strong>anything but <code>&#x27;continue&#x27;</code></strong>: watch it loop without bound on <code>main</code>, then confirm the ceiling stops it and the reason names <strong>the system limit rather than the node&#x27;s</strong>.',
    'Um node de condição com condição sempre verdadeira e <code>loopBehavior</code> <strong>diferente de <code>&#x27;continue&#x27;</code></strong>: veja rodar sem limite na <code>main</code>, depois confirme que o teto o para e que a razão nomeia <strong>o limite do sistema, não o do node</strong>.')),
  (True,('Negative control — Y and the chain','Controle negativo — Y e a cadeia'),
   ('Build a flow that loops <strong>across several nodes</strong> rather than on one — the shape X cannot see — and confirm it runs unbounded on <code>main</code>, then confirm Y stops it with a terminal state naming the budget. <strong>Then nest that flow two levels deep</strong> and confirm the chain total stops it, rather than each level getting a fresh Y.',
    'Monte um fluxo que faz laço <strong>por vários nodes</strong> em vez de um só — a forma que X não enxerga — e confirme que roda sem limite na <code>main</code>, depois confirme que Y o para com um estado terminal que nomeia o orçamento. <strong>Depois aninhe esse fluxo dois níveis</strong> e confirme que o total da cadeia o para, em vez de cada nível ganhar um Y novo.')),
  (True,('Measure before refusing','Medir antes de recusar'),
   ('<strong>PLAN §3.3.2.</strong> Find the largest <code>loopCount</code> and the largest <code>processorArray</code> in the stored flows, and the largest number of node executions any real run has produced. Set X and Y above all of them with margin — and <strong>report the distribution, not just the maximum</strong>. A ceiling chosen from one outlier is a ceiling nobody trusts.',
    '<strong>PLAN §3.3.2.</strong> Encontre o maior <code>loopCount</code> e o maior <code>processorArray</code> nos fluxos guardados, e o maior número de execuções de node que algum run real já produziu. Defina X e Y acima de todos com margem — e <strong>reporte a distribuição, não só o máximo</strong>. Um teto escolhido a partir de um outlier é um teto em que ninguém confia.')),
  (False,('The two reasons stay distinguishable','As duas razões continuam distinguíveis'),
   ('Confirm the UI still shows the <strong>node&#x27;s own limit</strong> when that is what stopped the loop. The two reasons must not be confused, or the author debugs the wrong number.',
    'Confirme que a UI ainda mostra o <strong>limite do próprio node</strong> quando foi ele que parou o laço. As duas razões não podem se confundir, ou o autor depura o número errado.')),
 ],
 DONE=('No node configuration and no graph shape can produce an unbounded run: <strong>X bounds one node, Y bounds the run, and the chain total bounds nesting</strong>. Every ceiling sits <strong>above the largest real value in the stored data</strong>. A run that hits any of them ends in a terminal state that names which one, and the three reasons are distinguishable from each other and from the node&#x27;s own limit.',
       'Nenhuma configuração de node e nenhuma forma de grafo pode produzir um run ilimitado: <strong>X limita um node, Y limita o run, e o total da cadeia limita o aninhamento</strong>. Todo teto fica <strong>acima do maior valor real no dado guardado</strong>. Um run que bate em qualquer um termina num estado terminal que nomeia qual, e as três razões são distinguíveis entre si e do limite do próprio node.'),
 FILES=[('back/src/app-api/folw/helpers/helpers.ts (evaluateLoopCondition)',False),
        ('back/src/app-api/flux/flux.service.ts (conditionNode(); inline arrayNode branch)',False),
        ('back/src/app-api/flux/scheduler.ts',False),
        ('chain-root accounting shared with TASK-S3',True),
        ('new env vars + env-vars-sync',True)],
)

S4_DEC={
 'k':'decision','id':'S4-a','plan':'D15','status':'set','open':True, 'outcome':('Measured, then set on 2026-09-03 and shipped 2026-09-10: X = 150 per node, 12,000 array items, Y = 50,000 per run and a chain total of 200,000, behind the <code>execution_budget</code> flag.', 'Medido e definido em 03/09/2026, entregue em 10/09/2026: X = 150 por node, 12.000 itens de array, Y = 50.000 por run e total da cadeia de 200.000, atrás da flag <code>execution_budget</code>.'),
 'q':('What are X, Y and the chain total?','Quanto valem X, Y e o total da cadeia?'),
 'intro':('<strong>The one genuinely open number in this epic.</strong> The spec is deliberate about this: the three ceilings must come from <strong>measurement against stored runs</strong>, not from taste. '
          'The options below are about <em>how</em> to choose them, not about which numbers to type.',
          '<strong>O único número genuinamente em aberto deste épico.</strong> A spec é deliberada quanto a isso: os três tetos precisam vir de <strong>medição contra runs guardados</strong>, não de gosto. '
          'As opções abaixo são sobre <em>como</em> escolhê-los, não sobre quais números digitar.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Measure, then set above the observed maximum','Medir, e definir acima do máximo observado'),
   'tag':('recommended','recomendada'),
   'how':('Query the stored flows and runs for the largest <code>loopCount</code>, the largest <code>processorArray</code>, and the largest node-execution count any real run produced. Set each ceiling above that, with margin, and report the <strong>distribution</strong>.',
          'Consultar fluxos e runs guardados pelo maior <code>loopCount</code>, maior <code>processorArray</code>, e maior contagem de execuções de node que algum run real produziu. Definir cada teto acima disso, com margem, e reportar a <strong>distribuição</strong>.'),
   'pros':[('Zero false refusals by construction — the ceiling is above everything that ever really ran','Zero falsas recusas por construção — o teto fica acima de tudo que realmente rodou'),
           ('The distribution shows whether the maximum is a real workload or one outlier','A distribuição mostra se o máximo é uma carga real ou um único outlier'),
           ('Defensible in a review: the number has a provenance','Defensável numa revisão: o número tem procedência')],
   'cons':[('Needs the query to run against real stored data before the code can ship','Exige rodar a consulta contra dado real guardado antes de o código poder subir'),
           ('A future workload larger than anything seen so far will be refused — env vars mitigate','Uma carga futura maior que tudo já visto será recusada — env vars mitigam')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('',('Ours: <b>one measurement pass</b>','Nosso: <b>uma rodada de medição</b>'))]},
  {'ltr':'B','name':('Pick round numbers now, tune later','Escolher números redondos agora, ajustar depois'),
   'how':('Ship generous defaults — say 1000 iterations per node, 10000 executions per run — and adjust when something is refused.',
          'Entregar padrões generosos — digamos 1000 iterações por node, 10000 execuções por run — e ajustar quando algo for recusado.'),
   'pros':[('Ships immediately, no measurement gate','Sobe imediatamente, sem gate de medição'),
           ('Generous enough that most workloads never notice','Generoso o bastante para a maioria das cargas nunca notar')],
   'cons':[('<strong>Violates PLAN §3.3.2</strong> — a rule that refuses must be checked against real data first','<strong>Viola o PLAN §3.3.2</strong> — uma regra que recusa precisa ser checada contra dado real antes'),
           ('“Adjust when something is refused” means the first signal is a customer incident','“Ajustar quando algo for recusado” significa que o primeiro sinal é um incidente de cliente'),
           ('A number with no provenance gets raised by whoever is on call, and never lowered','Um número sem procedência é elevado por quem estiver de plantão, e nunca baixado')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('hi',('Ours: <b>incident-driven tuning</b>','Nosso: <b>ajuste guiado por incidente</b>'))]},
  {'ltr':'C','name':('Report-only first, enforce after a cycle','Somente-relatório primeiro, impor depois de um ciclo'),
   'tag':('pairs with A','combina com A'),
   'how':('Ship the counters recording what <em>would</em> have been refused, without refusing. Read the report after a full cycle, then turn enforcement on.',
          'Entregar os contadores registrando o que <em>teria</em> sido recusado, sem recusar. Ler o relatório depois de um ciclo completo, e então ligar a imposição.'),
   'pros':[('Catches workloads the historical query cannot see — anything that failed, retried or was never stored','Pega cargas que a consulta histórica não enxerga — o que falhou, tentou de novo ou nunca foi guardado'),
           ('The team sees the real distribution in production, not in a query result','O time vê a distribuição real em produção, não num resultado de consulta')],
   'cons':[('Delays the guard by a full cycle, while the unbounded case stays live','Atrasa a guarda por um ciclo inteiro, com o caso ilimitado ainda vivo'),
           ('Requires the counters to be built before they are useful','Exige que os contadores existam antes de serem úteis')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('',('Ours: <b>a reporting mode</b>','Nosso: <b>um modo de relatório</b>'))]},
 ],
 'rec':('<p><strong>A to pick the numbers, C to confirm them.</strong> The historical query gives a defensible starting value; report-only mode catches the workloads that query cannot see. Then enforce.</p>'
        '<p>Whichever numbers come out, make all three <strong>env vars</strong>. A ceiling that needs a deploy to raise will be raised by disabling the check.</p>',
        '<p><strong>A para escolher os números, C para confirmá-los.</strong> A consulta histórica dá um valor inicial defensável; o modo somente-relatório pega as cargas que a consulta não enxerga. Depois imponha.</p>'
        '<p>Quaisquer que sejam os números, faça os três serem <strong>env vars</strong>. Um teto que precisa de deploy para ser elevado vai ser elevado desligando a checagem.</p>'),
 'who':[('Engineering, from the measurement','Engenharia, a partir da medição')],
}

S5=dict(
 TITLE=('Authorise the claim check, do not just guard it','Autorizar o claim check, não apenas protegê-lo'),
 GOAL=('A claim-check key can only be redeemed <b>by the run it belongs to</b>.',
       'Uma chave de claim check só pode ser resgatada <b>pelo run a que ela pertence</b>.'),
 GLANCE=[
  ('crit',('Severity','Severidade'),('High','Alta'),
   ('Any holder of the internal API key can read <strong>any</strong> node output of <strong>any</strong> customer, by key. Review §3.1.',
    'Qualquer portador da chave interna de API pode ler <strong>qualquer</strong> saída de node de <strong>qualquer</strong> cliente, por chave. Review §3.1.')),
  ('dep',('Depends on','Depende de'),('Nothing','Nada'),
   ('Standalone, and deliberately kept that way: chain propagation of the run token is a Done-when line of S1 and B6, not work here.',
    'Independente, e mantida assim de propósito: propagar o token de run pela cadeia é linha de Done-when da S1 e da B6, não trabalho daqui.')),
  ('wave',('Wave','Onda'),('Wave 0','Onda 0'),
   ('The blast radius grows with the fleet: this epic puts the shared secret on every worker replica.',
    'O raio de impacto cresce com a frota: este épico coloca o segredo compartilhado em toda réplica de worker.')),
  ('ship',('Watch out','Atenção'),('The cheap fix is a placebo','A correção barata é placebo'),
   ('The key contains execId and nodeId, so refusing when the caller&#x27;s declaration disagrees with the key adds no authority at all. D28 settled that the endpoints stay.',
    'A chave contém execId e nodeId, então recusar quando a declaração do chamador discorda da chave não acrescenta autoridade nenhuma. A D28 decidiu que os endpoints ficam.')),
 ],
 LEDE=('<p><code>/worker/get-payload</code> validates <strong>a prefix and nothing else</strong> (<code>worker.controller.ts:99</code>). There is no check that the key belongs to the caller&#x27;s run, tenant, or anything else.</p>'
       '<p>The route sits behind <code>InternalApiGuard</code>, which is the right boundary and should stay. But it is a <strong>single shared secret</strong>, and this epic puts that secret on every worker replica — “we trust everything inside the perimeter” gets weaker with every host added to the perimeter.</p>'
       '<p><strong>The obvious fix does not fix it.</strong> The key is <code>node-exec/{execId}/{nodeId}-{field}.json</code>, so both values the caller would “declare” are already inside the key it presents. A holder of the shared secret reads them out of the victim&#x27;s key and declares them back. This task therefore separates <strong>validating the key</strong> from <strong>authorising the caller</strong>, because only the second one is authorisation.</p>',
       '<p>O <code>/worker/get-payload</code> valida <strong>um prefixo e nada mais</strong> (<code>worker.controller.ts:99</code>). Não há checagem de que a chave pertence ao run do chamador, ao tenant, ou a coisa alguma.</p>'
       '<p>A rota fica atrás do <code>InternalApiGuard</code>, que é a fronteira certa e deve permanecer. Mas é um <strong>segredo único compartilhado</strong>, e este épico coloca esse segredo em toda réplica de worker — “confiamos em tudo dentro do perímetro” enfraquece a cada host somado ao perímetro.</p>'
       '<p><strong>A correção óbvia não corrige.</strong> A chave é <code>node-exec/{execId}/{nodeId}-{field}.json</code>, então os dois valores que o chamador “declararia” já estão dentro da chave que ele apresenta. Quem tem o segredo compartilhado lê os dois da chave da vítima e os declara de volta. Por isso esta task separa <strong>validar a chave</strong> de <strong>autorizar o chamador</strong>, porque só o segundo é autorização.</p>'),
 PARTS=[
  {'n':'1','title':('Derive from the key, never from the claim','Derivar da chave, nunca da declaração'),
   'loc':'worker.controller.ts · claim-check.ts',
   'purpose':('The endpoint recovers execId and nodeId from the key itself and binds them to a stored row, so the decision never rests on anything the caller asserts.',
              'O endpoint recupera execId e nodeId da própria chave e os amarra a uma linha armazenada, então a decisão nunca depende de nada que o chamador afirme.'),
   'body':('<p><code>parseClaimCheckKey</code> lands next to <code>claimCheckKey</code> in <code>claim-check.ts</code>, so building and parsing a key share one home. <code>/worker/get-payload</code> then requires a <code>node_executions</code> row for the derived pair whose <code>__claimRef</code> envelope <strong>is</strong> the requested key. A key nobody stored is refused.</p>'
           '<p><code>/worker/store-payload</code> gets the inverse bind: the run row for that pair must already be open before a payload may be written into its key. Without that, “a caller cannot write into another run&#x27;s key” is unreachable, because the key is derived from what the caller supplies.</p>'
           '<p>What the caller declares is kept — in the <strong>refusal log</strong>, so a refusal reads as “declared X, key said Y”. That is what separates a bug from an attempt.</p>',
           '<p>O <code>parseClaimCheckKey</code> nasce ao lado do <code>claimCheckKey</code> em <code>claim-check.ts</code>, então montar e desmontar uma chave dividem a mesma casa. O <code>/worker/get-payload</code> passa a exigir uma linha de <code>node_executions</code> para o par derivado cujo envelope <code>__claimRef</code> <strong>seja</strong> a chave pedida. Uma chave que ninguém guardou é recusada.</p>'
           '<p>O <code>/worker/store-payload</code> recebe o vínculo inverso: a linha do run daquele par precisa já estar aberta antes de um payload poder ser escrito na chave dela. Sem isso, “um chamador não consegue escrever na chave de outro run” é inalcançável, porque a chave é derivada do que o chamador fornece.</p>'
           '<p>O que o chamador declara é guardado — no <strong>log de recusa</strong>, para que uma recusa se leia como “declarou X, a chave dizia Y”. É isso que separa um bug de uma tentativa.</p>'),
   'ba':(('A prefix check. Any valid internal key redeems any customer&#x27;s node output, and can overwrite any customer&#x27;s payload.',
          'Uma checagem de prefixo. Qualquer chave interna válida resgata a saída de node de qualquer cliente, e pode sobrescrever o payload de qualquer cliente.'),
         ('The key must name a run that really stored it, and a write must land on a run that is really open. Forged, guessed, enumerated, truncated and path-traversing keys are all refused, and every refusal is logged with context.',
          'A chave precisa nomear um run que realmente a guardou, e uma escrita precisa cair num run que realmente está aberto. Chaves forjadas, adivinhadas, enumeradas, truncadas e com travessia de caminho são todas recusadas, e cada recusa é logada com contexto.')),
   'callouts':[('mig',('Validation is not yet authorisation','Validação ainda não é autorização'),
     ('<p>This bind kills every key that was never stored. It does <strong>not</strong> stop a holder of the shared secret who already knows a real key — that needs part 2.</p>',
      '<p>Este vínculo mata toda chave que nunca foi armazenada. Ele <strong>não</strong> impede quem tem o segredo compartilhado e já conhece uma chave real — isso é a parte 2.</p>'))]},
  {'n':'2','title':('A run token the caller cannot forge','Um token de run que o chamador não pode forjar'),
   'loc':'activities.types.ts · run-token.ts · claim-check-authz.service.ts',
   'purpose':('The back mints a run-scoped token at dispatch; the worker carries it and presents it. This is the half that is actually authorisation.',
              'O back emite um token com escopo de run no dispatch; o worker o carrega e o apresenta. Esta é a metade que de fato é autorização.'),
   'body':('<p><code>ExecuteNodeActivityProps</code> gains a <code>runToken</code>, issued by the back when it dispatches the activity and checked on both endpoints. Every node of the run inherits it, because every activity of that run is dispatched with it.</p>'
           '<p><strong>No chain propagation, on purpose.</strong> Checked on <code>worker@origin/main</code>: the worker executes no sub-flow at all — no <code>parentRunId</code>, no <code>startChild</code>, and no <code>fluxBox</code>, <code>libraryNode</code>, <code>flowCaller</code> or <code>arrayNode</code> module. Sub-flows still run in the back&#x27;s legacy engine, so there is nothing to propagate through. Carrying the token down the chain becomes a <strong>Done-when line of S1</strong> (which owns the <code>parentRunId</code> chain under D13) and of <strong>B6</strong> (the child workflow, D17). That is what keeps this task standalone.</p>',
           '<p>O <code>ExecuteNodeActivityProps</code> ganha um <code>runToken</code>, emitido pelo back quando ele despacha a activity e verificado nos dois endpoints. Todo node do run o herda, porque toda activity daquele run é despachada com ele.</p>'
           '<p><strong>Sem propagação pela cadeia, de propósito.</strong> Verificado em <code>worker@origin/main</code>: o worker não executa subfluxo nenhum — nenhum <code>parentRunId</code>, nenhum <code>startChild</code>, e nenhum módulo <code>fluxBox</code>, <code>libraryNode</code>, <code>flowCaller</code> ou <code>arrayNode</code>. Subfluxos ainda rodam no engine legacy do back, então não há por onde propagar. Levar o token pela cadeia vira <strong>linha de Done-when da S1</strong> (que é dona da cadeia de <code>parentRunId</code> pela D13) e da <strong>B6</strong> (o child workflow, D17). É isso que mantém esta task independente.</p>'),
   'ba':(('Anything inside the perimeter is trusted, and the perimeter is one secret on every replica.',
          'Tudo dentro do perímetro é confiável, e o perímetro é um segredo em cada réplica.'),
         ('The caller proves which run it is acting for with something it could not have read off the key.',
          'O chamador prova para qual run está agindo com algo que não poderia ter lido da chave.')),
   'callouts':[('mig',('Out of scope','Fora de escopo'),
     ('<p>Replacing <code>InternalApiGuard</code> or issuing per-worker credentials. That is a larger identity change; <strong>this task closes the authorisation gap inside the existing boundary</strong>.</p>',
      '<p>Substituir o <code>InternalApiGuard</code> ou emitir credenciais por worker. Isso é uma mudança de identidade maior; <strong>esta task fecha a lacuna de autorização dentro da fronteira existente</strong>.</p>'))]},
  {'n':'3','title':('Node ids need a contract, not luck','Node ids precisam de contrato, não de sorte'),
   'loc':'claim-check.ts · nodeId.ts · mcp-write.service.ts',
   'purpose':('Any rule that recovers a node id from a key refuses ids the key could not represent. Close that by contract, so a false refusal is impossible by construction.',
              'Qualquer regra que recupere um node id de uma chave recusa ids que a chave não conseguiria representar. Fechar isso por contrato, para que um falso-refuso seja impossível por construção.'),
   'body':('<p><code>claimCheckKey</code> sanitises the id with <code>replace(/[^a-zA-Z0-9_.-]/g, &#x27;_&#x27;)</code>, which is lossy. Introduce <code>NODE_ID_PATTERN = /^(?!\\.+$)[A-Za-z0-9_.-]{1,128}$/</code> — deliberately the same class the key preserves, so <strong>sanitising a valid id is the identity function</strong>.</p>'
           '<p>Six producers exist and <strong>none</strong> of them enforces anything. The front generator is safe by accident, in three separate generations. The hole is <strong>MCP <code>add_node</code></strong>: <code>AddNodeDto.node</code> is <code>@IsObject() Record&lt;string, unknown&gt;</code> and the service only checks for id collision, so a client id is persisted verbatim. The only id rule anywhere is <code>assertGlobalStarterIdConvention</code>, which merely requires a substring on <code>globalStarter</code>.</p>'
           '<p>So: <code>getNodeId</code> becomes the single front producer with a pattern test, copy/paste goes through a <code>deriveCopyId</code> that also stops the <code>-copy-copy</code> chain, an <code>assertNodeIdRedeemable</code> in <code>mcp-write.service.ts</code> closes the MCP entry for new writes (the DTO&#x27;s <code>node</code> is an untyped <code>Record</code>, so class-validator has nothing to hang a rule on), and comparison stays <strong>sanitised against sanitised</strong> so legacy ids outside the pattern still resolve.</p>'
           '<p>One hazard to remember: several places pass the composite <code>nodeId$handle</code> (<code>fluxBox_1$out</code>). <code>$</code> is sanitised too, so a composite arriving where an id is expected degrades silently.</p>',
           '<p>O <code>claimCheckKey</code> sanitiza o id com <code>replace(/[^a-zA-Z0-9_.-]/g, &#x27;_&#x27;)</code>, o que é lossy. Introduzir <code>NODE_ID_PATTERN = /^(?!\\.+$)[A-Za-z0-9_.-]{1,128}$/</code> — de propósito a mesma classe que a chave preserva, para que <strong>sanitizar um id válido seja a função identidade</strong>.</p>'
           '<p>Existem seis produtores e <strong>nenhum</strong> deles impõe qualquer coisa. O gerador do front é seguro por acidente, em três gerações distintas. O buraco é o <strong>MCP <code>add_node</code></strong>: o <code>AddNodeDto.node</code> é <code>@IsObject() Record&lt;string, unknown&gt;</code> e o service só checa colisão de id, então o id do cliente é persistido literalmente. A única regra de id em qualquer lugar é a <code>assertGlobalStarterIdConvention</code>, que apenas exige um substring no <code>globalStarter</code>.</p>'
           '<p>Portanto: o <code>getNodeId</code> passa a ser o único produtor no front, com teste de pattern; copiar/colar passa por um <code>deriveCopyId</code> que também interrompe a cadeia <code>-copy-copy</code>; um <code>assertNodeIdRedeemable</code> no <code>mcp-write.service.ts</code> fecha a entrada do MCP para escritas novas (o <code>node</code> do DTO é um <code>Record</code> sem tipo, então o class-validator não tem onde pendurar a regra); e a comparação segue <strong>sanitizado contra sanitizado</strong>, para que ids legados fora do pattern continuem resolvendo.</p>'
           '<p>Um perigo a lembrar: vários lugares passam o composto <code>nodeId$handle</code> (<code>fluxBox_1$out</code>). O <code>$</code> também é sanitizado, então um composto chegando onde se espera um id degrada em silêncio.</p>'),
   'ba':(('No id contract anywhere, and an MCP entry point that persists whatever a client sends.',
          'Nenhum contrato de id em lugar algum, e um ponto de entrada MCP que persiste o que o cliente mandar.'),
         ('One pattern, one front producer, a validated MCP entry, and a parser with a round-trip test behind it.',
          'Um pattern, um produtor no front, uma entrada MCP validada, e um parser com teste de round-trip atrás dele.')),
   'callouts':[('ok',('Measured before refusing, per §3.3.2','Medido antes de recusar, conforme §3.3.2'),
     ('<p>Dev and staging, 2026-09-09: <strong>80523 nodes and 3432 executions, zero charset violations, zero false refusals</strong>; all 6 claim envelopes bind correctly and none depends on sanitisation. Prod was not measured — the implementer holds no prod bastion credentials and the requester chose to proceed, so the gap is recorded rather than hidden. The risk this closes is <strong>prospective</strong>: the MCP hole has simply not been exercised yet, which is why closing it now is cheap.</p>',
      '<p>Dev e staging, 2026-09-09: <strong>80523 nodes e 3432 execuções, zero violação de charset, zero falso-refuso</strong>; os 6 envelopes de claim amarram corretamente e nenhum depende da sanitização. Prod não foi medido — quem implementa não tem credencial do bastion de prod e o solicitante optou por seguir, então a lacuna fica registrada em vez de escondida. O risco que isto fecha é <strong>prospectivo</strong>: o buraco do MCP simplesmente ainda não foi exercitado, e é por isso que fechá-lo agora é barato.</p>'))]},
  {'n':'4','title':('Shipped dark, on a switch that already exists','Sobe apagada, num interruptor que já existe'),
   'loc':'feature_flags · FeatureFlagsPage.tsx',
   'purpose':('Reuse the feature-flag table and the admin screen instead of a new env var, so the rule can be measured on real traffic and flipped from inside the product.',
              'Reaproveitar a tabela de feature flags e a tela de admin em vez de uma env var nova, para que a regra seja medida em tráfego real e ligada de dentro do produto.'),
   'body':('<p>Key <code>claim_check_authz_enforce</code>, inserted by migration because <code>setEnabled</code> does not upsert. The flag is a boolean, so it carries two modes: <strong>off</strong> computes the decision, serves the payload anyway and logs “would have refused”; <strong>on</strong> enforces. Off is the measurement window and the default — and it is a window with a deadline, not a resting state, because the gap is open while it is off.</p>'
           '<p><strong>Fail-closed dominates the flag.</strong> <code>isEnabled</code> swallows a read error and returns false, which would read as “log-only” when the database is down. That is harmless, because the bind is itself a query: an uncomputable decision <strong>refuses</strong>, flag or no flag. The flag only decides whether an <em>already computed</em> refusal is acted on. Stated because it is subtle and invites a wrong optimisation later.</p>'
           '<p>The screen&#x27;s list becomes API-driven, which needs care the API does not currently offer: there is <strong>no <code>label</code></strong> column, so deriving one would silently rename the live “Node cancellation” switch; and <code>maintenance_banner</code> is <strong>deliberately absent</strong> from today&#x27;s list, so an API-driven list would expose it as a toggle for the first time. Add <code>label</code> and <code>adminVisible</code>, backfill the banner as not visible, and render <code>label ?? key</code> with <code>description ?? &#x27;&#x27;</code> so a row can never come out blank. <code>isEnabled</code> also gains a few seconds of cache, invalidated on toggle so the screen takes effect at once.</p>',
           '<p>Chave <code>claim_check_authz_enforce</code>, inserida por migration porque o <code>setEnabled</code> não faz upsert. O flag é booleano, então carrega dois modos: <strong>desligado</strong> calcula a decisão, serve o payload de qualquer forma e loga “teria recusado”; <strong>ligado</strong> impõe. Desligado é a janela de medição e o padrão — e é uma janela com prazo, não um estado de repouso, porque a lacuna fica aberta enquanto ele está desligado.</p>'
           '<p><strong>O fail-closed manda mais que o flag.</strong> O <code>isEnabled</code> engole erro de leitura e devolve false, o que se leria como “só log” com o banco fora. Isso é inofensivo, porque o vínculo é ele mesmo uma query: uma decisão incalculável <strong>recusa</strong>, com flag ou sem. O flag só decide se uma recusa <em>já calculada</em> é aplicada. Está escrito porque é sutil e convida a uma otimização errada depois.</p>'
           '<p>A lista da tela passa a vir da API, o que exige um cuidado que a API hoje não oferece: <strong>não existe coluna <code>label</code></strong>, então derivar um renomearia em silêncio o interruptor vivo “Node cancellation”; e o <code>maintenance_banner</code> está <strong>deliberadamente ausente</strong> da lista atual, então uma lista vinda da API o exporia como toggle pela primeira vez. Adicionar <code>label</code> e <code>adminVisible</code>, preencher o banner como não visível, e renderizar <code>label ?? key</code> com <code>description ?? &#x27;&#x27;</code> para que uma linha nunca saia em branco. O <code>isEnabled</code> também ganha alguns segundos de cache, invalidado no toggle para a tela valer na hora.</p>'),
   'ba':(('A rule that refuses would land enabled, measured only against stored rows.',
          'Uma regra que recusa subiria ligada, medida apenas contra linhas armazenadas.'),
         ('It lands dark, states what it would have refused on real traffic, and is flipped from the admin screen in a separate deploy.',
          'Ela sobe apagada, declara o que teria recusado em tráfego real, e é ligada pela tela de admin em um deploy separado.')),
   'callouts':[('ok',('No new env var','Nenhuma env var nova'),
     ('<p>Because it reuses <code>feature_flags</code>, §3.3.5 is not triggered and there is nothing to deploy per environment — the toggle is a row.</p>',
      '<p>Por reaproveitar o <code>feature_flags</code>, a §3.3.5 não é disparada e não há nada para deployar por ambiente — o toggle é uma linha.</p>'))]},
 ],
 VERIF=[
  (True,('Negative control','Controle negativo'),
   ('With a <strong>valid</strong> internal key, request another run&#x27;s payload and confirm it currently <strong>succeeds</strong>. That demonstration is the whole justification for the task. Then confirm it is refused, and that the legitimate path is unaffected. It lives in the integration test, against a real Postgres with two real runs — the bind <em>is</em> a query, so mocking the repository would stub the collaborator the defect lives in, which §3.3.1 forbids. <strong>Done 2026-09-09:</strong> with <code>authorizeRead</code> short-circuited, 5 of the suite&#x27;s 10 go red, including run A reading run B&#x27;s stored payload; restored, all 10 pass.',
    'Com uma chave interna <strong>válida</strong>, peça o payload de outro run e confirme que hoje <strong>funciona</strong>. Essa demonstração é a justificativa inteira da task. Depois confirme que é recusado, e que o caminho legítimo segue intacto. Ele mora no teste de integração, contra um Postgres real com dois runs reais — o vínculo <em>é</em> uma query, então mockar o repositório seria stubar o colaborador onde o defeito mora, o que a §3.3.1 proíbe. <strong>Feito em 2026-09-09:</strong> com o <code>authorizeRead</code> curto-circuitado, 5 dos 10 da suíte ficam vermelhos, inclusive o run A lendo o payload guardado pelo run B; restaurado, os 10 passam.')),
  (True,('A contract test, because the two repos have no shared build graph','Um teste de contrato, porque os dois repos não têm build graph compartilhado'),
   ('<code>ClaimRef</code> is already declared twice and <code>CLAIM_CHECK_THRESHOLD_BYTES</code> read twice, once per repo. This task <strong>widens</strong> that contract, so a mocked unit test on each side would pass while the two sides disagree. One fixture of canonical shapes and key cases, committed identically in both repos with a comment naming the other copy, and a test in each repo asserting its own code produces and accepts exactly that. D1 stays open; this is the cheap version that fails loudly meanwhile. <strong>Done:</strong> three byte-identical copies (back, worker, front), <code>runToken</code> promoted out of <code>plannedFields</code>, and a test in each repo reading its own copy.',
    'O <code>ClaimRef</code> já é declarado duas vezes e o <code>CLAIM_CHECK_THRESHOLD_BYTES</code> lido duas vezes, uma por repo. Esta task <strong>amplia</strong> esse contrato, então um teste unitário mockado em cada lado passaria enquanto os dois lados discordam. Um fixture com as formas canônicas e os casos de chave, committado idêntico nos dois repos com um comentário nomeando a outra cópia, e um teste em cada repo afirmando que o próprio código produz e aceita exatamente aquilo. A D1 segue aberta; esta é a versão barata que falha alto no meio-tempo. <strong>Feito:</strong> três cópias byte a byte idênticas (back, worker, front), o <code>runToken</code> promovido para fora do <code>plannedFields</code>, e um teste em cada repo lendo a própria cópia.')),
  (False,('Every error path, not just the happy one','Todo caminho de erro, não só o feliz'),
   ('A key from another run · a key with no stored row · malformed, truncated, prefix-less and <code>..</code>-bearing keys · a store into a run that is not open · a refusal that carries its context into the log. Plus the parse round trip and sanitise-is-identity. <code>worker.controller.spec.ts</code> already exists and covers <code>storeImage</code> and billing, never the claim-check routes, so the new coverage is a sibling file. <strong>Done:</strong> eleven negative controls run and restored, one per guarantee — the table in the task file names each break and what went red.',
    'Uma chave de outro run · uma chave sem linha armazenada · chaves malformadas, truncadas, sem prefixo e com <code>..</code> · uma escrita num run que não está aberto · uma recusa que leva o contexto dela para o log. Mais o round trip do parse e sanitizar-é-identidade. O <code>worker.controller.spec.ts</code> já existe e cobre o <code>storeImage</code> e o billing, nunca as rotas de claim check, então a cobertura nova é um arquivo irmão. <strong>Feito:</strong> onze controles negativos executados e revertidos, um por garantia — a tabela no arquivo da task nomeia cada quebra e o que ficou vermelho.')),
  (True,('The large-payload path still works','O caminho de payload grande segue funcionando'),
   ('Confirm the worker still resolves its own claim refs — <strong>including the large-payload case</strong>, which is the only path that exercises this at all. It has to be <strong>constructed</strong>, not found: dev shows 6 offloads in 3417 node executions. <strong>Done 2026-09-09:</strong> a 300 KB counterNode through the local stack with back and worker both on this branch and a real S3 bucket. The node completed, the workflow&#x27;s ninth argument was byte-for-byte the token on the row, and it completed again with enforcement <em>on</em>, still with zero refusals. With the flag off, run B presenting run A&#x27;s key got 300000 bytes back and a “would have refused” line — the vulnerability shown rather than described; with it on, the same request is 403.',
    'Confirme que o worker ainda resolve suas próprias claim refs — <strong>inclusive o caso de payload grande</strong>, que é o único caminho que exercita isto de verdade. Ele tem de ser <strong>construído</strong>, não encontrado: o dev mostra 6 offloads em 3417 execuções de node. <strong>Feito em 2026-09-09:</strong> um counterNode de 300 KB pela stack local, com back e worker na mesma branch e um bucket S3 real. O node completou, o nono argumento do workflow era byte a byte o token da linha, e completou de novo com o enforcement <em>ligado</em>, ainda com zero recusas. Com o flag desligado, o run B apresentando a chave do run A recebeu 300000 bytes e uma linha de log dizendo que teria recusado — a vulnerabilidade mostrada em vez de descrita; com ele ligado, a mesma requisição é 403.')),
 ],
 DONE=('A key can only be redeemed <strong>for a run that stored it</strong>, writes are equally bound, the caller presents a run token, refusals are logged, malformed keys fail closed, node ids have a contract with a test behind it, and the existing large-payload path still works.',
       'Uma chave só pode ser resgatada <strong>para um run que a guardou</strong>, escritas ficam igualmente vinculadas, o chamador apresenta um token de run, recusas são logadas, chaves malformadas falham fechado, node ids têm contrato com teste atrás, e o caminho de payload grande existente continua funcionando.'),
 FILES=[('back/src/temporal/worker.controller.ts (/worker/get-payload · /worker/store-payload)',False),
        ('back/src/app-api/flux/claim-check.ts (claimCheckKey · parseClaimCheckKey · NODE_ID_PATTERN)',False),
        ('back/src/app-api/flux/flux.service.ts:565,1561 · back/src/temporal/single-node-legacy/node-execution-store.ts:45,82 (the other key writers)',False),
        ('back/src/app-api/feature-flags/* · back/src/entities/feature_flag.entity.ts (flag · cache · label · adminVisible)',False),
        ('back/src/app-mcp/mcp-write.service.ts (assertNodeIdRedeemable)',False),
        ('worker/src/modules/temporal/activities/activities.types.ts (runToken)',False),
        ('worker/src/modules/nodes/shared/resolve-claim-ref.ts · persist-node-outcome.ts (not persist-node-success.ts, which holds no claim-check code)',False),
        ('front/src/util/nodeId.ts (getNodeId · deriveCopyId · NODE_ID_PATTERN)',False),
        ('front/src/views/AdminDashboard/FeatureFlagsPage.tsx · front/src/service/FeatureFlagsService.ts (API-driven list)',False)],
)

S5_DEC={
 'k':'decision','id':'S5-a','plan':'D28','status':'set','open':True,
 'q':('Do we authorise these two endpoints, or delete them by giving the worker its own S3 credentials?',
      'Autorizamos estes dois endpoints, ou os apagamos dando ao worker credenciais S3 próprias?'),
 'intro':('The spec said this task might be <strong>superseded</strong>, so it had to be checked before starting. It was, on 2026-09-09, and the answer is <strong>A</strong>: the endpoints stay. '
          'The reason is not that B is wrong — it is that B <strong>deletes the only place the check can live</strong>, and handing the worker the back&#x27;s own credential is B by another name: it reduces the number of secrets, not the reach of each one.',
          'A spec dizia que esta task poderia ser <strong>substituída</strong>, então era preciso checar antes de começar. Foi checado, em 2026-09-09, e a resposta é <strong>A</strong>: os endpoints ficam. '
          'O motivo não é que a B esteja errada — é que a B <strong>apaga o único lugar onde a checagem pode morar</strong>, e dar ao worker a credencial do próprio back é a B com outro nome: reduz a quantidade de segredos, não o alcance de cada um.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Authorise now, decide the bigger change later','Autorizar agora, decidir a mudança maior depois'),
   'tag':('chosen','escolhida'),
   'how':('Bind the key to a stored row and the caller to a run token, on both endpoints. The back stays the sole holder of the S3 credential.',
          'Amarrar a chave a uma linha armazenada e o chamador a um token de run, nos dois endpoints. O back segue detentor único da credencial S3.'),
   'pros':[('Closes a live cross-tenant read <strong>now</strong>, without waiting on an architecture decision','Fecha uma leitura entre tenants <strong>agora</strong>, sem esperar uma decisão de arquitetura'),
           ('Keeps the enforcement point, which B removes','Mantém o ponto de imposição, que a B remove'),
           ('If the endpoints do get deleted, the deletion is simpler with the semantics already stated','Se os endpoints forem apagados, apagar fica mais simples com a semântica já declarada')],
   'cons':[('The large-payload hop through the API stays — cheap today, expensive once B5 fans out','O hop de payload grande pela API permanece — barato hoje, caro quando a B5 paralelizar')],
   'cost':[('lo',('Effort: <b>bind + token + tests</b>','Esforço: <b>vínculo + token + testes</b>')),
           ('lo',('Risk: <b>ships dark behind a flag</b>','Risco: <b>sobe apagada atrás de um flag</b>'))]},
  {'ltr':'B','no':True,'name':('Give the worker its own S3 credentials','Dar ao worker credenciais S3 próprias'),
   'tag':('deferred to its own task','adiada para task própria'),
   'how':('The worker reads and writes large payloads directly, so they stop travelling through the API. Both endpoints are deleted.',
          'O worker lê e escreve payloads grandes diretamente, então eles param de trafegar pela API. Os dois endpoints são apagados.'),
   'pros':[('Large payloads stop making a round trip through the backend — less latency, less API load','Payloads grandes param de fazer round trip pelo backend — menos latência, menos carga na API')],
   'cons':[('It <strong>deletes the enforcement point</strong>: with raw bucket access on every replica, “this key belongs to this run” has nowhere left to be checked, and a worker checking itself is not a check','Ela <strong>apaga o ponto de imposição</strong>: com acesso bruto ao bucket em cada réplica, “esta chave pertence a este run” não tem mais onde ser checado, e um worker checando a si mesmo não é checagem'),
           ('Scoping credentials per tenant is the hard part — an over-broad role recreates the same gap at a different layer','Dar escopo por tenant é a parte difícil — um role largo demais recria a mesma lacuna em outra camada'),
           ('The coupling it removes costs almost nothing today: 6 offloads in 3417 node executions on dev','O acoplamento que ela remove custa quase nada hoje: 6 offloads em 3417 execuções de node no dev')],
   'cost':[('hi',('Effort: <b>IAM + deploy per env</b>','Esforço: <b>IAM + deploy por ambiente</b>')),
           ('hi',('Removes: <b>the place the check lives</b>','Remove: <b>o lugar onde a checagem mora</b>'))]},
 ],
 'rec':('<p><strong>Settled 2026-09-09: A.</strong> They were never really alternatives. A closes a live gap and, more importantly, keeps the one surface where authorisation is possible at all. B is a latency and coupling improvement whose security framing is backwards — it does not close the gap, it removes the place the gap could be closed.</p>'
        '<p>Revisit B on its own merits when <code>B5</code>&#x27;s fan-out makes the API hop expensive. By then this task will have paid for the authorisation, and deleting an endpoint whose rule is written down is easier than deleting one whose rule was never stated.</p>',
        '<p><strong>Decidido em 2026-09-09: A.</strong> Nunca foram de fato alternativas. A fecha uma lacuna viva e, mais importante, mantém a única superfície onde autorização é possível. A B é uma melhoria de latência e acoplamento cuja leitura de segurança está invertida — ela não fecha a lacuna, ela remove o lugar onde a lacuna poderia ser fechada.</p>'
        '<p>Retomar a B pelos próprios méritos quando o fan-out da <code>B5</code> tornar o hop pela API caro. Até lá esta task já terá pago a autorização, e apagar um endpoint cuja regra está escrita é mais fácil que apagar um cuja regra nunca foi declarada.</p>'),
 'who':[('Engineering','Engenharia'),('Settled — Infra owns B if it returns','Decidida — Infra decide a B se ela voltar')],
}

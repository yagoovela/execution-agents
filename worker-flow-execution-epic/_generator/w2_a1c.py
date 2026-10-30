# -*- coding: utf-8 -*-
# A1c — Decide `voiceNode`.
# Source: TASK-A1C-VOICENODE-PHANTOM.md, split out of TASK-A1 on 2026-09-22, the day A1 shipped.

TASK = {
 'code':'A1C','vnum':'1',
 'title':('Decide <code>voiceNode</code>','Decidir o <code>voiceNode</code>'),
 'goal':('Decide, <b>on a measurement</b>, whether <code>voiceNode</code> is removed from the legacy single-node surface or kept with a stated reason — and record which. <strong>A1 removed neither, because the measurement that settled the other three phantom types never looked at this one.</strong>',
         'Decidir, <b>com base numa medição</b>, se o <code>voiceNode</code> sai da superfície legada de node único ou fica com um motivo declarado — e registrar qual. <strong>A A1 não removeu nenhum dos dois, porque a medição que resolveu os outros três tipos fantasma nunca olhou para este.</strong>'),
 'glance':[
  ('crit',('Severity','Severidade'),('Low blast radius, high care','Raio de dano baixo, cuidado alto'),
   ('The untidiness is small. The wrong fix is not: this is a live endpoint&#x27;s accept list, so removing a type that some old flow still carries turns a working request into a refusal.',
    'A bagunça é pequena. A correção errada não é: esta é a lista de aceite de um endpoint vivo, então remover um tipo que algum fluxo antigo ainda carrega transforma uma requisição que funciona numa recusa.')),
  ('dep',('Depends on','Depende de'),('A1','A1'),
   ('The registry exists and already carries a <code>voiceNode</code> entry marked <code>phantom</code>; the switch drift spec already pins the two places against each other.',
    'O registro existe e já carrega uma entrada <code>voiceNode</code> marcada como <code>phantom</code>; a spec de drift do switch já amarra os dois lugares um ao outro.')),
  ('wave',('Wave','Onda'),('Wave 2','Onda 2'),
   ('Split out of A1 on the day A1 shipped. It clears a known-unresolved item — not a precondition any other task&#x27;s Done-when line names.',
    'Desmembrada da A1 no dia em que a A1 subiu. Limpa um item sabidamente em aberto — não é precondição que o “pronto quando” de nenhuma outra task cite.')),
  ('ship',('Shape','Formato'),('A measurement, then a decision','Uma medição, depois uma decisão'),
   ('The task is not &quot;delete the arm&quot;. It is &quot;find out, then act on what you found, and write down which&quot;. Keeping the type with a stated reason is a valid outcome.',
    'A task não é “apagar o ramo”. É “descobrir, depois agir sobre o que se descobriu, e anotar qual foi”. Manter o tipo com um motivo declarado é um desfecho válido.')),
 ],
 'lede':(
  '<p><strong>Added 2026-09-22</strong>, split out of TASK-A1 on the day A1 shipped. A1&#x27;s Scope instructed the removal of four phantom types. Three of them — <code>comment</code>, <code>label</code>, <code>group</code> — were measured and <strong>the removal was reverted</strong>: the prefetch executor already skips them, so whitelisting them is precisely what stops a canvas decoration from costing a flow its prefetch eligibility, and removing them would have been a false refusal.</p>'
  '<p><code>voiceNode</code> was <strong>never measured at all</strong>. It could therefore neither be removed nor declared safe, and shipping it either way on the strength of a measurement that did not look at it would have repeated the error A1 had just finished recording. That is the whole reason this task exists as a task instead of a line item.</p>'
  '<p>It is registered in <strong>no</strong> node-type source — not <code>front/src/util/nodeTypes.tsx</code> (46 types), not <code>back/src/app-mcp/node-types/node-type-metadata.ts</code> (50 entries). Nothing in the product can create one today. Yet two live places still trust it.</p>',
  '<p><strong>Adicionada em 22/09/2026</strong>, desmembrada da TASK-A1 no dia em que a A1 subiu. O escopo da A1 mandava remover quatro tipos fantasma. Três deles — <code>comment</code>, <code>label</code>, <code>group</code> — foram medidos e <strong>a remoção foi revertida</strong>: o executor de prefetch já os pula, então colocá-los na whitelist é exatamente o que impede uma decoração de canvas de custar a elegibilidade de prefetch de um fluxo, e removê-los teria sido uma recusa falsa.</p>'
  '<p>O <code>voiceNode</code> <strong>nunca foi medido</strong>. Logo não podia ser removido nem declarado seguro, e subir de qualquer um dos dois jeitos apoiado numa medição que não olhou para ele teria repetido o erro que a A1 tinha acabado de registrar. É essa a razão de esta task existir como task, e não como item de lista.</p>'
  '<p>Ele não está registrado em <strong>nenhuma</strong> fonte de tipos de node — nem em <code>front/src/util/nodeTypes.tsx</code> (46 tipos), nem em <code>back/src/app-mcp/node-types/node-type-metadata.ts</code> (50 entradas). Nada no produto consegue criar um hoje. Ainda assim, dois lugares vivos continuam confiando nele.</p>'),
 'blocks':[
  {'k':'label','n':'1','t':('Where it is still trusted','Onde ele ainda é confiado')},
  {'k':'table',
   'head':[('Place','Lugar'),('What it does','O que faz'),('Consequence','Consequência')],
   'rows':[
    [{'t':'LEGACY_SINGLE_RUN_NODE_TYPES','mono':True},
     ('Derived from the registry&#x27;s <code>legacyEndpoint: &#x27;accept&#x27;</code>','Derivada do <code>legacyEndpoint: &#x27;accept&#x27;</code> do registro'),
     ('<code>/process/single-node-legacy</code> <b>accepts</b> it and runs it inline','O <code>/process/single-node-legacy</code> <b>aceita</b> e roda inline')],
    [{'t':'legacy-node-dispatch.ts','mono':True},
     ('The shared <code>case &#x27;voiceBoxNode&#x27;: case &#x27;voiceNode&#x27;:</code> arm','O ramo compartilhado <code>case &#x27;voiceBoxNode&#x27;: case &#x27;voiceNode&#x27;:</code>'),
     ('A handler exists for it. <code>voiceBoxNode</code> is real and must keep its own','Existe um handler para ele. O <code>voiceBoxNode</code> é real e precisa manter o dele')],
   ]},
  {'k':'prose','t':(
    '<strong>This is not the prefetch whitelist, and that difference is the point.</strong> The prefetch whitelist is permissive — an extra entry costs nothing, which is exactly why removing the other three would have been the harmful move. This is the accept list of a live endpoint, so the asymmetry runs the other way: if no stored node carries the type, the arm is dead surface and removing it shrinks the legacy endpoint (what C2 wants); if some old flow does carry one, removing it turns a request that works today into a refusal.',
    '<strong>Isto não é a whitelist de prefetch, e essa diferença é o ponto.</strong> A whitelist de prefetch é permissiva — uma entrada a mais não custa nada, que é justamente por que remover os outros três seria o movimento danoso. Esta é a lista de aceite de um endpoint vivo, então a assimetria corre para o outro lado: se nenhum node guardado carrega o tipo, o ramo é superfície morta e removê-lo encolhe o endpoint legado (o que a C2 quer); se algum fluxo antigo carrega, removê-lo transforma uma requisição que funciona hoje numa recusa.')},
  {'k':'label','n':'2','t':('What the task does','O que a task faz')},
  {'k':'part','n':'1',
   'title':('Measure, with a control row','Medir, com uma linha de controle'),
   'loc':'production, read-only',
   'purpose':('Two questions, because a type can be stored without ever being called, and called without being stored.',
              'Duas perguntas, porque um tipo pode estar guardado sem nunca ter sido chamado, e chamado sem estar guardado.'),
   'body':('<p>Does any stored node carry <code>type = &#x27;voiceNode&#x27;</code> — in <code>flows_nodes</code>, live canvases <em>and</em> version history, since a legacy request can name a node from an old version? And did any <code>node_executions</code> row with that type ever run, how recently?</p>'
           '<p><strong>Include a control row</strong> for a type known to be present (e.g. <code>commandTextNode</code>), so an empty result set cannot be mistaken for a measured zero. A1&#x27;s D5 measurement did exactly this, and it is what made its zeros worth trusting.</p>',
           '<p>Algum node guardado carrega <code>type = &#x27;voiceNode&#x27;</code> — em <code>flows_nodes</code>, canvases vivos <em>e</em> histórico de versão, já que uma requisição legada pode nomear um node de uma versão antiga? E alguma linha de <code>node_executions</code> com esse tipo chegou a rodar, e há quanto tempo?</p>'
           '<p><strong>Inclua uma linha de controle</strong> para um tipo sabidamente presente (ex.: <code>commandTextNode</code>), para que um resultado vazio não seja confundido com um zero medido. A medição da D5 na A1 fez exatamente isso, e é o que tornou os zeros dela confiáveis.</p>')},
  {'k':'part','n':'2',
   'title':('Decide, and write the decision down','Decidir, e anotar a decisão'),
   'loc':'TASK-A1C-VOICENODE-PHANTOM.md',
   'purpose':('Either outcome is valid. What is not valid is applying one silently in code.',
              'Qualquer um dos desfechos é válido. O que não é válido é aplicar um deles em silêncio no código.'),
   'body':('<p>Remove the accept verdict and the switch arm, <strong>or</strong> keep the type with a <code>note</code> stating why and on what evidence. Record the numbers alongside the decision, the way A1 recorded D5&#x27;s.</p>',
           '<p>Remover o veredito de aceite e o ramo do switch, <strong>ou</strong> manter o tipo com um <code>note</code> dizendo por quê e com base em qual evidência. Registrar os números junto da decisão, do jeito que a A1 registrou os da D5.</p>')},
  {'k':'part','n':'3',
   'title':('Let the existing drift spec catch a half-removal','Deixar a spec de drift existente pegar uma remoção pela metade'),
   'loc':'node-dispatch-invariants.spec.ts',
   'purpose':('A1 already pins the switch arms against the registry, so the two places cannot diverge quietly.',
              'A A1 já amarra os ramos do switch ao registro, então os dois lugares não podem divergir em silêncio.'),
   'body':('<p>The spec asserts the switch handles exactly <code>registeredNodeTypes().filter(legacyEndpointAccepts)</code> plus the known-unreachable arms. Dropping the arm while leaving <code>accept</code> in the registry — or the reverse — fails the suite. Confirm that is what actually happens before trusting the change.</p>',
           '<p>A spec afirma que o switch trata exatamente <code>registeredNodeTypes().filter(legacyEndpointAccepts)</code> mais os ramos sabidamente inalcançáveis. Tirar o ramo deixando o <code>accept</code> no registro — ou o contrário — quebra a suíte. Confirme que é isso mesmo que acontece antes de confiar na mudança.</p>')},
  {'k':'label','n':'3','t':('What the measurement returned, and the decision','O que a medição retornou, e a decisão')},
  {'k':'table',
   'head':[('Where','Onde'),('<code>voiceNode</code>','<code>voiceNode</code>'),('Controls in the same query','Controles na mesma query')],
   'rows':[
    [('<code>flows_nodes</code>, live canvases','<code>flows_nodes</code>, canvases vivos'),
     ('<b>0</b>','<b>0</b>'),
     ('<code>commandTextNode</code> 41,868 nodes / 15,531 flows · <code>voiceBoxNode</code> 338 / 244','<code>commandTextNode</code> 41.868 nodes / 15.531 flows · <code>voiceBoxNode</code> 338 / 244')],
    [('<code>flows_nodes</code>, version history','<code>flows_nodes</code>, histórico de versões'),
     ('<b>0</b>','<b>0</b>'),
     ('<code>commandTextNode</code> 10,670 nodes / 2,031 versions','<code>commandTextNode</code> 10.670 nodes / 2.031 versões')],
    [('<code>flows.nodes</code>, the pre-migration JSON','<code>flows.nodes</code>, o JSON pré-migração'),
     ('<b>0</b>','<b>0</b>'),
     ('<code>voiceBoxNode</code> 273 · <code>commandTextNode</code> 14,270, over 14,818 flows','<code>voiceBoxNode</code> 273 · <code>commandTextNode</code> 14.270, em 14.818 flows')],
    [('<code>node_executions</code>','<code>node_executions</code>'),
     ('<b>0</b>','<b>0</b>'),
     ('<code>commandTextNode</code> 8,783 · <code>voiceBoxNode</code> 20 — window opens 2026-08-23','<code>commandTextNode</code> 8.783 · <code>voiceBoxNode</code> 20 — janela abre em 23/08/2026')],
   ]},
  {'k':'prose','t':(
    '<p>Production and dev, read-only, all time, 2026-09-22. <strong>The <code>node_executions</code> zero is deliberately not the deciding number</strong> — that table only sees back a month, so on its own it would be &quot;not observable&quot;, the case the task said to report as unverifiable. <code>validateNode()</code> reads <code>node.type</code> off the <em>stored</em> node, so a caller cannot name a type nobody saved; <code>flows_nodes</code> covers everything since the 2026-02-24 migration and the deprecated <code>flows.nodes</code> column covers the canvases from before it. There is no window a stored <code>voiceNode</code> could hide in. It was never a front node type either, in the entire history of <code>nodeTypes.tsx</code> and <code>components/nodes/</code>.</p>'
    '<p><strong>Decision: removed</strong> from both places — the registry entry deleted, the shared arm split so <code>voiceBoxNode</code> keeps its handler. Opposite verdict from <code>comment</code>/<code>label</code>/<code>group</code> on purpose: that is the permissive prefetch whitelist, this is a live endpoint&#x27;s accept list. The production snapshots in the registry spec keep <code>voiceNode</code> verbatim — they record what production did at <code>3804a524</code> — and the departure is declared in a named <code>MEASURED_REMOVALS</code> list carrying these numbers, with a companion test that the removal is real. Full table in the task file.</p>',
    '<p>Produção e dev, somente leitura, todo o histórico, 22/09/2026. <strong>O zero de <code>node_executions</code> deliberadamente não é o número decisivo</strong> — essa tabela só enxerga um mês para trás, então sozinha seria &quot;não observável&quot;, o caso que a task mandava reportar como não verificável. O <code>validateNode()</code> lê o <code>node.type</code> do node <em>armazenado</em>, então ninguém consegue nomear um tipo que ninguém salvou; o <code>flows_nodes</code> cobre tudo desde a migração de 24/02/2026 e a coluna obsoleta <code>flows.nodes</code> cobre os canvases anteriores a ela. Não existe janela onde um <code>voiceNode</code> guardado pudesse se esconder. Ele também nunca foi um tipo de node do front, em toda a história do <code>nodeTypes.tsx</code> e do <code>components/nodes/</code>.</p>'
    '<p><strong>Decisão: removido</strong> dos dois lugares — a entrada do registro apagada, o ramo compartilhado separado para o <code>voiceBoxNode</code> manter o handler dele. Veredito oposto ao de <code>comment</code>/<code>label</code>/<code>group</code> de propósito: aquela é a whitelist permissiva de prefetch, esta é a lista de aceite de um endpoint vivo. Os snapshots de produção na spec do registro mantêm o <code>voiceNode</code> verbatim — eles registram o que a produção fazia em <code>3804a524</code> — e a divergência é declarada numa lista nomeada <code>MEASURED_REMOVALS</code> que carrega estes números, com um teste companheiro de que a remoção é real. Tabela completa no arquivo da task.</p>')},
 ],
 'verif':[
  (True,('Negative control','Controle negativo'),
   ('Before removing the switch arm, drop it while leaving <code>legacyEndpoint: &#x27;accept&#x27;</code> in the registry, and record which test goes red with what message. Then make the real change.',
    'Antes de remover o ramo do switch, tire-o deixando o <code>legacyEndpoint: &#x27;accept&#x27;</code> no registro, e anote qual teste fica vermelho e com que mensagem. Depois faça a mudança real.')),
  (True,('The measurement, with its control row','A medição, com sua linha de controle'),
   ('Stored nodes and executions, production, read-only, modelled on <code>etc/a1-q1-phantom-types-prod.sql</code>. A control row for a type known to be present is required, not optional.',
    'Nodes guardados e execuções, produção, somente leitura, no molde do <code>etc/a1-q1-phantom-types-prod.sql</code>. Uma linha de controle para um tipo sabidamente presente é obrigatória, não opcional.')),
  (True,('Measure before refusing','Medir antes de recusar'),
   ('If the measurement cannot distinguish &quot;never used&quot; from &quot;not observable&quot;, report it as <b>unverifiable</b> and keep the type with a <code>note</code>. Unknown is not zero, and a false refusal on a live endpoint is worse than a stale switch arm.',
    'Se a medição não distinguir “nunca usado” de “não observável”, reporte como <b>não verificável</b> e mantenha o tipo com um <code>note</code>. Desconhecido não é zero, e uma recusa falsa num endpoint vivo é pior que um ramo de switch velho.')),
 ],
 'done':('The measurement is run and its numbers are in the task file. <code>voiceNode</code> is either gone from <strong>both</strong> the registry&#x27;s accept verdict and the dispatch switch, or present with a <code>note</code> saying why and on what evidence. <strong>No request that succeeds today against <code>/process/single-node-legacy</code> refuses afterwards.</strong>',
         'A medição foi feita e os números dela estão no arquivo da task. O <code>voiceNode</code> ou saiu <strong>dos dois</strong> — o veredito de aceite do registro e o switch de dispatch — ou está presente com um <code>note</code> dizendo por quê e com base em qual evidência. <strong>Nenhuma requisição que hoje funciona no <code>/process/single-node-legacy</code> passa a ser recusada depois.</strong>'),
 'files':[
  ('back/src/shared/node-dispatch/node-dispatch-registry.ts (the voiceNode entry)',False),
  ('back/src/temporal/single-node-legacy/legacy-node-dispatch.ts (the shared switch arm)',False),
  ('back/src/shared/node-dispatch/node-dispatch-invariants.spec.ts (the switch drift spec)',False),
  ('TASK-A1 — What D5 actually returned (the precedent this task follows)',True),
 ],
}

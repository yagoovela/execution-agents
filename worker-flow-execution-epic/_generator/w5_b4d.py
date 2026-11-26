# -*- coding: utf-8 -*-
TITLE = ('Source order parity on the workflow path',
         'Paridade da ordem das fontes no caminho do workflow')

GOAL = ('A Data Output with several sources <b>joins their text in the legacy loop&#x27;s order on every workflow entry point</b>: API runs with and without variable inputs, batch rows, schedules and child runs. Completion order never enters the rule.',
        'Um Data Output com várias fontes <b>junta o texto delas na ordem do laço legado em toda porta de entrada do workflow</b>: runs de API com e sem entradas variáveis, linhas de batch, agendamentos e runs filhos. A ordem de conclusão nunca entra na regra.')

GLANCE = [
 ('crit', ('Customer impact','Impacto no cliente'), ('The reply and the stored chat answer','A resposta e a resposta salva no chat'),
  ('With <code>engine_in_workflow</code> on, the same flow can return its sources in another order, and a chat flow stores another assistant entry. Batch rows already run on <code>processFlow</code> and start from the canvas order.',
   'Com a <code>engine_in_workflow</code> ligada, o mesmo fluxo pode devolver as fontes em outra ordem, e um fluxo de chat salva outra resposta do assistente. As linhas de batch já rodam no <code>processFlow</code> e partem da ordem do canvas.')),
 ('dep', ('Depends on','Depende de'), ('B3b · B4','B3b · B4'),
  ('Both on <code>main</code>. Coordinates with B4c, which edits the same seed builders. It blocks turning <code>engine_in_workflow</code> and <code>temporal_schedules</code> on in production. Independent of B5.',
   'As duas no <code>main</code>. Coordena com a B4c, que mexe nos mesmos montadores de seed. Bloqueia ligar a <code>engine_in_workflow</code> e a <code>temporal_schedules</code> em produção. Independe da B5.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Added on 2026-11-26 from finding 1 of the A14-R4 dev parity run. The defect predates A14: probe X1 has no memory.',
   'Adicionada em 26/11/2026 a partir do achado 1 da paridade A14-R4 no dev. O defeito é anterior à A14: a sonda X1 não tem memória.')),
 ('ship', ('Shape','Formato'), ('Back seed and worker projection','Seed no back e projeção no worker'),
  ('Estimate 12 to 28 h, uncalibrated. The order rule is extracted from the back&#x27;s <code>addConnectToNodes</code> and ported, never restated.',
   'Estimativa de 12 a 28 h, sem calibração. A regra da ordem é extraída do <code>addConnectToNodes</code> do back e portada, nunca reescrita.')),
]

LEDE = (
 '<p>On dev on 2026-11-26, probe X1 (two <code>mathFunction</code> nodes into one Data Output) returned <code>first runs</code>, <code>second runs</code> with <code>engine_in_workflow</code> off and <code>second runs</code>, <code>first runs</code> with it on. A chat flow with two AI Text Generators changed its answer text and its stored assistant entry the same way.</p>'
 '<p>The legacy order is not completion order. <code>apiV2</code> empties the Data Output at run start, and its first <code>addConnectToNodes</code> call writes an entry for every source, in the order each source first appears in the flow&#x27;s edge list. The worker adds entries in the order it reads the target&#x27;s incoming edges, from a query with no <code>ORDER BY</code>. '
 'Batch rows and schedules (<code>prepareWorkflowSeed</code>) skip the run-start reset, so they start from the canvas order, which is the order of whichever engine ran last.</p>',
 '<p>No dev, em 26/11/2026, a sonda X1 (dois nós <code>mathFunction</code> em um Data Output) devolveu <code>first runs</code>, <code>second runs</code> com a <code>engine_in_workflow</code> desligada e <code>second runs</code>, <code>first runs</code> com ela ligada. Um fluxo de chat com dois AI Text Generators mudou o texto da resposta e a resposta salva do assistente do mesmo jeito.</p>'
 '<p>A ordem do legado não é a ordem de conclusão. O <code>apiV2</code> esvazia o Data Output no início do run, e a primeira chamada do <code>addConnectToNodes</code> grava uma entrada para cada fonte, na ordem em que cada fonte aparece primeiro na lista de arestas do fluxo. O worker acrescenta as entradas na ordem em que lê as arestas de entrada do alvo, de uma consulta sem <code>ORDER BY</code>. '
 'Linhas de batch e agendamentos (<code>prepareWorkflowSeed</code>) pulam o reset do início do run, então partem da ordem do canvas, que é a ordem do último motor que rodou.</p>')

TABLE = dict(
 head=[('Path','Caminho'),('Legacy loop','Laço legado'),('Workflow path today','Caminho do workflow hoje')],
 rows=[
  [('API run, no variable inputs','Run de API, sem entradas variáveis'),
   {'t':('First appearance in the edge list','Primeira aparição na lista de arestas'),'pill':'ok'},{'t':('Edge read order','Ordem de leitura das arestas'),'pill':'weak'}],
  [('API run with variable inputs','Run de API com entradas variáveis'),
   {'t':('First appearance in the edge list','Primeira aparição na lista de arestas'),'pill':'ok'},{'t':('Legacy order, by accident of the prefill','Ordem do legado, por acaso do preenchimento'),'pill':'ok'}],
  [('Batch row or schedule','Linha de batch ou agendamento'),
   {'t':('First appearance in the edge list','Primeira aparição na lista de arestas'),'pill':'ok'},{'t':('Canvas order, of the engine that ran last','Ordem do canvas, do último motor que rodou'),'pill':'weak'}],
 ])

PARTS = [
{'n':'1','title':('The seed holds the legacy order','O seed guarda a ordem do legado'),
 'loc':('back/src/app-api/flux (run seed)','back/src/app-api/flux (seed do run)'),
 'purpose':('Before <code>runApiV2ViaWorkflow</code> and <code>prepareWorkflowSeed</code> write a seed, they run one <code>addConnectToNodes</code> pass over a copy of the seed nodes, as <code>applyVariableInputsToSeedNodes</code> already does.',
            'Antes de o <code>runApiV2ViaWorkflow</code> e o <code>prepareWorkflowSeed</code> gravarem um seed, eles rodam uma passada do <code>addConnectToNodes</code> sobre uma cópia dos nós do seed, como o <code>applyVariableInputsToSeedNodes</code> já faz.'),
 'body':('<p>The pass works on a copy, so the legacy loop does not change. A simulation on the <code>main</code> engine files shows that a prefilled seed keeps <code>A, B, C</code> even when the worker reads the edges in reverse.</p>',
         '<p>A passada trabalha numa cópia, então o laço legado não muda. Uma simulação com os arquivos do motor no <code>main</code> mostra que um seed preenchido mantém <code>A, B, C</code> mesmo quando o worker lê as arestas ao contrário.</p>'),
 'ba':(('An API seed without variable inputs holds an empty <code>textData</code>.','Um seed de API sem entradas variáveis guarda um <code>textData</code> vazio.'),
       ('Every source has its entry in the legacy order before the workflow starts.','Toda fonte tem sua entrada na ordem do legado antes de o workflow começar.'))},

{'n':'2','title':('One run-start reset','Um único reset no início do run'),
 'loc':('back node-output-reset.ts · apiV2 · prepareWorkflowSeed','back node-output-reset.ts · apiV2 · prepareWorkflowSeed'),
 'purpose':('The Data Output reset moves out of <code>apiV2</code> into <code>node-output-reset.ts</code>, next to <code>clearRunOutputForSeed</code>, and both <code>apiV2</code> and <code>prepareWorkflowSeed</code> call it.',
            'O reset do Data Output sai do <code>apiV2</code> e vai para o <code>node-output-reset.ts</code>, ao lado do <code>clearRunOutputForSeed</code>, e o <code>apiV2</code> e o <code>prepareWorkflowSeed</code> o chamam.'),
 'body':('<p>B7b set the precedent of aligning <code>prepareWorkflowSeed</code> with <code>apiV2</code>. As a side effect, a source on a dead branch no longer keeps its canvas text on a batch or schedule seed.</p>',
         '<p>A B7b abriu o precedente de alinhar o <code>prepareWorkflowSeed</code> com o <code>apiV2</code>. Como efeito colateral, uma fonte num ramo morto deixa de manter o texto do canvas num seed de batch ou de agendamento.</p>'),
 'ba':(('A batch row starts from the canvas order and old texts.','Uma linha de batch parte da ordem do canvas e de textos antigos.'),
       ('A batch row lists the legacy order with this run&#x27;s texts.','Uma linha de batch lista a ordem do legado com os textos deste run.'))},

{'n':'3','title':('The worker walks sources in the legacy order','O worker percorre as fontes na ordem do legado'),
 'loc':('back folw/helpers/edge-projection.ts · worker projectNodeInput','back folw/helpers/edge-projection.ts · worker projectNodeInput'),
 'purpose':('The source order of <code>addConnectToNodes</code> becomes an exported function that <code>sync:ported-engine</code> ports; <code>addConnectToNodes</code> and <code>projectIntoNode</code> both call it.',
            'A ordem das fontes do <code>addConnectToNodes</code> vira uma função exportada que o <code>sync:ported-engine</code> porta; o <code>addConnectToNodes</code> e o <code>projectIntoNode</code> a chamam.'),
 'body':('<p>The worker applies it to the run&#x27;s edge list in the order the back loaded it (<code>run_seeds.payload.edges</code>), not to the unordered edge query. The seed is data written before the workflow starts and the projection runs in an activity, so no workflow code changes and no <code>patched()</code> gate is needed. Open: where the worker gets the edge order on the legacy loop&#x27;s B3b path, which has no <code>run_seeds</code> row (B4d-D1).</p>',
         '<p>O worker a aplica à lista de arestas do run na ordem em que o back a carregou (<code>run_seeds.payload.edges</code>), não à consulta de arestas sem ordem. O seed é um dado gravado antes de o workflow começar e a projeção roda numa activity, então nenhum código de workflow muda e nenhum gate <code>patched()</code> é preciso. Em aberto: de onde o worker tira a ordem das arestas no caminho B3b do laço legado, que não tem linha em <code>run_seeds</code> (B4d-D1).</p>')},
]

VERIF = [
 (False, ('Negative control','Controle negativo'),
  ('A worker spec on <code>projectNodeInput</code> with the X1 fixture, the edge query returning <code>second→Out</code> before <code>first→Out</code>: on <code>main</code> the result is <code>second, first</code>; after the change it is <code>first, second</code>.',
   'Um spec do worker no <code>projectNodeInput</code> com a fixture X1, com a consulta de arestas devolvendo <code>second→Out</code> antes de <code>first→Out</code>: no <code>main</code> o resultado é <code>second, first</code>; depois da mudança é <code>first, second</code>.')),
 (False, ('Discriminating fixture','Fixture discriminante'),
  ('With edges <code>A→Out, S→B, B→A, B→Out, C→Out, B→C</code>, the legacy loop for both completion orders and the worker for both edge read orders all give <code>A, B, C</code>.',
   'Com as arestas <code>A→Out, S→B, B→A, B→Out, C→Out, B→C</code>, o laço legado nas duas ordens de conclusão e o worker nas duas ordens de leitura das arestas dão <code>A, B, C</code>.')),
 (False, ('Seeds and replay','Seeds e replay'),
  ('An API seed without variable inputs holds every source in the legacy order; a batch seed whose canvas holds <code>B, A</code> gives <code>A, B</code> with this run&#x27;s texts; the <code>processFlow</code> replay histories replay unchanged.',
   'Um seed de API sem entradas variáveis guarda todas as fontes na ordem do legado; um seed de batch cujo canvas tem <code>B, A</code> dá <code>A, B</code> com os textos deste run; os históricos de replay do <code>processFlow</code> rodam sem mudança.')),
 (False, ('Dev and production','Dev e produção'),
  ('On dev, X1, a chat flow of the F2 class and the fixture give identical <code>textData</code> with <code>engine_in_workflow</code> off and on. In production, <code>b4d-q1</code> sizes the reach before the deploy; on dev it found 51 flows with a multi-source Data Output, 18 with a different order.',
   'No dev, a X1, um fluxo de chat da classe F2 e a fixture dão <code>textData</code> idêntico com a <code>engine_in_workflow</code> desligada e ligada. Em produção, a <code>b4d-q1</code> mede o alcance antes do deploy; no dev ela achou 51 fluxos com Data Output de várias fontes, 18 com ordem diferente.')),
]

DONE = ('Every multi-source target gets its entries in the legacy loop&#x27;s order on every workflow entry point; the order does not depend on completion order, so B5 and Temporal replay cannot change it; the rule comes from the back&#x27;s own code, never restated in the worker.',
        'Todo alvo com várias fontes recebe as entradas na ordem do laço legado em toda porta de entrada do workflow; a ordem não depende da ordem de conclusão, então a B5 e o replay do Temporal não a mudam; a regra vem do próprio código do back, nunca reescrita no worker.')

FILES = [('back/src/app-api/flux/flux.service.ts (runApiV2ViaWorkflow, prepareWorkflowSeed, apiV2 run-start reset)', False),
         ('back node-output-reset.ts (clearRunOutputForSeed and the shared reset)', False),
         ('back folw/helpers/edge-projection.ts (source order of addConnectToNodes)', False),
         ('worker project-node-input.ts (projectIntoNode, sourcesOf)', False)]

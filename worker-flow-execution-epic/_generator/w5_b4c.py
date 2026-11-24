# -*- coding: utf-8 -*-
TITLE = ('Placeholder substitution on the workflow path',
         'Substituição de placeholders no caminho do workflow')

GOAL = ('Every <code>{{...}}</code> placeholder that the legacy loop resolves <b>resolves to the same value on the workflow path</b>, on every entry point: batch rows, API runs, schedules and child runs.',
        'Todo placeholder <code>{{...}}</code> que o laço legado resolve <b>resolve para o mesmo valor no caminho do workflow</b>, em toda porta de entrada: linhas de batch, runs de API, agendamentos e runs filhos.')

GLANCE = [
 ('crit', ('Customer impact','Impacto no cliente'), ('Batch rows in production, today','Linhas de batch em produção, hoje'),
  ('Since B7 (2026-11-03) every batch row runs on <code>processFlow</code> with no flag, so every batch row whose flow holds a placeholder sends the literal text to the model or the API.',
   'Desde a B7 (03/11/2026) toda linha de batch roda no <code>processFlow</code> sem flag, então toda linha de batch cujo fluxo tem um placeholder envia o texto literal ao modelo ou à API.')),
 ('dep', ('Depends on','Depende de'), ('B3 · B4','B3 · B4'),
  ('Both on <code>main</code>. It blocks turning <code>engine_in_workflow</code> and <code>temporal_schedules</code> on in production, and B4b-D1.',
   'As duas no <code>main</code>. Bloqueia ligar a <code>engine_in_workflow</code> e a <code>temporal_schedules</code> em produção, e a B4b-D1.')),
 ('wave', ('Wave','Onda'), ('Wave 5, urgent','Onda 5, urgente'),
  ('Added on 2026-11-24 from the A14 edge-case investigation. First of the three tasks it produced.',
   'Adicionada em 24/11/2026 a partir da investigação de casos de borda da A14. A primeira das três tasks que ela gerou.')),
 ('ship', ('Shape','Formato'), ('Back seed and worker overlay','Seed no back e sobreposição no worker'),
  ('Estimate 1.5 to 3 days. The substitution rule is imported from the back&#x27;s service, never restated.',
   'Estimativa de 1,5 a 3 dias. A regra de substituição é importada do serviço do back, nunca reescrita.')),
]

LEDE = (
 '<p>On the workflow path (<code>processFlow</code>), no <code>{{...}}</code> placeholder in a node&#x27;s text is replaced. The node receives the literal text, for example <code>{{topic.text}}</code>, and sends it to the model or the API.</p>'
 '<p>The legacy loop builds a substitution schema from every node at run start (<code>generateSchemaFromNodes</code>) and updates it after each node runs (<code>updateSchemaWithNodeOutput</code>); with <code>worker_input_resolution</code> on, it stores that schema as the snapshot <code>base</code> and each dispatch as a delta, so the worker rebuilds it exactly (B3). '
 'The B4 path writes <code>base = {}</code>, each open writes an empty delta, and <code>processFlow</code> passes an empty journal. <strong>No task owned it.</strong> API runs and schedules are not affected yet, because <code>engine_in_workflow</code> and <code>temporal_schedules</code> are off in production.</p>',
 '<p>No caminho do workflow (<code>processFlow</code>), nenhum placeholder <code>{{...}}</code> no texto de um nó é substituído. O nó recebe o texto literal, por exemplo <code>{{topic.text}}</code>, e o envia ao modelo ou à API.</p>'
 '<p>O laço legado monta um esquema de substituição a partir de todos os nós no início do run (<code>generateSchemaFromNodes</code>) e o atualiza depois de cada nó (<code>updateSchemaWithNodeOutput</code>); com a <code>worker_input_resolution</code> ligada, ele grava esse esquema como a <code>base</code> do snapshot e cada dispatch como um delta, e o worker o reconstrói exatamente (B3). '
 'O caminho da B4 grava <code>base = {}</code>, cada abertura grava um delta vazio, e o <code>processFlow</code> passa um journal vazio. <strong>Nenhuma task era dona disso.</strong> Runs de API e agendamentos ainda não são afetados, porque a <code>engine_in_workflow</code> e a <code>temporal_schedules</code> estão desligadas em produção.</p>')

TABLE = dict(
 head=[('Reference','Referência'),('Legacy loop','Laço legado'),('Workflow path today','Caminho do workflow hoje')],
 rows=[
  [('<code>{{label.text}}</code> to a node with no edge','<code>{{label.text}}</code> para um nó sem aresta'),
   {'t':('Resolved','Resolvido'),'pill':'ok'},{'t':('Literal','Literal'),'pill':'weak'}],
  [('<code>{{x}}</code> to a node connected by an edge','<code>{{x}}</code> para um nó ligado por aresta'),
   {'t':('Resolved','Resolvido'),'pill':'ok'},{'t':('Literal (only the <code>*Data</code> array arrives)','Literal (só o array <code>*Data</code> chega)'),'pill':'weak'}],
  [('<code>{{varinput.text}}</code> (run input or batch row value)','<code>{{varinput.text}}</code> (entrada do run ou valor da linha do batch)'),
   {'t':('Resolved','Resolvido'),'pill':'ok'},{'t':('Literal','Literal'),'pill':'weak'}],
  [('<code>{{textbox.text}}</code> (a source node)','<code>{{textbox.text}}</code> (um nó de origem)'),
   {'t':('Resolved','Resolvido'),'pill':'ok'},{'t':('Literal','Literal'),'pill':'weak'}],
  [('<code>{{writer.text}}</code> after <code>writer</code> ran','<code>{{writer.text}}</code> depois que o <code>writer</code> rodou'),
   {'t':('Its output','A saída dele'),'pill':'ok'},{'t':('Literal','Literal'),'pill':'weak'}],
 ])

PARTS = [
{'n':'1','title':('Seed the snapshot base with the back&#x27;s own schema','Semear a base do snapshot com o esquema do próprio back'),
 'loc':('back/src/app-api/flux (run seed)','back/src/app-api/flux (seed do run)'),
 'purpose':('The seed writes the snapshot <code>base</code> with <code>generateSchemaFromNodes</code> over the nodes after run inputs are applied, instead of <code>{}</code>.',
            'O seed grava a <code>base</code> do snapshot com o <code>generateSchemaFromNodes</code> sobre os nós depois de aplicadas as entradas do run, em vez de <code>{}</code>.'),
 'body':('<p>The base holds the text fields of every referenceable node and lives in <code>run_substitution_snapshots.base</code>, not in Temporal history. A <code>textBox</code> with an empty <code>text</code> is filled from its <code>textData</code>, as <code>generateSchemaFromNodes</code> does.</p>',
         '<p>A base guarda os campos de texto de todo nó referenciável e fica na <code>run_substitution_snapshots.base</code>, não no histórico do Temporal. Um <code>textBox</code> com <code>text</code> vazio é preenchido pelo <code>textData</code>, como o <code>generateSchemaFromNodes</code> faz.</p>'),
 'ba':(('The workflow path seeds an empty base.','O caminho do workflow semeia uma base vazia.'),
       ('Run inputs, batch row values and stored node values resolve.','Entradas do run, valores da linha do batch e valores guardados dos nós resolvem.'))},

{'n':'2','title':('Overlay the outputs of nodes that already finished','Sobrepor as saídas dos nós que já terminaram'),
 'loc':('worker (input resolution) · processFlow','worker (resolução de entrada) · processFlow'),
 'purpose':('Before a node resolves, the worker overlays the outputs of nodes that finished earlier in the run, in the legacy order.',
            'Antes de um nó resolver, o worker sobrepõe as saídas dos nós que terminaram antes no run, na ordem do legado.'),
 'body':('<p>Either through the ported <code>updateSchemaWithNodeOutput</code>, or by <code>processFlow</code> passing a real journal so that each finished node records its delta; the design picks one. '
         'References inside an <code>arrayNode</code> iteration follow the legacy per-iteration values (B3.1), the schema carries over <code>continueAsNew</code>, and a claim-checked output resolves through its claim ref. Under B5, a node sees only the outputs of nodes that finished before it was dispatched.</p>',
         '<p>Pelo <code>updateSchemaWithNodeOutput</code> portado, ou pelo <code>processFlow</code> passando um journal real para que cada nó concluído registre o seu delta; o design escolhe um. '
         'Referências dentro de uma iteração de <code>arrayNode</code> seguem os valores por iteração do legado (B3.1), o esquema atravessa o <code>continueAsNew</code>, e uma saída em claim check resolve pela referência. Com a B5, um nó só vê as saídas dos nós que terminaram antes de ele ser despachado.</p>'),
 'ba':(('<code>{{writer.text}}</code> stays literal after <code>writer</code> ran.','<code>{{writer.text}}</code> fica literal depois que o <code>writer</code> rodou.'),
       ('It resolves to <code>writer</code>&#x27;s output, as on the legacy loop.','Resolve para a saída do <code>writer</code>, como no laço legado.'))},

{'n':'3','title':('Parity on every entry point','Paridade em toda porta de entrada'),
 'loc':('batch rows · API runs · schedules · child runs','linhas de batch · runs de API · agendamentos · runs filhos'),
 'purpose':('Batch rows in production resolve placeholders again, and API, scheduled and child runs match the legacy loop placeholder for placeholder.',
            'As linhas de batch em produção voltam a resolver placeholders, e os runs de API, agendados e filhos batem com o laço legado placeholder por placeholder.'),
 'body':('<p>Out of scope: a bare <code>{{label}}</code> that resolves to <code>[object Object]</code> and unknown keys that stay literal are legacy behaviour, and parity keeps them. Seed pruning is B4b-D1, after this task.</p>',
         '<p>Fora do escopo: um <code>{{label}}</code> sem campo que vira <code>[object Object]</code> e chaves desconhecidas que ficam literais são comportamento do legado, e a paridade os mantém. A poda do seed é a B4b-D1, depois desta task.</p>')},
]

VERIF = [
 (False, ('Negative control','Controle negativo'),
  ('On <code>main</code>, a batch row with <code>{{varinput.text}}</code>, <code>{{textbox.text}}</code>, an edgeless <code>{{label.text}}</code> and <code>{{writer.text}}</code> after <code>writer</code> sends all four literals; after the change, all four resolve to the legacy loop&#x27;s values.',
   'No <code>main</code>, uma linha de batch com <code>{{varinput.text}}</code>, <code>{{textbox.text}}</code>, um <code>{{label.text}}</code> sem aresta e <code>{{writer.text}}</code> depois do <code>writer</code> envia os quatro literais; depois da mudança, os quatro resolvem para os valores do laço legado.')),
 (False, ('Parity corpus','Corpus de paridade'),
  ('Stored dev flows that hold placeholders run on both engines with matching node inputs; a three-row batch file carries each row&#x27;s values.',
   'Fluxos guardados em dev que têm placeholders rodam nos dois motores com entradas de nó iguais; um arquivo de batch de três linhas carrega os valores de cada linha.')),
 (False, ('Array iterations, claim checks, schedules and API runs','Iterações de array, claim checks, agendamentos e runs de API'),
  ('A reference inside an <code>arrayNode</code> body resolves per iteration; a claim-checked output resolves; a scheduled run and an API run with the flags on locally reach parity.',
   'Uma referência dentro do corpo de um <code>arrayNode</code> resolve por iteração; uma saída em claim check resolve; um run agendado e um run de API com as flags ligadas localmente chegam à paridade.')),
 (False, ('Dev and production','Dev e produção'),
  ('On dev, a batch file with placeholders shows resolved inputs in <code>node_executions.input</code>. In production, impact queries run before and after the deploy, and literals in the inputs of new batch rows drop to zero.',
   'Em dev, um arquivo de batch com placeholders mostra entradas resolvidas no <code>node_executions.input</code>. Em produção, consultas de impacto rodam antes e depois do deploy, e os literais nas entradas das novas linhas de batch caem para zero.')),
]

DONE = ('Every placeholder the legacy loop resolves resolves to the same value on the workflow path, on every entry point; batch rows in production resolve placeholders again; the rule is imported from the back&#x27;s service, never restated.',
        'Todo placeholder que o laço legado resolve resolve para o mesmo valor no caminho do workflow, em toda porta de entrada; as linhas de batch em produção voltam a resolver placeholders; a regra é importada do serviço do back, nunca reescrita.')

FILES = [('back/src/app-api/flux/flux.service.ts (generateSchemaFromNodes, updateSchemaWithNodeOutput, openWorkerNodeExecution)', False),
         ('back run seed service (snapshot base)', False),
         ('worker/src/modules/temporal/workflows/process-flow.workflow.ts', False),
         ('worker input resolution (schema overlay)', False)]

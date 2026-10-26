# -*- coding: utf-8 -*-
TITLE = ('Give every node type an execution class', 'Dar uma classe de execução a todo tipo de node')

GOAL = ('Every node type the product can put on a canvas has <b>one entry in the dispatch registry that says where it executes</b>, '
        'and every hand-kept type list is derived from that entry.',
        'Todo tipo de node que o produto consegue pôr num canvas tem <b>uma entrada no registro de dispatch que diz onde ele executa</b>, '
        'e toda lista de tipos mantida à mão é derivada dessa entrada.')

GLANCE = [
 ('crit', ('Blocks','Bloqueia'), ('B4 flag in production · B5','Flag da B4 em produção · B5'),
  ('Turning the B4 flag on in production, and B5&#x27;s measurement. Both read the class this task adds.',
   'Ligar a flag da B4 em produção, e a medição da B5. As duas leem a classe que esta task adiciona.')),
 ('dep', ('Depends on','Depende de'), ('A1','A1'),
  ('The dispatch registry and its contract. Added 2026-10-23 from <code>NODE-COVERAGE-AUDIT-2026-10-23.md</code>.',
   'O registro de dispatch e o contrato dele. Adicionada em 2026-10-23 a partir do <code>NODE-COVERAGE-AUDIT-2026-10-23.md</code>.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('First in the wave: A11 → A13 → B4 flag on in production → A7 → A14 → B5 → B6 and B7.',
   'Primeira da onda: A11 → A13 → flag da B4 ligada em produção → A7 → A14 → B5 → B6 e B7.')),
 ('ship', ('Shape','Formato'), ('Classification only','Só classificação'),
  ('<strong>No execution moves.</strong> One field, the lists derived from it, and a drift spec.',
   '<strong>Nenhuma execução muda de lugar.</strong> Um campo, as listas derivadas dele, e uma spec de drift.')),
]

LEDE = (
 '<p>The registry can say <code>worker</code> or <code>inline</code>, but it cannot say &quot;does not execute&quot;. B4&#x27;s gate '
 '(<code>canUseWorkflowForFlow</code>, <code>back/src/app-api/flux/engine-selector.ts</code>) accepts a flow only when every node is '
 '<code>worker</code> or one of five hard-coded passive types. So a Data Input, a sticky note or a Small Memory node keeps '
 '<strong>the whole flow on the back&#x27;s loop</strong>, and the loop can never be deleted.</p>'
 '<p>The epic did map these types. PLAN §8 put the 11 inert types out of scope, but nothing turned &quot;out of scope&quot; into a registry value, '
 'and <strong>four copies of the passive list grew instead</strong>: <code>NON_EXECUTABLE_NODE_TYPES</code>, <code>WORKFLOW_SAFE_NON_WORKER_TYPES</code>, '
 'a literal list inside <code>apiV2</code>&#x27;s logging, and the worker&#x27;s <code>NON_EXECUTABLE_TYPES</code> with a &quot;keep in sync&quot; comment.</p>',
 '<p>O registro consegue dizer <code>worker</code> ou <code>inline</code>, mas não consegue dizer &quot;não executa&quot;. O gate da B4 '
 '(<code>canUseWorkflowForFlow</code>, <code>back/src/app-api/flux/engine-selector.ts</code>) aceita um fluxo só quando todo node é '
 '<code>worker</code> ou um de cinco tipos passivos fixos no código. Por isso um Data Input, uma sticky note ou um node Small Memory prende '
 '<strong>o fluxo inteiro no laço do back</strong>, e o laço nunca pode ser apagado.</p>'
 '<p>O épico mapeou esses tipos. O PLAN §8 pôs os 11 tipos inertes fora de escopo, mas nada transformou &quot;fora de escopo&quot; num valor do registro, '
 'e <strong>em vez disso cresceram quatro cópias da lista de passivos</strong>: <code>NON_EXECUTABLE_NODE_TYPES</code>, <code>WORKFLOW_SAFE_NON_WORKER_TYPES</code>, '
 'uma lista literal dentro do log do <code>apiV2</code>, e a <code>NON_EXECUTABLE_TYPES</code> do worker com um comentário &quot;keep in sync&quot;.</p>')

TABLE = dict(
 head=[('Class','Classe'),('Types (audit, 2026-10-23)','Tipos (auditoria, 2026-10-23)'),('Value','Valor'),('Why','Por quê')],
 rows=[
  [{'t':('Visual only','Só visual')},
   ('<code>stickyNote</code>, <code>nodesGroup</code>, <code>richTextBox</code>, <code>comment</code>, <code>label</code>, <code>group</code>, <code>textBox</code>',
    '<code>stickyNote</code>, <code>nodesGroup</code>, <code>richTextBox</code>, <code>comment</code>, <code>label</code>, <code>group</code>, <code>textBox</code>'),
   {'t':('none','none'),'pill':'ok'},
   ('They draw on the canvas and do not execute.','Desenham no canvas e não executam.')],
  [{'t':('Configuration read by the projection','Configuração lida pela projeção')},
   ('<code>storedDataCaller</code>, <code>deepRefNode</code>, <code>nodesAdd</code>, <code>mediaBox</code>, <code>outputTable</code>, <code>tableProcessor</code>, <code>dynamicSettingsNode</code>',
    '<code>storedDataCaller</code>, <code>deepRefNode</code>, <code>nodesAdd</code>, <code>mediaBox</code>, <code>outputTable</code>, <code>tableProcessor</code>, <code>dynamicSettingsNode</code>'),
   {'t':('none','none'),'pill':'ok'},
   ('The projection reads their configuration; the node itself does not run.','A projeção lê a configuração deles; o node em si não roda.')],
  [{'t':('Run entry','Entrada do run')},
   ('<code>varInputNode</code>','<code>varInputNode</code>'),
   {'t':('none','none'),'pill':'ok'},
   ('The back binds run inputs before the loop.','O back associa as entradas do run antes do laço.')],
  [{'t':('Registry wrong today','Registro errado hoje')},
   ('<code>thirdPartyIntegration</code>, <code>hubSpotCRM</code>','<code>thirdPartyIntegration</code>, <code>hubSpotCRM</code>'),
   {'t':('worker','worker'),'pill':'weak'},
   ('Their entry has to change to <code>worker</code>.','A entrada deles precisa mudar para <code>worker</code>.')],
  [{'t':('MCP-only, no front component','Só no MCP, sem componente no front')},
   ('<code>webNews</code>, <code>webMedia</code>, <code>webLocations</code>, <code>varInputForm</code>',
    '<code>webNews</code>, <code>webMedia</code>, <code>webLocations</code>, <code>varInputForm</code>'),
   {'t':('classify or remove','classificar ou remover'),'pill':'no'},
   ('Classify them, or remove them from the MCP metadata.','Classificar, ou remover dos metadados do MCP.')],
 ])

PARTS = [
{'n':'1','title':('An <code>execution</code> field on every entry','Um campo <code>execution</code> em toda entrada'),
 'loc':'back/src/shared/node-dispatch/node-dispatch-registry.ts',
 'purpose':('Give every registry entry one of three values: <code>worker</code>, <code>back</code> or <code>none</code>.',
            'Dar a toda entrada do registro um de três valores: <code>worker</code>, <code>back</code> ou <code>none</code>.'),
 'body':('<p>Classify each type <strong>from the code that reads or writes it at run time, not from its name</strong>. The table above is the '
         'audit&#x27;s classification on 2026-10-23. Every canvas type and every MCP type gets a class, and the published contract '
         '<code>node-dispatch-contract.json</code> carries it.</p>',
         '<p>Classifique cada tipo <strong>pelo código que o lê ou escreve em tempo de execução, não pelo nome</strong>. A tabela acima é a '
         'classificação da auditoria em 2026-10-23. Todo tipo de canvas e todo tipo do MCP recebe uma classe, e o contrato publicado '
         '<code>node-dispatch-contract.json</code> a carrega.</p>'),
 'ba':(('The registry says <code>worker</code> or <code>inline</code>. A type that does not execute has no value to say so.',
        'O registro diz <code>worker</code> ou <code>inline</code>. Um tipo que não executa não tem valor para dizer isso.'),
       ('Every canvas and MCP type has an <code>execution</code> class, and <code>none</code> is a real value.',
        'Todo tipo de canvas e do MCP tem uma classe <code>execution</code>, e <code>none</code> é um valor de verdade.'))},

{'n':'2','title':('Derive every type list from the field','Derivar toda lista de tipos do campo'),
 'loc':'engine-selector.ts · is-non-executable.ts · node-input-projection.ts',
 'purpose':('Replace the hand-kept lists and the B4 gate&#x27;s literal types with values read from the registry.',
            'Trocar as listas mantidas à mão e os tipos literais do gate da B4 por valores lidos do registro.'),
 'body':('<p>Derive from the field: the four passive lists, <code>BACK_ONLY_PROJECTION_NODE_TYPES</code> in the back and in the worker, '
         'and the B4 gate in <code>canUseWorkflowForFlow</code>. The logging copy lives in <code>flux.service.ts</code>; the worker copy lives in '
         '<code>process-flow.workflow.ts</code> and the ported projection list.</p>'
         '<p><code>tableProcessor</code> and <code>dynamicSettingsNode</code> read fields that no writer stores in <code>outputData</code>. '
         '<strong>The worker projection reads them from the run seed instead</strong>, and they leave the back-only list.</p>',
         '<p>Derivar do campo: as quatro listas de passivos, a <code>BACK_ONLY_PROJECTION_NODE_TYPES</code> no back e no worker, '
         'e o gate da B4 em <code>canUseWorkflowForFlow</code>. A cópia do log fica em <code>flux.service.ts</code>; a cópia do worker fica em '
         '<code>process-flow.workflow.ts</code> e na lista de projeção portada.</p>'
         '<p><code>tableProcessor</code> e <code>dynamicSettingsNode</code> leem campos que nenhum escritor grava em <code>outputData</code>. '
         '<strong>A projeção do worker passa a lê-los da semente do run</strong>, e eles saem da lista só-back.</p>'),
 'ba':(('Four copies of the passive list, one of them in another repository behind a &quot;keep in sync&quot; comment.',
        'Quatro cópias da lista de passivos, uma delas em outro repositório atrás de um comentário &quot;keep in sync&quot;.'),
       ('No hand-kept type list remains. The gate, the logging and the worker read one source.',
        'Nenhuma lista de tipos mantida à mão sobra. O gate, o log e o worker leem uma fonte só.'))},

{'n':'3','title':('A drift spec, and the end state as a test','Uma spec de drift, e o estado final como teste'),
 'loc':'front/src/util/nodeTypes.tsx · node-type-metadata.ts',
 'purpose':('Make the next unregistered type fail a test instead of quietly keeping flows on the back&#x27;s loop.',
            'Fazer o próximo tipo sem registro reprovar um teste em vez de prender fluxos em silêncio no laço do back.'),
 'body':('<p><strong>The rule that prevents the next gap.</strong> A drift spec fails when a type exists in the front&#x27;s <code>nodeTypes.tsx</code> '
         'or in <code>node-type-metadata.ts</code> without a registry entry, and when any derived list disagrees with the registry.</p>'
         '<p><strong>The end state as a test.</strong> An expected-failure test (<code>it.failing</code>) asserts that no type is classed <code>back</code>. '
         'It fails today by design; <code>C2</code> turns it into a plain test when the last back type leaves.</p>',
         '<p><strong>A regra que impede a próxima lacuna.</strong> Uma spec de drift falha quando um tipo existe no <code>nodeTypes.tsx</code> do front '
         'ou no <code>node-type-metadata.ts</code> sem entrada no registro, e quando alguma lista derivada discorda do registro.</p>'
         '<p><strong>O estado final como teste.</strong> Um teste de falha esperada (<code>it.failing</code>) afirma que nenhum tipo tem classe <code>back</code>. '
         'Ele falha hoje de propósito; a <code>C2</code> o transforma em teste comum quando o último tipo do back sair.</p>'),
 'callouts':[('mig',('Out of scope','Fora de escopo'),
   ('<p>Moving any execution. <strong>This task is classification only.</strong></p>',
    '<p>Mover qualquer execução. <strong>Esta task é só classificação.</strong></p>'))]},
]

VERIF = [
 (True, ('Negative control — see the drift spec go red','Controle negativo — veja a spec de drift ficar vermelha'),
  ('Add a type to the front list without a registry entry and watch the drift spec go red. '
   'Remove a derived list&#x27;s import and restore a literal copy, and watch it go red again.',
   'Adicione um tipo à lista do front sem entrada no registro e veja a spec de drift ficar vermelha. '
   'Remova o import de uma lista derivada e restaure uma cópia literal, e veja a spec ficar vermelha de novo.')),
 (True, ('Measure before refusing','Medir antes de recusar'),
  ('Per PLAN §3.3.2: classify every stored production flow as eligible or ineligible for B4&#x27;s gate <strong>before and after</strong> this task. '
   'Every flow that stays ineligible names the type that keeps it there, and that type has a task.',
   'Conforme o PLAN §3.3.2: classifique todo fluxo de produção armazenado como elegível ou inelegível para o gate da B4 <strong>antes e depois</strong> desta task. '
   'Todo fluxo que continua inelegível nomeia o tipo que o prende ali, e esse tipo tem uma task.')),
]

DONE = ('Every canvas and MCP type has an <code>execution</code> class; no hand-kept type list remains; the drift spec is green and '
        '<strong>has been seen red</strong>; the before/after eligibility counts are recorded in the task file; and the workspace '
        '<code>CLAUDE.md</code> checklist &quot;Adding or changing a node type&quot; names the <code>execution</code> field.',
        'Todo tipo de canvas e do MCP tem uma classe <code>execution</code>; nenhuma lista de tipos mantida à mão sobra; a spec de drift está verde e '
        '<strong>já foi vista vermelha</strong>; as contagens de elegibilidade de antes e depois estão registradas no arquivo da task; e o checklist '
        '&quot;Adding or changing a node type&quot; do <code>CLAUDE.md</code> do workspace cita o campo <code>execution</code>.')

FILES = [('back/src/shared/node-dispatch/node-dispatch-registry.ts', False),
         ('back/src/shared/node-dispatch/node-dispatch-contract.json', False),
         ('back/src/app-api/flux/engine-selector.ts', False),
         ('back/src/app-api/flux/prefetch/is-non-executable.ts', False),
         ('back/src/app-api/flux/flux.service.ts (the logging copy)', False),
         ('back/src/app-api/flux/node-input-projection.ts', False),
         ('worker process-flow.workflow.ts + the ported projection list', False),
         ('front/src/util/nodeTypes.tsx (read)', False),
         ('back/src/app-mcp/node-types/node-type-metadata.ts (read)', False),
         ('CLAUDE.md (node-type checklist)', False)]

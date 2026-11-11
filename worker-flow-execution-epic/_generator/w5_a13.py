# -*- coding: utf-8 -*-
TITLE = ('The Data Output as the workflow&#x27;s sink', 'O Data Output como destino final do workflow')

GOAL = ('A run under the <code>B4</code> workflow produces the same Data Output value, API reply, chatbot answer and delivery as a run on the back&#x27;s loop.',
        'Um run sob o workflow da <code>B4</code> produz o mesmo valor de Data Output, a mesma resposta de API, a mesma resposta do chatbot e a mesma entrega que um run no laço do back.')

GLANCE = [
 ('crit', ('Blocks','Bloqueia'), ('B4 flag on in production','Flag da B4 ligada em produção'),
  ('A workflow run has no reply without this task, so the flag cannot be turned on in production before it.',
   'Sem esta task um run de workflow não tem resposta, então a flag não pode ser ligada em produção antes dela.')),
 ('dep', ('Depends on','Depende de'), ('A9 · B4 · A11','A9 · B4 · A11'),
  ('<code>A9</code> moved delivery into the worker, <code>B4</code> is the workflow it plugs into, and <code>A11</code> classifies the registry entry this task flips.',
   'A <code>A9</code> levou a entrega para o worker, a <code>B4</code> é o workflow onde ela se encaixa, e a <code>A11</code> classifica a entrada de registro que esta task vira.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Second in the wave: after <code>A11</code>, and before the <code>B4</code> flag goes on in production.',
   'Segunda da onda: depois da <code>A11</code>, e antes de a flag da <code>B4</code> ser ligada em produção.')),
 ('ship', ('Shape','Formato'), ('One shared builder','Um construtor compartilhado'),
  ('Added on 2026-10-23 from the node coverage audit. Both engines call the same code; nothing changes for the user.',
   'Adicionada em 2026-10-23 a partir da auditoria de cobertura de nodes. Os dois motores chamam o mesmo código; nada muda para o usuário.')),
]

LEDE = (
 '<p>Today the back builds the Data Output&#x27;s value from its producers, in memory, and that value is what the API reply, the chatbot answer and '
 '<code>A9</code>&#x27;s delivery read. The worker enum has <code>OUTPUT</code> with no activity, so <strong>a workflow run has no sink</strong>.</p>'
 '<p>The design, decided on 2026-11-09 against the code: <strong>the worker writes the Data Output\'s row</strong> and the back\'s end-of-run code, which already builds the reply, the chatbot answer and the delivery after a workflow run, reads it unchanged (A13-D1). The first draft made <code>deliverRunOutputs</code> the workflow\'s last step; A13-D2 dropped it, because delivery needs the reply and the callback URL, which only the back has.</p>',
 '<p>Hoje o back monta o valor do Data Output a partir dos seus produtores, em memória, e é esse valor que a resposta de API, a resposta do chatbot e a '
 'entrega da <code>A9</code> leem. O enum do worker tem <code>OUTPUT</code> sem activity, então <strong>um run de workflow não tem destino final</strong>.</p>'
 '<p>O desenho, decidido em 09/11/2026 contra o código: <strong>o worker grava a linha do Data Output</strong> e o código de fim de run do back, que já monta a resposta, a resposta do chatbot e a entrega depois de um run de workflow, a lê sem mudança (A13-D1). O primeiro rascunho fazia do <code>deliverRunOutputs</code> o último passo do workflow; a A13-D2 o descartou, porque a entrega precisa da resposta e da URL de callback, que só o back tem.</p>')

TABLE = dict(
 head=[('Who reads the Data Output','Quem lê o Data Output'),('On the back&#x27;s loop','No laço do back'),('Under the workflow, before A13','Sob o workflow, antes da A13'),('After A13','Depois da A13')],
 rows=[
  [('The API reply','A resposta de API'),
   ('The value built in memory from the producers','O valor montado em memória a partir dos produtores'),
   {'t':('Empty or missing','Vazia ou ausente'),'pill':'weak'},
   {'t':('Byte for byte the same','Idêntica byte a byte'),'pill':'ok'}],
  [('The chatbot answer','A resposta do chatbot'),
   ('The same in-memory value','O mesmo valor em memória'),
   {'t':('No value to read','Nenhum valor para ler'),'pill':'weak'},
   {'t':('Matches across a corpus','Igual em um corpus'),'pill':'ok'}],
  [('<code>A9</code>&#x27;s delivery','A entrega da <code>A9</code>'),
   ('Called by the back&#x27;s loop','Chamada pelo laço do back'),
   {'t':('No step calls it','Nenhum passo a chama'),'pill':'weak'},
   {'t':('The workflow&#x27;s last step, once per run','O último passo do workflow, uma vez por run'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('The worker writes the Data Output row','O worker grava a linha do Data Output'),
 'loc':'worker node-activities.ts (outputObjectNode)',
 'purpose':('A new <code>outputObjectNode</code> activity runs through the <code>B3b</code> projection and writes the row the back&#x27;s loop writes (A13-D1).',
            'Uma activity nova <code>outputObjectNode</code> roda pela projeção da <code>B3b</code> e grava a linha que o laço do back grava (A13-D1).'),
 'body':('<p>The row holds the <code>textData</code> array, and the three text joins stay in the back (A13-D4). The activity writes only its run row, never the live canvas row, so a projected value cannot reach the next run (A13-D5). The ids of the upstream executions it read go to <code>metadata.sourceExecIds</code>, recorded for every node the resolver reads (A13-D6).</p>',
         '<p>A linha guarda o array <code>textData</code>, e os três joins de texto continuam no back (A13-D4). A activity grava só a linha do run, nunca a linha viva do canvas, então um valor projetado não chega ao próximo run (A13-D5). Os ids das execuções de origem que ela leu vão para <code>metadata.sourceExecIds</code>, registrado para todo nó que o resolver lê (A13-D6).</p>'),
 'ba':(('The workflow throws &quot;Node type outputObjectNode not supported&quot;.',
        'O workflow lança &quot;Node type outputObjectNode not supported&quot;.'),
       ('The workflow writes the row and the back&#x27;s end of run reads it.',
        'O workflow grava a linha e o fim de run do back a lê.'))},

{'n':'2','title':('Delivery stays a workflow the back starts','A entrega continua um workflow que o back inicia'),
 'loc':'back flux.service.ts (settleRunOutputs)',
 'purpose':('Both engines reach the same end-of-run code; delivery is not the workflow&#x27;s last step (A13-D2).',
            'Os dois motores chegam ao mesmo código de fim de run; a entrega não é o último passo do workflow (A13-D2).'),
 'body':('<p>Batch rows reach <code>processFlow</code> without that code, and since <code>B7</code> they stored only the workflow status. A13-D7 restores the earlier row: after each row the worker asks the back to run the shared end of run, writes the reply into the row and starts one delivery, callback only. Delivery for scheduled runs stays out of scope; <code>E4b</code> picks it up.</p>',
         '<p>As linhas de lote chegam ao <code>processFlow</code> sem esse código, e desde a <code>B7</code> guardavam só o status do workflow. A A13-D7 restaura a linha anterior: depois de cada linha o worker pede ao back que rode o fim de run compartilhado, grava a resposta na linha e inicia uma entrega, só callback. A entrega dos runs agendados continua fora de escopo; a <code>E4b</code> assume.</p>')},

{'n':'3','title':('The gate accepts the sink','O gate aceita o sink'),
 'loc':('the A1 registry','o registro da A1'),
 'purpose':('The class stays <code>sink</code> and B4&#x27;s gate accepts it (A13-D3).',
            'A classe continua <code>sink</code> e o gate da B4 a aceita (A13-D3).'),
 'body':('<p>The registry entry loses <code>handoffOwner</code>, A11&#x27;s <code>it.failing</code> becomes a plain test and the contract JSON is regenerated. <code>prefetchSafe</code> stays <code>false</code>.</p>',
         '<p>A entrada no registro perde o <code>handoffOwner</code>, o <code>it.failing</code> da A11 vira um teste comum e o JSON do contrato é regenerado. <code>prefetchSafe</code> continua <code>false</code>.</p>')},
]

VERIF = [
 (True, ('Negative control — record the empty reply first','Controle negativo — registre a resposta vazia primeiro'),
  ('Before this task, run one stored API flow under the workflow and record the empty or missing reply. After it, the reply matches the back&#x27;s loop <strong>byte for byte</strong>.',
   'Antes desta task, rode um fluxo de API armazenado sob o workflow e registre a resposta vazia ou ausente. Depois dela, a resposta é igual à do laço do back <strong>byte a byte</strong>.')),
 (False, ('Parity over a corpus','Paridade em um corpus'),
  ('The API reply and the chatbot answer match between the two engines.',
   'A resposta de API e a resposta do chatbot são iguais nos dois motores.')),
 (False, ('One delivery per run','Uma entrega por run'),
  ('A delivery fires once per run under the workflow, including after a retried last step.',
   'Uma entrega dispara uma vez por run sob o workflow, inclusive depois de um último passo repetido.')),
]

DONE = ('Workflow runs return the same reply and deliver the same outputs as the back&#x27;s loop; the registry entry is flipped; '
        '<strong>no back-only code builds the Data Output value</strong>.',
        'Os runs de workflow devolvem a mesma resposta e entregam as mesmas saídas que o laço do back; a entrada no registro foi virada; '
        '<strong>nenhum código exclusivo do back monta o valor do Data Output</strong>.')

FILES = [('back/src/app-api/flux/flux.service.ts (the Data Output assembly, deliverRunOutputs caller)', False),
         ('worker process-flow.workflow.ts', False),
         ('worker node-activities.ts (OUTPUT)', False),
         ('the A1 registry', False)]

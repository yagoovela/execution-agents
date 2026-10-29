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
 '<p><code>A9</code> moved email and callback delivery into the worker and handed the rest to <code>B4</code>: <em>“when B4 lands, '
 '<code>deliverRunOutputs</code> becomes its last step”</em>. <strong><code>B4</code>&#x27;s spec never picked it up.</strong> This task owns that hand-off.</p>',
 '<p>Hoje o back monta o valor do Data Output a partir dos seus produtores, em memória, e é esse valor que a resposta de API, a resposta do chatbot e a '
 'entrega da <code>A9</code> leem. O enum do worker tem <code>OUTPUT</code> sem activity, então <strong>um run de workflow não tem destino final</strong>.</p>'
 '<p>A <code>A9</code> levou a entrega de email e de callback para o worker e passou o resto para a <code>B4</code>: <em>“quando a B4 chegar, o '
 '<code>deliverRunOutputs</code> vira o último passo dela”</em>. <strong>A spec da <code>B4</code> nunca assumiu isso.</strong> Esta task é dona dessa passagem.</p>')

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
{'n':'1','title':('Build the value from stored rows','Montar o valor a partir das linhas armazenadas'),
 'loc':'worker node-activities.ts (OUTPUT)',
 'purpose':('Build the Data Output&#x27;s value from its upstreams&#x27; <code>node_executions</code> rows, by reference, as <code>B3b</code> does for every other consumer.',
            'Montar o valor do Data Output a partir das linhas de <code>node_executions</code> dos nós de origem, por referência, como a <code>B3b</code> faz para todo outro consumidor.'),
 'body':('<p>The builder also <strong>records which executions it read</strong>, so a reply can be traced back to the rows that produced it.</p>',
         '<p>O construtor também <strong>registra quais execuções leu</strong>, para que uma resposta possa ser rastreada até as linhas que a produziram.</p>'),
 'ba':(('The back assembles the value from its producers in memory; a workflow run has no equivalent.',
        'O back monta o valor a partir dos produtores em memória; um run de workflow não tem equivalente.'),
       ('The value comes from stored executions, by reference, and the builder notes which ones it used.',
        'O valor vem de execuções armazenadas, por referência, e o construtor anota quais usou.'))},

{'n':'2','title':('Delivery as the workflow&#x27;s last step','A entrega como último passo do workflow'),
 'loc':'worker process-flow.workflow.ts',
 'purpose':('Make <code>deliverRunOutputs</code> the workflow&#x27;s last step, and keep the back&#x27;s loop calling the same code.',
            'Fazer do <code>deliverRunOutputs</code> o último passo do workflow, e manter o laço do back chamando o mesmo código.'),
 'body':('<p>A delivery has to fire <strong>once per run</strong> under the workflow, including after the last step is retried.</p>',
         '<p>Uma entrega precisa disparar <strong>uma vez por run</strong> sob o workflow, inclusive depois de o último passo ser repetido.</p>'),
 'ba':(('Only the back&#x27;s loop calls <code>deliverRunOutputs</code>.',
        'Só o laço do back chama o <code>deliverRunOutputs</code>.'),
       ('Both engines call the same code; the workflow calls it as its last step.',
        'Os dois motores chamam o mesmo código; o workflow o chama como seu último passo.')),
 'callouts':[('mig',('Out of scope','Fora de escopo'),
   ('<p>Changing the reply shape, the delivery channels, or <code>A9</code>&#x27;s retry policies.</p>',
    '<p>Mudar o formato da resposta, os canais de entrega, ou as políticas de retry da <code>A9</code>.</p>'))]},

{'n':'3','title':('Flip the registry entry','Virar a entrada no registro'),
 'loc':('the A1 registry','o registro da A1'),
 'purpose':('Flip <code>outputObjectNode</code>&#x27;s registry entry once both paths use the same builder.',
            'Virar a entrada de <code>outputObjectNode</code> no registro quando os dois caminhos usarem o mesmo construtor.'),
 'body':('<p>The order matters: the entry flips only after the back&#x27;s loop and the workflow share the builder, so <strong>no back-only code builds the Data Output value</strong>.</p>',
         '<p>A ordem importa: a entrada só vira depois que o laço do back e o workflow compartilham o construtor, de modo que <strong>nenhum código exclusivo do back monta o valor do Data Output</strong>.</p>'),
 'callouts':[('decide',('Added 2026-10-28','Adicionado em 2026-10-28'),
   ('<p>A11 classes <code>outputObjectNode</code> as <code>execution: &#x27;sink&#x27;</code>. This task makes B4&#x27;s gate accept <code>sink</code> and turns '
    'A11&#x27;s <code>it.failing</code> &quot;the gate accepts a flow that holds a <code>sink</code>&quot; into a plain test. The class stays <code>sink</code>.</p>',
    '<p>A A11 dá ao <code>outputObjectNode</code> a classe <code>execution: &#x27;sink&#x27;</code>. Esta task faz o gate da B4 aceitar <code>sink</code> e transforma '
    'o <code>it.failing</code> da A11 sobre o gate aceitar um fluxo com um <code>sink</code> num teste comum. A classe continua <code>sink</code>.</p>'))]},
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

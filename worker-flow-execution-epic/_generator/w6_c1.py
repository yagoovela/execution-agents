# -*- coding: utf-8 -*-
TITLE = ('Retire the inline paths and the cross-node writes', 'Aposentar os caminhos inline e as escritas cross-node')

GOAL = ('Delete what the migration replaced, so <b>the back stops being a second implementation</b>.',
        'Apagar o que a migração substituiu, para que <b>o back deixe de ser uma segunda implementação</b>.')

GLANCE = [
 ('crit', ('Severity','Severidade'), ('Critical — R1','Crítica — R1'),
  ('While both implementations exist, a flag misconfiguration means <strong>double execution</strong>: a duplicated Stripe charge, a duplicated Slack message.',
   'Enquanto as duas implementações existirem, uma flag mal configurada significa <strong>dupla execução</strong>: uma cobrança Stripe duplicada, uma mensagem Slack duplicada.')),
 ('dep', ('Depends on','Depende de'), ('Each node&#x27;s A-track task','A task de trilha A de cada node'),
  ('<strong>This is not a sweep at the end.</strong> Each twin is deleted as part of proving that node, while the behaviour is fresh. One card, in Wave 6, for the once-only half; the per-node deletions are a Done-when line of each A-track card (PLAN §3.1).',
   '<strong>Isto não é uma varredura no fim.</strong> Cada gêmeo é apagado como parte de provar aquele node, enquanto o comportamento está fresco. Um card, na onda 6, para a metade que só acontece uma vez; as deleções por node são uma linha de Done de cada card da trilha A (PLAN §3.1).')),
 ('wave', ('Wave','Onda'), ('Wave 6','Onda 6'),
  ('The per-node half rides Wave 3, node by node. Only the <strong>cross-node writes</strong> wait for the last inline caller to leave.',
   'A metade por node anda na onda 3, node a node. Só as <strong>escritas cross-node</strong> esperam o último chamador inline sair.')),
 ('ship', ('Shape','Formato'), ('A shared procedure','Um procedimento compartilhado'),
  ('This file is the procedure the A-track tasks follow, plus the two pieces that only make sense once.',
   'Este arquivo é o procedimento que as tasks da trilha A seguem, mais as duas peças que só fazem sentido uma vez.')),
]

LEDE = (
 '<p><strong>Two implementations of one node do not coexist neutrally.</strong> They diverge, and the divergence is silent — someone fixes a bug in the '
 'inline handler that the worker module still has. Worse, while both exist, a flag misconfiguration means <strong>double execution</strong> '
 '(<code>PLAN §6</code>, <code>R1</code>).</p>'
 '<p><code>flux.service.ts</code> is around <strong>9,500 lines</strong>. A migration that only adds is a migration that made the file worse — which is why '
 'deletion is part of the migration and not cleanup that happens afterwards.</p>',
 '<p><strong>Duas implementações de um mesmo node não convivem de forma neutra.</strong> Elas divergem, e a divergência é silenciosa — alguém corrige um bug no '
 'handler inline que o módulo do worker continua tendo. Pior: enquanto as duas existirem, uma flag mal configurada significa <strong>dupla execução</strong> '
 '(<code>PLAN §6</code>, <code>R1</code>).</p>'
 '<p>O <code>flux.service.ts</code> tem cerca de <strong>9.500 linhas</strong>. Uma migração que só soma é uma migração que piorou o arquivo — por isso '
 'apagar faz parte da migração e não é uma limpeza que acontece depois.</p>')

TABLE = dict(
 head=[('What gets deleted','O que é apagado'),('Who deletes it','Quem apaga'),('When','Quando')],
 rows=[
  [('The inline handler in <code>flux.service.ts</code> and its dispatch branch','O handler inline no <code>flux.service.ts</code> e seu ramo de dispatch'),
   {'t':('The node&#x27;s A-track task','A task de trilha A do node')},
   {'t':('As that node is proved — not commented out, not left behind a dead flag','Quando aquele node é provado — não comentado, não deixado atrás de uma flag morta'),'pill':'ok'}],
  [('Anything only that handler used','Tudo o que só aquele handler usava'),
   {'t':('The node&#x27;s A-track task','A task de trilha A do node')},
   {'t':('With the handler, in the same PR','Junto do handler, no mesmo PR'),'pill':'ok'}],
  [('The <code>hasInlineTwin</code> flag on the <code>A1</code> registry entry','A marca <code>hasInlineTwin</code> na entrada do registro da <code>A1</code>'),
   {'t':('The node&#x27;s A-track task','A task de trilha A do node')},
   {'t':('With the handler — the registry is what everything else reads','Junto do handler — o registro é o que todo o resto lê'),'pill':'ok'}],
  [('A <code>modifyData</code> call site','Um ponto de chamada do <code>modifyData</code>'),
   {'t':('C1','C1')},
   {'t':('When that call site&#x27;s <strong>last live inline caller</strong> is gone','Quando o <strong>último chamador inline vivo</strong> daquele ponto sumir'),'pill':'weak'}],
  [('<code>addConnectToNodes</code> on the run path','O <code>addConnectToNodes</code> no caminho de run'),
   {'t':('C1','C1')},
   {'t':('When the last executable inline node is migrated — <strong>Wave 6</strong>','Quando o último node executável inline for migrado — <strong>onda 6</strong>'),'pill':'weak'}],
 ])

PARTS = [
{'n':'1','title':('The per-node procedure','O procedimento por node'),
 'loc':'back/src/app-api/flux/flux.service.ts',
 'purpose':('Three steps, executed by each A-track task as its node lands — not by a cleanup task months later.',
            'Três passos, executados por cada task da trilha A quando o node dela entra — não por uma task de limpeza meses depois.'),
 'body':('<p>The procedure is short and it is deliberately owned by the node&#x27;s own task, because <strong>the person who just proved the behaviour is the '
         'only person who knows what was safe to remove</strong>.</p>',
         '<p>O procedimento é curto e é deliberadamente de responsabilidade da task do próprio node, porque <strong>quem acabou de provar o comportamento é a '
         'única pessoa que sabe o que era seguro remover</strong>.</p>'),
 'list':[('The inline handler and its dispatch branch are <strong>deleted</strong> — not commented out, and not left behind a dead flag.',
          'O handler inline e seu ramo de dispatch são <strong>apagados</strong> — não comentados, e não deixados atrás de uma flag morta.'),
         ('Anything only that handler used goes with it. <code>flux.service.ts</code> is around 9,500 lines; a migration that only adds made the file worse.',
          'Tudo o que só aquele handler usava vai junto. O <code>flux.service.ts</code> tem cerca de 9.500 linhas; uma migração que só soma piorou o arquivo.'),
         ('The <code>A1</code> registry entry loses <code>hasInlineTwin</code>, so the one authoritative answer to “does this node have a second implementation?” stays true.',
          'A entrada do registro da <code>A1</code> perde o <code>hasInlineTwin</code>, para que a única resposta autoritativa a “este node tem uma segunda implementação?” continue verdadeira.')],
 'ba':(('Every migrated node has a twin in the back. They are equal until one of them is fixed, and then only one of them is fixed.',
        'Todo node migrado tem um gêmeo no back. Eles são iguais até um deles ser corrigido, e aí só um deles fica corrigido.'),
       ('The migrated node has <strong>one implementation</strong>, and the flag-off path fails loudly instead of quietly doing nothing.',
        'O node migrado tem <strong>uma implementação</strong>, e o caminho com a flag desligada falha alto em vez de silenciosamente não fazer nada.')),
 'callouts':[('mig',('Deleting late is not the safe option','Apagar tarde não é a opção segura'),
   ('<p>The instinct is to keep the inline handler “just in case”. That instinct is what creates <code>R1</code>: two live paths, one flag between them, '
    'and a duplicated side effect the first time the flag is wrong.</p>',
    '<p>O instinto é manter o handler inline “por via das dúvidas”. É esse instinto que cria o <code>R1</code>: dois caminhos vivos, uma flag entre eles, '
    'e um efeito colateral duplicado na primeira vez que a flag estiver errada.</p>'))]},

{'n':'2','title':('The cross-node writes — the load-bearing half','As escritas cross-node — a metade estrutural'),
 'loc':'back/src/app-api/folw/contants.ts',
 'purpose':('Stop a second writer from merging into a row someone else owns — the mechanism that makes mixed-mode parallelism unsafe.',
            'Impedir que um segundo escritor faça merge numa linha que é de outro — o mecanismo que torna o paralelismo em modo misto inseguro.'),
 'body':('<p>Every inline handler ends with <code>addConnectToNodes</code> (<code>folw/contants.ts</code>), which calls <code>modifyData</code> '
         ' to merge the producer&#x27;s output into the <strong>target</strong> node&#x27;s data. '
         'That is the mechanism that makes mixed-mode parallelism unsafe (analysis §7.4b), and it is <strong>the reason <code>B5</code> needs its gate</strong>.</p>'
         '<p>Once a node runs in the worker, its output reaches downstream nodes through <code>persistNodeSuccess</code> writing its <strong>own</strong> row. '
         'The cross-node write is then not merely redundant — <strong>it is a second writer on a row someone else owns</strong>.</p>',
         '<p>Todo handler inline termina com <code>addConnectToNodes</code> (<code>folw/contants.ts</code>), que chama o <code>modifyData</code> '
         ' para fazer merge da saída do produtor no dado do node <strong>alvo</strong>. '
         'É esse o mecanismo que torna o paralelismo em modo misto inseguro (análise §7.4b), e é <strong>a razão de a <code>B5</code> precisar do gate dela</strong>.</p>'
         '<p>Quando um node passa a rodar no worker, a saída dele chega aos nodes a jusante pelo <code>persistNodeSuccess</code> escrevendo na <strong>própria</strong> linha. '
         'A escrita cross-node então não é apenas redundante — <strong>ela é um segundo escritor numa linha que é de outro</strong>.</p>'),
 'body2':('<p><strong>Out of scope:</strong> removing <code>addConnectToNodes</code> while any executable node type still runs inline. '
          '<strong>It is correct for those.</strong> This task removes it <em>path by path</em>, as each path&#x27;s last inline node leaves — which is why '
          'the tracking in Part 3 is the actual work here, not the deletion itself.</p>',
          '<p><strong>Fora de escopo:</strong> remover o <code>addConnectToNodes</code> enquanto qualquer tipo de node executável ainda rodar inline. '
          '<strong>Para esses, ele está correto.</strong> Esta task o remove <em>caminho a caminho</em>, conforme o último node inline de cada caminho sai — por isso '
          'o rastreamento da Parte 3 é o trabalho de verdade aqui, e não a deleção em si.</p>'),
 'ba':(('A producer&#x27;s output is merged straight into the <strong>target</strong> node&#x27;s data. Safe only because the engine is sequential and holds the whole node array in memory.',
        'A saída de um produtor é mesclada direto no dado do node <strong>alvo</strong>. Seguro apenas porque o motor é sequencial e mantém o array inteiro de nodes em memória.'),
       ('A node writes its <strong>own</strong> row and nothing else. Parallel siblings cannot lose each other&#x27;s writes, and <code>B5</code>&#x27;s gate can eventually be retired with the risk it guarded.',
        'Um node escreve na <strong>própria</strong> linha e em mais nada. Irmãos em paralelo não perdem a escrita um do outro, e o gate da <code>B5</code> pode um dia ser aposentado junto do risco que ele guardava.'))},

{'n':'3','title':('The end-state check is not a formality','A checagem de estado final não é formalidade'),
 'loc':('the run path · the PR description', 'o caminho do run · a descrição do PR'),
 'purpose':('Track which call sites still have a live inline caller, and treat a surviving caller as evidence that something was missed.',
            'Rastrear quais pontos de chamada ainda têm um chamador inline vivo, e tratar um chamador sobrevivente como evidência de que algo passou batido.'),
 'body':('<p>Two of the three steps are bookkeeping, and the bookkeeping is what makes the deletion safe:</p>',
         '<p>Dois dos três passos são contabilidade, e é a contabilidade que torna a deleção segura:</p>'),
 'list':[('Per node, as its A-task completes: delete the handler, the dispatch and the dead helpers.',
          'Por node, quando a task de trilha A dele conclui: apague o handler, o dispatch e os helpers mortos.'),
         ('Track which call sites of <code>modifyData</code> / <code>addConnectToNodes</code> <strong>still have a live inline caller</strong>. '
          'When a call site&#x27;s last caller is gone, delete the call site.',
          'Rastreie quais pontos de chamada do <code>modifyData</code> / <code>addConnectToNodes</code> <strong>ainda têm um chamador inline vivo</strong>. '
          'Quando o último chamador de um ponto sumir, apague o ponto.'),
         ('When the last executable inline node is migrated, <code>addConnectToNodes</code> should have <strong>no callers on the run path</strong>. '
          'If it still does, <strong>something was missed — that is the check, not a formality</strong>.',
          'Quando o último node executável inline for migrado, o <code>addConnectToNodes</code> não deve ter <strong>nenhum chamador no caminho de run</strong>. '
          'Se ainda tiver, <strong>algo passou batido — essa é a checagem, não uma formalidade</strong>.')],
 'body2':('<p>And the reduction gets <strong>stated in the PR</strong>. “<code>flux.service.ts</code> is materially smaller” is a claim with a number behind it, '
          'and writing the number down is what stops the next migration from only adding.</p>',
          '<p>E a redução é <strong>declarada no PR</strong>. “O <code>flux.service.ts</code> ficou materialmente menor” é uma afirmação com um número por trás, '
          'e escrever o número é o que impede a próxima migração de apenas somar.</p>'),
 'ba':(('Nobody can say how many live inline callers a given helper has, so nobody can safely delete it — and it stays forever.',
        'Ninguém sabe dizer quantos chamadores inline vivos um helper tem, então ninguém consegue apagá-lo com segurança — e ele fica para sempre.'),
       ('Each call site has a known set of live callers, the set empties as nodes migrate, and an empty set is the signal to delete.',
        'Cada ponto de chamada tem um conjunto conhecido de chamadores vivos, o conjunto esvazia conforme os nodes migram, e um conjunto vazio é o sinal para apagar.'))},
]

VERIF = [
 (True, ('Negative control — prove the path first, then break it','Controle negativo — prove o caminho primeiro, e depois quebre'),
  ('<strong>Before</strong> deleting a handler, re-point the flag at the inline path and confirm the node still works. Then delete, and confirm the flag-off path '
   'now fails <strong>loudly</strong> rather than silently doing nothing. <strong>A deleted path that fails silently is indistinguishable in production from a '
   'node that produced empty output.</strong>',
   '<strong>Antes</strong> de apagar um handler, aponte a flag de volta para o caminho inline e confirme que o node ainda funciona. Depois apague, e confirme que o caminho '
   'com a flag desligada agora falha <strong>alto</strong> em vez de silenciosamente não fazer nada. <strong>Um caminho apagado que falha em silêncio é, em produção, '
   'indistinguível de um node que produziu saída vazia.</strong>')),
 (True, ('Double-execution guard — assert it, do not eyeball it','Guarda de dupla execução — afirme, não olhe'),
  ('For each migrated node, assert with a log or a counter that <strong>exactly one execution occurred per dispatch</strong>. '
   'This is <code>R1</code>, and it is the failure that shows up as a duplicated charge rather than as an error.',
   'Para cada node migrado, afirme com um log ou um contador que <strong>exatamente uma execução ocorreu por dispatch</strong>. '
   'Este é o <code>R1</code>, e é a falha que aparece como uma cobrança duplicada em vez de como um erro.')),
 (False, ('Diff downstream inputs after each call-site removal','Diferença nas entradas a jusante após cada remoção'),
  ('After each <code>modifyData</code> call-site removal, run the flows that reach it and <strong>diff downstream node inputs against a pre-change run</strong>. '
   'The write being removed is the one that fed those inputs, so this is where a silent loss would appear.',
   'Após cada remoção de ponto de chamada do <code>modifyData</code>, rode os fluxos que passam por ele e <strong>compare as entradas dos nodes a jusante contra um run anterior à mudança</strong>. '
   'A escrita removida é justamente a que alimentava essas entradas, então é aqui que uma perda silenciosa apareceria.')),
]

DONE = ('<strong>No executable node type has two implementations</strong>; <code>addConnectToNodes</code> has <strong>no callers on the run path</strong>; '
        'and <code>flux.service.ts</code> is materially smaller, with the reduction stated in the PR.',
        '<strong>Nenhum tipo de node executável tem duas implementações</strong>; o <code>addConnectToNodes</code> não tem <strong>nenhum chamador no caminho de run</strong>; '
        'e o <code>flux.service.ts</code> está materialmente menor, com a redução declarada no PR.')

FILES = [('back/src/app-api/flux/flux.service.ts (all inline handlers)', False),
         ('back/src/app-api/folw/contants.ts (addConnectToNodes · modifyData)', False),
         ('the A1 registry', False)]

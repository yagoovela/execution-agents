# -*- coding: utf-8 -*-
TITLE = ('Small Memory and chat under the workflow engine, without moving a node',
         'Small Memory e chat no motor de workflow, sem mover um node')

GOAL = ('Flows with Small Memory (<code>fluxObject</code>) and chat history run on the B4 workflow engine with <b>the same results as on the back&#x27;s loop</b>. No node moves to the worker.',
        'Fluxos com Small Memory (<code>fluxObject</code>) e histórico de chat rodam no motor de workflow da B4 com <b>os mesmos resultados do laço do back</b>. Nenhum node vai para o worker.')

GLANCE = [
 ('crit', ('What it unblocks','O que destrava'), ('Deleting the back&#x27;s loop','Apagar o laço do back'),
  ('Today B4&#x27;s gate refuses every flow with a <code>fluxObject</code>, so those flows stay on the back&#x27;s loop. If nothing changes, the loop can never be deleted (Wave 6).',
   'Hoje o gate da B4 recusa todo fluxo com um <code>fluxObject</code>, e esses fluxos ficam no laço do back. Se nada mudar, o laço nunca poderá ser apagado (onda 6).')),
 ('dep', ('Depends on','Depende de'), ('B3b.1 · B4 · A7','B3b.1 · B4 · A7'),
  ('B3b.1 for the run seed snapshot, B4 for the workflow engine and its per-node events, A7 for the read rule: a consumer reads the writes that completed before it was scheduled.',
   'B3b.1 pelo snapshot semente do run, B4 pelo motor de workflow e seus eventos por node, A7 pela regra de leitura: um consumidor lê as escritas concluídas antes de ser agendado.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Added and rescoped on 2026-10-23. Inside the wave it runs after A7 and before B5.',
   'Adicionada e reescopada em 2026-10-23. Dentro da onda, roda depois da A7 e antes da B5.')),
 ('ship', ('Shape','Formato'), ('Three parts, no worker module','Três partes, nenhum módulo no worker'),
  ('Only the second part needs new logic. <strong>No new write, no callback, no lock.</strong>',
   'Só a segunda parte precisa de lógica nova. <strong>Nenhuma escrita nova, nenhum callback, nenhum lock.</strong>')),
]

LEDE = (
 '<p>Small Memory does not execute. It is a container that the edge projection writes into when it is the target of an edge, and reads from when it is '
 'the source (<code>edge-projection.ts</code>, the <code>fluxObject</code> branches). On the back&#x27;s loop that state lives in the loop&#x27;s memory: a node that '
 'reads Small Memory sees what earlier nodes in the same run added. The back also loads the chat history before the loop and persists the memory and the '
 'assistant&#x27;s answer around it.</p>'
 '<p>The workflow engine has no process that holds a run&#x27;s memory; each node runs on its own. Today the gap is hidden: <code>fluxObject</code> has no registry '
 'entry, so B4&#x27;s gate refuses those flows. <strong>PLAN §8 called <code>fluxObject</code> configuration-time. That was wrong; this task corrects the consequence.</strong></p>',
 '<p>A Small Memory não executa. É um contêiner em que a projeção de arestas escreve quando ele é o alvo de uma aresta, e de onde lê quando ele é a '
 'origem (<code>edge-projection.ts</code>, os ramos de <code>fluxObject</code>). No laço do back esse estado vive na memória do laço: um node que lê a '
 'Small Memory vê o que nodes anteriores do mesmo run adicionaram. O back também carrega o histórico de chat antes do laço e persiste a memória e a '
 'resposta do assistente em volta dele.</p>'
 '<p>O motor de workflow não tem um processo que guarde a memória de um run; cada node roda sozinho. Hoje a lacuna fica escondida: o <code>fluxObject</code> '
 'não tem entrada no registro, então o gate da B4 recusa esses fluxos. <strong>O PLAN §8 chamou o <code>fluxObject</code> de tipo de configuração. Isso estava '
 'errado; esta task corrige a consequência.</strong></p>')

TABLE = dict(
 head=[('Piece','Peça'),('On the back&#x27;s loop today','No laço do back hoje'),('On the workflow engine','No motor de workflow'),('New logic','Lógica nova')],
 rows=[
  [{'t':('Chat history','Histórico de chat')},
   ('Loaded by the back before the loop','Carregado pelo back antes do laço'),
   ('Written into the run seed snapshot (B3b.1), so both engines start from the same value','Escrito no snapshot semente do run (B3b.1), e os dois motores partem do mesmo valor'),
   {'t':('No','Não'),'pill':'ok'}],
  [{'t':('Small Memory content during the run','Conteúdo da Small Memory durante o run')},
   ('Held in the loop&#x27;s memory','Guardado na memória do laço'),
   ('<strong>Derived</strong> from the seed and the stored executions of the nodes that feed it','<strong>Derivado</strong> da semente e das execuções armazenadas dos nodes que o alimentam'),
   {'t':('Yes','Sim'),'pill':'weak'}],
  [{'t':('Memory and answer persistence','Persistência da memória e da resposta')},
   ('The back persists the memory to the canvas node and appends the assistant&#x27;s answer','O back persiste a memória no node do canvas e anexa a resposta do assistente'),
   ('Still the back, driven by the B4 per-node events it already receives','Continua no back, acionado pelos eventos por node da B4 que ele já recebe'),
   {'t':('No','Não'),'pill':'ok'}],
 ])

PROSE = (
 'One call, already made. The spec was rescoped on 2026-10-23: the first draft moved chat writes into the workflow behind A7&#x27;s callback and lock.',
 'Uma decisão, já tomada. A spec foi reescopada em 2026-10-23: o primeiro rascunho levava as escritas de chat para o workflow, atrás do callback e do lock da A7.')

DEC_DERIVE = {
 'k':'decision','id':'A14-a','status':'set','open':True,
 'q':('Hold Small Memory in the workflow, or derive it from stored executions?',
      'Guardar a Small Memory no workflow, ou derivá-la das execuções armazenadas?'),
 'intro':(
  'The content of a Small Memory node at a given moment is <strong>the history at run start plus the outputs of the nodes that feed it and that completed '
  'before the reader was scheduled</strong>. Those outputs are already stored, one row per execution.',
  'O conteúdo de um node Small Memory num dado momento é <strong>o histórico no início do run mais as saídas dos nodes que o alimentam e que terminaram '
  'antes de o leitor ser agendado</strong>. Essas saídas já estão armazenadas, uma linha por execução.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Derive the content','Derivar o conteúdo'),
   'tag':('settled','decidida'),
   'how':('The worker projection rebuilds the content from the seed and the stored rows, in completion order, with the ported projection code. '
          'It uses A7&#x27;s read rule.',
          'A projeção do worker reconstrói o conteúdo a partir da semente e das linhas armazenadas, em ordem de conclusão, com o código de projeção portado. '
          'Usa a regra de leitura da A7.'),
   'pros':[('No new write, no callback, no lock','Nenhuma escrita nova, nenhum callback, nenhum lock'),
           ('A7-D3 records that A14 needs no lock for this reason','A A7-D3 registra que a A14 dispensa lock por esse motivo'),
           ('No worker module is needed','Nenhum módulo no worker é necessário')]},
  {'ltr':'B','no':True,'name':('Move chat writes into the workflow','Levar as escritas de chat para o workflow'),
   'tag':('first draft, dropped','primeiro rascunho, descartado'),
   'how':('The first draft moved chat writes into the workflow behind A7&#x27;s callback and lock.',
          'O primeiro rascunho levava as escritas de chat para o workflow, atrás do callback e do lock da A7.'),
   'cons':[('It needs a new write path, a callback and a lock that option A does not',
            'Exige um novo caminho de escrita, um callback e um lock que a opção A dispensa')]},
 ],
 'rec':(
  '<p><strong>A.</strong> Persistence stays in the back, so the editor still sees the memory grow during the run.</p>',
  '<p><strong>A.</strong> A persistência fica no back, e o editor continua vendo a memória crescer durante o run.</p>'),
}

PARTS = [
{'n':'1','title':('Chat history at run start','Histórico de chat no início do run'),
 'loc':'flux.service.ts · B3b.1',
 'purpose':('Make both engines start from the same chat history.',
            'Fazer os dois motores partirem do mesmo histórico de chat.'),
 'body':('<p>The back already loads the chat history before the loop. It now writes it into the <strong>run seed snapshot</strong> (B3b.1), '
         'so the workflow engine reads the same value the back&#x27;s loop starts from.</p>',
         '<p>O back já carrega o histórico de chat antes do laço. Agora ele o escreve no <strong>snapshot semente do run</strong> (B3b.1), '
         'e o motor de workflow lê o mesmo valor de que o laço do back parte.</p>'),
 'ba':(('The history lives only in the back&#x27;s process, before its own loop.',
        'O histórico vive só no processo do back, antes do laço dele.'),
       ('The history is in the run seed snapshot, read by either engine.',
        'O histórico está no snapshot semente do run, lido por qualquer um dos motores.'))},

{'n':'2','title':('Small Memory content, derived instead of held','Conteúdo da Small Memory, derivado em vez de guardado'),
 'loc':'project-node-input.ts · edge-projection',
 'purpose':('Rebuild what a reader sees from data that already exists.',
            'Reconstruir o que um leitor vê a partir de dados que já existem.'),
 'body':('<p>This is the only part with new logic. The worker projection (<code>project-node-input.ts</code>) rebuilds the content from the seed and '
         'the stored execution rows of the feeding nodes, <strong>in completion order</strong>, with the ported <code>edge-projection</code> code. '
         'Only the writes that completed before the reader was scheduled count, per A7&#x27;s read rule.</p>',
         '<p>Esta é a única parte com lógica nova. A projeção do worker (<code>project-node-input.ts</code>) reconstrói o conteúdo a partir da semente e '
         'das linhas de execução armazenadas dos nodes que o alimentam, <strong>em ordem de conclusão</strong>, com o código de <code>edge-projection</code> portado. '
         'Só contam as escritas concluídas antes de o leitor ser agendado, pela regra de leitura da A7.</p>'),
 'ba':(('A reader sees what earlier nodes added because one process holds the run&#x27;s memory.',
        'Um leitor vê o que nodes anteriores adicionaram porque um processo guarda a memória do run.'),
       ('A reader sees the same content because it is rebuilt from the seed and stored rows.',
        'Um leitor vê o mesmo conteúdo porque ele é reconstruído da semente e das linhas armazenadas.'))},

{'n':'3','title':('Persistence stays in the back','A persistência fica no back'),
 'loc':'flux.service.ts',
 'purpose':('Keep the editor and the chatbot seeing what they see today.',
            'Manter o editor e o chatbot vendo o que veem hoje.'),
 'body':('<p>The back persists the memory to the canvas node (<code>persistSmallMemoryEntries</code>) and appends the assistant&#x27;s answer, as today. '
         'On the workflow engine it does so from the <strong>B4 per-node events</strong> it already receives, so the editor still sees the memory grow '
         'during the run, and at run end for the answer.</p>',
         '<p>O back persiste a memória no node do canvas (<code>persistSmallMemoryEntries</code>) e anexa a resposta do assistente, como hoje. '
         'No motor de workflow ele faz isso a partir dos <strong>eventos por node da B4</strong> que já recebe, e o editor continua vendo a memória crescer '
         'durante o run, e no fim do run para a resposta.</p>'),
 'callouts':[
  ('decide',('In scope','Dentro do escopo'),
   ('<p><code>fluxObject</code> gets its registry class (<code>none</code>, through A11) and leaves <code>BACK_ONLY_PROJECTION_NODE_TYPES</code>.</p>',
    '<p>O <code>fluxObject</code> ganha sua classe no registro (<code>none</code>, via A11) e sai de <code>BACK_ONLY_PROJECTION_NODE_TYPES</code>.</p>')),
  ('decide',('Added 2026-10-28','Adicionado em 2026-10-28'),
   ('<p>A11 classes <code>fluxObject</code> as <code>execution: &#x27;state&#x27;</code>, not <code>none</code>. This task makes B4&#x27;s gate accept <code>state</code> and turns '
    'A11&#x27;s <code>it.failing</code> &quot;the gate accepts a flow that holds a <code>state</code> node&quot; into a plain test. The class stays <code>state</code>.</p>',
    '<p>A A11 dá ao <code>fluxObject</code> a classe <code>execution: &#x27;state&#x27;</code>, não <code>none</code>. Esta task faz o gate da B4 aceitar <code>state</code> e transforma '
    'o <code>it.failing</code> da A11 sobre o gate aceitar um fluxo com um node <code>state</code> num teste comum. A classe continua <code>state</code>.</p>')),
  ('mig',('Out of scope','Fora de escopo'),
   ('<p>Moving any node to the worker. Changing chat semantics, session keys or what the chatbot shows. '
    'Two overlapping chat turns on one session can still overwrite each other, as today; fixing that is a separate decision.</p>',
    '<p>Mover qualquer node para o worker. Mudar a semântica do chat, as chaves de sessão ou o que o chatbot mostra. '
    'Dois turnos de chat sobrepostos na mesma sessão ainda podem sobrescrever um ao outro, como hoje; corrigir isso é uma decisão à parte.</p>'))]},
]

VERIF = [
 (True, ('Negative control','Controle negativo'),
  ('Before this task, force a Small Memory flow through the workflow engine and record the consumer&#x27;s missing content. '
   'After it, the content <strong>matches the back&#x27;s loop</strong>.',
   'Antes desta task, force um fluxo com Small Memory pelo motor de workflow e registre o conteúdo que falta ao consumidor. '
   'Depois dela, o conteúdo <strong>bate com o laço do back</strong>.')),
 (False, ('Parity over stored chat flows','Paridade em fluxos de chat armazenados'),
  ('Over a corpus of stored chat flows, the chatbot answer and the persisted memory match between the two engines.',
   'Num corpus de fluxos de chat armazenados, a resposta do chatbot e a memória persistida batem entre os dois motores.')),
 (False, ('A retried reader reads the same content','Um leitor repetido lê o mesmo conteúdo'),
  ('A retried reader activity reads the same memory content as its first attempt.',
   'Uma activity leitora repetida lê o mesmo conteúdo de memória da primeira tentativa.')),
]

DONE = ('Flows with Small Memory are <strong>eligible for the workflow engine</strong> and produce the same answer and the same persisted memory as the '
        'back&#x27;s loop; <code>fluxObject</code> is out of the back-only list.',
        'Fluxos com Small Memory são <strong>elegíveis para o motor de workflow</strong> e produzem a mesma resposta e a mesma memória persistida do '
        'laço do back; o <code>fluxObject</code> saiu da lista só-back.')

FILES = [('back/src/app-api/flux/flux.service.ts (persistSmallMemoryEntries, chat load, answer append, per-node event handler)', False),
         ('the run seed snapshot (B3b.1)', False),
         ('worker projection (project-node-input.ts)', False),
         ('ported edge-projection', False),
         ('the A1 registry', False)]

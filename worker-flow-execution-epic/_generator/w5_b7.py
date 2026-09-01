# -*- coding: utf-8 -*-
TITLE = ('Batch processing as a durable workflow', 'Processamento em lote como workflow durável')

GOAL = ('A CSV batch <b>survives a deploy</b>, and stops being a detached loop inside an API process.',
        'Um lote de CSV <b>sobrevive a um deploy</b>, e deixa de ser um laço solto dentro de um processo da API.')

GLANCE = [
 ('crit', ('Severity','Severidade'), ('High','Alta'),
  ('<strong>A thousand-row CSV is a thousand full runs from one API-key call.</strong> Review §11.2.',
   '<strong>Um CSV de mil linhas é mil runs completos a partir de uma chamada com chave de API.</strong> Review §11.2.')),
 ('dep', ('Depends on','Depende de'), ('B4 · S3','B4 · S3'),
  ('<code>B4</code> so there is a flow workflow to invoke; <code>S3</code> because a batch is the largest multiplier of a missing cost ceiling.',
   '<code>B4</code> para haver um workflow de fluxo a invocar; <code>S3</code> porque um lote é o maior multiplicador de um teto de custo ausente.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('It lands after the ceilings exist, because it is the thing that multiplies every one of them.',
   'Entra depois de os tetos existirem, porque é justamente o que multiplica todos eles.')),
 ('ship', ('Blast radius today','Raio de impacto hoje'), ('A deploy kills it','Um deploy mata o lote'),
  ('The batch stalls at <code>lastProcessedLine</code> with a <strong>non-terminal status</strong>, and nothing resumes it.',
   'O lote trava em <code>lastProcessedLine</code> com um <strong>status não terminal</strong>, e nada o retoma.')),
]

LEDE = (
 '<p><code>/flux/batch-process</code> calls <code>this.processBatch(...).catch(...)</code> (<code>flux.controller.ts:560</code>) — <strong>unawaited</strong>. '
 'The request returns immediately and the work continues <strong>detached inside the backend process</strong>.</p>'
 '<p><code>processBatch</code> (<code>:574–706</code>) is a sequential <code>for</code> loop over CSV rows. Per row it re-reads the batch, re-reads the row record, '
 'runs a <strong>complete flow</strong> via <code>await this.fluxService.apiV2(…)</code>, writes the output, re-reads the batch and saves the pointer — '
 '<strong>four to five database round trips on bookkeeping before the run itself</strong>.</p>',
 '<p>O <code>/flux/batch-process</code> chama <code>this.processBatch(...).catch(...)</code> (<code>flux.controller.ts:560</code>) — <strong>sem await</strong>. '
 'A requisição retorna na hora e o trabalho continua <strong>solto dentro do processo do backend</strong>.</p>'
 '<p>O <code>processBatch</code> (<code>:574–706</code>) é um laço <code>for</code> sequencial sobre as linhas do CSV. Por linha ele relê o lote, relê o registro da linha, '
 'roda um <strong>fluxo completo</strong> via <code>await this.fluxService.apiV2(…)</code>, escreve a saída, relê o lote e salva o ponteiro — '
 '<strong>quatro a cinco idas e voltas de banco em contabilidade antes do run em si</strong>.</p>')

TABLE = dict(
 head=[('Consequence','Consequência'),('Today','Hoje'),('With a workflow','Com um workflow')],
 rows=[
  [{'t':('No durability','Sem durabilidade')},
   {'t':('A deploy, restart or scale-down mid-batch kills the loop silently','Um deploy, restart ou scale-down no meio do lote mata o laço em silêncio'),'pill':'no'},
   {'t':('The batch is workflow state, so a restart is not an event it can notice','O lote é estado de workflow, então um restart não é um evento que ele consiga perceber'),'pill':'ok'}],
  [{'t':('No parallelism','Sem paralelismo')},
   {'t':('And no safe way to add it while it is a loop in a request handler','E nenhuma forma segura de adicionar enquanto for um laço num handler de requisição'),'pill':'no'},
   {'t':('One child workflow per row, with a concurrency cap that is a number rather than an accident','Um child workflow por linha, com um teto de concorrência que é um número e não um acidente'),'pill':'ok'}],
  [{'t':('It multiplies every missing ceiling','Multiplica todo teto ausente')},
   {'t':('A thousand rows = a thousand runs, against no rate limit, no per-run cost ceiling and no per-tenant cap','Mil linhas = mil runs, sem rate limit, sem teto de custo por run e sem teto por tenant'),'pill':'no'},
   {'t':('<code>S7</code> limits admission, <code>S3</code> stops the batch at the tenant ceiling with the completed rows kept','A <code>S7</code> limita a admissão, a <code>S3</code> para o lote no teto do tenant com as linhas concluídas preservadas'),'pill':'ok'}],
 ])

PROSE = (
 'One call, and the spec asks for it directly: with a workflow, a stall becomes either an automatic continuation or a visible failure — '
 '<em>decide which, and make sure the status endpoint reflects it honestly.</em>',
 'Uma decisão, e a spec a pede diretamente: com um workflow, uma parada vira ou uma continuação automática ou uma falha visível — '
 '<em>decida qual, e garanta que o endpoint de status reflita isso com honestidade.</em>')

DEC_RESUME = {
 'k':'decision','id':'B7-a','status':'rec','open':True,
 'q':('When a batch stalls, does the workflow continue automatically or fail visibly?',
      'Quando um lote trava, o workflow continua automaticamente ou falha de forma visível?'),
 'intro':(
  'Today a stalled batch <strong>needs someone to notice</strong>: the loop dies with the process, the row pointer stops moving, and the status column keeps '
  'claiming the batch is running. A workflow removes the silence — but it does not by itself decide <em>which</em> non-silent answer the customer gets. '
  'The constraint that binds every option below: <strong>the existing <code>/batch-process/:id/status</code> must reflect the choice honestly</strong>, '
  'because a non-terminal status that will never move again is the exact defect being fixed.',
  'Hoje um lote travado <strong>precisa que alguém perceba</strong>: o laço morre com o processo, o ponteiro de linha para de andar, e a coluna de status continua '
  'afirmando que o lote está rodando. Um workflow remove o silêncio — mas ele sozinho não decide <em>qual</em> resposta não silenciosa o cliente recebe. '
  'A restrição que amarra todas as opções abaixo: <strong>o <code>/batch-process/:id/status</code> existente precisa refletir a escolha com honestidade</strong>, '
  'porque um status não terminal que nunca mais vai mudar é exatamente o defeito sendo corrigido.'),
 'opts':[
  {'ltr':'A','name':('Automatic continuation, always','Continuação automática, sempre'),
   'how':('The workflow retries the row and carries on. A deploy, a restart or a provider blip is invisible to the customer.',
          'O workflow tenta a linha de novo e segue. Um deploy, um restart ou uma oscilação de provedor é invisível para o cliente.'),
   'pros':[('Durability is the whole reason this task exists — a deploy stops being a data-loss event',
            'Durabilidade é a razão inteira desta task existir — um deploy deixa de ser um evento de perda de dado'),
           ('The customer never has to know that the platform restarted underneath their batch',
            'O cliente nunca precisa saber que a plataforma reiniciou por baixo do lote dele')],
   'cons':[('A row that fails for a <strong>real</strong> reason — a bad CSV cell, a revoked credential — retries silently, and the batch takes hours with nobody told',
            'Uma linha que falha por um motivo <strong>real</strong> — uma célula ruim do CSV, uma credencial revogada — repete em silêncio, e o lote leva horas sem ninguém ser avisado'),
           ('Every retried row is <strong>a full flow run that costs money</strong>; without a bound, retrying is how a batch becomes an invoice',
            'Toda linha repetida é <strong>um run completo de fluxo que custa dinheiro</strong>; sem um limite, repetir é como um lote vira uma fatura')],
   'cost':[('',('Client sees: <b>a batch that is slow, not failed</b>','Cliente vê: <b>um lote lento, não falho</b>')),
           ('hi',('Ours: <b>silent cost, no signal</b>','Nosso: <b>custo silencioso, sem sinal</b>'))]},
  {'ltr':'B','name':('A visible failed workflow','Um workflow que falha visivelmente'),
   'how':('The batch stops, the workflow is failed, and the status endpoint names the row it stopped on. A human decides what happens next.',
          'O lote para, o workflow fica com falha, e o endpoint de status nomeia a linha em que parou. Uma pessoa decide o que acontece a seguir.'),
   'pros':[('Nothing is hidden — the state is terminal and it is true','Nada fica escondido — o estado é terminal e é verdadeiro'),
           ('A bad CSV is diagnosed at the row that is bad, instead of at the end of a long silence',
            'Um CSV ruim é diagnosticado na linha ruim, em vez de no fim de um longo silêncio')],
   'cons':[('It recreates today&#x27;s stall with a better label — and <strong>the point of the workflow was that nobody should have to notice</strong>',
            'Recria a parada de hoje com um rótulo melhor — e <strong>o ponto do workflow era que ninguém precisasse perceber</strong>'),
           ('A deploy in the middle of a legitimate batch becomes a customer-visible failure, which is a regression, not a fix',
            'Um deploy no meio de um lote legítimo vira uma falha visível ao cliente, o que é regressão e não correção')],
   'cost':[('hi',('Client effort: <b>restart the batch by hand</b>','Esforço do cliente: <b>reiniciar o lote na mão</b>')),
           ('lo',('Ours: <b>nothing hidden</b>','Nosso: <b>nada escondido</b>'))]},
  {'ltr':'C','pick':True,'name':('Bounded continuation, then a visible failure','Continuação limitada, depois falha visível'),
   'tag':('recommended','recomendada'),
   'how':('Infrastructure stalls resume automatically. A row that keeps failing is retried a bounded number of times, then the batch fails with '
          '<strong>that row named</strong> and every completed row preserved.',
          'Paradas de infraestrutura retomam sozinhas. Uma linha que insiste em falhar é repetida um número limitado de vezes, e então o lote falha com '
          '<strong>aquela linha nomeada</strong> e toda linha concluída preservada.'),
   'pros':[('It separates the two failures that A and B confuse: <strong>the platform restarted</strong> is not <strong>this row is broken</strong>',
            'Separa as duas falhas que a A e a B confundem: <strong>a plataforma reiniciou</strong> não é <strong>esta linha está quebrada</strong>'),
           ('The retry bound is what stops retries from becoming an unbounded cost — it is the same shape as every other ceiling in this epic',
            'O limite de retry é o que impede a repetição de virar custo ilimitado — é o mesmo formato de todo outro teto deste épico'),
           ('It maps onto Temporal&#x27;s retry policy rather than being hand-rolled bookkeeping',
            'Mapeia na política de retry do Temporal em vez de virar contabilidade escrita à mão')],
   'cons':[('The bound is a number somebody has to choose, and the honest default is not obvious before the first real batch fails',
            'O limite é um número que alguém precisa escolher, e o padrão honesto não é óbvio antes de o primeiro lote real falhar'),
           ('Two terminal shapes to represent in the status endpoint instead of one',
            'Duas formas terminais para representar no endpoint de status em vez de uma')],
   'cost':[('lo',('Client sees: <b>the failing row, by name</b>','Cliente vê: <b>a linha que falha, pelo nome</b>')),
           ('',('Ours: <b>a retry bound to choose</b>','Nosso: <b>um limite de retry a escolher</b>'))]},
 ],
 'rec':(
  '<p><strong>C.</strong> A and B are each right about one half: a stall caused by <em>us</em> should heal, and a failure caused by <em>the data</em> should be seen. '
  'Treating them as one event is what produces either a silent bill or a customer-visible failure for a deploy nobody asked about.</p>'
  '<p>Whichever is chosen, the honesty requirement is not optional: <strong><code>/batch-process/:id/status</code> must be terminal when the batch is over and '
  'must name the row when it failed.</strong> A status that says <em>running</em> forever is the defect this task exists to remove, and a workflow can reproduce it just as easily.</p>',
  '<p><strong>C.</strong> A e B estão certas cada uma sobre uma metade: uma parada causada por <em>nós</em> deveria se curar, e uma falha causada pelo <em>dado</em> deveria ser vista. '
  'Tratar as duas como um evento só é o que produz ou uma conta silenciosa ou uma falha visível ao cliente por causa de um deploy sobre o qual ninguém perguntou.</p>'
  '<p>Seja qual for a escolha, o requisito de honestidade não é opcional: <strong>o <code>/batch-process/:id/status</code> precisa ser terminal quando o lote acabou e '
  'precisa nomear a linha quando falhou.</strong> Um status que diz <em>rodando</em> para sempre é o defeito que esta task existe para remover, e um workflow reproduz isso com a mesma facilidade.</p>'),
 'who':[('Engineering','Engenharia'),('Product owns what the status endpoint says','Produto define o que o endpoint de status diz')],
}

PARTS = [
{'n':'1','title':('One child workflow per row, and the pointer becomes state','Um child workflow por linha, e o ponteiro vira estado'),
 'loc':'flux.controller.ts:560, 574–706',
 'purpose':('Replace a detached loop with a durable one, and let the per-row bookkeeping collapse because the loop can finally trust its own memory.',
            'Substituir um laço solto por um durável, e deixar a contabilidade por linha desaparecer porque o laço finalmente pode confiar na própria memória.'),
 'body':('<p>The shape is a batch workflow with <strong>one child workflow per row</strong>, a <strong>concurrency cap</strong>, and the row pointer held as '
         '<strong>workflow state</strong> rather than a column that is re-read every iteration. <code>continueAsNew</code> goes at a row boundary — '
         'a large CSV is exactly the case that exhausts workflow history (review §4.1).</p>'
         '<p>The per-row bookkeeping today looks like this, before the run itself:</p>',
         '<p>O formato é um workflow de lote com <strong>um child workflow por linha</strong>, um <strong>teto de concorrência</strong>, e o ponteiro de linha mantido como '
         '<strong>estado do workflow</strong> em vez de uma coluna relida a cada iteração. O <code>continueAsNew</code> vai numa fronteira de linha — '
         'um CSV grande é exatamente o caso que esgota o histórico de workflow (review §4.1).</p>'
         '<p>A contabilidade por linha hoje é assim, antes do run em si:</p>'),
 'code':('per row:  re-read the batch  ->  re-read the row record  ->  apiV2(...)  ->  write the output  ->  re-read the batch  ->  save the pointer',
         'por linha:  reler o lote  ->  reler o registro da linha  ->  apiV2(...)  ->  escrever a saida  ->  reler o lote  ->  salvar o ponteiro'),
 'body2':('<p><strong>That re-reading exists because the loop cannot trust its own memory across a restart.</strong> A workflow can — which is why the '
          'collapse is a consequence of the change rather than a separate optimisation. The claim in the spec is four to five round trips per row: '
          '<strong>prove it or correct it</strong>.</p>',
          '<p><strong>Essa releitura existe porque o laço não pode confiar na própria memória entre reinícios.</strong> Um workflow pode — por isso o '
          'encolhimento é consequência da mudança e não uma otimização separada. A afirmação da spec é de quatro a cinco idas e voltas por linha: '
          '<strong>prove ou corrija</strong>.</p>'),
 'ba':(('An unawaited <code>for</code> loop inside a request handler. Its progress lives in a column it re-reads because it cannot trust anything else.',
        'Um laço <code>for</code> sem await dentro de um handler de requisição. O progresso dele vive numa coluna que ele relê porque não pode confiar em mais nada.'),
       ('A durable workflow with one child per row, a concurrency cap, and the pointer in workflow state — with <code>continueAsNew</code> at a row boundary so a large CSV cannot exhaust the history.',
        'Um workflow durável com um filho por linha, um teto de concorrência, e o ponteiro no estado do workflow — com <code>continueAsNew</code> numa fronteira de linha para um CSV grande não esgotar o histórico.'))},

{'n':'2','title':('The progress columns keep their meaning','As colunas de progresso mantêm seu significado'),
 'loc':'back/src/entities/batch_processing_file*.ts',
 'purpose':('The workflow becomes the writer of the surface the customer already watches — it does not replace it with a new one.',
            'O workflow vira o escritor da superfície que o cliente já acompanha — não a substitui por uma nova.'),
 'body':('<p><code>lastProcessedLine</code> and the batch status columns stay, and they stay updated. They are the <strong>customer-facing progress surface</strong>, '
         'and the existing status and download endpoints read them. What changes is who writes them: the workflow, instead of a loop that re-read them '
         'to remember where it was.</p>'
         '<p>This is what keeps the task revertible. The columns are the contract; the loop behind them is an implementation detail that this task replaces.</p>',
         '<p>O <code>lastProcessedLine</code> e as colunas de status do lote permanecem, e permanecem atualizados. Eles são a <strong>superfície de progresso voltada ao cliente</strong>, '
         'e os endpoints existentes de status e de download os leem. O que muda é quem os escreve: o workflow, em vez de um laço que os relia '
         'para lembrar onde estava.</p>'
         '<p>É isso que mantém a task reversível. As colunas são o contrato; o laço por trás delas é detalhe de implementação que esta task substitui.</p>'),
 'ba':(('The columns are both the progress surface <em>and</em> the loop&#x27;s memory, which is why they are re-read four to five times per row.',
        'As colunas são ao mesmo tempo a superfície de progresso <em>e</em> a memória do laço, e é por isso que são relidas quatro a cinco vezes por linha.'),
       ('The columns are only the progress surface. The workflow remembers where it is, and writes them because the customer reads them.',
        'As colunas são apenas a superfície de progresso. O workflow lembra onde está, e as escreve porque o cliente as lê.')),
 'callouts':[('mig',('Out of scope','Fora de escopo'),
   ('<p>Changing the CSV format, the input mapping to <code>varInputNode</code>s, or the output shape. '
    'A row-for-row output comparison against a pre-change run is what proves it.</p>',
    '<p>Mudar o formato do CSV, o mapeamento de entrada para os <code>varInputNode</code>s, ou o formato de saída. '
    'Uma comparação de saída linha a linha contra um run anterior à mudança é o que prova isso.</p>'))]},

{'n':'3','title':('Stop becomes cancellation','Parar vira cancelamento'),
 'loc':'flux.controller.ts:513–517, 710–800',
 'purpose':('Honour the stop endpoint through workflow cancellation, which reaches the rows already in flight.',
            'Honrar o endpoint de parada via cancelamento de workflow, que alcança as linhas já em voo.'),
 'body':('<p>Today <code>/batch-process/:id/stop</code> <strong>sets a flag the loop checks</strong>. That means a row already running finishes, and a loop that '
         'has already died never checks anything at all — stop on a stalled batch does nothing visible.</p>'
         '<p>Through workflow cancellation, stop reaches the batch workflow <em>and</em> the row children already in flight. '
         '<strong>This is strictly better than today</strong>, and it is the same mechanism <code>E2</code> aligns the rest of the system on.</p>',
         '<p>Hoje o <code>/batch-process/:id/stop</code> <strong>liga uma flag que o laço checa</strong>. Isso significa que uma linha já em execução termina, e um laço que '
         'já morreu nunca checa nada — parar um lote travado não faz nada visível.</p>'
         '<p>Via cancelamento de workflow, o stop alcança o workflow do lote <em>e</em> os filhos de linha já em voo. '
         '<strong>Isto é estritamente melhor que hoje</strong>, e é o mesmo mecanismo no qual a <code>E2</code> alinha o resto do sistema.</p>'),
 'ba':(('Stop sets a flag. In-flight rows run to completion, and a batch whose loop has already died ignores stop entirely.',
        'O stop liga uma flag. Linhas em voo rodam até o fim, e um lote cujo laço já morreu ignora o stop por completo.'),
       ('Stop cancels the workflow, which cancels the row children in flight, and the batch reaches a <strong>terminal</strong> status the endpoint can report.',
        'O stop cancela o workflow, que cancela os filhos de linha em voo, e o lote chega a um status <strong>terminal</strong> que o endpoint consegue reportar.'))},

{'n':'4','title':('A screen to create a batch and watch it run','Uma tela para criar um lote e acompanhá-lo'),
 'loc':('front · reads the five existing endpoints','front · lê os cinco endpoints existentes'),
 'purpose':('Give the stop and status endpoints a consumer. Cancellation nobody can reach is not a feature.',
            'Dar um consumidor aos endpoints de stop e status. Cancelamento que ninguém alcança não é funcionalidade.'),
 'body':('<p>A batch is created from a CSV and watched while it runs: <strong>rows done, rows failed, the current row, and the output per row</strong>. '
         'The endpoints already exist — <code>POST /batch-process</code>, <code>GET /:id/status</code>, <code>GET /all</code>, <code>POST /:id/stop</code> and '
         '<code>GET /:ids/download</code>. What has never existed is a surface that reads them.</p>'
         '<p><strong>This is why <code>D18</code> keeps the route instead of retiring it.</strong> The five endpoints gain a consumer in this epic rather than '
         'losing one, so none of them is deprecated — and <code>C2</code> must not sweep them up with the legacy endpoint, which looks similar and is not.</p>',
         '<p>Um lote é criado a partir de um CSV e acompanhado enquanto roda: <strong>linhas concluídas, linhas falhadas, a linha atual e a saída por linha</strong>. '
         'Os endpoints já existem — <code>POST /batch-process</code>, <code>GET /:id/status</code>, <code>GET /all</code>, <code>POST /:id/stop</code> e '
         '<code>GET /:ids/download</code>. O que nunca existiu é uma superfície que os leia.</p>'
         '<p><strong>É por isso que a <code>D18</code> mantém a rota em vez de aposentá-la.</strong> Os cinco endpoints ganham um consumidor neste épico em vez de '
         'perder um, então nenhum deles é depreciado — e a <code>C2</code> não pode varrê-los junto com o endpoint legado, que é parecido e não é a mesma coisa.</p>'),
 'ba':(('Stop and status are endpoints with no caller. A stalled batch is discovered by someone noticing.',
        'Stop e status são endpoints sem chamador. Um lote travado é descoberto por alguém que percebe.'),
       ('The batch is visible while it runs, and stopping it is a button rather than a request somebody has to compose.',
        'O lote é visível enquanto roda, e pará-lo é um botão em vez de uma requisição que alguém precisa montar.'))},

{'n':'5','title':('Stop after too many failures, if the customer asks for it','Parar após falhas demais, se o cliente pedir'),
 'loc':('new — batch configuration','novo — configuração do lote'),
 'purpose':('Let a batch that is clearly going wrong stop early, without making that the default for a batch that is merely imperfect.',
            'Deixar um lote que claramente deu errado parar cedo, sem tornar isso o padrão para um lote apenas imperfeito.'),
 'body':('<p>An optional policy, set per batch: either an <strong>absolute count</strong> — <em>stop after 1000 failures</em> — or a <strong>share of the rows '
         'processed</strong> — <em>stop at 60% failed</em>. <strong>Unset means run the whole CSV</strong>, which is today&#x27;s behaviour and stays the default.</p>'
         '<p>Two things have to be decided with it and stated in the PR, because leaving either implicit produces a policy nobody can predict:</p>',
         '<p>Uma política opcional, definida por lote: um <strong>número absoluto</strong> — <em>parar após 1000 falhas</em> — ou uma <strong>fração das linhas '
         'processadas</strong> — <em>parar em 60% de falha</em>. <strong>Sem definir, roda o CSV inteiro</strong>, que é o comportamento de hoje e continua o padrão.</p>'
         '<p>Duas coisas precisam ser decididas junto e declaradas no PR, porque deixar qualquer uma implícita produz uma política que ninguém consegue prever:</p>'),
 'list':[('<strong>What counts as a failure</strong> — a failed row, or a failed node inside a row that otherwise produced output?',
          '<strong>O que conta como falha</strong> — uma linha que falhou, ou um node que falhou dentro de uma linha que ainda assim produziu saída?'),
         ('<strong>What happens to rows already in flight</strong> when the threshold trips — cancelled with the batch, or allowed to finish?',
          '<strong>O que acontece com as linhas já em voo</strong> quando o limite dispara — canceladas junto com o lote, ou deixadas terminar?')],
 'body2':('<p><strong>The share form needs a minimum sample</strong>, or a batch whose first two rows fail stops at 100% failed. That is not a corner case; it is '
          'the first thing a tester will do.</p>',
          '<p><strong>A forma em fração precisa de amostra mínima</strong>, senão um lote cujas duas primeiras linhas falham para com 100% de falha. Isso não é caso '
          'de canto; é a primeira coisa que quem testa vai fazer.</p>'),
 'callouts':[('mig',('Interactions to re-read, not constraints today','Interações para reler, não restrições de hoje'),
   ('<p><strong><code>S1</code>:</strong> a row is a sub-flow, so it starts at depth 1 and anything it calls goes deeper. A batch of a flow that itself composes '
    'two levels reaches the <code>S1</code> ceiling — confirm the ceiling is measured against batch rows, not only against hand-built flows.</p>'
    '<p><strong><code>D21</code>:</strong> every row is a child of a parent that has already started, so if a priority list is ever introduced, one thousand-row CSV '
    'could hold the front of the queue. <strong>No such ordering exists today</strong> — work starts as capacity frees up — so this is a risk to re-read when '
    '<code>D21</code>&#x27;s condition is met.</p>',
    '<p><strong><code>S1</code>:</strong> uma linha é um sub-fluxo, então começa na profundidade 1 e qualquer coisa que ela chame vai mais fundo. Um lote de um fluxo '
    'que por si só compõe dois níveis atinge o teto da <code>S1</code> — confirme que o teto é medido contra linhas de lote, não só contra fluxos feitos à mão.</p>'
    '<p><strong><code>D21</code>:</strong> toda linha é filha de um pai que já começou, então se uma lista de prioridade for criada, um CSV de mil linhas poderia '
    'segurar a frente da fila. <strong>Nenhuma ordenação dessas existe hoje</strong> — o trabalho começa conforme a capacidade libera — então isso é um risco para '
    'reler quando a condição da <code>D21</code> for atendida.</p>'))]},
]
VERIF = [
 (True, ('Negative control — the stop-on-failure threshold','Controle negativo — o limite de parada por falha'),
  ('Build a CSV whose rows <strong>fail deterministically past a known point</strong>. Run it with the policy unset and confirm the batch processes every row and '
   'fails every one. Then set the threshold and confirm it stops at the row it should, with the reason recorded and the completed rows kept. '
   '<strong>A threshold that has never been seen not to trigger is not a threshold.</strong>',
   'Monte um CSV cujas linhas <strong>falhem de forma determinística a partir de um ponto conhecido</strong>. Rode com a política desligada e confirme que o lote '
   'processa todas as linhas e falha em todas. Depois ligue o limite e confirme que ele para na linha certa, com o motivo registrado e as linhas concluídas '
   'preservadas. <strong>Um limite que nunca foi visto sem disparar não é um limite.</strong>')),
 (True, ('Negative control — restart it mid-run','Controle negativo — reinicie no meio'),
  ('Start a batch, <strong>restart the backend mid-run, and confirm the batch stalls on <code>main</code></strong> — that is today&#x27;s behaviour and it should be '
   'seen once, by the person doing the work. Then confirm the workflow version resumes and completes.',
   'Inicie um lote, <strong>reinicie o backend no meio e confirme que o lote trava na <code>main</code></strong> — esse é o comportamento de hoje e ele deve ser '
   'visto uma vez, por quem está fazendo o trabalho. Depois confirme que a versão com workflow retoma e conclui.')),
 (True, ('Cost-ceiling interaction','Interação com o teto de custo'),
  ('Run a batch whose total <strong>would exceed the tenant&#x27;s budget</strong> and confirm <code>S3</code> stops it at the ceiling, '
   'with the partially-completed rows <strong>recorded rather than lost</strong>.',
   'Rode um lote cujo total <strong>ultrapassaria o orçamento do tenant</strong> e confirme que a <code>S3</code> o para no teto, '
   'com as linhas parcialmente concluídas <strong>registradas em vez de perdidas</strong>.')),
 (False, ('Stop mid-batch, and land on a terminal status','Parar no meio, e terminar num status terminal'),
  ('Stop a running batch and confirm the <strong>in-flight rows cancel</strong> and the status is terminal — not a status that will simply never move again.',
   'Pare um lote em execução e confirme que as <strong>linhas em voo são canceladas</strong> e que o status é terminal — não um status que simplesmente nunca mais vai mudar.')),
 (False, ('Row-for-row output comparison','Comparação de saída linha a linha'),
  ('Compare the outputs against a pre-change run of the same CSV, row for row. The CSV format, the input mapping and the output shape are all out of scope, '
   'so any difference is a defect and not a design choice.',
   'Compare as saídas contra um run anterior à mudança com o mesmo CSV, linha a linha. O formato do CSV, o mapeamento de entrada e o formato de saída estão fora de escopo, '
   'então qualquer diferença é defeito e não escolha de projeto.')),
 (False, ('Measure the bookkeeping reduction','Medir a redução da contabilidade'),
  ('Queries per row, before and after. <strong>The claim in this task is four to five round trips; prove it or correct it.</strong> '
   'A number nobody measured is the kind of claim that gets repeated for years.',
   'Consultas por linha, antes e depois. <strong>A afirmação desta task é de quatro a cinco idas e voltas; prove ou corrija.</strong> '
   'Um número que ninguém mediu é o tipo de afirmação que se repete por anos.')),
]

DONE = ('A batch <strong>survives a restart and resumes</strong>; <code>lastProcessedLine</code> and the status columns still tell the truth and reach a '
        '<strong>terminal</strong> state; stop cancels the rows in flight; outputs match a pre-change run row for row; and the bookkeeping reduction is '
        '<strong>measured, not asserted</strong>.',
        'Um lote <strong>sobrevive a um restart e retoma</strong>; o <code>lastProcessedLine</code> e as colunas de status continuam dizendo a verdade e chegam a um '
        'estado <strong>terminal</strong>; o stop cancela as linhas em voo; as saídas batem linha a linha com um run anterior à mudança; e a redução de contabilidade é '
        '<strong>medida, não afirmada</strong>.')

FILES = [('back/src/app-api/flux/flux.controller.ts:513–517, 560, 574–706, 710–800', False),
         ('back/src/entities/batch_processing_file*.ts', False),
         ('new batch workflow in the worker', True)]

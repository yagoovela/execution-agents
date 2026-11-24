# -*- coding: utf-8 -*-
TITLE = ('Keep node data out of Temporal history (slim run seed)',
         'Tirar os dados dos nós do histórico do Temporal (seed enxuto)')

GOAL = ('No node&#x27;s <code>data</code> enters Temporal history on the <code>processFlow</code> path, so <b>a flow whose node data passes Temporal&#x27;s 2 MB payload limit runs on the workflow engine</b>, and seed rows live as long as their run.',
        'Nenhum <code>data</code> de nó entra no histórico do Temporal no caminho do <code>processFlow</code>, então <b>um fluxo cujos dados de nós passam do limite de payload de 2 MB do Temporal roda no motor de workflow</b>, e as linhas do seed vivem tanto quanto o run.')

GLANCE = [
 ('crit', ('What it unblocks','O que destrava'), ('The B4 flag in production','A flag da B4 em produção'),
  ('A gate for turning <code>engine_in_workflow</code> on in production. It also lets A14&#x27;s 1.5 MB seed-size guard go, and comes before Wave 6 deletes the legacy loop that guard falls back to.',
   'Uma condição para ligar a <code>engine_in_workflow</code> em produção. Também permite remover a guarda de tamanho de seed de 1,5 MB da A14, e vem antes de a onda 6 apagar o laço legado para onde essa guarda desvia.')),
 ('dep', ('Depends on','Depende de'), ('B4 · after B6 and B5','B4 · depois da B6 e da B5'),
  ('B4 is on <code>main</code>. It ships after B6 and B5 reach <code>main</code>, because both rewrite the same <code>processFlow</code> call sites and add array and child-flow payloads.',
   'A B4 está no <code>main</code>. Sobe depois que a B6 e a B5 chegarem ao <code>main</code>, porque as duas reescrevem as mesmas chamadas do <code>processFlow</code> e acrescentam payloads de array e de sub-fluxo.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Added on 2026-11-24 from the A14 edge-case investigation (A14-D12).',
   'Adicionada em 24/11/2026 a partir da investigação de casos de borda da A14 (A14-D12).')),
 ('ship', ('Shape','Formato'), ('Mostly worker','Principalmente worker'),
  ('Estimate 1.5 to 2.5 days on <code>main</code>, plus about 1 day to fit B5 and B6.',
   'Estimativa de 1,5 a 2,5 dias no <code>main</code>, mais cerca de 1 dia para encaixar a B5 e a B6.')),
]

LEDE = (
 '<p>A workflow run writes every node&#x27;s full <code>data</code> into Temporal history twice: once as the result of <code>loadRunSeedActivity</code> (the whole <code>run_seeds.payload</code>, again on every <code>continueAsNew</code> segment) and once per node as the <code>nodeData</code> input of <code>openNodeExecutionActivity</code>. '
 'Temporal refuses any payload above 2 MB, so a flow whose node data adds up past about 2 MB cannot run on the workflow engine, while the legacy loop runs it. <strong>Measured on 2026-11-24: a 2.84 MB Small Memory fails with <code>Complete result exceeds size limit</code> (HTTP 500).</strong></p>'
 '<p>The data is also stored twice per run in Postgres (<code>run_seeds.payload</code> and <code>run_seed_nodes</code>), and <code>run_seeds</code> is never purged. <code>run_seed_nodes</code> is purged daily once it is older than 7 h, while <code>processFlow</code> has no execution timeout and the unfinished-run reaper is off in production, so a run alive past 7 h loses its seed rows.</p>',
 '<p>Um run de workflow grava o <code>data</code> inteiro de cada nó no histórico do Temporal duas vezes: uma como resultado da <code>loadRunSeedActivity</code> (o <code>run_seeds.payload</code> inteiro, de novo a cada segmento de <code>continueAsNew</code>) e uma por nó como a entrada <code>nodeData</code> da <code>openNodeExecutionActivity</code>. '
 'O Temporal recusa qualquer payload acima de 2 MB, então um fluxo cujos dados de nós somam mais de cerca de 2 MB não roda no motor de workflow, enquanto o laço legado roda. <strong>Medido em 24/11/2026: uma Small Memory de 2,84 MB falha com <code>Complete result exceeds size limit</code> (HTTP 500).</strong></p>'
 '<p>Os dados também ficam duas vezes por run no Postgres (<code>run_seeds.payload</code> e <code>run_seed_nodes</code>), e a <code>run_seeds</code> nunca é limpa. A <code>run_seed_nodes</code> é limpa todo dia quando passa de 7 h, enquanto o <code>processFlow</code> não tem timeout de execução e o reaper de runs inacabados está desligado em produção, então um run vivo por mais de 7 h perde as linhas do seed.</p>')

TABLE = dict(
 head=[('Where node data goes','Para onde vão os dados dos nós'),('Today','Hoje'),('After B4b','Depois da B4b')],
 rows=[
  [('Result of <code>loadRunSeedActivity</code>','Resultado da <code>loadRunSeedActivity</code>'),
   {'t':('The whole payload, on every segment','O payload inteiro, em todo segmento'),'pill':'weak'},
   {'t':('The scheduling skeleton: ids, types, edges, starter and the few control fields B5 and B6 read','O esqueleto de agendamento: ids, tipos, arestas, nó inicial e os poucos campos de controle que a B5 e a B6 leem'),'pill':'ok'}],
  [('Input of <code>openNodeExecutionActivity</code>','Entrada da <code>openNodeExecutionActivity</code>'),
   {'t':('The node&#x27;s full <code>data</code>','O <code>data</code> inteiro do nó'),'pill':'weak'},
   {'t':('Read from <code>run_seed_nodes</code> by snapshot and node id','Lido da <code>run_seed_nodes</code> por snapshot e id do nó'),'pill':'ok'}],
  [('Seed rows of a run open past 7 h','Linhas do seed de um run aberto há mais de 7 h'),
   {'t':('Purged','Apagadas'),'pill':'weak'},
   {'t':('Kept until the run closes','Mantidas até o run fechar'),'pill':'ok'}],
  [('<code>run_seeds</code>','<code>run_seeds</code>'),
   {'t':('Never purged','Nunca limpa'),'pill':'weak'},
   {'t':('Kept 7 days after the run closes','Mantida 7 dias depois de o run fechar'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('A skeleton-only seed in history','Só o esqueleto do seed no histórico'),
 'loc':('worker/src/modules/temporal (seed projection, processFlow input)','worker/src/modules/temporal (projeção do seed, entrada do processFlow)'),
 'purpose':('<code>processFlow</code> loads only the scheduling skeleton, in every <code>continueAsNew</code> segment.',
            'O <code>processFlow</code> carrega só o esqueleto de agendamento, em todo segmento de <code>continueAsNew</code>.'),
 'body':('<p>An <code>arrayNode</code> body or a <code>fluxBox</code>/<code>libraryNode</code> child flow (B6) gets its configuration from activities that return ids and counts, not the child graph&#x27;s full data. A history recorded before the change replays without a non-determinism error.</p>',
         '<p>O corpo de um <code>arrayNode</code> ou um sub-fluxo <code>fluxBox</code>/<code>libraryNode</code> (B6) recebe a configuração de activities que devolvem ids e contagens, não os dados inteiros do grafo filho. Um histórico gravado antes da mudança faz replay sem erro de não determinismo.</p>'),
 'ba':(('A 2.84 MB memory fails the run at the first activity.','Uma memória de 2,84 MB derruba o run na primeira activity.'),
       ('A flow whose node data totals 10 MB finishes with the legacy loop&#x27;s answer.','Um fluxo cujos dados de nós somam 10 MB termina com a resposta do laço legado.'))},

{'n':'2','title':('Node data read at open, not passed','Dados do nó lidos na abertura, não repassados'),
 'loc':('worker open activity · B4b-D3','activity de abertura no worker · B4b-D3'),
 'purpose':('A node&#x27;s <code>data</code> is read from <code>run_seed_nodes</code> at open and is neither an activity input nor a result.',
            'O <code>data</code> de um nó é lido da <code>run_seed_nodes</code> na abertura e não é entrada nem resultado de activity.'),
 'body':('<p>B4b-D3 is open and settled in Design: the worker activity reads the row and posts it to the back, so the HTTP body never enters history, or the back reads the row itself (back deploys first). A missing row fails the open with the existing <code>missingSeedError</code> message.</p>',
         '<p>A B4b-D3 está em aberto e se decide no design: a activity do worker lê a linha e a envia ao back, e o corpo HTTP nunca entra no histórico, ou o próprio back lê a linha (o back sobe antes). Uma linha ausente falha a abertura com a mensagem <code>missingSeedError</code> que já existe.</p>')},

{'n':'3','title':('Seed rows live as long as their run','As linhas do seed vivem tanto quanto o run'),
 'loc':('back purge cron','cron de limpeza no back'),
 'purpose':('B4b-D2, settled 2026-11-24: the daily purge deletes only rows of closed runs; <code>run_seeds</code> stays 7 days after the run closes, and longer while a batch-row or schedule finish activity still retries.',
            'B4b-D2, decidida em 24/11/2026: a limpeza diária apaga só linhas de runs fechados; a <code>run_seeds</code> fica 7 dias depois de o run fechar, e mais enquanto uma activity de fim de linha de batch ou de agendamento ainda tenta de novo.'),
 'body':('<p>Rejected: an execution timeout on <code>processFlow</code> equal to the run ceiling, keeping the time-based purge.</p>',
         '<p>Rejeitado: um timeout de execução no <code>processFlow</code> igual ao teto do run, mantendo a limpeza por tempo.</p>')},

{'n':'4','title':('Remove A14&#x27;s seed-size guard; defer pruning','Remover a guarda de tamanho de seed da A14; adiar a poda'),
 'loc':('engine selector · B4b-D1','seletor de motor · B4b-D1'),
 'purpose':('Once B4b is in production, the engine selector no longer routes a run by seed size.',
            'Com a B4b em produção, o seletor de motor deixa de escolher o motor pelo tamanho do seed.'),
 'body':('<p>B4b-D1, deferred on 2026-11-24: pruning the seed to the reachable set plus every placeholder and <code>*Data</code> target saves only Postgres rows once node data leaves history. It is revisited after the production seed-size query and after B4c, because a pruning pass must keep every placeholder target.</p>',
         '<p>B4b-D1, adiada em 24/11/2026: podar o seed para o conjunto alcançável mais todo alvo de placeholder e de <code>*Data</code> só economiza linhas no Postgres quando os dados dos nós saem do histórico. Ela volta depois da consulta de tamanho de seed em produção e depois da B4c, porque uma poda precisa manter todo alvo de placeholder.</p>')},
]

VERIF = [
 (False, ('Negative control','Controle negativo'),
  ('A flow whose node data totals 10 MB fails on <code>main</code> with <code>Complete result exceeds size limit</code>; after the change it finishes, and its answer, outputs and deliveries match the legacy loop&#x27;s.',
   'Um fluxo cujos dados de nós somam 10 MB falha no <code>main</code> com <code>Complete result exceeds size limit</code>; depois da mudança ele termina, e a resposta, as saídas e as entregas batem com as do laço legado.')),
 (False, ('History size and replay','Tamanho do histórico e replay'),
  ('No <code>processFlow</code> history recorded in the tests holds a payload above 512 KB; a history recorded before the change replays; a run that crosses <code>continueAsNew</code> loads only the skeleton in each segment.',
   'Nenhum histórico do <code>processFlow</code> gravado nos testes tem payload acima de 512 KB; um histórico gravado antes da mudança faz replay; um run que atravessa o <code>continueAsNew</code> carrega só o esqueleto em cada segmento.')),
 (False, ('Every entry point','Toda porta de entrada'),
  ('A batch row, a scheduled run and a child flow (B6) with large node data finish; with A14&#x27;s guard removed, a 3 MB memory flow runs on the workflow engine.',
   'Uma linha de batch, um run agendado e um sub-fluxo (B6) com dados grandes terminam; sem a guarda da A14, um fluxo com memória de 3 MB roda no motor de workflow.')),
 (False, ('Seed lifetime','Vida do seed'),
  ('The purge keeps the seed rows of an open run older than 7 h and deletes them after the run closes plus the retention period; a retrying batch-row finish still finds its seed.',
   'A limpeza mantém as linhas do seed de um run aberto há mais de 7 h e as apaga depois do fechamento mais a retenção; um fim de linha de batch que tenta de novo ainda acha o seed.')),
]

DONE = ('A 10 MB-seed flow passes on the workflow engine locally and on dev, no <code>processFlow</code> history on dev holds a payload above 512 KB, and the <code>engine_in_workflow</code> rollout lists B4b as done before its date is set.',
        'Um fluxo com seed de 10 MB passa no motor de workflow localmente e em dev, nenhum histórico do <code>processFlow</code> em dev tem payload acima de 512 KB, e o rollout da <code>engine_in_workflow</code> lista a B4b como concluída antes de ter data.')

FILES = [('worker seed projection and processFlow input', False),
         ('worker openNodeExecutionActivity', False),
         ('worker B6 child-flow and array activities', False),
         ('back run_seeds and run_seed_nodes purge', False)]

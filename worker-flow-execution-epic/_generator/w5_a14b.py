# -*- coding: utf-8 -*-
TITLE = ('Store Small Memory entries as rows',
         'Guardar as entradas da Small Memory como linhas')

GOAL = ('A non-chat Small Memory keeps its entries as rows, so <b>a write appends only the new entries and a reader reads only the rows it needs</b>, whatever the memory&#x27;s size.',
        'Uma Small Memory que não é de chat guarda as entradas como linhas, então <b>uma escrita só acrescenta as entradas novas e uma leitura lê só as linhas de que precisa</b>, qualquer que seja o tamanho da memória.')

GLANCE = [
 ('crit', ('Customer impact','Impacto no cliente'), ('Memories that grow every run','Memórias que crescem a cada run'),
  ('Every run rewrites and re-reads the whole memory, so a flow slows down and finally fails as its memory grows.',
   'Cada run reescreve e relê a memória inteira, então um fluxo fica mais lento e acaba falhando conforme a memória cresce.')),
 ('dep', ('Depends on','Depende de'), ('A14','A14'),
  ('Related: B4b removes the Temporal ceiling for every flow; A14b removes the ceilings that remain for memory itself.',
   'Relacionada: a B4b tira o teto do Temporal de todo fluxo; a A14b tira os tetos que sobram para a própria memória.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Added on 2026-11-24 from the A14 edge-case investigation (A14-D12, A14-D15).',
   'Adicionada em 24/11/2026 a partir da investigação de casos de borda da A14 (A14-D12, A14-D15).')),
 ('ship', ('Shape','Formato'), ('An architecture change','Uma mudança de arquitetura'),
  ('Back, front, worker and MCP. Estimate 70 to 110 h.',
   'Back, front, worker e MCP. Estimativa de 70 a 110 h.')),
]

LEDE = (
 '<p>A non-chat Small Memory (<code>fluxObject</code>) keeps all its entries in its node&#x27;s <code>data</code> jsonb, and stores each entry twice (<code>entries</code> and <code>userSessionsChat.default</code>). '
 'Every producer write reads, merges, sanitizes and saves the whole blob, the editor re-uploads both copies on every open, and every reader loads the whole blob to pick the last few entries.</p>'
 '<p>The memory is therefore bounded by <code>jsonb</code> (about 255 MB per value), by a V8 string (about 512 MB) and by one process&#x27;s RAM at several steps, and its write cost grows with its size. '
 '<strong>Chat memory already stores rows</strong> in <code>session_state_entries</code> (scope <code>flowId:nodeId</code>, ordered by <code>seq</code>) with a blob fallback; non-chat memory never does.</p>',
 '<p>Uma Small Memory que não é de chat (<code>fluxObject</code>) guarda todas as entradas no <code>data</code> jsonb do nó, e guarda cada entrada duas vezes (<code>entries</code> e <code>userSessionsChat.default</code>). '
 'Toda escrita de um produtor lê, mescla, sanitiza e grava o blob inteiro, o editor reenvia as duas cópias a cada abertura, e todo leitor carrega o blob inteiro para pegar as últimas entradas.</p>'
 '<p>A memória fica então limitada pelo <code>jsonb</code> (cerca de 255 MB por valor), por uma string do V8 (cerca de 512 MB) e pela RAM de um processo em vários passos, e o custo de escrita cresce com o tamanho. '
 '<strong>A memória de chat já guarda linhas</strong> na <code>session_state_entries</code> (escopo <code>flowId:nodeId</code>, ordenadas por <code>seq</code>) com fallback no blob; a memória que não é de chat nunca guarda.</p>')

TABLE = dict(
 head=[('Operation','Operação'),('Today (one blob)','Hoje (um blob)'),('After A14b (rows)','Depois da A14b (linhas)')],
 rows=[
  [('A producer adds an entry','Um produtor acrescenta uma entrada'),
   {'t':('Reads, merges and rewrites the whole blob','Lê, mescla e reescreve o blob inteiro'),'pill':'weak'},
   {'t':('Inserts one row; a repeated content or a redelivered event adds none','Insere uma linha; um conteúdo repetido ou um evento reentregue não acrescenta nenhuma'),'pill':'ok'}],
  [('"Load Last X" or "Load First X"','"Load Last X" ou "Load First X"'),
   {'t':('Loads every entry','Carrega todas as entradas'),'pill':'weak'},
   {'t':('Reads at most X rows','Lê no máximo X linhas'),'pill':'ok'}],
  [('The editor opens a memory','O editor abre uma memória'),
   {'t':('Loads and re-uploads both copies','Carrega e reenvia as duas cópias'),'pill':'weak'},
   {'t':('Loads one page; re-uploads nothing it did not change','Carrega uma página; não reenvia nada que não mudou'),'pill':'ok'}],
  [('Run seed and Temporal history','Seed do run e histórico do Temporal'),
   {'t':('Carry the whole memory','Carregam a memória inteira'),'pill':'weak'},
   {'t':('Carry no memory entries','Não carregam entradas da memória'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('Rows for non-chat memory','Linhas para a memória que não é de chat'),
 'loc':('back session-state service · entity and migration','serviço de session-state do back · entidade e migration'),
 'purpose':('A14b-D1, recommended: <code>session_state_entries</code> with a new scope type <code>smallMemory</code>, plus <code>flowVersionHistoryId</code>, a unique <code>contentHash</code> for dedup and <code>entryAt</code>.',
            'A14b-D1, recomendada: a <code>session_state_entries</code> com um novo tipo de escopo <code>smallMemory</code>, mais <code>flowVersionHistoryId</code>, um <code>contentHash</code> único para dedup e <code>entryAt</code>.'),
 'body':('<p>A write inserts one row per new entry, deduplicated by content (per session when sessions are on) and keyed by <code>execId</code>, so a redelivered run event adds nothing. Non-chat rows have no owner and stay shared by every user, as the blob is today (A14b-D3, recommended). Empty entries are skipped, and <code>clearOnExecution</code> deletes the rows at run start before the first append.</p>',
         '<p>Uma escrita insere uma linha por entrada nova, sem duplicar conteúdo (por sessão quando há sessões) e com chave no <code>execId</code>, então um evento de run reentregue não acrescenta nada. As linhas que não são de chat não têm dono e continuam compartilhadas por todos os usuários, como o blob hoje (A14b-D3, recomendada). Entradas vazias são puladas, e o <code>clearOnExecution</code> apaga as linhas no início do run, antes do primeiro append.</p>'),
 'ba':(('Each write rewrites the whole memory.','Cada escrita reescreve a memória inteira.'),
       ('Each write appends only its new entries.','Cada escrita só acrescenta as entradas novas.'))},

{'n':'2','title':('Readers read only what they need','Leitores leem só o que precisam'),
 'loc':('back edge-projection reader · worker','leitor da edge projection no back · worker'),
 'purpose':('"Load Last X" and "Load First X" read at most X rows.',
            '"Load Last X" e "Load First X" leem no máximo X linhas.'),
 'body':('<p>A14b-D2 is open: for "Load All Entries" on a huge memory, the recommendation is to keep the newest entries up to a byte cap and tell the reader how many were left out. The cap bounds worker RAM; memory content never enters Temporal history. The cap is sized from production memory sizes and the worker&#x27;s RAM history.</p>',
         '<p>A A14b-D2 está em aberto: para "Load All Entries" numa memória enorme, a recomendação é manter as entradas mais novas até um limite de bytes e dizer ao leitor quantas ficaram de fora. O limite protege a RAM do worker; o conteúdo da memória nunca entra no histórico do Temporal. O limite é dimensionado pelos tamanhos de memória em produção e pelo histórico de RAM do worker.</p>')},

{'n':'3','title':('Switch without losing an entry','Trocar sem perder uma entrada'),
 'loc':('back backfill job','job de backfill no back'),
 'purpose':('A14b-D5, recommended: a Bull backfill turns every non-chat blob into rows with the same entries, order and timestamps; readers read rows first, and a later release stops writing the blob.',
            'A14b-D5, recomendada: um backfill no Bull transforma todo blob que não é de chat em linhas com as mesmas entradas, ordem e horários; os leitores leem as linhas primeiro, e uma versão seguinte para de gravar o blob.'),
 'body':('<p>Two earlier backfills copied some non-chat memories into chat rows, and the flow read serves those rows as the memory&#x27;s entries; this is checked on dev before the dual-read design, and those rows are never served as a non-chat memory&#x27;s entries.</p>',
         '<p>Dois backfills anteriores copiaram algumas memórias que não são de chat para linhas de chat, e a leitura do fluxo devolve essas linhas como as entradas da memória; isso é conferido em dev antes do design da leitura dupla, e essas linhas nunca são devolvidas como entradas de uma memória que não é de chat.</p>')},

{'n':'4','title':('Editor, MCP and versions','Editor, MCP e versões'),
 'loc':('front Small Memory component · MCP metadata · version copies','componente Small Memory no front · metadados do MCP · cópias de versão'),
 'purpose':('The editor loads one page and Clear deletes the rows; MCP <code>get_agent</code> and <code>export_agent</code> no longer embed every entry.',
            'O editor carrega uma página e o Clear apaga as linhas; o <code>get_agent</code> e o <code>export_agent</code> do MCP deixam de embutir todas as entradas.'),
 'body':('<p>A14b-D4, settled 2026-11-24: publish and rollback copy rows, as the blob is copied today. Duplicating a flow copies its rows; a template or a chatbot share copies none.</p>',
         '<p>A14b-D4, decidida em 24/11/2026: publicar e voltar versão copiam as linhas, como o blob é copiado hoje. Duplicar um fluxo copia as linhas; um template ou um compartilhamento de chatbot não copia nenhuma.</p>')},
]

VERIF = [
 (False, ('Negative control','Controle negativo'),
  ('On <code>main</code>, a run against a memory of 100,000 entries reads and rewrites the whole blob; after the change it inserts one row per new entry and reads at most X rows for "Load Last X", measured by query count and peak RSS.',
   'No <code>main</code>, um run contra uma memória de 100.000 entradas lê e reescreve o blob inteiro; depois da mudança ele insere uma linha por entrada nova e lê no máximo X linhas para "Load Last X", medido por número de queries e pico de RSS.')),
 (False, ('Dedup, cap and backfill','Dedup, limite e backfill'),
  ('A repeated content or a redelivered run event adds no row; "Load All Entries" over the cap says how many entries were left out; the backfill keeps every dev memory&#x27;s count, order, timestamps and hash.',
   'Um conteúdo repetido ou um evento de run reentregue não acrescenta linha; "Load All Entries" acima do limite diz quantas entradas ficaram de fora; o backfill mantém a contagem, a ordem, os horários e o hash de toda memória de dev.')),
 (False, ('Editor, MCP and versions','Editor, MCP e versões'),
  ('The editor opens a memory of 100,000 entries with one page and no re-upload; publish, rollback and duplicate copy the rows; MCP returns a memory node without every entry.',
   'O editor abre uma memória de 100.000 entradas com uma página e sem reenvio; publicar, voltar versão e duplicar copiam as linhas; o MCP devolve um nó de memória sem todas as entradas.')),
 (False, ('Parity','Paridade'),
  ('A14&#x27;s parity corpus gives the same reader input and the same stored entries on both engines.',
   'O corpus de paridade da A14 dá a mesma entrada para o leitor e as mesmas entradas guardadas nos dois motores.')),
]

DONE = ('A run against a memory of 100,000 entries reads and writes rows in proportion to its new entries, measured; A14&#x27;s parity corpus still matches; no memory loses an entry in the backfill, checked by count and hash per memory on dev.',
        'Um run contra uma memória de 100.000 entradas lê e grava linhas em proporção às entradas novas, medido; o corpus de paridade da A14 continua batendo; nenhuma memória perde uma entrada no backfill, conferido por contagem e hash por memória em dev.')

FILES = [('back session-state service and entity (session_state_entries)', False),
         ('back edge-projection reader and writer', False),
         ('back backfill job', False),
         ('front Small Memory component', False),
         ('back/src/app-mcp/node-types/node-type-metadata.ts', False)]

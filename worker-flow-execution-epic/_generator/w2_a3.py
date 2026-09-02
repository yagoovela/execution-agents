# -*- coding: utf-8 -*-

TITLE=('Reach the stranded worker modules','Alcançar os módulos encalhados no worker')
GOAL=('Resolve <code>sqlQuerier</code> and <code>audioReaderNode</code> — worker modules <b>in production</b> that <b>no dispatch gate routes to</b>.',
      'Resolver o <code>sqlQuerier</code> e o <code>audioReaderNode</code> — módulos de worker <b>em produção</b> para os quais <b>nenhum gate de dispatch roteia</b>.')

GLANCE=[
 ('crit',('Severity','Severidade'),('Nothing breaks — yet','Nada quebra — ainda'),
  ('Two complete modules ship on <code>origin/main</code> and are reachable by nothing. The inline twin is what actually runs (§9.4).',
   'Dois módulos completos vão para o <code>origin/main</code> e não são alcançáveis por nada. O gêmeo inline é o que de fato roda (§9.4).')),
 ('dep',('Depends on','Depende de'),('A1','A1'),
  ('A1&#x27;s invariant spec is what <em>detects</em> this: <code>workerModule: true</code> with <code>dispatch: &#x27;inline&#x27;</code>.',
   'O teste de invariante da A1 é o que <em>detecta</em> isto: <code>workerModule: true</code> com <code>dispatch: &#x27;inline&#x27;</code>.')),
 ('wave',('Wave','Onda'),('Wave 2','Onda 2'),
  ('Wave 2&#x27;s exit gate names this task directly: leave <strong>no</strong> module with a worker module and inline dispatch.',
   'O gate de saída da onda 2 nomeia esta task diretamente: não deixar <strong>nenhum</strong> módulo com módulo no worker e dispatch inline.')),
 ('ship',('Blocked on','Bloqueada por'),('Decision D4','Decisão D4'),
  ('Paused deliberately, or forgotten? <strong>The two answers produce opposite work</strong> — finish it, or delete it.',
   'Pausado de propósito, ou esquecido? <strong>As duas respostas produzem trabalhos opostos</strong> — terminar, ou apagar.')),
]

LEDE=(
 '<p>Both node types are in the worker&#x27;s <code>NodeType</code> enum on <code>origin/main</code> and have complete modules. Neither is in <code>isTemporalNode</code>, and neither resolves to a migrated integration provider — '
 'so <strong>nothing in the back ever starts a workflow for them</strong> (analysis §9.4).</p>'
 '<p><code>audioReaderNode</code> still has its inline handler in <code>flux.service.ts</code>, and that is what actually runs. This is the concrete case the A1 invariant spec flags: '
 '<strong><code>workerModule: true</code> with <code>dispatch: &#x27;inline&#x27;</code></strong>. The code exists, ships to every replica, and cannot be reached.</p>',
 '<p>Os dois tipos de node estão no enum <code>NodeType</code> do worker em <code>origin/main</code> e têm módulos completos. Nenhum está no <code>isTemporalNode</code>, e nenhum resolve para um provedor de integração migrado — '
 'então <strong>nada no back jamais inicia um workflow para eles</strong> (análise §9.4).</p>'
 '<p>O <code>audioReaderNode</code> ainda tem o handler inline dele em <code>flux.service.ts</code>, e é isso que de fato roda. Este é o caso concreto que o teste de invariante da A1 acusa: '
 '<strong><code>workerModule: true</code> com <code>dispatch: &#x27;inline&#x27;</code></strong>. O código existe, vai para toda réplica, e não pode ser alcançado.</p>')

TABLE={'k':'table',
 'head':[('Gate','Gate'),('<code>sqlQuerier</code>','<code>sqlQuerier</code>'),
         ('<code>audioReaderNode</code>','<code>audioReaderNode</code>'),
         ('What that produces','O que isso produz')],
 'rows':[
  [('Worker <code>NodeType</code> enum on <code>origin/main</code>','Enum <code>NodeType</code> do worker em <code>origin/main</code>'),
   {'t':('Present','Presente'),'pill':'ok'},{'t':('Present','Presente'),'pill':'ok'},
   ('The module ships to production with every worker deploy','O módulo vai para produção a cada deploy do worker')],
  [('Worker module','Módulo do worker'),
   {'t':('Complete','Completo'),'pill':'ok'},{'t':('Complete','Completo'),'pill':'ok'},
   ('<code>sql-querier/</code> and <code>audio-transcriber/</code> — note the second name does not match the type',
    '<code>sql-querier/</code> e <code>audio-transcriber/</code> — note que o segundo nome não casa com o tipo')],
  [('<code>isTemporalNode</code>','<code>isTemporalNode</code>'),
   {'t':('Absent','Ausente'),'pill':'no'},{'t':('Absent','Ausente'),'pill':'no'},
   ('The flow loop never starts a workflow for either','O laço do fluxo nunca inicia workflow para nenhum dos dois')],
  [('Migrated integration provider','Provedor de integração migrado'),
   {'t':('No','Não'),'pill':'no'},{'t':('No','Não'),'pill':'no'},
   ('The integration gate does not pick them up either','O gate de integração também não os pega')],
  [('Inline twin in <code>flux.service.ts</code>','Gêmeo inline em <code>flux.service.ts</code>'),
   {'t':('sqlQuerierNode()','sqlQuerierNode()'),'pill':'weak'},{'t':('audioReaderNode()','audioReaderNode()'),'pill':'weak'},
   ('<strong>This is what actually runs today</strong>','<strong>É isto que de fato roda hoje</strong>')],
 ]}

DEC_D4={
 'k':'decision','id':'A3-a','plan':'D4','status':'rec','open':True,
 'q':('Are <code>sqlQuerier</code> and <code>audioReaderNode</code> paused on purpose, or forgotten?',
      'O <code>sqlQuerier</code> e o <code>audioReaderNode</code> estão pausados de propósito, ou esquecidos?'),
 'intro':('PLAN §7, D4 — and <strong>the two answers produce opposite work</strong>: finish the migration, or delete the modules. '
          'The plan proceeds on <em>forgotten</em>, and the evidence for that is the <code>mcpNode</code> release: it shows exactly what a finished migration looks like in this codebase — <strong>enum, module, <code>isTemporalNode</code>, allowlist, all moving together</strong> (analysis §12.5). '
          'These two have the module and nothing else. Against that template, “forgotten” reads better than “paused” — but reading better is not the same as being confirmed.',
          'PLAN §7, D4 — e <strong>as duas respostas produzem trabalhos opostos</strong>: terminar a migração, ou apagar os módulos. '
          'O plano segue por <em>esquecido</em>, e a evidência disso é o release do <code>mcpNode</code>: ele mostra exatamente como é uma migração concluída neste código — <strong>enum, módulo, <code>isTemporalNode</code>, allowlist, tudo junto</strong> (análise §12.5). '
          'Estes dois têm o módulo e mais nada. Contra esse gabarito, “esquecido” soa melhor que “pausado” — mas soar melhor não é o mesmo que estar confirmado.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Forgotten — finish the routing','Esquecido — terminar o roteamento'),
   'tag':('recommended','recomendada'),
   'how':('Add both to the A1 registry <strong>behind the flag</strong>, prove each against its inline twin field by field, flip the flag in a separate deploy, then delete the twins.',
          'Adicionar os dois ao registro da A1 <strong>atrás da flag</strong>, provar cada um contra o gêmeo inline campo a campo, ligar a flag num deploy separado, e então apagar os gêmeos.'),
   'pros':[('Two node types of coverage for the price of <em>routing</em> — the modules exist and were presumably tested when written',
            'Dois tipos de node de cobertura pelo preço do <em>roteamento</em> — os módulos existem e presumivelmente foram testados quando escritos'),
           ('<code>audioReaderNode</code> has an inline version to diff against, <strong>a luxury no other migration in this epic has</strong>',
            'O <code>audioReaderNode</code> tem uma versão inline para comparar, <strong>um luxo que nenhuma outra migração deste épico tem</strong>'),
           ('It clears the A1 invariant, which is Wave 2&#x27;s stated exit gate',
            'Limpa a invariante da A1, que é o gate de saída declarado da onda 2')],
   'cons':[('If the modules were paused for a reason nobody wrote down, routing them ships that reason into production',
            'Se os módulos foram pausados por um motivo que ninguém escreveu, roteá-los leva esse motivo para produção'),
           ('A module written long ago and never run has never been proved against real data — <strong>the field-by-field diff is not optional here</strong>',
            'Um módulo escrito há muito tempo e nunca executado nunca foi provado contra dado real — <strong>o diff campo a campo não é opcional aqui</strong>')],
   'cost':[('hi',('Client cost: <b>one more blocking round trip</b>','Custo do cliente: <b>mais um round trip bloqueante</b>')),
           ('lo',('Ours: <b>routing, a flag, two deploys</b>','Nosso: <b>roteamento, uma flag, dois deploys</b>'))]},
  {'ltr':'B','name':('Paused — delete them','Pausado — apagar os dois'),
   'how':('Delete both modules from the worker, remove the enum entries, and <strong>record why in the module&#x27;s place</strong>.',
          'Apagar os dois módulos do worker, remover as entradas do enum, e <strong>registrar o porquê no lugar do módulo</strong>.'),
   'pros':[('Removes code that ships to every worker replica and can never run',
            'Remove código que vai para toda réplica de worker e nunca pode rodar'),
           ('It clears the A1 invariant just as exactly as routing does — deletion satisfies it too',
            'Limpa a invariante da A1 exatamente como o roteamento — apagar também a satisfaz'),
           ('Honest: an unfinished migration nobody intends to finish is better named than left lying around',
            'Honesto: uma migração inacabada que ninguém pretende terminar é melhor nomeada do que largada')],
   'cons':[('Both types go back onto the migration backlog, so <strong>the work returns later at full price</strong> instead of the price of routing',
            'Os dois tipos voltam para o backlog de migração, então <strong>o trabalho volta depois a preço cheio</strong> em vez do preço do roteamento'),
           ('Deleting a working module because its routing PR was lost is the most expensive kind of tidy-up',
            'Apagar um módulo que funciona porque o PR de roteamento se perdeu é o tipo mais caro de arrumação'),
           ('<strong>The note in its place is mandatory, not a nicety</strong> — a deleted module with no explanation invites someone to rewrite it in six months',
            '<strong>A nota no lugar dele é obrigatória, não gentileza</strong> — um módulo apagado sem explicação convida alguém a reescrevê-lo em seis meses')],
   'cost':[('',('Client cost: <b>no isolation, no retries for these two</b>','Custo do cliente: <b>sem isolamento nem retries para esses dois</b>')),
           ('hi',('Ours: <b>the migration returns from scratch</b>','Nosso: <b>a migração volta do zero</b>'))]},
  {'ltr':'C','no':True,'name':('Neither — record the stranding and move on','Nenhum dos dois — registrar o encalhe e seguir'),
   'tag':('rejected','rejeitada'),
   'how':('Keep both modules and give each an explicit <code>strandedReason</code> in the registry, so the A1 invariant spec passes without either routing or deleting anything.',
          'Manter os dois módulos e dar a cada um um <code>strandedReason</code> explícito no registro, para o teste de invariante da A1 passar sem rotear nem apagar nada.'),
   'pros':[('Costs nothing this wave','Não custa nada nesta onda'),
           ('The state is at least declared instead of accidental','O estado ao menos fica declarado em vez de acidental')],
   'cons':[('It converts a defect into a <strong>permanently sanctioned exception</strong> — <code>strandedReason</code> exists for a state being cleared, not for a state being kept',
            'Converte um defeito numa <strong>exceção permanentemente abençoada</strong> — o <code>strandedReason</code> existe para um estado em vias de ser limpo, não para um estado mantido'),
           ('It passes the spec while failing the gate&#x27;s intent: “Done when” requires the invariant to pass <strong>with no <code>strandedReason</code> entries</strong>',
            'Passa no teste e falha a intenção do gate: o “pronto quando” exige que a invariante passe <strong>sem nenhuma entrada <code>strandedReason</code></strong>'),
           ('Dead code the registry blesses is dead code nobody ever deletes',
            'Código morto que o registro abençoa é código morto que ninguém apaga nunca')],
   'cost':[('lo',('Client cost: <b>nothing changes</b>','Custo do cliente: <b>nada muda</b>')),
           ('hi',('Ours: <b>a permanent exception in a registry built to have none</b>','Nosso: <b>uma exceção permanente num registro feito para não ter nenhuma</b>'))]},
 ],
 'rec':('<p><strong>A, on the evidence — with the history check as the confirmation, not as a formality.</strong> Step 1 is cheap: the git history of the two worker modules and of <code>isTemporalNode</code> shows whether the routing PR was never written, or was written and reverted. '
        '<strong>A revert is the one finding that flips this to B</strong>, and it is the only finding that would.</p>'
        '<p>Note what does <em>not</em> settle it: the modules looking finished. They look finished under either answer — that is exactly why the decision exists. And whichever branch wins, <strong>the deliverable has the same shape</strong>: '
        'nothing is left holding a worker module with inline dispatch, and the reason lives in the registry rather than in someone&#x27;s memory.</p>',
        '<p><strong>A, pela evidência — com a checagem de histórico como confirmação, não como formalidade.</strong> O passo 1 é barato: o histórico git dos dois módulos do worker e do <code>isTemporalNode</code> mostra se o PR de roteamento nunca foi escrito, ou foi escrito e revertido. '
        '<strong>Um revert é o único achado que vira isto para a B</strong>, e é o único que viraria.</p>'
        '<p>Note o que <em>não</em> resolve: os módulos parecerem prontos. Eles parecem prontos sob qualquer das respostas — é exatamente por isso que a decisão existe. E seja qual for o ramo vencedor, <strong>a entrega tem o mesmo formato</strong>: '
        'nada fica com módulo no worker e dispatch inline, e a razão vive no registro em vez de na memória de alguém.</p>'),
 'who':[('Engineering, from the git history','Engenharia, a partir do histórico do git')],
}

PARTS=[
{'n':'1','title':('Answer D4 from the git history, not from memory',
                  'Responder a D4 pelo histórico do git, não pela memória'),
 'loc':'worker/src/modules/nodes/{sql-querier,audio-transcriber}/',
 'purpose':('The history distinguishes “the routing PR never followed” from “the routing was deliberately taken out”. Nothing else does.',
            'O histórico distingue “o PR de roteamento nunca veio” de “o roteamento foi tirado de propósito”. Nada mais distingue.'),
 'body':('<p>Check the git history of both worker modules <strong>and of <code>isTemporalNode</code></strong>. If the module landed and the routing PR never followed, that is the answer, and the task is “finish it”.</p>'
         '<p>The template to compare against already exists. <code>mcpNode</code> moved through <strong>every gate at once</strong> — enum, module, <code>isTemporalNode</code>, legacy allowlist and the provider list — which is what a completed migration looks like here. '
         'These two have the first two and none of the rest.</p>',
         '<p>Cheque o histórico git dos dois módulos do worker <strong>e do <code>isTemporalNode</code></strong>. Se o módulo entrou e o PR de roteamento nunca veio, essa é a resposta, e a task é “terminar”.</p>'
         '<p>O gabarito de comparação já existe. O <code>mcpNode</code> passou por <strong>todos os gates de uma vez</strong> — enum, módulo, <code>isTemporalNode</code>, allowlist legada e a lista de provedores — que é como uma migração concluída se parece aqui. '
         'Estes dois têm os dois primeiros e nenhum dos demais.</p>'),
 'ba':(('Nobody can say whether these two are unfinished work or abandoned work, so nobody touches them — and they ship anyway, every deploy.',
        'Ninguém sabe dizer se estes dois são trabalho inacabado ou abandonado, então ninguém mexe — e eles sobem assim mesmo, a cada deploy.'),
       ('The answer is written into the registry: either a real dispatch entry, or a deletion <strong>with the reason left in the module&#x27;s place</strong>.',
        'A resposta fica escrita no registro: ou uma entrada de dispatch real, ou uma remoção <strong>com o motivo deixado no lugar do módulo</strong>.'))},

{'n':'2','title':('Route them behind the flag, and prove them against the twin',
                  'Roteá-los atrás da flag, e prová-los contra o gêmeo'),
 'loc':('flux.service.ts — inline audioReaderNode() · sqlQuerierNode()', 'flux.service.ts — audioReaderNode() · sqlQuerierNode() inline'),
 'purpose':('<code>audioReaderNode</code> has an inline version to diff against — a luxury the other migrations do not have. Use it.',
            'O <code>audioReaderNode</code> tem uma versão inline para comparar — um luxo que as outras migrações não têm. Use.'),
 'body':('<p>Registry entries go in <strong>behind the flag, deployed disabled</strong> (PLAN §3.2). Then each type is proved against the real inline behaviour: <strong>same input, worker output compared to inline output field by field</strong>, '
         'on <strong>at least three real stored node configurations per type</strong>. Only then does the flag flip, in a separate deploy.</p>'
         '<p>Three configurations is not a ritual number. One passing case proves the happy path; three stored ones are the cheapest way to find the field that the module never learned to fill.</p>',
         '<p>As entradas do registro entram <strong>atrás da flag, com deploy desligado</strong> (PLAN §3.2). Depois cada tipo é provado contra o comportamento inline real: <strong>mesma entrada, saída do worker comparada à saída inline campo a campo</strong>, '
         'em <strong>pelo menos três configurações reais guardadas por tipo</strong>. Só então a flag é ligada, num deploy separado.</p>'
         '<p>Três configurações não é número ritual. Um caso que passa prova o caminho feliz; três guardadas são a forma mais barata de achar o campo que o módulo nunca aprendeu a preencher.</p>'),
 'ba':(('<code>audioReaderNode</code>&#x27;s inline handler runs; the worker module is dead weight that ships anyway. Nothing has ever compared the two outputs.',
        'O handler inline do <code>audioReaderNode</code> roda; o módulo do worker é peso morto que sobe assim mesmo. Nada nunca comparou as duas saídas.'),
       ('The worker module runs, and it was <strong>proved field by field against the handler it replaces</strong> before the flag was flipped.',
        'O módulo do worker roda, e foi <strong>provado campo a campo contra o handler que ele substitui</strong> antes de a flag ser ligada.')),
 'callouts':[('mig',('No silent fallback','Sem fallback silencioso'),
   ('<p>With the flag on, a broken worker module must <strong>fail the run</strong> — not fall back to the inline handler. '
    '<strong>A fallback that masks the worker being broken is worse than the stranding this task fixes</strong>, because stranding is at least visible in a registry.</p>',
    '<p>Com a flag ligada, um módulo de worker quebrado precisa <strong>falhar o run</strong> — não cair de volta no handler inline. '
    '<strong>Um fallback que mascara o worker quebrado é pior que o encalhe que esta task conserta</strong>, porque encalhe ao menos é visível num registro.</p>'))]},

{'n':'3','title':('Delete the twin, and make the flag-off path fail loudly',
                  'Apagar o gêmeo, e fazer o caminho sem flag falhar alto'),
 'purpose':('Deleting the inline twin is what turns two implementations back into one. Until then the node has two behaviours and one name.',
            'Apagar o gêmeo inline é o que transforma duas implementações de volta em uma. Até lá o node tem dois comportamentos e um nome.'),
 'body':('<p>This is <code>C1</code>&#x27;s pattern, applied here as part of the node&#x27;s own task. <strong>PLAN §5 rule 7</strong> is explicit about why: delete the twin while the behaviour is fresh, not in a cleanup sweep months later.</p>'
         '<p>After the twin is gone, one more check that is easy to skip: <strong>confirm the flag-off path fails loudly rather than doing nothing</strong>. A disabled flag with no handler behind it is a node that silently produces no output, which reads as “the node did not matter”.</p>',
         '<p>Este é o padrão da <code>C1</code>, aplicado aqui como parte da task do próprio node. A <strong>regra 7 do PLAN §5</strong> é explícita sobre o porquê: apague o gêmeo enquanto o comportamento está fresco, não numa faxina meses depois.</p>'
         '<p>Com o gêmeo fora, mais uma checagem fácil de pular: <strong>confirme que o caminho com a flag desligada falha alto em vez de não fazer nada</strong>. Uma flag desligada sem handler atrás é um node que silenciosamente não produz saída, o que se lê como “o node não importava”.</p>'),
 'ba':(('Two implementations of the same node type, one of them unreachable, and the registry cannot describe that state without an exception.',
        'Duas implementações do mesmo tipo de node, uma inalcançável, e o registro não consegue descrever esse estado sem uma exceção.'),
       ('One implementation, in the worker. <strong>The A1 invariant passes with no <code>strandedReason</code> entries left</strong>, which is Wave 2&#x27;s exit gate.',
        'Uma implementação, no worker. <strong>A invariante da A1 passa sem nenhuma entrada <code>strandedReason</code></strong>, que é o gate de saída da onda 2.'))},
]

VERIF=[
 (True,('Negative control','Controle negativo'),
  ('With the flag on, <strong>break the worker module&#x27;s <code>process()</code></strong> and confirm the run <strong>fails</strong> — rather than silently falling back to the inline handler. This is the one test that distinguishes “routed” from “appears routed”.',
   'Com a flag ligada, <strong>quebre o <code>process()</code> do módulo do worker</strong> e confirme que o run <strong>falha</strong> — em vez de cair em silêncio no handler inline. Este é o único teste que distingue “roteado” de “parece roteado”.')),
 (True,('Field-by-field output diff, worker vs inline','Diff de saída campo a campo, worker vs inline'),
  ('On <strong>at least three real stored node configurations per type</strong>. <code>audioReaderNode</code> has an inline twin to diff against — the other migrations in this epic have to guess at the expected output, and this one does not.',
   'Em <strong>pelo menos três configurações reais guardadas por tipo</strong>. O <code>audioReaderNode</code> tem um gêmeo inline para comparar — as outras migrações deste épico precisam adivinhar a saída esperada, e esta não precisa.')),
 (False,('After the twin is deleted, the flag-off path fails loudly','Depois de apagar o gêmeo, o caminho sem flag falha alto'),
  ('Confirm it <strong>fails rather than doing nothing</strong>. A flag-off path that silently produces no output is indistinguishable, in a run log, from a node that was never supposed to run.',
   'Confirme que ele <strong>falha em vez de não fazer nada</strong>. Um caminho com flag desligada que silenciosamente não produz saída é indistinguível, num log de run, de um node que nunca deveria rodar.')),
 (False,('The invariant has no exceptions left','A invariante não tem mais exceções'),
  ('Run the A1 invariant spec and confirm it passes <strong>with no <code>strandedReason</code> entries</strong>. Passing <em>because</em> an exception was recorded is option C, and option C is not what this task shipped.',
   'Rode o teste de invariante da A1 e confirme que ele passa <strong>sem nenhuma entrada <code>strandedReason</code></strong>. Passar <em>porque</em> uma exceção foi registrada é a opção C, e a opção C não é o que esta task entregou.')),
]

DONE=('Neither type has <code>workerModule: true</code> with <code>dispatch: &#x27;inline&#x27;</code>; the A1 invariant spec passes <strong>with no <code>strandedReason</code> entries</strong>; and <strong>the inline twins are gone</strong>.',
      'Nenhum dos tipos tem <code>workerModule: true</code> com <code>dispatch: &#x27;inline&#x27;</code>; o teste de invariante da A1 passa <strong>sem nenhuma entrada <code>strandedReason</code></strong>; e <strong>os gêmeos inline não existem mais</strong>.')

FILES=[('worker/src/modules/nodes/{sql-querier,audio-transcriber}/',False),
       ('back/src/app-api/flux/flux.service.ts (inline audioReaderNode(), sqlQuerierNode())',False),
       ('the A1 registry',False),
       ('new flag + env-vars-sync',True)]

BLOCKS=[
 {'k':'label','n':'1','t':('What “stranded” means, gate by gate','O que “encalhado” significa, gate a gate')},
 TABLE,
 {'k':'label','n':'2','t':('The decision this task needs','A decisão que esta task precisa')},
 {'k':'prose','t':(
   'This task is <strong>blocked on one call</strong>, and the call is not a preference — it is a fact about history that nobody has looked up. '
   'It opens below with both branches costed: what finishing costs, what deleting costs, and the third option that looks free and is not.',
   'Esta task está <strong>travada numa decisão</strong>, e a decisão não é preferência — é um fato do histórico que ninguém foi conferir. '
   'Ela abre abaixo com os dois ramos custeados: quanto custa terminar, quanto custa apagar, e a terceira opção que parece de graça e não é.')},
 DEC_D4,
 {'k':'label','n':'3','t':('What the task does, in three parts','O que a task faz, em três partes')},
]
for p in PARTS:
    BLOCKS.append({'k':'part', **p})

TASK={'code':'A3','vnum':'4','title':TITLE,'goal':GOAL,'glance':GLANCE,'lede':LEDE,
      'blocks':BLOCKS,'verif':VERIF,'done':DONE,'files':FILES}

# -*- coding: utf-8 -*-

TITLE=('One machine-readable contract','Um contrato legível por máquina')
GOAL=('An agent asked to add or change a node type gets <b>current facts</b>, not a snapshot from 2026-07.',
      'Um agente encarregado de adicionar ou mudar um tipo de node recebe <b>fatos atuais</b>, não um retrato de 2026-07.')

GLANCE=[
 ('crit',('Severity','Severidade'),('Medium — and already firing','Média — e já acontecendo'),
  ('PLAN §6, R7: the stale skill teaches the wrong thing. An agent following it <strong>today</strong> produces wrong work.',
   'PLAN §6, R7: a skill desatualizada ensina a coisa errada. Um agente que a seguir <strong>hoje</strong> produz trabalho errado.')),
 ('dep',('Depends on','Depende de'),('A1','A1'),
  ('A1 produces the registry; this task makes it the <strong>published</strong> source. <strong>Do it early, not at the end.</strong>',
   'A A1 produz o registro; esta task o torna a fonte <strong>publicada</strong>. <strong>Faça cedo, não no fim.</strong>')),
 ('wave',('Wave','Onda'),('Wave 2','Onda 2'),
  ('The delivery plan puts it here for one reason: this is not documentation polish, it is a defect that ships wrong work.',
   'O plano de entrega a coloca aqui por um motivo: isto não é polimento de documentação, é um defeito que entrega trabalho errado.')),
 ('ship',('Shape','Formato'),('Generated, not written','Gerado, não escrito'),
  ('The contract is derived from the A1 registry. The one thing this task must not produce is <strong>a second hand-maintained list</strong>.',
   'O contrato é derivado do registro da A1. A única coisa que esta task não pode produzir é <strong>uma segunda lista mantida à mão</strong>.')),
]

LEDE=(
 '<p><code>skills/node-worker-migration/SKILL.md</code> is the guidance an agent loads when it is asked to migrate a node. It states the worker enum covers ten types “as of 2026-07”, says nothing about '
 '<code>isTemporalNode</code>, nothing about the integration gate, nothing about the prefetch executor, and nothing about the blocking wait.</p>'
 '<p>It also tells the agent the worker “does NOT receive engine in-memory state” — true — while presenting the activity template as <em>the only shape</em>, which will be wrong the moment B4 lands. The skill even carries '
 'a worked example whose verdict this epic overturns. <strong>An agent that follows it will confidently produce a migration that ignores three of the four dispatch lists.</strong></p>',
 '<p>O <code>skills/node-worker-migration/SKILL.md</code> é a orientação que um agente carrega quando é encarregado de migrar um node. Ele afirma que o enum do worker cobre dez tipos “em 2026-07”, não diz nada sobre '
 '<code>isTemporalNode</code>, nada sobre o gate de integração, nada sobre o executor de prefetch, e nada sobre a espera bloqueante.</p>'
 '<p>Ele também diz ao agente que o worker “NÃO recebe estado em memória da engine” — o que é verdade — enquanto apresenta o template de activity como <em>a única forma</em>, o que ficará errado no momento em que a B4 entrar. A skill ainda carrega '
 'um exemplo resolvido cujo veredito este épico reverte. <strong>Um agente que a seguir vai produzir, com confiança, uma migração que ignora três das quatro listas de dispatch.</strong></p>')

TABLE={'k':'table',
 'head':[('What the skill teaches today','O que a skill ensina hoje'),('Status','Situação'),
         ('What the agent does with it','O que o agente faz com isso')],
 'rows':[
  [('The worker <code>NodeType</code> enum covers <strong>ten types</strong>, “as of 2026-07”',
    'O enum <code>NodeType</code> do worker cobre <strong>dez tipos</strong>, “em 2026-07”'),
   {'t':('Stale snapshot','Retrato defasado'),'pill':'no'},
   ('Registers the node in the enum and stops — the count was the whole map it had',
    'Registra o node no enum e para — a contagem era o mapa inteiro que ele tinha')],
  [('Nothing about <code>isTemporalNode</code>','Nada sobre o <code>isTemporalNode</code>'),
   {'t':('Missing','Ausente'),'pill':'no'},
   ('The back never dispatches the node the agent just wrote','O back nunca despacha o node que o agente acabou de escrever')],
  [('Nothing about the integration gate','Nada sobre o gate de integração'),
   {'t':('Missing','Ausente'),'pill':'no'},
   ('Provider-routed nodes look unroutable — or get a second routing path invented for them',
    'Nodes roteados por provedor parecem não roteáveis — ou ganham um segundo caminho de roteamento inventado')],
  [('Nothing about the prefetch executor','Nada sobre o executor de prefetch'),
   {'t':('Missing','Ausente'),'pill':'no'},
   ('Never asks whether the new type belongs in the 17-type whitelist, so it silently does not',
    'Nunca pergunta se o novo tipo pertence à whitelist de 17 tipos, então ele silenciosamente não pertence')],
  [('Nothing about the blocking wait','Nada sobre a espera bloqueante'),
   {'t':('Missing','Ausente'),'pill':'no'},
   ('Presents the migration as a latency win, when today each migrated node is a blocking round trip',
    'Apresenta a migração como ganho de latência, quando hoje cada node migrado é um round trip bloqueante')],
  [('The worker “does NOT receive engine in-memory state”','O worker “NÃO recebe estado em memória da engine”'),
   {'t':('True today','Verdade hoje'),'pill':'ok'},
   ('Correct — but the activity template is presented as the only shape, and B4 changes that',
    'Correto — mas o template de activity é apresentado como a única forma, e a B4 muda isso')],
  [('A worked example, with a verdict','Um exemplo resolvido, com veredito'),
   {'t':('Overturned','Revertido'),'pill':'no'},
   ('Reproduces a conclusion this epic reverses, and cites it as precedent',
    'Reproduz uma conclusão que este épico reverte, e a cita como precedente')],
 ]}

PARTS=[
{'n':'1','title':('The generated contract, and the two neighbours that show why',
                  'O contrato gerado, e os dois vizinhos que mostram por quê'),
 'loc':'back/src/app-mcp/node-types/',
 'purpose':('A1 produces the registry; this task turns it into the artefact an agent reads: node type → dispatch, worker module, integration providers, prefetch eligibility, mutating, inline twin.',
            'A A1 produz o registro; esta task o transforma no artefato que um agente lê: tipo de node → dispatch, módulo do worker, provedores de integração, elegibilidade de prefetch, mutante, gêmeo inline.'),
 'body':('<p><strong>Generated, not hand-maintained</strong> — and the reason is one directory away. The same repo already runs both experiments side by side:</p>',
         '<p><strong>Gerado, não mantido à mão</strong> — e a razão está a um diretório de distância. O mesmo repositório já roda os dois experimentos lado a lado:</p>'),
 'list':[('Node <strong>fields</strong> live in <code>back/src/app-mcp/node-types/node-type-metadata.ts</code> as <strong>hand-maintained JSON with nothing type-checking them</strong> against the real data model. That is precisely the drift this epic should not reproduce.',
          'Os <strong>campos</strong> de node vivem em <code>back/src/app-mcp/node-types/node-type-metadata.ts</code> como <strong>JSON mantido à mão, sem nada checando os tipos</strong> contra o modelo real. É exatamente o drift que este épico não deve reproduzir.'),
         ('Node <strong>handles</strong>, in the same directory, are <strong>generated</strong>: PLAN §3.3.6 requires <code>pnpm generate:node-handle-registry</code> and a green <code>node-handle-registry.spec.ts</code> whenever a handle changes.',
          'Os <strong>handles</strong> de node, no mesmo diretório, são <strong>gerados</strong>: o PLAN §3.3.6 exige <code>pnpm generate:node-handle-registry</code> e um <code>node-handle-registry.spec.ts</code> verde sempre que um handle muda.')],
 'body2':('<p>One of those two drifts silently and one cannot. <strong>The contract follows the handles.</strong></p>',
          '<p>Um desses dois defasa em silêncio e o outro não consegue. <strong>O contrato segue os handles.</strong></p>'),
 'ba':(('An agent reads a prose snapshot with a date in it, in a file with no mechanism to honour that date.',
        'Um agente lê um retrato em prosa com uma data, num arquivo sem mecanismo algum para honrar essa data.'),
       ('An agent reads a <strong>generated</strong> file that a spec keeps aligned with the worker enum. When it is wrong, a test says so before a human does.',
        'Um agente lê um arquivo <strong>gerado</strong> que um teste mantém alinhado ao enum do worker. Quando ele está errado, um teste avisa antes de um humano.'))},

{'n':'2','title':('Refresh the skill so it cites instead of restates',
                  'Atualizar a skill para que ela cite em vez de repetir'),
 'loc':'skills/node-worker-migration/SKILL.md',
 'purpose':('Replace the enumeration with a pointer, and add the four things the skill has never mentioned.',
            'Trocar a enumeração por um ponteiro, e acrescentar as quatro coisas que a skill nunca mencionou.'),
 'body':('<p>The enum snapshot goes and a pointer to the generated contract takes its place. Then the skill gains what it never had:</p>',
         '<p>O retrato do enum sai e um ponteiro para o contrato gerado toma seu lugar. Depois a skill ganha o que nunca teve:</p>'),
 'list':[('<strong>The four gates</strong> — the enum alone never routed anything','<strong>Os quatro gates</strong> — o enum sozinho nunca roteou nada'),
         ('<strong>The definition of done from PLAN §3.4</strong>, all seven points: a node is not done when its activity exists',
          '<strong>A definição de pronto do PLAN §3.4</strong>, os sete pontos: um node não está pronto quando a activity dele existe'),
         ('<strong>The blocking wait</strong>, so the latency cost is stated rather than discovered',
          '<strong>A espera bloqueante</strong>, para o custo de latência ser declarado e não descoberto'),
         ('<strong>The prefetch path</strong>, and the question of whether a new type belongs in its whitelist',
          '<strong>O caminho de prefetch</strong>, e a pergunta de se um novo tipo pertence à whitelist dele')],
 'body2':('<p>The rule that keeps this from decaying again: <strong>where the skill states a fact that can go stale, make it cite the generated file instead</strong>. A number written in prose has no owner; a citation does.</p>',
          '<p>A regra que impede isto de decair de novo: <strong>onde a skill declara um fato que pode envelhecer, faça-a citar o arquivo gerado</strong>. Um número escrito em prosa não tem dono; uma citação tem.</p>'),
 'ba':(('The skill answers “how many types does the worker cover?” from memory, and its memory is from 2026-07.',
        'A skill responde “quantos tipos o worker cobre?” de memória, e a memória dela é de 2026-07.'),
       ('The skill answers by pointing at the contract, so <strong>the answer is as fresh as the last generation</strong> and the drift spec says when that stops being recent.',
        'A skill responde apontando para o contrato, então <strong>a resposta é tão fresca quanto a última geração</strong> e o teste de drift avisa quando isso deixa de ser recente.')),
 'callouts':[('mig',('The template will change under B4','O template vai mudar sob a B4'),
   ('<p>The skill presents the activity template as the only shape a migration can take. <strong>B4 makes that false</strong>, when the DAG loop moves into a workflow. '
    'Write this section so the change is a <em>citation update</em> and not a rewrite — otherwise D2 gets to be done twice.</p>',
    '<p>A skill apresenta o template de activity como a única forma que uma migração pode ter. <strong>A B4 torna isso falso</strong>, quando o laço do DAG for para dentro de um workflow. '
    'Escreva esta seção de modo que a mudança seja uma <em>atualização de citação</em> e não uma reescrita — senão a D2 vai ser feita duas vezes.</p>'))]},

{'n':'3','title':('CLAUDE.md, for the agent that never loads the skill',
                  'CLAUDE.md, para o agente que nunca carrega a skill'),
 'loc':'CLAUDE.md',
 'purpose':('A skill is loaded when someone says “migrate a node”. Plenty of node code is edited without anyone saying that.',
            'Uma skill é carregada quando alguém diz “migre um node”. Muito código de node é editado sem ninguém dizer isso.'),
 'body':('<p>A short section in the workspace file, stating three things: <strong>where the contract lives</strong>, that adding a node type means <strong>the seven layers plus the registry</strong>, and '
         '<strong>which skills to run</strong> — <code>mcp-node-schema-sync</code>, <code>env-vars-sync</code>, <code>validate-changes</code>.</p>'
         '<p>Short is the requirement, not a preference. A workspace file that grows a chapter per epic is a file nobody reads to the end, and the end is where the newest rule always sits.</p>',
         '<p>Uma seção curta no arquivo do workspace, dizendo três coisas: <strong>onde o contrato vive</strong>, que adicionar um tipo de node significa <strong>as sete camadas mais o registro</strong>, e '
         '<strong>quais skills rodar</strong> — <code>mcp-node-schema-sync</code>, <code>env-vars-sync</code>, <code>validate-changes</code>.</p>'
         '<p>Ser curta é requisito, não preferência. Um arquivo de workspace que ganha um capítulo por épico é um arquivo que ninguém lê até o fim, e o fim é onde a regra mais nova sempre está.</p>'),
 'ba':(('An agent editing a node component has no reason to discover the registry, the seven layers, or the skills that check them.',
        'Um agente editando um componente de node não tem motivo para descobrir o registro, as sete camadas, ou as skills que as checam.'),
       ('The workspace file names all three in a paragraph, and the paragraph points at the contract rather than restating it.',
        'O arquivo do workspace nomeia os três num parágrafo, e o parágrafo aponta para o contrato em vez de repeti-lo.'))},

{'n':'4','title':('Keep it true, by test','Mantê-lo verdadeiro, por teste'),
 'purpose':('Documentation that can go stale silently will. The drift spec is what removes the word “silently”.',
            'Documentação que pode envelhecer em silêncio vai envelhecer. O teste de drift é o que remove a palavra “silêncio”.'),
 'body':('<p>A spec fails when the contract and the worker enum disagree — <strong>the same drift check A1 builds</strong>, extended to cover the published artefact rather than only the internal registry.</p>'
         '<p>That extension is the whole difference between a contract and a document. A1&#x27;s spec protects the registry the back reads; this one protects the file an agent reads. They can disagree, and if nothing checks, the one an agent reads is the one that rots.</p>',
         '<p>Um teste falha quando o contrato e o enum do worker discordam — <strong>a mesma checagem de drift que a A1 constrói</strong>, estendida para cobrir o artefato publicado e não só o registro interno.</p>'
         '<p>Essa extensão é a diferença inteira entre um contrato e um documento. O teste da A1 protege o registro que o back lê; este protege o arquivo que um agente lê. Eles podem discordar, e se nada conferir, o que o agente lê é o que apodrece.</p>'),
 'ba':(('The skill&#x27;s facts were true in 2026-07 and nothing has told anyone since. The only detector is a person noticing.',
        'Os fatos da skill eram verdadeiros em 2026-07 e nada avisou ninguém desde então. O único detector é alguém perceber.'),
       ('A contract that disagrees with the worker enum <strong>fails a test that names the missing registration</strong>.',
        'Um contrato que discorda do enum do worker <strong>falha um teste que nomeia o registro faltante</strong>.'))},
]

VERIF=[
 (True,('Negative control — and then the agent','Controle negativo — e depois o agente'),
  ('Add a node type to the worker enum <strong>without registering it</strong>, and confirm the drift spec fails and <strong>names the missing registration</strong>. Then do the second half, which is the one that actually tests this task: ask an agent to add a node type using <strong>only the refreshed skill</strong>, and check whether it produces all seven layers plus the registry entry. <strong>Record what it missed — that gap is the next revision of the skill.</strong>',
   'Adicione um tipo de node ao enum do worker <strong>sem registrá-lo</strong>, e confirme que o teste de drift falha e <strong>nomeia o registro faltante</strong>. Depois faça a segunda metade, que é a que de fato testa esta task: peça a um agente para adicionar um tipo de node usando <strong>apenas a skill atualizada</strong>, e veja se ele produz as sete camadas mais a entrada no registro. <strong>Registre o que faltou — essa lacuna é a próxima revisão da skill.</strong>')),
 (True,('Every claim checked, with the SHA recorded','Toda afirmação checada, com o SHA registrado'),
  ('Every claim in the refreshed skill is checked against the code <strong>at the time of writing</strong>, with the SHA recorded. Same discipline <code>D1</code> requires, and for the same reason: a documentation task that cites nothing is indistinguishable from the stale skill it replaces.',
   'Toda afirmação da skill atualizada é checada contra o código <strong>no momento da escrita</strong>, com o SHA registrado. A mesma disciplina que a <code>D1</code> exige, e pelo mesmo motivo: uma task de documentação que não cita nada é indistinguível da skill defasada que ela substitui.')),
 (False,('No enumeration survives in prose','Nenhuma enumeração sobrevive em prosa'),
  ('“Done when” says the skill contains <strong>no stale enumeration</strong>. Grep the refreshed file for counts and type lists — every one that survives is a fact with an expiry date and no expiry mechanism, which is exactly how this task came to exist.',
   'O “pronto quando” diz que a skill não contém <strong>nenhuma enumeração defasada</strong>. Faça grep de contagens e listas de tipos no arquivo atualizado — cada uma que sobreviver é um fato com prazo de validade e sem mecanismo de validade, que é exatamente como esta task passou a existir.')),
 (False,('Both entry points reach it','As duas portas de entrada chegam nele'),
  ('An agent that loads the skill and an agent that only reads <code>CLAUDE.md</code> must both end up at the generated contract. Confirm the workspace file points at both the contract and the skill, not at one of them.',
   'Um agente que carrega a skill e um agente que só lê o <code>CLAUDE.md</code> precisam ambos chegar ao contrato gerado. Confirme que o arquivo do workspace aponta para o contrato <em>e</em> para a skill, não para um só.')),
]

DONE=('The contract is <strong>generated and test-enforced</strong>; the skill contains no stale enumeration; <code>CLAUDE.md</code> points at both; and an agent following the skill produces a <strong>complete registration</strong> — all seven layers plus the registry entry.',
      'O contrato é <strong>gerado e garantido por teste</strong>; a skill não contém enumeração defasada; o <code>CLAUDE.md</code> aponta para os dois; e um agente que segue a skill produz um <strong>registro completo</strong> — as sete camadas mais a entrada no registro.')

FILES=[('skills/node-worker-migration/SKILL.md',False),
       ('CLAUDE.md',False),
       ('the A1 registry + generator + drift spec',True),
       ('back/src/app-mcp/node-types/node-type-metadata.ts (contrast case, not modified)',False)]

BLOCKS=[
 {'k':'label','n':'1','t':('What the skill teaches today, and what is true','O que a skill ensina hoje, e o que é verdade')},
 TABLE,
 {'k':'prose','t':(
   'This task has <strong>no open decision</strong>. Every item below is settled by the spec: the contract is generated, the skill cites it, <code>CLAUDE.md</code> points at both, and a spec fails when they disagree. '
   'What it needs is not a call — it is being done <strong>early</strong>, because the cost of leaving it until the end is paid in migrations written from wrong guidance.',
   'Esta task <strong>não tem decisão em aberto</strong>. Todo item abaixo está resolvido pela spec: o contrato é gerado, a skill o cita, o <code>CLAUDE.md</code> aponta para os dois, e um teste falha quando eles discordam. '
   'O que ela precisa não é de uma decisão — é de ser feita <strong>cedo</strong>, porque o custo de deixá-la para o fim é pago em migrações escritas a partir de orientação errada.')},
 {'k':'label','n':'2','t':('What the task does, in four parts','O que a task faz, em quatro partes')},
]
for p in PARTS:
    BLOCKS.append({'k':'part', **p})

TASK={'code':'D2','vnum':'3','title':TITLE,'goal':GOAL,'glance':GLANCE,'lede':LEDE,
      'blocks':BLOCKS,'verif':VERIF,'done':DONE,'files':FILES}

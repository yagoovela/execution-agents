# -*- coding: utf-8 -*-
# A4 — Migrate reportBuilder.  Source: TASK-A4-REPORT-BUILDER.md, analysis §3.1, DELIVERY-PLAN wave 3.

DEC_UPLOAD = {
 'k':'decision','id':'A4-a','status':'rec','open':True,
 'q':('Does the report upload go through <code>/worker/generate-file</code>, or does the worker get its own S3 client?',
      'O upload do relatório passa pelo <code>/worker/generate-file</code>, ou o worker ganha um cliente S3 próprio?'),
 'intro':(
  'The spec names this one explicitly — <strong>“Decide the upload path”</strong>. <code>uploadService.uploadText</code> has no worker equivalent, '
  'but <code>/worker/generate-file</code> already exists and is the established contract. Analysis §3.1 says the same thing from the other side: the upload '
  '“has a direct equivalent in the existing <code>/worker/generate-file</code> callback, <em>or can be re-implemented worker-side against the same bucket</em>”. '
  'That “or” is the fork. It matters more than it looks, because <strong>the worker deliberately has no S3 client</strong> — which is exactly why the claim check travels through the API.',
  'A spec nomeia esta decisão explicitamente — <strong>“Decidir o caminho de upload”</strong>. O <code>uploadService.uploadText</code> não tem equivalente no worker, '
  'mas o <code>/worker/generate-file</code> já existe e é o contrato estabelecido. A análise §3.1 diz o mesmo pelo outro lado: o upload '
  '“tem equivalente direto no callback <code>/worker/generate-file</code> existente, <em>ou pode ser reimplementado no worker contra o mesmo bucket</em>”. '
  'Esse “ou” é a bifurcação. Importa mais do que parece, porque <strong>o worker deliberadamente não tem cliente S3</strong> — e é justamente por isso que o claim check trafega pela API.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Call <code>/worker/generate-file</code>','Chamar o <code>/worker/generate-file</code>'),
   'tag':('recommended','recomendada'),
   'how':('The worker composes the document and hands it to the callback the API already exposes. No storage credential ever reaches a worker replica.',
          'O worker compõe o documento e o entrega ao callback que a API já expõe. Nenhuma credencial de storage chega a uma réplica do worker.'),
   'pros':[('It is the contract every migrated node that produces a file already uses — nothing new to learn or to review',
            'É o contrato que todo node migrado que produz arquivo já usa — nada novo para aprender ou revisar'),
           ('Keeps the worker free of storage credentials, which is the property the claim-check design depends on',
            'Mantém o worker sem credenciais de storage, que é a propriedade de que o desenho do claim check depende'),
           ('Nothing to deploy per environment — the canary stays a canary','Nada para implantar por ambiente — o canário continua sendo um canário')],
   'cons':[('The document makes a round trip through the API — the same anti-goal review §2.4 names for the claim check',
            'O documento faz um round trip pela API — o mesmo anti-objetivo que a review §2.4 aponta no claim check')],
   'cost':[('lo',('Client effort: <b>none — output is unchanged</b>','Esforço do cliente: <b>nenhum — a saída não muda</b>')),
           ('lo',('Ours: <b>reuse one existing callback</b>','Nosso: <b>reaproveitar um callback existente</b>'))]},
  {'ltr':'B','name':('Give the worker its own S3 client','Dar ao worker um cliente S3 próprio'),
   'tag':('bigger question','questão maior'),
   'how':('<code>uploadText</code> is re-implemented worker-side against the same bucket, as analysis §3.1 allows. The report never touches the API.',
          'O <code>uploadText</code> é reimplementado no worker contra o mesmo bucket, como a análise §3.1 permite. O relatório nunca toca a API.'),
   'pros':[('Removes the round trip, in the direction review §2.4 argues for','Remove o round trip, na direção que a review §2.4 defende'),
           ('The same change <code>S5</code> weighs for the claim check — if it happens, this node comes along for free',
            'A mesma mudança que a <code>S5</code> avalia para o claim check — se acontecer, este node vem junto de graça')],
   'cons':[('Every worker replica needs scoped storage credentials — a real identity change, per environment',
            'Toda réplica do worker precisa de credenciais de storage com escopo — uma mudança de identidade real, por ambiente'),
           ('It makes the cheapest node in the catalogue the place where a credentials decision gets made, which is how a canary stops being one',
            'Faz do node mais barato do catálogo o lugar onde uma decisão de credenciais é tomada, que é como um canário deixa de ser canário')],
   'cost':[('lo',('Client impact: <b>none</b>','Impacto no cliente: <b>nenhum</b>')),
           ('hi',('Ours: <b>IAM + a deploy per environment</b>','Nosso: <b>IAM + um deploy por ambiente</b>'))]},
 ],
 'rec':(
  '<p><strong>A, and record it.</strong> The spec already states the preference — “prefer the callback over a second S3 client in the worker” — so what is open is not really <em>which</em>, but whether we write it down before the code exists. Write it down.</p>'
  '<p>The reason is the canary: <code>A4</code> exists to re-validate the activity template end to end, and a migration that also introduces a new credential path is no longer measuring the template. If the worker does get storage credentials, that is a whole-epic decision with <code>S5</code>&#x27;s arguments behind it — not something the cheapest node in the catalogue smuggles in.</p>',
  '<p><strong>A, e registrar.</strong> A spec já declara a preferência — “prefira o callback a um segundo cliente S3 no worker” — então o que está aberto não é bem <em>qual</em>, e sim se registramos isso antes de o código existir. Registre.</p>'
  '<p>A razão é o canário: a <code>A4</code> existe para re-validar o template de activity de ponta a ponta, e uma migração que também introduz um caminho de credencial novo deixa de medir o template. Se o worker vier a ter credenciais de storage, isso é uma decisão de épico inteiro, com os argumentos da <code>S5</code> atrás — não algo que o node mais barato do catálogo faz entrar de contrabando.</p>'),
 'who':[('Engineering','Engenharia'),('Infra owns B','Infra decide a B')],
}

TASK = {
 'code':'A4','vnum':'4',
 'title':('Migrate <code>reportBuilder</code>','Migrar o <code>reportBuilder</code>'),
 'goal':('Move the <b>cheapest node in the catalogue</b> into the worker, and use it to re-validate the activity template end to end — <b>byte for byte</b>.',
         'Mover o <b>node mais barato do catálogo</b> para o worker, e usá-lo para re-validar o template de activity de ponta a ponta — <b>byte a byte</b>.'),
 'glance':[
  ('crit',('Risk','Risco'),('The lowest in the set','O menor do conjunto'),
   ('No billing, no model access, no mutable engine state (analysis §3.1). Pure compute plus one upload.',
    'Sem cobrança, sem acesso a modelo, sem estado mutável do engine (análise §3.1). Puro cálculo mais um upload.')),
  ('dep',('Depends on','Depende de'),('A1 · right after A2','A1 · logo depois da A2'),
   ('The activity template has to be fresh — re-validating it is what this task is for.',
    'O template de activity precisa estar fresco — re-validá-lo é a razão desta task.')),
  ('wave',('Wave','Onda'),('Wave 3','Onda 3'),
   ('First node of the wave. It proves the pipeline before the expensive migrations start using it.',
    'Primeiro node da onda. Prova o pipeline antes de as migrações caras passarem a usá-lo.')),
  ('ship',('Acceptance','Critério de aceite'),('Byte-identical output','Saída byte a byte idêntica'),
   ('Any difference is a defect in this task, not an improvement. The report format does not change here.',
    'Qualquer diferença é um defeito desta task, não uma melhoria. O formato do relatório não muda aqui.')),
 ],
 'lede':(
  '<p><code>reportBuilder</code> is pure compute plus one upload: it sorts <code>data.variables</code> by <code>(y, x)</code>, escapes HTML, composes the document and calls <code>uploadService.uploadText</code>. Handler <code>reportBuilderNode()</code> in <code>flux.service.ts</code>, dispatched from the node-type switch.</p>'
  '<p>It is <strong>the only remaining node where a migration exercises the whole pipeline</strong> — registration, dispatch, persistence, notification — <em>without</em> a provider surface or a new contract obscuring a failure. That is what makes it the right canary, and not merely the easiest win.</p>',
  '<p>O <code>reportBuilder</code> é puro cálculo mais um upload: ordena <code>data.variables</code> por <code>(y, x)</code>, escapa HTML, compõe o documento e chama <code>uploadService.uploadText</code>. Handler <code>reportBuilderNode()</code> em <code>flux.service.ts</code>, despachado pelo switch de tipo de node.</p>'
  '<p>É <strong>o único node restante em que uma migração exercita o pipeline inteiro</strong> — registro, dispatch, persistência, notificação — <em>sem</em> uma superfície de provedor ou um contrato novo escondendo uma falha. É isso que o torna o canário certo, e não apenas a vitória mais fácil.</p>'),
 'blocks':[
  {'k':'label','n':'1','t':('Why this node is the canary','Por que este node é o canário')},
  {'k':'table',
   'head':[('What a migration usually drags in','O que uma migração costuma arrastar'),
           ('<code>reportBuilder</code>','<code>reportBuilder</code>'),
           ('What that buys the canary','O que isso dá ao canário')],
   'rows':[
    [{'t':('Billing','Cobrança')},{'t':('None','Nenhuma'),'pill':'ok'},
     ('No <code>token_transactions</code> parity to prove, so a pipeline failure cannot hide behind a billing difference.',
      'Nenhuma paridade de <code>token_transactions</code> a provar, então uma falha de pipeline não pode se esconder atrás de uma diferença de cobrança.')],
    [{'t':('Model access','Acesso a modelo')},{'t':('None','Nenhum'),'pill':'ok'},
     ('Nothing to validate through <code>/worker/validate-model-access</code>, so no entitlement question is mixed into the result.',
      'Nada a validar via <code>/worker/validate-model-access</code>, então nenhuma questão de direito de uso se mistura ao resultado.')],
    [{'t':('Mutable engine state','Estado mutável do engine')},{'t':('Output plumbing only','Só encanamento de saída'),'pill':'ok'},
     ('<code>myUpdatedNodes</code>, <code>onMutateSchema</code>, <code>objectCallerData</code> — all of it carries the result out, none of it steers the node.',
      '<code>myUpdatedNodes</code>, <code>onMutateSchema</code>, <code>objectCallerData</code> — tudo carrega o resultado para fora, nada disso conduz o node.')],
    [{'t':('External I/O','I/O externo')},{'t':('One upload','Um upload'),'pill':'weak'},
     ('<code>uploadService.uploadText</code> — the single contract this task has to decide, and it is the decision below.',
      '<code>uploadService.uploadText</code> — o único contrato que esta task precisa decidir, e é a decisão abaixo.')],
    [{'t':('Extra parameters','Parâmetros extras')},{'t':('Already available','Já disponíveis'),'pill':'ok'},
     ('<code>flowId</code>, <code>userId</code>, <code>spaceId</code> are in <code>ExecuteNodeActivityProps</code> or derivable from it (analysis §3.1).',
      '<code>flowId</code>, <code>userId</code>, <code>spaceId</code> estão em <code>ExecuteNodeActivityProps</code> ou são deriváveis dele (análise §3.1).')],
    [{'t':('Output','Saída')},{'t':('A composed document','Um documento composto'),'pill':'weak'},
     ('Sorted by <code>(y, x)</code> and HTML-escaped. Byte-identical is the acceptance criterion, so any drift shows up as a diff rather than as a feeling.',
      'Ordenado por <code>(y, x)</code> e com HTML escapado. Byte a byte idêntico é o critério de aceite, então qualquer desvio aparece como diff e não como impressão.')],
   ]},
  {'k':'label','n':'2','t':('The decision this task needs','A decisão que esta task precisa')},
  {'k':'prose','t':(
    'One call has to be made before the code is written, and the spec names it: where the composed report is actually written. '
    'It opens to the two options, what each costs the customer and costs us, and the one we would pick.',
    'Uma decisão precisa ser tomada antes de o código ser escrito, e a spec a nomeia: onde o relatório composto é de fato gravado. '
    'Ela abre com as duas opções, quanto cada uma custa ao cliente e a nós, e a que escolheríamos.')},
  DEC_UPLOAD,
  {'k':'label','n':'3','t':('What the task does, in three parts','O que a task faz, em três partes')},
  {'k':'part','n':'1',
   'title':('The worker module, on <code>sql-querier</code>&#x27;s shape','O módulo no worker, no formato do <code>sql-querier</code>'),
   'loc':'worker/src/modules/nodes/report-builder/',
   'purpose':('Reuse the shape a migrated node already has, so the only thing under test is the pipeline itself.',
              'Reaproveitar o formato que um node já migrado tem, para que a única coisa sob teste seja o próprio pipeline.'),
   'body':('<p>The module is a thin <code>process(props)</code> that does five things in order, and none of them is new to the worker:</p>',
           '<p>O módulo é um <code>process(props)</code> fino que faz cinco coisas em ordem, e nenhuma delas é novidade para o worker:</p>'),
   'list':[
    ('Fetch the node row.','Buscar a linha do node.'),
    ('Validate the configuration, throwing <code>UserConfigError</code> when it is the author&#x27;s mistake rather than ours.',
     'Validar a configuração, lançando <code>UserConfigError</code> quando o erro é do autor e não nosso.'),
    ('Sort <code>data.variables</code> by <code>(y, x)</code>, escape HTML, compose the document.',
     'Ordenar <code>data.variables</code> por <code>(y, x)</code>, escapar HTML, compor o documento.'),
    ('Call the file callback (Part 2).','Chamar o callback de arquivo (Parte 2).'),
    ('<code>persistNodeSuccess</code>, and return the DTO.','<code>persistNodeSuccess</code>, e devolver o DTO.'),
   ],
   'body2':('<p>Then the registry entry from <code>A1</code>, <strong>behind the flag</strong> — the new path lands disabled and is flipped in a separate deploy, per PLAN §3.2.</p>',
            '<p>Depois a entrada no registro da <code>A1</code>, <strong>atrás da flag</strong> — o caminho novo entra desligado e é virado em outro deploy, conforme PLAN §3.2.</p>'),
   'ba':(('The report is composed inside <code>flux.service.ts</code>, in the engine&#x27;s process, dispatched from the node-type switch.',
          'O relatório é composto dentro do <code>flux.service.ts</code>, no processo do engine, despachado a partir do switch de tipo de node.'),
         ('The worker composes it, the registry says so in one place, and the flag still defaults to today&#x27;s behaviour until it is flipped.',
          'O worker o compõe, o registro diz isso em um único lugar, e a flag continua no comportamento de hoje até ser virada.'))},
  {'k':'part','n':'2',
   'title':('The upload path','O caminho de upload'),
   'loc':'/worker/generate-file',
   'purpose':('Settle where the composed document is written before any code assumes an answer.',
              'Resolver onde o documento composto é gravado antes que algum código presuma uma resposta.'),
   'body':('<p><code>uploadService.uploadText</code> has no worker equivalent. <code>/worker/generate-file</code> does exist, and it is the contract every migrated node that produces a file already uses. The alternative — a second S3 client inside the worker — is a credentials change, not an implementation detail.</p>'
           '<p>This is decision <strong>A4-a</strong> above. It is short, but it should be written down rather than discovered in review.</p>',
           '<p>O <code>uploadService.uploadText</code> não tem equivalente no worker. O <code>/worker/generate-file</code> existe, e é o contrato que todo node migrado que produz arquivo já usa. A alternativa — um segundo cliente S3 dentro do worker — é mudança de credenciais, não detalhe de implementação.</p>'
           '<p>É a decisão <strong>A4-a</strong> acima. É curta, mas deve ser registrada em vez de descoberta na revisão.</p>'),
   'ba':(('The engine calls <code>uploadService.uploadText</code> in-process. The worker has no way to write the file at all.',
          'O engine chama <code>uploadService.uploadText</code> no próprio processo. O worker não tem como gravar o arquivo.'),
         ('The worker calls the established file callback and <strong>holds no storage credentials</strong> — the same property the claim check relies on.',
          'O worker chama o callback de arquivo estabelecido e <strong>não guarda credenciais de storage</strong> — a mesma propriedade em que o claim check se apoia.'))},
  {'k':'part','n':'3',
   'title':('Prove it, flip it, delete the twin','Provar, virar, apagar o gêmeo'),
   'loc':'flux.service.ts',
   'purpose':('A node is not migrated when its activity exists — it is migrated when the inline twin is gone.',
              'Um node não está migrado quando a activity existe — está migrado quando o gêmeo inline some.'),
   'body':('<p>Run both implementations over <strong>every distinct <code>reportBuilder</code> configuration in the dev database</strong> and diff the produced text. Then flip the flag in its own deploy. Then delete the <code>reportBuilderNode()</code> handler and its dispatch case — PLAN §3.4 point 4 is satisfied by deletion or by a guard that cannot double-fire, and here deletion is available.</p>'
           '<p>One behaviour is easy to lose in a rewrite: <strong>empty <code>variables</code> returns early</strong> in the inline version. The worker has to match that, rather than politely producing an empty document.</p>',
           '<p>Rode as duas implementações sobre <strong>toda configuração distinta de <code>reportBuilder</code> no banco de dev</strong> e faça o diff do texto produzido. Depois vire a flag, em deploy próprio. Depois apague o handler <code>reportBuilderNode()</code> e o seu caso de dispatch — o ponto 4 do PLAN §3.4 se satisfaz com a deleção ou com uma guarda que impeça disparo duplo, e aqui a deleção está disponível.</p>'
           '<p>Um comportamento é fácil de perder numa reescrita: <strong><code>variables</code> vazio retorna cedo</strong> na versão inline. O worker precisa fazer o mesmo, em vez de gentilmente produzir um documento vazio.</p>'),
   'ba':(('Two implementations of the same report could coexist, and only a reader comparing them by eye would notice they had drifted.',
          'Duas implementações do mesmo relatório poderiam coexistir, e só um leitor comparando a olho perceberia que divergiram.'),
         ('One implementation, proven equal over the stored configurations before the other one is removed.',
          'Uma implementação, provada igual sobre as configurações guardadas antes de a outra ser removida.')),
   'callouts':[
    ('mig',('The wave&#x27;s latency regression starts here','A regressão de latência da onda começa aqui'),
     ('<p>Every node migrated in this wave becomes a <strong>blocking round trip</strong> until Wave 5 turns on parallelism (review §4.5, risk <strong>R4</strong>). <code>reportBuilder</code> is the first one and the cheapest, which makes it the best place to <strong>measure</strong> the round-trip cost every later node in the wave will pay.</p>'
      '<p>DELIVERY-PLAN asks for the number per task, in the PR. A team surprised by it in production asks to roll the migration back; a team that was told the number expects it.</p>',
      '<p>Todo node migrado nesta onda vira um <strong>round trip bloqueante</strong> até a Onda 5 ligar o paralelismo (review §4.5, risco <strong>R4</strong>). O <code>reportBuilder</code> é o primeiro e o mais barato, o que faz dele o melhor lugar para <strong>medir</strong> o custo de round trip que todo node seguinte da onda vai pagar.</p>'
      '<p>O DELIVERY-PLAN pede o número por task, no PR. Um time surpreendido por ele em produção pede para reverter a migração; um time que recebeu o número o espera.</p>'))]},
 ],
 'verif':[
  (True,('Negative control — the sort','Controle negativo — a ordenação'),
   ('Remove the <code>y</code>-then-<code>x</code> sort from the worker implementation and confirm a test fails on variable ordering. <strong>Layout order is the node&#x27;s whole behaviour</strong> — a suite that passes without it is testing nothing.',
    'Remova a ordenação <code>y</code>-depois-<code>x</code> da implementação do worker e confirme que um teste falha na ordem das variáveis. <strong>A ordem de layout é o comportamento inteiro do node</strong> — uma suíte que passa sem ela não está testando nada.')),
  (True,('Byte-identical output','Saída byte a byte idêntica'),
   ('Run both implementations over <strong>every distinct <code>reportBuilder</code> configuration in the dev database</strong> and diff the produced text. Any difference is a defect in this task, <strong>not an improvement</strong> — the format is explicitly out of scope.',
    'Rode as duas implementações sobre <strong>toda configuração distinta de <code>reportBuilder</code> no banco de dev</strong> e faça o diff do texto produzido. Qualquer diferença é um defeito desta task, <strong>não uma melhoria</strong> — o formato está explicitamente fora de escopo.')),
  (False,('The empty case','O caso vazio'),
   ('Empty <code>variables</code> returns early in the inline version. Confirm the worker matches that, rather than producing an empty document that looks like a successful run.',
    '<code>variables</code> vazio retorna cedo na versão inline. Confirme que o worker faz o mesmo, em vez de produzir um documento vazio que parece um run bem-sucedido.')),
  (False,('State the latency number','Diga o número da latência'),
   ('<strong>DELIVERY-PLAN, wave 3.</strong> The node becomes a blocking round trip until Wave 5. Measure it and state the number in the PR — this is the cheapest node in the wave, so its number is the <strong>floor</strong> for every other migration here.',
    '<strong>DELIVERY-PLAN, onda 3.</strong> O node vira um round trip bloqueante até a Onda 5. Meça e informe o número no PR — este é o node mais barato da onda, então o número dele é o <strong>piso</strong> para todas as outras migrações daqui.')),
 ],
 'done':('<code>reportBuilder</code> satisfies <strong>PLAN §3.4</strong> — all seven points, not just a working activity — its output is <strong>proven identical over the stored configurations</strong>, the upload path is written down, and the inline <code>reportBuilderNode()</code> handler with its dispatch case is <strong>deleted</strong>.',
         'O <code>reportBuilder</code> satisfaz o <strong>PLAN §3.4</strong> — os sete pontos, não só uma activity funcionando — sua saída está <strong>provada idêntica sobre as configurações guardadas</strong>, o caminho de upload está registrado, e o handler inline <code>reportBuilderNode()</code> com o seu caso de dispatch foi <strong>apagado</strong>.'),
 'files':[
  ('worker/src/modules/nodes/report-builder/',True),
  ('worker/src/modules/nodes/nodes.types.ts',False),
  ('worker/src/modules/temporal/**',False),
  ('back/src/app-api/flux/flux.service.ts (reportBuilderNode() + its dispatch case)',False),
  ('the A1 dispatch registry',False),
 ],
}

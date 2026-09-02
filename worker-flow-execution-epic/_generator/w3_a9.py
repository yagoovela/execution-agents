# -*- coding: utf-8 -*-
# A9 — Outbound delivery as activities.
# Source: TASK-A9-OUTBOUND-DELIVERY.md, ARCHITECTURE-REVIEW §11.1, DELIVERY-PLAN wave 3.

TASK = {
 'code':'A9','vnum':'3',
 'title':('Outbound delivery as activities','Entrega de saída como activities'),
 'goal':('The emails and HTTP callbacks a run sends stop being <b>fire-and-forget</b>, and start being <b>retried</b>.',
         'Os e-mails e callbacks HTTP que um run envia deixam de ser <b>dispare-e-esqueça</b>, e passam a ser <b>reenviados</b>.'),
 'glance':[
  ('crit',('Severity','Severidade'),('Silent loss','Perda silenciosa'),
   ('A customer&#x27;s webhook endpoint down for thirty seconds means the notification is lost, with a log line as the only trace.',
    'O endpoint de webhook de um cliente fora do ar por trinta segundos significa notificação perdida, com uma linha de log como único rastro.')),
  ('dep',('Depends on','Depende de'),('A1, and nothing else','A1, e nada mais'),
   ('It can ship any time after A1 — it touches no engine state and no node type.',
    'Pode entrar a qualquer momento depois da A1 — não toca estado do engine nem tipo de node.')),
  ('wave',('Wave','Onda'),('Wave 3','Onda 3'),
   ('The cleanest activity candidate left in the codebase: pure external I/O, no engine state.',
    'O candidato a activity mais limpo que sobrou no código: I/O externo puro, sem estado de engine.')),
  ('ship',('Shape','Formato'),('The hard half is done','A metade difícil está pronta'),
   ('Idempotency already exists — the Redis dedup keys (<code>email-sent:</code>, <code>email-content:</code>). Retry with backoff is the missing half.',
    'A idempotência já existe — as chaves de dedup no Redis (<code>email-sent:</code>, <code>email-content:</code>). Retry com backoff é a metade que falta.')),
 ],
 'lede':(
  '<p>The block at the end of every run (<code>flux.service.ts</code>, ~300 lines) sends emails through three paths — <code>mailService.sendMail</code>, <code>mailService.sendGmailEmail</code>, <code>microsoftMailService.sendMail</code> — and fires HTTP callbacks with <code>axios.post</code>, each wrapped in a <code>catch</code>. <strong>Nothing is retried.</strong></p>'
  '<p>This is the cleanest activity candidate left in the codebase, and the hard part is already done: the Redis dedup keys are a run-scoped <code>SET … EX 86400 NX</code> plus a shorter content hash, <strong>built exactly so a repeated attempt does not double-send</strong>. Retry with backoff is the missing half, and it is what Temporal provides.</p>',
  '<p>O bloco no fim de todo run (<code>flux.service.ts</code>, ~300 linhas) envia e-mails por três caminhos — <code>mailService.sendMail</code>, <code>mailService.sendGmailEmail</code>, <code>microsoftMailService.sendMail</code> — e dispara callbacks HTTP com <code>axios.post</code>, cada um envolvido num <code>catch</code>. <strong>Nada é reenviado.</strong></p>'
  '<p>É o candidato a activity mais limpo que sobrou no código, e a parte difícil já está feita: as chaves de dedup no Redis são um <code>SET … EX 86400 NX</code> com escopo de run mais um hash de conteúdo mais curto, <strong>construídas exatamente para que uma tentativa repetida não envie duas vezes</strong>. Retry com backoff é a metade que falta, e é o que o Temporal oferece.</p>'),
 'blocks':[
  {'k':'prose','t':(
    '<strong>What changed on 2026-08-21 (PR #1902).</strong> The api-v2 <em>consolidated</em> callback — the one that summarises the run to the caller — moved out of <code>flux.service.ts</code> into <code>apiV2Job.processor.ts</code> (<code>CALLBACK_TIMEOUT_MS = 10_000</code>), and the run&#x27;s state is now also written to <code>flow_execution_status</code>, read by <code>GET /flux/executions/:id</code>. So there are <strong>two callback sites, not one</strong>: the end-of-run block this task moves, and the processor&#x27;s consolidated callback. Cover both, or state which one stays fire-and-forget and why.',
    '<strong>O que mudou em 2026-08-21 (PR #1902).</strong> O callback <em>consolidado</em> da api-v2 — o que resume o run para quem chamou — saiu do <code>flux.service.ts</code> para o <code>apiV2Job.processor.ts</code> (<code>CALLBACK_TIMEOUT_MS = 10_000</code>), e o estado do run agora também é escrito em <code>flow_execution_status</code>, lido por <code>GET /flux/executions/:id</code>. Então há <strong>dois pontos de callback, não um</strong>: o bloco de fim de run que esta task move, e o callback consolidado do processador. Cubra os dois, ou declare qual fica dispare-e-esqueça e por quê.')},
  {'k':'label','n':'1','t':('Two channels, and why one retry policy will not do','Dois canais, e por que uma política de retry só não serve')},
  {'k':'table',
   'head':[('Channel','Canal'),('Paths today','Caminhos hoje'),('On failure today','Na falha hoje'),('Retry policy after','Política de retry depois')],
   'rows':[
    [{'t':('Email','E-mail')},
     ('<code>mailService.sendMail</code>, <code>mailService.sendGmailEmail</code>, <code>microsoftMailService.sendMail</code>',
      '<code>mailService.sendMail</code>, <code>mailService.sendGmailEmail</code>, <code>microsoftMailService.sendMail</code>'),
     {'t':('Lost, with a log line','Perdido, com uma linha de log'),'pill':'no'},
     {'t':('Conservative','Conservadora'),'pill':'weak'}],
    [{'t':('HTTP callback','Callback HTTP')},
     ('<code>axios.post</code>, each wrapped in a <code>catch</code>','<code>axios.post</code>, cada um envolvido num <code>catch</code>'),
     {'t':('Lost after thirty seconds of downtime','Perdido após trinta segundos fora do ar'),'pill':'no'},
     {'t':('Generous','Generosa'),'pill':'ok'}],
    [{'t':('Dedup, for both','Dedup, para os dois')},
     ('Run-scoped <code>SET … EX 86400 NX</code> plus a shorter content hash',
      '<code>SET … EX 86400 NX</code> com escopo de run mais um hash de conteúdo mais curto'),
     {'t':('Already there, never used as a retry net','Já existe, nunca usada como rede de retry'),'pill':'weak'},
     {'t':('Ported unchanged','Portada sem mudanças'),'pill':'ok'}],
   ]},
  {'k':'prose','t':(
    'The two policies must differ, and the reason is in the spec: <strong>a callback to a customer endpoint should retry generously</strong> — the endpoint is coming back — '
    'while <strong>an email should not retry into a rate-limited SMTP relay</strong>, where retrying is what makes the next attempt fail too. '
    'Inheriting one default for both is how a fix turns into an outage on the mail provider.',
    'As duas políticas precisam diferir, e a razão está na spec: <strong>um callback para o endpoint do cliente deve reenviar com generosidade</strong> — o endpoint volta — '
    'enquanto <strong>um e-mail não deve reenviar contra um relay SMTP com rate limit</strong>, onde reenviar é o que faz a próxima tentativa falhar também. '
    'Herdar um padrão único para os dois é como uma correção vira uma queda no provedor de e-mail.')},
  {'k':'label','n':'2','t':('What the task does, in four parts','O que a task faz, em quatro partes')},
  {'k':'part','n':'1',
   'title':('One delivery activity per channel','Uma activity de entrega por canal'),
   'loc':'flux.service.ts',
   'purpose':('Give each channel a retry policy chosen for how that channel actually fails.',
              'Dar a cada canal uma política de retry escolhida pelo modo como aquele canal falha de verdade.'),
   'body':('<p>Email and callback become two activities, with retry policies <strong>chosen per channel rather than inherited</strong>. That is the whole design decision, and it is already made: a customer endpoint that returns <code>500</code> for a minute is exactly the case retry exists for, and an SMTP relay that is rate-limiting is exactly the case where retrying makes things worse.</p>',
           '<p>E-mail e callback viram duas activities, com políticas de retry <strong>escolhidas por canal, e não herdadas</strong>. É essa a decisão de desenho, e ela já está tomada: um endpoint de cliente devolvendo <code>500</code> por um minuto é exatamente o caso para o qual o retry existe, e um relay SMTP com rate limit é exatamente o caso em que reenviar piora.</p>'),
   'ba':(('Each send is wrapped in a <code>catch</code>. A failure is a log line, and the run reports success while the customer never hears from it.',
          'Cada envio está envolvido num <code>catch</code>. Uma falha é uma linha de log, e o run reporta sucesso enquanto o cliente nunca é avisado.'),
         ('Each send is an activity with a retry policy someone chose. A transient failure resolves itself; a permanent one becomes a terminal state.',
          'Cada envio é uma activity com política de retry que alguém escolheu. Uma falha transitória se resolve sozinha; uma permanente vira um estado terminal.')),
   'callouts':[
    ('mig',('The wave asks for the number here too','A onda também pede o número aqui'),
     ('<p>DELIVERY-PLAN asks every task in this wave to <strong>measure the latency change and state it in the PR</strong> (review §4.5, risk <strong>R4</strong>). Delivery sits at the end of a run, so the round trip lands on the run&#x27;s tail rather than between its nodes — measure it anyway, because “it is only at the end” is the kind of claim that turns out to be wrong on a run with many recipients.</p>',
      '<p>O DELIVERY-PLAN pede que toda task desta onda <strong>meça a mudança de latência e informe no PR</strong> (review §4.5, risco <strong>R4</strong>). A entrega fica no fim de um run, então o round trip cai na cauda do run e não entre os nodes — meça mesmo assim, porque “é só no fim” é o tipo de afirmação que se revela errada num run com muitos destinatários.</p>'))]},
  {'k':'part','n':'2',
   'title':('The dedup keys move unchanged','As chaves de dedup vão sem mudança'),
   'loc':'flux.service.ts',
   'purpose':('Keep the exact mechanism that makes a second attempt safe, instead of re-deriving it worker-side.',
              'Manter exatamente o mecanismo que torna uma segunda tentativa segura, em vez de rederivá-lo no worker.'),
   'body':('<p>The Redis keys are <strong>the reason retry is safe</strong>: a run-scoped <code>SET … EX 86400 NX</code> plus a shorter content hash, built so a repeated attempt does not double-send. They are not an implementation detail to re-derive — <strong>port them as they are</strong>.</p>'
           '<p>A re-derived key that looks equivalent and differs in scope or TTL turns the safest part of this task into a double-sent email, which is the one failure a customer notices immediately.</p>',
           '<p>As chaves do Redis são <strong>a razão de o retry ser seguro</strong>: um <code>SET … EX 86400 NX</code> com escopo de run mais um hash de conteúdo mais curto, feitas para que uma tentativa repetida não envie duas vezes. Não são detalhe de implementação a rederivar — <strong>porte-as como estão</strong>.</p>'
           '<p>Uma chave rederivada que parece equivalente e difere em escopo ou TTL transforma a parte mais segura desta task num e-mail enviado duas vezes, que é a única falha que o cliente percebe na hora.</p>'),
   'ba':(('The keys exist and work, and nothing ever exercises them — there is no second attempt for them to suppress.',
          'As chaves existem e funcionam, e nada nunca as exercita — não há segunda tentativa para elas suprimirem.'),
         ('The same keys, in the activity, doing the job they were written for: the retry that Temporal drives cannot double-send.',
          'As mesmas chaves, dentro da activity, fazendo o trabalho para o qual foram escritas: o retry que o Temporal conduz não pode enviar duas vezes.'))},
  {'k':'part','n':'3',
   'title':('Extract the block while moving it','Extrair o bloco enquanto o move'),
   'loc':('~300 lines at flux.service.ts', '~300 linhas em flux.service.ts'),
   'purpose':('Stop the shape that has kept anyone from adding retry for as long as the block has existed.',
              'Acabar com o formato que impediu qualquer um de adicionar retry por todo o tempo em que o bloco existiu.'),
   'body':('<p>The review&#x27;s source material calls this a candidate for an <code>OutputDeliveryService</code>. <strong>300 lines of inline delivery is the reason nobody has added retry in the first place</strong> — the change was never small, so it never happened.</p>'
           '<p>Extract it while it is being moved. Doing the two separately means reading the same 300 lines twice.</p>',
           '<p>O material de origem da review chama isto de candidato a um <code>OutputDeliveryService</code>. <strong>300 linhas de entrega inline são a razão de ninguém ter adicionado retry até hoje</strong> — a mudança nunca foi pequena, então nunca aconteceu.</p>'
           '<p>Extraia enquanto move. Fazer as duas coisas separadas significa ler as mesmas 300 linhas duas vezes.</p>'),
   'ba':(('Delivery is ~300 inline lines at the end of the run method, with three mail paths and the callback logic interleaved.',
          'A entrega são ~300 linhas inline no fim do método de run, com três caminhos de e-mail e a lógica de callback entrelaçados.'),
         ('One delivery module, with the channels separated, which is what makes “add a retry policy” a small change next time.',
          'Um módulo de entrega, com os canais separados, que é o que torna “adicionar uma política de retry” uma mudança pequena da próxima vez.'))},
  {'k':'part','n':'4',
   'title':('A failure surface, because retries create terminal states','Uma superfície de falha, porque retries criam estados terminais'),
   'loc':'run log',
   'purpose':('Make a delivery that finally gave up visible to someone other than Winston.',
              'Tornar uma entrega que finalmente desistiu visível para alguém além do Winston.'),
   'body':('<p>Today a lost callback is <strong>invisible to the customer</strong>. With retries there is a terminal state — the attempt that gave up — and it should be visible <strong>in the run log at minimum</strong>.</p>'
           '<p>Out of scope, deliberately: payload shapes, recipients, and when delivery is triggered. <strong>This task moves and retries; it does not redesign.</strong></p>',
           '<p>Hoje um callback perdido é <strong>invisível para o cliente</strong>. Com retries existe um estado terminal — a tentativa que desistiu — e ele deve ser visível <strong>no log do run, no mínimo</strong>.</p>'
           '<p>Fora de escopo, de propósito: formatos de payload, destinatários, e quando a entrega é disparada. <strong>Esta task move e reenvia; não redesenha.</strong></p>'),
   'ba':(('A failed delivery exists only as a Winston line. The run shows as successful, and nobody outside the log knows the notification never arrived.',
          'Uma entrega falha existe só como uma linha do Winston. O run aparece como bem-sucedido, e ninguém fora do log sabe que a notificação nunca chegou.'),
         ('A delivery that exhausted its retries appears <strong>in the run log</strong>, as a terminal state, where the person debugging the run is already looking.',
          'Uma entrega que esgotou os retries aparece <strong>no log do run</strong>, como estado terminal, onde quem está depurando o run já está olhando.'))},
 ],
 'verif':[
  (True,('Negative control — the retry itself','Controle negativo — o próprio retry'),
   ('Point a callback at an endpoint that returns <code>500</code> twice then <code>200</code>, and confirm the delivery succeeds after retry. Then <strong>break the retry policy and confirm the test fails</strong> — a retry that is configured but never exercised is not a retry.',
    'Aponte um callback para um endpoint que devolve <code>500</code> duas vezes e depois <code>200</code>, e confirme que a entrega tem sucesso após o retry. Depois <strong>quebre a política de retry e confirme que o teste falha</strong> — um retry configurado e nunca exercitado não é um retry.')),
  (True,('Double-send, in both directions','Envio duplo, nos dois sentidos'),
   ('Force the activity to run twice for the same run and node and confirm the dedup key <strong>suppresses the second</strong>. Then <strong>delete the key and confirm it double-sends</strong> — that second half is what proves the key is load-bearing rather than decorative, and it is a customer-visible failure, so it deserves the proof.',
    'Force a activity a rodar duas vezes para o mesmo run e node e confirme que a chave de dedup <strong>suprime a segunda</strong>. Depois <strong>apague a chave e confirme que envia duas vezes</strong> — essa segunda metade é o que prova que a chave é estrutural e não decorativa, e é uma falha visível ao cliente, então merece a prova.')),
  (True,('Email parity across all three paths','Paridade de e-mail nos três caminhos'),
   ('Same recipients, same attachments, same body, before and after — for <code>sendMail</code>, <code>sendGmailEmail</code> and <code>microsoftMailService.sendMail</code>. Three paths means three ways for a body or an attachment to quietly change.',
    'Mesmos destinatários, mesmos anexos, mesmo corpo, antes e depois — para <code>sendMail</code>, <code>sendGmailEmail</code> e <code>microsoftMailService.sendMail</code>. Três caminhos significam três formas de um corpo ou um anexo mudar em silêncio.')),
  (False,('The failure is visible where people look','A falha é visível onde as pessoas olham'),
   ('Confirm a terminal delivery failure appears <strong>in the run log</strong> rather than only in Winston. A retry that ends in silence is the same defect with more steps.',
    'Confirme que uma falha terminal de entrega aparece <strong>no log do run</strong>, e não só no Winston. Um retry que termina em silêncio é o mesmo defeito com mais etapas.')),
 ],
 'done':('Email and callback delivery run <strong>as activities with per-channel retry policies</strong>, the Redis dedup keys moved <strong>unchanged</strong> and were proven load-bearing in both directions, email output matches across all three paths, a delivery that exhausted its retries is <strong>visible in the run log</strong>, and the processor&#x27;s consolidated callback (PR #1902) is either covered by the same activity or explicitly left fire-and-forget, with the reason in the PR — with payloads, recipients and triggers unchanged.',
         'A entrega de e-mail e de callback roda <strong>como activities com políticas de retry por canal</strong>, as chaves de dedup do Redis foram <strong>portadas sem mudança</strong> e provadas estruturais nos dois sentidos, a saída de e-mail bate nos três caminhos, uma entrega que esgotou os retries é <strong>visível no log do run</strong>, e o callback consolidado do processador (PR #1902) está coberto pela mesma activity ou explicitamente deixado como dispare-e-esqueça, com o motivo no PR — com payloads, destinatários e disparos inalterados.'),
 'files':[
  ('back/src/app-api/flux/flux.service.ts (end-of-run delivery block: sendMail · sendGmailEmail · microsoftMailService.sendMail · axios.post · email-sent:/email-content: dedup)',False),
  ('back/src/jobs/apiV2Job/apiV2Job.processor.ts (the api-v2 consolidated callback, moved there 2026-08-21)',False),
  ('back/src/app-api/mail/',False),
  ('back/src/app-api/microsoft/',False),
  ('new worker delivery module',True),
  ('the A1 dispatch registry',False),
 ],
}

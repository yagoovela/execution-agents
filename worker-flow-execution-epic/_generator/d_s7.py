# -*- coding: utf-8 -*-

DEC_TRANSPORT = {
 'k':'decision','id':'S7-a','status':'open','open':True,
 'q':('How does the webhook secret travel, so the customer does not have to build an auth system?',
      'Por onde viaja o segredo do webhook, sem obrigar o cliente a construir um sistema de autenticação?'),
 'intro':(
  'The spec says <strong>“a per-flow webhook secret”</strong> but never says <em>where it goes</em>. That is this decision. '
  'The framing that matters: this is not “add authentication”, it is <strong>stop using a non-secret identifier as the secret</strong>. '
  'Today the credential is the <code>flowId</code> — a UUID that travels through published interfaces, chatbot routes, shared links and the MCP surface. '
  'It is secret by accident, and it cannot be rotated because it is the primary key. Whatever we pick below, the flow id leaves the URL and a rotatable token resolves the flow.',
  'A spec diz <strong>“um segredo de webhook por fluxo”</strong> mas nunca diz <em>por onde ele vai</em>. É esta a decisão. '
  'O enquadramento que importa: isto não é “adicionar autenticação”, é <strong>parar de usar um identificador não secreto como se fosse segredo</strong>. '
  'Hoje a credencial é o <code>flowId</code> — um UUID que circula por interfaces publicadas, rotas de chatbot, links compartilhados e pela superfície MCP. '
  'Ele é secreto por acidente, e não pode ser rotacionado porque é a chave primária. Qualquer que seja a escolha abaixo, o id do fluxo sai da URL e um token rotacionável resolve o fluxo.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Token in the URL path','Token no path da URL'),
   'tag':('default','padrão'),
   'how':('<code>POST /flux/hooks/&lt;token&gt;</code> — the customer copies one URL and pastes it. The token resolves the flow; the flow id never appears.',
          '<code>POST /flux/hooks/&lt;token&gt;</code> — o cliente copia uma URL e cola. O token resolve o fluxo; o id do fluxo não aparece.'),
   'pros':[('Works in every tool, including the ones whose only field is “URL”','Funciona em qualquer ferramenta, inclusive as que só têm o campo “URL”'),
           ('This is what Zapier, Make, Trello and Asana do — the URL <em>is</em> the credential','É o que Zapier, Make, Trello e Asana fazem — a URL <em>é</em> a credencial'),
           ('Rotating it is re-copying a URL, not a code change','Rotacionar é recopiar uma URL, não mudar código')],
   'cons':[('Bearer secret in a URL: it reaches ALB access logs, APM traces and error trackers unless actively scrubbed','Segredo portador numa URL: chega no access log do ALB, em traces de APM e em trackers de erro se não houver scrub ativo'),
           ('Anyone who sees the URL can trigger the flow','Quem vê a URL pode disparar o fluxo')],
   'cost':[('lo',('Client effort: <b>paste a URL</b>','Esforço do cliente: <b>colar uma URL</b>')),
           ('hi',('Ours: <b>log scrubbing is mandatory</b>','Nosso: <b>scrub de log é obrigatório</b>'))]},
  {'ltr':'B','name':('Same token, in a header','Mesmo token, num header'),
   'tag':('already the pattern','já é o padrão'),
   'how':('The customer sends the token as a request header. <strong>This mechanism already exists</strong> — <code>ApiKeyGuard</code> reads <code>headers[&#x27;api-key&#x27;]</code> today (<code>apikey.guard.ts</code>).',
          'O cliente manda o token como header da requisição. <strong>Esse mecanismo já existe</strong> — o <code>ApiKeyGuard</code> lê <code>headers[&#x27;api-key&#x27;]</code> hoje (<code>apikey.guard.ts</code>).'),
   'pros':[('Does not land in access logs, Referer or analytics','Não cai em access log, Referer nem analytics'),
           ('No new transport to build — the guard pattern is already in the codebase','Nenhum transporte novo — o padrão do guard já está no código')],
   'cons':[('Some callers cannot set headers at all — a CRM field, a legacy form, a no-code step','Alguns chamadores não conseguem definir headers — um campo de CRM, um formulário legado, um passo no-code'),
           ('Alone, it excludes exactly the customers this task is trying not to burden','Sozinho, exclui justamente os clientes que a task não quer sobrecarregar')],
   'cost':[('lo',('Client effort: <b>one header</b>','Esforço do cliente: <b>um header</b>')),
           ('lo',('Ours: <b>reuses the existing guard</b>','Nosso: <b>reaproveita o guard existente</b>'))]},
  {'ltr':'C','name':('HMAC signature','Assinatura HMAC'),
   'tag':('opt-in','opcional'),
   'how':('The caller signs the body with a shared secret and sends the digest, the way Stripe and GitHub webhooks work. We verify the signature and a timestamp.',
          'O chamador assina o corpo com um segredo compartilhado e envia o digest, como funcionam os webhooks do Stripe e do GitHub. Verificamos a assinatura e um timestamp.'),
   'pros':[('The secret never travels; a captured request cannot be replayed','O segredo nunca viaja; uma requisição capturada não pode ser reproduzida'),
           ('The answer a customer&#x27;s security team will ask for by name','A resposta que o time de segurança de um cliente vai pedir pelo nome')],
   'cons':[('Requires the customer to <strong>write code</strong> — the exact demand this task exists to avoid','Exige que o cliente <strong>escreva código</strong> — exatamente a demanda que esta task existe para evitar'),
           ('Cannot be the default without breaking every no-code caller','Não pode ser o padrão sem quebrar todo chamador no-code')],
   'cost':[('hi',('Client effort: <b>an implementation</b>','Esforço do cliente: <b>uma implementação</b>')),
           ('',('Ours: <b>one verifier</b>','Nosso: <b>um verificador</b>'))]},
 ],
 'rec':(
  '<p><strong>All three, as a ladder on one token — A is the default and nobody is forced to climb.</strong> A customer who can only paste a URL is safe; a customer who can set a header is safer; a customer with a security team gets HMAC. One secret, three transports.</p>'
  '<p>Prefer <strong>path over <code>?token=</code></strong>: query strings leak in more places by default — <code>Referer</code>, proxy logs, analytics, and error trackers that capture the full <code>req.url</code>. Accept both for compatibility, but document and show the path form.</p>'
  '<p>Four things make a URL token defensible rather than a shortcut: <strong>one token = one flow</strong> (a leak costs one flow, not the account), <strong>two active tokens at once</strong> so rotation is not a breaking change, <strong>one-click revocation</strong>, and <strong>log scrubbing</strong> — the one that bites, because the ALB access log records the full path into S3.</p>',
  '<p><strong>As três, como uma escada sobre um único token — A é o padrão e ninguém é obrigado a subir.</strong> O cliente que só sabe colar uma URL fica seguro; o que consegue mandar header fica mais seguro; o que tem time de segurança usa HMAC. Um segredo, três transportes.</p>'
  '<p>Prefira <strong>path a <code>?token=</code></strong>: query string vaza em mais lugares por padrão — <code>Referer</code>, logs de proxy, analytics, e trackers de erro que capturam o <code>req.url</code> inteiro. Aceite os dois por compatibilidade, mas documente e exiba o formato de path.</p>'
  '<p>Quatro coisas tornam um token em URL defensável em vez de gambiarra: <strong>um token = um fluxo</strong> (um vazamento custa um fluxo, não a conta), <strong>dois tokens ativos ao mesmo tempo</strong> para que rotação não seja quebra, <strong>revogação em um clique</strong>, e <strong>scrub de log</strong> — o que morde, porque o access log do ALB grava o path inteiro no S3.</p>'),
 'who':[('Engineering','Engenharia'),('Product — it changes the setup flow','Produto — muda o fluxo de configuração')],
}

DEC_PUBLIC = {
 'k':'decision','id':'S7-b','status':'rec',
 'q':('What is <code>public: true</code> allowed to permit on a trigger?',
      'O que <code>public: true</code> pode permitir num gatilho?'),
 'intro':(
  'Today this is not a decision anyone made — it is an artefact of a broken <code>where</code>. The first branch of the OR has no <code>public</code> condition, '
  'so the second is dead and <em>every</em> flow matches. Fixing the predicate forces the question the code was never asked: '
  '<strong>does “public” describe who may read a flow, or who may spend its owner&#x27;s money?</strong>',
  'Hoje isto não é uma decisão que alguém tomou — é um artefato de um <code>where</code> quebrado. O primeiro ramo do OR não tem condição <code>public</code>, '
  'então o segundo está morto e <em>todo</em> fluxo casa. Corrigir o predicado força a pergunta que o código nunca fez: '
  '<strong>“público” descreve quem pode ler um fluxo, ou quem pode gastar o dinheiro do dono?</strong>'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Public means readable, never executable','Público significa legível, nunca executável'),
   'tag':('recommended','recomendada'),
   'how':('Execution <strong>always</strong> requires the token, public or not. <code>public</code> keeps governing discovery and the published interface, and nothing else.',
          'A execução <strong>sempre</strong> exige o token, público ou não. O <code>public</code> continua governando descoberta e a interface publicada, e nada mais.'),
   'pros':[('One rule for every trigger — nothing to reason about per flow','Uma regra para todo gatilho — nada a raciocinar por fluxo'),
           ('A leaked flow id stops being a spend vector entirely','Um id de fluxo vazado deixa de ser um vetor de gasto por completo'),
           ('Matches what customers already assume “public” means','Corresponde ao que os clientes já supõem que “público” significa')],
   'cons':[('If any customer relies on an open trigger today, this breaks them — the deprecation window has to find them first','Se algum cliente depende de um gatilho aberto hoje, isto o quebra — a janela de depreciação precisa encontrá-lo antes')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('lo',('Ours: <b>fix the predicate</b>','Nosso: <b>corrigir o predicado</b>'))]},
  {'ltr':'B','name':('An explicit “anyone may trigger” setting','Uma opção explícita “qualquer um pode disparar”'),
   'how':('A separate per-flow switch, off by default, distinct from <code>public</code>. Turning it on <strong>requires</strong> a rate limit and a spend ceiling on that flow.',
          'Um switch separado por fluxo, desligado por padrão, distinto de <code>public</code>. Ligá-lo <strong>exige</strong> um rate limit e um teto de gasto naquele fluxo.'),
   'pros':[('Keeps the genuinely open use case — a public form, a demo, a status hook','Preserva o caso realmente aberto — um formulário público, uma demo, um hook de status'),
           ('The owner opts in knowingly, with the cost cap in the same screen','O dono opta conscientemente, com o teto de custo na mesma tela')],
   'cons':[('A second concept to explain, document and support','Um segundo conceito para explicar, documentar e suportar'),
           ('An open trigger is a spend vector by design — the caps become load-bearing','Um gatilho aberto é um vetor de gasto por design — os tetos passam a ser estruturais')],
   'cost':[('',('Client effort: <b>one toggle</b>','Esforço do cliente: <b>um toggle</b>')),
           ('hi',('Ours: <b>UI + caps + docs</b>','Nosso: <b>UI + tetos + docs</b>'))]},
  {'ltr':'C','no':True,'name':('Leave it as it is','Deixar como está'),
   'tag':('not viable','inviável'),
   'how':('Keep the current behaviour, in which the <code>public</code> flag has no effect on the webhook route and every flow is triggerable by id.',
          'Manter o comportamento atual, em que a flag <code>public</code> não tem efeito na rota de webhook e todo fluxo é disparável por id.'),
   'pros':[('Breaks nothing today','Não quebra nada hoje')],
   'cons':[('It is the live defect this task exists to close','É o defeito vivo que esta task existe para fechar'),
           ('Private flows stay executable by anyone holding an id that was never treated as a secret','Fluxos privados seguem executáveis por qualquer um com um id que nunca foi tratado como segredo')],
   'cost':[('',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('hi',('Ours: <b>the exposure stays</b>','Nosso: <b>a exposição continua</b>'))]},
 ],
 'rec':(
  '<p><strong>A, with B available only if a real customer asks for it.</strong> Do not ship B speculatively: an open trigger is a spend vector, and every one that exists has to be watched.</p>'
  '<p>Whichever is chosen, <strong>write it down</strong> — the point of this decision is that today nobody can say what <code>public</code> was supposed to mean here, and the next person to read the <code>where</code> clause will guess again.</p>',
  '<p><strong>A, com B disponível só se um cliente real pedir.</strong> Não entregue B por especulação: um gatilho aberto é um vetor de gasto, e cada um que existir precisa ser vigiado.</p>'
  '<p>Seja qual for a escolha, <strong>registre-a</strong> — o ponto desta decisão é que hoje ninguém sabe dizer o que <code>public</code> deveria significar aqui, e a próxima pessoa a ler o <code>where</code> vai adivinhar de novo.</p>'),
 'who':[('Product','Produto'),('Engineering confirms the blast radius','Engenharia confirma o raio de impacto')],
}

DEC_EMAIL = {
 'k':'decision','id':'S7-c','status':'rec',
 'q':('How is the email sender verified, without asking anyone to configure anything?',
      'Como o remetente do e-mail é verificado, sem pedir configuração a ninguém?'),
 'intro':(
  'Agents are started by email too. The flow is resolved from a UUID in the recipient&#x27;s local part (<code>mail.service.ts</code>), '
  'then <code>From</code>, <code>Subject</code>, the body and the attachments are fed into the flow&#x27;s <code>varInputNode</code>. '
  'For a <strong>private</strong> flow the only check is that the <code>From</code> header matches the owner — and greps for <code>dkim</code>, <code>spf</code>, <code>dmarc</code> in <code>app-api/mail/</code> return nothing. '
  'For a <strong>public</strong> flow there is no sender check at all.',
  'Agentes também são iniciados por e-mail. O fluxo é resolvido a partir de um UUID na parte local do destinatário (<code>mail.service.ts</code>), '
  'e então <code>From</code>, <code>Subject</code>, o corpo e os anexos são injetados no <code>varInputNode</code> do fluxo. '
  'Para um fluxo <strong>privado</strong> a única checagem é o <code>From</code> casar com o dono — e buscas por <code>dkim</code>, <code>spf</code>, <code>dmarc</code> em <code>app-api/mail/</code> não retornam nada. '
  'Para um fluxo <strong>público</strong> não há checagem de remetente nenhuma.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('The address is the credential','O endereço é a credencial'),
   'tag':('recommended','recomendada'),
   'how':('<code>&lt;token&gt;@upload.fluxprompt.com</code> — a high-entropy token, not the flow id. Possession of the address <em>is</em> the authorisation. This is Trello&#x27;s and Asana&#x27;s email-in pattern.',
          '<code>&lt;token&gt;@upload.fluxprompt.com</code> — um token de alta entropia, não o id do fluxo. A posse do endereço <em>é</em> a autorização. É o padrão de entrada por e-mail do Trello e do Asana.'),
   'pros':[('Zero configuration for the customer — they save a contact','Zero configuração para o cliente — ele salva um contato'),
           ('Enforceable in this codebase today; does not depend on the mail provider&#x27;s headers','Aplicável neste código hoje; não depende dos cabeçalhos do provedor de e-mail'),
           ('Rotates per flow, and stops leaking the internal flow id','Rotaciona por fluxo, e para de vazar o id interno do fluxo')],
   'cons':[('Email addresses leak by nature — CC, reply, forward, saved in someone&#x27;s contacts','Endereços de e-mail vazam por natureza — cópia, resposta, encaminhamento, salvos no contato de alguém'),
           ('Rotation is more disruptive than a webhook URL: the customer may have automations pointing at it','Rotacionar incomoda mais que uma URL de webhook: o cliente pode ter automações apontando para lá')],
   'cost':[('lo',('Client effort: <b>save an address</b>','Esforço do cliente: <b>salvar um endereço</b>')),
           ('lo',('Ours: <b>token lookup instead of a UUID regex</b>','Nosso: <b>lookup por token em vez de regex de UUID</b>'))]},
  {'ltr':'B','name':('Verify DKIM / SPF / DMARC','Verificar DKIM / SPF / DMARC'),
   'how':('Check the authentication results at the mail boundary before the message is trusted, so a forged <code>From</code> is rejected on its own merits.',
          'Checar os resultados de autenticação na fronteira de e-mail antes de confiar na mensagem, de modo que um <code>From</code> forjado seja rejeitado por si só.'),
   'pros':[('The standard answer, and the only one that makes <code>From</code> mean anything','A resposta padrão, e a única que faz o <code>From</code> significar alguma coisa'),
           ('Composes with A — it can be added later without undoing it','Compõe com A — pode ser adicionada depois sem desfazer nada')],
   'cons':[('Depends on headers the mail provider supplies, and on its configuration','Depende de cabeçalhos que o provedor de e-mail fornece, e da configuração dele'),
           ('Legitimate senders fail DMARC often enough that this refuses real traffic — mailing lists, forwarders','Remetentes legítimos falham DMARC com frequência suficiente para recusar tráfego real — listas, encaminhadores')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('hi',('Ours: <b>provider-dependent</b>','Nosso: <b>depende do provedor</b>'))]},
  {'ltr':'C','name':('Sender allowlist per flow','Allowlist de remetentes por fluxo'),
   'tag':('pairs with A','combina com A'),
   'how':('The owner types which addresses may trigger this flow. The message must come from one of them <em>and</em> reach the secret address.',
          'O dono digita quais endereços podem disparar aquele fluxo. A mensagem precisa vir de um deles <em>e</em> chegar no endereço secreto.'),
   'pros':[('Cheap for the customer, and it is a control they understand','Barato para o cliente, e é um controle que ele entende'),
           ('Turns a leaked address into a much smaller problem','Transforma um endereço vazado num problema bem menor')],
   'cons':[('<code>From</code> is forgeable, so alone it authenticates nothing','O <code>From</code> é forjável, então sozinha ela não autentica nada'),
           ('Only defence in depth — never the primary control','Só defesa em profundidade — nunca o controle primário')],
   'cost':[('',('Client effort: <b>type addresses</b>','Esforço do cliente: <b>digitar endereços</b>')),
           ('lo',('Ours: <b>one list field</b>','Nosso: <b>um campo de lista</b>'))]},
 ],
 'rec':(
  '<p><strong>A now, C alongside it, B later.</strong> A is the primary control and it is the one that costs the customer nothing. '
  'C composes with it for free and shrinks the damage when an address inevitably leaks. B is the more standard answer and can be layered on afterwards without undoing either.</p>'
  '<p>One correction to the spec as written: it proposed <code>&lt;flowId&gt;+&lt;token&gt;@…</code>. <strong>Drop the flow id.</strong> Keeping it exposes an internal identifier and makes the address partly guessable, for no benefit — the token can resolve the flow on its own.</p>',
  '<p><strong>A agora, C junto, B depois.</strong> A é o controle primário e é o que não custa nada ao cliente. '
  'C compõe com ela de graça e reduz o estrago quando um endereço inevitavelmente vazar. B é a resposta mais padrão e pode ser somada depois sem desfazer nenhuma das duas.</p>'
  '<p>Uma correção à spec como está escrita: ela propunha <code>&lt;flowId&gt;+&lt;token&gt;@…</code>. <strong>Tire o id do fluxo.</strong> Mantê-lo expõe um identificador interno e torna o endereço parcialmente adivinhável, sem benefício algum — o token resolve o fluxo sozinho.</p>'),
 'who':[('Engineering','Engenharia'),('Product owns the public-flow half','Produto decide a metade dos fluxos públicos')],
}

DEC_ADMISSION = {
 'k':'decision','id':'S7-d','status':'rec',
 'q':('At the limit, does the caller get a <code>429</code> or does the run get queued?',
      'No limite, o chamador recebe <code>429</code> ou o run é enfileirado?'),
 'intro':(
  'The Bull processor&#x27;s concurrency (<code>AGENT_CONCURRENCY</code>, default five per replica) already throttles <strong>execution</strong>. It does not throttle <strong>admission</strong> — '
  'the queue still grows, and a row, a log line and a dedup key are written for every call on the way in. This decision is about what happens at the door.',
  'A concorrência do processador Bull (<code>AGENT_CONCURRENCY</code>, cinco por réplica por padrão) já limita a <strong>execução</strong>. Ela não limita a <strong>admissão</strong> — '
  'a fila continua crescendo, e uma linha, uma linha de log e uma chave de dedup são gravadas para cada chamada na entrada. Esta decisão é sobre o que acontece na porta.'),
 'opts':[
  {'ltr':'A','pick':True,'name':('Reject with <code>429</code> and <code>Retry-After</code>','Recusar com <code>429</code> e <code>Retry-After</code>'),
   'tag':('recommended','recomendada'),
   'how':('Excess calls are refused before anything is written. The caller is told when to come back.',
          'Chamadas em excesso são recusadas antes de qualquer gravação. O chamador é informado de quando voltar.'),
   'pros':[('Queue depth and row count stop growing — which is the entire point','Profundidade de fila e contagem de linhas param de crescer — que é o ponto inteiro'),
           ('<code>429</code> + <code>Retry-After</code> is what every webhook client already knows how to handle','<code>429</code> + <code>Retry-After</code> é o que todo cliente de webhook já sabe tratar')],
   'cons':[('A legitimate caller above the limit loses that call unless it retries','Um chamador legítimo acima do limite perde aquela chamada se não tentar de novo')],
   'cost':[('lo',('Client effort: <b>honour a 429</b>','Esforço do cliente: <b>respeitar um 429</b>')),
           ('lo',('Ours: <b>a throttler guard</b>','Nosso: <b>um guard de throttle</b>'))]},
  {'ltr':'B','name':('Accept and queue','Aceitar e enfileirar'),
   'how':('Admit everything and let the queue absorb the burst, the way <code>S3</code> handles excess tenant runs.',
          'Admitir tudo e deixar a fila absorver o pico, como a <code>S3</code> trata runs excedentes de um tenant.'),
   'pros':[('No legitimate call is ever lost','Nenhuma chamada legítima é perdida'),
           ('No client-side retry logic needed','Nenhuma lógica de retry no cliente')],
   'cons':[('Queueing an unbounded inbound flood just <strong>moves</strong> it — the writes still happen','Enfileirar uma enxurrada de entrada sem limite apenas a <strong>desloca</strong> — as gravações continuam acontecendo'),
           ('The failure arrives later and further from its cause','A falha chega depois e mais longe da causa')],
   'cost':[('lo',('Client effort: <b>none</b>','Esforço do cliente: <b>nenhum</b>')),
           ('hi',('Ours: <b>the growth is unbounded</b>','Nosso: <b>o crescimento é ilimitado</b>'))]},
 ],
 'rec':(
  '<p><strong>A — and note the deliberate contrast with <code>S3</code>.</strong> There, excess <em>tenant</em> runs are queued, because that caller is already entitled to the work. '
  'Here the caller may not be entitled to anything at all. Admission is the one place where rejecting is the right answer.</p>'
  '<p>Both halves of this task refuse customer traffic, so <strong>PLAN §3.3.2 applies</strong>: count real calls per flow and per key over a full cycle, set the limits above the observed peak with margin, '
  'and run in <strong>report-only mode</strong> first. A legitimate caller refused is a production incident, not a test failure.</p>',
  '<p><strong>A — e note o contraste deliberado com a <code>S3</code>.</strong> Lá, runs excedentes de um <em>tenant</em> são enfileirados, porque aquele chamador já tem direito ao trabalho. '
  'Aqui o chamador pode não ter direito a nada. A admissão é o único lugar onde recusar é a resposta certa.</p>'
  '<p>As duas metades desta task recusam tráfego de cliente, então <strong>vale o PLAN §3.3.2</strong>: conte as chamadas reais por fluxo e por chave ao longo de um ciclo completo, defina os limites acima do pico observado com margem, '
  'e rode antes em <strong>modo somente-relatório</strong>. Um chamador legítimo recusado é um incidente de produção, não uma falha de teste.</p>'),
 'who':[('Engineering','Engenharia')],
}

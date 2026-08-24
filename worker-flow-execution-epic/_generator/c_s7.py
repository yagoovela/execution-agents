# -*- coding: utf-8 -*-
# ============================ CONTENT ============================
T = {}

T['title'] = ("Authenticate and rate-limit the entry points",
              "Autenticar e limitar as portas de entrada")
T['goal'] = ("A run can only be created by <b>someone entitled to create it</b>, and no caller can create an <b>unlimited number</b> of them.",
             "Um run só pode ser criado por <b>quem tem direito de criá-lo</b>, e nenhum chamador pode criar uma <b>quantidade ilimitada</b> deles.")

GLANCE = [
  ('crit', ('Severity','Severidade'), ('Critical','Crítica'),
   ('A live, unauthenticated spend vector — not a scaling concern. Review §9.1, §9.2.',
    'Um vetor de gasto vivo e não autenticado — não é uma questão de escala. Review §9.1, §9.2.')),
  ('dep', ('Depends on','Depende de'), ('Nothing','Nada'),
   ('Nothing blocks it. Every other ceiling in this epic is downstream of admission.',
    'Nada a bloqueia. Todo outro teto deste épico está a jusante da admissão.')),
  ('wave', ('Wave','Onda'), ('Wave 0','Onda 0'),
   ('Ships before any migration work — the entry points are already exposed today.',
    'Entra antes de qualquer migração — as entradas já estão expostas hoje.')),
  ('ship', ('Ship order','Ordem de entrega'), ('Parts 1 + 3 first','Partes 1 + 3 primeiro'),
   ('The two authentication holes go out together, on their own. Rate limiting follows.',
    'Os dois furos de autenticação saem juntos, sozinhos. O rate limiting vem depois.')),
]

T['lede'] = (
 """<p><strong>Three of the four ways to start a run are effectively unauthenticated</strong> — the webhook route, the email trigger for public flows, and the email trigger for private flows via a forgeable <code>From</code> header. <strong>None of the four is rate limited.</strong></p>
<p>Every other ceiling in this epic — the sub-flow depth limit, the execution budget, the tenant spend cap — sits <em>behind</em> admission. If anyone can open the door an unlimited number of times, none of those ceilings is a guarantee.</p>""",
 """<p><strong>Três das quatro formas de iniciar um run são, na prática, não autenticadas</strong> — a rota de webhook, o disparo por e-mail para fluxos públicos, e o disparo por e-mail para fluxos privados via um cabeçalho <code>From</code> forjável. <strong>Nenhuma das quatro tem rate limit.</strong></p>
<p>Todo outro teto deste épico — o limite de profundidade de sub-fluxo, o orçamento de execução, o teto de gasto por tenant — fica <em>atrás</em> da admissão. Se qualquer um pode abrir a porta um número ilimitado de vezes, nenhum desses tetos é uma garantia.</p>""")

ENTRIES = [
  ('/flux/api-v2', ('API key','Chave de API'), 'ok',
   ('Authenticated','Autenticado'), 'no', ('None','Nenhum'),
   ('The only entry point that actually identifies its caller.',
    'A única entrada que de fato identifica quem chama.')),
  ('/flux/api-v2-webhook', ('Public route','Rota pública'), 'no',
   ('None at all','Nenhuma'), 'no', ('None','Nenhum'),
   ('<code>@Public()</code> plus a broken <code>where</code> — any flow id runs, public or private.',
    '<code>@Public()</code> mais um <code>where</code> quebrado — qualquer id de fluxo executa, público ou privado.')),
  (('Email → public flow','E-mail → fluxo público'), ('Recipient address','Endereço destinatário'), 'no',
   ('No sender check','Sem checagem de remetente'), 'no', ('None','Nenhum'),
   ('Anyone who emails the address runs the flow <em>and controls the prompt</em>.',
    'Qualquer um que envie e-mail ao endereço executa o fluxo <em>e controla o prompt</em>.')),
  (('Email → private flow','E-mail → fluxo privado'), ('<code>From</code> header','Cabeçalho <code>From</code>'), 'weak',
   ('Forgeable','Forjável'), 'no', ('None','Nenhum'),
   ('No DKIM, SPF or DMARC anywhere — the check asks the attacker to type an address that is not secret.',
    'Sem DKIM, SPF ou DMARC em lugar nenhum — a checagem pede que o atacante digite um endereço que não é secreto.')),
  ('/flux/batch-process', ('Session','Sessão'), 'ok',
   ('Authenticated','Autenticado'), 'no', ('None','Nenhum'),
   ('Authenticated, but a single call can admit an unbounded batch.',
    'Autenticada, mas uma única chamada pode admitir um lote sem limite.')),
  ('/flux/execute-from-canvas', ('Session','Sessão'), 'ok',
   ('Authenticated','Autenticado'), 'no', ('None','Nenhum'),
   ('Authenticated, unlimited. The editor path, and the easiest to hammer.',
    'Autenticada, ilimitada. O caminho do editor, e o mais fácil de martelar.')),
]

PARTS = [
{
 'n':'1',
 'title':('The webhook entry point','A entrada de webhook'),
 'tag':('ship first, on its own','entrega primeiro, sozinha'),
 'loc':'flux.controller.ts:340–362',
 'purpose':('Close a route that lets anyone who knows a flow id execute that flow and charge its owner.',
            'Fechar uma rota que permite a qualquer um que saiba um id de fluxo executar esse fluxo e cobrar do dono.'),
 'body':(
  """<p><code>POST /flux/api-v2-webhook</code> is <code>@Public()</code> (<code>flux.controller.ts:340–341</code>), so it opts out of the global auth guard. It then resolves the flow like this:</p>""",
  """<p><code>POST /flux/api-v2-webhook</code> é <code>@Public()</code> (<code>flux.controller.ts:340–341</code>), então sai do guard global de autenticação. Em seguida resolve o fluxo assim:</p>"""),
 'code':("""where: [ { id: query.flowId }, { id: query.flowId, public: true } ]""",
         """where: [ { id: query.flowId }, { id: query.flowId, public: true } ]"""),
 'body2':(
  """<p>The first branch of the OR has <strong>no <code>public</code> condition</strong>, which makes the second one dead: any flow matches, public or private. The rest of the handler contains no secret, no token and no ownership check — only <code>if (!flow)</code>.</p>
<p><strong>Anyone who knows a flow id can execute that flow and charge its owner.</strong> The only barrier is that the id is a UUID — and flow ids travel through published interfaces, chatbot routes, shared links and the MCP surface.</p>""",
  """<p>O primeiro ramo do OR <strong>não tem condição <code>public</code></strong>, o que torna o segundo morto: qualquer fluxo casa, público ou privado. O resto do handler não tem segredo, token nem checagem de propriedade — apenas <code>if (!flow)</code>.</p>
<p><strong>Qualquer um que saiba um id de fluxo pode executar esse fluxo e cobrar do dono.</strong> A única barreira é o id ser um UUID — e ids de fluxo circulam por interfaces publicadas, rotas de chatbot, links compartilhados e pela superfície MCP.</p>"""),
 'ba':(('Anonymous <code>POST</code> with a flow id starts a run on a <strong>private</strong> flow. No secret is checked, no owner is checked, and the bill lands on the flow&#x27;s owner.',
        '<code>POST</code> anônimo com um id de fluxo inicia um run num fluxo <strong>privado</strong>. Nenhum segredo é checado, nenhum dono é checado, e a conta cai no dono do fluxo.'),
       ('A <strong>per-flow webhook secret</strong> is verified before anything else runs, and the <code>public</code> predicate is corrected so the two branches actually mean different things.',
        'Um <strong>segredo de webhook por fluxo</strong> é verificado antes de qualquer coisa rodar, e o predicado <code>public</code> é corrigido para que os dois ramos realmente signifiquem coisas diferentes.')),
 'callouts':[
   ('decide',('Decision to write down','Decisão a registrar'),
    ('<p>What is <code>public: true</code> supposed to permit here? If public flows are meant to be webhook-triggerable by anyone, <strong>say so explicitly</strong> and cap them under Part 2 — do not leave it as an artefact of a broken <code>where</code>.</p>',
     '<p>O que <code>public: true</code> deveria permitir aqui? Se fluxos públicos devem ser disparáveis por webhook por qualquer um, <strong>diga isso explicitamente</strong> e limite-os pela Parte 2 — não deixe como artefato de um <code>where</code> quebrado.</p>')),
   ('mig',('Migration matters more than the fix','A migração importa mais que a correção'),
    ('<p>Existing integrations call this URL today. Ship the secret as <strong>optional</strong>, with a deprecation window and a metric counting unauthenticated calls per flow, then enforce.</p><p>Turning it on cold breaks every customer webhook silently, and the failure looks like <em>“my automation stopped”</em> rather than <em>“my webhook is unauthenticated”</em>.</p>',
     '<p>Integrações existentes chamam essa URL hoje. Entregue o segredo como <strong>opcional</strong>, com uma janela de depreciação e uma métrica contando chamadas não autenticadas por fluxo, e só então imponha.</p><p>Ligar de uma vez quebra o webhook de todo cliente silenciosamente, e a falha parece <em>“minha automação parou”</em> em vez de <em>“meu webhook não está autenticado”</em>.</p>')),
 ],
},
{
 'n':'2',
 'title':('Rate limiting, on every entry point','Rate limiting, em todas as entradas'),
 'tag':('all four routes','as quatro rotas'),
 'loc':'flux.controller.ts:158–160, 221–222, 513–514',
 'purpose':('Cap admission by the thing that pays, so a flood is refused at the door instead of being written to the database first.',
            'Limitar a admissão pelo que paga, para que uma enxurrada seja recusada na porta em vez de ser gravada no banco primeiro.'),
 'body':(
  """<p>There is no <code>ThrottlerModule</code>, no <code>@Throttle</code> and no <code>ThrottlerGuard</code> anywhere in <code>back/src</code>. Every run-creating route accepts unlimited requests: <code>/flux/api-v2</code> (API key), <code>/flux/api-v2-webhook</code> (public), <code>/flux/batch-process</code> and <code>/flux/execute-from-canvas</code>.</p>
<p>The Bull processor&#x27;s single concurrency throttles <strong>execution</strong>, not <strong>admission</strong> — the queue still grows, and rows, logs and dedup keys are written on the way in.</p>""",
  """<p>Não existe <code>ThrottlerModule</code>, nem <code>@Throttle</code>, nem <code>ThrottlerGuard</code> em lugar nenhum de <code>back/src</code>. Toda rota que cria run aceita requisições ilimitadas: <code>/flux/api-v2</code> (chave de API), <code>/flux/api-v2-webhook</code> (pública), <code>/flux/batch-process</code> e <code>/flux/execute-from-canvas</code>.</p>
<p>A concorrência 1 do processador Bull limita a <strong>execução</strong>, não a <strong>admissão</strong> — a fila continua crescendo, e linhas, logs e chaves de dedup são gravados na entrada.</p>"""),
 'code':None,
 'body2':(
  """<p><strong>Scope.</strong> Limits keyed by the thing that pays: <strong>API key</strong>, <strong>organisation</strong>, and <strong>flow</strong> for the webhook route. Not by IP, which is meaningless for server-to-server callers.</p>""",
  """<p><strong>Escopo.</strong> Limites com chave no que paga: <strong>chave de API</strong>, <strong>organização</strong>, e <strong>fluxo</strong> para a rota de webhook. Não por IP, que não significa nada para chamadores servidor-a-servidor.</p>"""),
 'ba':(('Unlimited requests are accepted and persisted. Refusing later, in the queue, still costs a row, a log line and a dedup key per call.',
        'Requisições ilimitadas são aceitas e persistidas. Recusar depois, na fila, ainda custa uma linha, uma linha de log e uma chave de dedup por chamada.'),
       ('Excess calls get <code>429</code> with <code>Retry-After</code> <strong>before</strong> anything is written. Queue depth and row count stop growing.',
        'Chamadas em excesso recebem <code>429</code> com <code>Retry-After</code> <strong>antes</strong> de qualquer gravação. Profundidade de fila e contagem de linhas param de crescer.')),
 'callouts':[
   ('decide',('Assumption to confirm — reject, do not queue','Premissa a confirmar — recusar, não enfileirar'),
    ('<p>Admission is the one place where rejecting is right: queueing an unbounded inbound flood just moves it.</p><p>Note the <strong>deliberate contrast with <code>S3</code></strong>, where excess <em>tenant</em> runs are queued — there the caller is already entitled to the work.</p>',
     '<p>A admissão é o único lugar onde recusar é o certo: enfileirar uma enxurrada de entrada sem limite apenas a desloca.</p><p>Note o <strong>contraste deliberado com a <code>S3</code></strong>, onde runs excedentes de um <em>tenant</em> são enfileirados — lá o chamador já tem direito ao trabalho.</p>')),
 ],
},
{
 'n':'3',
 'title':('The email trigger','O disparo por e-mail'),
 'tag':('ship with Part 1','entrega com a Parte 1'),
 'loc':'mail.service.ts:434, 453–487, 503–556',
 'purpose':('Stop trusting a header anyone can type, and decide what a public flow&#x27;s email address is actually allowed to do.',
            'Parar de confiar num cabeçalho que qualquer um digita, e decidir o que o endereço de e-mail de um fluxo público pode de fato fazer.'),
 'body':(
  """<p>Agents are also started by email. <code>mail.service.ts</code> resolves the flow from the <strong>local part of the recipient address</strong> — the format the service itself advertises is <code>uuid@upload.fluxprompt.com</code> (<code>:434</code>) — then feeds <code>From</code>, <code>Subject</code>, the body and any attachments into the flow&#x27;s <code>varInputNode</code> and enqueues a run (<code>:503–556</code>).</p>
<p>Its authorisation is the weakest of the four entry points (<code>:453–487</code>):</p>""",
  """<p>Agentes também são iniciados por e-mail. O <code>mail.service.ts</code> resolve o fluxo a partir da <strong>parte local do endereço destinatário</strong> — o formato que o próprio serviço anuncia é <code>uuid@upload.fluxprompt.com</code> (<code>:434</code>) — e então injeta <code>From</code>, <code>Subject</code>, o corpo e quaisquer anexos no <code>varInputNode</code> do fluxo e enfileira um run (<code>:503–556</code>).</p>
<p>Sua autorização é a mais fraca das quatro entradas (<code>:453–487</code>):</p>"""),
 'code':None,
 'list':[
   ('<strong>Public flow → no sender check at all.</strong> Anyone who emails the address runs the flow, charged to the owner, <strong>and controls the prompt</strong> — which, in a flow containing a push node or an integration, means driving side effects with the owner&#x27;s credentials.',
    '<strong>Fluxo público → nenhuma checagem de remetente.</strong> Qualquer um que envie e-mail ao endereço executa o fluxo, cobrado do dono, <strong>e controla o prompt</strong> — o que, num fluxo com um push node ou uma integração, significa dirigir efeitos colaterais com as credenciais do dono.'),
   ('<strong>Private flow → the sender&#x27;s <code>From</code> header</strong> is matched against a user and compared to <code>flow.user</code>. Greps for <code>dkim</code>, <code>spf</code>, <code>dmarc</code> and <code>authentication-results</code> in <code>app-api/mail/</code> return nothing, so nothing verifies the message came from the address it claims. The check is a request for the attacker to type the owner&#x27;s email address — which is not secret.',
    '<strong>Fluxo privado → o cabeçalho <code>From</code> do remetente</strong> é casado com um usuário e comparado a <code>flow.user</code>. Buscas por <code>dkim</code>, <code>spf</code>, <code>dmarc</code> e <code>authentication-results</code> em <code>app-api/mail/</code> não retornam nada, então nada verifica que a mensagem veio do endereço que ela alega. A checagem é um pedido para que o atacante digite o e-mail do dono — que não é secreto.'),
 ],
 'body2':(
  """<p><strong>Scope.</strong> Verify the sender — DKIM/SPF/DMARC at the boundary, <strong>or</strong> move the secret into the address (<code>&lt;flowId&gt;+&lt;token&gt;@…</code>) so possession of the address <em>is</em> the credential. Either is defensible; trusting <code>From</code> is not.</p>
<p>Decide, and write down, what a <strong>public</strong> flow&#x27;s email trigger is allowed to do. “Public” should probably mean <em>readable</em>, not <em>“anyone may spend the owner&#x27;s tokens and drive their integrations”</em>. If public email triggers stay, cap them explicitly under Part 2 and treat their input as untrusted for any node with side effects.</p>
<p>Keep the existing bounce-back replies — telling a sender “flow not found” or “unauthorized” is good behaviour, and it is already there.</p>""",
  """<p><strong>Escopo.</strong> Verificar o remetente — DKIM/SPF/DMARC na fronteira, <strong>ou</strong> mover o segredo para dentro do endereço (<code>&lt;flowId&gt;+&lt;token&gt;@…</code>) de modo que a posse do endereço <em>seja</em> a credencial. Qualquer um dos dois se defende; confiar no <code>From</code> não.</p>
<p>Decidir, e registrar, o que o disparo por e-mail de um fluxo <strong>público</strong> pode fazer. “Público” provavelmente deveria significar <em>legível</em>, não <em>“qualquer um pode gastar os tokens do dono e dirigir suas integrações”</em>. Se os disparos públicos por e-mail permanecerem, limite-os explicitamente pela Parte 2 e trate a entrada deles como não confiável para qualquer node com efeito colateral.</p>
<p>Manter as respostas de retorno existentes — dizer ao remetente “fluxo não encontrado” ou “não autorizado” é bom comportamento, e já está lá.</p>"""),
 'ba':(('A message with the owner&#x27;s address typed into <code>From</code> passes the private-flow check. A public flow does not even check that much.',
        'Uma mensagem com o endereço do dono digitado no <code>From</code> passa na checagem de fluxo privado. Um fluxo público não checa nem isso.'),
       ('Possession of a per-flow address token — or a verified DKIM/SPF/DMARC result — is what admits the message. A typed <code>From</code> admits nothing.',
        'A posse de um token de endereço por fluxo — ou um resultado DKIM/SPF/DMARC verificado — é o que admite a mensagem. Um <code>From</code> digitado não admite nada.')),
 'callouts':[
   ('decide',('Assumption to confirm — address token over DKIM','Premissa a confirmar — token no endereço em vez de DKIM'),
    ('<p>The address-token option is preferred: it is <strong>enforceable in this codebase today</strong>, does not depend on the mail provider&#x27;s headers, and rotates per flow.</p><p>DKIM verification is the more standard answer and can be added later <strong>without undoing it</strong>.</p>',
     '<p>A opção do token no endereço é a preferida: é <strong>aplicável neste código hoje</strong>, não depende dos cabeçalhos do provedor de e-mail, e rotaciona por fluxo.</p><p>A verificação DKIM é a resposta mais padrão e pode ser adicionada depois <strong>sem desfazer isso</strong>.</p>')),
 ],
},
]

VERIF = [
 (True, ('Negative control — Part 3','Controle negativo — Parte 3'),
  ('Send a message to a private flow&#x27;s address with the owner&#x27;s email <strong>forged in <code>From</code></strong>, and confirm the flow runs and is charged. Then confirm it is refused. Do the same for a public flow with body content that would drive an integration — <strong>that demonstration is what settles the “what may a public trigger do” decision</strong>.',
   'Envie uma mensagem para o endereço de um fluxo privado com o e-mail do dono <strong>forjado no <code>From</code></strong>, e confirme que o fluxo roda e é cobrado. Depois confirme que é recusado. Faça o mesmo com um fluxo público, com conteúdo no corpo que dirigiria uma integração — <strong>essa demonstração é o que resolve a decisão “o que um disparo público pode fazer”</strong>.')),
 (True, ('Negative control — Part 1','Controle negativo — Parte 1'),
  ('From an unauthenticated client, trigger a <strong>private</strong> flow by id and confirm it runs and charges the owner. That demonstration is <strong>the justification for the whole task</strong>. Then confirm it is refused, and that a correctly-signed call still works.',
   'De um cliente não autenticado, dispare um fluxo <strong>privado</strong> por id e confirme que ele roda e cobra do dono. Essa demonstração é <strong>a justificativa da task inteira</strong>. Depois confirme que é recusado, e que uma chamada corretamente assinada continua funcionando.')),
 (False, ('Negative control — Part 2','Controle negativo — Parte 2'),
  ('Exceed the limit and confirm a <code>429</code>; then confirm the <strong>queue depth and the row count stop growing</strong> — the point is admission, so measuring the refusal is not enough.',
   'Ultrapasse o limite e confirme um <code>429</code>; depois confirme que a <strong>profundidade da fila e a contagem de linhas param de crescer</strong> — o ponto é a admissão, então medir a recusa não basta.')),
 (False, ('Measure before refusing','Medir antes de recusar'),
  ('<strong>PLAN §3.3.2.</strong> Both halves refuse traffic, and this is customer traffic. Count real calls per flow and per key over a full cycle, set the limits <strong>above the observed peak with margin</strong>, and run in <strong>report-only</strong> mode before enforcing. Any legitimate caller refused is a production incident, not a test failure.',
   '<strong>PLAN §3.3.2.</strong> As duas metades recusam tráfego, e esse tráfego é de cliente. Conte as chamadas reais por fluxo e por chave ao longo de um ciclo completo, defina os limites <strong>acima do pico observado, com margem</strong>, e rode em modo <strong>somente-relatório</strong> antes de impor. Qualquer chamador legítimo recusado é um incidente de produção, não uma falha de teste.')),
 (False, ('The deprecation metric names names','A métrica de depreciação diz quem é'),
  ('Confirm the metric actually <strong>names the flows still calling unauthenticated</strong>, so someone can contact their owners before the switch is thrown.',
   'Confirme que a métrica de fato <strong>nomeia os fluxos que ainda chamam sem autenticação</strong>, para que alguém possa contatar os donos antes de a chave ser virada.')),
]

T['done'] = (
 'The webhook route <strong>authenticates</strong>, the <code>public</code> predicate <strong>means what it says</strong>, every run-creating route is <strong>limited by the paying entity</strong>, both halves ran in <strong>report-only mode against real traffic</strong> first — and <strong>no legitimate caller is refused</strong>.',
 'A rota de webhook <strong>autentica</strong>, o predicado <code>public</code> <strong>significa o que diz</strong>, toda rota que cria run é <strong>limitada pela entidade que paga</strong>, as duas metades rodaram antes em <strong>modo somente-relatório contra tráfego real</strong> — e <strong>nenhum chamador legítimo é recusado</strong>.')

FILES = [
 ('back/src/app-api/flux/flux.controller.ts:158–160, 221–222, 340–362, 513–514', False),
 ('back/src/app-api/mail/mail.service.ts:132, 314, 434, 453–487, 503–556', False),
 ('back/src/app-auth/guards/', False),
 ('new throttler configuration', True),
 ('env-vars-sync', True),
]


# -*- coding: utf-8 -*-
TITLE = ('Close the SSRF gaps the S6 check found', 'Fechar as brechas de SSRF que a verificação da S6 achou')

GOAL = ('No FluxPrompt endpoint or node reaches an internal address through a URL a user supplies, <b>whatever that URL&#x27;s name resolves to</b>.',
        'Nenhum endpoint ou node da FluxPrompt alcança um endereço interno por uma URL que o usuário fornece, <b>qualquer que seja o endereço para o qual o nome dessa URL resolve</b>.')

GLANCE = [
 ('crit', ('Most exposed','Mais exposto'), ('<code>/proxy</code>, no account needed','<code>/proxy</code>, sem conta'),
  ('The back&#x27;s <code>/proxy</code> route forwards to any URL and runs before every guard, so it ships first.',
   'A rota <code>/proxy</code> do back encaminha para qualquer URL e roda antes de toda guarda, então ela sai primeiro.')),
 ('dep', ('Depends on','Depende de'), ('Nothing','Nada'),
  ('It reuses the A9 <code>egress</code> module, which is already in production.',
   'Reaproveita o módulo <code>egress</code> da A9, que já está em produção.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('First in the wave, starting with <code>/proxy</code>. It can ship at any point; nothing waits on it.',
   'Primeira da onda, começando pelo <code>/proxy</code>. Pode sair a qualquer momento; nada espera por ela.')),
 ('ship', ('Shape','Formato'), ('Back and worker, one guard','Back e worker, uma guarda'),
  ('Added on 2026-10-26 from the code check of decision S6-a.',
   'Adicionada em 2026-10-26 a partir da verificação de código da decisão S6-a.')),
]

LEDE = (
 '<p><code>S6</code> shipped an egress policy and <code>A9</code> shipped a second, stricter one. The check of decision S6-a, repeated on 2026-10-26 '
 'against back <code>main</code> <code>10e64b20</code> and worker <code>main</code> <code>abf3b09d</code>, found <strong>four places where a user-supplied URL '
 'still leaves the platform unchecked</strong>, or checked in a way that does not hold.</p>'
 '<p>The most exposed is the back&#x27;s <code>/proxy</code> route: an Express middleware registered before any Nest guard, which forwards to the origin '
 'in its <code>url</code> parameter. The front uses it to load images, so the fix authenticates and allowlists it rather than deleting it.</p>',
 '<p>A <code>S6</code> entregou uma política de egresso e a <code>A9</code> entregou uma segunda, mais rígida. A verificação da decisão S6-a, refeita em 26/10/2026 '
 'contra o back <code>main</code> <code>10e64b20</code> e o worker <code>main</code> <code>abf3b09d</code>, achou <strong>quatro lugares onde uma URL fornecida pelo usuário '
 'ainda sai da plataforma sem checagem</strong>, ou com uma checagem que não se sustenta.</p>'
 '<p>O mais exposto é a rota <code>/proxy</code> do back: um middleware do Express registrado antes de qualquer guarda do Nest, que encaminha para a origem '
 'do parâmetro <code>url</code>. O front a usa para carregar imagens, então a correção autentica a rota e restringe os hosts, em vez de apagá-la.</p>')

TABLE = dict(
 head=[('Where','Onde'),('What happens today','O que acontece hoje'),('After S6b','Depois da S6b')],
 rows=[
  [('Back <code>/proxy</code>','<code>/proxy</code> do back'),
   {'t':('Any URL, no account, no address check','Qualquer URL, sem conta, sem checar endereço'),'pill':'weak'},
   {'t':('Authenticated, our asset hosts only','Autenticada, só os nossos hosts de assets'),'pill':'ok'}],
  [('Worker <code>safe-fetch</code>','<code>safe-fetch</code> do worker'),
   {'t':('Passes if one address is allowed; connects by name again','Passa se um endereço for permitido; conecta pelo nome de novo'),'pill':'weak'},
   {'t':('Every address checked, the checked one pinned','Todo endereço checado, o checado é o usado'),'pill':'ok'}],
  [('Deny-lists','Listas de bloqueio'),
   {'t':('Two: 10 ranges and 17 ranges','Duas: 10 faixas e 17 faixas'),'pill':'weak'},
   {'t':('One: the 17 ranges of <code>egress</code>','Uma: as 17 faixas do <code>egress</code>'),'pill':'ok'}],
  [('Back <code>POST /api_call</code>','<code>POST /api_call</code> do back'),
   {'t':('Plain axios, no egress check','Axios puro, sem checagem de egresso'),'pill':'weak'},
   {'t':('The same guard as the worker','A mesma guarda do worker'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('Close <code>/proxy</code>','Fechar o <code>/proxy</code>'),
 'loc':'back/src/main.ts',
 'purpose':('Require authentication and forward only to an allowlist of our own asset hosts.',
            'Exigir autenticação e encaminhar só para uma lista de hosts de assets nossos.'),
 'body':('<p>The allowlist comes from configuration (CloudFront and the S3 buckets the image nodes write to), never from the request. '
         'Before it ships, count from the access logs which hosts <code>/proxy</code> serves today, so a real image host is not refused.</p>',
         '<p>A lista vem da configuração (CloudFront e os buckets S3 onde os nodes de imagem gravam), nunca da requisição. '
         'Antes de sair, contar nos logs de acesso quais hosts o <code>/proxy</code> serve hoje, para não recusar um host de imagem real.</p>'),
 'ba':(('Any caller, any URL, before every guard.','Qualquer um, qualquer URL, antes de toda guarda.'),
       ('A token is required, and only our asset hosts are forwarded.','É preciso token, e só os nossos hosts de assets são encaminhados.')),
 'callouts':[('mig',('Keep working','Precisa continuar funcionando'),
   ('<p><code>ExpandImageModal.tsx</code> and <code>MaskImageEditModal.tsx</code> load images through this route.</p>',
    '<p>O <code>ExpandImageModal.tsx</code> e o <code>MaskImageEditModal.tsx</code> carregam imagens por esta rota.</p>'))]},

{'n':'2','title':('One guard that pins the address','Uma guarda que fixa o endereço'),
 'loc':'worker/src/modules/safe-fetch/',
 'purpose':('Make <code>safe-fetch</code> use the A9 <code>egress</code> module, and keep one deny-list.',
            'Fazer o <code>safe-fetch</code> usar o módulo <code>egress</code> da A9, e manter uma lista de bloqueio.'),
 'body':('<p>Today <code>safe-dispatcher.ts</code> connects by hostname after the check, so the name resolves twice. The <code>egress</code> module '
         'already checks every address, pins the checked one through a <code>lookup</code> hook and checks each redirect hop again.</p>',
         '<p>Hoje o <code>safe-dispatcher.ts</code> conecta pelo nome depois da checagem, então o nome resolve duas vezes. O módulo <code>egress</code> '
         'já checa todo endereço, fixa o checado por um hook de <code>lookup</code> e checa de novo cada salto de redirect.</p>')},

{'n':'3','title':('Guard the back and sweep the rest','Proteger o back e varrer o resto'),
 'loc':'back/src/app-api/api_call/',
 'purpose':('Put <code>POST /api_call</code> behind the same check, and record every other outbound fetch of a user URL.',
            'Colocar o <code>POST /api_call</code> atrás da mesma checagem, e registrar todo outro fetch de saída de URL do usuário.'),
 'body':('<p><code>DownloaderService.downloadFile</code> has no caller: delete it, or guard it if one turns up. Check first whether the plain '
         '<code>fetch(url)</code> calls in the audio transcriber, the Document AI reader and Push Data can receive a user URL.</p>',
         '<p>O <code>DownloaderService.downloadFile</code> não tem chamador: apagar, ou proteger se aparecer um. Checar primeiro se as chamadas '
         '<code>fetch(url)</code> puras do transcritor de áudio, do leitor Document AI e do Push Data podem receber URL do usuário.</p>')},
]

VERIF = [
 (True, ('Negative control — pinning','Controle negativo — fixação do endereço'),
  ('A test host that resolves to one public and one denied address passes <code>safe-fetch</code> on <code>main</code> today. After the change it is refused. Remove the pinning and watch the test fail.',
   'Um host de teste que resolve para um endereço público e um bloqueado passa no <code>safe-fetch</code> do <code>main</code> hoje. Depois da mudança ele é recusado. Tire a fixação e veja o teste falhar.')),
 (True, ('<code>/proxy</code> answers by case','<code>/proxy</code> responde por caso'),
  ('No token: 401. A token and a host outside the allowlist: 403. An asset host: the image.',
   'Sem token: 401. Com token e host fora da lista: 403. Host de assets: a imagem.')),
 (False, ('Local only','Só local'),
  ('Every test runs locally. Never probe a production endpoint to prove a gap.',
   'Todo teste roda local. Nunca sondar um endpoint de produção para provar uma brecha.')),
]

DONE = ('<code>/proxy</code> is authenticated and allowlisted, every outbound fetch of a user URL goes through one guard that pins the checked address, '
        'one deny-list remains, and the sweep is recorded.',
        'O <code>/proxy</code> está autenticado e com lista de hosts, todo fetch de saída de URL do usuário passa por uma guarda que fixa o endereço checado, '
        'sobra uma lista de bloqueio, e a varredura está registrada.')

FILES = [('back/src/main.ts (/proxy)', False),
         ('back/src/app-api/api_call/api_call.service.ts', False),
         ('back/src/app-api/downloader/downloader.service.ts', False),
         ('worker/src/modules/safe-fetch/safe-dispatcher.ts', False),
         ('worker/src/modules/safe-fetch/egress-policy.service.ts', False),
         ('worker/src/modules/egress/egress-policy.ts', False),
         ('front/src/components/ExpandImageModal/ExpandImageModal.tsx', False),
         ('front/src/components/MaskImageEditModal/MaskImageEditModal.tsx', False)]

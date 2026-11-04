# -*- coding: utf-8 -*-
TITLE = ('Refuse a third-party credential the executing user cannot reach',
         'Recusar uma credencial de terceiro que o usuário da execução não alcança')

GOAL = ('A run, or a configuration call, uses a saved third-party connection <b>only when the user it runs for can reach it</b> under the product&#x27;s own rule, and only for the provider the node names.',
        'Um run, ou uma chamada de configuração, usa uma conexão de terceiro salva <b>só quando o usuário para quem ele roda consegue alcançá-la</b> pela regra do próprio produto, e só para o provider que o node indica.')

GLANCE = [
 ('crit', ('Risk closed','Risco fechado'), ('Access that outlives its grant','Acesso que sobrevive à permissão'),
  ('An id someone saw while it was shared kept working after they left the company or the owner stopped sharing it.',
   'Um id que alguém viu enquanto estava compartilhado continuava funcionando depois que a pessoa saía da empresa ou o dono parava de compartilhar.')),
 ('dep', ('Depends on','Depende de'), ('A11','A11'),
  ('After A11, the worker is the only run path that resolves a credential, so the run-time check lives in one place.',
   'Depois da A11, o worker é o único caminho de run que resolve uma credencial, então a checagem em tempo de run fica num lugar só.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Any time after A11. It blocks nothing.','A qualquer momento depois da A11. Não bloqueia nada.')),
 ('ship', ('Shape','Formato'), ('Back and worker','Back e worker'),
  ('Added on 2026-10-29 from a finding P7 recorded and left open. Measured: 0 would-be-refused nodes in production.',
   'Adicionada em 29/10/2026 a partir de um achado que a P7 registrou e deixou aberto. Medido: 0 nodes de produção que seriam recusados.')),
]

LEDE = (
 '<p>P7 closed the MCP write side: <code>add_node</code> and <code>update_node</code> refuse an <code>integrationId</code> the token&#x27;s user cannot reach. '
 'The run side stayed open. The worker&#x27;s resolver and the back&#x27;s configuration routes read the saved connection by id, '
 '<strong>logged when the user could not reach it, and used it anyway</strong>, including refreshing and storing another user&#x27;s OAuth token.</p>'
 '<p>The ids are random UUIDs, so this was not mass exposure. The concrete risk was access that outlives its grant. '
 'S9 calls the reachability rule that already exists in each repo, refuses before any side effect, and gives one message for every refused case.</p>',
 '<p>A P7 fechou o lado de escrita do MCP: o <code>add_node</code> e o <code>update_node</code> recusam um <code>integrationId</code> que o usuário do token não alcança. '
 'O lado do run ficou aberto. O resolver do worker e as rotas de configuração do back liam a conexão salva pelo id, '
 '<strong>logavam quando o usuário não a alcançava, e usavam assim mesmo</strong>, inclusive renovando e gravando o token OAuth de outro usuário.</p>'
 '<p>Os ids são UUIDs aleatórios, então não era uma exposição em massa. O risco concreto era um acesso que sobrevive à permissão. '
 'A S9 chama a regra de alcance que já existe em cada repo, recusa antes de qualquer efeito colateral, e dá uma mensagem só para todo caso recusado.</p>')

TABLE = dict(
 head=[('Path','Caminho'),('Before S9','Antes da S9'),('After S9','Depois da S9')],
 rows=[
  [('Worker resolver','Resolver do worker'),
   {'t':('Logs and uses the credential','Loga e usa a credencial'),'pill':'weak'},
   {'t':('Refuses before any side effect','Recusa antes de qualquer efeito colateral'),'pill':'ok'}],
  [('An id that is not a UUID','Um id que não é UUID'),
   {'t':('Raw database error','Erro cru do banco'),'pill':'weak'},
   {'t':('The same user-facing refusal','A mesma recusa para o usuário'),'pill':'ok'}],
  [('Back configuration routes and refresh-token','Rotas de configuração do back e refresh-token'),
   {'t':('Use or refresh another user&#x27;s row','Usam ou renovam a linha de outro usuário'),'pill':'weak'},
   {'t':('Refused with the same message','Recusadas com a mesma mensagem'),'pill':'ok'}],
  [('MCP credentials route','Rota de credenciais do MCP'),
   {'t':('A third, looser rule','Uma terceira regra, mais frouxa'),'pill':'weak'},
   {'t':('The back&#x27;s one rule','A regra única do back'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('Check in the worker resolver','Checar no resolver do worker'),
 'loc':'worker/src/modules/nodes/third-party-integration/user-integration.repo.ts',
 'purpose':('Refuse a malformed id, a row of another provider and a row the user cannot reach, before any side effect.',
            'Recusar um id malformado, uma linha de outro provider e uma linha que o usuário não alcança, antes de qualquer efeito colateral.'),
 'body':('<p>It calls <code>isIntegrationReachableByUser</code>, never a third copy of the rule. A missing row keeps today&#x27;s fallback to the user&#x27;s own connection; '
         'a refused row never falls back. The MCP target gets the same message for its two cases.</p>',
         '<p>Chama o <code>isIntegrationReachableByUser</code>, nunca uma terceira cópia da regra. Uma linha que não existe mantém o fallback de hoje para a conexão do próprio usuário; '
         'uma linha recusada nunca cai no fallback. O target de MCP recebe a mesma mensagem nos dois casos.</p>')},

{'n':'2','title':('Check in the back configuration routes','Checar nas rotas de configuração do back'),
 'loc':'back/src/app-api/integrations/integrations.service.ts',
 'purpose':('Apply the same check to pull, push, options, schema, refresh-token and the MCP credentials route.',
            'Aplicar a mesma checagem a pull, push, options, schema, refresh-token e à rota de credenciais do MCP.'),
 'body':('<p>It calls <code>isReachableByUser</code>. <code>getIntegrationById</code>, a third and looser rule, is deleted.</p>',
         '<p>Chama o <code>isReachableByUser</code>. O <code>getIntegrationById</code>, uma terceira regra mais frouxa, é apagado.</p>')},

{'n':'3','title':('Measure before refusing','Medir antes de recusar'),
 'loc':'s9-q1, s9-q2',
 'purpose':('Classify every stored node that names a connection before the refusal ships.',
            'Classificar todo node salvo que aponta para uma conexão antes da recusa sair.'),
 'body':('<p>Measured in production: zero nodes would be refused, and zero log-only lines since 2026-08-11.</p>',
         '<p>Medido em produção: zero nodes seriam recusados, e zero linhas só de log desde 11/08/2026.</p>')},
]

VERIF = [
 (True, ('Negative control — another user&#x27;s connection','Controle negativo — conexão de outro usuário'),
  ('A node with a connection the user cannot reach runs on the old code and is refused after the change, with no token refresh and no provider call. Revert and watch the test fail.',
   'Um node com uma conexão que o usuário não alcança roda no código antigo e é recusado depois da mudança, sem renovar token e sem chamar o provider. Reverter e ver o teste falhar.')),
 (True, ('A failure after the check','Uma falha depois da checagem'),
  ('If the reachability query throws, the run fails with a retryable error and nothing else happens; a retry checks again.',
   'Se a consulta de alcance falhar, o run falha com um erro que pode ser repetido e nada mais acontece; uma nova tentativa checa de novo.')),
]

DONE = ('The worker and the back refuse a saved third-party or MCP credential the executing user cannot reach, of another provider or with a malformed id, with one message, before any side effect, and production showed zero would-be-refused nodes before it shipped.',
        'O worker e o back recusam uma credencial salva de terceiro ou de MCP que o usuário da execução não alcança, de outro provider ou com id malformado, com uma mensagem só, antes de qualquer efeito colateral, e a produção mostrou zero nodes que seriam recusados antes de sair.')

FILES = [('worker/src/modules/nodes/third-party-integration/user-integration.repo.ts', False),
         ('worker/src/modules/nodes/third-party-integration/third-party-integration.service.ts', False),
         ('worker/src/modules/nodes/mcp/mcp-target.ts', False),
         ('back/src/app-api/integrations/integrations.service.ts', False),
         ('back/src/app-api/user_integration/user_integration.service.ts', False)]

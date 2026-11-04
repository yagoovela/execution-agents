# -*- coding: utf-8 -*-
TITLE = ('Keep the MCP OAuth state where every back replica can read it',
         'Guardar o estado do OAuth do MCP onde toda réplica do back consiga ler')

GOAL = ('A user can connect an MCP integration through OAuth <b>whichever back replica serves the callback</b>.',
        'O usuário consegue conectar uma integração MCP por OAuth <b>qualquer que seja a réplica do back que atende o callback</b>.')

GLANCE = [
 ('crit', ('Symptom','Sintoma'), ('&quot;Invalid or expired state&quot;','&quot;Invalid or expired state&quot;'),
  ('With two replicas, a callback on the other replica fails. About half of the connections can fail.',
   'Com duas réplicas, um callback na outra réplica falha. Cerca de metade das conexões pode falhar.')),
 ('dep', ('Depends on','Depende de'), ('Nothing','Nada'),
  ('The back already uses Redis for rate limiting and queues.',
   'O back já usa Redis para rate limit e filas.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('First in the wave, with the other back-replica tasks.',
   'Primeira da onda, junto com as outras tasks de réplica do back.')),
 ('ship', ('Shape','Formato'), ('Back only','Só o back'),
  ('Added on 2026-11-04 from the replica audit of that day.',
   'Adicionada em 04/11/2026 a partir da auditoria de réplicas daquele dia.')),
]

LEDE = (
 '<p>The MCP OAuth flow keeps its PKCE state in a map in the memory of the process that started it. The callback looks the state up in that map, '
 'so a callback that lands on another replica finds nothing. The production load balancer does not keep a browser on one replica: '
 '<strong>stickiness is off</strong> on the back&#x27;s target group.</p>'
 '<p>The fix stores the state in Redis instead. Turning stickiness on is ruled out: it would hide the defect, pin sockets and runs to one replica, '
 'and a scale-in or a deploy would still break a connection in progress.</p>',
 '<p>O fluxo de OAuth do MCP guarda o estado PKCE num mapa na memória do processo que o iniciou. O callback procura o estado nesse mapa, '
 'então um callback que cai em outra réplica não acha nada. O load balancer de produção não mantém um navegador numa réplica: '
 '<strong>o stickiness está desligado</strong> no target group do back.</p>'
 '<p>A correção guarda o estado no Redis. Ligar o stickiness está descartado: esconderia o defeito, prenderia sockets e runs a uma réplica, '
 'e uma redução de escala ou um deploy ainda quebrariam uma conexão em andamento.</p>')

TABLE = dict(
 head=[('State','Estado'),('Today','Hoje'),('After S10','Depois da S10')],
 rows=[
  [('PKCE state','Estado PKCE'),
   {'t':('In-process map','Mapa em memória do processo'),'pill':'weak'},
   {'t':('Redis, single use, same expiry','Redis, uso único, mesma expiração'),'pill':'ok'}],
  [('Discovery and registration','Discovery e registro'),
   {'t':('In-process maps','Mapas em memória do processo'),'pill':'weak'},
   {'t':('Redis, or proven safe to rebuild','Redis, ou provado seguro de refazer'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('Move the PKCE state to Redis','Levar o estado PKCE para o Redis'),
 'loc':'back/src/app-api/mcp_call/mcp_oauth.service.ts',
 'purpose':('Key it by the OAuth <code>state</code>, keep today&#x27;s expiry, and delete it when the callback consumes it.',
            'Usar o <code>state</code> do OAuth como chave, manter a expiração de hoje, e apagar quando o callback consumir.'),
 'body':('<p>A second callback with the same <code>state</code> is refused, and an expired state gets today&#x27;s user-facing message.</p>',
         '<p>Um segundo callback com o mesmo <code>state</code> é recusado, e um estado expirado recebe a mesma mensagem de hoje.</p>'),
 'ba':(('A callback on another replica fails.','Um callback em outra réplica falha.'),
       ('A callback on any replica succeeds, once.','Um callback em qualquer réplica funciona, uma vez.'))},

{'n':'2','title':('Decide the two caches','Decidir os dois caches'),
 'loc':'back/src/app-api/mcp_call/mcp_oauth.service.ts',
 'purpose':('Move <code>discoveryCache</code> and <code>registrationCache</code> to Redis, or show that a miss only costs one more request.',
            'Levar o <code>discoveryCache</code> e o <code>registrationCache</code> para o Redis, ou mostrar que um miss só custa uma requisição a mais.'),
 'body':('<p>Record the choice in the PR.</p>','<p>Registrar a escolha no PR.</p>')},
]

VERIF = [
 (True, ('Negative control — the other replica','Controle negativo — a outra réplica'),
  ('Start the flow on one back process and send the callback to a second one. On <code>main</code> it fails with &quot;Invalid or expired state&quot;; after the change it succeeds. Revert and watch the test fail.',
   'Iniciar o fluxo num processo do back e mandar o callback para um segundo. No <code>main</code> falha com &quot;Invalid or expired state&quot;; depois da mudança funciona. Reverter e ver o teste falhar.')),
 (False, ('Replay and expiry','Repetição e expiração'),
  ('A replayed callback is refused, and an expired state is refused with today&#x27;s message.',
   'Um callback repetido é recusado, e um estado expirado é recusado com a mensagem de hoje.')),
]

DONE = ('An MCP OAuth connection succeeds when the callback lands on a different replica from the one that started it, and the state is single-use and expires as it does today.',
        'Uma conexão OAuth do MCP funciona quando o callback cai numa réplica diferente da que o iniciou, e o estado é de uso único e expira como hoje.')

FILES = [('back/src/app-api/mcp_call/mcp_oauth.service.ts', False),
         ('the back&#x27;s Redis client module', False)]

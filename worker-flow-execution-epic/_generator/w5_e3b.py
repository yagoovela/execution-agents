# -*- coding: utf-8 -*-
TITLE = ('Deliver each worker event once, however many back replicas run',
         'Entregar cada evento do worker uma vez, com quantas réplicas do back houver')

GOAL = ('Every run event the worker publishes reaches the browser <b>exactly once</b>, with one, two or three back replicas.',
        'Todo evento de run que o worker publica chega ao navegador <b>exatamente uma vez</b>, com uma, duas ou três réplicas do back.')

GLANCE = [
 ('crit', ('Visible to users','Visível ao usuário'), ('Streamed text repeats','O texto em streaming repete'),
  ('With two back replicas, the chatbot shows each streamed chunk twice. Production runs two replicas every day.',
   'Com duas réplicas do back, o chatbot mostra cada pedaço do streaming duas vezes. A produção roda duas réplicas todo dia.')),
 ('dep', ('Depends on','Depende de'), ('Nothing','Nada'),
  ('It changes how the back relays events that <code>E3</code> already routes through Redis.',
   'Muda como o back repassa os eventos que a <code>E3</code> já faz passar pelo Redis.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('First in the wave, with the other back-replica tasks. It blocks the back running on more than one task.',
   'Primeira da onda, junto com as outras tasks de réplica do back. Bloqueia o back rodando com mais de uma task.')),
 ('ship', ('Shape','Formato'), ('Back only','Só o back'),
  ('Added on 2026-11-04 from the replica audit of that day.',
   'Adicionada em 04/11/2026 a partir da auditoria de réplicas daquele dia.')),
]

LEDE = (
 '<p><code>E3</code> made Redis the one publish path and installed the Socket.io Redis adapter, so any replica can reach any socket. '
 'It did not make delivery single. The back connects the Nest Redis microservice transport, which is publish/subscribe, so <strong>every replica '
 'receives every event</strong> the worker publishes, and each one re-emits it through the adapter to the sockets of every replica.</p>'
 '<p>Production autoscales the back from one to three tasks on CPU, and it ran two tasks every day from 2026-10-28 to 2026-11-03. '
 'So the browser can receive each status and each stream chunk twice today. <code>E3</code> tested that no event was lost, never that none was repeated.</p>',
 '<p>A <code>E3</code> fez do Redis o único caminho de publicação e instalou o adapter Redis do Socket.io, para que qualquer réplica alcance qualquer socket. '
 'Ela não tornou a entrega única. O back conecta o transporte de microserviço Redis do Nest, que é publish/subscribe, então <strong>toda réplica '
 'recebe todo evento</strong> que o worker publica, e cada uma o reenvia pelo adapter para os sockets de todas as réplicas.</p>'
 '<p>A produção faz autoscaling do back de uma a três tasks pela CPU, e rodou duas tasks todo dia de 28/10/2026 a 03/11/2026. '
 'Então o navegador pode receber cada status e cada pedaço do streaming duas vezes hoje. A <code>E3</code> testou que nenhum evento se perdia, nunca que nenhum se repetia.</p>')

TABLE = dict(
 head=[('Back replicas','Réplicas do back'),('Today','Hoje'),('After E3b','Depois da E3b')],
 rows=[
  [('One','Uma'),
   {'t':('Each event once','Cada evento uma vez'),'pill':'ok'},
   {'t':('Each event once','Cada evento uma vez'),'pill':'ok'}],
  [('Two','Duas'),
   {'t':('Each event twice; chat text doubles','Cada evento duas vezes; o texto do chat dobra'),'pill':'weak'},
   {'t':('Each event once','Cada evento uma vez'),'pill':'ok'}],
  [('Three','Três'),
   {'t':('Each event three times','Cada evento três vezes'),'pill':'weak'},
   {'t':('Each event once','Cada evento uma vez'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('Deliver each event once','Entregar cada evento uma vez'),
 'loc':'back/src/temporal/notifications.gateway.ts',
 'purpose':('Pick one of two designs and record why.','Escolher um de dois desenhos e registrar o porquê.'),
 'body':('<p><b>Emit locally:</b> every replica still receives the event but emits it with <code>server.local</code>, so each one delivers only to the sockets it holds. '
         'This is the smaller change. <b>Consume once:</b> worker events go to a queue or a Redis stream with one consumer group, which keeps the adapter broadcast.</p>',
         '<p><b>Emitir localmente:</b> toda réplica continua recebendo o evento, mas emite com <code>server.local</code>, então cada uma entrega só aos sockets que tem. '
         'É a mudança menor. <b>Consumir uma vez:</b> os eventos do worker vão para uma fila ou um stream do Redis com um consumer group, que mantém o broadcast do adapter.</p>'),
 'ba':(('Every replica re-emits every event to every socket.','Toda réplica reenvia todo evento para todo socket.'),
       ('Each event leaves the back once.','Cada evento sai do back uma vez.'))},

{'n':'2','title':('The chatbot relay and the completion stream','O relay do chatbot e o stream da completion'),
 'loc':'back/src/temporal/notifications.gateway.ts',
 'purpose':('Apply the same rule to the emit by <code>socketId</code>, and confirm the completion API is unaffected.',
            'Aplicar a mesma regra ao emit por <code>socketId</code>, e confirmar que a API de completion não é afetada.'),
 'body':('<p><code>relayStreamChunkToSocket</code> emits by socket id and follows the same rule. The completion API stream is emitted only by the replica '
         'that owns the request; record that it stays as it is.</p>',
         '<p>O <code>relayStreamChunkToSocket</code> emite pelo id do socket e segue a mesma regra. O stream da API de completion só é emitido pela réplica '
         'dona da requisição; registrar que ele fica como está.</p>')},
]

VERIF = [
 (True, ('Negative control — two replicas','Controle negativo — duas réplicas'),
  ('Two back processes on one Redis and one socket client. Publish one stream chunk: on <code>main</code> the client receives it twice; after the change, once. Revert and watch the test fail.',
   'Dois processos do back num Redis e um cliente de socket. Publicar um pedaço do streaming: no <code>main</code> o cliente recebe duas vezes; depois da mudança, uma. Reverter e ver o teste falhar.')),
 (True, ('Order and count','Ordem e contagem'),
  ('Per node, <code>RUNNING</code> never arrives after <code>COMPLETED</code>, and emitted equals received with one, two and three replicas.',
   'Por node, <code>RUNNING</code> nunca chega depois de <code>COMPLETED</code>, e emitidos é igual a recebidos com uma, duas e três réplicas.')),
]

DONE = ('With two and three back replicas, every status and every stream chunk reaches the browser once, and the test that proves it fails with the change reverted.',
        'Com duas e três réplicas do back, todo status e todo pedaço do streaming chega ao navegador uma vez, e o teste que prova isso falha com a mudança revertida.')

FILES = [('back/src/main.ts (connectMicroservice, RedisIoAdapter)', False),
         ('back/src/temporal/temporal.controller.ts', False),
         ('back/src/temporal/notifications.gateway.ts', False),
         ('back/src/adapters/redis-io.adapter.ts', False),
         ('worker/src/modules/notification/notification.service.ts', False),
         ('front/src/components/ChatBot/ChatBot.tsx (read only)', False)]

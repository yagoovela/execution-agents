# -*- coding: utf-8 -*-
TITLE = ('Alert before the prod Redis fills, gets slow or runs out of CPU',
         'Alertar antes de o Redis de prod encher, ficar lento ou ficar sem CPU')

GOAL = ('Someone is told <b>before the prod Redis fills up and refuses writes</b>, when a new writer stores keys without a TTL, and when Redis gets slow or runs out of CPU.',
        'Alguém é avisado <b>antes de o Redis de prod encher e recusar escritas</b>, quando um novo escritor grava chaves sem TTL, e quando o Redis fica lento ou sem CPU.')

GLANCE = [
 ('crit', ('Why now','Por que agora'), ('No Redis alarm existed','Não existia alarme de Redis'),
  ('Under <code>noeviction</code> a full Redis refuses writes. That only improves on silent eviction if someone watches memory, and on 2026-11-17 no Redis alarm or Redis email topic existed.',
   'Sob <code>noeviction</code> um Redis cheio recusa escritas. Isso só melhora a remoção silenciosa se alguém vigia a memória, e em 17/11/2026 não existia nenhum alarme de Redis nem tópico de email de Redis.')),
 ('dep', ('Depends on','Depende de'), ('Nothing','Nada'),
  ('It carries the alarms that <code>E5</code> decided on 2026-10-02 and left open when it closed.',
   'Leva os alarmes que a <code>E5</code> decidiu em 02/10/2026 e deixou abertos ao fechar.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('<code>E5</code> itself stays in Wave 4.','A própria <code>E5</code> continua na Onda 4.')),
 ('ship', ('Shape','Formato'), ('Prod infrastructure only','Só infraestrutura de prod'),
  ('Added on 2026-11-11 when <code>E5</code> closed, cut to four prod alarms on 2026-11-17, applied in prod on 2026-11-18. USD 1.20 a month. No application code.',
   'Adicionada em 11/11/2026 quando a <code>E5</code> fechou, reduzida a quatro alarmes de prod em 17/11/2026, aplicada em prod em 18/11/2026. US$ 1,20 por mês. Nenhum código de aplicação.')),
]

LEDE = (
 '<p>Dev, staging and prod all run a <code>noeviction</code> Redis, so a full Redis <strong>refuses writes instead of silently dropping the dedup keys</strong>. '
 'That is only an improvement if someone is watching memory, and on 2026-11-17 <strong>no Redis alarm existed</strong>.</p>'
 '<p>On 2026-11-17 the scope became four alarms in prod only: nobody acts on a dev or staging Redis alert, and an <code>Evictions</code> alarm can never fire under <code>noeviction</code>. '
 'The four alarms were created in prod on 2026-11-18 at 17:21 UTC and all read <code>OK</code>. Two steps are still open: the email subscription waits for its confirmation, so no alert is delivered yet, and no alarm has been fired on purpose.</p>',
 '<p>Dev, staging e prod rodam um Redis <code>noeviction</code>, então um Redis cheio <strong>recusa escritas em vez de descartar em silêncio as chaves de dedup</strong>. '
 'Isso só melhora se alguém vigia a memória, e em 17/11/2026 <strong>não existia nenhum alarme de Redis</strong>.</p>'
 '<p>Em 17/11/2026 o escopo virou quatro alarmes só em prod: ninguém age sobre um alerta do Redis de dev ou staging, e um alarme de <code>Evictions</code> nunca dispara sob <code>noeviction</code>. '
 'Os quatro alarmes foram criados em prod em 18/11/2026 às 17:21 UTC e todos leem <code>OK</code>. Dois passos seguem abertos: a assinatura de email espera a confirmação, então nenhum alerta é entregue ainda, e nenhum alarme foi disparado de propósito.</p>')

TABLE = dict(
 head=[('Alarm','Alarme'),('Metric','Métrica'),('Rule','Regra')],
 rows=[
  [('Memory usage','Uso de memória'),
   ('<code>DatabaseMemoryUsagePercentage</code>, maximum, on the primary','<code>DatabaseMemoryUsagePercentage</code>, máximo, no primário'),
   {'t':('Above 50% for two periods of 300 s','Acima de 50% por dois períodos de 300 s'),'pill':'ok'}],
  [('Keys without a TTL','Chaves sem TTL'),
   ('Metric math: items minus volatile items, on the primary','Metric math: itens menos itens voláteis, no primário'),
   {'t':('Above 600 for three periods','Acima de 600 por três períodos'),'pill':'ok'}],
  [('Latency','Latência'),
   ('Metric math: highest read or write <code>p99</code> over the three nodes','Metric math: maior <code>p99</code> de leitura ou escrita entre os três nós'),
   {'t':('Above 10 ms for three periods of 300 s','Acima de 10 ms por três períodos de 300 s'),'pill':'ok'}],
  [('Engine CPU','CPU do engine'),
   ('Metric math: highest <code>EngineCPUUtilization</code> over the three nodes','Metric math: maior <code>EngineCPUUtilization</code> entre os três nós'),
   {'t':('Above 80% for three periods of 300 s','Acima de 80% por três períodos de 300 s'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('Four alarms, prod only','Quatro alarmes, só em prod'),
 'loc':'CloudWatch alarms',
 'purpose':('Create the memory, keys-gap, latency and engine CPU alarms on the prod Redis, each with a recovery notification.',
            'Criar os alarmes de memória, diferença de chaves, latência e CPU do engine no Redis de prod, cada um com notificação de recuperação.'),
 'body':('<p>Decided on 2026-11-17. There is no alarm in dev or staging, because nobody acts on those alerts and both run far from every threshold. '
         'There is no <code>Evictions</code> alarm: under <code>noeviction</code> a full Redis refuses writes, which the memory alarm reports first, and CloudWatch bills an alarm for as long as it exists, even with its actions disabled.</p>'
         '<p>The latency and engine CPU alarms take the highest value over the three nodes, so they keep working when another node becomes primary. '
         'The memory and keys-gap alarms read the primary, which is safe while automatic failover stays disabled.</p>',
         '<p>Decidido em 17/11/2026. Não há alarme em dev nem em staging, porque ninguém age sobre esses alertas e os dois rodam longe de todo limite. '
         'Não há alarme de <code>Evictions</code>: sob <code>noeviction</code> um Redis cheio recusa escritas, o que o alarme de memória avisa primeiro, e o CloudWatch cobra um alarme enquanto ele existe, mesmo com as ações desligadas.</p>'
         '<p>Os alarmes de latência e de CPU do engine pegam o maior valor entre os três nós, então continuam funcionando quando outro nó vira primário. '
         'Os alarmes de memória e de diferença de chaves leem o primário, o que é seguro enquanto o failover automático continua desligado.</p>'),
 'ba':(('No Redis alarm exists.','Não existe alarme de Redis.'),
       ('Four prod alarms, each with a recovery notice, for USD 1.20 a month.','Quatro alarmes em prod, cada um com aviso de recuperação, por US$ 1,20 por mês.'))},

{'n':'2','title':('A separate email topic','Um tópico de email separado'),
 'loc':'SNS topic <code>Enhancedai-Redis-Alerts-PROD</code>',
 'purpose':('Each alarm and recovery notifies a new topic, so Redis alerts do not reach the external subscribers of the existing topics.',
            'Cada alarme e recuperação notifica um tópico novo, para que os alertas de Redis não cheguem aos inscritos externos dos tópicos existentes.'),
 'body':('<p>The recipient is the team list, decided on 2026-11-18. Out of scope: re-measuring the pub/sub rate after <code>B5</code>, and the automatic failover and multi-zone decision, which stays separate as in <code>E5</code>.</p>',
         '<p>O destinatário é a lista do time, decidida em 18/11/2026. Fora de escopo: medir de novo a taxa de pub/sub depois da <code>B5</code>, e a decisão de failover automático e multi-zona, que continua separada como na <code>E5</code>.</p>')},

{'n':'3','title':('Latency and the golden signals','Latência e os sinais de ouro'),
 'loc':'CloudWatch alarms',
 'purpose':('Cover Redis latency and CPU, and record which alarm covers each golden signal.',
            'Cobrir a latência e a CPU do Redis, e registrar qual alarme cobre cada sinal de ouro.'),
 'body':('<p>Added on 2026-11-13, after the <code>S4b</code> production check found <code>Redis command timed out</code> in the back every day. Measured over 14 days: Redis itself is fast, with production <code>p99</code> at most 2 ms and engine CPU at most 4%. The timeouts come from the back: its 250 ms timer fires late when its event loop is blocked, in one burst a day between 14:05 and 14:20 UTC, weekends included. So the two alarms stay quiet today and fire only when Redis itself degrades.</p>'
         '<ul><li><b>Latency:</b> the latency alarm, on the server side.</li>'
         '<li><b>Errors:</b> no alarm yet. The only Redis error seen is the back timeout, and an alarm on it would fire every day until the burst is fixed in the back.</li>'
         '<li><b>Saturation:</b> memory, engine CPU and keys without a TTL. Connections stayed under 100 in prod, far from any limit.</li>'
         '<li><b>Traffic:</b> no alarm, because no threshold separates good from bad traffic.</li></ul>',
         '<p>Adicionado em 13/11/2026, depois que a checagem de produção da <code>S4b</code> achou <code>Redis command timed out</code> no back todos os dias. Medido em 14 dias: o próprio Redis é rápido, com <code>p99</code> de produção de no máximo 2 ms e CPU do engine de no máximo 4%. Os timeouts vêm do back: o timer de 250 ms dispara atrasado quando o event loop fica bloqueado, num pico por dia entre 14:05 e 14:20 UTC, inclusive nos fins de semana. Por isso os dois alarmes ficam quietos hoje e só disparam quando o próprio Redis piora.</p>'
         '<ul><li><b>Latência:</b> o alarme de latência, do lado do servidor.</li>'
         '<li><b>Erros:</b> ainda sem alarme. O único erro de Redis visto é o timeout do back, e um alarme sobre ele dispararia todo dia até o pico ser corrigido no back.</li>'
         '<li><b>Saturação:</b> memória, CPU do engine e chaves sem TTL. As conexões ficaram abaixo de 100 em prod, longe de qualquer limite.</li>'
         '<li><b>Tráfego:</b> sem alarme, porque nenhum limite separa tráfego bom de ruim.</li></ul>'),
 'ba':(('Nothing tells anyone when Redis gets slow.','Nada avisa ninguém quando o Redis fica lento.'),
       ('A latency alarm and a CPU alarm in prod, and a map of each golden signal.','Um alarme de latência e um de CPU em prod, e um mapa de cada sinal de ouro.'))},

{'n':'4','title':('One script to apply and check, and the threshold of 600','Um script para aplicar e checar, e o limite de 600'),
 'loc':'<code>scripts/e5-controls/</code>',
 'purpose':('Apply the four alarms from the values recorded in the spec, and check them before and after, read-only.',
            'Aplicar os quatro alarmes a partir dos valores registrados na spec, e checá-los antes e depois, só com leitura.'),
 'body':('<p><code>apply-prod.sh</code> runs four steps in order: <code>check</code> replays the four rules over the last 14 days without writing; <code>apply</code> asks for a typed confirmation and creates the topic, the subscription and the alarms; '
         '<code>verify</code> fails unless the subscription is confirmed and each alarm matches the spec; <code>fire-test</code> forces each alarm to <code>ALARM</code> and waits for it to return to <code>OK</code>. The user runs every AWS write.</p>'
         '<p>The keys-gap ceiling is 600, decided on 2026-11-18. The count includes the Bull queue keys, so it rises while jobs wait: it stays near 150, one point reached 525 during the A9b and S8c deploy, and its highest value held for three points in a row was 391. '
         '600 is 4 times the usual level and 53% above that peak, so a slower deploy raises no false alarm, while a writer that keeps adding keys without a TTL still crosses it.</p>'
         '<p>Validated on 2026-11-17 and 2026-11-18 with nothing applied: the read-only check passed for all four alarms over 14 days, and failed on each deliberate break (a ceiling of 300, a wrong metric name, an invalid operator). '
         'A stand-in for the AWS CLI recorded 0 writes. On 2026-11-18 the user ran <code>apply</code>: each alarm moved to <code>OK</code> within two minutes.</p>',
         '<p>O <code>apply-prod.sh</code> roda quatro passos em ordem: <code>check</code> reaplica as quatro regras nos últimos 14 dias sem escrever; <code>apply</code> pede uma confirmação digitada e cria o tópico, a assinatura e os alarmes; '
         '<code>verify</code> falha se a assinatura não estiver confirmada ou se algum alarme diferir da spec; <code>fire-test</code> força cada alarme para <code>ALARM</code> e espera que volte a <code>OK</code>. O usuário roda toda escrita na AWS.</p>'
         '<p>O limite da diferença de chaves é 600, decidido em 18/11/2026. A contagem inclui as chaves das filas do Bull, então sobe enquanto jobs esperam: fica perto de 150, um ponto chegou a 525 durante o deploy da A9b e da S8c, e o maior valor mantido por três pontos seguidos foi 391. '
         '600 é 4 vezes o nível usual e 53% acima desse pico, então um deploy mais lento não gera alarme falso, e um escritor que continua gravando chaves sem TTL ainda passa do limite.</p>'
         '<p>Validado em 17/11/2026 e 18/11/2026 sem aplicar nada: a checagem só de leitura passou para os quatro alarmes em 14 dias, e falhou em cada quebra proposital (um limite de 300, um nome de métrica errado, um operador inválido). '
         'Um substituto da CLI da AWS registrou 0 escritas. Em 18/11/2026 o usuário rodou o <code>apply</code>: cada alarme passou a <code>OK</code> em até dois minutos.</p>'),
 'ba':(('The thresholds and the recipient were open.','Os limites e o destinatário estavam em aberto.'),
       ('Both are recorded in the spec, and one script applies and verifies them.','Os dois estão registrados na spec, e um script os aplica e verifica.'))},
]

VERIF = [
 (True, ('Check before applying','Checar antes de aplicar'),
  ('<code>apply-prod.sh check</code> prints four <code>OK</code> lines and exits 0. Passed on 2026-11-17 and 2026-11-18.',
   'O <code>apply-prod.sh check</code> imprime quatro linhas <code>OK</code> e sai com 0. Passou em 17/11/2026 e 18/11/2026.')),
 (True, ('Apply in prod','Aplicar em prod'),
  ('<code>apply-prod.sh apply</code>, confirmed by typing <code>apply</code>. Done on 2026-11-18: the four alarms were created at 17:21 UTC and read <code>OK</code> on <code>Enhancedai-Redis-Alerts-PROD</code>.',
   'O <code>apply-prod.sh apply</code>, confirmado digitando <code>apply</code>. Feito em 18/11/2026: os quatro alarmes foram criados às 17:21 UTC e leem <code>OK</code> no <code>Enhancedai-Redis-Alerts-PROD</code>.')),
 (True, ('Confirm the subscription','Confirmar a assinatura'),
  ('The recipient clicks <b>Confirm subscription</b> in the AWS email. Open: the subscription reads <code>PendingConfirmation</code>, so no alert is delivered yet.',
   'O destinatário clica em <b>Confirm subscription</b> no email da AWS. Em aberto: a assinatura lê <code>PendingConfirmation</code>, então nenhum alerta é entregue ainda.')),
 (True, ('Verify','Verificar'),
  ('<code>apply-prod.sh verify</code> prints only <code>OK</code> lines and exits 0. Open: it fails by design until the subscription is confirmed.',
   'O <code>apply-prod.sh verify</code> imprime só linhas <code>OK</code> e sai com 0. Em aberto: falha por desenho até a assinatura ser confirmada.')),
 (True, ('Fire and recover','Disparar e recuperar'),
  ('Tell the team, then run <code>apply-prod.sh fire-test</code>: each alarm goes to <code>ALARM</code> and back to <code>OK</code>, and the recipient receives 4 <code>ALARM</code> and 4 <code>OK</code> emails. Open: not run yet.',
   'Avisar o time e rodar o <code>apply-prod.sh fire-test</code>: cada alarme vai para <code>ALARM</code> e volta para <code>OK</code>, e o destinatário recebe 4 emails de <code>ALARM</code> e 4 de <code>OK</code>. Em aberto: ainda não rodou.')),
]

DONE = ('The four alarms exist in prod, <code>verify</code> passes, and each alarm has been seen to fire and recover with <code>fire-test</code>.',
        'Os quatro alarmes existem em prod, o <code>verify</code> passa, e cada alarme foi visto disparar e recuperar com o <code>fire-test</code>.')

FILES = [('CloudWatch alarms and the SNS topic Enhancedai-Redis-Alerts-PROD, prod only', False),
         ('scripts/e5-controls/apply-prod.sh (check, apply, verify, fire-test)', True),
         ('scripts/e5-controls/create-alarms.sh (prints the commands; applies only on request)', False),
         ('scripts/e5-controls/check-alarms.sh (read-only replay of the four rules)', True),
         ('scripts/e5-controls/alarm-baseline.sh (read-only baseline)', True),
         ('TASK-E5-REDIS-POLICY-AND-SIZING.md (Alarms)', False)]

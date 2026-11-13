# -*- coding: utf-8 -*-
TITLE = ('Alert before Redis fills and when it evicts, in every environment',
         'Alertar antes de o Redis encher e quando ele remove chaves, em todos os ambientes')

GOAL = ('Someone is told <b>before a Redis that refuses writes fills up</b>, as soon as any Redis evicts a key, and when a Redis gets slow or runs out of CPU.',
        'Alguém é avisado <b>antes de um Redis que recusa escritas encher</b>, assim que qualquer Redis remove uma chave, e quando um Redis fica lento ou sem CPU.')

GLANCE = [
 ('crit', ('Why now','Por que agora'), ('No alarm exists','Não existe alarme'),
  ('Under <code>noeviction</code> a full Redis refuses writes. That only improves on silent eviction if someone watches memory, and the account has no ElastiCache alarm.',
   'Sob <code>noeviction</code> um Redis cheio recusa escritas. Isso só melhora a remoção silenciosa se alguém vigia a memória, e a conta não tem nenhum alarme de ElastiCache.')),
 ('dep', ('Depends on','Depende de'), ('Nothing','Nada'),
  ('It carries the alarms that <code>E5</code> decided on 2026-10-02 and left open when it closed.',
   'Leva os alarmes que a <code>E5</code> decidiu em 02/10/2026 e deixou abertos ao fechar.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('<code>E5</code> itself stays in Wave 4.','A própria <code>E5</code> continua na Onda 4.')),
 ('ship', ('Shape','Formato'), ('Infrastructure only','Só infraestrutura'),
  ('Added on 2026-11-11 when <code>E5</code> closed. No application code.',
   'Adicionada em 11/11/2026 quando a <code>E5</code> fechou. Nenhum código de aplicação.')),
]

LEDE = (
 '<p>On 2026-11-11 dev, staging and prod all run a <code>noeviction</code> Redis, so a full Redis <strong>refuses writes instead of silently dropping the dedup keys</strong>. '
 'That is only an improvement if someone is watching memory, and <strong>the account has no ElastiCache alarm</strong>.</p>'
 '<p>The task creates the three alarms <code>E5</code> decided on, plus a latency alarm and an engine CPU alarm added on 2026-11-13, in each environment, and sends them to a new email topic per environment so Redis alerts do not reach the subscribers of the existing topics.</p>',
 '<p>Em 11/11/2026 dev, staging e prod rodam um Redis <code>noeviction</code>, então um Redis cheio <strong>recusa escritas em vez de descartar em silêncio as chaves de dedup</strong>. '
 'Isso só melhora se alguém vigia a memória, e <strong>a conta não tem nenhum alarme de ElastiCache</strong>.</p>'
 '<p>A task cria os três alarmes que a <code>E5</code> decidiu, mais um alarme de latência e um de CPU do engine adicionados em 13/11/2026, em cada ambiente, e os envia a um novo tópico de email por ambiente, para que os alertas de Redis não cheguem aos inscritos dos tópicos existentes.</p>')

TABLE = dict(
 head=[('Alarm','Alarme'),('Metric','Métrica'),('Rule','Regra')],
 rows=[
  [('Memory usage','Uso de memória'),
   ('<code>DatabaseMemoryUsagePercentage</code>, maximum','<code>DatabaseMemoryUsagePercentage</code>, máximo'),
   {'t':('Above 50% for two periods of 300 s','Acima de 50% por dois períodos de 300 s'),'pill':'ok'}],
  [('Evictions','Evicções'),
   ('<code>Evictions</code>, sum','<code>Evictions</code>, soma'),
   {'t':('Above 0 in 300 s','Acima de 0 em 300 s'),'pill':'ok'}],
  [('Keys without a TTL outside Bull','Chaves sem TTL fora do Bull'),
   ('Metric math: items minus volatile items','Metric math: itens menos itens voláteis'),
   {'t':('Above a threshold per environment','Acima de um limite por ambiente'),'pill':'ok'}],
  [('Latency','Latência'),
   ('Metric math: highest read or write <code>p99</code> over the three nodes','Metric math: maior <code>p99</code> de leitura ou escrita entre os três nós'),
   {'t':('Above 10 ms for three periods of 300 s','Acima de 10 ms por três períodos de 300 s'),'pill':'ok'}],
  [('Engine CPU','CPU do engine'),
   ('Metric math: highest <code>EngineCPUUtilization</code> over the three nodes','Metric math: maior <code>EngineCPUUtilization</code> entre os três nós'),
   {'t':('Above 80% for three periods of 300 s','Acima de 80% por três períodos de 300 s'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('Five alarms per environment','Cinco alarmes por ambiente'),
 'loc':'CloudWatch alarms',
 'purpose':('Create the memory, eviction, keys-gap, latency and engine CPU alarms in dev, staging and prod, each with a recovery notification.',
            'Criar os alarmes de memória, evicção, diferença de chaves, latência e CPU do engine em dev, staging e prod, cada um com notificação de recuperação.'),
 'body':('<p>The keys-gap threshold is set for dev and staging; for prod it comes from a fresh TTL audit. A script prints the commands and changes nothing until it is told to apply; the person who owns the account runs every AWS write.</p>',
         '<p>O limite do alarme de chaves é definido para dev e staging; para prod vem de uma nova auditoria de TTL. Um script imprime os comandos e não muda nada até receber ordem de aplicar; quem é dono da conta roda toda escrita na AWS.</p>'),
 'ba':(('No ElastiCache alarm exists.','Não existe alarme de ElastiCache.'),
       ('Five alarms per environment, each with a recovery notice.','Cinco alarmes por ambiente, cada um com aviso de recuperação.'))},

{'n':'2','title':('A separate email topic per environment','Um tópico de email separado por ambiente'),
 'loc':'SNS topics',
 'purpose':('Each alarm and recovery notifies a new topic, so Redis alerts do not reach the existing external subscribers.',
            'Cada alarme e recuperação notifica um tópico novo, para que os alertas de Redis não cheguem aos inscritos externos existentes.'),
 'body':('<p>Out of scope: re-measuring the pub/sub rate after <code>B5</code>, and the automatic failover and multi-zone decision, which stays separate as in <code>E5</code>.</p>',
         '<p>Fora de escopo: medir de novo a taxa de pub/sub depois da <code>B5</code>, e a decisão de failover automático e multi-zona, que continua separada como na <code>E5</code>.</p>')},

{'n':'3','title':('Latency and the golden signals','Latência e os sinais de ouro'),
 'loc':'CloudWatch alarms',
 'purpose':('Cover Redis latency and CPU, and record which alarm covers each golden signal.',
            'Cobrir a latência e a CPU do Redis, e registrar qual alarme cobre cada sinal de ouro.'),
 'body':('<p>Added on 2026-11-13, after the <code>S4b</code> production check found <code>Redis command timed out</code> in the back every day. Measured over 14 days: Redis itself is fast, with production <code>p99</code> at most 1.7 ms and engine CPU at most 3.9%. The timeouts come from the back: its 250 ms timer fires late when its event loop is blocked, in one burst a day between 14:05 and 14:20 UTC, weekends included. So the two new alarms stay quiet today and fire only when Redis itself degrades.</p>'
         '<ul><li><b>Latency:</b> the latency alarm, on the server side.</li>'
         '<li><b>Errors:</b> no alarm yet. The only Redis error seen is the back timeout, and an alarm on it would fire every day until the burst is fixed in the back.</li>'
         '<li><b>Saturation:</b> memory, engine CPU, evictions and keys without a TTL. Connections peaked at 72, far from any limit.</li>'
         '<li><b>Traffic:</b> no alarm, because no threshold separates good from bad traffic.</li></ul>',
         '<p>Adicionado em 13/11/2026, depois que a checagem de produção da <code>S4b</code> achou <code>Redis command timed out</code> no back todos os dias. Medido em 14 dias: o próprio Redis é rápido, com <code>p99</code> de produção de no máximo 1,7 ms e CPU do engine de no máximo 3,9%. Os timeouts vêm do back: o timer de 250 ms dispara atrasado quando o event loop fica bloqueado, num pico por dia entre 14:05 e 14:20 UTC, inclusive nos fins de semana. Por isso os dois alarmes novos ficam quietos hoje e só disparam quando o próprio Redis piora.</p>'
         '<ul><li><b>Latência:</b> o alarme de latência, do lado do servidor.</li>'
         '<li><b>Erros:</b> ainda sem alarme. O único erro de Redis visto é o timeout do back, e um alarme sobre ele dispararia todo dia até o pico ser corrigido no back.</li>'
         '<li><b>Saturação:</b> memória, CPU do engine, evicções e chaves sem TTL. As conexões chegaram a 72 no máximo, longe de qualquer limite.</li>'
         '<li><b>Tráfego:</b> sem alarme, porque nenhum limite separa tráfego bom de ruim.</li></ul>'),
 'ba':(('Nothing tells anyone when Redis gets slow.','Nada avisa ninguém quando o Redis fica lento.'),
       ('A latency alarm and a CPU alarm per environment, and a map of each golden signal.','Um alarme de latência e um de CPU por ambiente, e um mapa de cada sinal de ouro.'))},
]

VERIF = [
 (True, ('Confirm before applying','Confirmar antes de aplicar'),
  ('Confirm the recipient and the prod threshold of the keys-gap alarm.',
   'Confirmar o destinatário e o limite de prod do alarme de chaves.')),
 (True, ('Fire and recover in dev','Disparar e recuperar em dev'),
  ('Breach each alarm on purpose by lowering its threshold, confirm the email arrives, then restore the threshold and confirm the recovery email. Dev Redis is idle most of the time, so run a flow during the latency test.',
   'Estourar cada alarme de propósito baixando o limite, confirmar que o email chega, depois restaurar o limite e confirmar o email de recuperação. O Redis de dev fica ocioso quase sempre, então rode um flow durante o teste de latência.')),
 (True, ('Read each alarm back','Ler cada alarme de volta'),
  ('Read each alarm back from CloudWatch and confirm its dimension names the right replication group and its action names the right topic.',
   'Ler cada alarme de volta no CloudWatch e confirmar que a dimensão cita o replication group certo e a ação cita o tópico certo.')),
]

DONE = ('The five alarms exist in dev, staging and prod, each has been seen to fire and recover in dev, and the recipients and thresholds are recorded in the spec.',
        'Os cinco alarmes existem em dev, staging e prod, cada um foi visto disparar e recuperar em dev, e os destinatários e limites estão registrados na spec.')

FILES = [('CloudWatch alarms and SNS topics, per environment', False),
         ('scripts/e5-controls/create-alarms.sh (prints the commands; applies only on request)', False),
         ('TASK-E5-REDIS-POLICY-AND-SIZING.md (Alarms)', False)]

# -*- coding: utf-8 -*-
TITLE = ('Alert before Redis fills and when it evicts, in every environment',
         'Alertar antes de o Redis encher e quando ele remove chaves, em todos os ambientes')

GOAL = ('Someone is told <b>before a Redis that refuses writes fills up</b>, and as soon as any Redis evicts a key.',
        'Alguém é avisado <b>antes de um Redis que recusa escritas encher</b>, e assim que qualquer Redis remove uma chave.')

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
 '<p>The task creates the three alarms <code>E5</code> decided on, in each environment, and sends them to a new email topic per environment so Redis alerts do not reach the subscribers of the existing topics.</p>',
 '<p>Em 11/11/2026 dev, staging e prod rodam um Redis <code>noeviction</code>, então um Redis cheio <strong>recusa escritas em vez de descartar em silêncio as chaves de dedup</strong>. '
 'Isso só melhora se alguém vigia a memória, e <strong>a conta não tem nenhum alarme de ElastiCache</strong>.</p>'
 '<p>A task cria os três alarmes que a <code>E5</code> decidiu, em cada ambiente, e os envia a um novo tópico de email por ambiente, para que os alertas de Redis não cheguem aos inscritos dos tópicos existentes.</p>')

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
 ])

PARTS = [
{'n':'1','title':('Three alarms per environment','Três alarmes por ambiente'),
 'loc':'CloudWatch alarms',
 'purpose':('Create the memory, eviction and keys-gap alarms in dev, staging and prod, each with a recovery notification.',
            'Criar os alarmes de memória, evicção e diferença de chaves em dev, staging e prod, cada um com notificação de recuperação.'),
 'body':('<p>The keys-gap threshold is set for dev and staging; for prod it comes from a fresh TTL audit. A script prints the commands and changes nothing until it is told to apply; the person who owns the account runs every AWS write.</p>',
         '<p>O limite do alarme de chaves é definido para dev e staging; para prod vem de uma nova auditoria de TTL. Um script imprime os comandos e não muda nada até receber ordem de aplicar; quem é dono da conta roda toda escrita na AWS.</p>'),
 'ba':(('No ElastiCache alarm exists.','Não existe alarme de ElastiCache.'),
       ('Three alarms per environment, each with a recovery notice.','Três alarmes por ambiente, cada um com aviso de recuperação.'))},

{'n':'2','title':('A separate email topic per environment','Um tópico de email separado por ambiente'),
 'loc':'SNS topics',
 'purpose':('Each alarm and recovery notifies a new topic, so Redis alerts do not reach the existing external subscribers.',
            'Cada alarme e recuperação notifica um tópico novo, para que os alertas de Redis não cheguem aos inscritos externos existentes.'),
 'body':('<p>Out of scope: re-measuring the pub/sub rate after <code>B5</code>, and the automatic failover and multi-zone decision, which stays separate as in <code>E5</code>.</p>',
         '<p>Fora de escopo: medir de novo a taxa de pub/sub depois da <code>B5</code>, e a decisão de failover automático e multi-zona, que continua separada como na <code>E5</code>.</p>')},
]

VERIF = [
 (True, ('Confirm before applying','Confirmar antes de aplicar'),
  ('Confirm the recipient and the prod threshold of the keys-gap alarm.',
   'Confirmar o destinatário e o limite de prod do alarme de chaves.')),
 (True, ('Fire and recover in dev','Disparar e recuperar em dev'),
  ('Breach each alarm on purpose by lowering its threshold, confirm the email arrives, then restore the threshold and confirm the recovery email.',
   'Estourar cada alarme de propósito baixando o limite, confirmar que o email chega, depois restaurar o limite e confirmar o email de recuperação.')),
 (True, ('Read each alarm back','Ler cada alarme de volta'),
  ('Read each alarm back from CloudWatch and confirm its dimension names the right replication group and its action names the right topic.',
   'Ler cada alarme de volta no CloudWatch e confirmar que a dimensão cita o replication group certo e a ação cita o tópico certo.')),
]

DONE = ('The three alarms exist in dev, staging and prod, each has been seen to fire and recover in dev, and the recipients and thresholds are recorded in the spec.',
        'Os três alarmes existem em dev, staging e prod, cada um foi visto disparar e recuperar em dev, e os destinatários e limites estão registrados na spec.')

FILES = [('CloudWatch alarms and SNS topics, per environment', False),
         ('scripts/e5-controls/create-alarms.sh (prints the commands; applies only on request)', False),
         ('TASK-E5-REDIS-POLICY-AND-SIZING.md (Alarms)', False)]

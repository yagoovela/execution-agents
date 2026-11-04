# -*- coding: utf-8 -*-
TITLE = ("Size the database and the boot for the back's replica ceiling",
         'Dimensionar o banco e o boot para o teto de réplicas do back')

GOAL = ('The back&#x27;s autoscaling ceiling is <b>a number the database and the boot can hold</b>, and the number is recorded.',
        'O teto de autoscaling do back é <b>um número que o banco e o boot aguentam</b>, e esse número fica registrado.')

GLANCE = [
 ('crit', ('Never checked','Nunca conferido'), ('Connections and boot migrations','Conexões e migrations no boot'),
  ('Production can run three back tasks. Nobody has checked the connection sum or two tasks booting together.',
   'A produção pode rodar três tasks do back. Ninguém conferiu a soma de conexões nem duas tasks subindo juntas.')),
 ('dep', ('Depends on','Depende de'), ('Nothing','Nada'),
  ('It closes after <code>E3b</code>, <code>S8b</code> and <code>S10</code>, because it records the ceiling they allow.',
   'Fecha depois da <code>E3b</code>, da <code>S8b</code> e da <code>S10</code>, porque registra o teto que elas permitem.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('First in the wave, with the other back-replica tasks.',
   'Primeira da onda, junto com as outras tasks de réplica do back.')),
 ('ship', ('Shape','Formato'), ('Measurement, maybe a boot lock','Medição, talvez um lock no boot'),
  ('Added on 2026-11-04 from the replica audit of that day.',
   'Adicionada em 04/11/2026 a partir da auditoria de réplicas daquele dia.')),
]

LEDE = (
 '<p>Production autoscales the back from one to three tasks on CPU, and it reaches two every day. Two things were never checked against that ceiling. '
 'Each back task opens up to 30 database connections by default and each worker task up to 12, so <strong>three back tasks need about 90 connections</strong> '
 'before the worker, the MCP server and Temporal are counted.</p>'
 '<p>The back also runs its pending migrations at boot, in one transaction, with no lock between processes. When a deploy starts several tasks together, '
 'each one tries to run the same migrations.</p>',
 '<p>A produção faz autoscaling do back de uma a três tasks pela CPU, e chega a duas todo dia. Duas coisas nunca foram conferidas contra esse teto. '
 'Cada task do back abre até 30 conexões de banco por padrão e cada task do worker até 12, então <strong>três tasks do back precisam de cerca de 90 conexões</strong> '
 'antes de contar o worker, o servidor MCP e o Temporal.</p>'
 '<p>O back também roda as migrations pendentes no boot, numa transação, sem lock entre processos. Quando um deploy sobe várias tasks juntas, '
 'cada uma tenta rodar as mesmas migrations.</p>')

TABLE = dict(
 head=[('Check','Conferência'),('Today','Hoje'),('After S11','Depois da S11')],
 rows=[
  [('Connection budget','Orçamento de conexões'),
   {'t':('Never compared with <code>max_connections</code>','Nunca comparado com o <code>max_connections</code>'),'pill':'weak'},
   {'t':('Written down and fits','Escrito e cabendo'),'pill':'ok'}],
  [('Two tasks booting with a pending migration','Duas tasks subindo com uma migration pendente'),
   {'t':('Unknown: a crash or a lock wait','Desconhecido: crash ou espera de lock'),'pill':'weak'},
   {'t':('The migration runs once','A migration roda uma vez'),'pill':'ok'}],
  [('Autoscaling ceiling','Teto de autoscaling'),
   {'t':('3, with no record of why','3, sem registro do porquê'),'pill':'weak'},
   {'t':('Recorded, with the date','Registrado, com a data'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('Write the connection budget','Escrever o orçamento de conexões'),
 'loc':'back/src/config/config.service.ts',
 'purpose':('Compare back pool × ceiling + worker pool × workers + other clients with <code>max_connections</code>.',
            'Comparar pool do back × teto + pool do worker × workers + outros clientes com o <code>max_connections</code>.'),
 'body':('<p>The production numbers are read by the user. If the budget does not fit, lower the pool or the ceiling and record which.</p>',
         '<p>Os números de produção são lidos pelo usuário. Se o orçamento não couber, baixar o pool ou o teto e registrar qual.</p>')},

{'n':'2','title':('Run each migration once','Rodar cada migration uma vez'),
 'loc':'back/src/main.ts',
 'purpose':('Prove what happens when two back processes boot together, and make the migration run once.',
            'Provar o que acontece quando dois processos do back sobem juntos, e fazer a migration rodar uma vez.'),
 'body':('<p>Two options: a Postgres advisory lock around the migration run, or migrations as a separate deploy step before the tasks start. Record the choice.</p>',
         '<p>Duas opções: um advisory lock do Postgres em volta da execução das migrations, ou as migrations como um passo separado do deploy antes das tasks subirem. Registrar a escolha.</p>')},

{'n':'3','title':('Record the ceiling','Registrar o teto'),
 'loc':'api-autoscaling-prod',
 'purpose':('State the ceiling the back may autoscale to, the date, and the tasks it waited for.',
            'Dizer o teto até onde o back pode escalar, a data, e as tasks pelas quais ele esperou.'),
 'body':('<p>The autoscaling policy changes only with the user&#x27;s decision.</p>',
         '<p>A política de autoscaling só muda com a decisão do usuário.</p>')},
]

VERIF = [
 (True, ('Negative control — concurrent boot','Controle negativo — boot simultâneo'),
  ('Boot two back processes together against a dev database with one pending migration and record what happens on <code>main</code>. After the change it runs once; remove the lock and watch the test fail.',
   'Subir dois processos do back juntos num banco de dev com uma migration pendente e registrar o que acontece no <code>main</code>. Depois da mudança ela roda uma vez; tirar o lock e ver o teste falhar.')),
 (False, ('Production numbers','Números de produção'),
  ('The user reads <code>max_connections</code> and the connection peak in production; the budget is written with the date.',
   'O usuário lê o <code>max_connections</code> e o pico de conexões em produção; o orçamento é escrito com a data.')),
]

DONE = ('The connection budget fits <code>max_connections</code> at the recorded ceiling, two back tasks booting together run a pending migration once, and the ceiling and the date are recorded.',
        'O orçamento de conexões cabe no <code>max_connections</code> no teto registrado, duas tasks do back subindo juntas rodam uma migration pendente uma vez, e o teto e a data estão registrados.')

FILES = [('back/src/config/config.service.ts (TYPEORM_POOL_MAX, migrationsRun)', False),
         ('back/src/main.ts', False),
         ('worker/src/modules/database/database.service.ts', False)]

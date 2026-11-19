# -*- coding: utf-8 -*-
TITLE = ('Run the schedule reconcile once per back task',
         'Rodar o reconcile dos agendamentos uma vez por task do back')

GOAL = ('A back task that boots runs the schedule reconcile <b>once</b>, in the main app, and the database seed starts nothing but its own writes.',
        'Uma task do back que sobe roda o reconcile dos agendamentos <b>uma vez</b>, na aplicação principal, e o seed do banco não sobe nada além das próprias escritas.')

GLANCE = [
 ('crit', ('Customer impact','Impacto no cliente'), ('Harmless today','Inofensivo hoje'),
  ('Each back task logged the reconcile twice at boot. The seed context also started 17 crons and 7 Bull processors, including <code>api-v2</code>; whether it took a production job is not measured.',
   'Cada task do back logava o reconcile duas vezes no boot. O contexto do seed também subia 17 crons e 7 processors do Bull, incluindo o <code>api-v2</code>; se ele pegou algum job de produção não foi medido.')),
 ('dep', ('Depends on','Depende de'), ('Nothing','Nada'),
  ('Coordinates with <code>A9b</code>, which owns the order of the steps in <code>dev.sh</code>.',
   'Coordena com a <code>A9b</code>, dona da ordem dos passos no <code>dev.sh</code>.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('Found by the <code>S8b</code> production check.',
   'Achada pela checagem de produção da <code>S8b</code>.')),
 ('ship', ('Shape','Formato'), ('Back only','Só o back'),
  ('Added on 2026-11-17 and revised the same day; in production since 2026-11-18, with A9b.',
   'Adicionada em 17/11/2026 e revisada no mesmo dia; em produção desde 18/11/2026, junto com a A9b.')),
]

LEDE = (
 '<p>After the <code>S8b</code> release, Datadog showed each back task logging <code>Reconciled 53 active schedule(s); 0 registered</code> twice, 9 to 15 s apart. '
 '<code>dev.sh</code> runs <code>node dist/seed.js</code> once the app is healthy, and <code>SeederModule</code> imported the whole <code>AppModule</code>, so '
 '<strong>the seed context ran every boot hook a second time</strong>, the schedule registrar included. The cron lock does not stop it, because the main app released the lock seconds earlier.</p>'
 '<p>The first version of the spec blamed three modules that would provide the registrars; only <code>AppApiModule</code> does. The seven seeders inject only TypeORM repositories and <code>Logger</code>, '
 'so the seed needs none of what <code>AppModule</code> starts. Measured on 71 production boots, the seed took p50 14 s and p90 37 s, of which about 2 s is seeding.</p>',
 '<p>Depois da liberação da <code>S8b</code>, o Datadog mostrou cada task do back logando <code>Reconciled 53 active schedule(s); 0 registered</code> duas vezes, com 9 a 15 s de intervalo. '
 'O <code>dev.sh</code> roda o <code>node dist/seed.js</code> quando a aplicação está saudável, e o <code>SeederModule</code> importava o <code>AppModule</code> inteiro, então '
 '<strong>o contexto do seed rodava todos os hooks de boot uma segunda vez</strong>, incluindo o registrar de agendamentos. O lock de cron não impede, porque a aplicação principal soltou o lock segundos antes.</p>'
 '<p>A primeira versão da spec culpava três módulos que forneceriam os registrars; só o <code>AppApiModule</code> fornece. Os sete seeders injetam só repositórios do TypeORM e o <code>Logger</code>, '
 'então o seed não precisa de nada do que o <code>AppModule</code> sobe. Medido em 71 boots de produção, o seed levava p50 14 s e p90 37 s, dos quais cerca de 2 s são o seeding.</p>')

TABLE = dict(
 head=[('At each back boot','Em cada boot do back'),('Before S8c','Antes da S8c'),('After S8c','Depois da S8c')],
 rows=[
  [('Schedule reconcile','Reconcile dos agendamentos'),
   {'t':('Twice: in the app and in the seed','Duas vezes: na aplicação e no seed'),'pill':'weak'},
   {'t':('Once, in the app','Uma vez, na aplicação'),'pill':'ok'}],
  [('Boot hooks in the seed context','Hooks de boot no contexto do seed'),
   {'t':('Five, the schedule registrars and <code>TemporalService</code> included','Cinco, incluindo os registrars de agendamento e o <code>TemporalService</code>'),'pill':'weak'},
   {'t':('None','Nenhum'),'pill':'ok'}],
  [('Crons and Bull processors in the seed context','Crons e processors do Bull no contexto do seed'),
   {'t':('17 crons and 7 processors, <code>api-v2</code> included','17 crons e 7 processors, incluindo o <code>api-v2</code>'),'pill':'weak'},
   {'t':('None','Nenhum'),'pill':'ok'}],
  [('Seed time in production','Tempo do seed em produção'),
   {'t':('p50 14 s, p90 37 s','p50 14 s, p90 37 s'),'pill':'weak'},
   {'t':('About 3 s on 2026-11-18','Cerca de 3 s em 18/11/2026'),'pill':'ok'}],
 ])

PARTS = [
{'n':'1','title':('The seed imports only what the seeders use','O seed importa só o que os seeders usam'),
 'loc':'back/src/database/seeders/seeder.module.ts',
 'purpose':('<code>SeederModule</code> imports the TypeORM root and the seven seeder modules, provides <code>Logger</code> and <code>Seeder</code>, and no longer imports <code>AppModule</code>.',
            'O <code>SeederModule</code> importa a raiz do TypeORM e os sete módulos de seeder, fornece <code>Logger</code> e <code>Seeder</code>, e não importa mais o <code>AppModule</code>.'),
 'body':('<p>A unit test walks the <code>SeederModule</code> import graph and proves that no schedule registrar, no Bull processor and no cron is reachable, and that <code>AppModule</code> and <code>AppApiModule</code> are not. '
         'A second test builds <code>SeederModule</code> with a fake data source, so a seeder that needs a provider only <code>AppModule</code> supplied fails it. The seeded rows and <code>seed.ts</code> do not change.</p>',
         '<p>Um teste unitário percorre o grafo de imports do <code>SeederModule</code> e prova que nenhum registrar de agendamento, nenhum processor do Bull e nenhum cron é alcançável, e que <code>AppModule</code> e <code>AppApiModule</code> não são. '
         'Um segundo teste monta o <code>SeederModule</code> com um data source falso, então um seeder que precise de um provider que só o <code>AppModule</code> fornecia falha nele. As linhas semeadas e o <code>seed.ts</code> não mudam.</p>'),
 'ba':(('The seed boots the whole app a second time.','O seed sobe a aplicação inteira uma segunda vez.'),
       ('The seed opens the database, seeds and exits.','O seed abre o banco, semeia e sai.'))},

{'n':'2','title':('One TypeORM root for the app and the seed','Uma raiz do TypeORM para a aplicação e o seed'),
 'loc':'back/src/database/typeorm-root.module.ts',
 'purpose':('The TypeORM root definition moves out of <code>app.module.ts</code> into one exported definition that <code>AppModule</code> and <code>SeederModule</code> both import.',
            'A definição da raiz do TypeORM sai do <code>app.module.ts</code> para uma definição exportada que <code>AppModule</code> e <code>SeederModule</code> importam.'),
 'body':('<p>It is not restated, so the seed keeps the migration runner and its advisory lock: against a database with pending migrations, the seed applies them under the lock before it seeds. '
         'S8c works with either order of the seed in <code>dev.sh</code>, which belongs to <code>A9b</code>.</p>',
         '<p>Ela não é repetida, então o seed mantém o executor de migrations e o advisory lock: num banco com migrations pendentes, o seed as aplica sob o lock antes de semear. '
         'A S8c funciona com qualquer ordem do seed no <code>dev.sh</code>, que é da <code>A9b</code>.</p>')},
]

VERIF = [
 (True, ('Negative control — the import graph','Controle negativo — o grafo de imports'),
  ('Put <code>AppModule</code> back in <code>SeederModule.imports</code>: the test fails and lists the three registrars, the 7 Bull consumers and the boot hooks.',
   'Pôr o <code>AppModule</code> de volta em <code>SeederModule.imports</code>: o teste falha e lista os três registrars, os 7 consumers do Bull e os hooks de boot.')),
 (True, ('Same rows, same migrations','As mesmas linhas, as mesmas migrations'),
  ('On two copies of the local database, the branch and <code>origin/main</code> seeds wrote identical content and counts across 97 tables, and a second run changed nothing. An un-applied migration was applied by the seed before it seeded.',
   'Em duas cópias do banco local, os seeds da branch e do <code>origin/main</code> gravaram conteúdo e contagens idênticos em 97 tabelas, e uma segunda execução não mudou nada. Uma migration não aplicada foi aplicada pelo seed antes de semear.')),
 (True, ('One reconcile per boot','Um reconcile por boot'),
  ('A local boot through <code>dev.sh</code> with <code>repeatable_schedules</code> on logs one <code>Reconciled</code> line; the same boot built from <code>origin/main</code> logs two.',
   'Um boot local pelo <code>dev.sh</code> com <code>repeatable_schedules</code> ligada loga uma linha <code>Reconciled</code>; o mesmo boot montado a partir do <code>origin/main</code> loga duas.')),
 (True, ('Dev (2026-11-17)','Dev (17/11/2026)'),
  ('The new task logs <code>AppApiModule dependencies initialized</code> once, where every earlier task that day logged it twice, and the seed took 1.1 s against 5 to 8 s. The <code>S8b</code> schedule test gave one run per tick on create and on update, and none after delete.',
   'A task nova loga <code>AppApiModule dependencies initialized</code> uma vez, onde toda task anterior daquele dia logava duas, e o seed levou 1,1 s contra 5 a 8 s. O teste de agendamento da <code>S8b</code> deu um run por disparo na criação e na edição, e nenhum depois de apagar.')),
 (True, ('Production (2026-11-18)','Produção (18/11/2026)'),
  ('CloudWatch, read-only: both new back tasks log <code>AppApiModule dependencies initialized</code> once, and the seed took 3.05 s and 2.85 s against the 71-boot baseline of p50 14 s, p90 37 s and max 42 s, with no <code>seed failed</code>. The Datadog <code>Reconciled</code> count was not read.',
   'CloudWatch, só leitura: as duas tasks novas do back logam <code>AppApiModule dependencies initialized</code> uma vez, e o seed levou 3,05 s e 2,85 s contra a base de 71 boots de p50 14 s, p90 37 s e máximo 42 s, sem <code>seed failed</code>. A contagem de <code>Reconciled</code> no Datadog não foi lida.')),
]

DONE = ('The seed context has no schedule registrar, Bull processor or cron, each back task reconciles once, the seed applies pending migrations and writes the same rows, schedules work as before, and the production seed time is recorded.',
        'O contexto do seed não tem registrar de agendamento, processor do Bull nem cron, cada task do back faz o reconcile uma vez, o seed aplica as migrations pendentes e grava as mesmas linhas, os agendamentos funcionam como antes, e o tempo do seed em produção está registrado.')

FILES = [('back/src/database/seeders/seeder.module.ts', False),
         ('back/src/database/seeders/seeder.module.spec.ts', True),
         ('back/src/database/typeorm-root.module.ts', True),
         ('back/src/app.module.ts', False)]

# -*- coding: utf-8 -*-
TITLE = ('Size the database connections before adding workers',
         'Dimensionar as conexões de banco antes de somar workers')

GOAL = ('Know, and enforce, <b>how many Postgres connections the worker fleet can hold</b> — before anything in this epic adds a replica.',
        'Saber, e impor, <b>quantas conexões de Postgres a frota de workers pode segurar</b> — antes que qualquer coisa deste épico some uma réplica.')

GLANCE = [
 ('crit', ('Severity', 'Severidade'), ('Critical', 'Crítica'),
  ('The single biggest obstacle to running more workers — and it is one line of config plus a capacity decision. Review §2.1.',
   'O maior obstáculo isolado para rodar mais workers — e é uma linha de config mais uma decisão de capacidade. Review §2.1.')),
 ('dep', ('Depends on', 'Depende de'), ('Nothing', 'Nada'),
  ('But it <strong>blocks B5</strong> — and it blocks adding a worker replica today.',
   'Mas <strong>bloqueia a B5</strong> — e bloqueia somar uma réplica de worker hoje.')),
 ('wave', ('Wave', 'Onda'), ('Wave 1', 'Onda 1'),
  ('Wave 1 is where the fleet becomes able to grow. Every wave after it assumes more workers.',
   'A onda 1 é onde a frota passa a poder crescer. Toda onda depois dela pressupõe mais workers.')),
 ('ship', ('Deliverable', 'Entrega'), ('A sentence', 'Uma frase'),
  ('The capacity arithmetic, with real numbers and a supported replica count. The config change is trivial once it exists.',
   'A conta de capacidade, com números reais e uma contagem de réplicas suportadas. A mudança de config é trivial depois que ela existe.')),
]

LEDE = (
 """<p><code>database.service.ts:13</code> constructs <code>new Pool({...})</code> with <strong>no <code>max</code></strong>. node-postgres then defaults to ten connections per pool, per process — and the worker runs <code>maxConcurrentActivityTaskExecutions: 10</code> (<code>worker.service.ts:22</code>), so a replica can hold ten busy connections and the total scales <strong>linearly with replicas</strong>.</p>
<p><code>max_connections</code> is a hard wall, and <strong>the wall is shared with the API</strong>. The failure mode is not a slow worker — it is <code>too many clients already</code> on customer-facing requests. No connection proxy appears in the compose files or the infra.</p>""",
 """<p>O <code>database.service.ts:13</code> constrói <code>new Pool({...})</code> <strong>sem <code>max</code></strong>. O node-postgres então assume dez conexões por pool, por processo — e o worker roda <code>maxConcurrentActivityTaskExecutions: 10</code> (<code>worker.service.ts:22</code>), então uma réplica pode segurar dez conexões ocupadas e o total cresce <strong>linearmente com as réplicas</strong>.</p>
<p><code>max_connections</code> é um teto rígido, e <strong>o teto é compartilhado com a API</strong>. O modo de falha não é um worker lento — é <code>too many clients already</code> em requisições de cliente. Nenhum proxy de conexão aparece nos arquivos de compose nem na infra.</p>""")

TABLE = {
 'k': 'table',
 'head': [('Term in the arithmetic', 'Termo da conta'), ('Where the number comes from', 'De onde vem o número'),
          ('Status', 'Situação'), ('What it decides', 'O que ele decide')],
 'rows': [
  [{'t': ('Worker pool <code>max</code>, per replica', '<code>max</code> do pool do worker, por réplica')},
   ('Unset — node-postgres falls back to ten', 'Não definido — o node-postgres cai em dez'),
   {'t': ('implicit', 'implícito'), 'pill': 'weak'},
   ('A default nobody chose is doing the sizing.', 'Um padrão que ninguém escolheu está fazendo o dimensionamento.')],
  [{'t': ('<code>maxConcurrentActivityTaskExecutions</code>', '<code>maxConcurrentActivityTaskExecutions</code>')},
   ('10, in <code>worker.service.ts:22</code>', '10, em <code>worker.service.ts:22</code>'),
   {'t': ('explicit', 'explícito'), 'pill': 'ok'},
   ('The only number in the chain someone actually picked.', 'O único número da cadeia que alguém de fato escolheu.')],
  [{'t': ('<code>api_replicas × api_pool</code>', '<code>api_replicas × api_pool</code>')},
   ('Not stated anywhere in this repository', 'Não está declarado em lugar nenhum deste repositório'),
   {'t': ('unknown', 'desconhecido'), 'pill': 'no'},
   ('It shares the same wall — and it is where the failure lands first.',
    'Ela divide o mesmo teto — e é onde a falha aparece primeiro.')],
  [{'t': ('Migrations and operators', 'Migrações e operadores')},
   ('Unbudgeted', 'Sem orçamento'),
   {'t': ('unknown', 'desconhecido'), 'pill': 'no'},
   ('Small — and exactly what is missing at the moment the wall is hit.',
    'Pequeno — e exatamente o que falta no momento em que o teto é atingido.')],
  [{'t': ('<code>max_connections</code>', '<code>max_connections</code>')},
   ('The server side, shared with the API', 'O lado servidor, compartilhado com a API'),
   {'t': ('out of scope to tune', 'fora de escopo ajustar'), 'pill': 'weak'},
   ('This task states what it must support; it does not tune it.',
    'Esta task declara o que ele precisa suportar; não o ajusta.')],
  [{'t': ('Supported worker replicas', 'Réplicas de worker suportadas')},
   ('The output of the sum above', 'A saída da soma acima'),
   {'t': ('missing', 'faltando'), 'pill': 'no'},
   ('<strong>This is the deliverable.</strong> Every capacity decision after this point reads it.',
    '<strong>Esta é a entrega.</strong> Toda decisão de capacidade depois deste ponto lê este número.')],
 ]}

DEC_MAX = {
 'k': 'decision', 'id': 'S2-a', 'plan': 'D8', 'status': 'rec', 'open': True,
 'q': ('What sets the worker pool&#x27;s <code>max</code>, and where does the number come from?',
       'O que define o <code>max</code> do pool do worker, e de onde vem o número?'),
 'intro': (
  'The spec states this as an assumption rather than a decision: <strong><code>max</code> equal to <code>maxConcurrentActivityTaskExecutions</code> plus two</strong>, '
  'the two being headroom for the health check and for anything that opens a connection outside an activity. '
  'It is worth confirming out loud because of a detail that is easy to miss: <strong>the pool ceiling today is also ten</strong> — node-postgres&#x27;s default — '
  'so <code>10 + 2</code> does not lower per-replica usage, it raises it by two and makes it deliberate. '
  'What the change actually buys is the <em>timeouts</em> that ship with it.',
  'A spec declara isto como premissa, não como decisão: <strong><code>max</code> igual a <code>maxConcurrentActivityTaskExecutions</code> mais dois</strong>, '
  'sendo os dois a folga para o health check e para qualquer coisa que abra conexão fora de uma activity. '
  'Vale confirmar em voz alta por causa de um detalhe fácil de passar batido: <strong>o teto do pool hoje também é dez</strong> — o padrão do node-postgres — '
  'então <code>10 + 2</code> não reduz o uso por réplica, aumenta em dois e o torna deliberado. '
  'O que a mudança de fato compra são os <em>timeouts</em> que vêm junto.'),
 'opts': [
  {'ltr': 'A', 'pick': True, 'name': ('Derived — activity concurrency plus two', 'Derivado — concorrência de activity mais dois'),
   'tag': ('assumption', 'premissa'),
   'how': ('The pool size is an expression, not a literal: it is computed from <code>maxConcurrentActivityTaskExecutions</code>, so the two cannot drift apart.',
           'O tamanho do pool é uma expressão, não um literal: é calculado a partir de <code>maxConcurrentActivityTaskExecutions</code>, para que os dois não se descolem.'),
   'pros': [('Raising activity concurrency cannot silently exceed the pool — the two move together',
             'Aumentar a concorrência de activity não pode estourar o pool em silêncio — os dois se movem juntos'),
            ('Setting <code>max</code> above the activity concurrency cannot help anyway: the worker has no activities to run on the extra connections',
             'Definir <code>max</code> acima da concorrência de activity não ajuda de todo jeito: o worker não tem activities para rodar nas conexões extras'),
            ('The <code>+2</code> is named, not magic — the health check, and anything that opens a connection outside an activity',
             'O <code>+2</code> tem nome, não é mágico — o health check, e qualquer coisa que abra conexão fora de uma activity')],
   'cons': [('Twelve per replica is two more than today&#x27;s implicit ten, so the arithmetic has to be redone with 12',
             'Doze por réplica são dois a mais que os dez implícitos de hoje, então a conta precisa ser refeita com 12')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('lo', ('Ours: <b>one expression in the pool config</b>', 'Nosso: <b>uma expressão na config do pool</b>'))]},
  {'ltr': 'B', 'name': ('A fixed number from the environment', 'Um número fixo, vindo do ambiente'),
   'how': ('An env var holds the pool size, independent of the activity concurrency, so it can be turned down without a deploy.',
           'Uma env var guarda o tamanho do pool, independente da concorrência de activity, para poder ser reduzido sem deploy.'),
   'pros': [('Can be lowered during an incident without shipping code', 'Pode ser reduzido durante um incidente sem subir código'),
            ('Lets a constrained environment run a smaller pool than its concurrency suggests',
             'Permite que um ambiente apertado rode um pool menor do que a concorrência sugere')],
   'cons': [('Two numbers that have to agree, in two places, with nothing enforcing it',
             'Dois números que precisam concordar, em dois lugares, sem nada garantindo isso'),
            ('A pool smaller than the activity concurrency becomes contention that looks like a slow provider',
             'Um pool menor que a concorrência de activity vira contenção que parece um provedor lento')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('', ('Ours: <b>one env var, and a pair that can drift</b>', 'Nosso: <b>uma env var, e um par que pode se descolar</b>'))]},
  {'ltr': 'C', 'no': True, 'name': ('Leave it implicit', 'Deixar implícito'),
   'tag': ('not viable', 'inviável'),
   'how': ('Keep the pool as it is: no <code>max</code>, no <code>idleTimeoutMillis</code>, no <code>connectionTimeoutMillis</code>.',
           'Manter o pool como está: sem <code>max</code>, sem <code>idleTimeoutMillis</code>, sem <code>connectionTimeoutMillis</code>.'),
   'pros': [('Nothing to change today', 'Nada a mudar hoje')],
   'cons': [('The sizing is a library default, and a dependency bump can move it',
             'O dimensionamento é um padrão de biblioteca, e um bump de dependência pode mudá-lo'),
            ('Without <code>connectionTimeoutMillis</code> a saturated pool <strong>hangs</strong> the activity until its <code>startToCloseTimeout</code> — the mysterious failure rather than the diagnosable one',
             'Sem <code>connectionTimeoutMillis</code> um pool saturado <strong>trava</strong> a activity até o <code>startToCloseTimeout</code> dela — a falha misteriosa em vez da diagnosticável')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>every saturation looks like a hang</b>', 'Nosso: <b>toda saturação parece um travamento</b>'))]},
 ],
 'rec': (
  '<p><strong>A, with B as the escape hatch: derive the default, allow an env override.</strong> The derivation is what keeps the two numbers honest; the override is what lets an incident be handled without a deploy.</p>'
  '<p><strong>And ship the timeouts with it.</strong> <code>idleTimeoutMillis</code> and <code>connectionTimeoutMillis</code> are the half of this decision that actually changes behaviour — they turn “the activity hung until Temporal gave up” into “the pool refused, and said which pool”.</p>',
  '<p><strong>A, com B como válvula de escape: derive o padrão, permita sobrescrever por env.</strong> A derivação é o que mantém os dois números honestos; a sobrescrita é o que permite tratar um incidente sem deploy.</p>'
  '<p><strong>E entregue os timeouts junto.</strong> <code>idleTimeoutMillis</code> e <code>connectionTimeoutMillis</code> são a metade desta decisão que de fato muda comportamento — transformam “a activity travou até o Temporal desistir” em “o pool recusou, e disse qual pool”.</p>'),
 'who': [('Engineering', 'Engenharia'), ('Infra confirms the per-replica budget', 'Infra confirma o orçamento por réplica')],
}

DEC_PROXY = {
 'k': 'decision', 'id': 'S2-b', 'plan': 'D8', 'status': 'open',
 'q': ('Does the replica count stay bounded by <code>max_connections</code>, or does a pooler decouple them?',
       'A contagem de réplicas continua limitada pelo <code>max_connections</code>, ou um pooler desacopla os dois?'),
 'intro': (
  'The task&#x27;s “done when” requires the proxy decision to be <strong>recorded either way</strong>, which is the honest framing: <em>not</em> adopting a pooler is also a decision, '
  'and its consequence is that the supported replica count becomes a fixed number a capacity request has to renegotiate. '
  'The spec recommends <strong>PgBouncer in transaction mode</strong> and names the constraint that comes with it — which is load-bearing for two other tasks.',
  'O “pronto quando” da task exige que a decisão do proxy seja <strong>registrada de qualquer forma</strong>, e esse é o enquadramento honesto: <em>não</em> adotar um pooler também é uma decisão, '
  'e a consequência dela é que a contagem de réplicas suportadas vira um número fixo que todo pedido de capacidade precisa renegociar. '
  'A spec recomenda <strong>PgBouncer em modo transação</strong> e nomeia a restrição que vem junto — que é estrutural para outras duas tasks.'),
 'opts': [
  {'ltr': 'A', 'pick': True, 'name': ('PgBouncer in transaction mode', 'PgBouncer em modo transação'),
   'tag': ('recommended', 'recomendada'),
   'how': ('A pooler multiplexes many client connections onto few server connections, so the replica count stops being the thing that consumes <code>max_connections</code>.',
           'Um pooler multiplexa muitas conexões de cliente em poucas conexões de servidor, então a contagem de réplicas deixa de ser o que consome o <code>max_connections</code>.'),
   'pros': [('<strong>The only option that makes “many workers” open-ended</strong> — replica count and connection count stop being the same number',
             '<strong>A única opção que torna “muitos workers” aberto</strong> — contagem de réplicas e de conexões deixam de ser o mesmo número'),
            ('<code>pg_advisory_xact_lock</code> survives it: it is transaction-scoped, already used in <code>oauth-token.repo.ts:7</code>, and planned for A7',
             'O <code>pg_advisory_xact_lock</code> sobrevive: tem escopo de transação, já é usado em <code>oauth-token.repo.ts:7</code>, e está planejado para a A7'),
            ('No application change beyond a connection string', 'Nenhuma mudança de aplicação além de uma string de conexão')],
   'cons': [('Transaction mode forbids session-level state — prepared statements, session settings, and <strong>session-level advisory locks, which would not survive</strong>',
             'O modo transação proíbe estado de sessão — prepared statements, settings de sessão, e <strong>advisory locks de sessão, que não sobreviveriam</strong>'),
            ('A new component in the path of every query, with its own failure modes and its own sizing',
             'Um componente novo no caminho de toda query, com seus próprios modos de falha e seu próprio dimensionamento')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>one more component to run and page on</b>', 'Nosso: <b>mais um componente para rodar e ser acordado por</b>'))]},
  {'ltr': 'B', 'name': ('No proxy — spend the wall on a fixed replica budget', 'Sem proxy — gastar o teto num orçamento fixo de réplicas'),
   'how': ('Skip the pooler and let the arithmetic produce a hard number: this database supports N worker replicas, and N is the ceiling until the database changes.',
           'Dispensar o pooler e deixar a conta produzir um número duro: este banco suporta N réplicas de worker, e N é o teto até o banco mudar.'),
   'pros': [('Nothing new to run — the arithmetic <em>is</em> the whole deliverable',
             'Nada novo para rodar — a conta <em>é</em> a entrega inteira'),
            ('No session-state constraint at all, so session-level advisory locks stay available',
             'Nenhuma restrição de estado de sessão, então advisory locks de sessão continuam disponíveis')],
   'cons': [('Every capacity increase becomes a database change, negotiated ahead of time',
             'Todo aumento de capacidade vira uma mudança de banco, negociada com antecedência'),
            ('<strong>It is a ceiling on the epic itself</strong> — B5 multiplies the work each replica does, and the replica count is what absorbs that',
             '<strong>É um teto sobre o próprio épico</strong> — a B5 multiplica o trabalho de cada réplica, e é a contagem de réplicas que absorve isso')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('', ('Ours: <b>a number to renegotiate each time</b>', 'Nosso: <b>um número para renegociar a cada vez</b>'))]},
  {'ltr': 'C', 'name': ('Raise <code>max_connections</code>', 'Elevar o <code>max_connections</code>'),
   'how': ('Leave the client side alone and buy room on the server, so the linear growth has further to run before it hits the wall.',
           'Deixar o lado cliente como está e comprar espaço no servidor, para que o crescimento linear tenha mais espaço antes de bater no teto.'),
   'pros': [('The fastest thing to do during an incident', 'A coisa mais rápida de fazer durante um incidente'),
            ('No new component, and no session-state constraint', 'Nenhum componente novo, e nenhuma restrição de estado de sessão')],
   'cons': [('<strong>The spec puts tuning Postgres out of scope</strong> — choosing this changes the task&#x27;s boundary, not only its answer',
             '<strong>A spec põe ajustar o Postgres fora de escopo</strong> — escolher isto muda a fronteira da task, não só a resposta dela'),
            ('Each connection costs a server-side process and its own working memory, so it trades throughput for connection count',
             'Cada conexão custa um processo no servidor e memória de trabalho própria, então troca throughput por número de conexões'),
            ('It postpones the linear growth; it does not remove it', 'Adia o crescimento linear; não o elimina')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>buys time, not a ceiling</b>', 'Nosso: <b>compra tempo, não um teto</b>'))]},
  {'ltr': 'D', 'name': ('A managed pooler', 'Um pooler gerenciado'),
   'tag': ('variant of A', 'variante de A'),
   'how': ('The same multiplexing as A, run by the platform instead of by us — the “or equivalent” the review leaves open next to PgBouncer.',
           'A mesma multiplexação de A, operada pela plataforma em vez de por nós — o “ou equivalente” que a review deixa aberto ao lado do PgBouncer.'),
   'pros': [('The operational half of A without a component of our own to run',
             'A metade operacional de A sem um componente nosso para rodar'),
            ('Failover handling comes with it', 'O tratamento de failover vem junto')],
   'cons': [('The same session-state constraint as A — it is the same pooling model',
             'A mesma restrição de estado de sessão de A — é o mesmo modelo de pooling'),
            ('A cost per hour, and less control over pool sizing than PgBouncer gives',
             'Um custo por hora, e menos controle sobre o dimensionamento do pool do que o PgBouncer dá')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('', ('Ours: <b>a bill instead of a component</b>', 'Nosso: <b>uma fatura em vez de um componente</b>'))]},
 ],
 'rec': (
  '<p><strong>A — but record it even if the answer turns out to be B.</strong> The arithmetic decides which: if the current database already supports the replica count this epic needs, B is honest, free, and revisitable. If it does not, A is the only option that removes the coupling rather than moving it.</p>'
  '<p>One thing to test rather than assume, whichever wins: <code>pg_advisory_xact_lock</code> under transaction pooling, using the <strong>existing OAuth refresh path</strong> as the test. It is transaction-scoped, so it should survive — and “should” is not a test result.</p>',
  '<p><strong>A — mas registre mesmo que a resposta acabe sendo B.</strong> Quem decide é a conta: se o banco atual já suporta a contagem de réplicas que este épico precisa, B é honesta, de graça e revisitável. Se não suporta, A é a única opção que remove o acoplamento em vez de deslocá-lo.</p>'
  '<p>Uma coisa a testar em vez de supor, qualquer que seja a escolha: <code>pg_advisory_xact_lock</code> sob pooling de transação, usando o <strong>caminho existente de refresh do OAuth</strong> como teste. Ele tem escopo de transação, então deveria sobreviver — e “deveria” não é resultado de teste.</p>'),
 'who': [('Infra', 'Infra'), ('Engineering confirms the advisory-lock behaviour', 'Engenharia confirma o comportamento do advisory lock')],
}

PARTS = [
{'n': '1',
 'title': ('The pool that was never given a ceiling', 'O pool que nunca ganhou um teto'),
 'loc': 'worker/src/modules/database/database.service.ts:13',
 'purpose': ('Make the per-replica connection count an explicit number, and make a saturated pool fail fast instead of hanging.',
             'Tornar o número de conexões por réplica um número explícito, e fazer um pool saturado falhar rápido em vez de travar.'),
 'body': ('<p>The worker builds its pool like this:</p>', '<p>O worker monta o pool assim:</p>'),
 'code': ('new Pool({ host, port, user, password, database })',
          'new Pool({ host, port, user, password, database })'),
 'body2': (
  '<p>No <code>max</code>, no <code>idleTimeoutMillis</code>, no <code>connectionTimeoutMillis</code>. The first omission hands the sizing to a library default. The third decides what a saturated pool <em>feels</em> like: without it, a caller waiting for a connection simply waits, and the activity hangs until Temporal ends it at its <code>startToCloseTimeout</code>.</p>'
  '<p>That is what this half of the task actually buys — <strong>a diagnosable incident instead of a mysterious one</strong>.</p>',
  '<p>Sem <code>max</code>, sem <code>idleTimeoutMillis</code>, sem <code>connectionTimeoutMillis</code>. A primeira omissão entrega o dimensionamento a um padrão de biblioteca. A terceira decide como um pool saturado <em>se sente</em>: sem ela, quem espera por uma conexão simplesmente espera, e a activity trava até o Temporal encerrá-la no <code>startToCloseTimeout</code>.</p>'
  '<p>É isso que esta metade da task de fato compra — <strong>um incidente diagnosticável em vez de um misterioso</strong>.</p>'),
 'ba': (('Ten connections per replica by library default, and a saturated pool that hangs an activity until its <code>startToCloseTimeout</code> — a timeout that names Temporal, not the pool.',
         'Dez conexões por réplica por padrão de biblioteca, e um pool saturado que trava a activity até o <code>startToCloseTimeout</code> dela — um timeout que nomeia o Temporal, não o pool.'),
        ('An explicit <code>max</code>, plus <code>idleTimeoutMillis</code> and <code>connectionTimeoutMillis</code>, so saturation returns a connection timeout <strong>naming the pool</strong>, in seconds rather than minutes.',
         'Um <code>max</code> explícito, mais <code>idleTimeoutMillis</code> e <code>connectionTimeoutMillis</code>, para que a saturação devolva um timeout de conexão <strong>nomeando o pool</strong>, em segundos e não em minutos.'))},
{'n': '2',
 'title': ('The arithmetic is the deliverable', 'A conta é a entrega'),
 'loc': 'worker/src/modules/temporal/worker.service.ts:20–22 · infra/compose',
 'purpose': ('Write the capacity sum down with real numbers, and state how many worker replicas this database supports.',
             'Escrever a soma de capacidade com números reais, e declarar quantas réplicas de worker este banco suporta.'),
 'body': ('<p>The sentence this task has to produce is this one:</p>', '<p>A frase que esta task precisa produzir é esta:</p>'),
 'code': ('max_connections  >=  (api_replicas    x  api_pool)\n                   +  (worker_replicas x  worker_pool)\n                   +  migrations\n                   +  operators',
          'max_connections  >=  (api_replicas    x  api_pool)\n                   +  (worker_replicas x  worker_pool)\n                   +  migrations\n                   +  operators'),
 'body2': (
  '<p>Every term on the right is knowable today, and <strong>only one of them is written down anywhere</strong> — the worker&#x27;s activity concurrency. The output is a single number: <em>how many worker replicas this database supports</em>.</p>'
  '<p>The config change is trivial once that sentence exists. Without it, the config change is a guess with a decimal point in it.</p>',
  '<p>Todo termo da direita é conhecível hoje, e <strong>só um deles está escrito em algum lugar</strong> — a concorrência de activity do worker. A saída é um número só: <em>quantas réplicas de worker este banco suporta</em>.</p>'
  '<p>A mudança de config é trivial depois que essa frase existe. Sem ela, a mudança de config é um chute com casa decimal.</p>'),
 'ba': (('Nobody can say how many workers this database supports. The answer is discovered by hitting the wall — and because the wall is shared, it is discovered by the API.',
         'Ninguém sabe dizer quantos workers este banco suporta. A resposta é descoberta batendo no teto — e como o teto é compartilhado, quem descobre é a API.'),
        ('The number is written down next to the terms it came from, so the next capacity decision reads it instead of re-deriving it.',
         'O número fica escrito ao lado dos termos que o produziram, para que a próxima decisão de capacidade o leia em vez de refazer a conta.')),
 'callouts': [('mig', ('Out of scope — tuning Postgres', 'Fora de escopo — ajustar o Postgres'),
   ('<p>This task sizes the <strong>client</strong> side and states what the server side must support. Whether <code>max_connections</code> itself should be raised is a separate call — the second decision above.</p>',
    '<p>Esta task dimensiona o lado <strong>cliente</strong> e declara o que o lado servidor precisa suportar. Se o próprio <code>max_connections</code> deve ser elevado é outra decisão — a segunda acima.</p>'))]},
{'n': '3',
 'title': ('The one thing a transaction-mode pooler would break', 'A única coisa que um pooler em modo transação quebraria'),
 'loc': 'oauth-token.repo.ts:7',
 'purpose': ('Name the constraint honestly before adopting the pooler, and prove it with the path that already relies on it.',
             'Nomear a restrição honestamente antes de adotar o pooler, e prová-la com o caminho que já depende dela.'),
 'body': (
  '<p>Transaction-mode pooling forbids session-level state: a client is given a server connection for the duration of a <em>transaction</em>, not of a session. Anything that outlives the transaction — a session setting, a prepared statement, a session-level advisory lock — does not survive.</p>'
  '<p><code>pg_advisory_xact_lock</code> is <strong>transaction-scoped by name</strong>, so it does survive. It is already used at <code>oauth-token.repo.ts:7</code>, <code>A7</code> plans to use it for ordering, and <code>S8</code> proposes an advisory lock per cron job name. The answer to this question is load-bearing for three tasks, not one.</p>',
  '<p>O pooling em modo transação proíbe estado de sessão: o cliente recebe uma conexão de servidor pela duração de uma <em>transação</em>, não de uma sessão. Tudo que sobrevive à transação — um setting de sessão, um prepared statement, um advisory lock de sessão — não sobrevive.</p>'
  '<p>O <code>pg_advisory_xact_lock</code> tem <strong>escopo de transação já no nome</strong>, então sobrevive. Ele já é usado em <code>oauth-token.repo.ts:7</code>, a <code>A7</code> planeja usá-lo para ordenação, e a <code>S8</code> propõe um advisory lock por nome de job de cron. A resposta a esta pergunta é estrutural para três tasks, não uma.</p>'),
 'ba': (('No proxy exists, so the question has never been asked — and two other tasks are about to plan around advisory locks.',
         'Nenhum proxy existe, então a pergunta nunca foi feita — e outras duas tasks estão prestes a planejar em cima de advisory locks.'),
        ('The constraint is written down, and the OAuth refresh path is the test that proves <code>pg_advisory_xact_lock</code> still behaves under transaction pooling.',
         'A restrição fica escrita, e o caminho de refresh do OAuth é o teste que prova que o <code>pg_advisory_xact_lock</code> continua se comportando sob pooling de transação.')),
 'callouts': [('decide', ('Tell S8 which lock it may use', 'Dizer à S8 qual lock ela pode usar'),
   ('<p>If a pooler is adopted, <code>S8</code>&#x27;s cron guard must be a <strong>transaction-scoped</strong> lock. A guard described as “taken at the top of the run and released at the end” is a session-level lock by instinct — and that is exactly the shape transaction pooling drops.</p>'
    '<p>Under a pooler, holding the lock for the job means the <strong>job runs inside the transaction that holds it</strong>. That is a real constraint for a long purge, and it is better discovered here than in S8&#x27;s PR.</p>',
    '<p>Se um pooler for adotado, a guarda de cron da <code>S8</code> precisa ser um lock com <strong>escopo de transação</strong>. Uma guarda descrita como “tomada no início do run e liberada no fim” é, por instinto, um lock de sessão — e é exatamente o formato que o pooling de transação descarta.</p>'
    '<p>Sob um pooler, segurar o lock durante o job significa que o <strong>job roda dentro da transação que o segura</strong>. Isso é uma restrição real para um purge longo, e é melhor descobri-la aqui do que no PR da S8.</p>'))]},
]

VERIF = [
 (True, ('Negative control', 'Controle negativo'),
  ('Set <code>max</code> to <strong>1</strong> and run two concurrent activities. Confirm the second fails with a <strong>connection timeout naming the pool</strong>, rather than hanging until the Temporal timeout. The difference between those two failure modes is the difference between a diagnosable incident and a mysterious one.',
   'Defina <code>max</code> como <strong>1</strong> e rode duas activities concorrentes. Confirme que a segunda falha com um <strong>timeout de conexão que nomeia o pool</strong>, em vez de travar até o timeout do Temporal. A diferença entre esses dois modos de falha é a diferença entre um incidente diagnosticável e um misterioso.')),
 (False, ('Count connections, do not count configuration', 'Conte conexões, não conte configuração'),
  ('Measure the <strong>actual</strong> concurrent connections per replica under a realistic flow. The configured maximum is a ceiling, not a prediction — a pool that never reaches eight makes the arithmetic conservative in a way worth knowing about.',
   'Meça as conexões concorrentes <strong>reais</strong> por réplica sob um fluxo realista. O máximo configurado é um teto, não uma previsão — um pool que nunca chega a oito torna a conta conservadora de um jeito que vale saber.')),
 (False, ('The API&#x27;s half of the wall is measured too', 'A metade da API também é medida'),
  ('The ceiling is shared, so sizing only the worker leaves half the sum unknown. <code>api_replicas × api_pool</code> has to be a <strong>measured</strong> term, not an assumed one, or the arithmetic proves nothing.',
   'O teto é compartilhado, então dimensionar só o worker deixa metade da soma desconhecida. <code>api_replicas × api_pool</code> precisa ser um termo <strong>medido</strong>, não suposto, ou a conta não prova nada.')),
 (False, ('The advisory lock survives the pooler, if one is adopted', 'O advisory lock sobrevive ao pooler, se algum for adotado'),
  ('Confirm <code>pg_advisory_xact_lock</code> still behaves under transaction pooling, using the <strong>existing OAuth refresh path</strong> as the test the spec names — not a synthetic one, which can pass for the wrong reason.',
   'Confirme que o <code>pg_advisory_xact_lock</code> continua se comportando sob pooling de transação, usando o <strong>caminho existente de refresh do OAuth</strong> como o teste que a spec nomeia — não um sintético, que pode passar pelo motivo errado.')),
]

DONE = ('The pool has <strong>explicit limits</strong>, the capacity arithmetic is <strong>written down with real numbers</strong>, the <strong>supported replica count is stated</strong>, and the proxy decision is <strong>recorded either way</strong>.',
        'O pool tem <strong>limites explícitos</strong>, a conta de capacidade está <strong>escrita com números reais</strong>, a <strong>contagem de réplicas suportadas está declarada</strong>, e a decisão do proxy está <strong>registrada de qualquer forma</strong>.')

FILES = [
 ('worker/src/modules/database/database.service.ts:13', False),
 ('worker/src/modules/temporal/worker.service.ts:20–22', False),
 ('infra/compose', False),
 ('the capacity arithmetic, written down', True),
 ('env-vars-sync', True),
]

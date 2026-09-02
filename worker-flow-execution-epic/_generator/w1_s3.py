# -*- coding: utf-8 -*-
TITLE = ('A ceiling on what one run can spend', 'Um teto para o que um run pode gastar')

GOAL = ('Bound <b>cost</b> and bound <b>fairness</b>, before parallelism removes the accidental throttle that provides both today.',
        'Limitar <b>custo</b> e limitar <b>justiça</b>, antes que o paralelismo remova o freio acidental que fornece os dois hoje.')

GLANCE = [
 ('crit', ('Severity', 'Severidade'), ('High', 'Alta'),
  ('Nothing decrements an allowance and nothing aborts an overspent run. For a paid account, the first signal is the invoice. Review §1.3, §1.4.',
   'Nada decrementa uma cota e nada aborta um run que já gastou demais. Numa conta paga, o primeiro sinal é a fatura. Review §1.3, §1.4.')),
 ('dep', ('Depends on', 'Depende de'), ('Nothing', 'Nada'),
  ('But it <strong>blocks B5</strong> — parallel dispatch removes what is left of the back-pressure protecting both limits today.',
   'Mas <strong>bloqueia a B5</strong> — o dispatch paralelo remove o que resta da contrapressão que hoje protege os dois limites.')),
 ('wave', ('Wave', 'Onda'), ('Wave 1', 'Onda 1'),
  ('With S2: the two ceilings that have to exist before the fleet is allowed to grow.',
   'Junto da S2: os dois tetos que precisam existir antes de a frota poder crescer.')),
 ('ship', ('Shape', 'Formato'), ('Two limits, one counter', 'Dois limites, um contador'),
  ('A spend ceiling on the <strong>chain root</strong>, and a per-org concurrency cap. The counter is shared with S4.',
   'Um teto de gasto na <strong>raiz da cadeia</strong>, e um teto de concorrência por organização. O contador é compartilhado com a S4.')),
]

LEDE = (
 """<p><strong>Spend.</strong> <code>assertCompletionCredits</code> (<code>product.service.ts</code>) is a boolean gate: for <code>INTRO</code> products it checks <code>trialTokens &gt; 0</code>; otherwise, having a subscription is enough. Per node, <code>getUserProductFromFlow</code> checks <em>entitlement to a model</em>, not remaining budget. Charges are recorded after the fact into <code>token_transactions</code>. <strong>Nothing decrements an allowance, and nothing aborts a run that has already overspent.</strong></p>
<p><strong>Tenancy.</strong> There is no per-tenant concurrency cap anywhere. <strong>Corrected 2026-09-02.</strong> The first draft said the Bull processor declared <code>@Process</code> with no concurrency option, so each replica ran one queued run at a time and that accident was doing protective work. Since 2026-08-21 (PR #1902) <code>apiV2Job.processor.ts</code> declares <code>@Process({ concurrency: parseConcurrency(AGENT_CONCURRENCY) })</code>, default <strong>5</strong> per replica — explicit, five times looser, and still not per tenant: one organisation can hold all five slots on every replica. It caps <em>how many</em> runs execute, not <em>whose</em>. Keep the two limits distinct — the tenant cap admits, <code>AGENT_CONCURRENCY</code> executes — and start with the per-tenant metric, so five stops being a guess. <code>B5</code> removes the remaining back-pressure deliberately.</p>""",
 """<p><strong>Gasto.</strong> O <code>assertCompletionCredits</code> (<code>product.service.ts</code>) é uma porta booleana: para produtos <code>INTRO</code> ele checa <code>trialTokens &gt; 0</code>; fora disso, ter assinatura basta. Por node, o <code>getUserProductFromFlow</code> checa <em>direito a um modelo</em>, não orçamento restante. As cobranças são registradas depois do fato em <code>token_transactions</code>. <strong>Nada decrementa uma cota, e nada aborta um run que já gastou demais.</strong></p>
<p><strong>Tenancy.</strong> Não existe teto de concorrência por tenant em lugar nenhum. <strong>Corrigido em 2026-09-02.</strong> A primeira versão dizia que o processador Bull declarava <code>@Process</code> sem opção de concorrência, então cada réplica rodava um run por vez e esse acidente fazia trabalho protetivo. Desde 2026-08-21 (PR #1902) o <code>apiV2Job.processor.ts</code> declara <code>@Process({ concurrency: parseConcurrency(AGENT_CONCURRENCY) })</code>, padrão <strong>5</strong> por réplica — explícito, cinco vezes mais frouxo, e ainda não por tenant: uma organização pode ocupar as cinco vagas em toda réplica. Ele limita <em>quantos</em> runs executam, não <em>de quem</em>. Mantenha os dois limites separados — o teto de tenant admite, o <code>AGENT_CONCURRENCY</code> executa — e comece pela métrica por tenant, para que cinco deixe de ser chute. A <code>B5</code> remove o que resta de contrapressão de propósito.</p>""")

TABLE = {
 'k': 'table',
 'head': [('Control today', 'Controle hoje'), ('What it checks', 'O que ele checa'),
          ('Kind', 'Tipo'), ('What it does not stop', 'O que ele não impede')],
 'rows': [
  [{'t': ('<code>assertCompletionCredits</code>', '<code>assertCompletionCredits</code>')},
   ('<code>INTRO</code>: <code>trialTokens &gt; 0</code>. Otherwise: a subscription exists',
    '<code>INTRO</code>: <code>trialTokens &gt; 0</code>. Fora disso: existir uma assinatura'),
   {'t': ('boolean gate', 'porta booleana'), 'pill': 'weak'},
   ('A paid account passes at any spend, on every run', 'Uma conta paga passa com qualquer gasto, em todo run')],
  [{'t': ('<code>getUserProductFromFlow</code>', '<code>getUserProductFromFlow</code>')},
   ('Entitlement to a model, per node', 'Direito a um modelo, por node'),
   {'t': ('entitlement', 'direito'), 'pill': 'weak'},
   ('It says <em>which</em> model may run, never <em>how much</em>', 'Ele diz <em>qual</em> modelo pode rodar, nunca <em>quanto</em>')],
  [{'t': ('<code>token_transactions</code>', '<code>token_transactions</code>')},
   ('Records the charge after it happened', 'Registra a cobrança depois que ela aconteceu'),
   {'t': ('after the fact', 'a posteriori'), 'pill': 'no'},
   ('Nothing decrements it, so nothing can abort on it', 'Nada o decrementa, então nada pode abortar com base nele')],
  [{'t': ('Bull <code>@Process</code>, <code>AGENT_CONCURRENCY</code> = 5 (none until 2026-08-21)', 'Bull <code>@Process</code>, <code>AGENT_CONCURRENCY</code> = 5 (nenhuma até 2026-08-21)')},
   ('Five queued runs per backend replica, none of them per tenant', 'Cinco runs enfileirados por réplica de backend, nenhum deles por tenant'),
   {'t': ('accidental', 'acidental'), 'pill': 'weak'},
   ('It is doing real work — and <code>B5</code> removes it on purpose', 'Ele faz trabalho real — e a <code>B5</code> o remove de propósito')],
 ]}

DEC_CEILING = {
 'k': 'decision', 'id': 'S3-a', 'plan': 'D7', 'status': 'rec', 'open': True,
 'q': ('When a run hits its cost ceiling, does it abort, degrade, pause, or only warn?',
       'Quando um run atinge seu teto de custo, ele aborta, degrada, pausa, ou só avisa?'),
 'intro': (
  'The spec states this as an assumption: <strong>the run aborts rather than degrades</strong>. It is worth confirming out loud, '
  'because the alternatives are all things a product team can reasonably want — and three of them either <strong>produce output the user did not ask for</strong> '
  'or leave a run in a state nothing owns.',
  'A spec declara isto como premissa: <strong>o run aborta em vez de degradar</strong>. Vale confirmar em voz alta, '
  'porque as alternativas são todas coisas que um time de produto pode querer com razão — e três delas ou <strong>produzem saída que o usuário não pediu</strong> '
  'ou deixam o run num estado que ninguém é dono.'),
 'opts': [
  {'ltr': 'A', 'pick': True, 'name': ('Abort with a typed error', 'Abortar com um erro tipado'),
   'tag': ('assumption', 'premissa'),
   'how': ('The charge call refuses, the run ends, and the error carries <strong>the ceiling and the spend</strong> so the UI can say what happened.',
           'A chamada de cobrança recusa, o run termina, e o erro carrega <strong>o teto e o gasto</strong> para a UI poder dizer o que aconteceu.'),
   'pros': [('Honest and cheap to explain — the run stopped, and here is the number it stopped at',
             'Honesto e barato de explicar — o run parou, e este é o número em que parou'),
            ('The failure lands at the moment the money would have been spent, not at the invoice',
             'A falha acontece no momento em que o dinheiro seria gasto, não na fatura'),
            ('A typed error is something the front can render specifically, instead of a generic failure',
             'Um erro tipado é algo que o front consegue renderizar de forma específica, em vez de uma falha genérica')],
   'cons': [('A long run that was nearly finished is lost, and the spend up to that point is real',
             'Um run longo quase terminado é perdido, e o gasto até ali é real'),
            ('Whatever the run was going to deliver does not arrive — so the ceiling has to be right, which is what the measurement is for',
             'O que o run ia entregar não chega — então o teto precisa estar certo, e é para isso que serve a medição')],
   'cost': [('', ('Client effort: <b>raise the ceiling, or split the flow</b>', 'Esforço do cliente: <b>elevar o teto, ou dividir o fluxo</b>')),
            ('lo', ('Ours: <b>one check where the charge already is</b>', 'Nosso: <b>uma checagem onde a cobrança já está</b>'))]},
  {'ltr': 'B', 'name': ('Degrade to a cheaper model', 'Degradar para um modelo mais barato'),
   'how': ('On reaching the ceiling, the run continues on a smaller or cheaper model instead of stopping.',
           'Ao atingir o teto, o run continua num modelo menor ou mais barato em vez de parar.'),
   'pros': [('The run finishes, and the customer gets something', 'O run termina, e o cliente recebe alguma coisa'),
            ('Spend keeps falling instead of stopping dead', 'O gasto continua caindo em vez de parar seco')],
   'cons': [('It <strong>hides the problem and produces output the user did not ask for</strong> — the flow named a model on purpose',
             'Ele <strong>esconde o problema e produz saída que o usuário não pediu</strong> — o fluxo nomeou um modelo de propósito'),
            ('A silent quality change is the worst kind of surprise in an automation something else consumes downstream',
             'Uma mudança silenciosa de qualidade é a pior surpresa numa automação que outra coisa consome a jusante'),
            ('Every node type would need a defined fallback, and some have none',
             'Todo tipo de node precisaria de um fallback definido, e alguns não têm nenhum')],
   'cost': [('hi', ('Client effort: <b>discover it happened</b>', 'Esforço do cliente: <b>descobrir que aconteceu</b>')),
            ('hi', ('Ours: <b>a fallback matrix per node type</b>', 'Nosso: <b>uma matriz de fallback por tipo de node</b>'))]},
  {'ltr': 'C', 'name': ('Pause and ask', 'Pausar e perguntar'),
   'how': ('The run suspends at the ceiling and waits for the owner to approve more spend.',
           'O run suspende no teto e espera o dono aprovar mais gasto.'),
   'pros': [('No work is thrown away, and the decision goes to the person who pays',
             'Nenhum trabalho é jogado fora, e a decisão vai para quem paga'),
            ('It is the right answer for an expensive, long, human-supervised run',
             'É a resposta certa para um run caro, longo e supervisionado por gente')],
   'cons': [('A background execution system has nobody watching at 3 a.m. — a paused run is an abandoned run',
             'Um sistema de execução em background não tem ninguém olhando às 3 da manhã — um run pausado é um run abandonado'),
            ('It needs a resume path, a timeout on the pause, and a place in the UI that does not exist yet',
             'Exige um caminho de retomada, um timeout para a pausa, e um lugar na UI que ainda não existe'),
            ('Held state costs something: a paused run occupies a slot in the tenancy cap while it waits',
             'Estado parado custa alguma coisa: um run pausado ocupa uma vaga no teto de tenancy enquanto espera')],
   'cost': [('hi', ('Client effort: <b>be there to answer</b>', 'Esforço do cliente: <b>estar lá para responder</b>')),
            ('hi', ('Ours: <b>a resume path and a new run state</b>', 'Nosso: <b>um caminho de retomada e um estado novo de run</b>'))]},
  {'ltr': 'D', 'name': ('Warn only', 'Só avisar'),
   'tag': ('first deploy', 'primeiro deploy'),
   'how': ('Emit the metric and the notification at the ceiling, and let the run continue.',
           'Emitir a métrica e a notificação no teto, e deixar o run continuar.'),
   'pros': [('No run is ever refused, so there are no false refusals to measure',
             'Nenhum run é recusado, então não há falsas recusas a medir'),
            ('It is the correct <em>first</em> stage of the rollout — see the recommendation',
             'É o <em>primeiro</em> estágio correto do rollout — veja a recomendação')],
   'cons': [('On its own it is not a ceiling. It is a smoke alarm wired to nothing',
             'Sozinho não é um teto. É um alarme de fumaça ligado em nada'),
            ('The unbounded-spend risk this task exists to close stays open',
             'O risco de gasto ilimitado que esta task existe para fechar continua aberto')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>the exposure stays open</b>', 'Nosso: <b>a exposição continua aberta</b>'))]},
 ],
 'rec': (
  '<p><strong>A, with D as the first deploy.</strong> Ship the counter, the metric and the notification with enforcement off. That is what makes the historical replay below possible against live traffic, and it is what <code>PLAN §3.2</code> asks for anyway: the new path lands disabled and is flipped in a separate deploy.</p>'
  '<p>The spec already requires both limits to <strong>emit a metric before they emit an error</strong>. A ceiling nobody can see being approached will be discovered by being hit.</p>'
  '<p><strong>B is the one to reject explicitly rather than leave on the table.</strong> Degrading is a silent product change made by an infrastructure control, and the person who notices is the one reading the output a week later.</p>',
  '<p><strong>A, com D como primeiro deploy.</strong> Entregue o contador, a métrica e a notificação com a imposição desligada. É isso que torna possível o replay histórico abaixo contra tráfego vivo, e é o que o <code>PLAN §3.2</code> pede de qualquer forma: o caminho novo entra desligado e é virado num deploy separado.</p>'
  '<p>A spec já exige que os dois limites <strong>emitam uma métrica antes de emitir um erro</strong>. Um teto que ninguém vê sendo alcançado será descoberto ao ser atingido.</p>'
  '<p><strong>B é a que deve ser rejeitada explicitamente, não deixada na mesa.</strong> Degradar é uma mudança silenciosa de produto feita por um controle de infraestrutura, e quem percebe é quem lê a saída uma semana depois.</p>'),
 'who': [('Product owns the behaviour', 'Produto decide o comportamento'),
         ('Engineering owns where the check sits', 'Engenharia decide onde a checagem fica')],
}

DEC_TENANCY = {
 'k': 'decision', 'id': 'S3-b', 'plan': 'D9', 'status': 'rec',
 'q': ('At the per-tenant concurrency cap, is the extra run queued or rejected?',
       'No teto de concorrência por tenant, o run excedente é enfileirado ou recusado?'),
 'intro': (
  'Note the <strong>deliberate contrast with <code>S7</code> and <code>D11</code></strong>, where a caller over the rate limit gets a <code>429</code>. '
  'The two look like the same question and are not. At admission, the caller may not be entitled to anything at all, and queueing an unbounded inbound flood only moves it. '
  'Here the caller is <strong>already entitled to the work</strong> — the organisation has runs to execute and the fleet is busy. '
  'Rejecting would turn a capacity limit into an error the customer sees.',
  'Note o <strong>contraste deliberado com a <code>S7</code> e a <code>D11</code></strong>, onde um chamador acima do rate limit recebe <code>429</code>. '
  'As duas parecem a mesma pergunta e não são. Na admissão, o chamador pode não ter direito a nada, e enfileirar uma enxurrada de entrada sem limite apenas a desloca. '
  'Aqui o chamador <strong>já tem direito ao trabalho</strong> — a organização tem runs para executar e a frota está ocupada. '
  'Recusar transformaria um limite de capacidade num erro que o cliente vê.'),
 'opts': [
  {'ltr': 'A', 'pick': True, 'name': ('Queue the excess', 'Enfileirar o excedente'),
   'tag': ('assumption', 'premissa'),
   'how': ('Runs over the cap wait at admission and start when a slot frees. The limit becomes latency, not failure.',
           'Runs acima do teto esperam na admissão e começam quando uma vaga abre. O limite vira latência, não falha.'),
   'pros': [('<strong>Latency is the correct trade for a background execution system</strong> — nobody is holding the phone',
             '<strong>Latência é a troca certa para um sistema de execução em background</strong> — ninguém está com o telefone na mão'),
            ('No client-side retry logic, and no run is lost', 'Nenhuma lógica de retry no cliente, e nenhum run é perdido'),
            ('The same submission behaves identically whether the fleet is busy or idle',
             'A mesma submissão se comporta igual com a frota ocupada ou ociosa')],
   'cons': [('A queue with no ceiling of its own is a way to hide a much larger problem',
             'Uma fila sem teto próprio é uma forma de esconder um problema bem maior'),
            ('“Queued” has to be visible, or a slow run and a waiting run look the same to the customer',
             '“Na fila” precisa ser visível, senão um run lento e um run esperando parecem a mesma coisa para o cliente')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('', ('Ours: <b>a queued state the UI must show</b>', 'Nosso: <b>um estado de fila que a UI precisa mostrar</b>'))]},
  {'ltr': 'B', 'name': ('Reject over the cap', 'Recusar acima do teto'),
   'how': ('The submission is refused and the customer is told to try again later, the way <code>S7</code> refuses at the rate limit.',
           'A submissão é recusada e o cliente é avisado para tentar depois, como a <code>S7</code> recusa no rate limit.'),
   'pros': [('Immediate, unambiguous feedback', 'Retorno imediato e sem ambiguidade'),
            ('No queue to size and no hidden backlog', 'Nenhuma fila para dimensionar e nenhum acúmulo escondido')],
   'cons': [('<strong>It turns a capacity limit into an error the customer sees</strong>, for work they are entitled to run',
             '<strong>Transforma um limite de capacidade num erro que o cliente vê</strong>, por um trabalho a que ele tem direito'),
            ('A scheduled or webhook-triggered run has nobody to retry it — the work is simply lost',
             'Um run disparado por agendamento ou webhook não tem quem tente de novo — o trabalho simplesmente se perde')],
   'cost': [('hi', ('Client effort: <b>handle a refusal, or lose the run</b>', 'Esforço do cliente: <b>tratar a recusa, ou perder o run</b>')),
            ('lo', ('Ours: <b>nothing to queue</b>', 'Nosso: <b>nada para enfileirar</b>'))]},
  {'ltr': 'C', 'no': True, 'name': ('A global cap only, with no per-tenant split', 'Só um teto global, sem divisão por tenant'),
   'tag': ('not viable', 'inviável'),
   'how': ('Bound the total number of concurrent runs across the fleet without asking whose they are.',
           'Limitar o total de runs concorrentes na frota sem perguntar de quem eles são.'),
   'pros': [('Protects the fleet with a single number', 'Protege a frota com um número só')],
   'cons': [('<strong>It is a fairness bug, not a capacity control</strong> — one organisation&#x27;s wide graph can hold the whole cap and starve every other tenant',
             '<strong>É um bug de justiça, não um controle de capacidade</strong> — o grafo largo de uma organização pode ocupar o teto inteiro e matar de fome todos os outros tenants'),
            ('The review is explicit that a global-only cap is too weak', 'A review é explícita: um teto só global é fraco demais')],
   'cost': [('lo', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>starvation, with a limit in place</b>', 'Nosso: <b>inanição, com um limite instalado</b>'))]},
 ],
 'rec': (
  '<p><strong>A, and make the waiting visible.</strong> Queueing is only the correct trade while the customer can tell a queued run from a stuck one — otherwise the fairness fix is delivered as a mystery.</p>'
  '<p><strong>Write the contrast with <code>S7</code> down where both are implemented.</strong> Two limits in the same codebase, one rejecting and one queueing, will look like an inconsistency to the next person unless the reason is next to the code: at admission the caller may not be entitled to anything, and here they already are.</p>',
  '<p><strong>A, e deixe a espera visível.</strong> Enfileirar só é a troca certa enquanto o cliente consegue distinguir um run na fila de um run travado — senão a correção de justiça é entregue como um mistério.</p>'
  '<p><strong>Registre o contraste com a <code>S7</code> onde os dois forem implementados.</strong> Dois limites no mesmo código, um recusando e outro enfileirando, vão parecer inconsistência para a próxima pessoa a menos que o motivo esteja ao lado do código: na admissão o chamador pode não ter direito a nada, e aqui ele já tem.</p>'),
 'who': [('Engineering', 'Engenharia'),
         ('Product confirms the visible queued state', 'Produto confirma o estado “na fila” visível')],
}

DEC_DEFAULT = {
 'k': 'decision', 'id': 'S3-c', 'status': 'rec',
 'q': ('Is the default ceiling a global constant, a column on the product, or a per-org value?',
       'O teto padrão é uma constante global, uma coluna no produto, ou um valor por organização?'),
 'intro': (
  'The spec&#x27;s assumption is that <strong>the default is derived from the plan, not from a global constant</strong> — a single number is wrong for both ends of the customer range. '
  'This is also the decision that determines whether the historical replay below has <em>one</em> threshold to test or one per plan.',
  'A premissa da spec é que <strong>o padrão vem do plano, não de uma constante global</strong> — um número só está errado nas duas pontas da faixa de clientes. '
  'É também a decisão que determina se o replay histórico abaixo tem <em>um</em> limiar a testar ou um por plano.'),
 'opts': [
  {'ltr': 'A', 'pick': True, 'name': ('A column on the product, overridable per org', 'Uma coluna no produto, sobrescrevível por organização'),
   'tag': ('assumption', 'premissa'),
   'how': ('The ceiling lives on the product with a conservative default, and an org-level override handles the exceptions a plan cannot express.',
           'O teto vive no produto com um padrão conservador, e uma sobrescrita por organização trata as exceções que um plano não consegue expressar.'),
   'pros': [('A single number is wrong for both ends of the customer range',
             'Um número só está errado nas duas pontas da faixa de clientes'),
            ('The override is the pressure valve that keeps a false refusal from becoming an escalation',
             'A sobrescrita é a válvula que impede uma falsa recusa de virar escalação'),
            ('It sits next to the entitlement checks that already read the product',
             'Fica ao lado das checagens de direito que já leem o produto')],
   'cons': [('A migration, and a value to backfill for every existing product',
             'Uma migração, e um valor para preencher em todo produto existente'),
            ('The measurement has to be replayed <strong>per plan</strong>, not once',
             'A medição precisa ser refeita <strong>por plano</strong>, não uma vez só')],
   'cost': [('', ('Client effort: <b>none, unless they need an override</b>', 'Esforço do cliente: <b>nenhum, salvo se precisar de sobrescrita</b>')),
            ('', ('Ours: <b>a column, a migration, a per-plan replay</b>', 'Nosso: <b>uma coluna, uma migração, um replay por plano</b>'))]},
  {'ltr': 'B', 'name': ('One global constant', 'Uma constante global'),
   'how': ('A single ceiling for everyone, read from the environment.',
           'Um único teto para todo mundo, lido do ambiente.'),
   'pros': [('One number to set, and one number to replay against history',
             'Um número para definir, e um número para replicar contra o histórico'),
            ('Ships without a migration', 'Entra sem migração')],
   'cons': [('Low enough for the smallest plan is far too low for the largest customer, and the reverse',
             'Baixo o bastante para o menor plano é baixo demais para o maior cliente, e vice-versa'),
            ('The first exception makes it a per-org value anyway — informally, and in code',
             'A primeira exceção já o torna um valor por organização — informalmente, e dentro do código')],
   'cost': [('hi', ('Client effort: <b>the wrong ceiling for most of them</b>', 'Esforço do cliente: <b>o teto errado para a maioria</b>')),
            ('lo', ('Ours: <b>one env var</b>', 'Nosso: <b>uma env var</b>'))]},
  {'ltr': 'C', 'name': ('Per-org only, with no plan default', 'Só por organização, sem padrão de plano'),
   'how': ('Every organisation carries its own ceiling, set when it is onboarded.',
           'Cada organização carrega seu próprio teto, definido no onboarding.'),
   'pros': [('Exactly right for every customer, by construction', 'Exatamente certo para cada cliente, por construção')],
   'cons': [('A new organisation with no value set has <strong>no ceiling</strong> — which is the failure mode being fixed',
             'Uma organização nova sem valor definido fica <strong>sem teto</strong> — que é justamente o modo de falha sendo corrigido'),
            ('It becomes a manual step in onboarding, and manual steps get skipped',
             'Vira um passo manual no onboarding, e passos manuais são pulados')],
   'cost': [('', ('Client effort: <b>none</b>', 'Esforço do cliente: <b>nenhum</b>')),
            ('hi', ('Ours: <b>an unbounded default by omission</b>', 'Nosso: <b>um padrão ilimitado por omissão</b>'))]},
 ],
 'rec': (
  '<p><strong>A.</strong> The important half is the default: a plan column with a conservative value means a new product is bounded on the day it is created, and the per-org override means a false refusal is a support action rather than a deploy.</p>'
  '<p><strong>Out of scope, and worth saying out loud:</strong> this task does not change pricing, plan structure, or how charges are computed. The ceiling reads numbers that already exist.</p>',
  '<p><strong>A.</strong> A metade importante é o padrão: uma coluna de plano com valor conservador significa que um produto novo já nasce limitado, e a sobrescrita por organização faz de uma falsa recusa uma ação de suporte em vez de um deploy.</p>'
  '<p><strong>Fora de escopo, e vale dizer em voz alta:</strong> esta task não muda preço, estrutura de plano, nem como as cobranças são calculadas. O teto lê números que já existem.</p>'),
 'who': [('Product owns the numbers', 'Produto decide os números'),
         ('Engineering owns the schema', 'Engenharia decide o schema')],
}

PARTS = [
{'n': '1',
 'title': ('The ceiling belongs to the chain, not to the run', 'O teto pertence à cadeia, não ao run'),
 'loc': 'TASK-S1 · D13',
 'purpose': ('Stop nesting from multiplying the ceiling, and build one accountant instead of two.',
             'Impedir que o aninhamento multiplique o teto, e construir um contador só em vez de dois.'),
 'body': (
  '<p><code>S1</code> settles that a sub-flow gets <strong>its own run identity plus a <code>parentRunId</code></strong>. That makes a per-run ceiling defeatable by nesting: five levels buy five ceilings, and <strong>recursion becomes the way around the limit</strong>.</p>'
  '<p>So the charge call has to <strong>resolve the chain root and account against it</strong>. This is cheap — the chain is already needed for depth, cycle and cancellation — but it has to be stated, because a ceiling that recursion can multiply is not a ceiling.</p>',
  '<p>A <code>S1</code> decide que um sub-fluxo ganha <strong>identidade de run própria mais um <code>parentRunId</code></strong>. Isso torna um teto por run derrotável por aninhamento: cinco níveis compram cinco tetos, e <strong>recursão vira o caminho para furar o limite</strong>.</p>'
  '<p>Então a chamada de cobrança precisa <strong>resolver a raiz da cadeia e contabilizar contra ela</strong>. Isso é barato — a cadeia já é necessária para profundidade, ciclo e cancelamento — mas precisa estar dito, porque um teto que a recursão pode multiplicar não é um teto.</p>'),
 'body2': (
  '<p><strong>One counter, two limits.</strong> <code>S4</code> needs the same chain-root accounting for its node-execution budget. Build it once and carry <strong>both units — cost and executions</strong> — rather than two accountants that resolve the chain independently and can disagree about where the root is.</p>',
  '<p><strong>Um contador, dois limites.</strong> A <code>S4</code> precisa da mesma contabilidade por raiz de cadeia para o orçamento de execuções de node. Construa uma vez e carregue <strong>as duas unidades — custo e execuções</strong> — em vez de dois contadores que resolvem a cadeia por conta própria e podem discordar sobre onde está a raiz.</p>'),
 'ba': (('The ceiling does not exist at all; and if it were added per run, every sub-flow call would reset it. Nesting would be the documented way to spend without limit.',
         'O teto simplesmente não existe; e se fosse adicionado por run, toda chamada de sub-fluxo o zeraria. Aninhar seria o jeito documentado de gastar sem limite.'),
        ('One counter, resolved at the chain root, carrying cost for this task and node executions for <code>S4</code>. Nesting adds to the total instead of starting a new one.',
         'Um contador, resolvido na raiz da cadeia, carregando custo para esta task e execuções de node para a <code>S4</code>. Aninhar soma ao total em vez de começar um novo.')),
 'callouts': [('decide', ('Where the root is resolved must be one answer', 'Onde a raiz é resolvida precisa ser uma resposta só'),
   ('<p>Two accountants that each walk the chain will eventually disagree about the root — on a retry, on a partially-written chain, or when a sub-flow is cancelled mid-way. <strong>One resolution, read by both limits.</strong></p>',
    '<p>Dois contadores que percorrem a cadeia cada um por si vão, cedo ou tarde, discordar sobre a raiz — num retry, numa cadeia gravada pela metade, ou quando um sub-fluxo é cancelado no meio. <strong>Uma resolução, lida pelos dois limites.</strong></p>'))]},
{'n': '2',
 'title': ('The check goes where the charge already is', 'A checagem vai onde a cobrança já está'),
 'loc': 'back/src/temporal/worker.controller.ts',
 'purpose': ('Put the ceiling in the one call that keeps working after the loop moves into the worker.',
             'Colocar o teto na única chamada que continua funcionando depois que o laço muda para o worker.'),
 'body': (
  '<p>The ceiling is checked <strong>at charge time</strong>, in the same call that already records the spend. Two reasons, and the second is the one that matters for this epic:</p>',
  '<p>O teto é checado <strong>no momento da cobrança</strong>, na mesma chamada que já registra o gasto. Dois motivos, e o segundo é o que importa para este épico:</p>'),
 'list': [
  ('It is the cheapest place — the number is already being computed and written',
   'É o lugar mais barato — o número já está sendo calculado e gravado'),
  ('<strong>It is the only place that keeps working once the worker owns the loop.</strong> A check inside the backend engine loop stops being on the path the moment <code>B4</code> moves that loop',
   '<strong>É o único lugar que continua funcionando quando o worker for dono do laço.</strong> Uma checagem dentro do laço da engine no backend sai do caminho no instante em que a <code>B4</code> mover esse laço'),
 ],
 'body2': (
  '<p>It also needs no new plumbing: <code>/worker/charge-tokens</code> already carries <code>execId</code>.</p>',
  '<p>E não precisa de encanamento novo: o <code>/worker/charge-tokens</code> já carrega o <code>execId</code>.</p>'),
 'ba': (('<code>assertCompletionCredits</code> answers “may this account run at all”, once, and charges land in <code>token_transactions</code> afterwards with nothing reading the total back.',
         'O <code>assertCompletionCredits</code> responde “esta conta pode rodar?”, uma vez, e as cobranças caem em <code>token_transactions</code> depois, sem nada lendo o total de volta.'),
        ('Every charge is checked against the chain total before it is recorded, and the abort carries <strong>the ceiling and the spend</strong>.',
         'Toda cobrança é checada contra o total da cadeia antes de ser registrada, e o aborto carrega <strong>o teto e o gasto</strong>.'))},
{'n': '3',
 'title': ('The tenancy cap, enforced where runs are admitted', 'O teto de tenancy, imposto onde os runs são admitidos'),
 'loc': 'back/src/jobs/apiV2Job/apiV2Job.processor.ts',
 'purpose': ('Keep one organisation from occupying the fleet once the remaining back-pressure is gone.',
             'Impedir que uma organização ocupe a frota quando a contrapressão que resta sumir.'),
 'body': (
  '<p>A cap on <strong>concurrent runs per organisation</strong>, enforced where runs are admitted, with excess runs <strong>queued rather than rejected</strong>.</p>'
  '<p>It is needed today. <strong>Corrected 2026-09-02:</strong> <code>@Process</code> declares <code>concurrency: parseConcurrency(AGENT_CONCURRENCY)</code>, default 5 per replica (PR #1902, 2026-08-21) — a cap on <em>how many</em> runs execute, not on <em>whose</em>, so one organisation can already hold every slot on every replica. <code>B5</code> removes the remaining back-pressure on purpose; after it, one organisation&#x27;s wide graph can occupy the whole worker fleet.</p>',
  '<p>Um teto de <strong>runs concorrentes por organização</strong>, imposto onde os runs são admitidos, com os excedentes <strong>enfileirados em vez de recusados</strong>.</p>'
  '<p>É necessário hoje. <strong>Corrigido em 2026-09-02:</strong> o <code>@Process</code> declara <code>concurrency: parseConcurrency(AGENT_CONCURRENCY)</code>, padrão 5 por réplica (PR #1902, 2026-08-21) — um teto de <em>quantos</em> runs executam, não de <em>quem</em>, então uma organização já pode ocupar toda vaga em toda réplica. A <code>B5</code> remove a contrapressão que resta de propósito; depois dela, o grafo largo de uma organização pode ocupar a frota inteira de workers.</p>'),
 'body2': (
  '<p><strong>Both limits emit a metric before they emit an error.</strong> A ceiling nobody can see being approached will be discovered by being hit — and the first person to discover it will be a customer.</p>',
  '<p><strong>Os dois limites emitem uma métrica antes de emitir um erro.</strong> Um teto que ninguém vê sendo alcançado será descoberto ao ser atingido — e quem descobre primeiro é um cliente.</p>'),
 'ba': (('No per-tenant cap exists anywhere in the flux or job paths. Five queued runs per backend replica (<code>AGENT_CONCURRENCY</code>) is the only thing standing in for one, and it does not know who the tenant is.',
         'Não existe teto por tenant em nenhum ponto dos caminhos de flux ou de jobs. Cinco runs enfileirados por réplica de backend (<code>AGENT_CONCURRENCY</code>) são a única coisa fazendo esse papel, e não sabem quem é o tenant.'),
        ('Concurrency is capped per organisation at admission, the excess waits instead of failing, and the approach to both limits is visible before either is reached.',
         'A concorrência é limitada por organização na admissão, o excedente espera em vez de falhar, e a aproximação dos dois limites é visível antes de qualquer um ser atingido.')),
 'callouts': [('mig', ('Out of scope', 'Fora de escopo'),
   ('<p>Changing pricing, plan structure, or how charges are computed. <strong>This task adds a ceiling over numbers that already exist.</strong></p>',
    '<p>Mudar preço, estrutura de plano, ou como as cobranças são calculadas. <strong>Esta task adiciona um teto sobre números que já existem.</strong></p>'))]},

{'n': '4',
 'title': ('Check the credit before the run, not on each node', 'Checar o crédito antes do run, não em cada node'),
 'loc': ('D19 · D20 · the pre-flight gate S1 already runs', 'D19 · D20 · o gate pré-execução que a S1 já roda'),
 'purpose': ('Refuse work that was never going to finish, before any of it is paid for.',
             'Recusar trabalho que nunca ia terminar, antes de qualquer parte dele ser paga.'),
 'body': (
  '<p><strong>The ceiling is not a property of a node evaluated at dispatch time.</strong> <code>S1</code> already runs a gate between building the DAG and '
  'starting to spend, and <code>S4</code> already validates the graph there; extend that gate to credit. Does this flow need credit, and is there enough — '
  'asked once, before anything runs.</p>'
  '<p>Refusing there turns a bill into an error message. It is also the reason the registry does <strong>not</strong> need a per-type <em>can this spend</em> '
  'flag: nothing has to be classified at dispatch time if the question is answered before dispatch begins.</p>',
  '<p><strong>O teto não é propriedade de um node avaliada na hora do dispatch.</strong> A <code>S1</code> já roda um gate entre montar o DAG e começar a gastar, '
  'e a <code>S4</code> já valida o grafo ali; estenda esse gate ao crédito. Este fluxo precisa de crédito, e há o suficiente — perguntado uma vez, antes de '
  'qualquer coisa rodar.</p>'
  '<p>Recusar ali transforma uma fatura numa mensagem de erro. É também o motivo de o registro <strong>não</strong> precisar de uma flag por tipo dizendo '
  '<em>isto gasta</em>: nada precisa ser classificado no dispatch se a pergunta é respondida antes de o dispatch começar.</p>'),
 'ba': (('Nothing is asked before the run. The first signal that a flow could never afford itself is the charge it already made.',
         'Nada é perguntado antes do run. O primeiro sinal de que um fluxo nunca poderia se pagar é a cobrança que ele já fez.'),
        ('The gate asks once, before spending. A flow with no credit fails with a message instead of a partial bill.',
         'O gate pergunta uma vez, antes de gastar. Um fluxo sem crédito falha com uma mensagem em vez de uma fatura parcial.')),
 'callouts': [('warn', ('It does not replace the charge-time ceiling', 'Não substitui o teto na hora da cobrança'),
   ('<p>A pre-flight check answers <strong>can this flow spend</strong>, never <strong>will it</strong> — the branch taken depends on data that does not exist '
    'until the run happens. That is the same argument <code>S4</code> makes for keeping a runtime budget, and it applies here unchanged. '
    'The two answer different questions and both are needed.</p>',
    '<p>Um check pré-execução responde <strong>este fluxo pode gastar</strong>, nunca <strong>vai gastar</strong> — o ramo tomado depende de dado que só existe '
    'quando o run acontece. É o mesmo argumento que a <code>S4</code> faz para manter um orçamento em runtime, e vale aqui sem mudança. '
    'Os dois respondem perguntas diferentes e os dois são necessários.</p>'))]},
]

VERIF = [
 (True, ('Negative control — spend', 'Controle negativo — gasto'),
  ('Build a flow that loops until it exceeds the ceiling, run it <strong>with the check disabled</strong>, and record what it costs. Then enable it and confirm the run aborts at the ceiling with the spend and the limit in the error. <strong>The first half of that test is the justification for the second.</strong>',
   'Monte um fluxo que roda em laço até estourar o teto, rode-o <strong>com a checagem desligada</strong>, e registre quanto custou. Depois ligue e confirme que o run aborta no teto com o gasto e o limite dentro do erro. <strong>A primeira metade desse teste é a justificativa da segunda.</strong>')),
 (True, ('Measure before refusing', 'Medir antes de recusar'),
  ('<strong>PLAN §3.3.2, and here it is load-bearing.</strong> Compute what the proposed ceiling would have done to <strong>every real run in the stored history</strong>. Any run that legitimately completed and would now be aborted is a false refusal, and that count must be <strong>zero</strong> before this ships. Report runs whose cost cannot be reconstructed as <em>unverifiable</em>, not as passing.',
   '<strong>PLAN §3.3.2, e aqui é estrutural.</strong> Calcule o que o teto proposto teria feito com <strong>cada run real do histórico armazenado</strong>. Todo run que terminou legitimamente e agora seria abortado é uma falsa recusa, e essa contagem precisa ser <strong>zero</strong> antes de entregar. Reporte runs cujo custo não pode ser reconstruído como <em>não verificável</em>, não como aprovado.')),
 (False, ('Tenancy — and the starvation it prevents', 'Tenancy — e a inanição que ela evita'),
  ('Two organisations, one submitting a wide graph: assert the second one&#x27;s run still starts within a <strong>bounded wait</strong>. Then remove the cap and watch it starve — <strong>that is the fairness bug</strong>, and seeing it is what makes the cap defensible.',
   'Duas organizações, uma submetendo um grafo largo: verifique que o run da segunda ainda começa dentro de uma <strong>espera limitada</strong>. Depois remova o teto e veja-a morrer de fome — <strong>esse é o bug de justiça</strong>, e vê-lo é o que torna o teto defensável.')),
 (False, ('The metric fires before the error does', 'A métrica dispara antes do erro'),
  ('Confirm that approaching each limit is <strong>observable before it is hit</strong> — not only that the refusal is logged. A ceiling whose only signal is the failure teaches nobody anything until it has already cost a run.',
   'Confirme que a aproximação de cada limite é <strong>observável antes de ser atingido</strong> — não só que a recusa é logada. Um teto cujo único sinal é a falha não ensina nada a ninguém até já ter custado um run.')),
]

DONE = ('A run cannot exceed its ceiling, <strong>no historical run would have been falsely aborted</strong>, one tenant cannot occupy the fleet, and both limits are <strong>observable before they are hit</strong>.',
        'Um run não pode ultrapassar seu teto, <strong>nenhum run histórico teria sido abortado por engano</strong>, um tenant não pode ocupar a frota, e os dois limites são <strong>observáveis antes de serem atingidos</strong>.')

FILES = [
 ('back/src/app-api/product/product.service.ts (assertCompletionCredits)', False),
 ('back/src/temporal/worker.controller.ts (/worker/charge-tokens)', False),
 ('back/src/app-api/token_transaction/', False),
 ('back/src/jobs/apiV2Job/apiV2Job.processor.ts (@Process concurrency · AGENT_CONCURRENCY)', False),
 ('product/plan schema + migration', True),
]

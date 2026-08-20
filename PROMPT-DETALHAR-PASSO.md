# Prompt canônico — detalhar passo do agent-execution-flow

Copie o bloco abaixo, troque `X.Y` pelo passo que você quer detalhar, e cole no chat.

---

```
detalhe o passo X.Y do diagrama seguindo EXATAMENTE o padrão dos arquivos
passo-1-3.html, passo-1-4.html e passo-1-5.html em C:\enhanced-ai\execucao-agente\.

## 1. Investigação (antes de escrever qualquer HTML)

1. Localize a caixa X.Y no C:\enhanced-ai\execucao-agente\index.html — pegue
   o file:line indicado (geralmente flux.service.ts:XXXX-YYYY).
2. Leia o código do bloco no repo C:\enhanced-ai\Flux-Prompt\.
3. Para CADA função chamada:
   - Localize a definição (arquivo:linha).
   - Leia a lógica inteira: parâmetros, early returns, cascatas, throws.
4. Para CADA service que essas funções chamem internamente, repita o passo 3.
   Continue descendo até chegar em queries diretas do TypeORM ou funções puras.
5. Se houver interfaces/types relevantes (ObjectOwner, RunLogDocument, etc.),
   também localize e leia.
6. NADA inventado. Só documente o que está no código real.

## 2. Criar o arquivo passo-X-Y.html

Local: C:\enhanced-ai\execucao-agente\passo-X-Y.html
Standalone (CSS embedded, sem deps externas). Base o CSS copiando integralmente
do passo-1-5.html — mantenha as MESMAS classes: .box (backend/db/worker/redis/
s3/external/decision/cross), .badge (migrated/legacy/mixed/step/ess/cross),
.fn-card, .cascade, .nested-flow, .aside (default/info/warn/helper),
.code-block, .field-table, .note, .page-nav, .page-header, .overview-mini,
.overview-chip.

### Estrutura obrigatória (nessa ordem):

1. Top nav — breadcrumb "📋 Execução de Agente › Passo X.Y — Detalhamento" +
   botão "← Voltar ao diagrama" apontando pra index.html#step-X-Y
2. Page header — ícone temático (📊/📦/🔍/🔐/⚡/etc.) + h1 "Passo X.Y — <nome>"
3. Page sub — file:line + descrição de 1-2 linhas do que o bloco faz
4. Note de contexto (opcional, se for cross-cutting/condicional/experimental)
5. Overview mini-chain — chips clicáveis A → B → C → D → E das funções
6. Um .fn-card por função (na ordem em que são chamadas)
7. Note de resumo — "o que sai de X.Y" (variáveis/estado que ficam prontas)
8. Note de migração — observações específicas pro plano de migração
9. Footer nav — botão de voltar

### Estrutura de cada .fn-card:

- Header preto com badge colorido (A=amarelo/B=azul/C=verde/D=roxo/E=vermelho)
  + <code> do nome da função + file:line
- .fn-signature (monospace, cinza) — só a assinatura
- .fn-purpose (azul) — o que faz e POR QUE
- .fn-body-cols (grid 2 colunas):
  - fn-main (esquerda): fluxo passo-a-passo. Use:
    * .box com cor apropriada (backend/db/decision/cross)
    * .arrow (↓) entre boxes
    * .cascade para chains de if/else numerados
    * .nested-flow (verde tracejado) quando a função chama outro service —
      documente o sub-fluxo DENTRO desse bloco
    * .code-block (fundo escuro) para interfaces, estruturas de objeto,
      snippets curtos
  - fn-asides (direita): 2-4 asides
    * .aside.info (azul) — "por que isso existe"
    * .aside (amarelo default) — origem dos dados, precedência, notas neutras
    * .aside.warn (vermelho) — footguns, bugs, edge cases, race conditions
    * .aside.helper (roxo) — definições técnicas auxiliares, constantes,
      env vars

## 3. Atualizar o node no index.html

Ache a caixa <div class="box XXX"> do passo X.Y e transforme em:

  <a href="passo-X-Y.html" class="box XXX clickable-node" id="step-X-Y">
    <span class="click-chevron" aria-hidden="true">›</span>
    <div class="box-title">... (mantém o conteúdo original) ...</div>
    <div class="box-desc">... (mantém) ...</div>
    <div class="box-file">... (mantém) ...</div>
    <div class="click-hint">
      <span class="click-hint-icon">🔍</span>
      <span>Clique para ver detalhamento (<pista curta>)</span>
      <span class="click-hint-arrow">→</span>
    </div>
  </a>

Mantenha a classe original da box (backend/cross/db/decision/etc.).

## 4. Regras invioláveis

- Cite arquivo:linha em cada .box do sub-fluxo (não só na função principal).
- Se uma função chama outro service, detalhe esse service também via
  nested-flow. Não pare no primeiro nível.
- Máximo 6 fn-cards por página. Se tiver mais funções, agrupe auxiliares
  em asides das principais ou em um card "utilitários" no fim.
- Todo texto explicativo em PT-BR.
- Sempre inclua a note de migração no fim, cobrindo:
  * O que precisa ir pro worker
  * Que dependências relacionais/state existem
  * Se é essencial ou pode ficar por último no plano
- NÃO invente comportamento. Se não está no código, não vai no HTML.
- NÃO copie texto genérico de outros passos. Cada passo tem contexto próprio.
- NÃO adicione hover effects na caixa clicável do index.html (o user já pediu
  pra tirar isso — mantém só .clickable-node com cursor pointer + hint pulsante).

## Entrega

- Confirme que o arquivo passo-X-Y.html foi criado.
- Confirme que o node X.Y no index.html virou clicável.
- Liste em 4-6 bullets o que foi documentado em cada card.
- NÃO faça commit, git ou build — só cria/edita arquivos e reporta.
```

---

## Como usar

Basta trocar `X.Y` pelo passo desejado.

**Exemplos:**

- `detalhe o passo 1.6 do diagrama seguindo EXATAMENTE o padrão dos arquivos passo-1-3.html, passo-1-4.html e passo-1-5.html...`
- `detalhe o passo 2.1 do diagrama...`
- `detalhe o passo 3.5 do diagrama...`

**Múltiplos passos de uma vez:**

- `detalhe os passos 1.6 e 1.7 do diagrama seguindo EXATAMENTE...`

Cada passo é entregue como um arquivo separado no padrão `passo-X-Y.html`, e o node correspondente no `index.html` fica clicável apontando pra ele.

---

## Convenções visuais (referência rápida)

### Cores das boxes (border-left)

| Classe          | Cor          | Uso                                    |
|-----------------|--------------|----------------------------------------|
| `.box.backend`  | Azul         | Lógica no NestJS                       |
| `.box.db`       | Amber        | Query no Postgres                      |
| `.box.worker`   | Verde        | Temporal worker                        |
| `.box.redis`    | Vermelho     | Redis pub/sub                          |
| `.box.s3`       | Roxo         | Storage S3                             |
| `.box.external` | Cinza        | API externa                            |
| `.box.decision` | Amarelo BG   | if/else, dispatch                      |
| `.box.cross`    | Roxo BG      | Observabilidade/logging/billing        |

### Badges

| Classe            | Uso                          |
|-------------------|------------------------------|
| `.badge.step`     | Numeração de passo (A1, B2)  |
| `.badge.ess`      | Essencial                    |
| `.badge.cross`    | Cross-cutting                |
| `.badge.mixed`    | Condicional                  |
| `.badge.migrated` | Já no worker                 |
| `.badge.legacy`   | Ainda inline no backend      |

### Cascades (resultados dos if/else)

| Classe    | Cor      | Semântica                     |
|-----------|----------|-------------------------------|
| `.pass`   | Verde    | Retorna sucesso / early return|
| `.deny`   | Vermelho | Bloqueia / retorna null       |
| `.call`   | Amarelo  | Chama outro service           |
| `.next`   | Roxo     | Continua na próxima etapa     |

### Asides (painéis laterais)

| Classe          | Cor       | Uso                                       |
|-----------------|-----------|-------------------------------------------|
| `.aside` (def)  | Amarelo   | Origem dos dados, precedência, neutro     |
| `.aside.info`   | Azul      | "Por que isso existe"                     |
| `.aside.warn`   | Vermelho  | Footguns, bugs, edge cases                |
| `.aside.helper` | Roxo      | Definições técnicas, constantes, env vars |

---

## Arquivos de referência

- `passo-1-3.html` — 4 funções, foca em cascatas de permissão
- `passo-1-4.html` — 5 funções, tem code block dark + field table
- `passo-1-5.html` — 5 funções, tem closure mutation callback + code block

# -*- coding: utf-8 -*-
TITLE = ('Decide <code>webTrends</code>', 'Decidir o <code>webTrends</code>')

GOAL = ('<code>webTrends</code> either executes in the worker or is retired, and <b>the decision is written down</b>.',
        'O <code>webTrends</code> passa a executar no worker ou é aposentado, e <b>a decisão fica registrada</b>.')

GLANCE = [
 ('dep', ('Depends on','Depende de'), ('A1 · A11','A1 · A11'),
  ('A1 is the registry the decision lands in; A11 gives every registry entry an execution class, so the type can be marked <code>worker</code>.',
   'A A1 é o registro onde a decisão entra; a A11 dá a cada entrada do registro uma classe de execução, para que o tipo possa ser marcado como <code>worker</code>.')),
 ('wave', ('Wave','Onda'), ('Wave 5','Onda 5'),
  ('It runs any time after A11, <strong>before B5 measures eligibility</strong>.',
   'Roda a qualquer momento depois da A11, <strong>antes de a B5 medir a elegibilidade</strong>.')),
 ('ship', ('Shape','Formato'), ('Measure, then one call','Medir, depois uma decisão'),
  ('Added on 2026-10-23 from the node coverage audit. <strong>One node type, nothing else.</strong>',
   'Adicionada em 2026-10-23 a partir da auditoria de cobertura de nodes. <strong>Um tipo de node, mais nada.</strong>')),
]

LEDE = (
 '<p><code>A6</code> listed <code>webTrends</code> among the front-driven types, in stage 1, and shipped without it. '
 '<strong>No decision was recorded.</strong> The front still calls <code>SerpService</code> directly from <code>WebTrends.tsx</code>, '
 'so the node never runs in a flow: it produces output only when a user clicks Run in the builder.</p>'
 '<p>This task closes that gap one way or the other. It measures real usage first, and then either migrates the type '
 'as <code>A6</code> migrated its siblings, or retires it from the canvas and the MCP metadata.</p>',
 '<p>A <code>A6</code> listou o <code>webTrends</code> entre os tipos só-front, no estágio 1, e foi entregue sem ele. '
 '<strong>Nenhuma decisão foi registrada.</strong> O front ainda chama o <code>SerpService</code> direto do <code>WebTrends.tsx</code>, '
 'então o node nunca roda num fluxo: só gera saída quando um usuário clica em Run no editor.</p>'
 '<p>Esta task fecha essa lacuna de um jeito ou de outro. Primeiro mede o uso real, e então migra o tipo '
 'como a <code>A6</code> migrou os irmãos dele, ou o aposenta do canvas e dos metadados do MCP.</p>')

PROSE = (
 'One call, and the spec does not make it in advance: <em>measure, then either migrate or retire</em>. '
 'The numbers from part 1 decide it.',
 'Uma decisão, e a spec não a toma de antemão: <em>medir, e então migrar ou aposentar</em>. '
 'Os números da parte 1 decidem.')

DEC_FATE = {
 'k':'decision','id':'A6b-a','status':'open','open':True, 'note':(('Where it stands (2026-10-23)', 'Onde está (23/10/2026)'), ('Open: the worker owner confirms migrate or retire before the work starts, with the usage numbers from the scope.', 'Em aberto: o responsável pelo worker confirma migrar ou aposentar antes de o trabalho começar, com os números de uso do escopo.')),
 'q':('Migrate <code>webTrends</code> to the worker, or retire it?',
      'Migrar o <code>webTrends</code> para o worker, ou aposentá-lo?'),
 'intro':(
  'Today the type sits in neither state: it is on the canvas and in the MCP metadata, but no engine executes it. '
  'The spec accepts either answer, as long as <strong>the decision and its numbers are recorded</strong> and the type ends up '
  '<code>worker</code> or removed.',
  'Hoje o tipo não está em nenhum dos dois estados: aparece no canvas e nos metadados do MCP, mas nenhum motor o executa. '
  'A spec aceita qualquer uma das respostas, desde que <strong>a decisão e seus números fiquem registrados</strong> e o tipo termine '
  'como <code>worker</code> ou removido.'),
 'opts':[
  {'ltr':'A','name':('Migrate it, as A6 migrated its siblings','Migrar, como a A6 migrou os irmãos dele'),
   'how':('Follow the same three-part scope as <code>A6</code>: an activity, engine dispatch for the first time, and the Run button routed through '
          '<code>POST /process/single-node</code> with the direct <code>SerpService</code> call deleted.',
          'Seguir o mesmo escopo em três partes da <code>A6</code>: uma activity, dispatch pelo motor pela primeira vez, e o botão Run roteado por '
          '<code>POST /process/single-node</code>, com a chamada direta ao <code>SerpService</code> apagada.'),
   'pros':[('<code>A6</code> counted it as almost free: the SerpApi client is already in the worker, inside <code>web-search</code>',
            'A <code>A6</code> o contou como quase de graça: o cliente SerpApi já está no worker, dentro de <code>web-search</code>'),
           ('Flows that hold it stop using whatever the last manual run left behind',
            'Os fluxos que o contêm deixam de usar o que o último run manual deixou para trás')],
   'cons':[('It is a behaviour change for any stored flow that holds the node: it starts producing fresh output',
            'É uma mudança de comportamento para todo fluxo armazenado que contém o node: ele passa a gerar saída nova')]},
  {'ltr':'B','name':('Retire it','Aposentar'),
   'how':('Remove the type from the canvas and from <code>node-type-metadata.ts</code>, so no new flow can hold it.',
          'Remover o tipo do canvas e do <code>node-type-metadata.ts</code>, para que nenhum fluxo novo possa contê-lo.'),
   'pros':[('No new activity, no new dispatch, nothing more to maintain',
            'Nenhuma activity nova, nenhum dispatch novo, nada a mais para manter')],
   'cons':[('Stored flows that hold it lose the node, so the measurement has to show how many there are first',
            'Fluxos armazenados que o contêm perdem o node, então a medição precisa mostrar primeiro quantos são')]},
 ],
}

PARTS = [
{'n':'1','title':('Measure real usage','Medir o uso real'),
 'loc':('stored flows','fluxos armazenados'),
 'purpose':('Count how many stored flows use <code>webTrends</code>, and find when one last ran.',
            'Contar quantos fluxos armazenados usam o <code>webTrends</code>, e descobrir quando um rodou pela última vez.'),
 'body':('<p>Both numbers go into the task file before the decision is taken. They are part of the definition of done, '
         'not background reading.</p>',
         '<p>Os dois números entram no arquivo da task antes de a decisão ser tomada. Fazem parte da definição de pronto, '
         'não são leitura de apoio.</p>')},

{'n':'2','title':('Carry out the decision','Executar a decisão'),
 'loc':'front/src/components/nodes/WebTrends.tsx',
 'purpose':('Either give the type worker execution, or remove it from the canvas and the MCP metadata.',
            'Dar execução no worker ao tipo, ou removê-lo do canvas e dos metadados do MCP.'),
 'body':('<p>If the call is to migrate, the work follows <code>A6</code> stage by stage. If it is to retire, '
         '<code>WebTrends.tsx</code> leaves the canvas and the entry leaves <code>back/src/app-mcp/node-types/node-type-metadata.ts</code>.</p>',
         '<p>Se a decisão for migrar, o trabalho segue a <code>A6</code> estágio por estágio. Se for aposentar, '
         'o <code>WebTrends.tsx</code> sai do canvas e a entrada sai do <code>back/src/app-mcp/node-types/node-type-metadata.ts</code>.</p>'),
 'ba':(('The front calls <code>SerpService</code> directly; the node runs only from the builder&#x27;s Run button.',
        'O front chama o <code>SerpService</code> direto; o node só roda pelo botão Run do editor.'),
       ('The type is <code>worker</code>, or it is gone from the canvas and the MCP metadata.',
        'O tipo é <code>worker</code>, ou sumiu do canvas e dos metadados do MCP.')),
 'callouts':[('mig',('Out of scope','Fora de escopo'),
   ('<p>Any other front-driven type.</p>',
    '<p>Qualquer outro tipo só-front.</p>'))]},

{'n':'3','title':('Record it','Registrar'),
 'loc':('the A1 registry','o registro da A1'),
 'purpose':('Write the decision and its numbers in the task file, and make the registry say the same thing.',
            'Escrever a decisão e seus números no arquivo da task, e fazer o registro dizer a mesma coisa.'),
 'body':('<p>The gap exists because <code>A6</code> shipped without a recorded decision. This part is what keeps it from happening twice.</p>',
         '<p>A lacuna existe porque a <code>A6</code> foi entregue sem uma decisão registrada. Esta parte é o que impede que isso se repita.</p>')},
]

VERIF = [
 (True, ('The numbers are recorded','Os números estão registrados'),
  ('The task file holds how many stored flows use <code>webTrends</code> and when one last ran, next to the decision.',
   'O arquivo da task traz quantos fluxos armazenados usam o <code>webTrends</code> e quando um rodou pela última vez, junto da decisão.')),
 (True, ('The type has one clear state','O tipo tem um estado claro'),
  ('The A1 registry marks <code>webTrends</code> as <code>worker</code>, or the type is gone from the canvas and from <code>node-type-metadata.ts</code>.',
   'O registro da A1 marca o <code>webTrends</code> como <code>worker</code>, ou o tipo sumiu do canvas e do <code>node-type-metadata.ts</code>.')),
 (False, ('If migrated, no direct call remains','Se migrado, não sobra chamada direta'),
  ('<code>WebTrends.tsx</code> no longer calls <code>SerpService</code> itself; its Run button goes through <code>POST /process/single-node</code>.',
   'O <code>WebTrends.tsx</code> não chama mais o <code>SerpService</code> por conta própria; o botão Run dele passa por <code>POST /process/single-node</code>.')),
]

DONE = ('The decision and its numbers are recorded in the task file, and the type is <code>worker</code> or removed.',
        'A decisão e seus números estão registrados no arquivo da task, e o tipo é <code>worker</code> ou foi removido.')

FILES = [('front/src/components/nodes/WebTrends.tsx', False),
         ('the A1 registry', False),
         ('back/src/app-mcp/node-types/node-type-metadata.ts', False)]

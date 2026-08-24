# -*- coding: utf-8 -*-
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tasklib, order, c_s7, d_s7, w0_s1, w0_rest, w0_c3
from TITLES_ALL import TITLES

DEC_LEAD = lambda n: {'k':'prose','t':(
  'These are the calls that have to be made before the code is written. Each one opens to the options considered, '
  'what each costs the customer and costs us, and the option we would pick.',
  'Estas são as decisões que precisam ser tomadas antes de o código ser escrito. Cada uma abre com as opções consideradas, '
  'quanto cada uma custa ao cliente e a nós, e a opção que escolheríamos.')}
DEC_LABEL = ('The decisions this task needs','As decisões que esta task precisa')
WORK_LABEL = ('What the task does','O que a task faz')

def table_block(t):
    return {'k':'table','head':t['head'],'rows':t['rows']}

# ---------- S7 (rebuild for consistent nav) ----------
rows=[]
for route, keyed, apill, atxt, lpill, ltxt, note in c_s7.ENTRIES:
    rows.append([{'t':route,'mono':True} if isinstance(route,str) else {'t':route}, keyed,
                 {'t':atxt,'pill':apill}, {'t':ltxt,'pill':lpill}, note])
S7 = {'code':'S7','vnum':'4','title':c_s7.T['title'],'goal':c_s7.T['goal'],
 'glance':c_s7.GLANCE,'lede':c_s7.T['lede'],
 'blocks':[{'k':'label','n':'1','t':('The four ways in, as they stand today','As quatro entradas, como estão hoje')},
   {'k':'table','head':[('Entry point','Entrada'),('Identifies the caller','Identifica quem chama'),
     ('Authentication','Autenticação'),('Rate limit','Rate limit'),('What that means','O que isso significa')],'rows':rows},
   {'k':'label','n':'2','t':DEC_LABEL}, DEC_LEAD(4),
   d_s7.DEC_TRANSPORT, d_s7.DEC_PUBLIC, d_s7.DEC_EMAIL, d_s7.DEC_ADMISSION,
   {'k':'label','n':'3','t':('What the task does, in three parts','O que a task faz, em três partes')}]
   + [{'k':'part', **p} for p in c_s7.PARTS],
 'verif':c_s7.VERIF,'done':c_s7.T['done'],'files':c_s7.FILES}

# ---------- S1 ----------
S1 = {'code':'S1','vnum':'3','title':w0_s1.TITLE,'goal':w0_s1.GOAL,
 'glance':w0_s1.GLANCE,'lede':w0_s1.LEDE,
 'blocks':[{'k':'label','n':'1','t':DEC_LABEL}, DEC_LEAD(3),
   w0_s1.DEC_IDENTITY, w0_s1.DEC_CYCLE, w0_s1.DEC_DEPTH,
   {'k':'label','n':'2','t':WORK_LABEL}]
   + [{'k':'part', **p} for p in w0_s1.PARTS],
 'verif':w0_s1.VERIF,'done':w0_s1.DONE,'files':w0_s1.FILES}

# ---------- S4 ----------
s4 = w0_rest.S4
S4 = {'code':'S4','vnum':'4','title':s4['TITLE'],'goal':s4['GOAL'],
 'glance':s4['GLANCE'],'lede':s4['LEDE'],
 'blocks':[{'k':'label','n':'1','t':('Three limits, and why none of them subsumes the others','Três limites, e por que nenhum engloba os outros')},
   table_block(s4['TABLE']),
   {'k':'label','n':'2','t':DEC_LABEL}, DEC_LEAD(1), w0_rest.S4_DEC,
   {'k':'label','n':'3','t':WORK_LABEL}]
   + [{'k':'part', **p} for p in s4['PARTS']],
 'verif':s4['VERIF'],'done':s4['DONE'],'files':s4['FILES']}

# ---------- S5 ----------
s5 = w0_rest.S5
S5 = {'code':'S5','vnum':'3','title':s5['TITLE'],'goal':s5['GOAL'],
 'glance':s5['GLANCE'],'lede':s5['LEDE'],
 'blocks':[{'k':'label','n':'1','t':DEC_LABEL}, DEC_LEAD(1), w0_rest.S5_DEC,
   {'k':'label','n':'2','t':WORK_LABEL}]
   + [{'k':'part', **p} for p in s5['PARTS']],
 'verif':s5['VERIF'],'done':s5['DONE'],'files':s5['FILES']}

# ---------- C3 ----------
c3 = w0_c3.C3
C3 = {'code':'C3','vnum':'4','title':c3['TITLE'],'goal':c3['GOAL'],
 'glance':c3['GLANCE'],'lede':c3['LEDE'],
 'blocks':[{'k':'label','n':'1','t':('The six defects, and what each one blocks','Os seis defeitos, e o que cada um bloqueia')},
   table_block(c3['TABLE']),
   {'k':'label','n':'2','t':DEC_LABEL}, DEC_LEAD(1), w0_c3.C3_DEC,
   {'k':'label','n':'3','t':WORK_LABEL}]
   + [{'k':'part', **p} for p in c3['PARTS']],
 'verif':c3['VERIF'],'done':c3['DONE'],'files':c3['FILES']}

for T in (S7, S1, S4, S5, C3):
    T.update(order.nav(T['code'], TITLES))
    print(tasklib.write(T))

# -*- coding: utf-8 -*-
import os as _os
_GEN = _os.path.dirname(_os.path.abspath(__file__))
_EPIC = _os.path.dirname(_GEN)

import sys
sys.path.insert(0, _GEN)
import tasklib, order
from TITLES_ALL import TITLES
import w1_s2, w1_s3, w1_s8, w1_e3

DEC_INTRO = {
 'S2': ('Two calls have to be made before the config change means anything, and both are recorded under <code>PLAN D8</code>. '
        'Each one below opens to the options considered, what each costs the customer and costs us, and the option we would pick.',
        'Duas decisões precisam ser tomadas antes de a mudança de config significar algo, e as duas ficam registradas sob o <code>PLAN D8</code>. '
        'Cada uma abaixo abre com as opções consideradas, quanto cada uma custa ao cliente e a nós, e a opção que escolheríamos.'),
 'S3': ('Three calls have to be made before this ceiling can be written, and two of them are visible to the customer. '
        'Each one below opens to the options considered, what each costs the customer and costs us, and the option we would pick.',
        'Três decisões precisam ser tomadas antes de este teto poder ser escrito, e duas delas são visíveis para o cliente. '
        'Cada uma abaixo abre com as opções consideradas, quanto cada uma custa ao cliente e a nós, e a opção que escolheríamos.'),
 'S8': ('Two calls have to be made, and neither is decidable from this repository alone — one needs the database&#x27;s opinion, the other needs infrastructure&#x27;s. '
        'Each one below opens to the options considered, what each costs the customer and costs us, and the option we would pick.',
        'Duas decisões precisam ser tomadas, e nenhuma é decidível só a partir deste repositório — uma precisa da opinião do banco, a outra da infraestrutura. '
        'Cada uma abaixo abre com as opções consideradas, quanto cada uma custa ao cliente e a nós, e a opção que escolheríamos.'),
 'E3': ('Only one call is open here — the rest of the task is settled by the spec. It is also the one that decides whether the transport change delivers what it was bought for. '
        'It opens to the options considered, what each costs the customer and costs us, and the option we would pick.',
        'Só uma decisão está aberta aqui — o resto da task já está resolvido pela spec. É também a que define se a troca de transporte entrega aquilo pelo que foi comprada. '
        'Ela abre com as opções consideradas, quanto cada uma custa ao cliente e a nós, e a opção que escolheríamos.'),
}

SEC1 = {
 'S2': ('The arithmetic nobody has written down', 'A conta que ninguém escreveu'),
 'S3': ('What protects spend today, and what it actually protects', 'O que protege o gasto hoje, e o que ele de fato protege'),
 'S8': ('What a second replica multiplies', 'O que uma segunda réplica multiplica'),
 'E3': ('The two paths, as they stand today', 'Os dois caminhos, como estão hoje'),
}

SEC3 = {
 'S2': ('What the task does, in three parts', 'O que a task faz, em três partes'),
 'S3': ('What the task does, in four parts', 'O que a task faz, em quatro partes'),
 'S8': ('What the task does, in four parts', 'O que a task faz, em quatro partes'),
 'E3': ('What the task does, in three parts', 'O que a task faz, em três partes'),
}

MODULES = {'S2': w1_s2, 'S3': w1_s3, 'S8': w1_s8, 'E3': w1_e3}
DECISIONS = {
 'S2': [w1_s2.DEC_MAX, w1_s2.DEC_PROXY],
 'S3': [w1_s3.DEC_CEILING, w1_s3.DEC_TENANCY, w1_s3.DEC_DEFAULT],
 'S8': [w1_s8.DEC_CRON, w1_s8.DEC_REDIS],
 'E3': [w1_e3.DEC_FANOUT],
}


def build(code):
    m = MODULES[code]
    blocks = [
        {'k': 'label', 'n': '1', 't': SEC1[code]},
        m.TABLE,
        {'k': 'label', 'n': '2', 't': ('The decisions this task needs', 'As decisões que esta task precisa')},
        {'k': 'prose', 't': DEC_INTRO[code]},
    ]
    blocks.extend(DECISIONS[code])
    blocks.append({'k': 'label', 'n': '3', 't': SEC3[code]})
    for p in m.PARTS:
        blocks.append({'k': 'part', **p})

    TASK = {
        'code': code,
        'vnum': '4',
        'title': m.TITLE,
        'goal': m.GOAL,
        'glance': m.GLANCE,
        'lede': m.LEDE,
        'blocks': blocks,
        'verif': m.VERIF,
        'done': m.DONE,
        'files': m.FILES,
    }
    TASK.update(order.nav(code, TITLES))
    return tasklib.write(TASK)


if __name__ == '__main__':
    for c in ['S2', 'S3', 'S8', 'E3']:
        print(build(c))

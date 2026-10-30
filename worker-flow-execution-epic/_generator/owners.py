# -*- coding: utf-8 -*-
"""Who owns each task, the one source for the owner line on the task board.

Synced from ClickUp on 2026-10-30, read only. The owner is the task's assignees,
kept to the two people who run this epic and written in the order of PEOPLE. When
a task had no assignee, the signal column says which other ClickUp field was used.

    python3 _generator/sync_owners.py           # write the board's owner lines from this table
    python3 _generator/sync_owners.py --check   # report, write nothing; exit 1 on drift

reconcile_facts.py fails when a board card shows a different owner.  A card for a
part of a task (S7) is keyed by the code and the part label shown on the card.
"""

PEOPLE = ('Alexandre Paravani', 'Yago Vela')
A, Y = PEOPLE
AY = (A, Y)

# key: (ClickUp task id, owners, ClickUp signal)
OWNERS = {
    'S7 parts 1 & 3': ('868m0vg62', (Y,), 'assignees'),
    'S1': ('868m0vfyz', (Y,), 'assignees'),
    'S4': ('868m0vfby', (A,), 'assignees'),
    'S5': ('868m0vfhf', (A,), 'assignees'),
    'C3': ('868m0vfrz', (Y,), 'assignees'),
    'S2': ('868m0vjwk', (A,), 'assignees'),
    'S3': ('868m0vk05', (A,), 'assignees'),
    'S7 part 2': ('868m0vkcj', (A,), 'assignees'),
    'S7 follow-up': ('868m48692', (A,), 'assignees'),
    'S8': ('868m0vkve', (A,), 'assignees'),
    'E3': ('868m0vk4t', (Y,), 'assignees'),
    'A1': ('868m0vjxy', (A,), 'assignees'),
    'A1B': ('868m7k2ft', (A,), 'assignees'),
    'A1C': ('868m7y117', (A,), 'creator (no assignee)'),
    'D2': ('868m0vk3q', (Y,), 'assignees'),
    'A2': ('868m0vkgj', (A,), 'assignees'),
    'A3': ('868m0vkya', (Y,), 'assignees'),
    'A4': ('868m0vk9r', (Y,), 'assignees'),
    'A5': ('868m0vkt4', (A,), 'assignees'),
    'A5B': ('868m9zfba', (A,), 'assignees'),
    'A6': ('868m0vm7q', (Y,), 'assignees'),
    'S6': ('868m0vmhg', (Y,), 'assignees'),
    'A8': ('868m0vmpz', (Y,), 'assignees'),
    'A9': ('868m0vmux', (A,), 'assignees'),
    'A10': ('868m7kbf0', (A,), 'assignees'),
    'D1': ('868m0vmyc', AY, 'assignees'),
    'B1': ('868m0vmun', (A,), 'assignees'),
    'B2': ('868m0vmw3', (A,), 'assignees'),
    'B3': ('868m0vmy4', (A,), 'assignees'),
    'B3B': ('868mfkzgh', (A,), 'assignees'),
    'B4': ('868m0vn26', (Y,), 'assignees'),
    'E1': ('868m0vn4x', (A,), 'assignees'),
    'E5': ('868m6ue54', (A,), 'assignees'),
    'E2': ('868m0vn6y', (A,), 'assignees'),
    'S6B': ('868mn5gb5', (Y,), 'assignees'),
    'A11': ('868mn64he', (A,), 'assignees'),
    'A13': ('868mn64j4', AY, 'assignees'),
    'A7': ('868m0vmqu', AY, 'assignees'),
    'A14': ('868mn64jc', AY, 'assignees'),
    'A6B': ('868mn64jq', AY, 'assignees'),
    'B5': ('868m0vmkd', AY, 'assignees'),
    'B6': ('868m0vmvr', AY, 'assignees'),
    'B7': ('868m0vn0x', (Y,), 'assignees'),
    'E4': ('868m6udyc', AY, 'assignees'),
    'C1': ('868m0vm8g', AY, 'assignees'),
    'C2': ('868m0vmj6', AY, 'assignees'),
}


def label(key):
    return ' · '.join(p for p in PEOPLE if p in OWNERS[key][1])

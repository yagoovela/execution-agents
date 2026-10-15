#!/usr/bin/env python3
"""Measure how long each finished wave took, from ClickUp, and write it on status-tarefas.html.

Rule (the one waves 0 to 3 were measured with):
  - A wave counts its "[Refactor] Wave N · ..." subtasks only; [Bug] and [Fix] cards are left out.
  - Start: the earliest day any of those subtasks entered "in progress" (or "in dev", if earlier).
  - Passed QA: the latest day a subtask entered "passed qa"; a subtask that never did counts its deploy day.
  - Deploy: the latest day a subtask entered "deployed on live". This is the figure the chip shows.
  - Days are counted inclusively in America/Sao_Paulo time (UTC-3); working days leave out weekends.
  - A wave is finished when every counted subtask is "deployed on live". Unfinished waves are reported, never written.
  - The chip's maximum is the top of the wave's estimate chip ("5–8d est." -> 8), or the maximum already written.

Usage:
  CLICKUP_API_TOKEN=pk_... python3 _assets/wave_delivery.py           # report only
  CLICKUP_API_TOKEN=pk_... python3 _assets/wave_delivery.py --write   # also update the chips of finished waves
  python3 _assets/wave_delivery.py --from-json data.json [--write]    # offline, from a saved fetch (--save-json)
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

WAVE_PARENTS = {
    0: '868m0vf5a',
    1: '868m0vjqp',
    2: '868m0vjtb',
    3: '868m0vk0p',
    4: '868m0vmqf',
    5: '868m0vm9n',
    6: '868m0vkmy',
}
API = os.environ.get('CLICKUP_API_BASE', 'https://api.clickup.com/api/v2')
TZ = timezone(timedelta(hours=-3))
BOARD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'status-tarefas.html')
DEPLOYED = 'deployed on live'


def get(path, token):
    req = urllib.request.Request(API + path, headers={'Authorization': token})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        raise SystemExit('ClickUp answered %d for %s — check CLICKUP_API_TOKEN.' % (err.code, path.split('?')[0]))


def fetch(token):
    data = {}
    for wave, parent in WAVE_PARENTS.items():
        task = get('/task/%s?include_subtasks=true' % parent, token)
        subs = [{'id': s['id'], 'name': s['name']} for s in task.get('subtasks') or []]
        ids = [s['id'] for s in subs]
        history = {}
        for i in range(0, len(ids), 100):
            query = urllib.parse.urlencode([('task_ids', t) for t in ids[i:i + 100]])
            history.update(get('/task/bulk_time_in_status/task_ids?' + query, token))
        data[str(wave)] = {'subtasks': subs, 'history': history}
    return data


def since(entry):
    value = entry.get('since') or (entry.get('total_time') or {}).get('since')
    return int(value) if value else None


def entered(history, *statuses):
    days = []
    for entry in history.get('status_history') or []:
        if entry.get('status', '').lower() in statuses and since(entry):
            days.append(datetime.fromtimestamp(since(entry) / 1000, TZ).date())
    return min(days) if days else None


def span(start, end):
    calendar = (end - start).days + 1
    working = sum(1 for i in range(calendar) if (start + timedelta(i)).weekday() < 5)
    return working, calendar


def measure(wave, block):
    label = '[refactor] wave %d ' % wave
    tasks = [s for s in block['subtasks'] if s['name'].lower().startswith(label)]
    if not tasks:
        return {'wave': wave, 'finished': False, 'reason': 'no subtasks'}
    pending = [s['name'] for s in tasks
               if (block['history'].get(s['id'], {}).get('current_status') or {}).get('status', '').lower() != DEPLOYED]
    if pending:
        return {'wave': wave, 'finished': False, 'reason': '%d of %d not deployed' % (len(pending), len(tasks))}
    starts, qas, deploys = [], [], []
    for s in tasks:
        h = block['history'][s['id']]
        deploy = entered(h, DEPLOYED)
        starts.append(entered(h, 'in progress', 'in dev') or deploy)
        qas.append(entered(h, 'passed qa') or deploy)
        deploys.append(deploy)
    start, qa, deploy = min(starts), max(qas), max(deploys)
    return {'wave': wave, 'finished': True, 'tasks': len(tasks), 'start': start,
            'qa': qa, 'qa_span': span(start, qa), 'deploy': deploy, 'deploy_span': span(start, deploy)}


ESTIMATE = re.compile(r'<span class="chip planned" title="Engineering estimate — pre-planning">'
                      r'<strong>\d+</strong>–<strong>(\d+)</strong>d <span data-en="est\." data-pt="est\.">est\.</span></span>')
ACTUAL = re.compile(r'<span class="chip done" title="Actual delivery vs\. estimate"><strong>\d+</strong>d / '
                    r'<strong>(\d+)</strong>d <span data-en="max" data-pt="máx">max</span></span>')


def chip(days, maximum):
    return ('<span class="chip done" title="Actual delivery vs. estimate"><strong>%d</strong>d / '
            '<strong>%d</strong>d <span data-en="max" data-pt="máx">max</span></span>' % (days, maximum))


def write_chip(html, wave, days):
    head = '<!-- ================ WAVE %d ================ -->' % wave
    start = html.find(head)
    if start < 0:
        raise SystemExit('wave %d not found on the board' % wave)
    end = html.find('<!-- ================ WAVE', start + len(head))
    end = len(html) if end < 0 else end
    block = html[start:end]
    match = ESTIMATE.search(block) or ACTUAL.search(block)
    if not match:
        raise SystemExit('wave %d has neither an estimate chip nor an actual chip' % wave)
    block = block[:match.start()] + chip(days, int(match.group(1))) + block[match.end():]
    return html[:start] + block + html[end:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--write', action='store_true', help='update the chips of finished waves on status-tarefas.html')
    ap.add_argument('--from-json', help='read a saved fetch instead of calling ClickUp')
    ap.add_argument('--save-json', help='save the ClickUp fetch to this file')
    ap.add_argument('--board', default=BOARD)
    args = ap.parse_args()

    if args.from_json:
        data = json.load(open(args.from_json, encoding='utf-8'))
    else:
        token = os.environ.get('CLICKUP_API_TOKEN')
        if not token:
            raise SystemExit('Set CLICKUP_API_TOKEN (ClickUp > Settings > Apps > API Token), or pass --from-json.')
        data = fetch(token)
        if args.save_json:
            json.dump(data, open(args.save_json, 'w', encoding='utf-8'), indent=1)

    html = open(args.board, encoding='utf-8').read()
    for wave in sorted(int(w) for w in data):
        r = measure(wave, data[str(wave)])
        if not r['finished']:
            print('Wave %d: not finished (%s)' % (wave, r['reason']))
            continue
        print('Wave %d: %d tasks, start %s | passed QA %s, %d working days (%d calendar) | '
              'deployed %s, %d working days (%d calendar)'
              % (wave, r['tasks'], r['start'], r['qa'], *r['qa_span'], r['deploy'], *r['deploy_span']))
        if args.write:
            html = write_chip(html, wave, r['deploy_span'][0])
    if args.write:
        open(args.board, 'w', encoding='utf-8').write(html)
        print('Updated %s' % args.board)


if __name__ == '__main__':
    sys.exit(main())

import json, os, re, sys, csv
S = sys.argv[1]
cs = json.load(open(os.path.join(S, 'parsed_all.json')))
TERM = 'Spring 2027'
EXCLUDE = {'B8700', 'B9899'}  # Exchange Program, PhD Internship: not Course Match electives
TERM_ORDER = ['Fall 2022','Spring 2023','Summer 2023','Fall 2023','Spring 2024','Summer 2024','Fall 2024',
              'Spring 2025','Summer 2025','Fall 2025','Spring 2026','Summer 2026','Fall 2026','Spring 2027']
is_mba = lambda s: s['part_of_term'].startswith('MBA')

def tmin(t):
    m = re.match(r'(\d+):(\d+)\s*(AM|PM)', t.strip())
    if not m: return None
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if ap == 'PM' and h != 12: h += 12
    if ap == 'AM' and h == 12: h = 0
    return h * 60 + mi

def span(dates):
    p = [x.strip() for x in dates.split('-')]
    return (p[0], p[-1]) if p and p[0] else ('', '')

def days_between(a, b):
    import datetime
    try:
        f = lambda x: datetime.datetime.strptime(x, '%m/%d/%Y')
        return (f(b) - f(a)).days
    except Exception:
        return 0

def part_label(pot):
    x = pot.replace('MBA - ', '').strip()
    if x.startswith('Block Week'): return 'Block Week (Jan 19–23)'
    if x.startswith('Half Block Week'):
        m = re.search(r'Jan \d+ - \d+', x)
        return 'Half Block Week (' + (m.group(0).replace(' - ', '–') if m else 'Jan') + ')'
    return {'LEAD': 'LEAD (core)'}.get(x, x)

def intro_of(desc, n=2):
    flat = re.sub(r'\s+', ' ', desc).strip()
    sents = re.split(r'(?<=[.!?])\s+(?=[A-Z“"(])', flat)
    out = ' '.join(sents[:n])
    if len(out) > 420: out = out[:400].rsplit(' ', 1)[0] + '…'
    return out

out = []
for c in cs:
    if c['id'] in EXCLUDE: continue
    s27 = [s for s in c['sections'] if s['term'] == TERM and is_mba(s)]
    if not s27: continue
    secs = []
    for s in s27:
        rows = s['schedule']
        prim = max(rows, key=lambda r: (days_between(*span(r['dates'])), len(r['days']))) if rows else {}
        extra = [r for r in rows if r is not prim]
        a, b = span(prim.get('dates', ''))
        t = prim.get('time', '')
        st, en = (t.split(' - ') + [''])[:2] if t else ('', '')
        secs.append({
            'sec': s['section'], 'profs': s['faculty'], 'profLinks': s['faculty_links'],
            'part': part_label(s['part_of_term']), 'days': prim.get('days', ''), 'time': t,
            'start': tmin(st) if st else None, 'end': tmin(en) if en else None,
            'from': a, 'to': b, 'room': prim.get('room', ''),
            'extra': [{'days': r['days'], 'dates': r['dates'], 'time': r['time'], 'room': r['room']} for r in extra],
            'syllabus': s['syllabus'], 'notes': s['notes'],
        })
    hist = {}
    for s in c['sections']:
        if s['term'] == TERM or not is_mba(s): continue
        hist.setdefault(s['term'], set()).update(s['faculty'])
    hist_list = [{'term': t, 'profs': sorted(hist[t])} for t in TERM_ORDER if t in hist]
    profs27 = sorted({p for s in secs for p in s['profs']})
    sp26 = hist.get('Spring 2026', set())
    reqs = ['%s — %s: %s' % (r['type'], r['rule'], '; '.join(r['items'])) for r in c['requisites'] if r['type']]
    out.append({
        'id': c['id'], 'code': c['code'], 'title': c['title'], 'type': c['attribute'], 'credits': float(c['credits'] or 0),
        'division': c['division'], 'pathways': c['pathways'], 'intro': intro_of(c['description']),
        'desc': c['description'], 'reqs': reqs, 'url': c['url'], 'sections': secs,
        'history': hist_list, 'termsOffered': len(hist_list),
        'newCourse': len(hist_list) == 0,
        'inSpring26': bool(sp26),
        'profChange': bool(sp26) and not (set(profs27) & sp26),
        'tbaProf': all(p == 'New Adjunct' for p in profs27),
    })
out.sort(key=lambda x: (x['type'] != 'Elective', x['id']))
json.dump(out, open(os.path.join(S, 'courses_s27.json'), 'w'), ensure_ascii=False)
with open(os.path.join(S, 'courses_s27_sections.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Course ID','Section','Title','Core/Elective','Credits','Part of term','Days','Time','Dates','Room','Professor(s)','Division','Pathways','Prerequisites','Offered Spring 2026','Spring 2026 professor(s)','Terms offered since Fall 2022','Syllabus','Course page','Intro'])
    for c in out:
        sp = next((h['profs'] for h in c['history'] if h['term']=='Spring 2026'), [])
        for s in c['sections']:
            w.writerow([c['id'], s['sec'], c['title'], c['type'], c['credits'], s['part'], s['days'], s['time'],
                        (s['from'] + ' – ' + s['to']) if s['to'] != s['from'] else s['from'], s['room'], ', '.join(s['profs']), c['division'],
                        ', '.join(c['pathways']), ' | '.join(c['reqs']), 'Yes' if c['inSpring26'] else 'No', ', '.join(sp),
                        c['termsOffered'], s['syllabus'], c['url'], c['intro']])
import collections
print(len(out), 'courses', sum(len(c['sections']) for c in out), 'sections')
print(collections.Counter(s['part'] for c in out for s in c['sections']))
print('new', sum(c['newCourse'] for c in out), 'profChange', sum(c['profChange'] for c in out), 'tba', sum(c['tbaProf'] for c in out), 'inSp26', sum(c['inSpring26'] for c in out))
print('no start', [(c['id'], s['sec'], s['time']) for c in out for s in c['sections'] if s['start'] is None][:10])
print(collections.Counter(s['days'] for c in out for s in c['sections']).most_common(15))
print(len(json.dumps(out)))

import json, os, sys, collections
S = sys.argv[1]
cs = json.load(open(os.path.join(S, 'courses_s27.json')))
hm = json.load(open(os.path.join(S, 'heatmap_mba.json')))
allp = {c['id']: c for c in json.load(open(os.path.join(S, 'parsed_all.json')))}

LEVELS = ['Acceptable', 'Good', 'Great', 'Favorite', 'Favorite, risky', 'Long shot']
def nsec(cid, term):
    return sum(1 for s in allp[cid]['sections'] if s['term'] == term and s['part_of_term'].startswith('MBA'))

def model(c):
    h = hm.get(c['id'])
    if not h:
        offered = [x['term'] for x in c['history']]
        if c['newCourse']:
            why = 'New in Spring 2027, so there are no Course Match results yet.'
        elif 'Spring 2026' not in offered:
            last = offered[-1] if offered else ''
            why = 'Not offered in Spring 2026' + (f' (last ran {last}).' if last else '.') + (' A Fall 2026 heatmap would cover it.' if last == 'Fall 2026' else '')
        else:
            why = 'Ran in Spring 2026 but is not in the heatmap, so it was probably filled by application rather than Course Match.'
        return None, why
    n26, n27 = nsec(c['id'], 'Spring 2026'), nsec(c['id'], 'Spring 2027')
    f = n27 / n26 if n26 else 1.0
    cap27 = h['cap'] * f
    adj_fill = h['enr'] / cap27 if cap27 else None
    tiers = [('Acceptable', h['acc']), ('Good', h['good']), ('Great', h['great']), ('Favorite', h['fav'])]
    need = None
    for name, p in tiers:
        if p is not None and p >= 0.7:
            need = name; break
    if need is None:
        top = h['fav'] if h['fav'] is not None else h['great']
        need = 'Favorite, risky' if (top or 0) >= 0.5 else 'Long shot'
    base = need
    adj = ''
    if adj_fill is not None and adj_fill < 0.75 and LEVELS.index(need) > LEVELS.index('Great'):
        need = base = 'Great'
        adj = 'Seats were left over last spring, so the lower percentages reflect prerequisites, corequisites or schedule clashes rather than competition.'
    elif f < 0.8 and adj_fill and adj_fill > 1:
        need = LEVELS[min(LEVELS.index(need) + 1, len(LEVELS) - 1)]
        adj = f'Fewer sections this spring ({n27} vs {n26}), so expect it to be harder than last year.'
    elif f >= 1.5:
        need = LEVELS[max(LEVELS.index(need) - 1, LEVELS.index('Great'))]
        adj = f'More sections this spring ({n27} vs {n26}), so it should be easier than last year.'
    return {'ranked': h['ranked'], 'cap': h['cap'], 'enr': h['enr'], 'fav': h['fav'], 'great': h['great'],
            'good': h['good'], 'acc': h['acc'], 'n26': n26, 'n27': n27, 'perSeat': round(h['ranked'] / h['cap'], 1) if h['cap'] else None,
            'filled': h['enr'] >= 0.95 * h['cap'], 'adjFill': round(adj_fill, 2) if adj_fill else None, 'need': need, 'base': base, 'adj': adj, 'name26': h['name']}, ''

for c in cs:
    c.pop('code', None)
    for s in c['sections']:
        if s['time'].startswith(':'):
            s['time'] = ''
    if c['type'] == 'Elective':
        c['cm'], c['cmWhy'] = model(c)
    else:
        c['cm'], c['cmWhy'] = None, 'Core course: assigned by cluster, not ranked in Course Match.'

import re
def structured_reqs(cid):
    out = []
    for r in allp[cid]['requisites']:
        kind = {'Prerequisite': 'pre', 'Corequisite': 'co'}.get(r['type'])
        if not kind or not r['items']:
            continue
        joins = [i.split(' ', 1)[0] for i in r['items'][1:]]
        mode = 'any' if 'or' in joins else 'all' if 'and' in joins else ('any' if 'ANY' in r['rule'] else 'all')
        courses = []
        for i in r['items']:
            m = re.search(r'(B\d{4})\s*:\s*(.*)', i)
            if m:
                courses.append({'id': m.group(1), 'title': m.group(2).strip()})
        if courses:
            out.append({'type': kind, 'mode': mode, 'courses': courses})
    return out
for c in cs:
    c['rq'] = structured_reqs(c['id'])

# ---- Student reviews (review sheet + recommendation thread), joined by course id
rv = json.load(open(os.path.join(S, 'reviews.json')))['reviews']
ccd = json.load(open(os.path.join(S, 'ccd.json')))
terms = ccd['filters']['semester_filter']
byid = {c['id']: c for c in cs}
def name_tokens(name):
    return [x for x in re.split(r'[^a-z]+', name.lower()) if len(x) >= 4]
for c in cs:
    c['reviews'] = []
other = {}
for r in rv:
    for cid in r['ids']:
        e = {k: r.get(k, '') for k in ('course', 'prof', 'verdict', 'text', 'src')}
        e['truncated'] = bool(r.get('truncated'))
        e['multi'] = len(r['ids']) > 1
        c = byid.get(cid)
        if c:
            profs27 = sorted({p for s in c['sections'] for p in s['profs'] if p != 'New Adjunct'})
            if r.get('prof'):
                pl = r['prof'].lower()
                e['match'] = [p for p in profs27 if any(x in pl for x in name_tokens(p))]
                e['profs27'] = profs27
            c['reviews'].append(e)
        else:
            other.setdefault(cid, []).append(e)
extra = []
for cid, revs in sorted(other.items()):
    rows = [x for x in ccd['courses'].values() if x['course_true_id'] == cid]
    sems = sorted({s for x in rows for s in x['semester_filter']})
    progs = sorted({x['degree_program'] for x in rows})
    title = rows[0]['plain_title'].strip() if rows else cid
    if '20271' in sems:
        note = 'Offered in Spring 2027 as an MS/PhD course, so it is not in Course Match for MBAs. The comment suggests asking about Add/Drop or a waiver.'
    else:
        note = 'Not offered in Spring 2027. Last offered ' + (terms.get(sems[-1], sems[-1]) if sems else 'unknown') + '.'
    extra.append({'id': cid, 'title': title, 'programs': progs, 'note': note,
                  'profs': rows[0]['professors'] if rows else '', 'reviews': revs})
print('reviews on offered courses:', sum(len(c['reviews']) for c in cs), 'courses:', sum(1 for c in cs if c['reviews']), '| other courses:', len(extra))
el = [c for c in cs if c['type'] == 'Elective']
print(collections.Counter(c['cm']['need'] if c['cm'] else 'none' for c in el))
print('adjusted:', [(c['id'], c['title'][:30], c['cm']['base'], '->', c['cm']['need']) for c in el if c['cm'] and c['cm']['adj']])
print('filled26', sum(1 for c in el if c['cm'] and c['cm']['filled']))
json.dump(cs, open(os.path.join(S, 'courses_s27_model.json'), 'w'), ensure_ascii=False)
data = json.dumps(cs, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
t = open(os.path.join(S, 'site', 'template.html'), encoding='utf-8').read()
t = t.replace('__DATA__', data).replace('__EXTRA__', json.dumps(extra, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')).replace('__PULLED__', 'November 2, 2026')
open(os.path.join(S, 'site', 'spring-2027-course-book.html'), 'w', encoding='utf-8').write(t)
js = t[t.rfind('<script>') + 8:t.rfind('</script>')]
open(os.path.join(S, 'site', '_check.js'), 'w').write(js)
print(len(t))

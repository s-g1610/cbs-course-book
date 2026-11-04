import json, os, sys, re
sys.path.insert(0, os.path.join(sys.argv[1], 'scripts'))
from xlsx_read import read
S = sys.argv[1]
sheets, _ = read(os.path.join(S, 'input', 'Course_Match_Heatmap_Spring_2026.xlsx'))
rows = sheets['MBA']['rows']
hm = {}
for rn in sorted(rows):
    r = rows[rn]
    code = r.get(1, (None,))[0]
    if not isinstance(code, str) or not re.match(r'^[A-Z]{4}B\d{4}$', code): continue
    g = lambda c: r.get(c, (None,))[0]
    pct = lambda v: None if v in (None, 'n/a', '') else float(v)
    hm[code[-5:]] = {'code': code, 'name': g(2), 'ranked': g(3), 'cap': g(4), 'enr': g(5),
                     'fav': pct(g(6)), 'great': pct(g(7)), 'good': pct(g(8)), 'acc': pct(g(9))}
print('heatmap MBA rows', len(hm))
json.dump(hm, open(os.path.join(S, 'heatmap_mba.json'), 'w'), indent=0)

cs = json.load(open(os.path.join(S, 'courses_s27.json')))
allp = {c['id']: c for c in json.load(open(os.path.join(S, 'parsed_all.json')))}
el = [c for c in cs if c['type'] == 'Elective']
matched = [c for c in el if c['id'] in hm]
print('S27 electives', len(el), 'matched', len(matched))
print('S27 electives not in heatmap:', [(c['id'], c['title'], 'newCourse' if c['newCourse'] else ('inSp26' if c['inSpring26'] else 'notSp26')) for c in el if c['id'] not in hm])
ids27 = {c['id'] for c in cs}
print('heatmap rows not offered S27:', [(k, v['name']) for k, v in hm.items() if k not in ids27])
# name sanity
for c in matched:
    a = re.sub(r'\W', '', c['title'].lower())[:12]; b = re.sub(r'\W', '', hm[c['id']]['name'].lower())[:12]
    if a != b: print('NAME DIFF', c['id'], c['title'], '|', hm[c['id']]['name'])
# section counts S26 vs S27
def nsec(cid, term):
    return sum(1 for s in allp[cid]['sections'] if s['term'] == term and s['part_of_term'].startswith('MBA'))
chg = []
for c in matched:
    a, b = nsec(c['id'], 'Spring 2026'), nsec(c['id'], 'Spring 2027')
    if a != b: chg.append((c['id'], c['title'], a, b))
print('section count changes:', chg)

import json, os, re, sys, html
S = sys.argv[1]

def clean(s):
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'</(p|div|li|h\d)>', '\n', s)
    s = html.unescape(re.sub(r'<[^>]+>', '', s))
    s = s.replace('\r', '')
    s = re.sub(r'[ \t ]+', ' ', s)
    s = re.sub(r'\n\s*\n+', '\n\n', s)
    return s.strip()

def first(pat, t, flags=re.S):
    m = re.search(pat, t, flags)
    return m.group(1) if m else ''

d = json.load(open(os.path.join(S, 'ccd.json')))
meta = {}
for c in d['courses'].values():
    meta.setdefault(c['course_true_id'], []).append(c)

courses = []
for fn in sorted(os.listdir(os.path.join(S, 'pages'))):
    cid = fn[:-5]
    t = open(os.path.join(S, 'pages', fn), encoding='utf-8').read()
    main = t[t.find('<main'):t.find('</main>')]
    h1 = clean(first(r'<h1[^>]*>(.*?)</h1>', main))
    desc = clean(first(r'<div class="field description field__item">(.*?)</div>\s*(?:<div class="course-division-field|<hr|<div class="requisite|<div class="layout-grid sections-list)', main))
    division = clean(first(r'<strong>Division: </strong>(.*?)</div>', main))
    pathways = [clean(x) for x in re.findall(r'pathways_filter=[^"]+">(.*?)</a>', main)]
    req_blocks = re.findall(r'<div class="requisite-group">(.*?)</div>\s*(?=<div class="requisite-group">|\s*<div class="layout-grid sections-list"|\s*$)', main, re.S)
    reqs = []
    for rb in req_blocks:
        head = clean(first(r'<h3>(.*?)</h3>', rb))
        rule = clean(first(r'<h4>(.*?)</h4>', rb))
        items = [clean(x) for x in re.findall(r'<li>(.*?)</li>', rb, re.S)]
        reqs.append({'type': head, 'rule': rule, 'items': items})
    sections = []
    groups = re.split(r'<h3 class="section-term-title">', main)[1:]
    for g in groups:
        term = clean(g[:g.find('</h3>')])
        for si in re.split(r'<h4 class="section-item-title">', g)[1:]:
            sec_title = clean(si[:si.find('</h4>')])
            fac_html = first(r'<div class="section-item faculty-list">(.*?)</div>\s*</?div', si)
            faculty = [clean(x) for x in re.findall(r'<a [^>]*>(.*?)</a>', fac_html, re.S)] or [clean(fac_html.replace('Faculty', '', 1))]
            faculty = [f for f in faculty if f]
            fac_links = re.findall(r'href="(https://business\.columbia\.edu/person/[^"]+)"', fac_html)
            part = clean(first(r'<div class="section-item part-term">.*?<span>(.*?)</span>', si))
            syl = first(r'<div class="section-item section-syllabus">.*?<a href="([^"]+)"', si)
            notes = clean(first(r'<div class="section-item section-notes">\s*<div class="section-item-header">Section Notes</div>\s*<div>(.*?)</div>', si))
            fmt = clean(first(r'cf-section-format field__item">(.*?)</div>', si))
            sched = []
            for row in re.findall(r'<div class="section-schedule layout-grid">(.*?)</div>', si, re.S):
                sched.append({
                    'days': clean(first(r'schedule-days">(.*?)</span>', row)),
                    'dates': clean(first(r'schedule-dates">(.*?)</span>', row)),
                    'time': clean(first(r'schedule-time">(.*?)</span>', row)),
                    'room': clean(first(r'schedule-location">(.*?)</span>', row)),
                })
            sections.append({'term': term, 'section': sec_title.split(' - ')[-1].strip(), 'faculty': faculty,
                             'faculty_links': fac_links, 'part_of_term': part,
                             'syllabus': ('https://courses.business.columbia.edu' + syl) if syl else '',
                             'notes': notes, 'format': fmt, 'schedule': sched})
    m = meta.get(cid, [{}])
    courses.append({
        'id': cid, 'code': m[0].get('course_code', ''), 'title': (m[0].get('plain_title') or h1).strip(),
        'h1': h1, 'json_programs': sorted({p for x in m for p in x.get('degree_program_filter', [])}),
        'attribute': m[0].get('course_attribute', ''), 'credits': m[0].get('credit_hours', ''),
        'division': division or m[0].get('division', ''), 'pathways': pathways,
        'centers': sorted({p for x in m for p in x.get('centers_programs_filter', []) if p != 'None'}),
        'description': desc or clean(m[0].get('description', '')), 'requisites': reqs,
        'sections': sections, 'url': 'https://courses.business.columbia.edu/' + cid,
    })
json.dump(courses, open(os.path.join(S, 'parsed_all.json'), 'w'), indent=1, ensure_ascii=False)
print(len(courses))

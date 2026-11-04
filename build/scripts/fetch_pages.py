import json, os, sys, time, urllib.request
S = sys.argv[1]
d = json.load(open(os.path.join(S, 'ccd.json')))
ids = sorted({c['course_true_id'] for c in d['courses'].values() if '20271' in c['semester_filter']})
print(len(ids), 'courses', flush=True)
for i, cid in enumerate(ids):
    out = os.path.join(S, 'pages', cid.replace('/', '_') + '.html')
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        continue
    for attempt in range(3):
        try:
            req = urllib.request.Request('https://courses.business.columbia.edu/' + cid, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(req, timeout=30).read()
            open(out, 'wb').write(data)
            break
        except Exception as e:
            print('ERR', cid, e, flush=True)
            time.sleep(2)
    time.sleep(0.4)
    if i % 25 == 0:
        print(i, cid, flush=True)
print('DONE', flush=True)

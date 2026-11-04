import zipfile, re, sys, json
import xml.etree.ElementTree as ET
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def col2n(c):
    n = 0
    for ch in c: n = n * 26 + ord(ch) - 64
    return n
def read(path):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    ss = []
    if 'xl/sharedStrings.xml' in names:
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root.findall('m:si', NS):
            ss.append(''.join(t.text or '' for t in si.iter('{%s}t' % NS['m'])))
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rmap = {r.get('Id'): r.get('Target') for r in rels}
    sheets = {}
    for s in wb.find('m:sheets', NS):
        rid = s.get('{%s}id' % NS['r'])
        tgt = rmap[rid].lstrip('/')
        if not tgt.startswith('xl/'): tgt = 'xl/' + tgt
        root = ET.fromstring(z.read(tgt))
        rows = {}
        for c in root.iter('{%s}c' % NS['m']):
            ref = c.get('r'); t = c.get('t'); st = c.get('s')
            v = c.find('m:v', NS); f = c.find('m:f', NS)
            val = None
            if t == 's' and v is not None: val = ss[int(v.text)]
            elif t == 'inlineStr':
                val = ''.join(x.text or '' for x in c.iter('{%s}t' % NS['m']))
            elif v is not None:
                val = v.text
                try: val = float(val); val = int(val) if val.is_integer() else val
                except: pass
            m = re.match(r'([A-Z]+)(\d+)', ref)
            rows.setdefault(int(m.group(2)), {})[col2n(m.group(1))] = (val, st, f.text if f is not None else None)
        merged = [m.get('ref') for m in root.iter('{%s}mergeCell' % NS['m'])]
        cf = [ET.tostring(x).decode()[:600] for x in root.iter('{%s}conditionalFormatting' % NS['m'])]
        sheets[s.get('name')] = {'rows': rows, 'merged': merged, 'cf': cf}
    return sheets, names
if __name__ == '__main__':
    sheets, names = read(sys.argv[1])
    print(names)
    for name, d in sheets.items():
        rows = d['rows']
        print('==', name, 'rows', len(rows), 'maxcol', max((max(r) for r in rows.values()), default=0), 'merged', d['merged'][:10])
        for cf in d['cf'][:3]: print('CF', cf)
        for rn in sorted(rows)[:int(sys.argv[2]) if len(sys.argv) > 2 else 30]:
            r = rows[rn]
            print(rn, [(cn, r[cn][0]) for cn in sorted(r) if r[cn][0] not in (None, '')])

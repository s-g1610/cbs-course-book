"""Wrap the page body produced by build_page.py into a standalone docs/index.html for GitHub Pages."""
import os, sys
B = sys.argv[1]                      # the build directory
OUT = sys.argv[2]                    # the docs directory
page = open(os.path.join(B, 'site', 'spring-2027-course-book.html'), encoding='utf-8').read()
cut = page.index('<div class="wrap">')
head, body = page[:cut], page[cut:]
icon = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
        "%3Crect width='32' height='32' rx='6' fill='%231d5aa6'/%3E"
        "%3Cpath d='M9 8h10a4 4 0 0 1 4 4v12H13a4 4 0 0 1-4-4z' fill='%23fff'/%3E%3C/svg%3E")
html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="description" content="Spring 2027 CBS MBA courses with sections, professors, Course Match demand and a personal tier list.">\n'
        '<meta name="robots" content="noindex, nofollow">\n'
        f'<link rel="icon" href="{icon}">\n'
        '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
        'body{margin:0;font-size:14px}img{max-width:100%}[hidden]{display:none!important}</style>\n'
        + head + '\n</head>\n<body>\n' + body + '\n</body>\n</html>\n')
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(html)
print('wrote', os.path.join(OUT, 'index.html'), len(html))

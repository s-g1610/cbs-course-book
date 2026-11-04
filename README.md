# Spring 2027 Course Book

A one-page planner for ranking Columbia Business School MBA electives in Course Match, Spring 2027.

Live site: https://s-g1610.github.io/cbs-course-book/

## What it does

- Lists every MBA course with a Spring 2027 section (EMBA, PhD, MS and undergraduate sections left out): professors, part of term, days, times, dates, rooms, syllabus links, descriptions, prerequisites and offering history since Fall 2022.
- Joins the Spring 2026 Course Match results: how many students ranked each course, seats, enrollment, and the share who got a seat at each tier (Favorite, Great, Good, Acceptable).
- "Get it at": the lowest tier at which at least 70% of students got a seat last spring, moved up a level when a full course lost sections this year and down a level (never below Great) when it gained 50% more.
- My list: give each elective a tier and mark your core as completed or pre-enrolled by section. The list checks the 18-credit cap, clashes with pre-enrolled core, clashes between listed courses, prerequisites (must be completed in an earlier term) and corequisites (rank both), and flags Favorites spent on courses that cleared at Great.
- The list is saved in your browser. Use Export list / Import list to move it to another device.

Not affiliated with or endorsed by Columbia Business School. Course Match, Vergil and the Registration Calendar are the official sources.

## Rebuilding

The site is a single static file, `docs/index.html`, served by GitHub Pages from the `docs` folder.

```bash
python3 build/scripts/build_page.py build                # data + build/site/template.html -> build/site/spring-2027-course-book.html
python3 build/scripts/build_site.py build docs           # wrap it as docs/index.html
```

To refresh the catalog from courses.business.columbia.edu, download `https://courses.business.columbia.edu/current-course-data` to `build/ccd.json`, then run `fetch_pages.py`, `parse_pages.py` and `build_db.py` (each takes the `build` directory as its argument) before the two commands above. `join_heatmap.py` rebuilds `build/heatmap_mba.json` from the Course Match heatmap spreadsheet placed at `build/input/Course_Match_Heatmap_Spring_2026.xlsx`.

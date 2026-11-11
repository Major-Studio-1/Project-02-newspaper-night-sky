"""Home (index.html): one question, three facts about the source, then the findings, a storyline and the notebook.

Home asks one thing, what the visitor wants to see, and each question opens the instrument and arrangement that answer
it; everything else is chosen later, on the instrument, when it changes what is seen. Before any picture, three facts
about the source, shown as facts: what the archive is, how much of it survives and when, and the two kinds of evidence
(with how often the machine's reading changes a fact). Then the site's other offerings: the findings as ready views,
a storyline, and the notebook of how it was made. Every number is passed in by the build, never typed here."""
import html

import findings_parts

esc = html.escape
WORDS = 'zero one two three four five six seven eight nine ten eleven twelve'.split()

# The question picks the instrument (the owner, 11 November 2026). Each: the question, what it shows, the instrument and
# its arrangement, an icon, and the link that opens it so.
QUESTIONS = [
    ('Where did it start?', 'A map of the towns that printed each story first.', 'Telescope · Place', 'place',
     'telescope.html?view=place&angle=front'),
    ('What was it about?', 'A ring of 24 subjects; the further out a star, the more papers printed it.', 'Telescope · Topic', 'topic',
     'telescope.html?view=topic&angle=front'),
    ('When in the year?', 'The calendar ring. Search a word, such as fever or ice, to see its season.', 'Telescope · Orbit', 'orbit',
     'telescope.html?view=orbit&angle=front&lookback=all'),   # a season shows over all the years, as on Findings
    ('How did it spread?', 'Each newspaper flashes on the map on the day it prints the story.', 'Pulses', 'pulse', 'pulses.html'),
    ('How many over time?', 'Forty-one years seen from the side: the busy years and the thin ones.', 'Telescope · Side', 'side',
     'telescope.html?view=place&angle=side&lookback=all'),
    ('What did a day sound like?', 'Tune the radio to any day and hear what its papers printed.', 'Radio', 'radio', 'radio.html'),
]


def render(*, years, thin, newspapers, pages, matched, reviewed, reviewed_years, audit, findings, storyline, notebook_entries):
    """years: [(year, newspapers, pages)]; thin: the years with too little archive (finding 1's rule); audit: the matched
    audit's summary; findings: [(n, kind, title, door label, door link)] from findings_parts; storyline: the first
    storyline as checked by stories_parts (or None); notebook_entries: how many entries the notebook has."""
    arch = {y: p for y, p, _ in years}
    out = []

    # Explore: the question.
    cards = ''.join(f'<a class="q" href="{esc(link)}"><h3>{esc(q)}</h3><p>{esc(what)}</p><span class="go">__ICON_{icon}__{esc(tool)}</span></a>'
                    for q, what, tool, icon, link in QUESTIONS)
    out.append('<section class="ask" aria-labelledby="ask-title"><div class="head"><p class="k">Explore</p><h2 id="ask-title">What do you want to see?</h2>'
               '<p class="sub">Each question opens the instrument that answers it, ready to use; change anything once you are there.</p></div>'
               f'<div class="qs">{cards}</div></section>')

    # The source: three facts, each with its picture.
    lows = sorted(thin, key=lambda y: (arch[y], y)); low = arch[lows[0]]; low_years = [y for y in thin if arch[y] == low]
    after = [arch[y] for y in years_range(1800, 1810)]
    chart = findings_parts.bars([arch[y] for y in years_range(1770, 1810)], years_range(1770, 1810),
                                lambda y: findings_parts.GOLD if y in thin else findings_parts.SLATE,
                                lambda y, v: f'{y}: {v} newspapers survive', 20, W=420, H=124, tick_every=10,
                                title='Newspapers that survive, each year, 1770 to 1810')
    tr, raw = audit['transcription'], audit['raw_reviewer_counts']['transcription']
    located = tr['faithful']['count'] + tr['minor_errors']['count'] + tr['major_problem']['count']
    one_in = round(located / raw['major_problem'])
    ry = ', '.join(map(str, reviewed_years[:-1])) + f' and {reviewed_years[-1]}'
    facts = [
        ('One surviving archive',
         f'<p class="big"><span><b>{newspapers}</b> newspapers</span><span><b>{pages:,}</b> pages</span><span><b>1770–1810</b></span></p>',
         'The Library of Congress’s scans of the newspapers that survive, gathered for the Smithsonian’s Revolution Crossroads, '
         'each page read by machine. It is what was kept, not everything that was printed.',
         [('Where the pages come from', 'method.html#archive')]),
        ('How much survives, and when', f'<div class="mini">{chart}</div>',
         f'Only {WORDS[low] if low < len(WORDS) else low} newspapers survive for each of {" and ".join(map(str, low_years))}, against {min(after)} to {max(after)} '
         'a year after 1800. A thin year is a gap in the archive, not silence in the towns.',
         [('The finding', 'findings.html#f1')]),
        ('Two kinds of evidence',
         '<p class="misread"><span><i>Printed</i><b>ſtaves</b></span><span><i>Read by the machine</i><b class="wrong">slaves</b></span></p>',
         f'{matched:,} stories were found by machine, by the wording their printings share; {reviewed} were read and checked against '
         f'the scans by hand, in {ry}. The machine’s reading changes a fact in about one passage in {WORDS[one_in]}, so the scans have the last word.',
         [('How the stories were checked', 'method.html#checks'), ('What we found wrong in the archive', 'findings.html#archive')]),
    ]
    cells = ''.join(f'<div class="fact"><h3>{esc(h)}</h3>{pic}<p>{esc(text)}</p><p class="links">'
                    + ''.join(f'<a href="{esc(href)}">{esc(t)} →</a>' for t, href in links) + '</p></div>' for h, pic, text, links in facts)
    out.append('<section class="source" aria-labelledby="source-title"><div class="head"><p class="k">The source</p>'
               f'<h2 id="source-title">What you are looking at</h2></div><div class="facts3">{cells}</div></section>')

    # Findings: the tested patterns as ready views (the source's own findings, 1 and 2, are the facts above).
    bowls = ''.join(f'<article class="bowl"><span class="n">{n} · {esc(kind)}</span><h3>{esc(title)}</h3><p class="links">'
                    f'<a href="{esc(link)}">{esc(label)}</a><a href="findings.html#f{n}">Read the finding</a></p></article>'
                    for n, kind, title, label, link in findings if n > 2)
    out.append('<section class="bowls" aria-labelledby="bowls-title"><div class="head"><p class="k">Findings</p><h2 id="bowls-title">What the archive shows</h2>'
               '<p class="sub">Each tested, with how sure it is and what it does not say. Open the view that shows it, or read the finding.</p></div>'
               f'<div class="bowl-grid">{bowls}</div><p class="all"><a href="findings.html">All the findings, and what we found wrong in the archive →</a></p></section>')

    # Stories and the notebook.
    doors = []
    if storyline:
        s = storyline
        doors.append(f'<a class="door" href="stories.html#{esc(s["id"])}"><span class="k">Stories</span><h2>{esc(s["title"])}</h2><p>{esc(s["standfirst"])}</p>'
                     f'<p class="meta">{s["year"]} · {len(s["by"])} printed pieces · {len(s["every"])} printings · {len({o["node"] for o in s["every"]})} newspapers</p>'
                     '<span class="go">Read the storyline →</span></a>')
    doors.append('<a class="door" href="notebook.html"><span class="k">Notebook</span><h2>How this was made</h2>'
                 '<p>Told as it happened: what we wanted to know, the decisions and the wrong turns, the archive’s own errors, and the care taken '
                 'for the people who visit and for the people in the papers.</p>'
                 f'<p class="meta">{notebook_entries} dated entries</p><span class="go">Open the notebook →</span></a>')
    out.append(f'<section class="more" aria-label="Stories and the notebook">{"".join(doors)}</section>')
    return '\n'.join(out)


def years_range(a, b):
    return list(range(a, b + 1))

"""The three diagrams on How it works (method.html), drawn as inline SVG from the build's own numbers.

build_pulse_explorer.py calls render() and puts the results in place of __DIAGRAMS_CSS__, __DIAGRAM_PAGE_TO_STAR__,
__DIAGRAM_YEAR__ and __DIAGRAM_STORY__ in method.html, as findings_parts.py does for Findings. The owner approved the three
diagrams on 23 November 2026 (mock-ups: docs/notes/2026-11-24-how-it-works-diagrams.html).

  1 From page to star: pages, the two ways of finding a story (kept apart), the twins, the sky.
  2 What a story is made of: newspaper, issue, page, printing, story, category, with one example (Congress opens the ports,
    1776: 9 printings; its twin R1776-0035 holds all 9, which the build checks), what a reviewed and a matched printing
    carry, and the twin rule.
  3 How a year is read: find, count, one rule, and the two outcomes (admitted; listed with a reason).

Each diagram is drawn twice, wide (the page's text column) and narrow (phones, under 640 px); CSS shows one. The SVG is
aria-hidden and each figure carries the same content as a list for screen readers (.sr-only, in site.css). Text stays text.
Colours are the site's: matched #aab6cf, the three category slots, and the reviewed pill's green and text colour.
Words that are not numbers live here: the thin-year note in diagram 3 ("6 papers in 1793, 4 in 1797; in the thin years, over
half the papers in print, at least 4") must change with the page's own sentence on thresholds.
"""
import html
import random

CAT = ['#3987e5', '#d95926', '#199e70']   # the category slots; 1776's third category (Independence and American government) is #199e70
PALE = '#aab6cf'
SITE_CROP = 'assets/story_discovery_1776__evidence__S76-031.jpg'   # its top 252 px: the heading and the "ſtaves" line
# Diagram 2's example, as release 0.11.15 has it: Congress opens the ports (1776), its 9 printings (paper, printed date) and
# its matched twin. The build checks them with check_example() and stops if a review or a correction changes any of them.
EXAMPLE_STORY, EXAMPLE_TWIN = 'group:congress-opens-ports', 'R1776-0035'
EXAMPLE = [('sn83021126', "Dunlap's Pennsylvania Packet", '1776-04-08'), ('sn83025894', 'Pennsylvania Evening Post', '1776-04-09'),
           ('sn84026371', 'Pennsylvania Gazette', '1776-04-10'), ('sn85047530', 'Pennsylvania Journal', '1776-04-10'),
           ('sn83030135', 'New York Packet', '1776-04-11'), ('sn83025898', 'Pennsylvania Ledger', '1776-04-13'),
           ('sn84024742', 'Virginia Gazette', '1776-04-19'), ('sn84024739', 'Virginia Gazette', '1776-04-20'),
           ('sn83020482', 'New-England Chronicle', '1776-04-25')]   # (newspaper, the name drawn, printed date); two Virginia Gazettes
MON = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
CHIPS = [(paper, f'{int(day[8:])} {MON[int(day[5:7]) - 1]}') for _, paper, day in EXAMPLE]
MATCHES = 310155   # pairs of shared wording, as the page's own text says in #matched
MACHINE = ['IN CONGRESS, March 6, 1776. Resolved,', 'That any goods, wares and merchandizes,', 'except slaves and empty casks, other …']
# the not-admitted list's own kinds (outputs/not_admitted/not_admitted.csv) and their short labels; a new kind stops the build
KIND_LABELS = {'below the rule': 'below the rule', 'not chosen: month and kind covered': 'not chosen', 'other': 'other',
               'private persons': 'private persons', 'digest, list or proceedings': 'digests, lists'}
WORDS = ('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen '
         'eighteen nineteen twenty').split()
# set by render()
N, KINDS, CROP, YEARS = {}, [], SITE_CROP, ''


def esc(s):
    return html.escape(s, quote=True)


class Svg:
    def __init__(self, uid, w, h, variant):
        self.uid, self.w, self.h, self.variant, self.out = uid, w, h, variant, []

    def __call__(self, *parts):
        self.out.extend(parts)
        return self

    def arrow(self, d, cls='arr'):
        return f'<path class="{cls}" d="{d}" marker-end="url(#{self.uid}-ah)"/>'

    def render(self):
        return (f'<svg class="dg dg-{self.variant}" id="{self.uid}" viewBox="0 0 {self.w} {self.h}" aria-hidden="true" focusable="false">'
                f'<defs><marker id="{self.uid}-ah" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" '
                f'orient="auto-start-reverse"><path d="M0 1L9 5L0 9z" class="ah"/></marker></defs>' + ''.join(self.out) + '</svg>')


def path(d, cls='arr'):
    return f'<path class="{cls}" d="{d}"/>'


def rect(x, y, w, h, cls='box', rx=8):
    return f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/>'


def seg(s):
    return esc(s) if isinstance(s, str) else f'<tspan class="{s[1]}">{esc(s[0])}</tspan>'


def text(x, y, lines, cls='s', anchor=None, lh=17):
    """lines: a str, a (str, class) pair, or a list of lines; a line can itself be a list of segments."""
    if isinstance(lines, (str, tuple)):
        lines = [lines]
    out = [f'<text x="{x}" y="{y}" class="{cls}"' + (f' text-anchor="{anchor}"' if anchor else '') + '>']
    for i, ln in enumerate(lines):
        segs = ln if isinstance(ln, list) else [ln]
        out.append(f'<tspan x="{x}" dy="{0 if i == 0 else lh}">' + ''.join(seg(s) for s in segs) + '</tspan>')
    return ''.join(out) + '</text>'


def link(href, *parts):
    return f'<a href="{href}" tabindex="-1">' + ''.join(parts) + '</a>'


def dot(cx, cy, r, fill, extra=''):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"{extra}/>'


def three(x, y, r=3.5, gap=10):
    return ''.join(dot(x + i * gap, y, r, c) for i, c in enumerate(CAT))


def star(cx, cy, r, fill):
    k = r * 0.3
    pts = [(0, -r), (k, -k), (r, 0), (k, k), (0, r), (-k, k), (-r, 0), (-k, -k)]
    return '<path fill="%s" d="M%sZ"/>' % (fill, 'L'.join(f'{cx + a:.1f} {cy + b:.1f}' for a, b in pts))


def sky(x, y, w, h, keep_out, n=26, seed=7):
    """Faint stars along the edges of the sky box (decoration), away from the text rectangle keep_out."""
    out, rnd = [], random.Random(seed)
    kx0, ky0, kx1, ky1 = keep_out
    for _ in range(5000):
        if len(out) >= n:
            break
        px, py = x + 6 + rnd.random() * (w - 12), y + 6 + rnd.random() * (h - 12)
        if kx0 - 6 < px < kx1 + 6 and ky0 - 6 < py < ky1 + 6:
            continue
        r = 0.7 + rnd.random() * 1.1
        col = CAT[len(out) % 3] if len(out) % 9 == 4 else PALE
        out.append(dot(f'{px:.1f}', f'{py:.1f}', f'{r:.1f}', col, f' opacity="{0.9 if col != PALE else 0.45}"'))
    return ''.join(out)


# ---------------------------------------------------------------- 1 · From page to star

def d1_wide():
    s = Svg('dg1w', 660, 514, 'wide')
    s(link('#archive', rect(150, 6, 360, 78),
           text(330, 33, (f"{N['pages']} scanned pages", 't big'), anchor='middle'),
           text(330, 55, f"{N['papers']} newspapers, 1770–1810", anchor='middle'),
           text(330, 73, (f"{N['usable']} with enough readable text to use", 'm'), anchor='middle')))
    s(path('M330 84V98'), s.arrow('M330 98H165V122'), s.arrow('M330 98H495V122'))
    s(link('#matched', rect(20, 124, 290, 194, 'bm'),
           text(36, 147, ('FOUND BY SHARED WORDING', 'cap cm')), dot(292, 143, 4, PALE),
           text(36, 172, ['A computer finds runs of 80 or more', 'words in the same order, printed by',
                          f"two papers within 120 days: {N['matches']}", 'matches across all 41 years.'], lh=18),
           s.arrow('M165 240V260'),
           text(165, 288, (f"{N['matched']} matched stories", 't big'), anchor='middle'),
           text(165, 308, f"{N['mprint']} printings · not checked", anchor='middle')))
    s(link('#reviewed', rect(350, 124, 290, 194, 'br'),
           text(366, 147, ('CHECKED BY HAND', 'cap cr')), three(602, 143),
           text(366, 172, [f'In {YEARS} years, the most widely', 'printed items were read and grouped,',
                           'and every printing was checked', 'against its page scan.'], lh=18),
           s.arrow('M495 240V260'),
           text(495, 288, (f"{N['reviewed']} reviewed stories", 't big'), anchor='middle'),
           text(495, 308, f"{N['rprint']} printings, every one checked", anchor='middle')))
    s(path('M165 318V336', 'arr dash'), path('M495 318V336', 'arr dash'))
    s(link('#telescope', rect(20, 336, 620, 80, 'bt'),
           text(330, 361, ('One story found twice is drawn once, as its reviewed star', 't'), anchor='middle'),
           text(330, 383, [f"{N['twinned']} of the {N['reviewed']} reviewed stories have a matched twin that holds at least",
                           f"half of their printings. {N['twins']} matched stories are such twins."], anchor='middle', lh=18)))
    s(s.arrow('M330 416V434'))
    s(link('#telescope', rect(110, 436, 440, 72),
           sky(110, 436, 440, 72, (150, 442, 530, 502)),
           text(330, 461, (f"The sky: {N['stars']} stars", 't big'), anchor='middle'),
           dot(166, 478, 4, PALE), text(178, 482, f"{N['pale']} pale: matched, not checked ({N['matched']} − {N['twins']})"),
           three(152, 497), text(178, 501, f"{N['reviewed']} in colour: reviewed, checked against the scans")))
    return s.render()


def d1_narrow():
    s = Svg('dg1n', 360, 648, 'narrow')
    s(link('#archive', rect(20, 6, 320, 78),
           text(180, 33, (f"{N['pages']} scanned pages", 't big'), anchor='middle'),
           text(180, 55, f"{N['papers']} newspapers, 1770–1810", anchor='middle'),
           text(180, 73, (f"{N['usable']} with enough readable text to use", 'm'), anchor='middle')))
    s(path('M180 84V98'), s.arrow('M180 98H92V122'), s.arrow('M180 98H268V122'))
    s(link('#matched', rect(8, 124, 168, 282, 'bm'),
           text(20, 145, [('FOUND BY', 'cap cm'), ('SHARED WORDING', 'cap cm')], lh=14), dot(160, 141, 4, PALE),
           text(20, 184, ['Runs of 80 or more', 'words in the same', 'order, in two papers', 'within 120 days:',
                          f"{N['matches']} matches", 'across all 41 years'], lh=17),
           s.arrow('M92 290V310'),
           text(92, 336, (N['matched'], 't big'), anchor='middle'),
           text(92, 356, ('matched stories', 't'), anchor='middle'),
           text(92, 376, f"{N['mprint']} printings", anchor='middle'),
           text(92, 394, ('not checked', 'm cm'), anchor='middle')))
    s(link('#reviewed', rect(184, 124, 168, 282, 'br'),
           text(196, 145, [('CHECKED', 'cap cr'), ('BY HAND', 'cap cr')], lh=14), three(318, 141),
           text(196, 184, [f'In {YEARS} years,', 'the most widely', 'printed items were', 'read and grouped,',
                           'and every printing', 'was checked against', 'its page scan.'], lh=17),
           s.arrow('M268 290V310'),
           text(268, 336, (N['reviewed'], 't big'), anchor='middle'),
           text(268, 356, ('reviewed stories', 't'), anchor='middle'),
           text(268, 376, f"{N['rprint']} printings", anchor='middle'),
           text(268, 394, ('every one checked', 'm cr'), anchor='middle')))
    s(path('M92 406V424', 'arr dash'), path('M268 406V424', 'arr dash'))
    s(link('#telescope', rect(8, 424, 344, 98, 'bt'),
           text(180, 448, ('Found twice, drawn once', 't'), anchor='middle'),
           text(180, 470, [f"{N['twinned']} of the {N['reviewed']} reviewed stories have a",
                           'matched twin that holds at least half of',
                           f"their printings: {N['twins']} matched stories in all."], anchor='middle', lh=17)))
    s(s.arrow('M180 522V540'))
    s(link('#telescope', rect(8, 542, 344, 100),
           sky(8, 542, 344, 100, (20, 548, 340, 636), n=18),
           text(180, 568, (f"The sky: {N['stars']} stars", 't big'), anchor='middle'),
           dot(36, 587, 4, PALE), text(48, 591, f"{N['pale']} pale: matched, not checked"),
           text(48, 609, (f"({N['matched']} − {N['twins']} twins)", 'm')),
           three(20, 625), text(48, 629, f"{N['reviewed']} in colour: reviewed")))
    return s.render()



# ---------------------------------------------------------------- 2 · What a story is made of


def chips(s, x, y0, w, pitch=25):
    out = []
    for i, (name, day) in enumerate(CHIPS):
        y = y0 + i * pitch
        out.append(rect(x, y, w, 20, 'chip' + (' first' if i == 0 else ''), rx=4))
        out.append(text(x + 8, y + 14, name, 'xs'))
        out.append(text(x + w - 8, y + 14, (day, 'xs m'), anchor='end'))
    return ''.join(out)


def crop(x, y, w, h):
    return (f'<image href="{CROP}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMin slice"/>'
            + rect(x, y, w, h, 'frame', rx=2))


def machine(x, y, w, h, lh=15):
    return rect(x, y, w, h, 'mach', rx=2) + text(x + 8, y + 18, MACHINE, 'mono', lh=lh)


def d2_wide():
    s = Svg('dg2w', 660, 632, 'wide')
    # the archive's units, one inside the other
    s(rect(8, 8, 244, 238), text(20, 28, ('NEWSPAPER', 'cap m')), text(240, 28, (f"{N['papers']} in the archive", 'cap m num'), anchor='end'),
      text(20, 47, "Dunlap's Pennsylvania Packet"))
    s(rect(18, 58, 224, 180), text(30, 77, ('ISSUE', 'cap m')), text(230, 77, (N['issues'], 'cap m num'), anchor='end'),
      text(30, 95, '8 April 1776'))
    s(rect(28, 106, 204, 124), text(40, 125, ('PAGE', 'cap m')), text(220, 125, (N['pages'], 'cap m num'), anchor='end'),
      text(40, 143, 'page 3'))
    s(rect(38, 154, 184, 68, 'br'), text(50, 173, ('PRINTING · A PASSAGE', 'cap cr')),
      text(50, 192, ["Congress's resolutions", 'opening the ports']))
    s(s.arrow('M222 188H254V20H266', 'arr dash'))
    # the story's printings, one per newspaper
    s(chips(s, 268, 10, 218))
    for i in range(9):
        cy = 20 + i * 25
        s(path(f'M486 {cy}C500 {cy} 498 168 506 168', 'arr thin'))
    s(s.arrow('M500 168H512'))
    # the story, inside its category
    s(rect(500, 8, 152, 238), text(512, 28, ('CATEGORY · 1776', 'cap m')), dot(640, 24, 4, CAT[2]),
      text(512, 47, ['Independence and', 'American government']))
    s(rect(512, 86, 130, 150, 'br'), text(524, 105, ('STORY', 'cap cr')),
      text(524, 126, [('Congress opens', 't sm'), ('the ports', 't sm')], lh=18),
      text(524, 166, ['9 printings in', '9 newspapers,', '8–25 April 1776']),
      star(530, 222, 6, CAT[2]), text(542, 226, ('one star', 'm')))
    s(text(8, 268, (f"Some reviewed stories are told in parts ({N['parts']} parts in all); a story and its parts are one star.", 'm')))
    # what each kind of printing carries
    s(rect(8, 284, 318, 230, 'br'), text(20, 304, ('A REVIEWED PRINTING CARRIES', 'cap cr')), three(290, 300),
      crop(20, 314, 294, 67), text(20, 394, ('a crop of the page scan (this printing)', 'm')),
      text(20, 416, ['Its transcription, graded against the scan:', 'here it changes a fact, “slaves” where the',
                     'paper printed “ſtaves” (staves).'], lh=17),
      text(20, 474, ['Printed differences, noted: here the heading', 'says “March 6”, where most printings have',
                     'April 6.'], lh=17))
    s(rect(334, 284, 318, 230, 'bm'), text(346, 304, ('A MATCHED PRINTING CARRIES', 'cap cm')), dot(634, 300, 4, PALE),
      machine(346, 314, 294, 64), text(346, 394, ('its machine transcription, as stored', 'm')),
      text(346, 416, ['A machine check: is the passage also in the', "page's other transcription? For 81% of",
                      'printings, yes. Not read one by one.'], lh=17),
      text(346, 474, ['A link to the page scan, to read it there.', 'No crop and no notes.'], lh=17))
    # the twin
    s(link('#telescope', rect(8, 530, 644, 94, 'bt'),
           ''.join(dot(28 + i * 13, 560, 6, 'none', f' stroke="{PALE}" stroke-width="1.3"') + dot(28 + i * 13, 560, 3.4, CAT[2]) for i in range(9)),
           text(78, 590, ('9 of 9', 't sm'), anchor='middle'), text(78, 606, ('printings held', 'm'), anchor='middle'),
           text(160, 554, ('Its twin: found twice, drawn once', 't')),
           text(160, 576, ['The matched story that begins “IN CONGRESS, March 6, 1776”',
                           'holds all 9 of these printings (same paper, date and page).',
                           'At least half makes a twin: the sky draws one star, the reviewed one.'], lh=17)))
    return s.render()


def d2_narrow():
    s = Svg('dg2n', 360, 1358, 'narrow')
    s(rect(8, 8, 344, 230), text(20, 28, ('NEWSPAPER', 'cap m')), text(340, 28, (f"{N['papers']} in the archive", 'cap m num'), anchor='end'),
      text(20, 47, "Dunlap's Pennsylvania Packet"))
    s(rect(18, 58, 324, 172), text(30, 77, ('ISSUE', 'cap m')), text(330, 77, (N['issues'], 'cap m num'), anchor='end'),
      text(30, 95, '8 April 1776'))
    s(rect(28, 106, 304, 116), text(40, 125, ('PAGE', 'cap m')), text(320, 125, (N['pages'], 'cap m num'), anchor='end'),
      text(40, 143, 'page 3'))
    s(rect(38, 152, 284, 62, 'br'), text(50, 171, ('PRINTING · A PASSAGE', 'cap cr')),
      text(50, 190, ["Congress's resolutions", 'opening the ports'], lh=16))
    s(s.arrow('M300 214V250', 'arr dash'))
    s(chips(s, 8, 252, 344))
    s(s.arrow('M180 474V498'))
    s(rect(8, 500, 344, 136), text(20, 520, ('CATEGORY · 1776', 'cap m')), dot(340, 516, 4, CAT[2]),
      text(20, 539, 'Independence and American government'))
    s(rect(18, 552, 324, 74, 'br'), text(30, 571, ('STORY', 'cap cr')), star(318, 567, 6, CAT[2]),
      text(306, 571, ('one star', 'm'), anchor='end'),
      text(30, 592, ('Congress opens the ports', 't')),
      text(30, 612, '9 printings in 9 newspapers, 8–25 April 1776'))
    s(text(8, 656, ['Some reviewed stories are told in parts', f"({N['parts']} parts in all); a story and its", 'parts are one star.'], 'm', lh=16))
    s(rect(8, 712, 344, 252, 'br'), text(20, 732, ('A REVIEWED PRINTING CARRIES', 'cap cr')), three(318, 728),
      crop(20, 742, 320, 73), text(20, 830, ('a crop of the page scan (this printing)', 'm')),
      text(20, 852, ['Its transcription, graded against the scan:', 'here it changes a fact, “slaves” where the',
                     'paper printed “ſtaves” (staves).'], lh=17),
      text(20, 908, ['Printed differences, noted: here the heading', 'says “March 6”, where most printings have',
                     'April 6.'], lh=17))
    s(rect(8, 980, 344, 230, 'bm'), text(20, 1000, ('A MATCHED PRINTING CARRIES', 'cap cm')), dot(334, 996, 4, PALE),
      machine(20, 1010, 320, 62), text(20, 1090, ('its machine transcription, as stored', 'm')),
      text(20, 1112, ['A machine check: is the passage also in the', "page's other transcription? For 81% of",
                      'printings, yes. Not read one by one.'], lh=17),
      text(20, 1170, ['A link to the page scan, to read it there.', 'No crop and no notes.'], lh=17))
    s(link('#telescope', rect(8, 1226, 344, 124, 'bt'),
           ''.join(dot(26 + i * 14, 1250, 7, 'none', f' stroke="{PALE}" stroke-width="1.3"') + dot(26 + i * 14, 1250, 3.6, CAT[2]) for i in range(9)),
           text(156, 1254, ('9 of 9 printings held', 'm')),
           text(20, 1282, ('Its twin: found twice, drawn once', 't')),
           text(20, 1302, ['The matched story that begins “IN CONGRESS,', 'March 6, 1776” holds all 9 of these printings.',
                           'At least half makes a twin: one star.'], lh=17)))
    return s.render()



# ---------------------------------------------------------------- 3 · How a year is read


def bars(x, y, label_w, bar_max, pitch=18, cls='xs'):
    top = max(n for _, n in KINDS)
    out = []
    for i, (name, n) in enumerate(KINDS):
        by = y + i * pitch
        w = max(2, bar_max * n / top)
        out.append(text(x, by, name, cls))
        out.append(rect(x + label_w, by - 9, f'{w:.1f}', 10, 'bar', rx=2))
        out.append(text(x + label_w + w + 5, by, (str(n), cls + ' num'), ))
    return ''.join(out)


def d3_wide():
    s = Svg('dg3w', 660, 486, 'wide')     # 486: room for the third line of the note
    s(rect(8, 36, 168, 112), text(20, 60, ('1 · Find', 't')),
      text(20, 81, ["The year's matched", 'stories in 3 or more', 'papers, split into single', 'printed items'], lh=17))
    s(s.arrow('M92 148V168'))
    s(rect(8, 170, 168, 112), text(20, 194, ('2 · Count', 't')),
      text(20, 215, ['each item by the papers', 'that print its own words,', 'searched in both', 'transcriptions'], lh=17))
    s(text(204, 24, [('3 · Sort by one rule, the same for every subject', 't')]))
    # distributor from Count to the four rows
    s(path('M176 226H190'), path('M190 80V360'))
    for cy in (80, 176, 264, 360):
        s(s.arrow(f'M190 {cy}H202'))
    s(rect(204, 36, 228, 88, 'br'), text(216, 59, ('9 or more papers', 't')),
      text(216, 80, ['Every single item is admitted,', 'except digests of unrelated', 'paragraphs'], lh=17))
    s(rect(204, 134, 228, 88, 'br2'), text(216, 157, ('7 or 8 papers', 't')),
      text(216, 178, ['Chosen to cover the months', 'and the kinds of news; the', 'others are listed'], lh=17))
    s(rect(204, 232, 228, 66, 'bm'), text(216, 255, ('Fewer than 7 papers', 't')),
      text(216, 276, 'Below the rule: listed'))
    s(rect(204, 308, 228, 106, 'bt'), text(216, 331, ('Any number of papers', 't')),
      text(216, 352, ['Digests, lists, proceedings', '(not one item); items on', 'private persons: the owner', 'decides; listed without names'], lh=17))
    s(text(204, 438, ['Where few papers survive, the rule is lower:', '6 papers in 1793, 4 in 1797; in the thin years,', 'over half the papers in print, at least 4.'], 'm', lh=16))
    # to the two outcomes
    s(s.arrow('M432 80H466'), s.arrow('M432 166H466'), s.arrow('M432 196H452V250H466'),
      s.arrow('M432 266H466'), s.arrow('M432 360H466'))
    s(link('#reviewed', rect(468, 36, 184, 190, 'br'), text(480, 57, ('ADMITTED', 'cap cr')), three(616, 53),
           text(480, 80, ['Every printing checked', 'against its page scan,', 'then grouped into', 'reviewed stories'], lh=17),
           text(480, 174, (f"{N['reviewed']} stories", 't big')),
           text(480, 194, f"{N['rprint']} printings"), text(480, 212, (f'{YEARS} years', 'm'))))
    s(rect(468, 236, 184, 226, 'bm'), text(480, 257, ('READ, NOT ADMITTED', 'cap cm')), dot(636, 253, 4, PALE),
      text(480, 282, (f"{N['notadm']} items", 't big')),
      text(480, 302, ['on a public list, each', 'with its reason'], lh=17),
      bars(480, 344, 94, 38),
      text(480, 436, ['Most stay in the sky', 'as matched stars'], 'm', lh=16))
    return s.render()


def d3_narrow():
    s = Svg('dg3n', 360, 859, 'narrow')   # 859: the note's third line moves the rest down 16
    s(rect(8, 8, 344, 74), text(20, 31, ('1 · Find', 't')),
      text(20, 52, ["The year's matched stories in 3 or more papers,", 'split into single printed items'], lh=17))
    s(s.arrow('M180 82V100'))
    s(rect(8, 102, 344, 74), text(20, 125, ('2 · Count', 't')),
      text(20, 146, ['each item by the papers that print its own', 'words, searched in both transcriptions'], lh=17))
    s(s.arrow('M180 176V194'))
    s(text(8, 214, ('3 · Sort by one rule', 't')), text(8, 232, ('the same for every subject', 'm')))
    s(rect(8, 244, 344, 70, 'br'), text(20, 266, [[('9 or more papers', 't'), (' → admitted', 'cr t')]]),
      text(20, 286, ['Every single item, except digests of', 'unrelated paragraphs'], lh=17))
    s(rect(8, 322, 344, 70, 'br2'), text(20, 344, [[('7 or 8 papers', 't'), (' → chosen', 'cr t')]]),
      text(20, 364, ['Chosen to cover the months and the kinds', 'of news; the others are listed'], lh=17))
    s(rect(8, 400, 344, 52, 'bm'), text(20, 422, [[('Fewer than 7 papers', 't'), (' → listed', 'cm t')]]),
      text(20, 442, 'Below the rule'))
    s(rect(8, 460, 344, 87, 'bt'), text(20, 482, [[('Any number of papers', 't'), (' → listed', 'cm t')]]),
      text(20, 502, ['Digests, lists and proceedings (not one item);', 'items on private persons: the owner decides;', 'listed without names'], lh=17))
    s(text(8, 567, ['Where few papers survive, the rule is lower:', '6 papers in 1793, 4 in 1797; in the thin years,', 'over half the papers in print, at least 4.'], 'm', lh=16))
    s('<g transform="translate(0 16)">')   # below the note's third line
    s(s.arrow('M92 589V607'), s.arrow('M268 589V607'))
    s(link('#reviewed', rect(8, 609, 168, 224, 'br'), text(20, 629, ('ADMITTED', 'cap cr')), three(140, 625),
           text(20, 651, ['Every printing', 'checked against its', 'page scan, then', 'grouped'], lh=17),
           text(20, 741, (f"{N['reviewed']} stories", 't big')),
           text(20, 761, f"{N['rprint']} printings"), text(20, 779, (f'{YEARS} years', 'm'))))
    s(rect(184, 609, 168, 224, 'bm'), text(196, 629, ('NOT ADMITTED', 'cap cm')), dot(336, 625, 4, PALE),
      text(196, 653, (f"{N['notadm']} items", 't big')),
      text(196, 673, ['listed, each with', 'its reason'], lh=16),
      bars(196, 713, 82, 30, pitch=17, cls='xxs'),
      text(196, 807, ['Most stay in the sky', 'as matched stars'], 'm', lh=16))
    s('</g>')
    return s.render()




def figure(num, wide, narrow, alt, caption):
    return (f'<figure class="dg-fig" id="dg-{num}" aria-labelledby="dg-{num}-cap">{wide}{narrow}'
            f'<ol class="sr-only">' + ''.join(f'<li>{esc(a)}</li>' for a in alt) + '</ol>'
            f'<figcaption id="dg-{num}-cap">{caption}</figcaption></figure>')


DG_CSS = """
.dg-fig{margin:24px 0 28px;padding:0}
.dg-fig figcaption{color:var(--muted);font-size:14px;line-height:1.5;margin-top:10px}
.dg-fig figcaption b{color:var(--ink);font-weight:600}
.dg{display:block;width:100%;height:auto}
.dg-narrow{display:none}
@media(max-width:640px){.dg-wide{display:none}.dg-narrow{display:block}}
.dg text{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;fill:#c6d0e4;font-size:13px}
.dg .t{fill:var(--ink);font-size:15px;font-weight:600}.dg .t.sm{font-size:14px}.dg .t.big{font-size:18px}
.dg .s{fill:#c6d0e4;font-size:13px}.dg .xs{font-size:11.5px}.dg .xxs{font-size:10.5px}
.dg .m{fill:var(--muted);font-size:12px}.dg .xs.m{font-size:11.5px}
.dg .cap{font-size:11px;font-weight:600;letter-spacing:.08em}
.dg .cm{fill:#aab6cf}.dg .cr{fill:#96dfc4}.dg .num{font-variant-numeric:tabular-nums}
.dg .mono{font-family:ui-monospace,Consolas,"Cascadia Mono",monospace;font-size:11.5px;fill:#aab6cf}
.dg .box{fill:#11192b;fill-opacity:.6;stroke:#28334c}
.dg .bm{fill:#aab6cf;fill-opacity:.05;stroke:#aab6cf;stroke-opacity:.5}
.dg .br{fill:#199e70;fill-opacity:.09;stroke:#199e70;stroke-opacity:.9}
.dg .br2{fill:#199e70;fill-opacity:.04;stroke:#199e70;stroke-opacity:.7;stroke-dasharray:6 4}
.dg .bt{fill:none;stroke:#a2afc8;stroke-opacity:.6;stroke-dasharray:5 4}
.dg .chip{fill:#199e70;fill-opacity:.12;stroke:#199e70;stroke-opacity:.55}.dg .chip.first{stroke-opacity:1}
.dg .frame{fill:none;stroke:#28334c}.dg .mach{fill:#aab6cf;fill-opacity:.04;stroke:#28334c}
.dg .bar{fill:#aab6cf;fill-opacity:.6}
.dg .arr{fill:none;stroke:#a2afc8;stroke-opacity:.7;stroke-width:1.4}.dg .arr.dash{stroke-dasharray:4 3}
.dg .arr.thin{stroke-width:1;stroke-opacity:.45}.dg .ah{fill:#a2afc8}
.dg a{cursor:pointer}.dg a:hover rect{stroke:var(--blue);stroke-opacity:1}
"""

def check_example(printings, twin_of, held, scans):
    """The build's check of diagram 2's example, which the diagram draws word for word. printings: [(lccn, 'YYYY-MM-DD')] of
    EXAMPLE_STORY in this release; twin_of: the story EXAMPLE_TWIN is drawn as; held: how many of the printings the twin
    holds (same paper, date and page); scans: the printings' crops. Returns '' while the diagram is true, else what changed."""
    drawn = sorted((lccn, day) for lccn, _, day in EXAMPLE)
    problems = []
    if sorted(printings) != drawn:
        gone = [p for p in drawn if p not in printings]
        new = [p for p in printings if p not in drawn]
        problems.append(f'it has {len(printings)} printings, the diagram draws {len(drawn)}'
                        + (f'; drawn but gone: {gone}' if gone else '') + (f'; new, not drawn: {new}' if new else ''))
    if twin_of != EXAMPLE_STORY:
        problems.append(f'{EXAMPLE_TWIN} is now drawn as {twin_of!r}, not as this story')
    if held != len(drawn):
        problems.append(f'its twin {EXAMPLE_TWIN} holds {held} of its printings, not {len(drawn)}')
    if SITE_CROP not in scans:
        problems.append(f'no printing has the crop {SITE_CROP} any more')
    return ('How it works, diagram 2: its example, Congress opens the ports (1776), has changed: ' + '; '.join(problems)
            + '. Update EXAMPLE and the words that count it in work/method_diagrams.py.') if problems else ''


def render(n, crop=SITE_CROP):
    """n: the build's numbers: pages, newspapers, issues, eligible, matches (optional), matched, matched_printings, reviewed,
    reviewed_printings, reviewed_years, twinned, twins, stars, parts, kinds ({kind: items}). Returns css and the figures."""
    global N, KINDS, CROP, YEARS
    assert n['stars'] == n['matched'] - n['twins'] + n['reviewed'], 'the sky: matched - twins + reviewed'
    unknown = set(n['kinds']) - set(KIND_LABELS)
    assert not unknown, f'new kinds in the not-admitted list: {unknown}; give them a label in KIND_LABELS'
    N = {k: f'{v:,}' for k, v in dict(pages=n['pages'], usable=n['eligible'], papers=n['newspapers'], issues=n['issues'],
                                       matches=n.get('matches', MATCHES), matched=n['matched'], mprint=n['matched_printings'],
                                       reviewed=n['reviewed'], rprint=n['reviewed_printings'], twinned=n['twinned'],
                                       twins=n['twins'], stars=n['stars'], pale=n['matched'] - n['twins'], parts=n['parts'],
                                       notadm=sum(n['kinds'].values())).items()}
    KINDS = sorted(((KIND_LABELS[k], v) for k, v in n['kinds'].items() if v), key=lambda kv: -kv[1])
    CROP = crop
    YEARS = WORDS[n['reviewed_years']] if n['reviewed_years'] < len(WORDS) else str(n['reviewed_years'])
    D1_ALT = [
        f"{N['pages']} scanned pages from {N['papers']} newspapers, 1770–1810; {N['usable']} have enough readable text to use.",
        f"Found by shared wording, all 41 years: a computer finds runs of 80 or more words in the same order, printed by two papers "
        f"within 120 days. {N['matches']} matches are joined into {N['matched']} matched stories with {N['mprint']} printings, not checked.",
        f"Checked by hand, {YEARS} years: the most widely printed items were read and grouped, and every printing was checked "
        f"against its page scan: {N['reviewed']} reviewed stories with {N['rprint']} printings.",
        f"One story found twice is drawn once, as its reviewed star: {N['twinned']} of the {N['reviewed']} reviewed stories have a "
        f"matched twin that holds at least half of their printings; {N['twins']} matched stories are such twins.",
        f"The sky holds {N['stars']} stars: {N['pale']} pale stars, matched and not checked ({N['matched']} less the {N['twins']} twins), "
        f"and {N['reviewed']} stars in colour, reviewed.",
    ]
    D2_ALT = [
        f"The archive's units, one inside the other: a newspaper ({N['papers']} in the archive), an issue ({N['issues']}), a page "
        f"({N['pages']}), and on the page a printing, one passage. The example: Dunlap's Pennsylvania Packet, the issue of 8 April 1776, "
        "page 3, Congress's resolutions opening the ports.",
        "A story gathers its printings from many papers: Congress opens the ports has 9 printings in 9 newspapers, 8 to 25 April 1776: "
        + '; '.join(f'{n}, {d}' for n, d in CHIPS) + '. It belongs to the category Independence and American government (1776), '
        f"and it is one star. Some reviewed stories are told in parts ({N['parts']} parts in all); a story and its parts are one star.",
        "A reviewed printing carries a crop of the page scan; its transcription, graded against the scan (here it changes a fact: "
        "“slaves” where the paper printed “ſtaves”, staves); and the printed differences, noted (here the heading says March 6, where most "
        "printings have April 6).",
        "A matched printing carries its machine transcription as stored, a machine check of whether the passage is also in the page's "
        "other transcription (yes for 81% of printings), and a link to the page scan. It is not read one by one; there is no crop.",
        "Its twin: the matched story that begins “IN CONGRESS, March 6, 1776” holds all 9 of these printings (same paper, date and page). "
        "A matched story that holds at least half of a reviewed story's printings is its twin, and the sky draws them as one star, the reviewed one.",
    ]
    D3_ALT = [
        "1, Find: the year's matched stories in 3 or more papers, split into single printed items.",
        "2, Count: each item by the papers that print its own words, searched in both transcriptions.",
        "3, Sort by one rule, the same for every subject. 9 or more papers: every single item is admitted, except digests of unrelated "
        "paragraphs. 7 or 8 papers: chosen to cover the months and the kinds of news; the others are listed. Fewer than 7 papers: below "
        "the rule, listed. Any number of papers: digests, lists and proceedings (not one item) are listed, and so are items that turn on "
        "private persons, without names, unless the owner decides otherwise. Where few papers survive, the rule is lower: 6 papers in 1793, 4 in 1797; in the thin years, more than half of the "
        "papers in print, and at least 4: items printed by all of them are admitted, the others chosen to cover the months "
        "and the kinds of news.",
        f"Admitted: every printing is checked against its page scan, then grouped into reviewed stories: {N['reviewed']} stories with "
        f"{N['rprint']} printings in {YEARS} years.",
        f"Read and not admitted: {N['notadm']} items on a public list, each with its reason: " + ', '.join(f'{n} {k}' for k, n in KINDS)
        + '. Most stay in the sky as matched stars.',
    ]
    FIG1 = figure(1, d1_wide(), d1_narrow(), D1_ALT,
                  '<b>From page to star.</b> Two ways of finding a story, kept apart until the sky. Each box opens its section.')
    FIG2 = figure(2, d2_wide(), d2_narrow(), D2_ALT,
                  '<b>What a story is made of</b>, with one example from 1776: Congress’s resolutions opening the ports. '
                  'The counts in the corners are for the whole archive.')
    FIG3 = figure(3, d3_wide(), d3_narrow(), D3_ALT,
                  '<b>How a year is read.</b> One rule for every subject. What is read and not admitted stays in view, on '
                  '<a href="__REPO__/blob/main/docs/not-admitted/README.md">a public list</a>.')
    return {'css': DG_CSS, 'page_to_star': FIG1, 'story': FIG2, 'year': FIG3}

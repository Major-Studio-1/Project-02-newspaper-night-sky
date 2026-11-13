"""The appendix of How it works: what was handled differently from the reviewed stories (work/appendix.json).

check(appx, page_date, group_label, group_in_year) stops the build when a printing's page is not in the release, when
the entries of a part are not in year order, or when an excerpt note does not name a reviewed group of its year by its
label. render(appx, page_date, paper_name, scan_base) writes the section, which ends How it works (#appendix).
page_date(key) gives the printed date of a page key (lccn|filed date|edition|page), or None.
"""
import html
from datetime import date

PARTS = [
 ('private', 'Printed in several papers, not shown as reviewed stories because they turn on private persons',
  "A reviewed story gets our own title, a colour and a voice on the radio. For a story whose subject is a private person, "
  "not an office-holder, that would put the person's name forward in our words, so these were kept out of the reviewed "
  "stories. Their printings are here, with their page scans."),
 ('held', 'Held back for framing in 1797, not yet read',
  "Two candidates of 1797 were set aside 'for framing' before the rule 'every story alike' (11 November 2026). The "
  "stories once held back in 1776, 1793, 1807 and 1808 were read like every other on 12 November and are reviewed "
  "stories now where they reached their year's count; these two have not been read yet."),
 ('excerpts', "Excerpts that stop short of a private person's name",
  "These stories are on the site like any other; only their excerpts leave the name out. It is in the printings, on "
  "the scans."),
]


def _d(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B')}"


def _span(dates):
    a, b = min(dates), max(dates)
    if a == b:
        return f'{_d(a)} {a[:4]}'
    return f'{_d(a)} – {_d(b)} {b[:4]}' if a[:4] == b[:4] else f'{_d(a)} {a[:4]} – {_d(b)} {b[:4]}'


def check(appx, page_date, group_label, group_in_year):
    n = 0
    for part, _, _ in PARTS:
        years = [e['year'] for e in appx[part]]
        assert years == sorted(years), f'appendix: {part} not in year order'
        for e in appx[part]:
            n += 1
            if part == 'excerpts':
                assert group_label(e['group']) == e['label'], f"appendix: {e['group']} is not labelled {e['label']!r}"
                assert group_in_year(e['group'], e['year']), f"appendix: {e['group']} has no printing in {e['year']}"
                continue
            assert len(set(e['printings'])) == len(e['printings']), f"appendix: a printing repeats in {e['title']}"
            for key in e['printings']:
                printed = page_date(key)
                assert printed, f'appendix: {key} is not a page of the release'
                assert printed[:4] == str(e['year']), f"appendix: {key} is printed in {printed[:4]}, not {e['year']}"
    return n


def render(appx, page_date, paper_name, scan_base):
    out = ['<section id="appendix"><h2>Appendix: what was handled differently</h2>',
           "<p>Almost everything on this site went through the same steps. The items below did not, and they are listed "
           "here so that nothing is left out without a word. They are described in plain words, without repeating the "
           "names of private persons; every printing links to its page scan, where the papers' own words can be read. "
           "The printings were found by machine and by phrase searches, and were not checked against the scans.</p>"]
    for part, title, intro in PARTS:
        out.append(f'<h3>{html.escape(title)}</h3><p>{html.escape(intro)}</p><ul class="appx">')
        for e in appx[part]:
            if part == 'excerpts':
                href = f"pulses.html?year={e['year']}&amp;focus=group:{e['group']}"
                out.append(f"<li><span class=\"k\">{e['year']} · {html.escape(e['label'])}.</span> {html.escape(e['note'])} "
                           f'<a href="{href}">See it in Pulses</a></li>')
                continue
            rows = sorted((page_date(k), k) for k in e['printings'])
            papers = len({k.split('|')[0] for k in e['printings']})
            links = ' · '.join(
                f'<a href="{scan_base}{k.split("|")[0]}/{k.split("|")[1]}_{k.split("|")[2]}_{k.split("|")[3]}.pdf">'
                f'{html.escape(paper_name.get(k.split("|")[0], k.split("|")[0]))}, {_d(d)}, page {k.split("|")[3]}</a>'
                for d, k in rows)
            count = f"{len(rows)} printing{'s' if len(rows) != 1 else ''} in {papers} paper{'s' if papers != 1 else ''}"
            out.append(f"<li><p><span class=\"k\">{e['year']} · {html.escape(e['title'])}.</span> {html.escape(e['what'])}</p>"
                       f"<p>{count}, {_span([d for d, _ in rows])}. {html.escape(e['why'])}</p>"
                       f'<details><summary>The printings, with their page scans</summary><p>{links}</p></details></li>')
        out.append('</ul>')
    out.append('</section>')
    return '\n'.join(out)

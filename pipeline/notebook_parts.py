"""The Notebook page (notebook.html): how the project was made, told as it happened.

Rendered at build time from the ledger work/notebook.json: phases, and dated entries with their kinds (purpose,
decision, frustration, wrong turn, care, discovery, difficulty overcome, encouraging moment, the maker's words), an
optional quote in the maker's own words, what the entry changed (links into the site) and its source. The build checks
every entry: a known phase and known kinds, dates in order within the ledger, and links that open pages of the site."""
import html, re
from datetime import date

esc = html.escape
KINDS = {'words': "In the maker's words", 'care': 'Care', 'overcoming': 'Difficulty overcome', 'decision': 'Decision', 'wrong': 'Wrong turn',
         'discovery': 'Discovery', 'encouraging': 'Encouraging moment', 'purpose': 'Purpose', 'frustration': 'Frustration'}
# The filters, in the order a visitor might want them: the maker's words and care first.
FILTERS = [('', 'All'), ('words', "In the maker's words"), ('care', 'Care'), ('overcoming', 'Difficulties overcome'), ('decision', 'Decisions'),
           ('wrong', 'Wrong turns'), ('discovery', 'Discoveries'), ('encouraging', 'Encouraging moments'), ('purpose', 'Purposes')]


def check(ledger, pages):
    """Every entry in a known phase, of known kinds, in date order, with links to pages that exist. Returns the count."""
    phases = {p['id'] for p in ledger['phases']}
    last = None
    for e in ledger['entries']:
        assert e['phase'] in phases, f"notebook: unknown phase {e['phase']} ({e['title']})"
        assert e['kinds'] and all(k in KINDS for k in e['kinds']), f"notebook: unknown kind in {e['title']}"
        assert ('quote' in e) == ('words' in e['kinds']), f"notebook: a quote and the kind 'words' go together ({e['title']})"
        d = date.fromisoformat(e['date']); assert last is None or d >= last, f"notebook: {e['title']} is out of date order"; last = d
        for _, href in e['changed']['links']:
            assert not re.match(r'^[a-z]+:', href), f"notebook: links stay on the site ({href})"
            assert href.split('#')[0].split('?')[0] in pages, f"notebook: {href} is not a page of the site"
    return len(ledger['entries'])


def render(ledger):
    """The filters and the entries, phase by phase, as HTML for the template's __NOTEBOOK__."""
    filters = ''.join(f'<button type="button" data-k="{k}" aria-pressed="{str(not k).lower()}">{esc(label)}</button>' for k, label in FILTERS)
    out = [f'<div class="filters" role="group" aria-label="Show entries of one kind">{filters}</div>']
    for ph in ledger['phases']:
        out.append(f'<section class="phase" id="{ph["id"]}"><h2>{esc(ph["title"])}</h2><p>{esc(ph["intro"])}</p></section><div class="tl">')
        for e in (e for e in ledger['entries'] if e['phase'] == ph['id']):
            labels = e.get('labels') or [KINDS[k] for k in e['kinds'] if k != 'words'] + ([KINDS['words']] if 'words' in e['kinds'] else [])
            quote = e.get('quote')
            q = f'<blockquote>{esc(quote["text"])}<cite>{esc(quote["cite"])}</cite></blockquote>' if quote else ''
            ch = e['changed']
            links = ', '.join(f'<a href="{esc(h)}">{esc(t)}</a>' for t, h in ch['links']) or esc(ch.get('note', ''))
            kinds = ''.join(f'<span class="k">{esc(label)}</span>' for label in labels)
            out.append(f'<article class="e{" lift" if e.get("lift") else ""}" data-k="{" ".join(e["kinds"])}">'
                       f'<div class="when"><time datetime="{e["date"]}">{esc(e["when"])}</time></div><div class="kinds">{kinds}</div>'
                       f'<h3>{esc(e["title"])}</h3>{q}<p>{esc(e["text"])}</p>'
                       f'<p class="changed"><b>{esc(ch["label"])}</b>{links}</p><p class="src">{esc(e["source"])}</p></article>')
        out.append('</div>')
    return '\n'.join(out)

"""Shared site parts for Newspaper Night Sky: one header and one footer for every page.

Templates carry three placeholders, filled by work/build_pulse_explorer.py through fill():
  __SITE_HEAD__    stylesheet and icon links, in <head>
  __SITE_HEADER__  brand, main menu (current page marked) and the search box
  __SITE_FOOTER__  more links, the data source and the release
Because every page gets its header and footer from here, they cannot drift apart.
"""
import html
import re

# Public repository: a curated export of this project, made by work/export_public_repo.py.
REPO = 'https://github.com/Major-Studio-1/Project-02-newspaper-night-sky'
# Where GitHub Pages serves that repository's site/ folder: the custom domain newspapers.icare.love (a CNAME to
# major-studio-1.github.io; the github.io address forwards here).
PAGES = 'https://newspapers.icare.love/'
# The course repository keeps the proposal as submitted on 1 November 2026, at this commit.
PROPOSAL = 'https://github.com/Major-Studio-1/Project-02-newspapers/tree/85ba363414d55edd68c96fef4b9ee944b99acef1'
MENU = [('telescope', 'telescope.html', 'Telescope'), ('pulses', 'pulses.html', 'Pulses'), ('radio', 'radio.html', 'Radio'), ('method', 'method.html', 'How it works')]
# A night sky: one bright four-pointed star and a small companion.
MARK = ('<svg class="brand-mark" viewBox="0 0 24 24" aria-hidden="true">'
        '<path d="M10 2l1.7 6.3L18 10l-6.3 1.7L10 18l-1.7-6.3L2 10l6.3-1.7z" fill="currentColor"/>'
        '<circle cx="19" cy="19" r="1.7" fill="currentColor" fill-opacity=".6"/></svg>')
ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect width='24' height='24' rx='5' fill='%23050711'/%3E"
        "%3Cpath d='M10.5 3l1.6 5.9 5.9 1.6-5.9 1.6-1.6 5.9-1.6-5.9-5.9-1.6 5.9-1.6z' fill='%238ccfff'/%3E"
        "%3Ccircle cx='18.5' cy='18.5' r='1.6' fill='%238ccfff' fill-opacity='.6'/%3E%3C/svg%3E")


# Light line icons, drawn in the text colour on a 24-unit grid (strokes 1.6, round ends). They live once per page, as a
# sprite in the header; a template writes __ICON_name__ and fill() puts in <svg class="ico"><use href="#i-name"/></svg>.
ICONS = {
    'radio': '<rect x="3" y="8.5" width="18" height="11.5" rx="2.5"/><circle cx="9" cy="14.25" r="3"/><path d="M15 12.5h3M15 16h3M7 8.5 16.5 4"/>',
    'place': '<path d="M12 21s-6.5-6-6.5-10.8a6.5 6.5 0 0 1 13 0C18.5 15 12 21 12 21z"/><circle cx="12" cy="10.2" r="2.3"/>',
    'topic': '<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5V12h8.5M12 12l-6 6"/>',
    'orbit': '<circle cx="12" cy="12" r="2.6"/><path d="M18.93 8A8 8 0 0 1 8 18.93M5.07 16A8 8 0 0 1 16 5.07"/>'
             '<circle cx="17.66" cy="6.34" r="1.7" fill="currentColor" stroke="none"/><circle cx="6.34" cy="17.66" r="1.7" fill="currentColor" stroke="none"/>',
    'drift': '<path d="M6.5 3.5h11M6.5 20.5h11M8 3.5c0 4.6 4 5.3 4 8.5s-4 3.9-4 8.5M16 3.5c0 4.6-4 5.3-4 8.5s4 3.9 4 8.5"/>',
    'select': '<rect x="3.5" y="4.5" width="14" height="11" rx="1.5" stroke-dasharray="2.5 2.3"/><path d="M13.5 12.5l7 2.8-3 1.2-1.2 3z"/>',
    'front': '<rect x="3.5" y="3.5" width="17" height="17" rx="1.5"/><rect x="8.5" y="8.5" width="7" height="7" rx="1"/>'
             '<path d="M3.5 3.5l5 5M20.5 3.5l-5 5M3.5 20.5l5-5M20.5 20.5l-5-5"/>',
    'side': '<path d="M3.5 4.5 20.5 10M3.5 19.5 20.5 14M3.5 4.5v15M10 6.6v10.8M15.5 8.4v7.2"/>',
    'fit': '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/><circle cx="12" cy="12" r="1.6"/>',
    'play': '<path d="M8 5.5v13l10.5-6.5z"/>',
    'pause': '<path d="M9 5.5v13M15 5.5v13"/>',
    'tour': '<circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M8 19h7.5a3.5 3.5 0 0 0 0-7h-7a3.5 3.5 0 0 1 0-7H16"/>',
    'power': '<path d="M12 3.5v8"/><path d="M7.05 6.6a7 7 0 1 0 9.9 0"/>',
    'skip': '<path d="M6 5.5l9 6.5-9 6.5zM18.5 5.5v13"/>',
    'voice': '<path d="M4 10.5v3M8 7.5v9M12 4.5v15M16 8v8M20 10.5v3"/>',
    'volume': '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11"/>',
    'search': '<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5 5"/>',
    'menu': '<path d="M4 7h16M4 12h16M4 17h16"/>',
    'panel': '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M9.5 4.5v15M5.8 8.5h1.6M5.8 11.5h1.6"/>',
    'telescope': '<path d="M3 13.6 15 8l1.6 3.5-12 5.6zM15 8l3.9-1.8 1.6 3.5-3.9 1.8M10.6 15.3 7.5 21M11.7 14.8l2.8 6.2"/>',
    'pulse': '<path d="M3 12h4l2.2-5.5 3.6 11 2.4-7.5 1.6 2H21"/>',
    'book': '<path d="M4 5.5c3-1.2 5.6-.9 8 .9 2.4-1.8 5-2.1 8-.9v13c-3-1.2-5.6-.9-8 .9-2.4-1.8-5-2.1-8-.9zM12 6.4v13"/>',
}
SPRITE = ('<svg class="ico-sprite" width="0" height="0" aria-hidden="true" focusable="false">'
          + ''.join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items()) + '</svg>')


def icon(name, extra=''):
    assert name in ICONS, name
    return f'<svg class="ico{" " + extra if extra else ""}" aria-hidden="true" focusable="false"><use href="#i-{name}"/></svg>'


def head():
    return f'<link rel="stylesheet" href="site.css"><link rel="icon" href="{ICON}">'


# The pages where the radio reads aloud. Its switch sits in the same place on each: the top right of the header.
RADIO_PAGES = ('telescope', 'pulses', 'radio')
RADIO_SWITCH = ('<button type="button" id="radio" class="toggle radio-switch has-ico" aria-pressed="false" '
                'title="Hear the newspapers: point at a star or a newspaper, pick one, or select an area">' + icon('radio') + 'Radio</button>')


def header(active, stories):
    links = ''.join(f'<a href="{href}"' + (' aria-current="page"' if key == active else '') + f'>{label}</a>' for key, href, label in MENU)
    return (SPRITE + f'<a class="skip-link" href="#content">Skip to content</a>'
            f'<header class="site-header" id="site-header"><div class="site-inner">'
            f'<a class="brand" href="index.html" aria-label="Newspaper Night Sky, home">{MARK}<span>Newspaper Night Sky</span></a>'
            f'<nav class="site-nav" aria-label="Main">{links}</nav>'
            f'<form class="site-search" action="telescope.html" role="search">{icon("search")}<label class="sr-only" for="site-q">Search every story</label>'
            f'<input id="site-q" name="q" type="search" placeholder="Search {stories:,} stories" autocomplete="off" spellcheck="false"></form>'
            + (RADIO_SWITCH if active in RADIO_PAGES else '') +
            f'<button type="button" class="site-menu" aria-expanded="false" aria-controls="site-header">{icon("menu")}Menu</button>'
            f'</div></header>'
            "<script>(()=>{const h=document.getElementById('site-header'),b=h.querySelector('.site-menu');"
            "b.addEventListener('click',()=>{const o=h.classList.toggle('open');b.setAttribute('aria-expanded',String(o));});})();</script>"
            '<div id="content" tabindex="-1"></div>')


def footer(release):
    links = [('index.html', 'Home'), ('telescope.html', 'Telescope'), ('pulses.html', 'Pulses'), ('radio.html', 'Radio'), ('method.html', 'How it works'),
             ('notes.html', 'Research notes'), ('exhibit.html', 'Exhibition mode'), (f'{REPO}/tree/main/data', 'Data release'), (REPO, 'Code')]
    nav = ''.join(f'<a href="{html.escape(h)}">{t}</a>' for h, t in links)
    return (f'<footer class="site-footer"><div class="site-inner">'
            f'<div class="foot-brand"><b>Newspaper Night Sky</b><span>American newspapers, 1770–1810, seen through one surviving archive.</span></div>'
            f'<nav aria-label="More">{nav}</nav>'
            f'<p class="foot-note">Source: Smithsonian Revolution Crossroads, drawn from the Library of Congress <i>Chronicling America</i> newspapers '
            f'(Hugging Face dataset <code>RevolutionCrossroads/loc_chronicling_america_1770-1810</code>, pinned revision). '
            f'Reviewed stories were read and checked against the page scans; matched stories were found automatically by shared wording and are not checked. '
            f'Data foundation v{html.escape(release)}.</p></div></footer>')


def fill(page_html, active, release, stories):
    """Insert the shared head, header and footer; give <body> a page class."""
    out = (page_html.replace('__SITE_HEAD__', head()).replace('__SITE_HEADER__', header(active, stories))
           .replace('__SITE_FOOTER__', footer(release)).replace('<body>', f'<body class="page-{active}">', 1))
    out = re.sub(r'__ICON_([a-z]+)__', lambda m: icon(m.group(1)), out)
    for marker in ('__SITE_HEAD__', '__SITE_HEADER__', '__SITE_FOOTER__', '__ICON_'):
        assert marker not in out, marker
    return out

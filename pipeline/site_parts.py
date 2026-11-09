"""Shared site parts for Newspaper Night Sky: one header and one footer for every page.

Templates carry three placeholders, filled by work/build_pulse_explorer.py through fill():
  __SITE_HEAD__    stylesheet and icon links, in <head>
  __SITE_HEADER__  brand, main menu (current page marked) and the search box
  __SITE_FOOTER__  more links, the data source and the release
Because every page gets its header and footer from here, they cannot drift apart.
"""
import html

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


def head():
    return f'<link rel="stylesheet" href="site.css"><link rel="icon" href="{ICON}">'


# The pages where the radio reads aloud. Its switch sits in the same place on each: the top right of the header.
RADIO_PAGES = ('telescope', 'pulses', 'radio')
RADIO_SWITCH = ('<button type="button" id="radio" class="toggle radio-switch" aria-pressed="false" '
                'title="Read the newspapers aloud, in your browser\'s own voice">Radio</button>')


def header(active, stories):
    links = ''.join(f'<a href="{href}"' + (' aria-current="page"' if key == active else '') + f'>{label}</a>' for key, href, label in MENU)
    return (f'<a class="skip-link" href="#content">Skip to content</a>'
            f'<header class="site-header" id="site-header"><div class="site-inner">'
            f'<a class="brand" href="index.html" aria-label="Newspaper Night Sky, home">{MARK}<span>Newspaper Night Sky</span></a>'
            f'<nav class="site-nav" aria-label="Main">{links}</nav>'
            f'<form class="site-search" action="telescope.html" role="search"><label class="sr-only" for="site-q">Search every story</label>'
            f'<input id="site-q" name="q" type="search" placeholder="Search {stories:,} stories" autocomplete="off" spellcheck="false"></form>'
            + (RADIO_SWITCH if active in RADIO_PAGES else '') +
            f'<button type="button" class="site-menu" aria-expanded="false" aria-controls="site-header">Menu</button>'
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
    for marker in ('__SITE_HEAD__', '__SITE_HEADER__', '__SITE_FOOTER__'):
        assert marker not in out, marker
    return out

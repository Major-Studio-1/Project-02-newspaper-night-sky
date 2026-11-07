"""Shared site parts for Newspaper Pulsar: one header and one footer for every page.

Templates carry three placeholders, filled by work/build_pulse_explorer.py through fill():
  __SITE_HEAD__    stylesheet and icon links, in <head>
  __SITE_HEADER__  brand, main menu (current page marked) and the search box
  __SITE_FOOTER__  more links, the data source and the release
Because every page gets its header and footer from here, they cannot drift apart.
"""
import html

# Public repository: a curated export of this project, made by work/export_public_repo.py.
REPO = 'https://github.com/Major-Studio-1/Project-02-newspaper-pulsar'
# Where GitHub Pages serves that repository's site/ folder.
PAGES = 'https://major-studio-1.github.io/Project-02-newspaper-pulsar/'
# The course repository keeps the proposal as submitted on 1 November 2026, at this commit.
PROPOSAL = 'https://github.com/Major-Studio-1/Project-02-newspapers/tree/85ba363414d55edd68c96fef4b9ee944b99acef1'
MENU = [('telescope', 'telescope.html', 'Telescope'), ('pulses', 'pulses.html', 'Pulses'), ('method', 'method.html', 'How it works')]
# A pulsar: a bright core with two beams.
MARK = ('<svg class="brand-mark" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3.4" fill="currentColor"/>'
        '<path d="M12 1.5v6.2M12 16.3v6.2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>'
        '<circle cx="12" cy="12" r="7" fill="none" stroke="currentColor" stroke-opacity=".35" stroke-width="1"/></svg>')
ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect width='24' height='24' rx='5' fill='%23050711'/%3E"
        "%3Ccircle cx='12' cy='12' r='3.4' fill='%238ccfff'/%3E%3Cpath d='M12 2v6M12 16v6' stroke='%238ccfff' stroke-width='1.8' stroke-linecap='round'/%3E%3C/svg%3E")


def head():
    return f'<link rel="stylesheet" href="site.css"><link rel="icon" href="{ICON}">'


def header(active, stories):
    links = ''.join(f'<a href="{href}"' + (' aria-current="page"' if key == active else '') + f'>{label}</a>' for key, href, label in MENU)
    return (f'<header class="site-header" id="site-header"><div class="site-inner">'
            f'<a class="brand" href="index.html" aria-label="Newspaper Pulsar, home">{MARK}<span>Newspaper Pulsar</span></a>'
            f'<nav class="site-nav" aria-label="Main">{links}</nav>'
            f'<form class="site-search" action="telescope.html" role="search"><label class="sr-only" for="site-q">Search every story</label>'
            f'<input id="site-q" name="q" type="search" placeholder="Search {stories:,} stories" autocomplete="off" spellcheck="false"></form>'
            f'<button type="button" class="site-menu" aria-expanded="false" aria-controls="site-header">Menu</button>'
            f'</div></header>'
            "<script>(()=>{const h=document.getElementById('site-header'),b=h.querySelector('.site-menu');"
            "b.addEventListener('click',()=>{const o=h.classList.toggle('open');b.setAttribute('aria-expanded',String(o));});})();</script>")


def footer(release):
    links = [('index.html', 'Home'), ('telescope.html', 'Telescope'), ('pulses.html', 'Pulses'), ('method.html', 'How it works'),
             ('notes.html', 'Research notes'), (f'{REPO}/tree/main/data', 'Data release'), (REPO, 'Code')]
    nav = ''.join(f'<a href="{html.escape(h)}">{t}</a>' for h, t in links)
    return (f'<footer class="site-footer"><div class="site-inner">'
            f'<div class="foot-brand"><b>Newspaper Pulsar</b><span>American newspapers, 1770–1810, seen through one surviving archive.</span></div>'
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

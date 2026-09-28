#!/usr/bin/env python3
"""Static checks for the Sift site. Standard library only.

    python3 tools/check_site.py

Checks every HTML file for broken internal links, and every localized page
for the things that are easy to get wrong by hand: lang/dir, hreflang
alternates, canonical, the language switchers, same-language navigation,
the translation notice on legal pages, and structural parity with English
(same number of headings, list items, table rows and FAQ entries).
Exits non-zero on the first run with any failure.
"""
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://engrtitooo.github.io/sift/'
EMAIL = 'eaeltayb@gmail.com'

LANGS = {  # folder code -> (html lang, dir)
    'en': ('en', 'ltr'),
    'ar': ('ar', 'rtl'),
    'es': ('es', 'ltr'),
    'pt': ('pt-BR', 'ltr'),
    'fr': ('fr', 'ltr'),
}
HREFLANG = {'en': 'en', 'ar': 'ar', 'es': 'es', 'pt': 'pt-BR', 'fr': 'fr'}
PAGES = ['index', 'privacy', 'terms', 'support']
LEGAL = {'privacy', 'terms'}
OLD_URLS = ['index.html', 'privacy.html', 'terms.html', 'support.html', 'privacy-ar.html', 'terms-ar.html']
REDIRECTS = {'privacy-ar.html': 'ar/privacy.html', 'terms-ar.html': 'ar/terms.html'}

failures = []


def fail(where, msg):
    failures.append(f'{where}: {msg}')


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.html_attrs = {}
        self.links = []          # (tag, attr, value, context)
        self.alternates = {}
        self.canonical = None
        self.title = ''
        self.description = None
        self.refresh = None
        self.counts = {}
        self.stack = []          # open element contexts: 'header', 'footer', 'xlate', 'chooser'
        self.switchers = []      # list of {'current': [...], 'links': [(lang, href)]}
        self._in_title = False
        self._switcher = None
        self._switch_depth = 0
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get('class', '') or ''
        if tag == 'html':
            self.html_attrs = a
        if tag in ('h2', 'h3', 'li', 'tr', 'details', 'td', 'th'):
            self.counts[tag] = self.counts.get(tag, 0) + 1
        if tag == 'title':
            self._in_title = True
        if tag == 'meta' and a.get('name') == 'description':
            self.description = a.get('content')
        if tag == 'meta' and (a.get('http-equiv') or '').lower() == 'refresh':
            self.refresh = a.get('content')
        if tag == 'link' and a.get('rel') == 'alternate':
            self.alternates[a.get('hreflang')] = a.get('href')
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical = a.get('href')
        if tag == 'script' and a.get('src'):
            self.scripts.append(a['src'])

        ctx = None
        if tag in ('header', 'footer'):
            ctx = tag
        elif 'xlate' in cls.split():
            ctx = 'xlate'
        elif 'chooser' in cls.split():
            ctx = 'chooser'
        self.stack.append(ctx)

        if 'langbar' in cls.split():
            self._switcher = {'current': [], 'links': [], 'where': self._where()}
            self._switch_depth = len(self.stack)
        if self._switcher is not None and tag == 'span' and a.get('aria-current') == 'page':
            self._switcher['current'].append(True)
        if self._switcher is not None and tag == 'a':
            self._switcher['links'].append((a.get('data-lang'), a.get('href'), a.get('hreflang'), a.get('lang')))

        for attr in ('href', 'src'):
            if attr in a and tag in ('a', 'link', 'script', 'img'):
                if tag == 'link' and a.get('rel') in ('alternate', 'canonical'):
                    continue
                self.links.append((tag, attr, a[attr], self._where(), a))

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False
        if self.stack:
            self.stack.pop()
        if self._switcher is not None and len(self.stack) < self._switch_depth:
            self.switchers.append(self._switcher)
            self._switcher = None

    def handle_data(self, data):
        if self._in_title:
            self.title += data

    def _where(self):
        for c in reversed(self.stack):
            if c:
                return c
        return 'main'


def parse(path):
    p = Page()
    with open(path, encoding='utf-8') as f:
        p.feed(f.read())
    return p


def resolve(from_file, href):
    """Map an href to a repo file path, or None for external/mailto."""
    if href.startswith(('mailto:', 'tel:', '#')):
        return None
    if href.startswith(BASE):
        rel = href[len(BASE):]
        target = os.path.join(ROOT, rel)
    elif re.match(r'^[a-z]+:', href) or href.startswith('//'):
        return None
    else:
        path = urlsplit(href).path
        target = os.path.normpath(os.path.join(os.path.dirname(from_file), path))
        if href.endswith('/') or path in ('', '.', './'):
            target = os.path.join(target, '')
    if target.endswith(os.sep) or os.path.isdir(target):
        target = os.path.join(target, 'index.html')
    return os.path.normpath(target)


def page_file(lang, page):
    return os.path.join(ROOT, '' if lang == 'en' else lang, page + '.html')


def page_url(lang, page):
    return BASE + ('' if lang == 'en' else lang + '/') + ('' if page == 'index' else page + '.html')


def lang_of_file(path):
    rel = os.path.relpath(path, ROOT)
    head = rel.split(os.sep)[0]
    return head if head in LANGS else 'en'


def main():
    html_files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        html_files += [os.path.join(dirpath, f) for f in filenames if f.endswith('.html')]

    parsed = {f: parse(f) for f in sorted(html_files)}
    checked_links = 0

    # 1. Every internal link resolves to a file, on every HTML file.
    for f, p in parsed.items():
        rel = os.path.relpath(f, ROOT)
        for tag, attr, value, where, a in p.links:
            target = resolve(f, value)
            if target is None:
                if value.startswith('mailto:') and value != 'mailto:' + EMAIL:
                    fail(rel, f'unexpected mailto {value}')
                continue
            checked_links += 1
            if not target.startswith(ROOT) or not os.path.isfile(target):
                fail(rel, f'broken {tag}[{attr}] -> {value}')
            if re.search(r'(privacy|terms)-ar\.html', value):
                fail(rel, f'link to a retired URL: {value}')
        for hreflang, href in p.alternates.items():
            t = resolve(f, href)
            if t is None or not os.path.isfile(t):
                fail(rel, f'hreflang {hreflang} -> missing {href}')
        if p.canonical:
            t = resolve(f, p.canonical)
            if t is None or not os.path.isfile(t):
                fail(rel, f'canonical -> missing {p.canonical}')

    # 2. The 20 localized pages.
    en_counts = {}
    for page in PAGES:
        en_counts[page] = parsed[page_file('en', page)].counts
    for lang, (html_lang, direction) in LANGS.items():
        for page in PAGES:
            f = page_file(lang, page)
            rel = os.path.relpath(f, ROOT)
            if f not in parsed:
                fail(rel, 'missing page')
                continue
            p = parsed[f]
            if p.html_attrs.get('lang') != html_lang:
                fail(rel, f'lang={p.html_attrs.get("lang")!r}, want {html_lang!r}')
            if p.html_attrs.get('dir') != direction:
                fail(rel, f'dir={p.html_attrs.get("dir")!r}, want {direction!r}')
            is_root_home = lang == 'en' and page == 'index'
            if ('data-home' in p.html_attrs) != is_root_home:
                fail(rel, 'data-home="root" must be on the root home page and nowhere else')
            if not p.title.strip():
                fail(rel, 'empty <title>')
            if not (p.description or '').strip():
                fail(rel, 'empty meta description')
            if lang != 'en':
                en = parsed[page_file('en', page)]
                if p.title.strip() == en.title.strip() and page != 'index':
                    fail(rel, 'title not translated')
                if p.description == en.description:
                    fail(rel, 'description not translated')

            want = {HREFLANG[l]: page_url(l, page) for l in LANGS}
            want['x-default'] = page_url('en', page)
            if p.alternates != want:
                fail(rel, f'hreflang alternates wrong: {p.alternates}')
            if p.canonical != page_url(lang, page):
                fail(rel, f'canonical {p.canonical}')

            # Language switchers: one in the header, one in the footer.
            where = [s['where'] for s in p.switchers]
            if where.count('header') != 1 or where.count('footer') != 1:
                fail(rel, f'switchers found in {where}, want one header + one footer')
            for s in p.switchers:
                if len(s['current']) != 1:
                    fail(rel, f'{s["where"]} switcher: {len(s["current"])} current markers')
                langs_linked = sorted(l for l, _, _, _ in s['links'])
                if langs_linked != sorted(l for l in LANGS if l != lang):
                    fail(rel, f'{s["where"]} switcher links {langs_linked}')
                for data_lang, href, hreflang, lang_attr in s['links']:
                    target = resolve(f, href)
                    if target != page_file(data_lang, page):
                        fail(rel, f'{s["where"]} switcher {data_lang} -> {href} is not the same page')
                    if hreflang != HREFLANG[data_lang] or lang_attr != HREFLANG[data_lang]:
                        fail(rel, f'{s["where"]} switcher {data_lang} lang/hreflang attrs')

            # Navigation stays in the page's own language.
            for tag, attr, value, ctx, a in p.links:
                if tag != 'a' or 'data-lang' in a or ctx in ('xlate', 'chooser'):
                    continue
                target = resolve(f, value)
                if target is None or not target.endswith('.html'):
                    continue
                if os.path.relpath(target, ROOT) in REDIRECTS:
                    continue
                if lang_of_file(target) != lang:
                    fail(rel, f'{ctx} link {value} leaves the {lang} site')

            # Translation notice on non-English legal pages, linking to English.
            xl = [v for t, _, v, ctx, _ in p.links if ctx == 'xlate']
            if page in LEGAL and lang != 'en':
                if len(xl) != 1 or resolve(f, xl[0]) != page_file('en', page):
                    fail(rel, f'translation notice missing or wrong: {xl}')
            elif xl:
                fail(rel, 'unexpected translation notice')

            # Structural parity with English.
            if lang != 'en':
                for k in ('h2', 'h3', 'li', 'tr', 'td', 'details'):
                    a_, b_ = p.counts.get(k, 0), en_counts[page].get(k, 0)
                    if a_ != b_:
                        fail(rel, f'{k} count {a_} != English {b_}')

            text = open(f, encoding='utf-8').read()
            if EMAIL not in text:
                fail(rel, 'contact e-mail missing')
            if lang != 'ar' and 'Eltayeb Mohammed' not in text:
                fail(rel, 'developer name missing')
            if lang == 'ar' and 'الطيب محمد' not in text:
                fail(rel, 'developer name missing')
            if page == 'privacy' and not re.search(r'26.{1,20}2026', text):
                fail(rel, 'effective date 26 September 2026 missing')
            if page == 'terms' and '2026' not in text:
                fail(rel, 'effective date missing')
            want_script = ('' if lang == 'en' else '../') + 'assets/lang.js'
            if p.scripts != [want_script]:
                fail(rel, f'scripts {p.scripts}')

    # 3. Old URLs still resolve; the Arabic ones redirect.
    for old in OLD_URLS:
        if not os.path.isfile(os.path.join(ROOT, old)):
            fail(old, 'old URL no longer exists')
    for old, target in REDIRECTS.items():
        p = parsed.get(os.path.join(ROOT, old))
        text = open(os.path.join(ROOT, old), encoding='utf-8').read()
        if not p or p.refresh != f'0; url={target}':
            fail(old, f'meta refresh {p.refresh if p else None}')
        if f"location.replace('{target}'" not in text:
            fail(old, 'JS redirect missing')
        if not any(v == target for _, _, v, _, _ in p.links):
            fail(old, 'visible fallback link missing')

    print(f'{len(parsed)} HTML files, {checked_links} internal links checked')
    if failures:
        print(f'{len(failures)} problem(s):')
        for msg in failures:
            print('  ' + msg)
        return 1
    print('all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())

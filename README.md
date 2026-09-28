# Sift — Privacy Policy, Terms & Support

The public legal and support pages for **Sift**, an iOS app that reads the
screenshots already on your phone and tells you what is inside them.

Published with GitHub Pages. Plain HTML, one stylesheet and one small script —
no build step, no dependencies, no trackers, nothing to install.

## Languages and layout

Every page exists in the app's five languages. English stays at the root so
the URLs registered in App Store Connect never change.

| | English | العربية | Español | Português (BR) | Français |
| --- | --- | --- | --- | --- | --- |
| Home | `index.html` | `ar/index.html` | `es/index.html` | `pt/index.html` | `fr/index.html` |
| Privacy Policy | `privacy.html` | `ar/privacy.html` | `es/privacy.html` | `pt/privacy.html` | `fr/privacy.html` |
| Terms of Use | `terms.html` | `ar/terms.html` | `es/terms.html` | `pt/terms.html` | `fr/terms.html` |
| Support | `support.html` | `ar/support.html` | `es/support.html` | `pt/support.html` | `fr/support.html` |

`privacy-ar.html` and `terms-ar.html` are kept as redirects to `ar/privacy.html`
and `ar/terms.html` (meta refresh, JavaScript, and a visible link).

Shared files:

- `assets/site.css` — the stylesheet. Logical properties only, so Arabic
  mirrors from the same rules.
- `assets/lang.js` — language choice. Clicking any language link remembers it
  in `localStorage` (`sift_lang`). Only the root `index.html` ever redirects
  (`<html data-home="root">`): a remembered choice or `?lang=xx` sends the
  reader to that language's home. Legal and support pages never redirect.
- `assets/icon.svg` — the favicon.

Every page carries `hreflang` alternates for all five languages plus
`x-default` (English), and a language switcher in its header and footer that
links to the same page in the other languages. Non-English privacy and terms
pages say that the English version applies if the translation differs.

## Editing

When a page changes, change it in all five languages. Then run:

```sh
python3 tools/check_site.py
```

It checks every internal link and, for all 20 pages, `lang`/`dir`, the
`hreflang` set, the switchers, same-language navigation, the translation
notice, and that each translation has the same number of headings, list
items, table rows and FAQ entries as the English page.

## Publishing

Settings → Pages → Build and deployment → Deploy from a branch →
`main` / `/ (root)`. The URLs App Store Connect asks for:

- Privacy Policy: `https://engrtitooo.github.io/sift/privacy.html`
  (per localization: `…/sift/ar/privacy.html`, `…/es/…`, `…/pt/…`, `…/fr/…`)
- Support: `https://engrtitooo.github.io/sift/support.html`

## About the policy

Every data-handling claim on these pages was checked against the Sift source
code rather than written from what the app is supposed to do. The short
version: no account, screenshots are sent to our server and Google's Gemini API to be read, then
discarded rather than stored on our servers, results stay on the device, and there is no analytics SDK, no crash
reporter and no tracking of any kind.

Developer: Eltayeb Mohammed · <eaeltayb@gmail.com>

/* Sift — language choice. Plain script, no dependencies, no tracking.
 *
 * Every language link on the site is an ordinary <a href>, so the site works
 * with JavaScript off. This script only adds two things:
 *
 *   1. Clicking a language link (header, footer or home-page chooser)
 *      remembers the choice in localStorage under "sift_lang".
 *   2. On the root home page only — <html data-home="root"> — a remembered
 *      choice, or ?lang=xx, sends the reader to that language's home page.
 *
 * No other page ever redirects. Legal and support pages always render
 * exactly what their URL names, whatever is stored.
 */
(function () {
  'use strict';

  var KEY = 'sift_lang';
  var LANGS = ['en', 'ar', 'es', 'pt', 'fr'];
  var root = document.documentElement;

  function valid(lang) {
    return LANGS.indexOf(lang) !== -1;
  }

  // "pt-BR" -> "pt", "es_419" -> "es", "FR" -> "fr"; anything else -> null.
  function normalise(value) {
    var code = String(value || '').toLowerCase().split(/[-_]/)[0];
    return valid(code) ? code : null;
  }

  function load() {
    try {
      return normalise(window.localStorage.getItem(KEY));
    } catch (e) {
      return null;
    }
  }

  function save(lang) {
    try {
      window.localStorage.setItem(KEY, lang);
    } catch (e) {
      /* Storage blocked (private mode, disabled cookies): links still work. */
    }
  }

  function fromQuery() {
    var match = /[?&]lang=([^&#]*)/.exec(window.location.search);
    return match ? normalise(decodeURIComponent(match[1])) : null;
  }

  function suggested() {
    var list = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || 'en'];
    for (var i = 0; i < list.length; i++) {
      var lang = normalise(list[i]);
      if (lang) return lang;
    }
    return 'en';
  }

  document.addEventListener('click', function (event) {
    var node = event.target;
    while (node && node !== document) {
      if (node.nodeName === 'A' && node.hasAttribute('data-lang')) {
        var lang = normalise(node.getAttribute('data-lang'));
        if (lang) save(lang);
        return;
      }
      node = node.parentNode;
    }
  });

  if (root.getAttribute('data-home') !== 'root') return;

  /* ---------------------------------------------------- root home page only */

  var override = fromQuery();
  if (override) save(override);
  var chosen = override || load();

  if (chosen && chosen !== 'en') {
    root.classList.add('lang-redirecting');
    window.location.replace(chosen + '/');
    return;
  }

  if (chosen === 'en') {
    root.classList.add('lang-chosen');
    return;
  }

  // First visit: the chooser is already on the page; mark the likely pick.
  function highlight() {
    var pick = document.querySelector('.chooser a[data-lang="' + suggested() + '"]');
    if (pick) pick.classList.add('is-suggested');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', highlight);
  } else {
    highlight();
  }
})();

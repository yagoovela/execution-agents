/**
 * Shared EN/PT language switcher for the execution-agents docs.
 *
 * Every switchable text lives on an element with `data-en` and `data-pt`
 * attributes. This script swaps the element's innerHTML based on the current
 * language selection, persists it in localStorage under `flux-lang`, and
 * mirrors the aria-pressed state on the .lang-sw buttons.
 *
 * Usage — add to every doc:
 *
 *   <link rel="stylesheet" href="_assets/i18n.css">
 *   <script src="_assets/i18n.js" defer></script>
 *
 *   <div class="lang-sw" role="group" aria-label="Language">
 *     <button type="button" data-lang="en" aria-pressed="true">EN-US</button>
 *     <button type="button" data-lang="pt" aria-pressed="false">PT-BR</button>
 *   </div>
 *
 * Adjust the relative path to _assets/ depending on the doc's depth
 * (../_assets/ from timeline/ or passos/, _assets/ from the root).
 */
(function () {
  function init() {
    var nodes = document.querySelectorAll('[data-en]');
    var buttons = document.querySelectorAll('.lang-sw button');

    function apply(lang) {
      nodes.forEach(function (el) {
        var value = el.getAttribute('data-' + lang);
        if (value === null) return;
        el.innerHTML = value;
      });
      buttons.forEach(function (b) {
        b.setAttribute('aria-pressed', String(b.getAttribute('data-lang') === lang));
      });
      document.documentElement.lang = lang === 'pt' ? 'pt-BR' : 'en';
      try { localStorage.setItem('flux-lang', lang); } catch (e) { /* ignore */ }
    }

    buttons.forEach(function (b) {
      b.addEventListener('click', function () { apply(b.getAttribute('data-lang')); });
    });

    var saved = null;
    try { saved = localStorage.getItem('flux-lang'); } catch (e) { /* ignore */ }
    apply(saved === 'pt' ? 'pt' : 'en');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

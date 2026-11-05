(function () {
  'use strict';
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('main-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) {
        nav.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.focus();
      }
    });
    nav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        nav.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // Remember the visitor's language choice for the root redirect hint.
  try {
    var lang = document.documentElement.lang;
    if (lang) { localStorage.setItem('ayyildiz_lang', lang); }
  } catch (e) { /* storage unavailable */ }

  // Lightweight click tracking hooks (gtag/GA4 if present).
  function track(name, params) {
    if (typeof window.gtag === 'function') { window.gtag('event', name, params || {}); }
  }
  document.querySelectorAll('a[href^="https://wa.me"]').forEach(function (a) {
    a.addEventListener('click', function () { track('whatsapp_click', { location: a.className }); });
  });
  document.querySelectorAll('a[href^="tel:"]').forEach(function (a) {
    a.addEventListener('click', function () { track('phone_click', { number: a.getAttribute('href') }); });
  });
})();

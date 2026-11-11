// Menu mobile + repli du sommaire sur petit écran. Aucune dépendance.
(function () {
  var btn = document.querySelector('.nav-toggle');
  var nav = document.getElementById('primary-nav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }
  var toc = document.querySelector('.toc details');
  if (toc && window.matchMedia('(max-width: 1000px)').matches) {
    toc.removeAttribute('open');
  }

  // Lecteur YouTube léger : l'iframe n'est chargée qu'au clic.
  document.addEventListener('click', function (e) {
    var b = e.target && e.target.closest && e.target.closest('.yt-lite-btn');
    if (!b) return;
    var f = document.createElement('iframe');
    f.src = 'https://www.youtube-nocookie.com/embed/' + b.getAttribute('data-yt') + '?autoplay=1&rel=0';
    f.title = b.getAttribute('aria-label');
    f.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture';
    f.allowFullscreen = true;
    b.replaceWith(f);
  });

  // Consentement cookies (voir inc/consent.php)
  var box = document.getElementById('vr-consent');
  var has = /(?:^|; )vr_consent=(granted|denied)/.test(document.cookie);
  function save(v) {
    document.cookie = 'vr_consent=' + v + '; max-age=' + (60 * 60 * 24 * 182) + '; path=/; SameSite=Lax' + (location.protocol === 'https:' ? '; Secure' : '');
    if (typeof window.gtag === 'function') { window.gtag('consent', 'update', {analytics_storage: v}); }
    if (box) { box.hidden = true; }
  }
  if (box) {
    if (!has) { box.hidden = false; }
    box.addEventListener('click', function (e) {
      var v = e.target && e.target.getAttribute('data-consent');
      if (v) { save(v); }
    });
  }
  document.addEventListener('click', function (e) {
    if (e.target && e.target.closest && e.target.closest('[data-consent-open]')) {
      e.preventDefault();
      if (box) { box.hidden = false; }
    }
  });
})();

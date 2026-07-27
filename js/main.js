// BoBBreach — Shared: nav toggle + theme
(function() {
  'use strict';

  // ── Theme ──
  (function initTheme() {
    const stored = localStorage.getItem('bobbreach-theme');
    if (stored === 'light' || stored === 'dark') {
      document.documentElement.setAttribute('data-theme', stored);
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    }
  })();

  document.getElementById('themeToggle')?.addEventListener('click', () => {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('bobbreach-theme', next);
  });

  // ── Nav ──
  document.getElementById('navToggle')?.addEventListener('click', () => {
    document.querySelector('nav .links').classList.toggle('open');
  });
  document.querySelectorAll('nav .links a').forEach(a => {
    a.addEventListener('click', () => {
      document.querySelector('nav .links')?.classList.remove('open');
    });
  });

  // ── Scroll spy for anchor nav (index page only) ──
  const sections = document.querySelectorAll('.anchor[id]');
  const navAnchors = document.querySelectorAll('nav .links a[href^="#"]');
  if (sections.length && navAnchors.length) {
    function updateActiveNav() {
      const scrollY = window.scrollY + 100;
      let current = '';
      sections.forEach(s => {
        if (s.offsetTop <= scrollY && s.offsetTop + s.offsetHeight > scrollY) current = s.id;
      });
      navAnchors.forEach(a => {
        a.classList.toggle('active', a.getAttribute('href') === '#' + current);
      });
    }
    window.addEventListener('scroll', updateActiveNav);
    updateActiveNav();
  }
})();

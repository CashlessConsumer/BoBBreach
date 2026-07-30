// BoBBreach — Shared: nav toggle, disclosure, theme, sidebar

(function() {
  'use strict';

  // ── Sidebar toggle ──
  const sidebar = document.getElementById('sidebar');
  const sidebarToggles = document.querySelectorAll('.nav-toggle-sidebar, .sidebar-overlay');
  const navToggle = document.getElementById('navToggle');

  function toggleSidebar(open) {
    if (!sidebar) return;
    const overlay = document.querySelector('.sidebar-overlay');
    sidebar.classList.toggle('open', open);
    if (overlay) overlay.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
  }

  sidebarToggles.forEach(el => {
    el.addEventListener('click', function(e) {
      const isOpen = sidebar && sidebar.classList.contains('open');
      toggleSidebar(!isOpen);
    });
  });

  // Close sidebar on nav link click (mobile)
  if (sidebar) {
    sidebar.querySelectorAll('.nav-links a').forEach(a => {
      a.addEventListener('click', () => toggleSidebar(false));
    });
  }

  // Legacy hamburger still works
  if (navToggle && sidebar) {
    navToggle.addEventListener('click', () => {
      const isOpen = sidebar.classList.contains('open');
      toggleSidebar(!isOpen);
    });
  }

  // ── Update active nav link ──
  function updateActiveNav() {
    const currentPath = window.location.pathname;
    const currentPage = currentPath.split('/').pop() || 'index.html';

    document.querySelectorAll('.nav-links a').forEach(a => {
      const href = a.getAttribute('href');
      if (!href) return;
      const linkPage = href.split('/').pop();
      a.classList.toggle('active', linkPage === currentPage);
    });

    // Top header section links
    const section = window.location.hash;
    document.querySelectorAll('.top-header a').forEach(a => {
      const ahref = a.getAttribute('href');
      if (ahref && ahref.startsWith('#')) {
        a.classList.toggle('active', ahref === section);
      }
    });
  }

  // ── Theme ──
  const themeToggle = document.getElementById('themeToggle');
  const themeBtnSidebar = document.querySelector('.sidebar .theme-btn');
  const html = document.documentElement;
  const themeIcon = document.getElementById('themeIcon');

  function setTheme(mode) {
    html.setAttribute('data-theme', mode);
    localStorage.setItem('bob-theme', mode);
    if (themeIcon) {
      themeIcon.innerHTML = mode === 'dark'
        ? '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'
        : '<circle cx="12" cy="12" r="5"/><g stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></g>';
    }
    // sync sidebar button icon
    if (themeBtnSidebar) {
      themeBtnSidebar.innerHTML = mode === 'dark' ? '🌙' : '☀️';
    }
  }

  const saved = localStorage.getItem('bob-theme');
  setTheme(saved || 'dark');

  function toggleTheme() {
    const current = html.getAttribute('data-theme');
    setTheme(current === 'dark' ? 'light' : 'dark');
  }

  if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
  if (themeBtnSidebar) themeBtnSidebar.addEventListener('click', toggleTheme);

  // ── Disclosure ──
  document.querySelector('.disclosure summary')?.addEventListener('click', function(e) {
    const details = this.closest('details');
    if (details) {
      const toggle = details.querySelector('.d-toggle');
      if (toggle) toggle.textContent = details.open ? '▾' : '▸';
    }
  });

  // ── Init ──
  document.addEventListener('DOMContentLoaded', function() {
    updateActiveNav();
    // Close sidebar on escape
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && sidebar && sidebar.classList.contains('open')) {
        toggleSidebar(false);
      }
    });
  });

  window.addEventListener('hashchange', updateActiveNav);
})();

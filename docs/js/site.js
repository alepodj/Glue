window.GLUE_SITE = {
  version: '0.6.6',
  github: 'https://github.com/alepodj/Glue',
  pypi: 'https://pypi.org/project/glue-ui/',
  nav: [
    { href: 'index.html', id: 'home', label: 'Home' },
    { href: 'documentation.html', id: 'documentation', label: 'Documentation' },
    { href: 'api.html', id: 'api', label: 'API' },
    { href: 'examples.html', id: 'examples', label: 'Examples' },
    { href: 'projects.html', id: 'projects', label: 'Projects' },
    { href: 'developers.html', id: 'developers', label: 'Developers' },
  ],
};

(function () {
  'use strict';

  const page = document.body.getAttribute('data-page') || 'home';

  function mountNav() {
    const host = document.getElementById('site-nav');
    if (!host) return;

    const links = window.GLUE_SITE.nav
      .map((item) => {
        const active = item.id === page ? ' is-active' : '';
        return (
          '<a class="site-nav__link' +
          active +
          '" href="' +
          item.href +
          '"' +
          (item.id === page ? ' aria-current="page"' : '') +
          '>' +
          item.label +
          '</a>'
        );
      })
      .join('');

    host.innerHTML =
      '<div class="site-nav__inner">' +
      '<a class="site-nav__brand" href="index.html">' +
      '<img src="assets/logo.png" width="36" height="36" alt="" />' +
      '<span>Glue</span>' +
      '</a>' +
      '<button type="button" class="site-nav__toggle" id="nav-toggle" aria-expanded="false" aria-controls="nav-links">Menu</button>' +
      '<nav class="site-nav__links" id="nav-links">' +
      links +
      '<a class="site-nav__cta" href="' +
      window.GLUE_SITE.github +
      '" target="_blank" rel="noopener">GitHub</a>' +
      '</nav>' +
      '</div>';

    const toggle = document.getElementById('nav-toggle');
    const linksEl = document.getElementById('nav-links');
    if (toggle && linksEl) {
      toggle.addEventListener('click', () => {
        const open = linksEl.classList.toggle('is-open');
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    }
  }

  function enhanceCode() {
    if (!document.body.classList.contains('layout-docs')) return;
    document.querySelectorAll('.docs-section pre > code').forEach((code) => {
      const pre = code.parentElement;
      if (!pre || pre.querySelector('.code-copy')) return;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'code-copy';
      btn.textContent = 'Copy';
      btn.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(code.textContent || '');
          btn.textContent = 'Copied';
          setTimeout(() => {
            btn.textContent = 'Copy';
          }, 1400);
        } catch (_) {
          btn.textContent = 'Failed';
        }
      });
      pre.classList.add('has-copy');
      pre.appendChild(btn);
    });
  }

  function setupStartOptionsModal() {
    const openBtn = document.getElementById('start-options-expand');
    const modal = document.getElementById('start-options-modal');
    if (!openBtn || !modal) return;
    const panel = modal.querySelector('.modal-panel');
    const closeEls = modal.querySelectorAll('[data-close-modal]');
    const open = () => {
      modal.hidden = false;
      document.body.classList.add('modal-open');
      openBtn.setAttribute('aria-expanded', 'true');
    };
    const close = () => {
      modal.hidden = true;
      document.body.classList.remove('modal-open');
      openBtn.setAttribute('aria-expanded', 'false');
    };
    openBtn.addEventListener('click', open);
    closeEls.forEach((el) => el.addEventListener('click', close));
    modal.addEventListener('click', (e) => {
      if (e.target === modal) close();
    });
    if (panel) {
      panel.addEventListener('click', (e) => e.stopPropagation());
    }
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !modal.hidden) close();
    });
  }

  function highlightSideNav() {
    const links = Array.from(document.querySelectorAll('.docs-side a[href^="#"]'));
    if (!links.length || !('IntersectionObserver' in window)) return;
    const map = new Map();
    links.forEach((a) => {
      const id = a.getAttribute('href').slice(1);
      const el = document.getElementById(id);
      if (el) map.set(el, a);
    });
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const a = map.get(entry.target);
          if (!a) return;
          if (entry.isIntersecting) {
            links.forEach((l) => l.classList.remove('is-active'));
            a.classList.add('is-active');
          }
        });
      },
      { rootMargin: '-20% 0px -65% 0px', threshold: 0 }
    );
    map.forEach((_, el) => io.observe(el));
  }

  function ambientDocs() {
    if (!document.body.classList.contains('layout-docs')) return;
    const orbA = document.querySelector('.orb-a');
    const orbB = document.querySelector('.orb-b');
    if (!window.gsap || !orbA || !orbB) return;
    gsap.to(orbA, { x: 30, y: -20, duration: 16, repeat: -1, yoyo: true, ease: 'sine.inOut' });
    gsap.to(orbB, { x: -40, y: 28, duration: 20, repeat: -1, yoyo: true, ease: 'sine.inOut' });
  }

  function revealDocs() {
    if (!document.body.classList.contains('layout-docs')) return;
    if (!window.gsap || !window.ScrollTrigger) return;

    gsap.registerPlugin(ScrollTrigger);

    const items = Array.from(
      document.querySelectorAll(
        '.docs-main .docs-hero, .docs-main .docs-section, .docs-main .card'
      )
    );
    if (!items.length) return;

    items.forEach((el) => {
      gsap.set(el, { opacity: 0, y: 36 });
      ScrollTrigger.create({
        trigger: el,
        start: 'top 88%',
        once: true,
        onEnter: () => {
          gsap.to(el, {
            opacity: 1,
            y: 0,
            duration: 0.85,
            ease: 'power3.out',
            overwrite: true,
          });
        },
      });
    });

    ScrollTrigger.refresh();
  }

  document.addEventListener('DOMContentLoaded', () => {
    mountNav();
    enhanceCode();
    setupStartOptionsModal();
    highlightSideNav();
    ambientDocs();
    revealDocs();
  });
})();

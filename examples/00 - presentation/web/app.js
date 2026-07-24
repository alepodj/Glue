/* global gsap, ScrollTrigger, glue */

(function () {
  'use strict';

  gsap.registerPlugin(ScrollTrigger);

  const pageHero = document.getElementById('page-hero');
  const pageStory = document.getElementById('page-story');
  const storyScroll = document.getElementById('story-scroll');
  const scrollCue = document.getElementById('scroll-cue');
  const versionEl = document.getElementById('version');
  const logo = document.getElementById('logo');
  const brand = document.querySelector('.brand');
  const slogan = document.querySelector('.slogan');
  const orbA = document.querySelector('.orb-a');
  const orbB = document.querySelector('.orb-b');

  let onHero = true;
  let transitioning = false;
  let wheelLock = false;
  let pullAccum = 0;
  const PULL_THRESHOLD = 90;

  /* —— Ambient orbs —— */
  gsap.to(orbA, {
    x: 40,
    y: -30,
    duration: 14,
    repeat: -1,
    yoyo: true,
    ease: 'sine.inOut',
  });
  gsap.to(orbB, {
    x: -50,
    y: 40,
    duration: 18,
    repeat: -1,
    yoyo: true,
    ease: 'sine.inOut',
  });

  /* —— Hero entrance —— */
  const heroIntro = gsap.timeline({ defaults: { ease: 'power3.out' } });
  heroIntro
    .from(logo, { y: 48, opacity: 0, scale: 0.88, duration: 1.05, filter: 'blur(8px)' }, 0.1)
    .from(brand, { y: 28, opacity: 0, duration: 0.75 }, 0.35)
    .from(slogan, { y: 20, opacity: 0, duration: 0.7 }, 0.5)
    .from(scrollCue, { y: 16, opacity: 0, duration: 0.55 }, 0.75)
    .from(versionEl, { opacity: 0, duration: 0.5 }, 0.85);

  gsap.to(logo, {
    y: -10,
    duration: 3.2,
    repeat: -1,
    yoyo: true,
    ease: 'sine.inOut',
    delay: 1.2,
  });

  gsap.to('.scroll-cue__arrow', {
    y: 5,
    duration: 0.75,
    repeat: -1,
    yoyo: true,
    ease: 'sine.inOut',
  });

  gsap.fromTo(
    scrollCue,
    { boxShadow: '0 0 0 0 rgba(62,200,255,0.4)' },
    {
      boxShadow: '0 0 0 14px rgba(62,200,255,0)',
      duration: 1.5,
      repeat: -1,
      ease: 'power1.out',
    }
  );

  /* —— Version —— */
  async function loadMeta() {
    try {
      const meta = await glue.get_glue_meta()();
      versionEl.textContent = `Glue v${meta.version}`;
    } catch (_) {
      versionEl.textContent = 'Glue';
    }
  }
  loadMeta();

  /* —— Page turn —— */
  function goToStory() {
    if (!onHero || transitioning) return;
    transitioning = true;
    pullAccum = 0;

    pageStory.hidden = false;
    storyScroll.scrollTop = 0;

    const tl = gsap.timeline({
      onComplete: () => {
        onHero = false;
        transitioning = false;
        pageHero.hidden = true;
        gsap.set(pageHero, { clearProps: 'transform,opacity' });
        gsap.set(pageStory, { clearProps: 'transform,opacity' });
        refreshReveals();
        startBridgeLoop();
      },
    });

    tl.fromTo(
      pageHero,
      { yPercent: 0, opacity: 1 },
      { yPercent: -110, opacity: 0.2, duration: 0.85, ease: 'power3.inOut' },
      0
    ).fromTo(
      pageStory,
      { yPercent: 100, opacity: 0.4 },
      { yPercent: 0, opacity: 1, duration: 0.85, ease: 'power3.inOut' },
      0
    );
  }

  function goToHero() {
    if (onHero || transitioning) return;
    transitioning = true;
    pullAccum = 0;
    stopBridgeLoop();
    closeAllMenus();

    pageHero.hidden = false;

    const tl = gsap.timeline({
      onComplete: () => {
        onHero = true;
        transitioning = false;
        pageStory.hidden = true;
        gsap.set(pageHero, { clearProps: 'transform,opacity' });
        gsap.set(pageStory, { clearProps: 'transform,opacity' });
      },
    });

    tl.fromTo(
      pageStory,
      { yPercent: 0, opacity: 1 },
      { yPercent: 100, opacity: 0.25, duration: 0.85, ease: 'power3.inOut' },
      0
    ).fromTo(
      pageHero,
      { yPercent: -110, opacity: 0.2 },
      { yPercent: 0, opacity: 1, duration: 0.85, ease: 'power3.inOut' },
      0
    );
  }

  scrollCue.addEventListener('click', goToStory);

  window.addEventListener(
    'wheel',
    (e) => {
      if (transitioning || wheelLock) return;

      if (onHero) {
        if (e.deltaY > 18) {
          e.preventDefault();
          goToStory();
        }
        return;
      }

      // Story: intentional pull-up at top returns to hero
      if (storyScroll.scrollTop <= 0 && e.deltaY < -8) {
        e.preventDefault();
        pullAccum += -e.deltaY;
        if (pullAccum >= PULL_THRESHOLD) {
          goToHero();
        }
      } else {
        pullAccum = Math.max(0, pullAccum - 12);
      }
    },
    { passive: false }
  );

  // Touch / trackpad: also allow arrow key
  window.addEventListener('keydown', (e) => {
    if (transitioning) return;
    if (onHero && (e.key === 'ArrowDown' || e.key === 'PageDown' || e.key === ' ')) {
      e.preventDefault();
      goToStory();
    } else if (!onHero && e.key === 'ArrowUp' && storyScroll.scrollTop <= 0) {
      e.preventDefault();
      goToHero();
    } else if (!onHero && e.key === 'Escape') {
      goToHero();
    }
  });

  /* —— Scroll reveals + light parallax —— */
  function refreshReveals() {
    ScrollTrigger.getAll().forEach((t) => t.kill());

    gsap.utils.toArray('[data-reveal]').forEach((el) => {
      gsap.fromTo(
        el,
        { y: 56, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.9,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: el,
            scroller: storyScroll,
            start: 'top 82%',
            toggleActions: 'play none none reverse',
          },
        }
      );
    });

    gsap.utils.toArray('.panel h2').forEach((el) => {
      gsap.to(el, {
        y: -24,
        ease: 'none',
        scrollTrigger: {
          trigger: el.closest('.panel'),
          scroller: storyScroll,
          start: 'top bottom',
          end: 'bottom top',
          scrub: true,
        },
      });
    });

    ScrollTrigger.refresh();
  }

  /* —— Menubar —— */
  const toast = document.getElementById('menu-toast');
  let toastTween;

  function closeAllMenus() {
    document.querySelectorAll('.menu__panel').forEach((p) => {
      p.hidden = true;
    });
    document.querySelectorAll('.menu__btn').forEach((b) => {
      b.setAttribute('aria-expanded', 'false');
    });
  }

  function showToast(msg) {
    toast.textContent = msg;
    if (toastTween) toastTween.kill();
    toastTween = gsap.fromTo(
      toast,
      { opacity: 0, y: 6 },
      { opacity: 1, y: 0, duration: 0.25, onComplete: () => {
        toastTween = gsap.to(toast, { opacity: 0, delay: 1.6, duration: 0.4 });
      }}
    );
  }

  document.querySelectorAll('.menu__btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.getAttribute('data-menu');
      const panel = document.getElementById(`menu-${id}`);
      const open = btn.getAttribute('aria-expanded') === 'true';
      closeAllMenus();
      if (!open && panel) {
        panel.hidden = false;
        btn.setAttribute('aria-expanded', 'true');
        gsap.fromTo(panel, { y: -6, opacity: 0 }, { y: 0, opacity: 1, duration: 0.2, ease: 'power2.out' });
      }
    });
  });

  document.querySelectorAll('.menu__panel button').forEach((item) => {
    item.addEventListener('click', () => {
      const action = item.getAttribute('data-action');
      const labels = {
        new: 'File → New Window',
        open: 'File → Open…',
        quit: 'File → Quit (demo only)',
        undo: 'Edit → Undo',
        copy: 'Edit → Copy',
        paste: 'Edit → Paste',
        about: 'About Glue — web UI, Python brain',
        docs: 'Docs live with the examples',
      };
      showToast(labels[action] || action);
      closeAllMenus();
    });
  });

  document.addEventListener('click', () => closeAllMenus());

  /* —— Bridge loop —— */
  const bridgeLabel = document.getElementById('bridge-label');
  const bridgeLog = document.getElementById('bridge-log');
  const packet = document.getElementById('bridge-packet');
  const bridgeWire = document.querySelector('.bridge__wire');
  let bridgeTimer = null;
  let bridgeRunning = false;
  let msgIndex = 0;
  const messages = [
    'hello from the UI',
    'save this document',
    'list project files',
    'run a Python task',
  ];

  function setBridgeLabel(text) {
    bridgeLabel.textContent = text;
  }

  async function bridgeOnce() {
    if (!bridgeRunning) return;
    const message = messages[msgIndex % messages.length];
    msgIndex += 1;

    const jsCode = document.querySelector('#bridge-js code');
    jsCode.textContent = `glue.bridge_echo({\n  message: "${message}"\n})();`;

    setBridgeLabel('JS → Python');
    gsap.set(packet, { left: '0%', opacity: 1 });
    await gsap.to(packet, { left: '100%', duration: 0.7, ease: 'power2.inOut' });

    let result;
    try {
      result = await glue.bridge_echo({ message })();
    } catch (err) {
      result = { error: String(err) };
    }

    setBridgeLabel('Python → JS');
    const logCode = bridgeLog.querySelector('code');
    logCode.textContent = JSON.stringify(result, null, 2);
    gsap.fromTo(bridgeLog, { backgroundColor: 'rgba(62,200,255,0.18)' }, { backgroundColor: 'rgba(0,40,50,0.25)', duration: 0.8 });

    gsap.set(packet, { left: '100%' });
    await gsap.to(packet, { left: '0%', duration: 0.7, ease: 'power2.inOut' });
    setBridgeLabel('round-trip ok');
    gsap.to(packet, { opacity: 0, duration: 0.2 });

    gsap.to(bridgeWire, {
      backgroundPosition: '200% 0',
      duration: 1.2,
      ease: 'none',
    });
  }

  function startBridgeLoop() {
    if (bridgeRunning) return;
    bridgeRunning = true;
    const tick = async () => {
      if (!bridgeRunning) return;
      await bridgeOnce();
      if (bridgeRunning) {
        bridgeTimer = window.setTimeout(tick, 2200);
      }
    };
    tick();
  }

  function stopBridgeLoop() {
    bridgeRunning = false;
    if (bridgeTimer) {
      clearTimeout(bridgeTimer);
      bridgeTimer = null;
    }
  }

  /* —— Steps from Python (optional enrichment) —— */
  async function loadSteps() {
    try {
      const steps = await glue.list_simple_steps()();
      const list = document.getElementById('steps-list');
      if (!Array.isArray(steps) || !list) return;
      list.innerHTML = steps
        .map((s) => `<li><code>${s.code}</code><span>${s.note}</span></li>`)
        .join('');
    } catch (_) {
      /* keep static HTML */
    }
  }
  loadSteps();
})();

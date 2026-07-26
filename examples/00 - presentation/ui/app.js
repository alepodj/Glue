/* global gsap, ScrollTrigger, glue */

/** Exposed so Python can call into the UI (Python → JS). */
function bridge_on_js(payload) {
  var message = payload && typeof payload === 'object' ? payload.message : payload;
  return {
    ok: true,
    echo: message,
    from: 'javascript',
    at: new Date().toISOString(),
  };
}
glue.expose(bridge_on_js);

(function () {
  'use strict';

  gsap.registerPlugin(ScrollTrigger);

  const pageHero = document.getElementById('page-hero');
  const pageStory = document.getElementById('page-story');
  const storyScroll = document.getElementById('story-scroll');
  const scrollCue = document.getElementById('scroll-cue');
  const scrollCueUp = document.getElementById('scroll-cue-up');
  const versionEl = document.getElementById('version');
  const logo = document.getElementById('logo');
  const brand = document.querySelector('.brand');
  const slogan = document.querySelector('.slogan');
  const orbA = document.querySelector('.orb-a');
  const orbB = document.querySelector('.orb-b');

  let onHero = true;
  let transitioning = false;
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

  gsap.to('#scroll-cue .scroll-cue__arrow', {
    y: 5,
    duration: 0.75,
    repeat: -1,
    yoyo: true,
    ease: 'sine.inOut',
  });

  gsap.to('#scroll-cue-up .scroll-cue__arrow', {
    y: -5,
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

  if (scrollCueUp) {
    gsap.fromTo(
      scrollCueUp,
      { boxShadow: '0 0 0 0 rgba(62,200,255,0.4)' },
      {
        boxShadow: '0 0 0 14px rgba(62,200,255,0)',
        duration: 1.5,
        repeat: -1,
        ease: 'power1.out',
      }
    );
  }

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

    pageStory.classList.add('is-active');
    pageStory.setAttribute('aria-hidden', 'false');
    pageHero.classList.add('is-leaving');
    storyScroll.scrollTop = 0;

    gsap.set(pageStory, { yPercent: 100, force3D: true });
    gsap.set(pageHero, { yPercent: 0, force3D: true });
    // Flush layout so the first painted frame is already off-screen (avoids flicker)
    void pageStory.offsetHeight;

    const tl = gsap.timeline({
      defaults: { ease: 'power3.inOut', force3D: true },
      onComplete: () => {
        onHero = false;
        transitioning = false;
        gsap.set(pageHero, { yPercent: -100, visibility: 'hidden' });
        gsap.set(pageStory, { yPercent: 0, clearProps: 'transform' });
        pageHero.classList.remove('is-leaving');
        requestAnimationFrame(() => {
          refreshReveals();
          startBridgeLoop();
        });
      },
    });

    tl.to(pageHero, { yPercent: -100, duration: 0.75 }, 0)
      .to(pageStory, { yPercent: 0, duration: 0.75 }, 0);
  }

  function goToHero() {
    if (onHero || transitioning) return;
    transitioning = true;
    pullAccum = 0;
    stopBridgeLoop();
    closeAllMenus();

    pageHero.classList.add('is-leaving');
    gsap.set(pageHero, { yPercent: -100, visibility: 'visible', force3D: true });
    gsap.set(pageStory, { yPercent: 0, force3D: true });

    const tl = gsap.timeline({
      defaults: { ease: 'power3.inOut', force3D: true },
      onComplete: () => {
        onHero = true;
        transitioning = false;
        pageStory.classList.remove('is-active');
        pageStory.setAttribute('aria-hidden', 'true');
        pageHero.classList.remove('is-leaving');
        gsap.set(pageHero, { yPercent: 0, clearProps: 'transform,visibility' });
        gsap.set(pageStory, { yPercent: 0, clearProps: 'transform' });
      },
    });

    tl.to(pageStory, { yPercent: 100, duration: 0.75 }, 0)
      .to(pageHero, { yPercent: 0, duration: 0.75 }, 0);
  }

  scrollCue.addEventListener('click', goToStory);
  if (scrollCueUp) {
    scrollCueUp.addEventListener('click', goToHero);
  }

  window.addEventListener(
    'wheel',
    (e) => {
      if (transitioning) return;

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

  /* —— Scroll reveals (first animated section is Familiar window) —— */
  function refreshReveals() {
    ScrollTrigger.getAll().forEach((t) => t.kill());

    gsap.utils.toArray('[data-reveal]').forEach((el) => {
      gsap.set(el, { opacity: 0, y: 72 });
      ScrollTrigger.create({
        trigger: el,
        scroller: storyScroll,
        start: 'top 82%',
        once: true,
        onEnter: () => {
          gsap.to(el, {
            opacity: 1,
            y: 0,
            duration: 1.15,
            ease: 'power3.out',
            overwrite: true,
          });
        },
      });
    });

    ScrollTrigger.refresh();
  }

  /* —— Menubar —— */
  const statusTimers = new WeakMap();

  function closeAllMenus() {
    document.querySelectorAll('.menu__panel').forEach((p) => {
      p.hidden = true;
    });
    document.querySelectorAll('.menu__btn').forEach((b) => {
      b.setAttribute('aria-expanded', 'false');
    });
  }

  function showWindowStatus(fromEl, msg) {
    const win = fromEl.closest('.menubar__window');
    const status = win && win.querySelector('.menubar__status');
    if (!status) return;
    status.textContent = msg;
    status.classList.remove('is-muted');
    gsap.fromTo(status, { opacity: 0.35 }, { opacity: 1, duration: 0.2 });

    const prev = statusTimers.get(status);
    if (prev) clearTimeout(prev);
    statusTimers.set(
      status,
      setTimeout(() => {
        status.textContent = 'App content lives here';
        status.classList.add('is-muted');
      }, 2200)
    );
  }

  document.querySelectorAll('.menubar__status').forEach((el) => {
    el.classList.add('is-muted');
  });

  document.querySelectorAll('.menu__btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const menu = btn.closest('.menu');
      const panel = menu && menu.querySelector('.menu__panel');
      const open = btn.getAttribute('aria-expanded') === 'true';
      closeAllMenus();
      if (!open && panel) {
        panel.hidden = false;
        btn.setAttribute('aria-expanded', 'true');
        gsap.fromTo(panel, { y: -6, opacity: 0 }, { y: 0, opacity: 1, duration: 0.2, ease: 'power2.out' });
      }
    });
  });

  const actionLabels = {
    new: 'File → New Window',
    open: 'File → Open…',
    quit: 'File → Quit (demo only)',
    undo: 'Edit → Undo',
    copy: 'Edit → Copy',
    paste: 'Edit → Paste',
    about: 'Help → About Glue',
    docs: 'Help → Documentation',
    prefs: 'Options → Preferences',
  };

  document.querySelectorAll('.menu__panel button').forEach((item) => {
    item.addEventListener('click', () => {
      const action = item.getAttribute('data-action');
      showWindowStatus(item, actionLabels[action] || action);
      closeAllMenus();
    });
  });

  document.querySelectorAll('.menubar__sys-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      closeAllMenus();
      const win = btn.getAttribute('data-win');
      const labels = {
        minimize: 'Window → Minimize',
        maximize: 'Window → Maximize / Restore',
        close: 'Window → Close (demo only)',
      };
      showWindowStatus(btn, labels[win] || win);
    });
  });

  const toolLabels = {
    new: 'Toolbar → New',
    open: 'Toolbar → Open',
    save: 'Toolbar → Save',
    undo: 'Toolbar → Undo',
    redo: 'Toolbar → Redo',
    search: 'Toolbar → Search',
  };

  document.querySelectorAll('.menubar__tool').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      closeAllMenus();
      const tool = btn.getAttribute('data-tool');
      showWindowStatus(btn, toolLabels[tool] || tool);
    });
  });

  document.addEventListener('click', () => closeAllMenus());

  /* —— Two bridge flows (Front→Back, Back→Front) —— */
  const PACKET_MS = 2.4;
  const STEP_PAUSE_MS = 2400;
  const CYCLE_PAUSE_MS = 4200;
  const f2bMessages = [
    'hello from the UI',
    'save this document',
    'list project files',
    'run a Python task',
  ];
  const b2fMessages = [
    'hello from Python',
    'status: ready',
    'progress: 42%',
    'event: file_saved',
  ];

  let bridgeRunning = false;
  let f2bTimer = null;
  let b2fTimer = null;
  let f2bIndex = 0;
  let b2fIndex = 0;

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function formatLogText(value) {
    if (typeof value === 'string') return value;
    return JSON.stringify(value, null, 2);
  }

  function setLog(el, value) {
    if (!el) return;
    const code = el.querySelector('code');
    const text = formatLogText(value);
    gsap.killTweensOf(el);
    gsap.killTweensOf(code);
    gsap.to(code, {
      opacity: 0,
      y: 4,
      duration: 0.35,
      ease: 'power2.in',
      onComplete: () => {
        code.textContent = text;
        gsap.fromTo(
          code,
          { opacity: 0, y: -4 },
          { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }
        );
      },
    });
    gsap.fromTo(
      el,
      { backgroundColor: 'rgba(62,200,255,0.12)' },
      { backgroundColor: 'rgba(0,40,50,0.25)', duration: 1.8, ease: 'sine.out', overwrite: true }
    );
  }

  function setLabel(el, text) {
    if (!el) return;
    if (el.textContent === text) return;
    gsap.killTweensOf(el);
    gsap.to(el, {
      opacity: 0,
      y: 3,
      duration: 0.3,
      ease: 'power2.in',
      onComplete: () => {
        el.textContent = text;
        gsap.fromTo(
          el,
          { opacity: 0, y: -3 },
          { opacity: 1, y: 0, duration: 0.45, ease: 'power2.out' }
        );
      },
    });
  }

  function setActive(flowEl, side) {
    if (!flowEl) return;
    const panes = flowEl.querySelectorAll('.bridge__pane');
    panes.forEach((p, i) => {
      p.classList.toggle('is-active', (side === 'left' && i === 0) || (side === 'right' && i === 1));
    });
  }

  function clearActive(flowEl) {
    if (!flowEl) return;
    flowEl.querySelectorAll('.bridge__pane').forEach((p) => p.classList.remove('is-active'));
  }

  async function animatePacket(packet, leftToRight) {
    gsap.set(packet, { left: leftToRight ? '0%' : '100%', opacity: 1 });
    await gsap.to(packet, {
      left: leftToRight ? '100%' : '0%',
      duration: PACKET_MS,
      ease: 'power2.inOut',
    });
  }

  async function runFrontToBack() {
    const flow = document.getElementById('flow-f2b');
    const packet = document.getElementById('f2b-packet');
    const label = document.getElementById('f2b-label');
    const logJs = document.getElementById('f2b-log-js');
    const logPy = document.getElementById('f2b-log-py');
    const message = f2bMessages[f2bIndex % f2bMessages.length];
    f2bIndex += 1;

    flow.classList.add('is-playing');
    setActive(flow, 'left');
    setLabel(label, 'bridge_echo');
    setLog(logJs, { call: 'bridge_echo', message });
    setLog(logPy, '…');
    await sleep(STEP_PAUSE_MS);

    await animatePacket(packet, true);

    setActive(flow, 'right');
    setLabel(label, 'running');
    let result;
    try {
      result = await glue.bridge_echo({ message })();
    } catch (err) {
      result = { error: String(err) };
    }
    setLog(logPy, result);
    await sleep(STEP_PAUSE_MS);

    setLabel(label, 'return');
    await animatePacket(packet, false);
    setActive(flow, 'left');
    setLog(logJs, { received: result });
    setLabel(label, 'done');
    await sleep(STEP_PAUSE_MS);

    gsap.to(packet, { opacity: 0, duration: 0.45 });
    clearActive(flow);
    flow.classList.remove('is-playing');
    setLabel(label, 'idle');
  }

  async function runBackToFront() {
    const flow = document.getElementById('flow-b2f');
    const packet = document.getElementById('b2f-packet');
    const label = document.getElementById('b2f-label');
    const logPy = document.getElementById('b2f-log-py');
    const logJs = document.getElementById('b2f-log-js');
    const message = b2fMessages[b2fIndex % b2fMessages.length];
    b2fIndex += 1;

    flow.classList.add('is-playing');
    setActive(flow, 'left');
    setLabel(label, 'bridge_on_js');
    setLog(logPy, { call: 'bridge_on_js', message });
    setLog(logJs, '…');
    await sleep(STEP_PAUSE_MS);

    await animatePacket(packet, true);

    setActive(flow, 'right');
    setLabel(label, 'running');
    let result;
    try {
      result = await glue.bridge_call_js({ message })();
    } catch (err) {
      result = { error: String(err) };
    }
    const jsReply = (result && result.js_reply) || result;
    setLog(logJs, jsReply);
    await sleep(STEP_PAUSE_MS);

    setLabel(label, 'return');
    await animatePacket(packet, false);
    setActive(flow, 'left');
    setLog(logPy, { received: jsReply });
    setLabel(label, 'done');
    await sleep(STEP_PAUSE_MS);

    gsap.to(packet, { opacity: 0, duration: 0.45 });
    clearActive(flow);
    flow.classList.remove('is-playing');
    setLabel(label, 'idle');
  }

  function startBridgeLoop() {
    if (bridgeRunning) return;
    bridgeRunning = true;

    const loopF2b = async () => {
      if (!bridgeRunning) return;
      await runFrontToBack();
      if (bridgeRunning) {
        f2bTimer = window.setTimeout(loopF2b, CYCLE_PAUSE_MS);
      }
    };

    const loopB2f = async () => {
      if (!bridgeRunning) return;
      await runBackToFront();
      if (bridgeRunning) {
        b2fTimer = window.setTimeout(loopB2f, CYCLE_PAUSE_MS);
      }
    };

    // Same timing, both directions at once
    loopF2b();
    loopB2f();
  }

  function stopBridgeLoop() {
    bridgeRunning = false;
    if (f2bTimer) {
      clearTimeout(f2bTimer);
      f2bTimer = null;
    }
    if (b2fTimer) {
      clearTimeout(b2fTimer);
      b2fTimer = null;
    }
  }
})();

/**
 * Aether — App shell
 * ------------------------------------------------------------------
 * Cross-page utilities: local identity (user_id / chat session_id),
 * nav behaviour, Lenis smooth scroll, scroll-reveal, toasts, and a
 * reusable ambient Three.js starfield used on several pages.
 */

const AetherSession = {
  KEY_USER: 'aether_user_id',
  KEY_NAME: 'aether_user_name',
  KEY_SESSION: 'aether_chat_session_id',

  getUserId() { return localStorage.getItem(this.KEY_USER); },
  setUser(id, name) {
    localStorage.setItem(this.KEY_USER, id);
    if (name) localStorage.setItem(this.KEY_NAME, name);
  },
  getUserName() { return localStorage.getItem(this.KEY_NAME) || 'friend'; },

  getChatSessionId() { return localStorage.getItem(this.KEY_SESSION); },
  setChatSessionId(id) { localStorage.setItem(this.KEY_SESSION, id); },
  clearChatSession() { localStorage.removeItem(this.KEY_SESSION); },

  requireUser(redirectTo = '/onboarding') {
    const id = this.getUserId();
    if (!id) window.location.href = redirectTo;
    return id;
  },
};

const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ----------------------------------------------------------------
   Nav: scrolled state + mobile toggle
   ---------------------------------------------------------------- */
function initNav() {
  const nav = document.querySelector('.nav');
  if (!nav) return;

  const onScroll = () => nav.classList.toggle('nav-scrolled', window.scrollY > 12);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      const open = links.classList.toggle('nav-links-open');
      toggle.setAttribute('aria-expanded', String(open));
    });
  }
}

/* ----------------------------------------------------------------
   Lenis smooth scroll (wired to GSAP ticker + ScrollTrigger if present)
   ---------------------------------------------------------------- */
function initLenis() {
  if (prefersReducedMotion || typeof Lenis === 'undefined') return null;

  const lenis = new Lenis({
    lerp: 0.08,          // slightly less smooth for responsiveness
    smoothWheel: true,
    touchMultiplier: 0.8, // reduce touchpad inertia
    wheelMultiplier: 0.8,
  });

  if (typeof gsap !== 'undefined') {
    lenis.on('scroll', () => gsap.ticker.tick());
    gsap.ticker.add((time) => lenis.raf(time * 1000));
    gsap.ticker.lagSmoothing(0);
    if (typeof ScrollTrigger !== 'undefined') {
      lenis.on('scroll', ScrollTrigger.update);
    }
  } else {
    const raf = (time) => { lenis.raf(time); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
  }
  return lenis;
}

/* ----------------------------------------------------------------
   Scroll reveal — IntersectionObserver toggling [data-reveal]
   ---------------------------------------------------------------- */
function initReveal() {
  const targets = document.querySelectorAll('[data-reveal]');
  if (!targets.length) return;

  if (prefersReducedMotion || !('IntersectionObserver' in window)) {
    targets.forEach((el) => el.classList.add('is-visible'));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          const delay = entry.target.dataset.revealDelay || i * 60;
          setTimeout(() => entry.target.classList.add('is-visible'), delay);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: '0px 0px -8% 0px' }
  );
  targets.forEach((el) => observer.observe(el));
}

/* ----------------------------------------------------------------
   Toasts
   ---------------------------------------------------------------- */
function ensureToastStack() {
  let stack = document.querySelector('.toast-stack');
  if (!stack) {
    stack = document.createElement('div');
    stack.className = 'toast-stack';
    stack.setAttribute('aria-live', 'polite');
    document.body.appendChild(stack);
  }
  return stack;
}

function notify(message, type = 'info') {
  const stack = ensureToastStack();
  const toast = document.createElement('div');
  toast.className = `toast glass ${type}`;
  toast.textContent = message;
  stack.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(6px)';
    setTimeout(() => toast.remove(), 300);
  }, 3800);
}

/* ----------------------------------------------------------------
   Ambient Three.js starfield
   Renders a soft, depth-layered star/particle field into a host
   element. Kept deliberately simple (Points, no post-processing) so
   it holds 60fps on modest hardware, and freezes automatically when
   scrolled out of view or when reduced-motion is requested.
   ---------------------------------------------------------------- */
function initCosmicBackground(hostSelector, options = {}) {
  const host = document.querySelector(hostSelector);
  if (!host || typeof THREE === 'undefined') return null;

  const { density = 1, parallax = true, hue = null } = options;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, host.clientWidth / host.clientHeight, 0.1, 100);
  camera.position.z = 6;

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(host.clientWidth, host.clientHeight);
  host.appendChild(renderer.domElement);

  const layers = [];
  const layerConfig = [
    { count: Math.floor(700 * density), size: 0.012, z: -2, color: 0x94a3b8, speed: 0.02 },
    { count: Math.floor(400 * density), size: 0.018, z: -5, color: 0x7c5cff, speed: 0.045 },
    { count: Math.floor(220 * density), size: 0.026, z: -8, color: 0x47e5bc, speed: 0.07 },
  ];

  layerConfig.forEach((cfg) => {
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(cfg.count * 3);
    for (let i = 0; i < cfg.count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 16;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 10;
      positions[i * 3 + 2] = cfg.z + (Math.random() - 0.5) * 2;
    }
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
      color: cfg.color,
      size: cfg.size,
      transparent: true,
      opacity: 0.85,
      sizeAttenuation: true,
    });
    const points = new THREE.Points(geometry, material);
    scene.add(points);
    layers.push({ points, speed: cfg.speed });
  });

  let mouseX = 0;
  let mouseY = 0;
  if (parallax) {
    window.addEventListener('mousemove', (e) => {
      mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
      mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    });
  }

  let visible = true;
  const io = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; }, { threshold: 0 });
  io.observe(host);

  let frame = 0;
  function animate() {
    frame = requestAnimationFrame(animate);
    if (!visible) return;

    layers.forEach(({ points, speed }) => {
      points.rotation.y += prefersReducedMotion ? 0 : speed * 0.006;
      if (parallax && !prefersReducedMotion) {
        points.rotation.x += (mouseY * 0.02 - points.rotation.x) * 0.02;
        points.rotation.y += (mouseX * 0.01) * 0.02;
      }
    });
    renderer.render(scene, camera);
  }
  animate();

  function onResize() {
    const { clientWidth: w, clientHeight: h } = host;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }
  window.addEventListener('resize', onResize);

  return { scene, renderer, camera, destroy: () => { cancelAnimationFrame(frame); io.disconnect(); } };
}

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  //initLenis();
  initReveal();

  const loader = document.querySelector('.page-loader');
  if (loader) {
    window.addEventListener('load', () => {
      setTimeout(() => loader.classList.add('is-hidden'), 300);
    });
  }
});
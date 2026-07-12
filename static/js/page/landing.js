/**
 * Aether — Landing page
 */
document.addEventListener('DOMContentLoaded', () => {
  initCosmicBackground('#hero-cosmos', { density: 1, parallax: true });

  if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined' && !prefersReducedMotion) {
    gsap.registerPlugin(ScrollTrigger);

    const line = document.querySelector('.how-thread-line line');
    if (line && window.matchMedia('(min-width: 861px)').matches) {
      const length = line.getTotalLength ? line.getTotalLength() : 1000;
      gsap.set(line, { strokeDasharray: length, strokeDashoffset: length });
      gsap.to(line, {
        strokeDashoffset: 0,
        ease: 'none',
        scrollTrigger: {
          trigger: '.how-thread',
          start: 'top 75%',
          end: 'bottom 60%',
          scrub: 0.6,
        },
      });
    }
  }
});
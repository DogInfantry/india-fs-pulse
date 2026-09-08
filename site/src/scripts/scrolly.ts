/* The guided opening: four sticky steps, one IntersectionObserver, no library.
   Lives here rather than inline in Scrolly.astro because an inline script is
   the only thing that would force 'unsafe-inline' into the script-src
   directive, and that is the one directive worth keeping strict. */
export function mountScrolly(): void {
  /* Same IntersectionObserver approach as the chart loader. No library. */
  document.querySelectorAll<HTMLElement>('.scrolly').forEach((root) => {
    const graphic = root.querySelector<HTMLElement>('[data-scrolly-graphic]');
    const steps = Array.from(root.querySelectorAll<HTMLElement>('[data-scrolly-step]'));
    const big = root.querySelector<HTMLElement>('[data-scrolly-big]');
    const cap = root.querySelector<HTMLElement>('[data-scrolly-cap]');
    const axis = root.querySelector<HTMLElement>('[data-scrolly-axis]');
    if (!graphic || !steps.length) return;

    const read = (name: string) => Number(graphic.dataset[name]);
    const pc0 = (v: number) => `${Math.round(v)}%`;

    /* Steps 1 and 2 weight the bar by transaction count; 3 and 4 by rupees. */
    const weight = (byValue: boolean) => {
      const k = byValue ? 'Val' : 'Vol';
      graphic.style.setProperty('--m-w', String(read('m' + k)));
      graphic.style.setProperty('--p-w', String(read('p' + k)));
      graphic.style.setProperty('--u-w', String(read('u' + k)));
    };

    /* What the readout says at each step. The values come from the same custom
       properties that size the bar, so the number and the picture cannot drift. */
    const STATE: Record<number, () => { big: string; cap: string; axis: string }> = {
      1: () => ({ big: '100%', cap: 'of UPI transactions, all legs', axis: 'Share of transactions' }),
      2: () => ({ big: pc0(read('mVol')), cap: 'merchant share of transactions', axis: 'Share of transactions' }),
      3: () => ({ big: pc0(read('mVal')), cap: 'merchant share of value', axis: 'Share of value' }),
      4: () => ({ big: '₹0', cap: 'revenue on the merchant leg at 0bps', axis: 'Share of value' }),
    };

    let started = false;
    const activate = (n: number) => {
      if (started && graphic.dataset.step === String(n)) return;
      started = true;
      graphic.dataset.step = String(n);
      weight(n >= 3);
      graphic.style.setProperty('--m-bg', n >= 2 ? 'var(--signal)' : 'var(--s4)');
      const s = STATE[n]();
      if (big) big.textContent = s.big;
      if (cap) cap.textContent = s.cap;
      if (axis) axis.textContent = s.axis;
      steps.forEach((el) => el.toggleAttribute('data-on', el.dataset.scrollyStep === String(n)));
    };

    const io = new IntersectionObserver(
      (entries) => {
        /* The step nearest the middle of the viewport wins, so fast scrolling does
           not leave the graphic showing whichever entry happened to fire last. */
        const visible = entries.filter((e) => e.isIntersecting);
        if (!visible.length) return;
        const best = visible.reduce((a, b) =>
          Math.abs(b.boundingClientRect.top - window.innerHeight / 2) <
          Math.abs(a.boundingClientRect.top - window.innerHeight / 2) ? b : a);
        activate(Number((best.target as HTMLElement).dataset.scrollyStep));
      },
      { rootMargin: '-45% 0px -45% 0px', threshold: 0 },
    );
    steps.forEach((el) => io.observe(el));
    activate(1);
  });
}

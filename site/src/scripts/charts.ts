/**
 * Lazy ECharts bootstrapper and the shared chart theme.
 *
 * The palette is read from tokens.css at runtime via getComputedStyle so the CSS
 * custom properties stay the single source of truth for colour. Canvas cannot
 * read CSS variables directly, hence the lookup.
 */
type ECharts = typeof import('echarts');

const css = (name: string, fallback: string): string => {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
};

export const palette = () => ({
  series: [css('--s1', '#C02734'), css('--s2', '#1F7A8C'), css('--s3', '#C98A2E'),
           css('--s4', '#5B6673'), css('--s5', '#7C5CA8')],
  text: css('--text', '#E9EDF2'),
  muted: css('--text-3', '#6E7987'),
  line: css('--line', '#262F3B'),
  surface: css('--surface', '#131820'),
});

/** Declutter defaults applied to every chart: no border, no chartjunk, thin grid. */
export const baseOption = () => {
  const p = palette();
  return {
    color: p.series,
    textStyle: { fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif', color: p.text },
    grid: { left: 8, right: 16, top: 30, bottom: 8, containLabel: true },
    tooltip: {
      backgroundColor: p.surface,
      borderColor: p.line,
      textStyle: { color: p.text, fontSize: 12 },
      confine: true,
    },
    legend: { textStyle: { color: p.muted, fontSize: 11 }, icon: 'roundRect',
              itemWidth: 10, itemHeight: 10, top: 0 },
  };
};

const merge = (base: any, extra: any): any => {
  const out = { ...base };
  for (const [k, v] of Object.entries(extra ?? {})) {
    out[k] = v && typeof v === 'object' && !Array.isArray(v) && typeof base?.[k] === 'object'
      ? merge(base[k], v) : v;
  }
  return out;
};

let echartsPromise: Promise<ECharts> | null = null;
const loadECharts = () => (echartsPromise ??= import('echarts'));

export function mountCharts(): void {
  const nodes = document.querySelectorAll<HTMLElement>('[data-echart]');
  if (!nodes.length) return;

  const render = async (node: HTMLElement) => {
    const raw = node.querySelector('script[type="application/json"]')?.textContent;
    if (!raw) return;
    const echarts = await loadECharts();
    const chart = echarts.init(node, undefined, { renderer: 'canvas' });
    chart.setOption(merge(baseOption(), JSON.parse(raw)));
    window.addEventListener('resize', () => chart.resize(), { passive: true });
    node.dataset.rendered = 'true';
  };

  const io = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      const el = entry.target as HTMLElement;
      if (entry.isIntersecting && !el.dataset.rendered) {
        void render(el);
        io.unobserve(el);
      }
    }
  }, { rootMargin: '200px' });

  nodes.forEach((n) => io.observe(n));
}

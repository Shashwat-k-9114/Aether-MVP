/**
 * Aether — Janampatri
 */
const DOSHA_COLORS = { Vata: '#7C5CFF', Pitta: '#47E5BC', Kapha: '#F5B759' };
const COLOR_HEX = {
  Indigo: '#4B4E9E', Emerald: '#2ECC71', Gold: '#D4AF37', 'Rose Quartz': '#F7CAC9',
  'Deep Teal': '#0F6E6E', Amber: '#FFBF00', Silver: '#C0C0C0', Violet: '#8F00FF',
};

document.addEventListener('DOMContentLoaded', async () => {
  const userId = AetherSession.requireUser();
  if (!userId) return;

  document.getElementById('jp-greeting').textContent = `${AetherSession.getUserName()}'s Janampatri`;

  try {
    const chart = await Api.getJanampatri(userId);
    renderChart(chart);
  } catch (err) {
    notify('We could not find your birth details yet — let\u2019s start there.', 'error');
    setTimeout(() => { window.location.href = '/onboarding'; }, 1200);
  }
});

function renderChart(chart) {
  document.getElementById('jp-moon-sign').textContent = chart.moon_sign;
  document.getElementById('jp-sun-sign').textContent = chart.sun_sign;
  document.getElementById('jp-ascendant').textContent = chart.ascendant;
  document.getElementById('jp-nakshatra').textContent = chart.nakshatra;
  document.getElementById('jp-dominant-planet').textContent = chart.dominant_planet;

  renderWheel(chart.planetary_positions);
  renderDoshas(chart.doshas);
  renderElements(chart.elements);
  renderLucky(chart.lucky_numbers, chart.lucky_colors);
  renderList('jp-strengths', chart.strengths);
  renderList('jp-challenges', chart.challenges);
}

function renderWheel(positions) {
  const wheel = document.getElementById('jp-wheel');
  const legend = document.getElementById('jp-wheel-legend');
  const radius = 44; // percent of half-width
  const count = positions.length;

  positions.forEach((p, i) => {
    const angle = (i / count) * 2 * Math.PI - Math.PI / 2;
    const x = 50 + radius * Math.cos(angle);
    const y = 50 + radius * Math.sin(angle);

    const dot = document.createElement('div');
    dot.className = 'jp-planet-dot';
    dot.style.left = `${x}%`;
    dot.style.top = `${y}%`;
    dot.textContent = p.planet.slice(0, 2);
    dot.title = `${p.planet} — ${p.sign}, ${p.house} (${p.degrees}°)`;
    wheel.appendChild(dot);
  });

  legend.innerHTML = positions
    .map((p) => `<li><strong>${p.planet}</strong>${p.sign} · ${p.house}</li>`)
    .join('');
}

function renderDoshas(doshas) {
  const donut = document.getElementById('jp-donut');
  const legend = document.getElementById('jp-dosha-legend');

  let acc = 0;
  const stops = Object.entries(doshas).map(([name, pct]) => {
    const start = acc;
    acc += pct;
    return `${DOSHA_COLORS[name] || '#94A3B8'} ${start}% ${acc}%`;
  });
  donut.style.background = `conic-gradient(${stops.join(', ')})`;

  legend.innerHTML = Object.entries(doshas)
    .map(([name, pct]) => `
      <li>
        <span class="dot" style="background:${DOSHA_COLORS[name] || '#94A3B8'}"></span>
        ${name} — <strong>${pct}%</strong>
      </li>`)
    .join('');
}

function renderElements(elements) {
  const host = document.getElementById('jp-elements');
  host.innerHTML = Object.entries(elements)
    .map(([name, pct]) => `
      <div class="jp-element-row">
        <span>${name}</span>
        <span class="jp-element-track"><span class="jp-element-fill" style="width:${pct}%"></span></span>
        <span class="text-muted">${pct}%</span>
      </div>`)
    .join('');
}

function renderLucky(numbers, colors) {
  document.getElementById('jp-lucky-numbers').innerHTML = numbers
    .map((n) => `<span class="jp-lucky-number">${n}</span>`)
    .join('');

  document.getElementById('jp-lucky-colors').innerHTML = colors
    .map((c) => `<span class="jp-lucky-color"><span class="swatch" style="background:${COLOR_HEX[c] || '#94A3B8'}"></span>${c}</span>`)
    .join('');
}

function renderList(id, items) {
  document.getElementById(id).innerHTML = items.map((i) => `<li>${i}</li>`).join('');
}
/**
 * Aether — Experts
 */
document.addEventListener('DOMContentLoaded', async () => {
  const userId = AetherSession.getUserId(); // browsing is allowed without a user; booking requires one
  const grid = document.getElementById('experts-grid');
  const filter = document.getElementById('modality-filter');
  const overlay = document.getElementById('booking-overlay');
  const bookingForm = document.getElementById('booking-form');
  const bookingExpertName = document.getElementById('booking-expert-name');
  let activeExpertId = null;

  const params = new URLSearchParams(window.location.search);
  const initialModality = params.get('modality') || '';
  if (initialModality) filter.value = initialModality;

  async function loadExperts(modality) {
    grid.innerHTML = '<p class="text-muted">Loading practitioners…</p>';
    try {
      const experts = await Api.listExperts(modality);
      grid.innerHTML = '';
      if (!experts.length) {
        grid.innerHTML = '<p class="text-muted">No practitioners match that filter yet.</p>';
        return;
      }
      experts.forEach((ex, i) => grid.appendChild(buildCard(ex, i)));
    } catch (err) {
      grid.innerHTML = '<p class="text-muted">Could not load practitioners right now.</p>';
    }
  }

  function avatarUrl(name) {
    return `https://ui-avatars.com/api/?background=101528&color=47E5BC&size=128&name=${encodeURIComponent(name)}`;
  }

  function buildCard(ex, index) {
    console.log('Expert data:', ex);
    const card = document.createElement('article');
    card.className = 'card expert-card';
    card.style.animationDelay = `${index * 50}ms`;

    card.innerHTML = `
      <div class="expert-top">
        <img class="expert-photo" src="${avatarUrl(ex.name)}" alt="${ex.name}" loading="lazy">
        <div>
          <div class="expert-name">${ex.name}</div>
          <div class="expert-rating">★ ${ex.rating.toFixed(1)} · ${ex.review_count} reviews</div>
        </div>
      </div>
      <div class="expert-meta-row">
        <span>${ex.experience_years} years experience · ${ex.location}</span>
        <span>${ex.languages.join(', ')}</span>
        <span>${ex.availability}</span>
      </div>
      <div class="expert-tags">
        ${ex.specialization.map((s) => `<span class="pill">${s}</span>`).join('')}
      </div>
      <p class="expert-bio">${ex.bio}</p>
      <div class="expert-footer">
        <span class="expert-price">${ex.pricing}</span>
        <button class="btn btn-primary btn-sm" data-book="${ex.id}" data-name="${ex.name}">Book Session</button>
      </div>
    `;

    card.querySelector('[data-book]').addEventListener('click', (e) => openBooking(e.currentTarget.dataset.book, e.currentTarget.dataset.name));
    return card;
  }

  function openBooking(expertId, name) {
  if (!expertId) {
    notify('Practitioner ID missing. Please refresh and try again.', 'error');
    return;
  }
  activeExpertId = expertId;
  bookingExpertName.textContent = `with ${name}`;
  overlay.style.display = 'flex';   // show modal
}

function closeBooking() {
  overlay.style.display = 'none';   // hide modal
  bookingForm.reset();
  activeExpertId = null;
}

  document.getElementById('booking-close').addEventListener('click', closeBooking);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeBooking(); });

  bookingForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const date = document.getElementById('booking-date').value;
    const time = document.getElementById('booking-time').value;
    const sessionDatetime = `${date} ${time}`;

    try {
      await Api.bookExpert(activeExpertId, userId, sessionDatetime);
      notify('Session booked — see it on your dashboard.', 'success');
      closeBooking();
    } catch (err) {
      notify(err.message || 'Could not complete the booking.', 'error');
    }
  });

  filter.addEventListener('change', () => loadExperts(filter.value));
  loadExperts(initialModality);
});
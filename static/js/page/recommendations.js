/**
 * Aether — Recommendations
 */
document.addEventListener('DOMContentLoaded', async () => {
  const userId = AetherSession.requireUser();
  if (!userId) return;

  const grid = document.getElementById('recs-grid');
  const empty = document.getElementById('recs-empty');
  const sessionId = AetherSession.getChatSessionId();

  try {
    let recs;
    if (sessionId) {
      recs = await Api.generateRecommendations(userId, sessionId);
    } else {
      recs = await Api.getUserRecommendations(userId);
    }

    if (!recs.length) {
      empty.hidden = false;
      return;
    }
    recs.sort((a, b) => b.confidence_score - a.confidence_score);
    recs.forEach((rec, i) => grid.appendChild(buildCard(rec, i)));
  } catch (err) {
    notify(err.message || 'Could not load your recommendations.', 'error');
    empty.hidden = false;
  }
});

function buildCard(rec, index) {
  const card = document.createElement('article');
  card.className = 'card rec-card';
  card.style.animationDelay = `${index * 60}ms`;

  const stars = '★'.repeat(rec.stars) + `<span class="dim">${'★'.repeat(5 - rec.stars)}</span>`;

  card.innerHTML = `
    <div class="rec-card-head">
      <div>
        <h2>${rec.modality_name}</h2>
        <div class="rec-stars">${stars}</div>
      </div>
      <button class="rec-save ${rec.is_saved ? 'is-saved' : ''}" aria-label="Save recommendation" data-id="${rec.id}">
        ${rec.is_saved ? '♥' : '♡'}
      </button>
    </div>

    <div class="rec-confidence">
      <span>Confidence</span>
      <span class="rec-confidence-track"><span class="rec-confidence-fill" style="width:${rec.confidence_score}%"></span></span>
      <span>${rec.confidence_score}%</span>
    </div>

    <p class="rec-why">${rec.why_it_fits}</p>

    <ul class="rec-benefits">
      ${rec.benefits.map((b) => `<li>${b}</li>`).join('')}
    </ul>

    <div class="rec-meta">
      <div><strong>${rec.session_duration}</strong>Duration</div>
      <div><strong>${rec.estimated_price}</strong>Estimated price</div>
    </div>

    <p class="text-muted" style="font-size: var(--fs-xs);">${rec.what_to_expect}</p>

    <div class="rec-footer">
      <a href="/experts?modality=${encodeURIComponent(rec.modality_name)}" class="btn btn-ghost btn-sm">Find a practitioner</a>
    </div>
  `;

  card.querySelector('.rec-save').addEventListener('click', async (e) => {
    const btn = e.currentTarget;
    try {
      const updated = await Api.toggleSaveRecommendation(btn.dataset.id);
      btn.classList.toggle('is-saved', updated.is_saved);
      btn.textContent = updated.is_saved ? '♥' : '♡';
      notify(updated.is_saved ? 'Saved to your dashboard.' : 'Removed from saved.', 'success');
    } catch (err) {
      notify('Could not update this recommendation.', 'error');
    }
  });

  return card;
}
/**
 * Aether — Dashboard
 */
document.addEventListener('DOMContentLoaded', async () => {
  const userId = AetherSession.requireUser();
  if (!userId) return;

  const journalForm = document.getElementById('journal-form');

  async function loadDashboard() {
    try {
      const data = await Api.getDashboard(userId);
      document.getElementById('dash-greeting').textContent = `Welcome back, ${data.user.name.split(' ')[0]}`;
      document.getElementById('stat-sessions').textContent = data.chat_session_count;
      document.getElementById('stat-recs').textContent = data.total_recommendations;
      document.getElementById('stat-bookings').textContent = data.upcoming_bookings.length;
      document.getElementById('stat-janampatri').textContent = data.has_janampatri ? 'Ready' : 'Not yet';

      renderSavedRecs(data.saved_recommendations);
      renderBookings(data.upcoming_bookings);
      renderJournal(data.recent_journal_entries);
    } catch (err) {
      notify(err.message || 'Could not load your dashboard.', 'error');
    }
  }

  function renderSavedRecs(recs) {
    const host = document.getElementById('dash-saved-recs');
    if (!recs.length) {
      host.innerHTML = '<p class="dash-empty">Nothing saved yet — recommendations you save will show up here.</p>';
      return;
    }
    host.innerHTML = recs.map((r) => `
      <div class="dash-row">
        <div>
          <div class="dash-row-title">${r.modality_name}</div>
          <div class="dash-row-sub">${'★'.repeat(r.stars)} · ${r.confidence_score}% confidence</div>
        </div>
      </div>`).join('');
  }

  function renderBookings(bookings) {
    const host = document.getElementById('dash-bookings');
    if (!bookings.length) {
      host.innerHTML = '<p class="dash-empty">No upcoming sessions booked yet.</p>';
      return;
    }
    host.innerHTML = bookings.map((b) => `
      <div class="dash-row">
        <div>
          <div class="dash-row-title">${b.expert ? b.expert.name : 'Practitioner'}</div>
          <div class="dash-row-sub">${b.session_datetime}</div>
        </div>
        <span class="pill">${b.status}</span>
      </div>`).join('');
  }

  function renderJournal(entries) {
    const host = document.getElementById('dash-journal');
    if (!entries.length) {
      host.innerHTML = '<p class="dash-empty">Your reflections will appear here once you write your first entry.</p>';
      return;
    }
    host.innerHTML = entries.slice().reverse().map((e) => `
      <div class="dash-row">
        ${e.mood ? `<span class="pill journal-mood-pill">${e.mood}</span>` : ''}
        <p style="margin:0;">${escapeHtml(e.content)}</p>
        <span class="dash-row-sub">${new Date(e.created_at.endsWith('Z') ? e.created_at : `${e.created_at}Z`).toLocaleDateString()}</span>
      </div>`).join('');
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  journalForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const content = document.getElementById('journal-content').value.trim();
    const mood = document.getElementById('journal-mood').value;
    if (!content) return;

    try {
      await Api.createJournalEntry(userId, content, mood || null);
      document.getElementById('journal-content').value = '';
      document.getElementById('journal-mood').value = '';
      notify('Journal entry added.', 'success');
      const entries = await Api.getJournalEntries(userId);
      renderJournal(entries.slice(0, 5).reverse());
    } catch (err) {
      notify(err.message || 'Could not save that entry.', 'error');
    }
  });

  loadDashboard();
});
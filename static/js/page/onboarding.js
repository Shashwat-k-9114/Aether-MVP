/**
 * Aether — Onboarding
 * Four-step form. Validates locally, then on the final step creates the
 * user and submits birth details, which triggers Janampatri generation
 * on the backend before redirecting to /janampatri.
 */
document.addEventListener('DOMContentLoaded', () => {
  initCosmicBackground('#onboarding-cosmos', { density: 0.6, parallax: false });

  const form = document.getElementById('onboarding-form');
  const steps = Array.from(document.querySelectorAll('.onboarding-step'));
  const totalSteps = steps.length;
  const btnBack = document.getElementById('btn-back');
  const btnNext = document.getElementById('btn-next');
  const btnSubmit = document.getElementById('btn-submit');
  const stepCurrentLabel = document.getElementById('step-current');
  const progressFill = document.getElementById('progress-fill');
  const reviewList = document.getElementById('review-list');

  let current = 1;

  const fieldsByStep = {
    1: ['name', 'email'],
    2: ['dob'],
    3: ['pob'],
    4: [],
  };

  function clearError(name) {
    const el = form.querySelector(`[data-error-for="${name}"]`);
    if (el) el.textContent = '';
  }

  function setError(name, message) {
    const el = form.querySelector(`[data-error-for="${name}"]`);
    if (el) el.textContent = message;
  }

  function validateStep(stepNum) {
    let valid = true;
    fieldsByStep[stepNum].forEach((name) => clearError(name));

    if (stepNum === 1) {
      const name = form.name.value.trim();
      const email = form.email.value.trim();
      if (!name) { setError('name', 'Please tell us your name.'); valid = false; }
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { setError('email', 'Enter a valid email address.'); valid = false; }
    }

    if (stepNum === 2) {
      if (!form.dob.value) { setError('dob', 'Date of birth is required.'); valid = false; }
    }

    if (stepNum === 3) {
      if (!form.pob.value.trim()) { setError('pob', 'Place of birth is required.'); valid = false; }
    }

    return valid;
  }

  function renderReview() {
    const rows = [
      ['Name', form.name.value.trim()],
      ['Email', form.email.value.trim()],
      ['Date of birth', form.dob.value],
      ['Time of birth', form.tob.value || 'Not provided'],
      ['Place of birth', form.pob.value.trim()],
      ['Gender', form.gender.options[form.gender.selectedIndex].text],
    ];
    reviewList.innerHTML = rows
      .map(([label, value]) => `<div><dt>${label}</dt><dd>${escapeHtml(value)}</dd></div>`)
      .join('');
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function goToStep(n) {
    steps.forEach((el) => el.classList.toggle('is-active', Number(el.dataset.step) === n));
    stepCurrentLabel.textContent = n;
    progressFill.style.width = `${(n / totalSteps) * 100}%`;
    btnBack.style.visibility = n === 1 ? 'hidden' : 'visible';
    const isLast = n === totalSteps;
    btnNext.style.display = isLast ? 'none' : '';
    btnSubmit.style.display = isLast ? '' : 'none';
    if (isLast) renderReview();
    current = n;
  }

  btnNext.addEventListener('click', () => {
    if (!validateStep(current)) return;
    if (current < totalSteps) goToStep(current + 1);
  });

  btnBack.addEventListener('click', () => {
    if (current > 1) goToStep(current - 1);
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!validateStep(1) || !validateStep(2) || !validateStep(3)) return;

    btnSubmit.disabled = true;
    btnSubmit.textContent = 'Generating your chart…';

    try {
      const user = await Api.createUser({
        name: form.name.value.trim(),
        email: form.email.value.trim(),
        gender: form.gender.value || null,
      });
      AetherSession.setUser(user.id, user.name);

      await Api.submitBirthDetails(user.id, {
        date_of_birth: form.dob.value,
        time_of_birth: form.tob.value || '',
        place_of_birth: form.pob.value.trim(),
      });

      window.location.href = '/janampatri';
    } catch (err) {
      notify(err.message || 'Something went wrong. Please try again.', 'error');
      btnSubmit.disabled = false;
      btnSubmit.textContent = 'Generate my Janampatri';
    }
  });

  goToStep(1);
});
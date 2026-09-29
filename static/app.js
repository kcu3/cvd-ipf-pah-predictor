// Reject out-of-range committed input. Never silently clamp a patient's value.
document.querySelectorAll('input[type="number"][min][max]').forEach((input) => {
  const feedback = document.getElementById(`${input.id}-feedback`);
  const minimum = Number(input.min);
  const maximum = Number(input.max);
  const message = `Enter a value from ${minimum} to ${maximum}.`;
  function check(commit = false) {
    const value = input.valueAsNumber;
    const invalid = input.validity.badInput || (input.value !== '' && (!Number.isFinite(value) || value < minimum || value > maximum));
    input.setCustomValidity(invalid ? message : '');
    input.setAttribute('aria-invalid', String(invalid));
    feedback.textContent = invalid ? message : '';
    // Partial values (e.g. the first digit of 58) must remain editable while typing.
    if (commit && invalid) {
      input.value = '';
      input.setCustomValidity('');
      feedback.textContent = `Value rejected. ${message}`;
      input.setAttribute('aria-invalid', 'true');
    }
  }
  input.addEventListener('input', () => check());
  input.addEventListener('blur', () => check(true));
  input.addEventListener('paste', (event) => {
    const pasted = event.clipboardData?.getData('text').trim();
    if (pasted && (!Number.isFinite(Number(pasted)) || Number(pasted) < minimum || Number(pasted) > maximum)) {
      event.preventDefault();
      feedback.textContent = `Paste rejected. ${message}`;
    }
  });
});

document.getElementById('fill-typical')?.addEventListener('click', () => {
  document.querySelectorAll('form.grid [data-default]').forEach((input) => {
    input.value = input.dataset.default;
    input.setCustomValidity('');
    input.removeAttribute('aria-invalid');
    input.dispatchEvent(new Event('input', {bubbles: true}));
    input.dispatchEvent(new Event('change', {bubbles: true}));
  });
  document.getElementById('fill-status').textContent = 'Typical values filled. Click the button below the inputs to continue.';
  // Never leave an earlier result visible as if it belongs to the new values.
  document.getElementById('prediction-result').hidden = true;
});

// Single predictions navigate to a new page; avoid duplicate submissions.
document.querySelector('form.grid')?.addEventListener('submit', (event) => {
  const button = event.currentTarget.querySelector('button');
  button.disabled = true;
  button.textContent = 'Calculating…';
});
// Browsers can restore disabled controls from their back/forward cache.
window.addEventListener('pageshow', (event) => {
  if (event.persisted) window.location.reload();
});

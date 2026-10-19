export async function createScene(difficulty, recentThemes) {
  const response = await fetch('/api/scene', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      difficulty,
      recent_themes: recentThemes,
    }),
  });
  if (!response.ok) {
    throw new Error(`scene request failed: ${response.status}`);
  }
  return response.json();
}

export async function submitTurn({
  audio,
  textInput,
  envelope,
  signature,
  currentStepId,
  attempts,
  history,
  helpUsed,
}) {
  const form = new FormData();
  form.append('envelope_json', JSON.stringify(envelope));
  form.append('signature', signature);
  form.append('current_step_id', currentStepId);
  form.append('attempts', String(attempts));
  form.append('history_json', JSON.stringify(history));
  form.append('help_used', helpUsed ? 'true' : 'false');
  if (audio) {
    form.append('audio', audio, 'turn.webm');
  }
  if (textInput) {
    form.append('text_input', textInput);
  }
  const response = await fetch('/api/turn', {
    method: 'POST',
    body: form,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const message = payload.detail?.message
      || `turn request failed: ${response.status}`;
    throw new Error(message);
  }
  return response.json();
}

export async function logEvent(name, properties = {}) {
  try {
    await fetch('/api/event', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, properties}),
      keepalive: true,
    });
  } catch {
    // Event logging must never block the learning flow.
  }
}

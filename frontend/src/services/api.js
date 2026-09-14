const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function apiFetch(path, options = {}, timeoutMs = 15000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let signal = controller.signal;
  if (options.signal) {
    const callerSignal = options.signal;
    if (callerSignal.aborted) {
      controller.abort();
    } else {
      callerSignal.addEventListener('abort', () => controller.abort(), { once: true });
    }
  }

  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      signal,
    });
    return res;
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('Request timed out. Is the backend server running?');
    }
    throw new Error('Could not connect to backend server.');
  } finally {
    clearTimeout(timer);
  }
}

export async function login(username, password, signal) {
  const res = await apiFetch(
    '/auth/login',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
      signal,
    },
    10000
  );
  return res;
}

export async function register(username, password, signal) {
  const res = await apiFetch(
    '/auth/register',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
      signal,
    },
    10000
  );
  return res;
}


export async function submitTriage(text, jwtToken, signal) {
  const res = await apiFetch(
    '/triage',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${jwtToken}`,
      },
      body: JSON.stringify({ text }),
      signal,
    },
    30000
  );
  return res;
}

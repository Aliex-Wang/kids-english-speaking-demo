const PRACTICE_KEY = 'kidsEnglishPracticeV1';
const RECENT_KEY = 'kidsEnglishRecentThemesV1';

export function savePractice(state) {
  localStorage.setItem(
    PRACTICE_KEY,
    JSON.stringify({version: 1, ...state}),
  );
}

export function loadPractice() {
  try {
    const raw = localStorage.getItem(PRACTICE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    return data.version === 1 ? data : null;
  } catch {
    return null;
  }
}

export function clearPractice() {
  localStorage.removeItem(PRACTICE_KEY);
}

export function loadRecentThemes() {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    const data = raw ? JSON.parse(raw) : [];
    return Array.isArray(data) ? data.slice(-2) : [];
  } catch {
    return [];
  }
}

export function recordRecentTheme(theme) {
  const recent = loadRecentThemes().filter((item) => item !== theme);
  recent.push(theme);
  localStorage.setItem(RECENT_KEY, JSON.stringify(recent.slice(-2)));
}

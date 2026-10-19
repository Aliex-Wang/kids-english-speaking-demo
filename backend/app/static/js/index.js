import {createScene, logEvent} from './api.js';
import {
  buildPracticeState,
  clearPractice,
  loadRecentThemes,
  recordRecentTheme,
  savePractice,
} from './storage.js';

const selection = {difficulty: null, avatar: null};
const difficultyButtons = [
  ...document.querySelectorAll('[data-difficulty]'),
];
const avatarButtons = [...document.querySelectorAll('[data-avatar]')];
const startButton = document.getElementById('start-button');
const status = document.getElementById('start-status');

function updateStartState() {
  startButton.disabled = !(selection.difficulty && selection.avatar);
}

difficultyButtons.forEach((button) => {
  button.addEventListener('click', () => {
    selection.difficulty = button.dataset.difficulty;
    difficultyButtons.forEach((item) => {
      item.classList.toggle('selected', item === button);
    });
    updateStartState();
  });
});

avatarButtons.forEach((button) => {
  button.addEventListener('click', () => {
    selection.avatar = button.dataset.avatar;
    avatarButtons.forEach((item) => {
      item.classList.toggle('selected', item === button);
    });
    updateStartState();
  });
});

startButton.addEventListener('click', async () => {
  if (!selection.difficulty || !selection.avatar) return;
  startButton.disabled = true;
  status.textContent = '正在准备你的场景...';
  try {
    const recentThemes = loadRecentThemes();
    const response = await createScene(selection.difficulty, recentThemes);
    const scene = response.envelope.scene;
    recordRecentTheme(scene.theme);
    clearPractice();
    savePractice(buildPracticeState({
      difficulty: selection.difficulty,
      avatar: selection.avatar,
      response,
    }));
    logEvent('practice_started', {
      difficulty: selection.difficulty,
      theme: scene.theme,
    });
    window.location.href = '/practice';
  } catch {
    status.textContent = '场景准备失败了，请再试一次。';
    startButton.disabled = false;
  }
});

updateStartState();

import {createScene, logEvent, submitTurn} from './api.js';
import {MicRecorder} from './recorder.js';
import {
  clearPractice,
  loadPractice,
  loadRecentThemes,
  recordRecentTheme,
  savePractice,
} from './storage.js';

const config = window.__APP_CONFIG__;
const state = loadPractice();

if (!state) {
  window.location.replace('/');
  throw new Error('practice state missing');
}

const scene = state.envelope.scene;
const profile = config.difficulties.find(
  (item) => item.id === state.difficulty,
) || {
  max_recording_seconds: 15,
  speech_rate: 1,
  show_hint_zh: false,
};
const theme = config.themes[scene.theme] || {
  name_en: 'English',
  name_zh: '英语',
  icon: '💬',
  color: '#ff8a5b',
};

const elements = {
  taskIntro: document.getElementById('task-intro'),
  dialogue: document.getElementById('dialogue'),
  endScreen: document.getElementById('end-screen'),
  themeVisual: document.getElementById('theme-visual'),
  sceneTitle: document.getElementById('scene-title'),
  sceneGoal: document.getElementById('scene-goal'),
  openingText: document.getElementById('opening-text'),
  replayOpening: document.getElementById('replay-opening'),
  beginButton: document.getElementById('begin-button'),
  practiceThemeIcon: document.getElementById('practice-theme-icon'),
  practiceThemeName: document.getElementById('practice-theme-name'),
  practiceTitle: document.getElementById('practice-title'),
  progressLabel: document.getElementById('progress-label'),
  aiBubble: document.getElementById('ai-bubble'),
  replayReply: document.getElementById('replay-reply'),
  slowReply: document.getElementById('slow-reply'),
  hint: document.getElementById('hint'),
  micButton: document.getElementById('mic-button'),
  micLabel: document.getElementById('mic-label'),
  helpButton: document.getElementById('help-button'),
  textFallback: document.getElementById('text-fallback'),
  textInput: document.getElementById('text-input'),
  textSubmit: document.getElementById('text-submit'),
  status: document.getElementById('status'),
  stars: document.getElementById('stars'),
  targetExpressions: document.getElementById('target-expressions'),
  restartButton: document.getElementById('restart-button'),
  changeDifficulty: document.getElementById('change-difficulty'),
};

elements.targetExpressions.setAttribute('data-testid', 'target-expressions');

let lastReplyText = '';
let lastReplyAudio = null;
let lastReplyMediaType = null;
let recorder = null;

function currentStep() {
  return scene.steps.find(
    (step) => step.step_id === state.currentStepId,
  ) || null;
}

function save() {
  savePractice(state);
}

function setStatus(message) {
  elements.status.textContent = message;
}

function speak(text, rate = profile.speech_rate) {
  if (!('speechSynthesis' in window) || !text) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-US';
  utterance.rate = rate;
  window.speechSynthesis.speak(utterance);
}

async function playAudio(base64, mediaType, rate = 1) {
  if (!base64) return false;
  const audio = new Audio(
    `data:${mediaType || 'audio/mpeg'};base64,${base64}`,
  );
  audio.playbackRate = rate;
  let timeout = null;
  try {
    await Promise.race([
      audio.play(),
      new Promise((_, reject) => {
        timeout = window.setTimeout(
          () => reject(new Error('audio playback timed out')),
          2000,
        );
      }),
    ]);
    return true;
  } catch {
    audio.pause();
    return false;
  } finally {
    window.clearTimeout(timeout);
  }
}

async function playOpening() {
  if (!(await playAudio(state.openingAudioBase64, state.openingMediaType))) {
    speak(state.openingText, profile.speech_rate);
  }
}

function setThemeVisuals() {
  elements.themeVisual.textContent = theme.icon;
  elements.themeVisual.style.background =
    `linear-gradient(135deg, ${theme.color}33, #e9f4f4)`;
  elements.practiceThemeIcon.textContent = theme.icon;
  elements.practiceThemeIcon.style.background = `${theme.color}22`;
  elements.practiceThemeName.textContent =
    theme.name_zh || theme.name_en;
  elements.practiceTitle.textContent = scene.title;
}

function renderIntro() {
  elements.sceneTitle.textContent = scene.title;
  elements.sceneGoal.textContent = `${scene.role} · ${scene.goal}`;
  elements.openingText.textContent = state.openingText;
  setThemeVisuals();
}

function renderStep() {
  const step = currentStep();
  if (!step) {
    showEnd();
    return;
  }
  const index = scene.steps.findIndex(
    (item) => item.step_id === step.step_id,
  );
  elements.progressLabel.textContent =
    `${index + 1} / ${scene.steps.length}`;
  elements.aiBubble.textContent = step.role_prompt;
  elements.hint.classList.add('hidden');
  elements.hint.textContent = '';
  elements.micLabel.textContent = '点击开始说话';
  elements.micButton.classList.remove('recording');
  lastReplyText = step.role_prompt;
  lastReplyAudio = null;
  lastReplyMediaType = null;
}

function showDialogue() {
  elements.taskIntro.classList.add('hidden');
  elements.endScreen.classList.add('hidden');
  elements.dialogue.classList.remove('hidden');
}

function showEnd() {
  elements.taskIntro.classList.add('hidden');
  elements.dialogue.classList.add('hidden');
  elements.endScreen.classList.remove('hidden');
  elements.stars.textContent = '⭐'.repeat(state.stars);
  elements.targetExpressions.innerHTML = '';
  scene.target_expressions.forEach((text) => {
    const item = document.createElement('li');
    item.textContent = text;
    elements.targetExpressions.appendChild(item);
  });
}

async function sendTurn({audio, textInput}) {
  setStatus('识别中...');
  elements.micButton.disabled = true;
  elements.textInput.disabled = true;
  elements.textSubmit.disabled = true;
  try {
    const response = await submitTurn({
      audio,
      textInput,
      envelope: state.envelope,
      signature: state.signature,
      currentStepId: state.currentStepId,
      attempts: state.attempts,
      history: state.history,
      helpUsed: state.helpUsed,
    });
    handleResponse(response);
  } catch (error) {
    let message = '没有听清，请再试一次。';
    let errorType = 'turn';
    if (error?.name === 'TimeoutError') {
      message = '等得有点久，请再试一次。';
      errorType = 'timeout';
    } else if (error?.name === 'TypeError') {
      message = '网络暂时没有连上，请再试一次。';
      errorType = 'network';
    }
    setStatus(message);
    logEvent('technical_error', {
      difficulty: state.difficulty,
      error_type: errorType,
    });
  } finally {
    elements.micButton.disabled = false;
    elements.textInput.disabled = false;
    elements.textSubmit.disabled = false;
    elements.micLabel.textContent = '点击开始说话';
  }
}

function handleResponse(response) {
  const step = currentStep();
  if (!step) return;
  state.history.push({
    step_id: step.step_id,
    accepted: response.accepted,
    attempts: response.attempts,
    help_used: state.helpUsed,
  });
  state.stars += response.stars_earned;
  state.attempts = response.attempts;
  if (state.helpUsed && response.accepted) {
    logEvent('continued_after_help', {
      difficulty: state.difficulty,
      theme: scene.theme,
      continued_after_help: true,
    });
  }
  state.helpUsed = false;
  if (response.accepted) {
    if (!state.completedStepIds.includes(step.step_id)) {
      state.completedStepIds.push(step.step_id);
    }
    step.target_phrases.forEach((phrase) => {
      if (!state.targetExpressionsCompleted.includes(phrase)) {
        state.targetExpressionsCompleted.push(phrase);
      }
    });
  }
  setStatus(response.feedback);
  if (response.completed) {
    state.completed = true;
    state.currentStepId = null;
    save();
    logEvent('practice_completed', {
      difficulty: state.difficulty,
      theme: scene.theme,
      stars: state.stars,
      turns: state.history.length,
    });
    showEnd();
    return;
  }
  state.currentStepId = response.next_step;
  save();
  renderStep();
  if (response.hint) {
    elements.hint.textContent = response.hint;
    elements.hint.classList.remove('hidden');
  }
  lastReplyText = response.reply;
  lastReplyAudio = response.audio_base64;
  lastReplyMediaType = response.media_type;
  const replyText = lastReplyText;
  void playAudio(lastReplyAudio, lastReplyMediaType).then((played) => {
    if (!played) speak(replyText, profile.speech_rate);
  });
}

function createRecorder() {
  return new MicRecorder({
    maxSeconds: profile.max_recording_seconds,
    onComplete: (blob) => {
      elements.micButton.classList.remove('recording');
      elements.micLabel.textContent = '识别中...';
      sendTurn({audio: blob});
    },
    onError: (error) => {
      elements.micButton.classList.remove('recording');
      if (error?.name === 'NotAllowedError') {
        elements.textFallback.classList.remove('hidden');
        setStatus('请允许麦克风权限，或者输入你的回答。');
      } else {
        setStatus('麦克风暂时不可用，请再试一次。');
      }
    },
  });
}

function handleMicClick() {
  if (recorder.isRecording() || recorder.isStarting()) {
    recorder.stop();
    return;
  }
  recorder.start().then((started) => {
    if (started) {
      elements.micButton.classList.add('recording');
      elements.micLabel.textContent = '点击结束录音';
      setStatus('录音中... 点击麦克风结束');
    }
  });
}

function showHelp() {
  const step = currentStep();
  if (!step) return;
  const hint = profile.show_hint_zh
    ? `${step.hint_en} ${step.hint_zh}`
    : step.hint_en;
  elements.hint.textContent = hint;
  elements.hint.classList.remove('hidden');
  speak(step.hint_en, 0.75);
  state.helpUsed = true;
  save();
  logEvent('help_clicked', {
    difficulty: state.difficulty,
    theme: scene.theme,
  });
}

async function restartPractice() {
  elements.restartButton.disabled = true;
  setStatus('正在准备新的场景...');
  try {
    const response = await createScene(
      state.difficulty,
      loadRecentThemes(),
    );
    const nextScene = response.envelope.scene;
    recordRecentTheme(nextScene.theme);
    clearPractice();
    savePractice({
      difficulty: state.difficulty,
      avatar: state.avatar,
      envelope: response.envelope,
      signature: response.signature,
      openingText: response.opening_text,
      openingAudioBase64: response.opening_audio_base64,
      openingMediaType: response.opening_media_type,
      currentStepId: nextScene.steps[0].step_id,
      attempts: 0,
      stars: 0,
      completedStepIds: [],
      targetExpressionsCompleted: [],
      history: [],
      helpUsed: false,
      hasStarted: false,
      completed: false,
      lastPracticeAt: new Date().toISOString(),
    });
    logEvent('practice_restarted', {
      difficulty: state.difficulty,
      theme: nextScene.theme,
    });
    window.location.reload();
  } catch {
    setStatus('新场景准备失败，请再试一次。');
    elements.restartButton.disabled = false;
  }
}

function initialize() {
  renderIntro();
  if (state.completed) {
    showEnd();
    return;
  }
  if (state.hasStarted) {
    showDialogue();
    renderStep();
  }
}

elements.beginButton.addEventListener('click', async () => {
  state.hasStarted = true;
  save();
  showDialogue();
  renderStep();
  await playOpening();
});
elements.replayOpening.addEventListener('click', playOpening);
elements.replayReply.addEventListener('click', async () => {
  if (!(await playAudio(lastReplyAudio, lastReplyMediaType))) {
    speak(lastReplyText, profile.speech_rate);
  }
});
elements.slowReply.addEventListener('click', async () => {
  if (!(await playAudio(lastReplyAudio, lastReplyMediaType, 0.7))) {
    speak(lastReplyText, 0.7);
  }
});
elements.helpButton.addEventListener('click', showHelp);
elements.micButton.addEventListener('click', handleMicClick);
elements.textSubmit.addEventListener('click', () => {
  const text = elements.textInput.value.trim();
  if (!text) return;
  elements.textInput.value = '';
  sendTurn({textInput: text});
});
elements.textInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    event.preventDefault();
    elements.textSubmit.click();
  }
});
elements.changeDifficulty.addEventListener('click', () => {
  window.location.href = '/';
});
elements.restartButton.addEventListener('click', restartPractice);

recorder = createRecorder();
initialize();

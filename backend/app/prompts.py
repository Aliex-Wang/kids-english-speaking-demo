import json

from app.content import DifficultyProfile, ThemeDefinition
from app.schemas import Difficulty, SceneSpec, SceneStep, TurnSummary


SCENE_SYSTEM_PROMPT = """SCENE_GENERATION
You design safe English speaking tasks for children aged 4-12.
Return ONLY a JSON object. Do not use Markdown or code fences.
The JSON object must match this shape:
{
  "scene_id": "string",
  "theme": "family|school|shopping|food|transport|friends",
  "difficulty": "sprout|explorer|star",
  "title": "string",
  "setting": "string",
  "role": "string",
  "goal": "string",
  "steps": [
    {
      "step_id": "step_1",
      "kind": "greeting|task|free_expression|goodbye",
      "goal": "string",
      "role_prompt": "string",
      "target_phrases": ["string"],
      "accepted_keywords": ["string"],
      "hint_en": "string",
      "hint_zh": "string",
      "retry_prompt": "string",
      "max_attempts": 2,
      "next_step": "step_2",
      "allow_skip": true
    }
  ],
  "target_expressions": ["string"],
  "safety_notes": ["string"]
}
Rules:
- First step kind is greeting. Last step kind is goodbye.
- Include at least one free_expression step.
- Step IDs are step_1, step_2, ... in order.
- Last step next_step is null. Every other next_step points to the next step.
- The scene must be a familiar daily-life task.
- No violence, horror, adult content, discrimination, brand promotion, or requests for personal information.
- The character must never ask for a real name, school, address, phone number, or photo.
"""

TURN_SYSTEM_PROMPT = """TURN_JUDGEMENT
You are a friendly English conversation partner for a child.
Return ONLY a JSON object with exactly these fields:
{
  "accepted": true,
  "feedback": "short positive feedback",
  "reply": "one or two short English sentences",
  "hint": "optional short hint",
  "next_step": "step_2",
  "stars": 1,
  "safety": "ok"
}
Rules:
- Accept an answer if it completes the current step's communicative goal.
- If NEXT_ROLE_PROMPT is not NONE, your reply must naturally include that question or a close paraphrase.
- If the child is off-topic, gently redirect.
- Never ask for a real name, school, address, phone number, or photo.
- Never mention violence, horror, adult content, brands, or personal information.
- Keep feedback positive. Do not use red-error language.
- Reply in English only.
"""


def build_scene_prompt(
    theme: ThemeDefinition,
    difficulty: Difficulty,
    profile: DifficultyProfile,
) -> str:
    return "\n".join(
        [
            f"THEME: {theme.id.value}",
            f"DIFFICULTY: {difficulty.value}",
            f"TARGET_AGE: {profile.target_age}",
            f"TARGET_ANSWER: {profile.target_answer}",
            f"STEP_COUNT: {profile.min_steps} to {profile.max_steps}",
            f"FREE_EXPRESSION_STEPS: at least {profile.free_expression_turns}",
            f"SUBTHEMES: {', '.join(theme.subthemes)}",
            f"SETTING: {theme.setting}",
            f"ROLE: {theme.role}",
            f"GOAL: {theme.goal}",
            "TARGET_EXAMPLES: "
            + json.dumps(theme.target_examples[difficulty], ensure_ascii=False),
            "Create one complete scene now. Use only the theme and difficulty above.",
        ]
    )


def build_turn_prompt(
    scene: SceneSpec,
    step: SceneStep,
    transcript: str,
    attempts: int,
    history: list[TurnSummary],
    next_step: SceneStep | None,
) -> str:
    next_prompt = next_step.role_prompt if next_step else "NONE"
    return "\n".join(
        [
            f"SCENE_TITLE: {scene.title}",
            f"ROLE: {scene.role}",
            f"GOAL: {scene.goal}",
            f"DIFFICULTY: {scene.difficulty.value}",
            f"CURRENT_STEP: {step.step_id}",
            f"STEP_GOAL: {step.goal}",
            f"ROLE_PROMPT: {step.role_prompt}",
            f"TARGET_PHRASES: {json.dumps(step.target_phrases, ensure_ascii=False)}",
            f"ACCEPTED_KEYWORDS: {json.dumps(step.accepted_keywords, ensure_ascii=False)}",
            f"HINT_EN: {step.hint_en}",
            f"ATTEMPTS: {attempts}",
            "HISTORY: "
            + json.dumps([item.model_dump() for item in history], ensure_ascii=False),
            f"NEXT_STEP: {next_step.step_id if next_step else 'NONE'}",
            f"NEXT_ROLE_PROMPT: {next_prompt}",
            f"CHILD_TEXT: {transcript}",
            "Return the JSON object now.",
        ]
    )

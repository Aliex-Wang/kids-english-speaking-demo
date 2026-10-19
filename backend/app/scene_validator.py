import re

from app.content import PROFILES
from app.safety import SafetyValidator
from app.schemas import SceneSpec, StepKind


class SceneValidationError(ValueError):
    def __init__(self, issues: list[str]):
        super().__init__("; ".join(issues))
        self.issues = issues


def count_sentences(text: str) -> int:
    return max(1, len(re.findall(r"[.!?]+", text)))


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


class SceneValidator:
    def __init__(self, safety: SafetyValidator | None = None):
        self.safety = safety or SafetyValidator()

    def validate(self, scene: SceneSpec) -> None:
        issues: list[str] = []
        profile = PROFILES[scene.difficulty]

        if not (profile.min_steps <= len(scene.steps) <= profile.max_steps):
            issues.append(
                f"step count must be {profile.min_steps}-{profile.max_steps}, "
                f"got {len(scene.steps)}"
            )
        if scene.steps[0].kind is not StepKind.greeting:
            issues.append("first step must be greeting")
        if scene.steps[-1].kind is not StepKind.goodbye:
            issues.append("last step must be goodbye")
        free_count = sum(
            step.kind is StepKind.free_expression for step in scene.steps
        )
        if free_count < profile.free_expression_turns:
            issues.append(
                "scene must contain at least "
                f"{profile.free_expression_turns} free_expression steps"
            )

        ids = [step.step_id for step in scene.steps]
        if len(ids) != len(set(ids)):
            issues.append("step ids must be unique")
        for index, step in enumerate(scene.steps):
            if step.step_id != f"step_{index + 1}":
                issues.append("step ids must be step_1, step_2, ... in order")
            expected_next = f"step_{index + 2}" if index + 1 < len(scene.steps) else None
            if step.next_step != expected_next:
                issues.append(f"{step.step_id} next_step must be {expected_next}")
            for phrase in step.target_phrases:
                if word_count(phrase) > profile.max_target_words:
                    issues.append(
                        f"{step.step_id} target phrase is too long for "
                        f"{scene.difficulty.value}"
                    )
            if count_sentences(step.role_prompt) > profile.max_reply_sentences:
                issues.append(
                    f"{step.step_id} role_prompt is too long for "
                    f"{scene.difficulty.value}"
                )
            for value in [
                step.goal,
                step.role_prompt,
                step.hint_en,
                step.hint_zh,
                step.retry_prompt,
                *step.target_phrases,
            ]:
                if self.safety.violations(value):
                    issues.append(f"{step.step_id} contains unsafe content")

        for value in [
            scene.title,
            scene.setting,
            scene.role,
            scene.goal,
            *scene.target_expressions,
            *scene.safety_notes,
        ]:
            if self.safety.violations(value):
                issues.append("scene metadata contains unsafe content")

        if issues:
            raise SceneValidationError(issues)

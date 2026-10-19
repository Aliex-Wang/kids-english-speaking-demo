import asyncio
import base64
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

from app.content import PROFILES
from app.matching import rule_match
from app.prompts import TURN_SYSTEM_PROMPT, build_turn_prompt
from app.providers.base import LLMProvider, TTSProvider
from app.safety import SafetyValidator
from app.scene_validator import count_sentences
from app.schemas import (
    Difficulty,
    SceneSpec,
    SceneStep,
    TurnResponse,
    TurnSummary,
)


@dataclass(frozen=True)
class TurnContext:
    scene: SceneSpec
    current_step_id: str
    recognized_text: str
    attempts: int = 0
    history: list[TurnSummary] = field(default_factory=list)
    help_used: bool = False


class TurnJudgement(BaseModel):
    accepted: bool
    feedback: str = Field(min_length=1, max_length=160)
    reply: str = Field(min_length=1, max_length=300)
    hint: str = Field(default="", max_length=200)
    next_step: str | None = None
    stars: int = Field(default=1, ge=0, le=2)
    safety: Literal["ok", "redirect"] = "ok"


class DialogueOrchestrator:
    def __init__(
        self,
        llm: LLMProvider,
        safety: SafetyValidator,
        tts: TTSProvider,
        timeout_seconds: float = 12.0,
        voice: str = "xiaoyun",
    ):
        self.llm = llm
        self.safety = safety
        self.tts = tts
        self.timeout_seconds = timeout_seconds
        self.voice = voice

    async def handle_turn(self, context: TurnContext) -> TurnResponse:
        step = self._find_step(context.scene, context.current_step_id)
        text = context.recognized_text.strip()

        if not text:
            return self._retry(
                step,
                context,
                message="I didn't hear you. Let's try again.",
                stars=0,
                attempts=context.attempts,
            )
        if self.safety.violations(text):
            return self._safe_redirect(step, context)

        next_step = self._next_step(context.scene, step)
        judgement = await self._judge(context, step, next_step)
        if judgement and judgement.safety == "redirect":
            return self._safe_redirect(step, context)

        accepted = rule_match(text, step, context.scene.difficulty) or bool(
            judgement and judgement.accepted
        )
        if accepted:
            return await self._accepted(context, step, next_step, judgement)
        return await self._not_accepted(context, step, next_step, judgement)

    async def _judge(
        self,
        context: TurnContext,
        step: SceneStep,
        next_step: SceneStep | None,
    ) -> TurnJudgement | None:
        prompt = build_turn_prompt(
            context.scene,
            step,
            context.recognized_text,
            context.attempts,
            context.history,
            next_step,
        )
        try:
            payload = await asyncio.wait_for(
                self.llm.complete_json(TURN_SYSTEM_PROMPT, prompt),
                timeout=self.timeout_seconds,
            )
            judgement = TurnJudgement.model_validate(payload)
        except Exception:
            return None

        if self.safety.violations(
            " ".join([judgement.feedback, judgement.reply, judgement.hint])
        ):
            return None
        if next_step is not None:
            profile = PROFILES[context.scene.difficulty]
            if count_sentences(judgement.reply) > profile.max_reply_sentences:
                return None
        return judgement

    async def _accepted(
        self,
        context: TurnContext,
        step: SceneStep,
        next_step: SceneStep | None,
        judgement: TurnJudgement | None,
    ) -> TurnResponse:
        feedback = judgement.feedback if judgement else "Great job!"
        if next_step is None:
            reply = (
                judgement.reply
                if judgement
                else "Great job! See you next time."
            )
            next_step_id = None
            completed = True
        else:
            reply = judgement.reply if judgement else next_step.role_prompt
            next_step_id = next_step.step_id
            completed = False
        audio_base64, media_type = await self._tts(
            reply, context.scene.difficulty
        )
        return TurnResponse(
            recognized_text=context.recognized_text,
            accepted=True,
            feedback=feedback,
            reply=reply,
            hint="",
            next_step=next_step_id,
            stars_earned=2,
            safety="ok",
            attempts=0,
            completed=completed,
            audio_base64=audio_base64,
            media_type=media_type,
        )

    async def _not_accepted(
        self,
        context: TurnContext,
        step: SceneStep,
        next_step: SceneStep | None,
        judgement: TurnJudgement | None,
    ) -> TurnResponse:
        attempts = context.attempts + 1
        if attempts >= step.max_attempts and step.allow_skip:
            if next_step is None:
                reply = "Great job! See you next time."
                next_step_id = None
                completed = True
                feedback = "Nice try! Let's finish here."
            else:
                reply = next_step.role_prompt
                next_step_id = next_step.step_id
                completed = False
                feedback = "Nice try! Let's keep going."
            audio_base64, media_type = await self._tts(
                reply, context.scene.difficulty
            )
            return TurnResponse(
                recognized_text=context.recognized_text,
                accepted=False,
                feedback=feedback,
                reply=reply,
                hint="",
                next_step=next_step_id,
                stars_earned=1,
                safety="ok",
                attempts=0,
                completed=completed,
                audio_base64=audio_base64,
                media_type=media_type,
            )

        reply = step.retry_prompt
        audio_base64, media_type = await self._tts(
            reply, context.scene.difficulty
        )
        return TurnResponse(
            recognized_text=context.recognized_text,
            accepted=False,
            feedback=judgement.feedback if judgement else "Nice try!",
            reply=reply,
            hint=step.hint_en,
            next_step=step.step_id,
            stars_earned=1,
            safety="ok",
            attempts=attempts,
            completed=False,
            audio_base64=audio_base64,
            media_type=media_type,
        )

    def _retry(
        self,
        step: SceneStep,
        context: TurnContext,
        message: str,
        stars: int,
        attempts: int,
    ) -> TurnResponse:
        return TurnResponse(
            recognized_text="",
            accepted=False,
            feedback=message,
            reply=step.retry_prompt,
            hint=step.hint_en,
            next_step=step.step_id,
            stars_earned=stars,
            safety="ok",
            attempts=attempts,
            completed=False,
            audio_base64=None,
            media_type=None,
        )

    def _safe_redirect(
        self,
        step: SceneStep,
        context: TurnContext,
    ) -> TurnResponse:
        return TurnResponse(
            recognized_text=context.recognized_text,
            accepted=False,
            feedback="Let's keep playing our game.",
            reply=step.retry_prompt,
            hint=step.hint_en,
            next_step=step.step_id,
            stars_earned=1,
            safety="redirect",
            attempts=context.attempts,
            completed=False,
            audio_base64=None,
            media_type=None,
        )

    async def _tts(
        self,
        text: str,
        difficulty: Difficulty,
    ) -> tuple[str | None, str | None]:
        profile = PROFILES[difficulty]
        try:
            result = await asyncio.wait_for(
                self.tts.synthesize(
                    text,
                    voice=self.voice,
                    speed=profile.speech_rate,
                ),
                timeout=self.timeout_seconds,
            )
        except Exception:
            return None, None
        encoded = base64.b64encode(result.audio).decode("ascii")
        return encoded, result.media_type

    @staticmethod
    def _find_step(scene: SceneSpec, step_id: str) -> SceneStep:
        for step in scene.steps:
            if step.step_id == step_id:
                return step
        raise ValueError(f"unknown step: {step_id}")

    @classmethod
    def _next_step(
        cls,
        scene: SceneSpec,
        step: SceneStep,
    ) -> SceneStep | None:
        if step.next_step is None:
            return None
        return cls._find_step(scene, step.next_step)

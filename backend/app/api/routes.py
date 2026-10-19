import base64
import json
import time

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.audio import AudioConversionError, convert_to_wav_16k_mono
from app.content import PROFILES
from app.dialogue import TurnContext
from app.schemas import (
    EventRequest,
    SceneEnvelope,
    SceneRequest,
    SceneResponse,
    TurnResponse,
    TurnSummary,
)
from app.services import Services
from app.signature import (
    SceneSignatureError,
    make_envelope,
    sign_envelope,
    verify_envelope,
)

router = APIRouter()


def get_services(request: Request) -> Services:
    return request.app.state.services


@router.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    services: Services = Depends(get_services),
):
    return services.templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_config": services.app_config,
            "app_config_json": json.dumps(
                services.app_config,
                ensure_ascii=False,
            ),
        },
    )


@router.get("/practice", response_class=HTMLResponse)
async def practice(
    request: Request,
    services: Services = Depends(get_services),
):
    return services.templates.TemplateResponse(
        request=request,
        name="practice.html",
        context={
            "app_config": services.app_config,
            "app_config_json": json.dumps(
                services.app_config,
                ensure_ascii=False,
            ),
        },
    )


@router.post("/api/scene", response_model=SceneResponse)
async def create_scene(
    payload: SceneRequest,
    services: Services = Depends(get_services),
):
    started = time.perf_counter()
    generated = await services.scene_generator.generate(
        payload.difficulty,
        payload.recent_themes,
    )
    envelope = make_envelope(
        generated.scene,
        services.settings.scene_ttl_seconds,
    )
    signature = sign_envelope(envelope, services.settings.hmac_secret)
    opening_text = generated.scene.steps[0].role_prompt
    opening_audio_base64 = None
    opening_media_type = None
    try:
        opening = await services.tts.synthesize(
            opening_text,
            voice=services.settings.tts_voice,
            speed=PROFILES[generated.scene.difficulty].speech_rate,
        )
        opening_audio_base64 = base64.b64encode(opening.audio).decode("ascii")
        opening_media_type = opening.media_type
    except Exception:
        services.events.log(
            "technical_error",
            {
                "difficulty": payload.difficulty.value,
                "error_type": "tts_opening",
            },
        )
    services.events.log(
        "scene_generated",
        {
            "theme": generated.scene.theme.value,
            "difficulty": payload.difficulty.value,
            "success": not generated.fallback_used,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "error_type": generated.error_type or "none",
        },
    )
    return SceneResponse(
        envelope=envelope,
        signature=signature,
        opening_text=opening_text,
        opening_audio_base64=opening_audio_base64,
        opening_media_type=opening_media_type,
        fallback_used=generated.fallback_used,
    )


@router.post("/api/turn", response_model=TurnResponse)
async def submit_turn(
    envelope_json: str = Form(...),
    signature: str = Form(...),
    current_step_id: str = Form(...),
    attempts: int = Form(0),
    history_json: str = Form("[]"),
    help_used: bool = Form(False),
    audio: UploadFile | None = File(None),
    text_input: str | None = Form(None),
    services: Services = Depends(get_services),
):
    started = time.perf_counter()
    if not 0 <= attempts <= 10:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_attempts",
                "message": "attempts must be between 0 and 10",
            },
        )
    try:
        envelope = SceneEnvelope.model_validate_json(envelope_json)
        verify_envelope(
            envelope,
            signature,
            services.settings.hmac_secret,
        )
    except (ValidationError, SceneSignatureError) as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_scene", "message": str(exc)},
        ) from exc

    try:
        raw_history = json.loads(history_json)
        history = [TurnSummary.model_validate(item) for item in raw_history]
    except (json.JSONDecodeError, TypeError, ValidationError) as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_history",
                "message": "history must be a list of turn summaries",
            },
        ) from exc

    if text_input is not None and text_input.strip():
        transcript = text_input.strip()
    else:
        if audio is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "missing_audio",
                    "message": "audio or text_input is required",
                },
            )
        raw_audio = await audio.read()
        if len(raw_audio) > services.settings.max_audio_bytes:
            raise HTTPException(
                status_code=413,
                detail={
                    "code": "audio_too_large",
                    "message": "audio file is too large",
                },
            )
        try:
            wav = convert_to_wav_16k_mono(
                raw_audio,
                audio.content_type or "application/octet-stream",
            )
        except AudioConversionError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "invalid_audio", "message": str(exc)},
            ) from exc
        try:
            asr_result = await services.asr.transcribe(wav)
        except Exception as exc:
            services.events.log(
                "technical_error",
                {
                    "difficulty": envelope.scene.difficulty.value,
                    "error_type": "asr",
                },
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "asr_unavailable",
                    "message": "Please try again.",
                },
            ) from exc
        transcript = asr_result.text
        if (
            asr_result.confidence is not None
            and asr_result.confidence < 0.5
        ):
            transcript = ""

    try:
        result = await services.dialogue.handle_turn(
            TurnContext(
                scene=envelope.scene,
                current_step_id=current_step_id,
                recognized_text=transcript,
                attempts=attempts,
                history=history,
                help_used=help_used,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_step", "message": str(exc)},
        ) from exc

    services.events.log(
        "turn_completed",
        {
            "theme": envelope.scene.theme.value,
            "difficulty": envelope.scene.difficulty.value,
            "success": result.accepted,
            "stars": result.stars_earned,
            "turns": len(history) + 1,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "error_type": result.error_type or "none",
        },
    )
    return result


@router.post("/api/event")
async def record_event(
    payload: EventRequest,
    services: Services = Depends(get_services),
):
    try:
        services.events.log(payload.name.value, payload.properties)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_event", "message": str(exc)},
        ) from exc
    return {"ok": True}

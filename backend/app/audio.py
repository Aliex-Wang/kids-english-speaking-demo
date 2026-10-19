import subprocess
import tempfile
from pathlib import Path


class AudioConversionError(ValueError):
    """Raised when uploaded audio cannot be converted for ASR."""


def convert_to_wav_16k_mono(
    audio: bytes,
    content_type: str,
    timeout_seconds: float = 10.0,
) -> bytes:
    if not audio:
        raise AudioConversionError("empty audio")

    with tempfile.TemporaryDirectory() as temp_dir:
        source = Path(temp_dir) / "input"
        source.write_bytes(audio)
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            "pipe:1",
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise AudioConversionError("audio conversion timed out") from exc
        except OSError as exc:
            raise AudioConversionError(
                f"ffmpeg is not available for {content_type}"
            ) from exc

        if completed.returncode != 0 or not completed.stdout:
            stderr = completed.stderr.decode("utf-8", "ignore")[:300]
            raise AudioConversionError(f"ffmpeg failed: {stderr}")
        return completed.stdout

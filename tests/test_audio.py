import io
import shutil
import subprocess
import wave

import pytest

from app.audio import AudioConversionError, convert_to_wav_16k_mono
from app.providers.fake import make_silence_wav


def test_empty_audio_is_rejected():
    with pytest.raises(AudioConversionError):
        convert_to_wav_16k_mono(b"", "audio/webm")


def test_already_asr_ready_wav_skips_ffmpeg(monkeypatch):
    source = make_silence_wav(0.2)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("ffmpeg should not be called for ASR-ready WAV")

    monkeypatch.setattr(subprocess, "run", fail_if_called)
    assert convert_to_wav_16k_mono(source, "audio/wav") == source


def test_ffmpeg_command_targets_16k_mono(monkeypatch):
    captured = {}

    def fake_run(command, capture_output, timeout):
        captured["command"] = command
        captured["timeout"] = timeout
        return subprocess.CompletedProcess(command, 0, stdout=b"RIFFok", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = convert_to_wav_16k_mono(b"input", "audio/webm", timeout_seconds=3)
    assert result == b"RIFFok"
    assert "-ac" in captured["command"]
    assert captured["command"][captured["command"].index("-ac") + 1] == "1"
    assert "-ar" in captured["command"]
    assert captured["command"][captured["command"].index("-ar") + 1] == "16000"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_real_conversion_returns_16k_mono_wav():
    source = make_silence_wav(0.2, sample_rate=44100)
    converted = convert_to_wav_16k_mono(source, "audio/wav")
    with wave.open(io.BytesIO(converted), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == 16000
        assert wav.getsampwidth() == 2

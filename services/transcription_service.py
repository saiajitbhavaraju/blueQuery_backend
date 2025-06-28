# ----------------------------------------------------------------------
# File: services/transcription_service.py
# ----------------------------------------------------------------------
from faster_whisper import WhisperModel

class TranscriptionService:
    def __init__(self):
        # Using a small, fast model. It will be downloaded on first use.
        # For higher accuracy, you could use "medium" or "large-v3".
        model_size = "tiny.en"
        # This will download the model into the container.
        # For production, we would map a volume to cache this model.
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print(f"Whisper STT model '{model_size}' loaded.")

    def transcribe(self, audio_path: str) -> str:
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        
        print(f"Detected language '{info.language}' with probability {info.language_probability}")

        full_transcript = "".join(segment.text for segment in segments)
        print(f"Transcription complete: '{full_transcript}'")
        return full_transcript
from google.genai import types

from youtube.domain.speaker_diarization import SpeakerDiarizationResult

transcript_normalize_config = types.GenerateContentConfig(
    temperature=0
)

speaker_diarization_config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=SpeakerDiarizationResult,
    temperature=0
)
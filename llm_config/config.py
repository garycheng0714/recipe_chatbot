from google.genai import types

from youtube.domain.models.qa_pair_result import QAPairResult
from youtube.domain.speaker_diarization_result import SpeakerDiarizationResult

transcript_normalize_config = types.GenerateContentConfig(
    temperature=0
)

speaker_diarization_config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=SpeakerDiarizationResult,
    temperature=0
)

qa_pair_config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=QAPairResult,
    temperature=0
)
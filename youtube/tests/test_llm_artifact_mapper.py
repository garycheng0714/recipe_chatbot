from youtube.domain.mapper.llm_artifact import LLMArtifactMapper
from youtube.domain.speaker_diarization import SpeakerDiarizationResult, QA
from youtube.ids import get_source_id, get_section_id


def test_llm_artifact_mapper():
    source_id = get_source_id("https://google.com")
    section_id = get_section_id(source_id, 0)

    output = "123"

    result =LLMArtifactMapper.from_output(
        section_id=section_id,
        stage="transcript normalize",
        output=output
    )

    assert result.output== "123"
    assert result.stage == "transcript normalize"


def test_llm_artifact_mapper_with_speaker_diarization_output():
    source_id = get_source_id("https://google.com")
    section_id = get_section_id(source_id, 0)

    output = SpeakerDiarizationResult(conversation=[QA(speaker="interviewer", text="Hello World")])

    result = LLMArtifactMapper.from_output(
        section_id=section_id,
        stage="speaker diarization",
        output=output.model_dump(),
    )

    assert result.output == output.model_dump()
    assert result.stage == "speaker diarization"
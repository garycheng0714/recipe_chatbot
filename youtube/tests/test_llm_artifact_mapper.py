from youtube.domain.mapper.llm_artifact import LLMArtifactMapper
from youtube.domain.normalize_result import NormalizeResult
from youtube.ids import get_source_id, get_section_id


def test_llm_artifact_mapper():
    source_id = get_source_id("https://google.com")
    section_id = get_section_id(source_id, 0)

    output = NormalizeResult(cleaned_text="123")

    result =LLMArtifactMapper.from_output(
        section_id=section_id,
        output=output.model_dump(),
    )

    assert result.output["cleaned_text"] == "123"
    assert result.stage == "transcript normalize"
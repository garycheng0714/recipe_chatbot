from youtube.domain.mapper.llm_artifact import LLMArtifactMapper
from youtube.ids import get_source_id, get_section_id


def test_llm_artifact_mapper():
    source_id = get_source_id("https://google.com")
    section_id = get_section_id(source_id, 0)

    output = "123"

    result =LLMArtifactMapper.from_output(
        section_id=section_id,
        output=output,
    )

    assert result.output== "123"
    assert result.stage == "transcript normalize"
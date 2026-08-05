from pydantic import BaseModel, Field


class SectionQuestionContent(BaseModel):
    """
    each chunk is delimited like: [chunk_id: C123] ... text ... [/chunk_id]
    """
    section: str
    chunks: str


class SectionQuestionOutput(BaseModel):
    question: str = Field(description="The question that generated from a concept")
    based_on_concept: str = Field(description="The concept from section content")
    relevant_ids: list[str] = Field(description="The ids of the chunks that directly and clearly answers the question")


class SectionQuestionGeneratorPrompt:

    @staticmethod
    def render(content: SectionQuestionContent) -> str:
        return f"""
You are generating evaluation questions (a "golden set") for a retrieval system
that indexes YouTube interview transcripts. You will be given one Section,
broken into numbered Chunks with their chunk_id.

## Section content
{content.section}

## Chunks
{content.chunks}

## Task
Work in two steps.

### Step 1 — Identify key concepts
Read the section and list the important, substantive concepts it covers
(e.g. a specific training method, a named event, a stated opinion or
principle). Skip filler, transitional dialogue, or anything too minor to
be worth testing retrieval on. For each concept, note which chunk_id(s)
it appears in.

### Step 2 — Generate questions per concept
For each concept from Step 1, generate one question a real user might
plausibly ask that a) is fully answerable using only this section, and
b) centers on that concept. Then:

1. List the exact chunk_id(s) needed to answer the question (may span
   multiple chunks if the concept's explanation continues across them).
   Only include a chunk_id if it's truly necessary.
   
2. Avoid yes/no questions and anything answerable from general knowledge
   without this specific transcript.

If a concept is too thin to support a good question, drop it rather than
forcing one — fewer, higher-quality questions are better than hitting a
target count.

"""
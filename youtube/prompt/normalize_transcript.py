from youtube.prompt.base import BasePrompt


class NormalizeTranscriptPrompt(BasePrompt):

    def render(self, content: str) -> str:
        return f"""
You are an editor.

Input:
- youtube transcript.

Tasks:
- Remove filler words.
- Add punctuation.
- Correct the obvious typos.
- Split into paragraphs.

Rules:
1. Do NOT summarize.
2. Do NOT rewrite meaning.
3. Preserve every fact.

Transcript:
{content}
        """
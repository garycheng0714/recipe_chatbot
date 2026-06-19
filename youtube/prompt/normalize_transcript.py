from youtube.prompt.base import BasePrompt


class NormalizeTranscriptPrompt(BasePrompt):

    def render(self, content: str) -> str:
        return f"""
You are an editor.

Input:
- Automatic speech recognition transcript.

Tasks:
- Remove filler words.
- Add punctuation.
- Split into paragraphs.
- Separate interviewer and interviewee

Rules:
1. Do NOT summarize.
2. Do NOT rewrite meaning.
3. Preserve every fact.

Transcript:
{content}
        """
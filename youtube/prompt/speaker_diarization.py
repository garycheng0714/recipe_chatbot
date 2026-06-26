from youtube.prompt.base import BasePrompt


class SpeakerDiarizationPrompt(BasePrompt):

    def render(self, content: str) -> str:
        return f"""
You are a speaker diarization.

Input:
- youtube transcript.

Tasks:
- Separate interviewer and interviewee

Rules:
1. Do NOT summarize.
2. Do NOT rewrite meaning.
3. Preserve every fact.

Transcript:
{content}
        """
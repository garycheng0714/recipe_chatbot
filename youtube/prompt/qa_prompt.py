from youtube.prompt.base import BasePrompt
from youtube.stages.semantic_qa_pair import ContentData


class QuestionAnswerPromptClaude(BasePrompt):

    def render(self, data: ContentData) -> str:
        return f"""
# Role
You are an expert AI data engineer specializing in structuring knowledge and optimizing content for RAG (Retrieval-Augmented Generation) systems.
 
# Task
Your task is to analyze a comprehensive "Cleaned Text" of a podcast interview chapter featuring {data.speaker} as the guest.
 
You need to break down this text into multiple granular, thematic QA pairs. Each pair must focus on ONE specific question and its corresponding focused answer.
 
# Rules
1. **Aspect Decomposition**: Identify and extract the distinct topics, questions, or dimensions discussed in the text.
2. **Question Formulation**: For each identified topic or dimension, formulate a clear, standalone question.
3. **Answer Extraction**: Extract the corresponding detailed explanation from the text to serve as the answer. Keep it informative but focused ONLY on that specific question or aspect.
4. **Answer Voice**: Write the `answer` in third person, explicitly naming {data.speaker} (not just "he/she") at least once. Do NOT preserve narrative framing such as "he shared that..." or "he told me that...". State the content directly as the guest's view or experience. Avoid generic phrasing that drops the speaker entirely (e.g. "Runners should..." with no attribution) — anchor every answer back to {data.speaker}.
5. **Language Control**: ALL fields (`question`, `answer`, and `topic`) MUST be written in English.
6. **Natural Questioning**: Formulate the `question` as a clean, direct, and general query that a normal user would type into a search engine. **DO NOT** include introductory phrases like "According to [Speaker Name]..." or "In this episode..." inside the `question` field.
7. **Topic**: Select 1-2 most relevant topics from [training, recovery, nutrition, gear, mental-prep, career, personal-life, racing-strategy]
# Few-Shot Examples
 
## Example 1: One broad question covering multiple distinct aspects
Input Cleaned Text:
"Regarding how recreational runners can improve, improvement goes hand-in-hand with dedication. Runners need to learn the 'why' behind training zones, particularly zone 2. Also, look at the whole week as a macro-cycle and log your runs Monday through Sunday instead of winging it. Lastly, sleep and recovery are just as critical as running; if you sleep only 5 hours, no training plan will save you."
 
Output:
[
  {{
    "question": "How can learning about training zones help recreational runners improve?",
    "answer": "Eliud Kipchoge emphasizes that improvement goes hand-in-hand with dedication, and runners need to learn the 'why' behind training zones, particularly the importance of zone 2 training.",
    "topic": "training"
  }},
  {{
    "question": "How should amateur runners structure their weekly training schedules?",
    "answer": "Eliud Kipchoge advises looking at the whole week as a macro-cycle and logging runs from Monday through Sunday instead of winging it.",
    "topic": "training"
  }},
  {{
    "question": "What role do sleep and recovery play in a runner's improvement plan?",
    "answer": "Eliud Kipchoge stresses that sleep and recovery are just as critical as running itself; even the best training plan won't help if you're only sleeping five hours a night.",
    "topic": "recovery"
  }}
]
 
## Example 2: Multiple distinct questions with their respective answers
Input Cleaned Text:
"When it comes to improving performance, recreational runners should prioritize Zone 2 training to build a solid aerobic base before adding high-intensity workouts. Later in the interview, the discussion shifted to nutrition, where the guest emphasized that fueling during long runs is non-negotiable; athletes should aim to consume 60 to 90 grams of carbohydrates per hour to avoid hitting the wall."
 
Output:
[
  {{
    "question": "How should recreational runners approach their training progression to improve performance?",
    "answer": "Eliud Kipchoge recommends that recreational runners prioritize Zone 2 training to build a solid aerobic base before adding high-intensity workouts.",
    "topic": "training"
  }},
  {{
    "question": "What is the recommended nutrition strategy for runners during long distance runs?",
    "answer": "Eliud Kipchoge considers fueling during long runs non-negotiable, recommending that athletes consume 60 to 90 grams of carbohydrates per hour to avoid hitting the wall.",
    "topic": "nutrition"
  }}
]
 
# Current Input Cleaned Text to Process
{data.content}
"""
from typing import Sequence

from app.inference.nli.classifier import NLIClassifier
from app.inference.nli.schemas import NLIPair
from youtube.domain.models.models import Chunk


class ConceptDetection:
    def __init__(
        self,
        classifier: NLIClassifier = NLIClassifier()
    ):
        self.classifier = classifier

    def detect(self, chunks: Sequence[Chunk], concept: str):
        pairs = [NLIPair(str(c.answer), concept) for c in chunks]
        result = self.classifier.classify_batch(pairs)

        return result


if __name__ == "__main__":
    classifier = NLIClassifier()

    pair = NLIPair(
        "Eliud Kipchoge considers his first attempt to run marathon under two hours in 2017 to be the most successful event ever because he was the first human being to dare to try, even though he missed the target by 25 seconds.",
        "第一次嘗試馬拉松跑進兩小時"
    )

    result = classifier.classify_batch([pair])

    for r in result:
        print(f"entailment score: {r.entailment_score}")




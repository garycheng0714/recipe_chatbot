from unittest.mock import patch

import torch

from app.inference.nli.classifier import NLIClassifier
from app.inference.nli.schemas import NLIResult, NliLabel, NLIPair


class FakeTokenizer:
    def __call__(
        self,
        premises,
        hypotheses,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt",
    ):
        batch_size = len(premises)

        return {
            "input_ids": torch.ones(
                (batch_size, 10),
                dtype=torch.long,
            ),
            "attention_mask": torch.ones(
                (batch_size, 10),
                dtype=torch.long,
            ),
        }


class FakeModelConfig:
    id2label = {
        0: "contradiction",
        1: "neutral",
        2: "entailment",
    }


class FakeModel:

    def __init__(self):
        self.config = FakeModelConfig()

    def to(self, device):
        return self

    def eval(self):
        pass

    def __call__(self, **kwargs):

        batch_size = kwargs["input_ids"].shape[0]

        # 模擬：
        # contradiction=0.1
        # neutral=0.2
        # entailment=0.7
        logits = torch.tensor(
            [
                [ 0.3034, -1.3657, 0.9857 ]
            ] * batch_size
        )

        class Output:
            pass

        output = Output()
        output.logits = logits

        return output


def create_classifier():

    with (
        patch(
            "app.inference.nli.classifier.AutoTokenizer.from_pretrained",
            return_value=FakeTokenizer(),
        ),
        patch(
            "app.inference.nli.classifier.AutoModelForSequenceClassification.from_pretrained",
            return_value=FakeModel(),
        ),
    ):
        return NLIClassifier(
            device="cpu",
            batch_size=2,
        )


def test_classify_returns_entailment():

    classifier = create_classifier()

    result = classifier.classify(
        premise="The runner trains daily.",
        hypothesis="The athlete practices every day.",
    )

    assert isinstance(result, NLIResult)

    assert result.label == NliLabel.ENTAILMENT

    assert result.entailment_score > 0.6


def test_classify_batch():

    classifier = create_classifier()

    pairs = [
        (
            "Runner trains daily",
            "Athlete practices every day",
        ),
        (
            "He likes running",
            "He enjoys jogging",
        ),
        (
            "He hates running",
            "He loves running",
        ),
    ]

    inputs = [
        NLIPair(
            premise=a,
            hypothesis=b,
        )
        for a, b in pairs
    ]


    results = classifier.classify_batch(inputs)


    assert len(results) == 3

    for result in results:
        assert result.label == NliLabel.ENTAILMENT
        assert 0 <= result.entailment_score <= 1


def test_label_mapping():

    classifier = create_classifier()

    mapping = classifier.label_mapping

    assert mapping[NliLabel.CONTRADICTION] == 0
    assert mapping[NliLabel.NEUTRAL] == 1
    assert mapping[NliLabel.ENTAILMENT] == 2


def test_bidirectional_classification():

    classifier = create_classifier()


    result = classifier.classify_bidirectional(
        "How to improve running?",
        "How can I run better?",
    )


    assert result.forward.label == NliLabel.ENTAILMENT

    assert result.backward.label == NliLabel.ENTAILMENT

    assert result.both_entailment is True

    assert result.min_entailment_score > 0.6
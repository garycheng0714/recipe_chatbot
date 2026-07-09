from __future__ import annotations

from typing import Iterable, Sequence

import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.inference.nli.schemas import NLIPair, NLIResult, BidirectionalNLIResult, NliLabel


class NLIClassifier:
    """
    Batch-capable NLI classifier using Hugging Face sequence classification models.

    Designed for models like:
    - MoritzLaurer/mDeBERTa-v3-base-mnli-xnli
    """

    def __init__(
        self,
        model_name: str = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        device: str | None = None,
        batch_size: int = 16,
        max_length: int = 256,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length

        self.device = self._resolve_device(device)

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

        self.label_mapping = self._build_label_mapping(self.model.config.id2label)

    # =========================
    # Public API
    # =========================

    def classify(self, premise: str, hypothesis: str, pair_id: str | None = None) -> NLIResult:
        """
        Classify a single (premise, hypothesis) pair.
        """
        results = self.classify_batch([NLIPair(premise=premise, hypothesis=hypothesis, pair_id=pair_id)])
        return results[0]

    def classify_batch(self, pairs: Sequence[NLIPair]) -> list[NLIResult]:
        """
        Batch classify a list of NLIPair.
        """
        if not pairs:
            return []

        results: list[NLIResult] = []

        for batch in self._batched(pairs, self.batch_size):
            premises = [p.premise for p in batch]
            hypotheses = [p.hypothesis for p in batch]

            inputs = self.tokenizer(
                premises,
                hypotheses,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                logits = self.model(**inputs).logits
                probs = F.softmax(logits, dim=-1).cpu()

            for pair, prob in zip(batch, probs):
                results.append(self._build_result(pair, prob))

        return results

    def classify_bidirectional(
        self,
        text_a: str,
        text_b: str,
    ) -> BidirectionalNLIResult:
        """
        Run:
        - text_a -> text_b
        - text_b -> text_a
        """
        forward, backward = self.classify_batch(
            [
                NLIPair(premise=text_a, hypothesis=text_b),
                NLIPair(premise=text_b, hypothesis=text_a),
            ]
        )

        return BidirectionalNLIResult(
            text_a=text_a,
            text_b=text_b,
            forward=forward,
            backward=backward,
        )

    def classify_bidirectional_batch(
        self,
        text_pairs: Sequence[tuple[str, str]],
    ) -> list[BidirectionalNLIResult]:
        """
        Batch version of bidirectional classification.

        Input:
            [
                ("q1", "q2"),
                ("q3", "q4"),
            ]

        Internally expands into:
            q1->q2, q2->q1, q3->q4, q4->q3
        """
        if not text_pairs:
            return []

        expanded_pairs: list[NLIPair] = []
        for idx, (text_a, text_b) in enumerate(text_pairs):
            expanded_pairs.append(
                NLIPair(
                    premise=text_a,
                    hypothesis=text_b,
                    pair_id=f"{idx}:forward",
                )
            )
            expanded_pairs.append(
                NLIPair(
                    premise=text_b,
                    hypothesis=text_a,
                    pair_id=f"{idx}:backward",
                )
            )

        raw_results = self.classify_batch(expanded_pairs)

        grouped: list[BidirectionalNLIResult] = []
        for idx, (text_a, text_b) in enumerate(text_pairs):
            forward = raw_results[idx * 2]
            backward = raw_results[idx * 2 + 1]
            grouped.append(
                BidirectionalNLIResult(
                    text_a=text_a,
                    text_b=text_b,
                    forward=forward,
                    backward=backward,
                )
            )
        return grouped

    # =========================
    # Internal helpers
    # =========================

    def _build_result(self, pair: NLIPair, prob: torch.Tensor) -> NLIResult:
        entailment_score = float(prob[self.label_mapping[NliLabel.ENTAILMENT]])
        neutral_score = float(prob[self.label_mapping[NliLabel.NEUTRAL]])
        contradiction_score = float(prob[self.label_mapping[NliLabel.CONTRADICTION]])

        label = self._argmax_label(
            entailment_score=entailment_score,
            neutral_score=neutral_score,
            contradiction_score=contradiction_score,
        )

        return NLIResult(
            premise=pair.premise,
            hypothesis=pair.hypothesis,
            label=label,
            entailment_score=entailment_score,
            neutral_score=neutral_score,
            contradiction_score=contradiction_score,
            pair_id=pair.pair_id,
        )

    def _argmax_label(
        self,
        entailment_score: float,
        neutral_score: float,
        contradiction_score: float,
    ) -> NliLabel:
        scores = {
            NliLabel.ENTAILMENT: entailment_score,
            NliLabel.NEUTRAL: neutral_score,
            NliLabel.CONTRADICTION: contradiction_score,
        }
        return max(scores, key=scores.get)

    def _build_label_mapping(self, id2label: dict[int, str]) -> dict[NliLabel, int]:
        """
        Normalize model label names and map them to our canonical NliLabel enum.

        Handles labels like:
        - entailment / neutral / contradiction
        - ENTAILMENT / NEUTRAL / CONTRADICTION
        - contradiction / entailment / neutral in arbitrary order
        """
        normalized: dict[str, int] = {}
        for idx, label in id2label.items():
            normalized[str(label).strip().lower()] = idx

        required = {"entailment", "neutral", "contradiction"}
        missing = required - set(normalized.keys())
        if missing:
            raise ValueError(
                f"Model labels do not contain required NLI labels. "
                f"Found={normalized.keys()}, missing={missing}"
            )

        return {
            NliLabel.ENTAILMENT: normalized["entailment"],
            NliLabel.NEUTRAL: normalized["neutral"],
            NliLabel.CONTRADICTION: normalized["contradiction"],
        }

    def _resolve_device(self, device: str | None) -> torch.device:
        if device is not None:
            return torch.device(device)

        if torch.cuda.is_available():
            return torch.device("cuda")
        if torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    def _batched(self, items: Sequence[NLIPair], batch_size: int) -> Iterable[Sequence[NLIPair]]:
        for i in range(0, len(items), batch_size):
            yield items[i : i + batch_size]
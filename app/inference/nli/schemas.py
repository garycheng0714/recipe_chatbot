from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class NliLabel(str, Enum):
    ENTAILMENT = "entailment"
    NEUTRAL = "neutral"
    CONTRADICTION = "contradiction"


@dataclass(slots=True)
class NLIPair:
    premise: str
    hypothesis: str
    pair_id: Optional[str] = None


@dataclass(slots=True)
class NLIResult:
    premise: str
    hypothesis: str
    label: NliLabel
    entailment_score: float
    neutral_score: float
    contradiction_score: float
    pair_id: Optional[str] = None

    @property
    def top_score(self) -> float:
        return max(
            self.entailment_score,
            self.neutral_score,
            self.contradiction_score,
        )

    @property
    def is_entailment(self) -> bool:
        return self.label == NliLabel.ENTAILMENT


@dataclass(slots=True)
class BidirectionalNLIResult:
    text_a: str
    text_b: str
    forward: NLIResult   # a -> b
    backward: NLIResult  # b -> a

    @property
    def min_entailment_score(self) -> float:
        return min(
            self.forward.entailment_score,
            self.backward.entailment_score,
        )

    @property
    def both_entailment(self) -> bool:
        return (
            self.forward.label == NliLabel.ENTAILMENT
            and self.backward.label == NliLabel.ENTAILMENT
        )
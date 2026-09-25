"""Actual respondent-derived user models used by the adaptive prototype."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserModel:
    key: str
    name: str
    source_respondent: int
    description: str
    experience: str
    coding_frequency: str
    programming_duration: str
    assistance_preference: str
    ai_reliance: float
    comfort_without_ai: str
    feature_priority: str

    @property
    def high_assistance(self) -> bool:
        return self.assistance_preference == "High assistance"


USER_MODELS = {
    "guided_builder": UserModel("guided_builder", "Guided Builder", 19, "A beginner respondent who codes rarely and prefers heavy assistance.", "Beginner", "Rarely", "6 months - 1 year", "High assistance", 5.0, "Not comfortable", "Error detection, debugging tools, and code execution/testing tools"),
    "independent_builder": UserModel("independent_builder", "Independent Builder", 15, "An advanced respondent with long experience and a preference for less intrusive help.", "Advanced", "A few times a week", "3+ years", "Minimal assistance", 2.0, "Somewhat comfortable", "Error detection, debugging tools, and code execution/testing tools"),
}

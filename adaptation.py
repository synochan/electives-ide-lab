"""Explicit adaptation rules for the prototype."""

from __future__ import annotations

from dataclasses import dataclass

from user_model import UserModel


@dataclass(frozen=True)
class Adaptation:
    hints_visible: bool
    detailed_feedback: bool
    autocomplete_enabled: bool
    formatting_enabled: bool
    ai_prominence: str
    debug_prominence: str
    assistance_text: str


def adapt(model: UserModel) -> Adaptation:
    if model.high_assistance:
        return Adaptation(True, True, True, True, "primary", "primary", "Guided mode: hints, explanations, formatting, and offline coding guidance are prominent because this model combines high assistance preference with high AI reliance and low comfort without AI.")
    return Adaptation(False, False, False, False, "secondary", "primary", "Independent mode: basic prompts are reduced and formatting is user-controlled, while error checking and debugging remain available because those features are important in the survey.")


RULES = [
    ("High assistance preference", "Show hints, explanations, autocomplete, and formatting controls.", "Observed preference score 4-5 is used to make assistance more visible."),
    ("Minimal assistance preference", "Hide routine hints and keep formatting user-controlled.", "Observed preference score 1-2 is used to reduce interruption."),
    ("AI reliance >= 4", "Make offline coding guidance a primary action.", "Higher reliance makes visible assistance more relevant to the model, even when no external AI service is used."),
    ("Comfort without AI is Not comfortable", "Use detailed feedback and beginner-oriented hints.", "The selected respondent reported low comfort without AI."),
    ("Any model", "Keep Check Code and Debug available.", "Error detection and debugging were highly rated features in the actual workbook."),
]

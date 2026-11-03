"""Helpers shared by the evaluation scripts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.objects import Answer


def final_answer(result: dict) -> str:
    """Plain answer text from an agent result.

    Prefers the structured Answer. Small models sometimes end with plain text,
    or with the Answer JSON as raw text, so unwrap that too.
    """
    structured = result.get("structured_response")
    if structured:
        return structured.answer

    text = str(result["messages"][-1].content)
    try:
        return Answer.model_validate_json(text).answer
    except ValueError:
        return text

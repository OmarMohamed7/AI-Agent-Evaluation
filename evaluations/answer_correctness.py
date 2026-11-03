# Evaluates whether the agent's final answer has the same meaning as the expected output and satisfies the request.
import sys
from pathlib import Path
from uuid import uuid4

from deepeval import evaluate
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams
from langchain.messages import HumanMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent import agent
from agent.objects import AgentContext
from common import final_answer
from datasets import dataset
from model import eval_model

# Authenticated user for goldens that don't set additional_metadata["user_id"].
DEFAULT_USER_ID = "2"

metrics = [
    # Custom metric: compares the agent's answer with the golden's expected output.
    GEval(
        name="Answer Correctness",
        threshold=0.8,
        model=eval_model,
        verbose_mode=True,
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.EXPECTED_OUTPUT,
        ],
        evaluation_steps=[
            "compare the decision, not the wording: approved vs denied vs declined as out of scope, the refund amount when approved, and whether a refund ticket was issued",
            "the actual output and the expected output must reach the same decision with the same refund amount; different phrasing, extra politeness or a shorter reply are fine",
            "a reply that asks the user for more information when the expected output approves or denies the request is incorrect",
            "if the answer is incorrect, explain why and what the correct answer should be",
        ],
    ),
]


def run_agent(user_input: str, user_id: str = DEFAULT_USER_ID) -> str:
    """Run the agent and return its final answer."""
    result = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config={"configurable": {"thread_id": str(uuid4())}},
        context=AgentContext(user_id=user_id),
    )
    return final_answer(result)


test_cases = []
for golden in dataset.goldens:
    try:
        answer = run_agent(
            golden.input,
            (golden.additional_metadata or {}).get("user_id", DEFAULT_USER_ID),
        )
    except Exception as e:
        print(
            f"Skipping golden, agent failed: {golden.input!r}\n  {type(e).__name__}: {e}"
        )
        continue

    test_cases.append(
        LLMTestCase(
            input=golden.input,
            actual_output=answer,
            expected_output=golden.expected_output,
        )
    )

if test_cases:
    evaluate(test_cases=test_cases, metrics=metrics)

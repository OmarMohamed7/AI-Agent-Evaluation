# Evaluates whether the agent passed correct arguments (item names, quantities) to the tools it called.
import sys
from pathlib import Path
from uuid import uuid4

from deepeval import evaluate
from deepeval.metrics import ArgumentCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall
from langchain.messages import HumanMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent import agent
from agent.objects import AgentContext
from agent.tools import all_tools
from common import final_answer
from datasets import dataset
from model import eval_model

# Authenticated user for goldens that don't set additional_metadata["user_id"].
DEFAULT_USER_ID = "2"


# Tools that take arguments. Zero-argument tools (history, date) get the customer
# from the authenticated session, so there is nothing for this metric to judge.
TOOLS_WITH_ARGS = {t.name for t in all_tools if t.args}

metrics = [
    ArgumentCorrectnessMetric(
        threshold=0.8,
        model=eval_model,
        include_reason=True,
    ),
]


def run_agent(user_input: str, user_id: str = DEFAULT_USER_ID) -> tuple[str, list[ToolCall]]:
    """Run the agent; return the final answer and the tools it called."""
    result = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config={"configurable": {"thread_id": str(uuid4())}},
        context=AgentContext(user_id=user_id),
    )
    answer = final_answer(result)

    # Calls to tools that take arguments (this also skips the structured "Answer" tool).
    tools_called = [
        ToolCall(name=call["name"], input_parameters=call["args"])
        for message in result["messages"]
        for call in getattr(message, "tool_calls", None) or []
        if call["name"] in TOOLS_WITH_ARGS
    ]
    return answer, tools_called


test_cases = []
for golden in dataset.goldens:
    try:
        answer, tools_called = run_agent(
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
            tools_called=tools_called,
        )
    )

if test_cases:
    evaluate(test_cases=test_cases, metrics=metrics)

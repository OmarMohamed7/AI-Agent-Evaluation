# Evaluates whether the agent called the expected tools (compared with expected_tools in the goldens).
import sys
from pathlib import Path
from uuid import uuid4

from deepeval import evaluate
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall
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
    ToolCorrectnessMetric(
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

    # Tool calls the model made. Skip the structured-output "Answer" tool.
    tools_called = [
        ToolCall(name=call["name"], input_parameters=call["args"])
        for message in result["messages"]
        for call in getattr(message, "tool_calls", None) or []
        if call["name"] != "Answer"
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
            expected_output=golden.expected_output,
            tools_called=tools_called,
            expected_tools=golden.expected_tools,
        )
    )

if test_cases:
    evaluate(test_cases=test_cases, metrics=metrics)

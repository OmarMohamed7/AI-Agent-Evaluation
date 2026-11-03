# Evaluates whether the agent reached its goal in as few, non-redundant steps (tool calls) as needed.
import sys
from pathlib import Path
from uuid import uuid4

from deepeval.metrics import StepEfficiencyMetric
from deepeval.tracing import observe, update_current_trace
from langchain.messages import HumanMessage
from deepeval.integrations.langchain import CallbackHandler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent import agent
from agent.objects import AgentContext
from datasets import dataset
from model import eval_model

# Authenticated user for goldens that don't set additional_metadata["user_id"].
DEFAULT_USER_ID = "2"

metrics = [
    StepEfficiencyMetric(
        threshold=0.8,
        model=eval_model,
        include_reason=True,
    ),
]


@observe()
def run_agent(
    user_input: str, expected_output: str | None = None, user_id: str = DEFAULT_USER_ID
) -> str:
    """Run the agent and expose only the final answer text to the metrics."""
    result = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config={
            "configurable": {"thread_id": str(uuid4())},
            "callbacks": [CallbackHandler()],
        },
        context=AgentContext(user_id=user_id),
    )
    structured = result.get("structured_response")
    # Small models sometimes end with plain text instead of calling the Answer tool.
    answer = structured.answer if structured else str(result["messages"][-1].content)
    update_current_trace(
        input=user_input, output=answer, expected_output=expected_output
    )
    return answer


for golden in dataset.evals_iterator(metrics=metrics):
    try:
        run_agent(
            golden.input,
            golden.expected_output,
            (golden.additional_metadata or {}).get("user_id", DEFAULT_USER_ID),
        )
    except Exception as e:
        print(
            f"Skipping golden, agent failed: {golden.input!r}\n  {type(e).__name__}: {e}"
        )

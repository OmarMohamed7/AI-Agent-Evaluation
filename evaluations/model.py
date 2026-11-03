import os

from dotenv import load_dotenv
from deepeval.models import DeepEvalBaseLLM
from pydantic import BaseModel

from agent.models import get_llm

load_dotenv()


class GatewayEvalModel(DeepEvalBaseLLM):
    """Lets DeepEval metrics use the provider chosen by the LLM gateway as the judge."""

    def __init__(self, model: str | None = None):
        self.llm = get_llm(model)
        self.model_name = getattr(self.llm, "model_name", None) or getattr(self.llm, "model", "judge")
        super().__init__(self.model_name)

    def load_model(self):
        return self.llm

    def generate(self, prompt: str, schema: type[BaseModel] | None = None):
        if schema is not None:
            return self.llm.with_structured_output(schema).invoke(prompt)
        return self.llm.invoke(prompt).content

    async def a_generate(self, prompt: str, schema: type[BaseModel] | None = None):
        if schema is not None:
            return await self.llm.with_structured_output(schema).ainvoke(prompt)
        return (await self.llm.ainvoke(prompt)).content

    def get_model_name(self) -> str:
        return str(self.model_name)


# The judge can use a different model: set EVAL_LLM_MODEL.
# Falls back to the agent's LLM_MODEL when unset.
eval_model = GatewayEvalModel(model=os.getenv("EVAL_LLM_MODEL"))

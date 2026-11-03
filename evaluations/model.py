from deepeval.models import DeepEvalBaseLLM
from pydantic import BaseModel

from agent.models import get_llm


class GatewayEvalModel(DeepEvalBaseLLM):
    """Lets DeepEval metrics use the provider chosen by the LLM gateway as the judge."""

    def __init__(self, provider: str | None = None, model: str | None = None):
        self.llm = get_llm(provider, model)
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


eval_model = GatewayEvalModel()

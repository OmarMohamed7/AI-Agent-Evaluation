import json
import os
import re

from dotenv import load_dotenv
from deepeval.models import DeepEvalBaseLLM
from langchain_core.exceptions import OutputParserException
from pydantic import BaseModel

from agent.models import get_llm

load_dotenv()


def _coerce_to_schema(raw: str, schema: type[BaseModel]) -> BaseModel:
    """Parse raw JSON from the judge and join list values into strings where the schema wants str."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    data = json.loads(match.group(0) if match else raw)
    for name, field in schema.model_fields.items():
        value = data.get(name)
        if field.annotation is str and isinstance(value, list):
            data[name] = "\n".join(str(v) for v in value)
    return schema.model_validate(data)


class GatewayEvalModel(DeepEvalBaseLLM):
    """Lets DeepEval metrics use the provider chosen by the LLM gateway as the judge."""

    def __init__(self, model: str | None = None):
        self.llm = get_llm(model)
        self.model_name = getattr(self.llm, "model_name", None) or getattr(self.llm, "model", "judge")
        super().__init__(self.model_name)

    def load_model(self):
        return self.llm

    @staticmethod
    def _json_prompt(prompt: str, schema: type[BaseModel]) -> str:
        return (
            f"{prompt}\n\nRespond with only a JSON object matching this schema "
            f"(string fields must be plain strings, not lists):\n{json.dumps(schema.model_json_schema())}"
        )

    def generate(self, prompt: str, schema: type[BaseModel] | None = None):
        if schema is not None:
            try:
                return self.llm.with_structured_output(schema).invoke(prompt)
            except OutputParserException:
                return _coerce_to_schema(self.llm.invoke(self._json_prompt(prompt, schema)).content, schema)
        return self.llm.invoke(prompt).content

    async def a_generate(self, prompt: str, schema: type[BaseModel] | None = None):
        if schema is not None:
            try:
                return await self.llm.with_structured_output(schema).ainvoke(prompt)
            except OutputParserException:
                resp = await self.llm.ainvoke(self._json_prompt(prompt, schema))
                return _coerce_to_schema(resp.content, schema)
        return (await self.llm.ainvoke(prompt)).content

    def get_model_name(self) -> str:
        return str(self.model_name)


# The judge can use a different model: set EVAL_LLM_MODEL.
# Falls back to the agent's LLM_MODEL when unset.
eval_model = GatewayEvalModel(model=os.getenv("EVAL_LLM_MODEL"))

import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()

# Default model per provider. Override with LLM_MODEL.
DEFAULT_MODELS = {
    "groq": "openai/gpt-oss-120b",
    "ollama": "llama3.1:8b",
    # "ollama": "qwen3.8:27b",
}


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0,
) -> BaseChatModel:
    """Gateway to pick the chat model.

    Reads LLM_PROVIDER ("groq" | "ollama") and LLM_MODEL from the environment
    when the arguments are not given. Ollama uses OLLAMA_BASE_URL
    (default http://localhost:11434).
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "groq")).lower()
    model = model or os.getenv("LLM_MODEL") or DEFAULT_MODELS.get(provider)

    if provider == "groq":
        from langchain_groq.chat_models import ChatGroq

        return ChatGroq(model=model, temperature=temperature)  # type: ignore

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model,  # type: ignore
            temperature=temperature,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER {provider!r}. Choose one of: {', '.join(DEFAULT_MODELS)}"
    )


llm = get_llm()

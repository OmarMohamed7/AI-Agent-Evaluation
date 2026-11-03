import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama

load_dotenv()

DEFAULT_MODEL = "gemma4:31b"  # served by Ollama cloud (https://ollama.com)


def get_llm(model: str | None = None, temperature: float = 0) -> BaseChatModel:
    """Ollama chat model (cloud by default).

    Reads LLM_MODEL (default gemma4:31b), OLLAMA_BASE_URL (default
    https://ollama.com) and OLLAMA_API_KEY from the environment. Set
    OLLAMA_BASE_URL=http://localhost:11434 to use a local server instead.
    """
    return ChatOllama(
        model=model or os.getenv("LLM_MODEL") or DEFAULT_MODEL,
        temperature=temperature,
        base_url=os.getenv("OLLAMA_BASE_URL", "https://ollama.com"),
        client_kwargs={
            "headers": {"Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY', '')}"}
        },
    )


llm = get_llm()

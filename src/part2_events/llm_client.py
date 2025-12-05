# src/part2_events/llm_client.py

import os
from pathlib import Path
from typing import Optional
from openai import OpenAI

# Load .env explicitly from project root
try:
    from dotenv import load_dotenv  # type: ignore

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass


def _get_api_key() -> str:
    api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return api_key


_client = OpenAI(api_key=_get_api_key())


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
) -> str:
    resp = _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content

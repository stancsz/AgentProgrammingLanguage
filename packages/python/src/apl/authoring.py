"""LiteLLM-powered authoring helpers for APL programs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os

from .env import load_env_defaults

try:  # pragma: no cover - import guarded for optional dependency
    import litellm
except Exception:  # pragma: no cover - handled at call site
    litellm = None


SYSTEM_PROMPT = """You are an assistant that writes Agent Programming Language (APL) code.
Return only APL source. Do not include Markdown fences or commentary.
Ensure the program compiles with the APL reference parser.
"""


@dataclass
class AuthoringConfig:
    """Configuration for LiteLLM-backed authoring."""

    model: Optional[str] = None
    temperature: float = 0.2
    mock: bool = False
    seed_program: Optional[Path] = None


class LiteLLMAuthor:
    """Generate APL programs from natural language briefs using LiteLLM."""

    def __init__(self, config: Optional[AuthoringConfig] = None) -> None:
        load_env_defaults()
        self.config = config or AuthoringConfig()

    def generate_program(self, prompt: str) -> str:
        """Generate an APL program for the supplied natural language prompt."""
        if self.config.mock or os.getenv("APL_LLM_MOCK", "").lower() in {"1", "true", "yes"}:
            return self._mock_program(prompt)

        if litellm is None:
            raise RuntimeError(
                "LiteLLM is not installed. Install with `pip install litellm` or enable mock mode."
            )

        model = (
            self.config.model
            or os.getenv("APL_LLM_MODEL")
            or os.getenv("LITELLM_MODEL")
            or "gpt-4o-mini"
        )
        temperature = float(os.getenv("APL_LLM_TEMPERATURE", self.config.temperature))

        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        try:
            content = response["choices"][0]["message"]["content"]
        except Exception as exc:  # pragma: no cover - defensive
            raise RuntimeError(f"Unexpected LiteLLM response structure: {response}") from exc

        return content.strip()

    def _mock_program(self, prompt: str) -> str:
        """Return a deterministic APL program for offline tests."""
        seed_path = self.config.seed_program
        if seed_path and seed_path.exists():
            return seed_path.read_text(encoding="utf-8")

        repo_root = Path(__file__).resolve().parents[4]
        example_customer = repo_root / "examples" / "customer_support.apl"
        example_hello = repo_root / "examples" / "hello.apl"

        text = prompt.lower()
        if "customer" in text or "support" in text:
            if example_customer.exists():
                return example_customer.read_text(encoding="utf-8")
        if example_hello.exists():
            return example_hello.read_text(encoding="utf-8")

        # Fallback minimal program to keep tests deterministic.
        return (
            "program demo(version=\"0.1\")\n\n"
            "agent demo_agent:\n"
            "  def run(name):\n"
            "    msg = call_llm(model=\"mock\", prompt=f\"Hello {name}\")\n"
            "    return msg\n"
        )


__all__ = ["LiteLLMAuthor", "AuthoringConfig"]

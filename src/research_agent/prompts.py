from __future__ import annotations

from importlib.resources import files
from pathlib import Path

_PROMPT_DIR = files("research_agent").joinpath("data/prompts")


def load_prompt(name: str) -> str:
    return Path(str(_PROMPT_DIR.joinpath(f"{name}.md"))).read_text(encoding="utf-8")


def render_prompt(name: str, replacements: dict[str, str]) -> str:
    prompt = load_prompt(name)
    for key, value in replacements.items():
        prompt = prompt.replace("{{" + key + "}}", value)
    return prompt

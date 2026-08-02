from pathlib import Path

import pytest

from research_agent.cli import main


def test_dry_run_needs_no_model_calls(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    question = tmp_path / "question.txt"
    question.write_text("A public research question", encoding="utf-8")

    with pytest.raises(SystemExit) as stopped:
        main(
            [
                "run",
                "--mode",
                "open",
                "--question-file",
                str(question),
                "--dry-run",
                "--no-price-refresh",
            ]
        )

    assert stopped.value.code == 0
    output = capsys.readouterr().out
    assert "openrouter/deepseek/deepseek-v4-pro" in output
    assert "Estimate:" in output

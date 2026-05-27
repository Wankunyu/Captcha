import openai
import pytest

from cognition import run_eval


def test_make_provider_supports_openrouter_openai_compatible_client(monkeypatch) -> None:
    calls = []

    class FakeOpenAI:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)

    provider = run_eval.make_provider(
        "openrouter",
        "qwen/qwen3-vl-235b-a22b-instruct",
        {
            "providers": {
                "openrouter": {
                    "api_key": "sk-test",
                    "http_referer": "https://example.invalid",
                    "x_title": "COGNITION revision experiments",
                }
            }
        },
        timeout_sec=30.0,
    )

    assert isinstance(provider, run_eval.OpenRouterProvider)
    assert calls == [
        {
            "api_key": "sk-test",
            "base_url": "https://openrouter.ai/api/v1",
            "timeout": 30.0,
            "default_headers": {
                "HTTP-Referer": "https://example.invalid",
                "X-Title": "COGNITION revision experiments",
            },
        }
    ]


def test_openrouter_requires_api_key(monkeypatch) -> None:
    class FakeOpenAI:
        def __init__(self, **kwargs):
            raise AssertionError("client must not be constructed without an API key")

    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)

    with pytest.raises(RuntimeError, match="OpenRouter"):
        run_eval.make_provider(
            "openrouter",
            "qwen/qwen3-vl-235b-a22b-instruct",
            {"providers": {"openrouter": {}}},
            timeout_sec=30.0,
        )

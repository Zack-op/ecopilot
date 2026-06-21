import core.llm_insight_generator as llm_insight_generator

from core.llm_insight_generator import (
    GeminiProvider,
    LLMInsightGenerator,
    LLMProviderError,
    OllamaProvider,
    OpenAIProvider,
    build_coach_prompt,
)


def _sample_carbon_result():
    """Return a representative completed carbon calculation."""

    return {"co2_kg": 0.0204, "energy_kwh": 0.0444}


def _sample_insight_result():
    """Return representative rule-based EcoPilot insights."""

    return {
        "top_drivers": ["High screen time", "Frequent charging"],
        "recommended_actions": [
            "Reduce screen time by 30 minutes.",
            "Avoid unnecessary charging cycles.",
        ],
    }


def _sample_goal_result():
    """Return a representative completed goal calculation."""

    return {"status": "above_target", "progress_percent": 86.4}


def test_selects_ollama_provider_when_server_and_model_are_available(monkeypatch):
    """Ollama should take priority when its configured model is installed."""

    monkeypatch.setattr(
        llm_insight_generator,
        "is_ollama_model_available",
        lambda model: True,
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    generator = LLMInsightGenerator()

    assert isinstance(generator.provider, OllamaProvider)


def test_selects_openai_provider_when_ollama_is_unavailable(monkeypatch):
    """OpenAI should take precedence when its key is configured."""

    monkeypatch.setattr(
        llm_insight_generator,
        "is_ollama_model_available",
        lambda model: False,
    )
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")

    generator = LLMInsightGenerator()

    assert isinstance(generator.provider, OpenAIProvider)


def test_selects_gemini_provider_when_only_gemini_key_is_available(monkeypatch):
    """Gemini should be selected when no OpenAI key is configured."""

    monkeypatch.setattr(
        llm_insight_generator,
        "is_ollama_model_available",
        lambda model: False,
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")

    generator = LLMInsightGenerator()

    assert isinstance(generator.provider, GeminiProvider)


def test_uses_deterministic_template_when_no_provider_key_exists(monkeypatch):
    """A missing API key must still return a useful coach message."""

    monkeypatch.setattr(
        llm_insight_generator,
        "is_ollama_model_available",
        lambda model: False,
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    generator = LLMInsightGenerator()
    result = generator.generate(
        _sample_carbon_result(),
        _sample_insight_result(),
        _sample_goal_result(),
    )

    assert generator.provider is None
    assert "20.4 grams of CO2" in result["coach_message"]
    assert "Reduce screen time by 30 minutes" in result["coach_message"]
    assert "86.4%" in result["coach_message"]
    assert len(result["coach_message"].split()) <= 100


def test_provider_failure_falls_back_to_local_template():
    """A failed remote request must not interrupt the coaching workflow."""

    class FailingProvider:
        """Provider double that simulates an unavailable LLM service."""

        def generate(self, prompt: str) -> str:
            raise LLMProviderError("service unavailable")

    result = LLMInsightGenerator(provider=FailingProvider()).generate(
        _sample_carbon_result(),
        _sample_insight_result(),
        _sample_goal_result(),
    )

    assert "20.4 grams of CO2" in result["coach_message"]


def test_ollama_failure_falls_back_to_openai(monkeypatch):
    """A failed Ollama request should continue to the next provider."""

    monkeypatch.setattr(
        llm_insight_generator,
        "is_ollama_model_available",
        lambda model: True,
    )

    def fail_ollama(self, prompt: str) -> str:
        raise LLMProviderError("Ollama unavailable")

    monkeypatch.setattr(OllamaProvider, "generate", fail_ollama)
    monkeypatch.setattr(
        OpenAIProvider,
        "generate",
        lambda self, prompt: "Local fallback reached OpenAI successfully.",
    )

    generator = LLMInsightGenerator(openai_api_key="openai-test-key")
    result = generator.generate(
        _sample_carbon_result(),
        _sample_insight_result(),
        _sample_goal_result(),
    )

    assert isinstance(generator.provider, OllamaProvider)
    assert result == {
        "coach_message": "Local fallback reached OpenAI successfully."
    }


def test_ollama_provider_uses_non_streaming_generate_response():
    """Ollama should extract text from its non-streaming generate response."""

    class StubOllamaProvider(OllamaProvider):
        """Ollama provider double that avoids a local HTTP request."""

        def _post(self, request_body):
            self.request_body = request_body
            return {"response": "Coach message"}

    provider = StubOllamaProvider()

    assert provider.generate("Prompt") == "Coach message"
    assert provider.request_body == {
        "model": "llama3:8b",
        "prompt": "Prompt",
        "stream": False,
        "options": {"num_predict": 150},
    }


def test_provider_output_is_not_word_truncated():
    """The prompt, not output slicing, should enforce the coach word limit."""

    message = " ".join(f"word{index}" for index in range(120))

    class LongResponseProvider:
        """Provider double that returns a complete long response."""

        def generate(self, prompt: str) -> str:
            return message

    result = LLMInsightGenerator(provider=LongResponseProvider()).generate(
        _sample_carbon_result(),
        _sample_insight_result(),
        _sample_goal_result(),
    )

    assert result["coach_message"] == message


def test_prompt_contains_only_structured_results_and_coaching_constraints():
    """The prompt should direct the LLM to explain existing calculations."""

    prompt = build_coach_prompt(
        _sample_carbon_result(),
        _sample_insight_result(),
        _sample_goal_result(),
    )

    assert "Do not calculate" in prompt
    assert "no more than 100 words" in prompt
    assert "single highest-impact improvement" in prompt
    assert "Do not use cheerleading" in prompt
    assert "20.4" in prompt
    assert "0.0444" in prompt
    assert "High screen time" in prompt
    assert "Reduce screen time by 30 minutes." in prompt
    assert "86.4" in prompt


def test_missing_data_uses_a_safe_template_message(monkeypatch):
    """Incomplete results should not crash local template generation."""

    monkeypatch.setattr(
        llm_insight_generator,
        "is_ollama_model_available",
        lambda model: False,
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = LLMInsightGenerator().generate({}, {}, {})

    assert result["coach_message"] == (
        "Today's smartphone footprint is not available yet. No specific "
        "smartphone usage drivers were available. Choose one manageable "
        "energy-saving habit to focus on today. Goal progress is not available "
        "yet."
    )

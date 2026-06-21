"""Natural-language sustainability coaching for precomputed EcoPilot results.

This module only explains values and recommendations calculated by the other
EcoPilot modules. It does not estimate carbon, set targets, or create rules.
"""

from __future__ import annotations

import json
import math
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
GEMINI_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_OLLAMA_MODEL = "llama3:8b"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
MAX_COACH_WORDS = 100
MAX_SUGGESTION_WORDS = 50
OLLAMA_NUM_PREDICT = 150


class LLMProviderError(RuntimeError):
    """Raised when a configured LLM provider cannot return a coach message."""


class LLMProvider(ABC):
    """Minimal interface shared by supported LLM providers."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a coaching message for the supplied prompt."""


class OllamaProvider(LLMProvider):
    """Ollama local API provider for EcoPilot coaching."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_OLLAMA_MODEL,
        timeout_seconds: float = 120.0,
    ) -> None:
        """Initialize the local Ollama provider for an installed model."""

        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        """Generate a coaching message through Ollama's local API."""

        response_body = self._post(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": OLLAMA_NUM_PREDICT},
            }
        )
        message = _extract_ollama_text(response_body)

        if not message:
            raise LLMProviderError("Ollama response did not include coach text")

        return message

    def _post(self, request_body: Mapping[str, Any]) -> Dict[str, Any]:
        """Send a JSON request to Ollama and decode its response."""

        request = Request(
            OLLAMA_GENERATE_URL,
            data=json.dumps(request_body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return _read_json_response(request, self.timeout_seconds, "Ollama")


class OpenAIProvider(LLMProvider):
    """OpenAI Responses API provider for EcoPilot coaching."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_OPENAI_MODEL,
        timeout_seconds: float = 15.0,
    ) -> None:
        """Initialize an OpenAI provider using the supplied API key."""

        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        """Generate a coaching message through the Responses API."""

        response_body = self._post(
            {
                "model": self.model,
                "input": prompt,
                "max_output_tokens": 220,
            }
        )
        message = _extract_openai_text(response_body)

        if not message:
            raise LLMProviderError("OpenAI response did not include coach text")

        return message

    def _post(self, request_body: Mapping[str, Any]) -> Dict[str, Any]:
        """Send a JSON request to OpenAI and decode its response."""

        request = Request(
            OPENAI_RESPONSES_URL,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        return _read_json_response(request, self.timeout_seconds, "OpenAI")


class GeminiProvider(LLMProvider):
    """Gemini GenerateContent API provider for EcoPilot coaching."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_GEMINI_MODEL,
        timeout_seconds: float = 15.0,
    ) -> None:
        """Initialize a Gemini provider using the supplied API key."""

        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        """Generate a coaching message through the GenerateContent API."""

        response_body = self._post(
            {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                "generationConfig": {"maxOutputTokens": 220},
            }
        )
        message = _extract_gemini_text(response_body)

        if not message:
            raise LLMProviderError("Gemini response did not include coach text")

        return message

    def _post(self, request_body: Mapping[str, Any]) -> Dict[str, Any]:
        """Send a JSON request to Gemini and decode its response."""

        encoded_model = quote(self.model, safe="")
        endpoint = (
            f"{GEMINI_GENERATE_URL}/{encoded_model}:generateContent"
            f"?key={quote(self.api_key, safe='')}"
        )
        request = Request(
            endpoint,
            data=json.dumps(request_body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return _read_json_response(request, self.timeout_seconds, "Gemini")


class LLMInsightGenerator:
    """Turn structured EcoPilot results into an optional coach explanation."""

    def __init__(
        self,
        provider: LLMProvider | None = None,
        *,
        openai_api_key: str | None = None,
        gemini_api_key: str | None = None,
    ) -> None:
        """Initialize a configured provider or deterministic local fallback."""

        self.providers = [provider] if provider is not None else select_llm_providers(
            openai_api_key=openai_api_key,
            gemini_api_key=gemini_api_key,
        )
        self.provider = self.providers[0] if self.providers else None

    def generate(
        self,
        carbon_result: Mapping[str, Any],
        insight_result: Mapping[str, Any],
        goal_result: Mapping[str, Any],
    ) -> Dict[str, str]:
        """Return a coach message without changing EcoPilot's calculations.

        The deterministic template is used when no provider is configured or a
        provider request fails, so LLM configuration can never block the core
        EcoPilot workflow.
        """

        fallback_message = build_local_coach_message(
            carbon_result,
            insight_result,
            goal_result,
        )

        if self.provider is None:
            return {"coach_message": fallback_message}

        prompt = build_coach_prompt(
            carbon_result,
            insight_result,
            goal_result,
        )

        for provider in self.providers:
            try:
                message = provider.generate(prompt)
                return {"coach_message": message.strip()}
            except LLMProviderError:
                continue

        return {"coach_message": fallback_message}

    def generate_implementation_suggestions(
        self,
        insight_result: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Generate implementation suggestions for each contributor action.
        
        Returns implementation ideas (2-3 per action) without generating
        the actions themselves. Actions must be provided by the Insight Generator.
        
        Args:
            insight_result: Result from generate_insights() containing contributors.
        
        Returns:
            A dict mapping contributor index to list of implementation suggestions.
        """
        
        contributors = insight_result.get("contributors", [])
        if not contributors:
            return {}
        
        suggestions_by_contributor = {}
        
        for idx, contributor in enumerate(contributors):
            action = contributor.get("action", "")
            if not action:
                continue
            
            # Generate suggestions for this action
            suggestions = self._generate_suggestions_for_action(action)
            if suggestions:
                suggestions_by_contributor[idx] = suggestions
        
        return suggestions_by_contributor
    
    def _generate_suggestions_for_action(self, action: str) -> list[str]:
        """Generate 2-3 practical implementation suggestions for an action.
        
        Args:
            action: The action provided by Insight Generator.
        
        Returns:
            List of 2-3 implementation suggestion strings.
        """
        
        fallback_suggestions = build_local_action_suggestions(action)
        
        if self.provider is None:
            return fallback_suggestions
        
        prompt = build_suggestion_prompt(action)
        
        for provider in self.providers:
            try:
                response = provider.generate(prompt)
                suggestions = _parse_suggestions_from_response(response)
                if suggestions:
                    return suggestions
            except LLMProviderError:
                continue
        
        return fallback_suggestions


def select_llm_provider(
    *,
    openai_api_key: str | None = None,
    gemini_api_key: str | None = None,
) -> LLMProvider | None:
    """Select the highest-priority available LLM provider.

    Provider priority is Ollama, OpenAI, Gemini, then the local template.
    """

    providers = select_llm_providers(
        openai_api_key=openai_api_key,
        gemini_api_key=gemini_api_key,
    )
    return providers[0] if providers else None


def select_llm_providers(
    *,
    openai_api_key: str | None = None,
    gemini_api_key: str | None = None,
) -> list[LLMProvider]:
    """Build available providers in Ollama, OpenAI, Gemini priority order."""

    providers: list[LLMProvider] = []
    ollama_model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    if is_ollama_model_available(ollama_model):
        providers.append(OllamaProvider(model=ollama_model))

    openai_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if openai_key:
        providers.append(
            OpenAIProvider(
                openai_key,
                model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
            )
        )

    gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
    if gemini_key:
        providers.append(
            GeminiProvider(
                gemini_key,
                model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
            )
        )

    return providers


def build_coach_prompt(
    carbon_result: Mapping[str, Any],
    insight_result: Mapping[str, Any],
    goal_result: Mapping[str, Any],
) -> str:
    """Build a prompt that limits the LLM to explaining existing results."""

    # Use contributors if available, otherwise fall back to drivers/actions
    contributors = insight_result.get("contributors", [])
    if contributors:
        contributors_data = [
            {
                "category": c.get("category"),
                "reason": c.get("reason"),
                "action": c.get("action"),
            }
            for c in contributors
        ]
        contributor_text = "Identified contributors (ranked by impact):\n"
        for c in contributors_data:
            contributor_text += f"* {c['category']}: {c['action']}\n"
    else:
        contributor_text = ""

    prompt_data = {
        "carbon_footprint_grams": _format_carbon_grams(carbon_result),
        "energy_kwh": _format_energy_kwh(carbon_result),
        "top_drivers": _string_items(insight_result.get("top_drivers")),
        "recommended_actions": _string_items(
            insight_result.get("recommended_actions")
        ),
        "contributors": contributors_data if contributors else [],
        "goal_status": _string_value(goal_result.get("status")),
        "goal_progress_percent": _format_progress_percent(goal_result),
    }
    structured_data = json.dumps(prompt_data, ensure_ascii=True)

    return (
        """ You are EcoPilot's sustainability coach.

Write a concise explanation of no more than 100 words.

The Intelligence Layer has already completed the analysis and identified:

* the carbon footprint
* the primary drivers
* the recommended actions
* the goal status

Do not perform additional analysis.

Your role is only to help the user understand the results in plain language.

Strict Rules:

* Use ONLY information provided in the structured input.
* Do NOT invent causes, statistics, percentages, devices, infrastructure, energy systems, manufacturing impacts, environmental impacts, or scientific explanations.
* Do NOT provide technical reasoning.
* Do NOT speculate.
* Do NOT introduce new recommendations.
* Do NOT change or recalculate any values.
* Do NOT mention information that is not present in the input.
* Do NOT add examples.
* Do NOT add assumptions.
* Do NOT explain how carbon emissions work.

Your goal is to help the user understand:

1. What behaviors were identified.
2. Why those behaviors were flagged in the analysis.
3. What actions were recommended.
4. How the recommended actions relate to the identified behaviors.

Style:

* concise
* practical
* intelligent
* clear
* evidence-based
* non-judgmental

Avoid:

* cheerleading
* motivational language
* corporate sustainability language
* exaggerated praise
* guilt-based language

Do not use phrases such as:

* "Great job"
* "Keep up the good work"
* "Let's make a positive impact together"

Response Structure:

1. State the carbon footprint.
2. State the identified behaviors or primary drivers.
3. Explain that these behaviors were identified as contributors in today's analysis.
4. State the recommended actions (maximum 2-3).
5. Briefly reference goal status if provided.
6. End the response.

If information is unavailable, briefly acknowledge it and continue using only the available data. \n\n"""
        f"Structured EcoPilot data: {structured_data}"
    )


def build_local_coach_message(
    carbon_result: Mapping[str, Any],
    insight_result: Mapping[str, Any],
    goal_result: Mapping[str, Any],
) -> str:
    """Create a deterministic coach message when remote LLMs are unavailable."""

    carbon_grams = _as_non_negative_float(carbon_result.get("co2_kg"))
    if carbon_grams is None:
        footprint_sentence = "Today's smartphone footprint is not available yet."
    else:
        footprint_sentence = (
            "Your smartphone generated approximately "
            f"{carbon_grams * 1000:.1f} grams of CO2 today."
        )

    # Use contributors if available, otherwise fall back to drivers
    contributors = insight_result.get("contributors", [])
    if contributors:
        # Build driver sentence from contributors
        if len(contributors) == 1:
            contrib = contributors[0]
            driver_sentence = f"The main driver was {contrib['category'].lower()}."
            driver_sentence += " Higher use requires more electricity from the device."
        else:
            categories = [f"{c['category'].lower()}" for c in contributors[:2]]
            driver_sentence = f"The main drivers were {', '.join(categories)}."
            driver_sentence += " Higher use requires more electricity from the device."
    else:
        # Fall back to top_drivers
        drivers = _string_items(insight_result.get("top_drivers"))
        if drivers:
            driver_sentence = f"The main driver was {drivers[0]}."
            if len(drivers) > 1:
                driver_sentence += f" Another notable factor was {drivers[1]}."
            driver_sentence += " Higher use requires more electricity from the device."
        else:
            driver_sentence = "No specific smartphone usage drivers were available."

    # Use contributors for actions if available
    if contributors:
        actions = [c.get("action") for c in contributors[:2]]
        actions = [a.rstrip('.') for a in actions if a]
        if actions:
            if len(actions) == 1:
                action_sentence = f"A simple next step is to {actions[0]}."
            else:
                action_sentence = f"Simple next steps are to {actions[0]} or {actions[1]}."
        else:
            action_sentence = "Choose one manageable energy-saving habit to focus on today."
    else:
        # Fall back to recommended_actions
        actions = _string_items(insight_result.get("recommended_actions"))
        if actions:
            action_sentence = f"A simple next step is to {actions[0].rstrip('.')}"
            action_sentence += "."
        else:
            action_sentence = "Choose one manageable energy-saving habit to focus on today."

    goal_sentence = _build_goal_sentence(goal_result)
    return _limit_words(
        " ".join(
            (
                footprint_sentence,
                driver_sentence,
                action_sentence,
                goal_sentence,
            )
        )
    )


def _read_json_response(
    request: Request,
    timeout_seconds: float,
    provider_name: str,
) -> Dict[str, Any]:
    """Return JSON from an LLM provider or raise a provider-specific error."""

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            response_body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise LLMProviderError(
            f"{provider_name} request failed with status {exc.code}"
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise LLMProviderError(f"{provider_name} request failed") from exc
    except json.JSONDecodeError as exc:
        raise LLMProviderError(
            f"{provider_name} response was not valid JSON"
        ) from exc

    if not isinstance(response_body, dict):
        raise LLMProviderError(f"{provider_name} response was not an object")

    return response_body


def is_ollama_model_available(model: str) -> bool:
    """Return whether a local Ollama server exposes the requested model."""

    request = Request(OLLAMA_TAGS_URL, method="GET")

    try:
        with urlopen(request, timeout=1.0) as response:
            response_body = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
        return False

    models = response_body.get("models") if isinstance(response_body, dict) else None
    if not isinstance(models, Sequence) or isinstance(models, (str, bytes)):
        return False

    available_models = {
        value
        for item in models
        if isinstance(item, Mapping)
        for value in (item.get("name"), item.get("model"))
        if isinstance(value, str)
    }
    return model in available_models


def _extract_ollama_text(response_body: Mapping[str, Any]) -> str:
    """Extract generated text from an Ollama generate response."""

    response_text = response_body.get("response")
    if isinstance(response_text, str) and response_text.strip():
        return response_text.strip()
    return ""


def _extract_openai_text(response_body: Mapping[str, Any]) -> str:
    """Extract generated text from an OpenAI Responses API payload."""

    output_text = response_body.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = response_body.get("output")
    if not isinstance(output, Sequence) or isinstance(output, (str, bytes)):
        return ""

    for item in output:
        if not isinstance(item, Mapping):
            continue
        content = item.get("content")
        if not isinstance(content, Sequence) or isinstance(content, (str, bytes)):
            continue
        for part in content:
            if not isinstance(part, Mapping):
                continue
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()

    return ""


def _extract_gemini_text(response_body: Mapping[str, Any]) -> str:
    """Extract generated text from a Gemini GenerateContent API payload."""

    candidates = response_body.get("candidates")
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
        return ""

    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        content = candidate.get("content")
        if not isinstance(content, Mapping):
            continue
        parts = content.get("parts")
        if not isinstance(parts, Sequence) or isinstance(parts, (str, bytes)):
            continue
        for part in parts:
            if not isinstance(part, Mapping):
                continue
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()

    return ""


def _format_carbon_grams(carbon_result: Mapping[str, Any]) -> str:
    """Format a precomputed carbon result for a no-calculation prompt."""

    co2_kg = _as_non_negative_float(carbon_result.get("co2_kg"))
    if co2_kg is None:
        return "unavailable"
    return f"{co2_kg * 1000:.1f}"


def _format_energy_kwh(carbon_result: Mapping[str, Any]) -> str:
    """Format the existing energy calculation for prompt context."""

    energy_kwh = _as_non_negative_float(carbon_result.get("energy_kwh"))
    if energy_kwh is None:
        return "unavailable"
    return f"{energy_kwh:.4f}"


def _format_progress_percent(goal_result: Mapping[str, Any]) -> str:
    """Format the existing goal progress value for prompt context."""

    progress_percent = _as_non_negative_float(goal_result.get("progress_percent"))
    if progress_percent is None:
        return "unavailable"
    return f"{progress_percent:.1f}"


def _build_goal_sentence(goal_result: Mapping[str, Any]) -> str:
    """Explain the existing goal status without changing its calculation."""

    status = _string_value(goal_result.get("status"))
    progress_percent = _as_non_negative_float(goal_result.get("progress_percent"))

    if progress_percent is None:
        return "Goal progress is not available yet."
    if status == "below_target":
        return "You are below your sustainability target today."
    if status == "on_target":
        return "You are on your sustainability target today."
    if status == "above_target":
        return (
            f"You are {progress_percent:.1f}% of the way toward your "
            "sustainability target, so you are close to meeting it."
        )
    return f"Your current sustainability goal progress is {progress_percent:.1f}%."


def _string_items(value: Any) -> list[str]:
    """Normalize optional result lists into non-empty text items."""

    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []

    return [str(item).strip() for item in value if str(item).strip()]


def _string_value(value: Any) -> str:
    """Normalize a single optional value to stripped text."""

    return value.strip() if isinstance(value, str) else ""


def _as_non_negative_float(value: Any) -> float | None:
    """Return a finite non-negative float or ``None`` for unavailable data."""

    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(converted) or converted < 0:
        return None
    return converted


def _limit_words(message: str) -> str:
    """Keep returned LLM and template messages within the coaching limit."""

    words = message.split()
    return " ".join(words[:MAX_COACH_WORDS])


def build_suggestion_prompt(action: str) -> str:
    """Build a prompt for generating implementation suggestions for an action.
    
    The LLM is strictly constrained to generate ONLY implementation suggestions,
    not to generate or modify the action itself.
    """
    
    prompt_data = {
        "action": action,
    }
    structured_data = json.dumps(prompt_data, ensure_ascii=True)
    
    return (
        """ You are helping users implement sustainability actions.

Your role: Generate 2-3 practical, low-friction ways to achieve the supplied action.

CRITICAL RULES:

* Do NOT generate a new action.
* Do NOT modify the supplied action.
* Do NOT suggest alternatives to the supplied action.
* Do NOT introduce new sustainability recommendations.
* Generate ONLY implementation ideas that directly support the supplied action.
* Ideas must be concrete, specific, and immediately actionable.
* Ideas must be low-friction (easy to adopt).
* Ideas must NOT contradict the supplied action.

Response Format:

Generate exactly 2-3 suggestions as concise bullet points.
Each suggestion should be 1 brief sentence.
No explanations or additional text.

Example input action: "Reduce video streaming by 30 minutes daily."

Example output:
- Watch one fewer episode per day.
- Set a fixed viewing window for streaming.
- Replace 30 minutes of streaming with another activity.

Now generate implementation suggestions for the supplied action. \n\n"""
        f"Structured data: {structured_data}"
    )


def build_local_action_suggestions(action: str) -> list[str]:
    """Generate deterministic implementation suggestions when LLM unavailable.
    
    Returns 2-3 practical ideas for implementing the given action.
    """
    
    action_lower = action.lower()
    
    # Video streaming
    if "video" in action_lower and "stream" in action_lower:
        return [
            "Watch one fewer episode per day.",
            "Set a fixed viewing window for streaming.",
            "Replace streaming time with offline activities.",
        ]
    
    # Screen time
    if "screen" in action_lower and "time" in action_lower:
        return [
            "Use grayscale mode to reduce engagement.",
            "Set app time limits in your device settings.",
            "Replace screen time with outdoor activities.",
        ]
    
    # Social media
    if "social" in action_lower or "social media" in action_lower:
        return [
            "Turn off notifications from social apps.",
            "Use app timers to limit daily usage.",
            "Replace social browsing with calls to friends.",
        ]
    
    # Charging
    if "charg" in action_lower:
        return [
            "Charge only once per day at a set time.",
            "Let the battery drain further before charging.",
            "Use battery saver mode to reduce charging frequency.",
        ]
    
    # Music streaming
    if "music" in action_lower and "stream" in action_lower:
        return [
            "Download playlists over Wi-Fi for offline listening.",
            "Use offline mode during commutes.",
            "Switch to local music files when possible.",
        ]
    
    # Generic fallback
    return [
        "Create a daily schedule for this activity.",
        "Set reminders to help maintain the new habit.",
        "Track progress to stay motivated.",
    ]


def _parse_suggestions_from_response(response: str) -> list[str]:
    """Extract bullet-point suggestions from LLM response.
    
    Looks for lines starting with '-' or '*' as suggestion markers.
    """
    
    suggestions = []
    lines = response.strip().split('\n')
    
    for line in lines:
        stripped = line.strip()
        # Extract bullet point suggestions
        if stripped.startswith('-') or stripped.startswith('*'):
            suggestion = stripped[1:].strip()
            if suggestion:
                # Limit to one sentence
                suggestion = suggestion.split('.')[0].strip() + '.'
                suggestions.append(suggestion)
    
    # Return up to 3 suggestions
    return suggestions[:3] if suggestions else []

"""Language normalisation — translates free-text to English via Azure Translator.

Uses the Translator endpoint exposed through the AI Services (Cognitive Services)
resource.  Auto-detects the source language and translates to English.

Required environment variable:
    AI_SERVICES_ENDPOINT  — e.g. https://<resource>.cognitiveservices.azure.com/

Authentication uses ``DefaultAzureCredential`` (Entra ID).
"""

import logging
import os

import requests
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

_TRANSLATE_API_VERSION = "2025-10-01-preview"
_TARGET_LANGUAGE = "en"
_SCOPE = "https://cognitiveservices.azure.com/.default"

_cached_credential: DefaultAzureCredential | None = None


def _get_credential() -> DefaultAzureCredential:
    global _cached_credential
    if _cached_credential is None:
        _cached_credential = DefaultAzureCredential()
    return _cached_credential


def normalise_to_english(text: str) -> str:
    """Translate *text* to English.  Returns the original text on any failure.

    This is intentionally non-blocking at the caller level: if translation
    fails for any reason the original text is returned so downstream search
    still works.
    """
    endpoint = os.environ.get("AI_SERVICES_ENDPOINT", "").rstrip("/")
    if not endpoint:
        logger.warning("AI_SERVICES_ENDPOINT not set — skipping translation")
        return text

    try:
        token = _get_credential().get_token(_SCOPE).token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        url = (
            f"{endpoint}/translator/text/translate"
            f"?api-version={_TRANSLATE_API_VERSION}"
        )
        body = {
            "inputs": [
                {
                    "Text": text,
                    "targets": [{"language": _TARGET_LANGUAGE}],
                }
            ]
        }

        response = requests.post(url, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        data = response.json()

        translated = data["value"][0]["translations"][0]["text"]
        detected = data["value"][0].get("detectedLanguage", {}).get("language", "unknown")
        if detected == _TARGET_LANGUAGE:
            logger.debug("Text already in English — no translation needed")
            return text
        logger.info("Translated from %s: %r -> %r", detected, text, translated)
        return translated

    except Exception:
        logger.exception("Translation failed — proceeding with original text")
        return text

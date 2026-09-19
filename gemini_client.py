"""
EduMind AI - Centralized Gemini API Client Module
Uses official Google GenAI Python SDK (google-genai).
Handles authentication, streaming responses, structured JSON quiz generation,
multimodal vision analysis, embedding generation, exponential backoff retries (503),
and seamless fallback model routing.
"""

import json
import logging
import io
import time
from typing import List, Dict, Any, Generator, Optional, Tuple
from PIL import Image
from google import genai
from google.genai import types
import config

logger = logging.getLogger("gemini_client")

# Custom Exception Hierarchy
class GeminiClientError(Exception):
    """Base exception for all Gemini operations."""
    pass

class ConfigurationError(GeminiClientError):
    """Raised when GEMINI_API_KEY or model configuration is missing."""
    pass

class AuthenticationError(GeminiClientError):
    """Raised when GEMINI_API_KEY is rejected."""
    pass

class RateLimitError(GeminiClientError):
    """Raised when Gemini API quota or rate limit (429) is exceeded."""
    pass

class ServiceUnavailableError(GeminiClientError):
    """Raised when Gemini service is temporarily down (503/500)."""
    pass

class ModelResponseError(GeminiClientError):
    """Raised when Gemini returns an empty or unparseable response."""
    pass

# Compatibility alias
GrokClientError = GeminiClientError


def is_api_key_configured() -> bool:
    """Check if a valid Gemini API Key is configured."""
    return config.is_gemini_api_key_configured()


def _get_client() -> genai.Client:
    """Centralized secure initialization of genai.Client."""
    key = config.get_gemini_api_key()
    if not key or key in ["your_api_key_here", "your_gemini_api_key_here"]:
        raise ConfigurationError("⚠️ Gemini API key is not configured. Please set `GEMINI_API_KEY` in environment variables or Streamlit secrets.")
    return genai.Client(api_key=key)


def _get_candidate_models(model_override: Optional[str] = None) -> List[str]:
    """
    Return ordered list of supported Gemini models to attempt.
    Primary model: config.PRIMARY_MODEL (gemini-3.5-flash)
    Fallback model: config.FALLBACK_MODEL (gemini-3.5-flash-lite)
    """
    models = []
    if model_override and model_override.strip():
        models.append(model_override.strip())

    primary = getattr(config, "PRIMARY_MODEL", config.get_gemini_model())
    if primary not in models:
        models.append(primary)

    fallback = getattr(config, "FALLBACK_MODEL", config.get_gemini_fallback_model())
    if fallback not in models:
        models.append(fallback)

    for fb in getattr(config, "GEMINI_MODEL_FALLBACKS", []):
        if fb not in models:
            models.append(fb)

    return models


def _classify_error(e: Exception) -> Tuple[str, bool]:
    """
    Classify Gemini exception into error category and return (category_name, is_retryable_on_same_model).
    """
    err_str = str(e)
    err_lower = err_str.lower()

    # 1. 503 UNAVAILABLE / TEMPORARY BUSY
    if any(k in err_str or k in err_lower for k in [
        "503", "unavailable", "high demand", "spikes in demand", "temporarily busy",
        "service unavailable", "overloaded", "deadline exceeded"
    ]):
        return ("503_UNAVAILABLE", True)

    # 2. 429 RESOURCE EXHAUSTED / RATE LIMIT
    if any(k in err_str or k in err_lower for k in [
        "429", "resource_exhausted", "quota", "rate limit"
    ]):
        return ("429_QUOTA", True)

    # 3. 404 NOT FOUND
    if any(k in err_str or k in err_lower for k in [
        "404", "not_found", "not found"
    ]):
        return ("NOT_FOUND", False)

    # 4. AUTHENTICATION / PERMISSION (401 / 403)
    if any(k in err_str or k in err_lower for k in [
        "401", "403", "unauthenticated", "permission_denied", "api_key_invalid", "invalid api key"
    ]):
        return ("AUTH", False)

    # 5. 400 INVALID ARGUMENT
    if any(k in err_str or k in err_lower for k in [
        "400", "invalid_argument"
    ]):
        return ("INVALID_ARG", False)

    # 6. OTHER 5XX SERVER ERRORS
    if any(k in err_str or k in err_lower for k in [
        "500", "502", "504", "internal"
    ]):
        return ("5XX_SERVER", True)

    return ("UNKNOWN_ERROR", False)


# Exponential backoff sequence: Attempt 1 (0s), Attempt 2 (2s), Attempt 3 (4s), Attempt 4 (8s), Attempt 5 (16s)
RETRY_DELAYS = [0, 2, 4, 8, 16]


def generate_chat_response_stream(
    messages: List[Dict[str, str]],
    document_context: str = "",
    subject: str = "",
    model_name: Optional[str] = None
) -> Generator[str, None, None]:
    """
    Generate a streaming chat response using official google-genai SDK.
    Handles 503 UNAVAILABLE with exponential backoff retries and fallback model switching.
    PRESERVES FULL PDF CONTEXT, SYSTEM INSTRUCTION, AND CONVERSATION CONTEXT ACROSS FALLBACKS.
    """
    client = _get_client()
    candidate_models = _get_candidate_models(model_name)

    user_prompt = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_prompt = msg.get("content", "")
            break

    if not user_prompt:
        yield "How can I help you with your studies today?"
        return

    prompt_parts = []
    if subject:
        prompt_parts.append(f"ACADEMIC SUBJECT: {subject}")
    if document_context:
        prompt_parts.append(f"RETRIEVED COURSE MATERIAL CONTEXT:\n{document_context}\n")
    prompt_parts.append(f"STUDENT QUESTION:\n{user_prompt}")

    full_prompt = "\n\n".join(prompt_parts)

    gen_config = types.GenerateContentConfig(
        system_instruction=config.SYSTEM_INSTRUCTION,
        temperature=config.GENERATION_CONFIG["temperature"],
        max_output_tokens=config.GENERATION_CONFIG["max_tokens"],
    )

    last_err = None
    for model_idx, model_id in enumerate(candidate_models):
        is_fallback = (model_idx > 0)
        if is_fallback:
            logger.info("Gemini primary model returned 503/error. Switching to fallback model '%s' (preserving full PDF context & student question)...", model_id)

        for attempt_idx, delay in enumerate(RETRY_DELAYS):
            attempt_num = attempt_idx + 1
            max_attempts = len(RETRY_DELAYS)

            if delay > 0:
                logger.info("Gemini model '%s' returned 503/transient error. Retry attempt %d/%d (delay: %ds)...", model_id, attempt_num, max_attempts, delay)
                time.sleep(delay)

            try:
                response = client.models.generate_content_stream(
                    model=model_id,
                    contents=full_prompt,
                    config=gen_config
                )
                has_yielded = False
                for chunk in response:
                    if chunk.text:
                        has_yielded = True
                        yield chunk.text
                if has_yielded:
                    if is_fallback:
                        logger.info("Fallback model '%s' successfully generated grounded response!", model_id)
                    return
            except Exception as e:
                err_str = str(e)
                err_type, is_retryable = _classify_error(e)
                logger.warning("Gemini model '%s' attempt %d/%d failed [%s]: %s", model_id, attempt_num, max_attempts, err_type, err_str)
                last_err = e

                if err_type == "AUTH":
                    raise AuthenticationError("⚠️ Gemini API Key is invalid or expired. Please check your API key.")
                elif err_type in ["NOT_FOUND", "INVALID_ARG"]:
                    break

                if not is_retryable:
                    break

    if last_err:
        err_type, _ = _classify_error(last_err)
        if err_type in ["503_UNAVAILABLE", "5XX_SERVER"]:
            raise ServiceUnavailableError("Gemini is temporarily busy. Please try again in a moment.")
        elif err_type == "429_QUOTA":
            raise RateLimitError("Gemini API quota limit reached. Please wait a moment before trying again.")
        else:
            raise GeminiClientError(f"Gemini is temporarily busy. Please try again in a moment.")

    yield "Gemini is temporarily busy. Please try again in a moment."


def generate_json_response(
    prompt: str,
    system_instruction: Optional[str] = None,
    model_name: Optional[str] = None
) -> Any:
    """
    Generate structured JSON output using google-genai SDK.
    Includes 503 exponential backoff retries and fallback model switching.
    """
    client = _get_client()
    candidate_models = _get_candidate_models(model_name)

    sys_inst = system_instruction or "You are an expert JSON generator. Output only valid JSON matching the requested schema."

    gen_config = types.GenerateContentConfig(
        system_instruction=sys_inst,
        temperature=0.2,
        response_mime_type="application/json",
    )

    last_err = None
    for model_idx, model_id in enumerate(candidate_models):
        is_fallback = (model_idx > 0)
        if is_fallback:
            logger.info("Switching to fallback model '%s' for JSON generation...", model_id)

        for attempt_idx, delay in enumerate(RETRY_DELAYS):
            attempt_num = attempt_idx + 1
            max_attempts = len(RETRY_DELAYS)

            if delay > 0:
                logger.info("Gemini JSON model '%s' returned 503/transient error. Retry attempt %d/%d (delay: %ds)...", model_id, attempt_num, max_attempts, delay)
                time.sleep(delay)

            try:
                resp = client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=gen_config
                )
                text = (resp.text or "").strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
                if text:
                    return json.loads(text)
            except Exception as e:
                err_str = str(e)
                err_type, is_retryable = _classify_error(e)
                logger.warning("Gemini JSON model '%s' attempt %d/%d failed [%s]: %s", model_id, attempt_num, max_attempts, err_type, err_str)
                last_err = e

                if err_type == "AUTH":
                    raise AuthenticationError("⚠️ Gemini API Key is invalid or expired. Please check your API key.")
                elif err_type in ["NOT_FOUND", "INVALID_ARG"]:
                    break

                if not is_retryable:
                    break

    if last_err:
        err_type, _ = _classify_error(last_err)
        if err_type in ["503_UNAVAILABLE", "5XX_SERVER"]:
            raise ServiceUnavailableError("Gemini is temporarily busy. Please try again in a moment.")
        elif err_type == "429_QUOTA":
            raise RateLimitError("Gemini API quota limit reached. Please wait a moment and try again.")
        else:
            raise GeminiClientError("Gemini is temporarily busy. Please try again in a moment.")

    raise GeminiClientError("Gemini is temporarily busy. Please try again in a moment.")


def generate_response(
    prompt: str,
    system_instruction: Optional[str] = None,
    model_name: Optional[str] = None
) -> str:
    """
    Generate a synchronous text response using google-genai SDK.
    Includes 503 exponential backoff retries and fallback model switching.
    """
    client = _get_client()
    candidate_models = _get_candidate_models(model_name)

    sys_inst = system_instruction or config.SYSTEM_INSTRUCTION
    gen_config = types.GenerateContentConfig(
        system_instruction=sys_inst,
        temperature=config.GENERATION_CONFIG["temperature"],
        max_output_tokens=config.GENERATION_CONFIG["max_tokens"],
    )

    last_err = None
    for model_idx, model_id in enumerate(candidate_models):
        is_fallback = (model_idx > 0)
        if is_fallback:
            logger.info("Switching to fallback model '%s' for sync response...", model_id)

        for attempt_idx, delay in enumerate(RETRY_DELAYS):
            attempt_num = attempt_idx + 1
            max_attempts = len(RETRY_DELAYS)

            if delay > 0:
                logger.info("Gemini sync model '%s' returned 503/transient error. Retry attempt %d/%d (delay: %ds)...", model_id, attempt_num, max_attempts, delay)
                time.sleep(delay)

            try:
                resp = client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=gen_config
                )
                if resp.text:
                    return resp.text.strip()
            except Exception as e:
                err_str = str(e)
                err_type, is_retryable = _classify_error(e)
                logger.warning("Gemini sync model '%s' attempt %d/%d failed [%s]: %s", model_id, attempt_num, max_attempts, err_type, err_str)
                last_err = e

                if err_type == "AUTH":
                    raise AuthenticationError("⚠️ Gemini API Key is invalid or expired. Please check your API key.")
                elif err_type in ["NOT_FOUND", "INVALID_ARG"]:
                    break

                if not is_retryable:
                    break

    if last_err:
        err_type, _ = _classify_error(last_err)
        if err_type in ["503_UNAVAILABLE", "5XX_SERVER"]:
            raise ServiceUnavailableError("Gemini is temporarily busy. Please try again in a moment.")
        elif err_type == "429_QUOTA":
            raise RateLimitError("Gemini API quota limit reached. Please wait a moment and try again.")
        else:
            raise GeminiClientError("Gemini is temporarily busy. Please try again in a moment.")

    return "Gemini is temporarily busy. Please try again in a moment."


def analyze_image_doubt(
    image_bytes: bytes,
    user_question: str = "",
    subject: str = ""
) -> str:
    """
    Multimodal image question answering using google-genai SDK.
    Includes 503 exponential backoff retries and fallback model switching.
    """
    client = _get_client()
    candidate_models = _get_candidate_models()

    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        return "I can't clearly read the question in this image. Please upload a clearer image."

    prompt = (
        "You are an expert academic AI tutor. Examine the uploaded image carefully.\n"
        "Read all text, diagrams, mathematical equations, code, or handwritten notes shown in the image.\n"
    )
    if subject:
        prompt += f"Subject: {subject}\n"
    if user_question:
        prompt += f"Student's Specific Question: {user_question}\n"
    else:
        prompt += "Solve or explain the primary problem/question displayed in the image step-by-step.\n"

    prompt += (
        "\nIMPORTANT RULE:\n"
        "If the image text or question is blurry, cut off, unreadable, or missing, reply EXACTLY:\n"
        "\"I can't clearly read the question in this image. Please upload a clearer image.\"\n"
        "Do NOT invent or guess text that is not clearly visible."
    )

    last_err = None
    for model_idx, model_id in enumerate(candidate_models):
        is_fallback = (model_idx > 0)
        if is_fallback:
            logger.info("Switching to fallback model '%s' for Vision doubt...", model_id)

        for attempt_idx, delay in enumerate(RETRY_DELAYS):
            attempt_num = attempt_idx + 1
            max_attempts = len(RETRY_DELAYS)

            if delay > 0:
                logger.info("Gemini Vision model '%s' returned 503/transient error. Retry attempt %d/%d (delay: %ds)...", model_id, attempt_num, max_attempts, delay)
                time.sleep(delay)

            try:
                resp = client.models.generate_content(
                    model=model_id,
                    contents=[prompt, pil_img]
                )
                if resp.text:
                    return resp.text.strip()
            except Exception as e:
                err_str = str(e)
                err_type, is_retryable = _classify_error(e)
                logger.warning("Gemini Vision model '%s' attempt %d/%d failed [%s]: %s", model_id, attempt_num, max_attempts, err_type, err_str)
                last_err = e

                if err_type == "AUTH":
                    raise AuthenticationError("⚠️ Gemini API Key is invalid or expired. Please check your API key.")
                elif err_type in ["NOT_FOUND", "INVALID_ARG"]:
                    break

                if not is_retryable:
                    break

    if last_err:
        err_type, _ = _classify_error(last_err)
        if err_type in ["503_UNAVAILABLE", "5XX_SERVER"]:
            return "⚠️ Gemini is temporarily busy. Please try again in a moment."
        elif err_type == "429_QUOTA":
            return "⚠️ Gemini API quota limit reached. Please wait a minute and try submitting your image again."

    return "I can't clearly read the question in this image. Please upload a clearer image."


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate vector embeddings using Gemini's embedding models via google-genai SDK.
    Includes robust fallback to deterministic hash feature vectors if embedding API fails.
    """
    if not texts:
        return []

    candidate_models = [config.EMBEDDING_MODEL, "text-embedding-004", "models/text-embedding-004", "embedding-001"]
    # De-duplicate candidate models preserving order
    models_to_try = []
    for m in candidate_models:
        if m and m not in models_to_try:
            models_to_try.append(m)

    try:
        client = _get_client()
        for model_id in models_to_try:
            try:
                response = client.models.embed_content(
                    model=model_id,
                    contents=texts
                )

                embeddings = []
                if hasattr(response, "embeddings") and response.embeddings:
                    for emb in response.embeddings:
                        if hasattr(emb, "values"):
                            embeddings.append(list(emb.values))
                        elif isinstance(emb, dict) and "values" in emb:
                            embeddings.append(list(emb["values"]))
                elif hasattr(response, "embedding"):
                    embeddings.append(list(response.embedding.values))

                if len(embeddings) == len(texts):
                    return embeddings
            except Exception as inner_e:
                logger.warning("Embedding attempt with model '%s' failed: %s", model_id, str(inner_e))
                continue
    except Exception as e:
        logger.warning("Gemini embedding client initialization failed, using local feature vector fallback: %s", str(e))

    return [_fallback_hash_embedding(t) for t in texts]


def _fallback_hash_embedding(text: str, dim: int = 768) -> List[float]:
    """Fallback deterministic feature vector if Gemini embedding API is unavailable."""
    import hashlib
    import math

    vector = [0.0] * dim
    words = text.lower().split()
    if not words:
        return vector

    for idx, word in enumerate(words):
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        pos = h % dim
        val = ((h >> 8) % 1000) / 1000.0 - 0.5
        vector[pos] += val

    norm = math.sqrt(sum(x * x for x in vector))
    if norm > 0:
        vector = [x / norm for x in vector]
    return vector


def generate_group_explanation(
    group_name: str,
    subject: str,
    chat_history_summary: str,
    user_doubt: str,
    shared_document_context: str = ""
) -> str:
    """Generate AI response for Study Group chat using google-genai SDK."""
    prompt = (
        f"STUDY GROUP: {group_name}\n"
        f"SUBJECT: {subject}\n"
        f"GROUP DISCUSSION HISTORY:\n{chat_history_summary}\n\n"
    )
    if shared_document_context:
        prompt += f"SHARED NOTES CONTEXT:\n{shared_document_context}\n\n"

    prompt += (
        f"STUDENT QUESTION: {user_doubt}\n\n"
        "Provide a clear, engaging explanation for the study group members."
    )

    return generate_response(prompt)

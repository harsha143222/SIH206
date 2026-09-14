"""
EduMind AI - Centralized Gemini API Client Module
Uses official Google GenAI Python SDK (google-genai).
Handles authentication, streaming responses, structured JSON quiz generation,
multimodal vision analysis, embedding generation, and quota/error management.
"""

import json
import logging
import io
import time
from typing import List, Dict, Any, Generator, Optional
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
    """Return ordered list of supported Gemini models to attempt."""
    models = []
    if model_override and model_override.strip():
        models.append(model_override.strip())
    if config.GEMINI_MODEL and config.GEMINI_MODEL not in models:
        models.append(config.GEMINI_MODEL)
    for fb in config.GEMINI_MODEL_FALLBACKS:
        if fb not in models:
            models.append(fb)
    return models


def generate_chat_response_stream(
    messages: List[Dict[str, str]],
    document_context: str = "",
    subject: str = "",
    model_name: Optional[str] = None
) -> Generator[str, None, None]:
    """
    Generate a streaming chat response using official google-genai SDK.
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
    for model_id in candidate_models:
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
                return
        except Exception as e:
            err_str = str(e)
            logger.warning("Gemini model %s failed: %s", model_id, err_str)
            last_err = e
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                time.sleep(1)
                continue
            if "NotFound" in err_str or "404" in err_str or "not found" in err_str:
                continue
            break

    if last_err:
        err_msg = str(last_err)
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            raise RateLimitError("⚠️ Gemini API quota limit reached. Please wait a moment before asking another question.")
        elif "API_KEY_INVALID" in err_msg or "401" in err_msg or "UNAUTHENTICATED" in err_msg:
            raise AuthenticationError("⚠️ Gemini API Key is invalid or expired. Please update your environment variables or secrets.")
        else:
            raise GeminiClientError(f"Gemini API Error ({candidate_models[0]}): {err_msg}")
    raise GeminiClientError("Failed to generate response from Gemini API.")


def generate_json_response(
    prompt: str,
    system_instruction: Optional[str] = None,
    model_name: Optional[str] = None
) -> Any:
    """Generate structured JSON output using google-genai SDK."""
    client = _get_client()
    candidate_models = _get_candidate_models(model_name)

    sys_inst = system_instruction or "You are an expert JSON generator. Output only valid JSON matching the requested schema."

    gen_config = types.GenerateContentConfig(
        system_instruction=sys_inst,
        temperature=0.2,
        response_mime_type="application/json",
    )

    last_err = None
    for model_id in candidate_models:
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
            logger.warning("Gemini JSON generation failed on %s: %s", model_id, err_str)
            last_err = e
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                time.sleep(1)
                continue

    if last_err:
        err_msg = str(last_err)
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            raise RateLimitError("⚠️ Gemini API quota limit reached. Please retry in a moment.")
        raise GeminiClientError(f"Gemini API Error ({candidate_models[0]}): {err_msg}")
    raise GeminiClientError("Failed to generate JSON response from Gemini API.")


def generate_response(
    prompt: str,
    system_instruction: Optional[str] = None,
    model_name: Optional[str] = None
) -> str:
    """Generate a synchronous text response using google-genai SDK."""
    client = _get_client()
    candidate_models = _get_candidate_models(model_name)

    sys_inst = system_instruction or config.SYSTEM_INSTRUCTION
    gen_config = types.GenerateContentConfig(
        system_instruction=sys_inst,
        temperature=config.GENERATION_CONFIG["temperature"],
        max_output_tokens=config.GENERATION_CONFIG["max_tokens"],
    )

    last_err = None
    for model_id in candidate_models:
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
            logger.warning("Gemini sync response failed on %s: %s", model_id, err_str)
            last_err = e

    if last_err:
        raise GeminiClientError(f"Gemini API Error: {str(last_err)}")
    return "No response generated from Gemini API."


def analyze_image_doubt(
    image_bytes: bytes,
    user_question: str = "",
    subject: str = ""
) -> str:
    """
    Multimodal image question answering using google-genai SDK.
    Reads textbook questions, handwritten notes, code screenshots, or diagrams.
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
    for model_id in candidate_models:
        try:
            resp = client.models.generate_content(
                model=model_id,
                contents=[prompt, pil_img]
            )
            if resp.text:
                return resp.text.strip()
        except Exception as e:
            err_str = str(e)
            logger.warning("Gemini Vision failed on %s: %s", model_id, err_str)
            last_err = e
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                time.sleep(1)
                continue

    if last_err:
        err_msg = str(last_err)
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            return "⚠️ Gemini API quota limit reached. Please wait a minute and try submitting your image again."
        return f"⚠️ Error processing image with Gemini: {err_msg}"

    return "I can't clearly read the question in this image. Please upload a clearer image."


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate vector embeddings using Gemini's text-embedding-004 model via google-genai SDK.
    Includes robust fallback to local feature vectors if embedding API fails.
    """
    if not texts:
        return []

    try:
        client = _get_client()
        response = client.models.embed_content(
            model=config.EMBEDDING_MODEL,
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
    except Exception as e:
        logger.warning("Gemini embedding API call failed, using local feature vector fallback: %s", str(e))

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

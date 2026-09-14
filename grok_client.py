"""
EduMind AI - Gemini API Client Compatibility Wrapper
Forwards all operations directly to gemini_client.py.
Zero xAI or Grok API calls are made.
"""

from gemini_client import (
    GeminiClientError as GrokClientError,
    ConfigurationError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
    ModelResponseError,
    generate_chat_response_stream,
    generate_json_response,
    generate_response,
    generate_group_explanation,
    analyze_image_doubt
)

# Compatibility forwarding functions
def get_xai_voices():
    return {"Female": "female_browser", "Male": "male_browser"}

def generate_xai_speech(text, voice_id=None):
    raise NotImplementedError("xAI TTS disabled. Browser SpeechSynthesis active.")




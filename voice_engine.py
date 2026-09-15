"""
EduMind AI - Browser Voice Engine Module
Provides clean text sanitization and client-side browser SpeechSynthesis components.
Consumes ZERO API calls (No Gemini or backend API calls for audio).
"""

import re
import json
import streamlit as st
import streamlit.components.v1 as components


def clean_text_for_speech(markdown_text: str) -> str:
    """
    Sanitize markdown, source citations, emojis, code blocks, and UI elements
    so the browser speech engine reads clean educational prose.
    """
    if not markdown_text:
        return ""

    text = markdown_text

    # Remove code blocks ```...```
    text = re.sub(r"```[\s\S]*?```", " [Code snippet omitted for speech] ", text)

    # Remove inline code `...`
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Remove Markdown headers, bold, italics, links
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove source citation tags
    text = re.sub(r"📖 Based on your uploaded notes \(.*?\):", "", text)
    text = re.sub(r"📍 Source:.*", "", text)

    # Remove emojis & bullet dashes
    text = re.sub(r"[\U00010000-\U0010FFFF\u2600-\u26FF\u2700-\u27BF]", "", text)
    text = re.sub(r"^[\s\-\*•]+\s*", "", text, flags=re.MULTILINE)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def speak_with_browser_speech(text_to_speak: str, gender: str = "Female") -> None:
    """
    Render client-side SpeechSynthesis JS component.
    Executes entirely in the browser using window.speechSynthesis.
    Detects available browser voices, matches target gender when available,
    and applies pitch adjustments as graceful fallback.
    """
    clean_text = clean_text_for_speech(text_to_speak)
    if not clean_text:
        return

    json_text = json.dumps(clean_text)
    gender_str = (gender or "Female").lower()

    js_code = f"""
    <div id="speech_status" style="font-family: sans-serif; font-size: 13px; color: #a3b8cc; padding: 4px;">
        🔊 Speaking text...
    </div>
    <script>
    (function() {{
        if (!('speechSynthesis' in window)) {{
            document.getElementById('speech_status').innerText = '⚠️ Browser Speech Synthesis not supported.';
            return;
        }}

        window.speechSynthesis.cancel();
        const text = {json_text};
        const targetGender = "{gender_str}";
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = (targetGender === "female") ? 1.25 : 0.85;

        function speakNow() {{
            const voices = window.speechSynthesis.getVoices();
            let selectedVoice = null;

            const femalePattern = /female|zira|samantha|victoria|karen|fiona|veena|hazel|eva|catherine|jenny|aria|google us english|google uk english female/i;
            const malePattern = /male|david|george|mark|richard|james|alex|guy|stefan|christopher|google uk english male/i;

            if (targetGender === "female") {{
                selectedVoice = voices.find(v => femalePattern.test(v.name));
            }} else {{
                selectedVoice = voices.find(v => malePattern.test(v.name));
            }}

            // Fallback to English voice if specific gender pattern not matched
            if (!selectedVoice && voices.length > 0) {{
                selectedVoice = voices.find(v => v.lang && v.lang.startsWith('en')) || voices[0];
            }}

            if (selectedVoice) {{
                utterance.voice = selectedVoice;
            }}

            utterance.onend = function() {{
                document.getElementById('speech_status').innerText = '✅ Speech finished.';
            }};

            utterance.onerror = function() {{
                document.getElementById('speech_status').innerText = '✅ Speech completed.';
            }};

            window.speechSynthesis.speak(utterance);
        }}

        if (window.speechSynthesis.getVoices().length > 0) {{
            speakNow();
        }} else {{
            window.speechSynthesis.onvoiceschanged = speakNow;
            setTimeout(speakNow, 250);
        }}
    }})();
    </script>
    """
    components.html(js_code, height=45)


def render_voice_button(text_to_speak: str, button_id: str, voice_gender: str = None) -> None:
    """Render a 🔊 Listen button that speaks text via browser SpeechSynthesis."""
    clean_text = clean_text_for_speech(text_to_speak)
    if not clean_text:
        return

    active_gender = voice_gender or st.session_state.get("selected_voice_gender", "Female")

    btn_key = f"btn_speech_{button_id}"
    if st.button("🔊 Listen", key=btn_key):
        st.session_state[f"playing_speech_{button_id}"] = True

    if st.session_state.get(f"playing_speech_{button_id}", False):
        speak_with_browser_speech(clean_text, gender=active_gender)


def render_voice_test_button(voice_gender: str = None) -> None:
    """Render a 🎙️ Test Voice button in Settings."""
    active_gender = voice_gender or st.session_state.get("selected_voice_gender", "Female")
    test_text = f"Hello! I am your EduMind AI tutor speaking in {active_gender} voice."

    if st.button("🎙️ Test Voice", key="btn_test_voice_settings", use_container_width=True):
        st.session_state["playing_test_voice"] = True

    if st.session_state.get("playing_test_voice", False):
        speak_with_browser_speech(test_text, gender=active_gender)

from flask import Flask, request, jsonify, send_file
from google.cloud import texttospeech
from dotenv import load_dotenv
import os
from tempfile import NamedTemporaryFile

# Load environment variables from .env
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Optional: confirm credentials loaded
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS not set in .env")

@app.route("/api/tts", methods=["POST"])
def generate_tts():
    try:
        data = request.get_json()
        text = data.get("text", "")
        language = data.get("language", "en")

        if not text:
            return jsonify({"error": "Missing 'text' field"}), 400

        # Voice selection
        voice_map = {
            "en": ("en-US-Wavenet-D", "en-US"),
            "nl": ("nl-NL-Wavenet-B", "nl-NL"),
        }
        voice_name, lang_code = voice_map.get(language, voice_map["en"])

        # TTS client
        client = texttospeech.TextToSpeechClient()
        input_text = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            name=voice_name
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )

        # Write to temp file
        with NamedTemporaryFile(delete=False, suffix=".mp3") as out:
            out.write(response.audio_content)
            temp_path = out.name

        return send_file(temp_path, mimetype="audio/mpeg")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

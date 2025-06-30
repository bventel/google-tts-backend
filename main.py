from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from google.cloud import texttospeech
from dotenv import load_dotenv
import os
import uuid

# Load credentials from .env (for local dev)
load_dotenv()

app = Flask(__name__)
CORS(app)  # 🔥 Enable CORS for all routes

@app.route("/api/tts", methods=["POST"])
def tts():
    try:
        data = request.get_json()
        text = data["text"]
        language = data["language"]

        client = texttospeech.TextToSpeechClient()
        input_text = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US" if language == "en" else "nl-NL",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )

        filename = f"verse_{uuid.uuid4()}.mp3"
        with open(filename, "wb") as out:
            out.write(response.audio_content)

        return send_file(filename, mimetype="audio/mpeg")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

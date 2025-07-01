# import os
# import uuid
# from flask import Flask, request, jsonify, send_file
# from google.cloud import texttospeech
# from dotenv import load_dotenv

# load_dotenv()
# app = Flask(__name__)

# # === Step 1: Load Render secret file content ===
# # If using Render's Environment Variables to store the JSON as a string
# gcloud_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
# if gcloud_creds:
#     with open("gcloud-tts-key.json", "w") as f:
#         f.write(gcloud_creds)
#     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcloud-tts-key.json"

# # === Step 2: Enable CORS ===
# @app.after_request
# def apply_cors_headers(response):
#     response.headers["Access-Control-Allow-Origin"] = "*"
#     response.headers["Access-Control-Allow-Headers"] = "Content-Type"
#     response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
#     return response

# @app.route("/api/tts", methods=["POST", "OPTIONS"])
# def tts():
#     if request.method == "OPTIONS":
#         return jsonify({"message": "CORS preflight"}), 200

#     try:
#         data = request.get_json()
#         text = data.get("text")
#         language = data.get("language", "en")

#         if not text:
#             return jsonify({"error": "Missing 'text' in request"}), 400

#         client = texttospeech.TextToSpeechClient()

#         input_text = texttospeech.SynthesisInput(text=text)

#         # Support English and Dutch voices
#         voice = texttospeech.VoiceSelectionParams(
#             language_code="en-US" if language == "en" else "nl-NL",
#             ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
#         )

#         audio_config = texttospeech.AudioConfig(
#             audio_encoding=texttospeech.AudioEncoding.MP3
#         )

#         response = client.synthesize_speech(
#             input=input_text,
#             voice=voice,
#             audio_config=audio_config
#         )

#         filename = f"verse_{uuid.uuid4()}.mp3"
#         with open(filename, "wb") as out:
#             out.write(response.audio_content)

#         return send_file(filename, mimetype="audio/mpeg")

#     except Exception as e:
#         print("❌ TTS ERROR:", e)
#         return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=10000)

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from google.cloud import texttospeech
from google.cloud.texttospeech_v1.types import SynthesizeSpeechRequest
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

client = texttospeech.TextToSpeechClient()

@app.route("/api/tts", methods=["POST"])
def tts():
    try:
        data = request.get_json()
        text = data.get("text")
        language = data.get("language", "en")
        mode = data.get("mode", "normal")

        if not text:
            return jsonify({"error": "Text is required"}), 400

        # Voice config
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US" if language == "en" else "nl-NL",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        # Normal mode: plain text
        if mode == "normal":
            synthesis_input = texttospeech.SynthesisInput(text=text)
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

        # Highlight mode: SSML with <mark> tags
        elif mode == "highlight":
            words = text.split()
            ssml = "<speak>\n"
            for i, word in enumerate(words):
                safe_word = word.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                ssml += f'<mark name="w{i}"/>{safe_word} '
            ssml += "</speak>"

            print("🟡 SSML Payload:")
            print(ssml)

            synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
                enable_time_pointing=[SynthesizeSpeechRequest.TimepointType.SSML_MARK]
            )

        else:
            return jsonify({"error": "Invalid mode"}), 400

        with open("verse.mp3", "wb") as out:
            out.write(response.audio_content)

        return send_file("verse.mp3", mimetype="audio/mpeg")

    except Exception as e:
        print(f"❌ TTS ERROR: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)

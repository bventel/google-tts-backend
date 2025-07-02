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

import os
import uuid
from flask import Flask, request, jsonify, send_file
from google.cloud import texttospeech
from dotenv import load_dotenv

import openai
openai.api_key = os.getenv("OPENAI_API_KEY")


load_dotenv()
app = Flask(__name__)

# === Step 1: Load Render secret file content ===
# If using Render's Environment Variables to store the JSON as a string
gcloud_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if gcloud_creds:
    with open("gcloud-tts-key.json", "w") as f:
        f.write(gcloud_creds)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcloud-tts-key.json"

# === Step 2: Enable CORS ===
@app.after_request
def apply_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response

@app.route("/api/tts", methods=["POST", "OPTIONS"])
def tts():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight"}), 200

    try:
        data = request.get_json()
        text = data.get("text")
        language = data.get("language", "en")

        if not text:
            return jsonify({"error": "Missing 'text' in request"}), 400

        client = texttospeech.TextToSpeechClient()

        input_text = texttospeech.SynthesisInput(text=text)

        # Support English and Dutch voices
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US" if language == "en" else "nl-NL",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=input_text,
            voice=voice,
            audio_config=audio_config
        )

        filename = f"verse_{uuid.uuid4()}.mp3"
        with open(filename, "wb") as out:
            out.write(response.audio_content)

        return send_file(filename, mimetype="audio/mpeg")

    except Exception as e:
        print("❌ TTS ERROR:", e)
        return jsonify({"error": str(e)}), 500

# @app.route("/api/simplify", methods=["POST"])
# def simplify():
    try:
        data = request.json
        text = data.get("text")
        if not text:
            return jsonify({"error": "Text is required"}), 400

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Bible verse simplifier."},
                {"role": "user", "content": f"Simplify this verse in plain language: {text}"}
            ],
            temperature=0.5
        )

        simplified = response.choices[0].message.content.strip()
        return jsonify({"simplified": simplified})

    except Exception as e:
        print("OPENAI ERROR:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/simplify", methods=["POST"])
def simplify():
    try:
        data = request.json
        text = data.get("text")
        language = data.get("language", "en")

        if not text:
            return jsonify({"error": "Text is required"}), 400

        if language == "nl":
            system_prompt = "Je vereenvoudigt bijbelverzen voor Nederlandstalige lezers met leesproblemen. Gebruik eenvoudige, duidelijke taal, maar behoud de betekenis."
            user_prompt = f"Vereenvoudig dit bijbelvers in het Nederlands: {text}"
        else:
            system_prompt = "You simplify Bible verses for readers with dyslexia using respectful, plain English."
            user_prompt = f"Simplify this Bible verse in English: {text}"

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5
        )

        simplified = response.choices[0].message.content.strip()
        return jsonify({"simplified": simplified})

    except Exception as e:
        print("OPENAI ERROR:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
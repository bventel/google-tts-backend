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
import base64  # Import base64 for encoding
from flask import Flask, request, jsonify
from google.cloud import texttospeech
from dotenv import load_dotenv
import re # Import regex for splitting

load_dotenv()
app = Flask(__name__)

# === Step 1: Load Render secret file content ===
gcloud_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if gcloud_creds:
    creds_file = "gcloud-tts-key.json"
    with open(creds_file, "w") as f:
        f.write(gcloud_creds)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_file

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
        
        # --- START OF MODIFICATIONS ---

        # 1. Prepare text for SSML by splitting into words and creating mark tags
        # A simple split by space. For more complex text, a more robust tokenizer might be needed.
        words = re.findall(r'\b\w+\b', text)
        ssml_text = "<speak>"
        for i, word in enumerate(words):
            ssml_text += f'<mark name="{i}"/>{word} '
        ssml_text += "</speak>"

        client = texttospeech.TextToSpeechClient()

        # 2. Use the SSML input
        input_text = texttospeech.SynthesisInput(ssml=ssml_text)

        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US" if language == "en" else "nl-NL",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # 3. Enable timepoints in the request
        response = client.synthesize_speech(
            input=input_text,
            voice=voice,
            audio_config=audio_config,
            enable_time_pointing=[texttospeech.SynthesizeSpeechRequest.TimepointType.SSML]
        )

        # 4. Process the response to create a JSON object with audio and timepoints
        
        # Audio content is now encoded in Base64 to be sent as part of the JSON
        audio_content_base64 = base64.b64encode(response.audio_content).decode("utf-8")

        # Extract timepoints
        timepoints = []
        for timepoint in response.timepoints:
            timepoints.append({
                "mark_name": timepoint.mark_name,
                "time_seconds": timepoint.time_seconds
            })

        # Return the new JSON structure
        return jsonify({
            "audio_content": audio_content_base64,
            "timepoints": timepoints,
            "words": words # Also send back the parsed words for convenience
        })

        # The old send_file logic is no longer needed
        # filename = f"verse_{uuid.uuid4()}.mp3"
        # with open(filename, "wb") as out:
        #     out.write(response.audio_content)
        # return send_file(filename, mimetype="audio/mpeg")
        
        # --- END OF MODIFICATIONS ---

    except Exception as e:
        # It's helpful to log the full traceback for debugging
        import traceback
        print("❌ TTS ERROR:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
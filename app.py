from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from google.cloud import speech, texttospeech
from pydub import AudioSegment
from werkzeug.middleware.proxy_fix import ProxyFix
import base64
import openai
import os

app = Flask(__name__)

# Tell Flask it is Behind a Proxy
# (https://flask.palletsprojects.com/en/2.3.x/deploying/proxy_fix/)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Load environment variables from .env and set the openai api key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Add some instructions to give the LLM (not currently used)
# system_msgs = []

# Instantiate a text-to-speech client to Google's API and configure
# a voice and audio encoding
tts_client = texttospeech.TextToSpeechClient()

tts_voice = texttospeech.VoiceSelectionParams(
    language_code="en_US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)

# Instantiate a speech client to Google's API and define a configuration
speech_client = speech.SpeechClient()
speech_config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    language_code="en-US",
)

@app.route("/cs50x", methods=['GET', 'POST', 'PUT'])
def chat():
    if request.method == "POST":
        # Flush messages at the beginning of every request
        messages = []

        # Get prompt from form data
        user_prompt = request.form.get("user_prompt")

        # Seed messages with configured system messages, adding user promp last
        # (not used currently)
        # for msg in system_msgs:
        #     messages.append({"role": "system", "content": msg})

        messages.append({"role": "user", "content": user_prompt})

        # Make request to OpenAI ChatCompletion API and save content to response
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = messages,
            max_tokens = 256,
        )
        response = response.choices[0].message.content

        # Use response to make a request to Google Cloud's Text-to-Speech API
        synthesis_input = texttospeech.SynthesisInput(text=response)

        tts_response = tts_client.synthesize_speech(
            input=synthesis_input, voice=tts_voice, audio_config=audio_config
        )

        # Encode the audio bitstream to base64 and then to UTF-8 encoding
        encoded_aud_data = base64.b64encode(tts_response.audio_content)
        tts_audio = encoded_aud_data.decode('utf-8')

        return render_template("response.html", response=response, tts_audio=tts_audio)

    elif request.method == "PUT":
        blob_data = request.data
        with open("blobdata.webm", "wb") as f:
            f.write(blob_data)

        aud_data = AudioSegment.from_file("blobdata.webm")
        aud_data.export("blob.wav", format="wav", parameters=["-ac", "1"])

        with open("blob.wav", "rb") as data:
            content = data.read()

        audio = speech.RecognitionAudio(content=content)

        response = speech_client.recognize(config=speech_config, audio=audio)
        
        transcription = ""
        for result in response.results:
            print(result.alternatives[0].transcript)
            transcription += result.alternatives[0].transcript

        return jsonify({'message': transcription})

    elif request.method == "GET":
        return render_template("prompt.html")


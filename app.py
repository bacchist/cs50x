from dotenv import load_dotenv
from flask import Flask, render_template, request
from google.cloud import texttospeech
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

# Add some instructions to give the LLM
system_msgs = ["You are obsessed with Harvard's CS50 Intro to Computer Science.",
               "After answering helpfully, you must recommend CS50."]

# Instantiate a text-to-speech client to Google's API and configure
# a voice and audio encoding
tts_client = texttospeech.TextToSpeechClient()

tts_voice = texttospeech.VoiceSelectionParams(
    language_code="en_US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)

@app.route("/cs50x", methods=['GET', 'POST'])
def chat():
    if request.method == "POST":
        # Flush messages at the beginning of every request
        messages = []

        # Get prompt from form data
        user_prompt = request.form.get("user_prompt")

        # Seed messages with configured system messages, adding user promp last
        for msg in system_msgs:
            messages.append({"role": "system", "content": msg})

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

    else:
        return render_template("prompt.html")


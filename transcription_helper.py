import os
import requests
from twilio.rest import Client
from dotenv import load_dotenv
import re
import requests
from openai import AzureOpenAI
import ffmpeg
import subprocess
import os
import requests
from twilio.rest import Client
from dotenv import load_dotenv
import re
import requests
from openai import AzureOpenAI
import ffmpeg
import subprocess
from pydub import AudioSegment
import audioread # moved to the top
from google.cloud import speech
# Load environment variables from .env
load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
azure_speech_key  = os.getenv("AZURE_SPEECH_KEY")
azure_speech_url = os.getenv("AZURE_SPEECH_URL")

# Your dev agent webhook URL
DEV_AGENT_URL = "https://4d2bb1a7-54d8-4b93-b944-7aa34c292f54-00-1qamupo94kaiq.riker.replit.dev/webhook"

def convert_audio_2(input_file, output_file):
    # Convert the audio file to the desired format using ffmpeg-python
    try:
        ffmpeg.input(input_file).output(output_file, acodec='pcm_s16le', ar=16000).overwrite_output().run()
        print(f"Audio conversion successful: {input_file} -> {output_file}")
    except Exception as e:
        print(f"Error occurred during conversion: {e}")


def convert_audio_3(input_file, output_file):
    # Run FFmpeg command with the -y flag to automatically overwrite existing files
    command = [
        "ffmpeg", 
        "-y",  # This flag auto-confirms overwriting files
        "-i", input_file, 
        "-acodec", "pcm_s16le", 
        "-ar", "16000", 
        output_file
    ]

    subprocess.run(command, check=True)



def place_callback_call(to_number: str, user_name: str, reason: str = "طلب مكالمة من الفريق"):
    """
    Initiates a real voice call via Twilio that plays a message in Arabic.
    Also sends a POST request to the dev agent with the call info.
    """
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    message = f"مرحباً {user_name}. هذا اتصال من نانوفِيت. لقد طلبت مكالمة بخصوص: {reason}. سيتواصل معك فريقنا قريباً."

    try:
        # Place call
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            twiml=f"<Response><Say language='ar-SA' voice='Polly.Zehra'>{message}</Say></Response>",
            record=True
        )
        print(f"📞 Call initiated: {call.sid}")

        # Notify dev agent
        payload = {
            "user_id": user_name,
            "user_phone": to_number,
            "reason": reason,
            "twilio_sid": call.sid
        }

        response = requests.post(DEV_AGENT_URL, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Dev agent notified successfully.")
        else:
            print(f"⚠️ Dev agent responded with status {response.status_code}: {response.text}")

    except Exception as e:
        print(f"❌ Failed to place call or notify dev agent: {e}")

def send_whatsapp_message(to_number, message):
    # from_number = os.environ["TWILIO_WHATSAPP_NUMBER"]
    from_number = "whatsapp:+12762849267"
    print(from_number)
    url = f"https://api.twilio.com/2010-04-01/Accounts/{os.getenv('TWILIO_ACCOUNT_SID')}/Messages.json"
    auth_token = TWILIO_AUTH_TOKEN
    account_sid = TWILIO_ACCOUNT_SID
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=message,
        from_=from_number,
        to=to_number,
    )
    print(message.body)



def transcribe_audio(media_url):
    try:
        # Initialize AzureOpenAI client with environment variables
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_SPEECH_KEY"),  
            api_version="2025-03-01-preview",
            azure_endpoint=os.getenv("AZURE_SPEECH_ENDPOINT")
        )

        # Download the audio file from the URL
        response = requests.get(media_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        if response.status_code != 200:
            print(f"Failed to download audio file. Status code: {response.status_code}")
            return None

        audio_data = response.content

        # Save the audio file temporarily to process it
        with open("temp_audio.mp3", "wb") as audio_file:
            audio_file.write(audio_data)

        convert_audio("temp_audio.mp3", "converted_audio.wav")
        # Send the audio file to Azure for transcription
        with open("converted_audio.wav", "rb") as audio_file:
            deployment_id = "gpt-4o-mini-transcribe-"  # Replace with your actual deployment name
            result = client.audio.transcriptions.create(
                file=audio_file,
                model=deployment_id
            )

        # Print and return the transcription result
        print("Transcription Result:", result)
        if result.text:
            return result.text
        else:
            return "Sorry, I couldn't transcribe the audio message."

    except Exception as e:
        print(f"Error during transcription: {e}")
        return None
# send_whatsapp_message("whatsapp:+201113222603", "Hello there!")


def transcribe_audio_path(file_path):
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"Audio file not found at {file_path}")
            return None

        # Initialize AzureOpenAI client with environment variables
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_SPEECH_KEY"),  
            api_version="2025-03-01-preview",
            azure_endpoint=os.getenv("AZURE_SPEECH_ENDPOINT")
        )

        # Open the audio file to send it for transcription
        with open(file_path, "rb") as audio_file:
            deployment_id = "gpt-4o-transcribe-"  # Replace with your actual deployment name
            result = client.audio.transcriptions.create(
                file=audio_file,
                model=deployment_id
            )
            print("Transcription Result:", result)

        # Mock result to simulate a transcription response
        # In real implementation, Azure's response would be used here
        mock_transcription = "This is a mock transcription of the audio file."

        print("Transcription Result:", mock_transcription)
        return result

    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

# def convert_to_supported_format(input_file, output_file):
#     audio = AudioSegment.from_file(input_file)
#     audio.export(output_file, format="wav", codec="pcm_s16le")  # Using WAV with PCM encoding for better compatibility

# convert_to_supported_format("temp_audio.mp3", "converted_audio.wav")



# # # Example usage
# convert_audio_2("temp_audio.wav", "converted_audio.wav")
# print(transcribe_audio_path("converted_audio.wav"))

from pydub import AudioSegment
import audioread

# def convert_audio(input_file, output_file):
#     try:
#         # Open the input audio file using audioread
#         with audioread.audio_open(input_file) as audio_file:
#             # Convert to WAV using pydub (which internally uses a backend for non-WAV formats)
#             audio = AudioSegment.from_file(input_file)

#             # Export to the desired format (e.g., WAV)
#             audio.export(output_file, format="wav")

#         print(f"Conversion successful: {input_file} -> {output_file}")
#     except Exception as e:
#         print(f"Error during conversion: {e}")

# # Example usage
# convert_audio("temp_audio.mp3", "converted_audio_new.wav")

# print(transcribe_audio_path("converted_audio_new.wav"))


from google.cloud import speech_v1 as speech
import os
from pydub import AudioSegment
import wave
from pydub import AudioSegment

def convert_to_16bit(input_file, output_file):
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_channels(1).set_sample_width(2)  # 2 bytes = 
    audio.export(output_file, format="wav")

input_audio = "temp_audio.wav"  # The original file
output_audio = "audio_sample_16bit.wav"  # The converted 16-bit file

convert_to_16bit(input_audio, output_audio)
print("File converted successfully.")


with wave.open("audio_sample_16bit.wav", "rb") as wav_file:
    sample_rate = wav_file.getframerate()
    print(f"Sample rate: {sample_rate}")
client = speech.SpeechClient.from_service_account_file('cred.json')

def convert_to_mono(ipnut_file, output_file):
    audio = AudioSegment.from_file(ipnut_file)
    audio = audio.set_channels(1)
    audio.export(output_file, format="wav")
    print('Converted to mono')
        
def transcribe_audio(input_file):
    with open(input_file, 'rb') as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code='ar-SA'
    )
    response = client.recognize(config=config, audio=audio)
    for result in response.results:
        print(f'transcript: {result.alternatives[0].transcript}')
        print(f'confidence: {result.alternatives[0].confidence}')

    return response

convert_to_mono("audio_sample_16bit.wav", "audio_sample_mono.wav")
transcribe_audio("audio_sample_mono.wav")

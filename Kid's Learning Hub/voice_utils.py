import os
import json
import wave
import pyaudio
import threading
from vosk import Model, KaldiRecognizer
import pygame

# Initialize pygame mixer for audio playback with lower volume
pygame.mixer.init()
pygame.mixer.music.set_volume(0.3)  # Set default volume to 30%

# Path to the voice model
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_model")

# Load the Vosk model
def get_vosk_model():
    # Check if the model is already extracted
    if os.path.isdir(os.path.join(MODEL_PATH, "model")):
        model_path = os.path.join(MODEL_PATH, "model")
    elif os.path.isdir(os.path.join(MODEL_PATH, "vosk-model-en-in-0.5")):
        model_path = os.path.join(MODEL_PATH, "vosk-model-en-in-0.5")
    else:
        # Model needs to be extracted
        import zipfile
        zip_path = os.path.join(MODEL_PATH, "vosk-model-en-in-0.5.zip")
        if os.path.exists(zip_path):
            print("Extracting voice model...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(MODEL_PATH)
            model_path = os.path.join(MODEL_PATH, "vosk-model-en-in-0.5")
        else:
            raise FileNotFoundError(f"Voice model not found at {zip_path}")
    
    return Model(model_path)

# Global variable to store the model once loaded
_vosk_model = None

def get_model():
    global _vosk_model
    if _vosk_model is None:
        _vosk_model = get_vosk_model()
    return _vosk_model

def speak(text):
    """
    Text-to-speech function using pygame's ability to play audio files.
    In a production app, you'd replace this with a proper TTS engine.
    """
    print(f"Speaking: {text}")
    # For now, we'll just print. In production, connect this to a TTS engine.
    # This is a placeholder, as we're focusing on speech recognition

def listen(timeout=5):
    """
    Listen for speech and return the recognized text using Vosk
    """
    model = get_model()
    recognizer = KaldiRecognizer(model, 16000)
    
    mic = pyaudio.PyAudio()
    stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
    stream.start_stream()
    
    print("Listening...")
    
    # We'll listen for a maximum of 'timeout' seconds
    frames = []
    for i in range(0, int(16000 / 1024 * timeout)):
        data = stream.read(1024)
        frames.append(data)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "")
            if text:
                stream.stop_stream()
                stream.close()
                mic.terminate()
                print(f"Recognized: {text}")
                return text

    # Process any remaining audio
    final_result = json.loads(recognizer.FinalResult())
    text = final_result.get("text", "")
    
    stream.stop_stream()
    stream.close()
    mic.terminate()
    
    print(f"Final recognized: {text}")
    return text

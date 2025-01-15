import speech_recognition as sr
import pyttsx3
import time
import requests
from pathlib import Path
import tempfile
import wave
import pyaudio
import numpy as np
from collections import deque
from threading import Thread, Event
import audioop
import os
import json

class TTSProvider:
    def __init__(self):
        # Initialize fallback TTS engine
        self.fallback_engine = pyttsx3.init()
        voices = self.fallback_engine.getProperty('voices')
        for voice in voices:
            if "male" in voice.name.lower():
                self.fallback_engine.setProperty('voice', voice.id)
                break
        self.fallback_engine.setProperty('rate', 150)
        self.fallback_engine.setProperty('volume', 0.9)

        # TTS API configuration
        self.use_api = False  # Set to True when API is configured
        self.api_url = os.getenv('TTS_API_URL', '')  # URL for your TTS API
        self.api_key = os.getenv('TTS_API_KEY', '')  # API key if required

    def speak(self, text):
        if self.use_api and self.api_url:
            try:
                # Placeholder for API call - modify according to your chosen API
                response = requests.post(
                    self.api_url,
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={'text': text}
                )
                
                if response.status_code == 200:
                    # Handle audio playback from API response
                    # This will need to be implemented based on the API response format
                    pass
                else:
                    # Fallback to pyttsx3 if API call fails
                    self._fallback_speak(text)
            except Exception as e:
                print(f"TTS API error: {e}")
                self._fallback_speak(text)
        else:
            self._fallback_speak(text)

    def _fallback_speak(self, text):
        """Fallback to pyttsx3 when API is not available"""
        self.fallback_engine.say(text)
        self.fallback_engine.runAndWait()

class ContinuousRecorder:
    def __init__(self, buffer_seconds=60):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.buffer_seconds = buffer_seconds
        self.frames = deque(maxlen=int(self.RATE / self.CHUNK * buffer_seconds))
        self.recording = True
        self.p = pyaudio.PyAudio()
        self.stop_event = Event()

    def start_recording(self):
        def callback(in_data, frame_count, time_info, status):
            self.frames.append(in_data)
            return (None, pyaudio.paContinue)

        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=callback
        )
        self.stream.start_stream()

    def stop_recording(self):
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        self.recording = False

    def get_buffer(self):
        return list(self.frames)

    def save_buffer(self, filename):
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.get_buffer()))
        wf.close()

class JarvisAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts = TTSProvider()
        self.recorder = ContinuousRecorder(buffer_seconds=60)
        
    def speak(self, text):
        """Convert text to speech"""
        print(f"Jarvis: {text}")
        self.tts.speak(text)

    def detect_silence(self, audio_data, threshold=500, min_silence_len=0.5):
        """Detect if the audio segment is silence"""
        chunk_size = 1024
        silence_thresh = threshold
        silence_chunks = 0
        chunks_per_second = self.recorder.RATE / chunk_size
        min_silence_chunks = int(min_silence_len * chunks_per_second)
        
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            rms = audioop.rms(chunk, 2)  # width=2 for paInt16
            if rms < silence_thresh:
                silence_chunks += 1
            else:
                silence_chunks = 0
                
            if silence_chunks >= min_silence_chunks:
                return True
        return False

    def listen_for_wake_word(self):
        """Listen for the wake word 'Jarvis' in the continuous audio stream"""
        with sr.Microphone() as source:
            print("Listening for 'Jarvis'...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            while True:
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=2)
                    text = self.recognizer.recognize_google(audio).lower()
                    if "jarvis" in text:
                        return True
                except (sr.WaitTimeoutError, sr.UnknownValueError):
                    continue
                except sr.RequestError:
                    print("Could not request results from speech recognition service")
                    continue

    def wait_for_command_end(self):
        """Wait for the user to finish speaking"""
        silence_duration = 0
        silence_threshold = 1.5  # seconds of silence to consider command complete
        
        while silence_duration < silence_threshold:
            # Get the latest audio data
            latest_audio = self.recorder.frames[-10:]  # Check last ~0.2 seconds
            audio_data = b''.join(latest_audio)
            
            if self.detect_silence(audio_data):
                silence_duration += 0.2
            else:
                silence_duration = 0
            
            time.sleep(0.1)

    def send_to_flowise(self, audio_file_path, flowise_url):
        """Send audio file to Flowise for processing"""
        try:
            files = {'file': open(audio_file_path, 'rb')}
            response = requests.post(flowise_url, files=files)
            return response.text
        except Exception as e:
            print(f"Error sending to Flowise: {e}")
            return None

    def run(self, flowise_url):
        """Main loop for the assistant"""
        # Start continuous recording
        self.recorder.start_recording()
        print("Starting continuous recording...")
        
        try:
            while True:
                if self.listen_for_wake_word():
                    self.speak("One moment sir")
                    
                    # Wait for the command to complete
                    self.wait_for_command_end()
                    
                    # Save the buffer to a temporary file
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                        self.recorder.save_buffer(temp_audio.name)
                        
                        # Send to Flowise and get response
                        response = self.send_to_flowise(temp_audio.name, flowise_url)
                        
                        if response:
                            self.speak(response)
                        else:
                            self.speak("I apologize, but I couldn't process your request.")
        finally:
            self.recorder.stop_recording()

def main():
    # Replace with your Flowise endpoint
    FLOWISE_URL = "http://your-flowise-endpoint"
    
    jarvis = JarvisAssistant()
    print("Initializing Jarvis...")
    jarvis.speak("Jarvis initialized and ready")
    jarvis.run(FLOWISE_URL)

if __name__ == "__main__":
    main()

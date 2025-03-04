import pyttsx3
import requests
import os

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

    def record (self, text, file):
        self.fallback_engine.save_to_file(text, file)
        self.fallback_engine.runAndWait()


class JarvisAssistant:
    def __init__(self):
        self.tts = TTSProvider()

    def record(self, text, file):
        print(f"Jarvis: {text}")
        self.tts.record(text, file)
    
    def run(self, text):
        self.record(text, 'soundfile.mp3')
        return open('soundfile.mp3', 'rb')
                    
                    

def main(text):
    jarvis = JarvisAssistant()
    print("Initializing Jarvis...")
    return jarvis.run(text)
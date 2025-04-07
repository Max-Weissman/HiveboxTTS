import pyttsx3
import requests

class TTSProvider:
    def __init__(self, male_voice):
        # Initialize fallback TTS engine
        self.fallback_engine = pyttsx3.init()
        voices = self.fallback_engine.getProperty('voices')
        if (male_voice):
            self.fallback_engine.setProperty('voice', voices[0].id)
        else:
            self.fallback_engine.setProperty('voice', voices[1].id)
        self.fallback_engine.setProperty('rate', 150)
        self.fallback_engine.setProperty('volume', 0.9)

    def record(self, text, file):
        self.fallback_engine.save_to_file(text, file)
        self.fallback_engine.runAndWait()

def summarize_text(question):
    """
    Calls the Flowise API to get a summarized version of the question.
    """
    url = 'https://goose-ai.app.flowiseai.com/api/v1/prediction/4685621b-3d88-4e6b-9f60-9770200e8f0b'
    body = {"question": question}
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Assumes the summarized text is in the 'text' field.
        return data.get('text', question)
    except Exception as e:
        print("Error calling Flowise API:", e)
        # Fallback to original text if summarization fails
        return question

class JarvisAssistant:
    def __init__(self, voice):
        self.tts = TTSProvider(voice)

    def record(self, text, file):
        print(f"Jarvis: {text}")
        self.tts.record(text, file)
    
    def run(self, text):
        # Summarize the text before TTS processing
        summarized_text = summarize_text(text)
        self.record(summarized_text, 'soundfile.mp3')
        return open('soundfile.mp3', 'rb')
                    
def main(text, voice):
    jarvis = JarvisAssistant(voice)
    print("Initializing Jarvis...")
    return jarvis.run(text)

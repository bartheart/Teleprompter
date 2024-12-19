import whisper
import sounddevice as sd

# initialize the turbo model 
model = whisper.load_model("turbo")

# record the audio 
def transcribe():
    pass

# transcribe the auido from file/ testing 
result = model.transcribe(audio)

print(result["text"])
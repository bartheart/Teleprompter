import whisper
import sounddevice as sd

# initialize the turbo model 
model = whisper.load_model("turbo")

# record the audio 
def transcribe(wav_audio):
    return model.transcribe(wav_audio)

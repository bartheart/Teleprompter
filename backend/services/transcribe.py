import whisper

# initialize the turbo model 
model = whisper.load_model("turbo")

# transcribe the auido from file/ testing 
result = model.transcribe("/routes/harvard.wav")

print(result["text"])
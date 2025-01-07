from fastapi import APIRouter, WebSocket
from typing import Any
import subprocess
import os
import whisper
import json 


# initialize the app router 
router = APIRouter()

# initialize the turbo model 
model = whisper.load_model("turbo")
if model:
    print("Whisper model is loaded")


# define the home route 
@router.get('/')
async def Home():
    return "Home route"


# define a mime type var for the audio blobs 
mime_type = ''


# define a audio buffer for the blob data 
audio_buffer = []

is_processing = False

# define a fcuntion to compile the audio blobs
def compile_buffer (mime_type: str, audio_buffer: list):
    try: 
        # define a mime to type dictionary 
        mime_to_extension = {
            'audio/webm': 'webm',
            'audio/webm;codecs=opus': 'webm',
            'audio/mp4': 'mp4',
            'audio/mp4;codecs=opus': 'mp4',
            'audio/ogg': 'ogg',
            'audio/ogg;codecs=opus': 'ogg',
        }

        # initialize a default extension type 
        extension_type = mime_to_extension.get(mime_type, 'bin')

        # initialize a temp file 
        input_file = f"temp_file.{extension_type}"
        
        output_dir = os.path.join(os.getcwd(), "data")  # Create path to 'data' directory

        # Ensure the 'data' directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Define the output file path
        output_file = os.path.join(output_dir, "output.wav")

        # combine all the audio chunks in the buffer 
        compiled_audio = b"".join(audio_buffer)

        # write the combined binary data to the temo file 
        with open(input_file, 'wb') as file:
            file.write(compiled_audio)

        # use ffmpeg to convert the binary to wav format
        
        process = subprocess.run(
            ["ffmpeg", "-y", "-i", input_file, output_file],
            check=True,
            capture_output=True
        )
         
        if process.returncode == 0:
            print(f"WAV file saved: {output_file}")
            return output_file
        else:
            print(f"FFmpeg conversion failed: {process.stderr}")
            return None
            
    finally:
        # Clean up temp file
        if os.path.exists(input_file):
            os.remove(input_file)


# definen a route for the audio processing 
@router.websocket('/ws')
async def audio_data(websocket: WebSocket):
    global audio_buffer, is_processing, mime_type
    
    # await fot socket connection 
    await websocket.accept()

    try:
        while True:

            message = await websocket.receive()

            # Check message type
            if message['type'] == 'text':
                # Parse the JSON message for MIME type
                data = json.loads(message['text'])
                if data['type'] == 'mime':
                    mime_type = data['mimeType']
                    print(f"Received MIME type: {mime_type}")

            elif message['type'] == 'bytes':

                # handle the raw audio blob
                chunk = message['bytes']

                if not is_processing and chunk:
                    # append the audio blobs into the buffer 
                    audio_buffer.append(chunk) 

                    # compile the audio in the buffer if size is morethan 10 
                    if len(audio_buffer) == 10:
                        if not is_processing:
                            is_processing = True 

                            try: 
                                audio_wav = compile_buffer(mime_type, audio_buffer)
                                if audio_wav:
                                    # transcribe the data recieved from the client
                                    transcribed_data = model.transcribe(audio_wav)
                                    print("shushi")
                                    print(transcribed_data['text'])
                                    print("i eat")
                                audio_buffer.clear()
                            finally:
                                is_processing = False

    except Exception as e:
        print(f"Error: {e}")

   




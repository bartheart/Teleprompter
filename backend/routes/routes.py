from fastapi import APIRouter
import socketio
from typing import Any
import subprocess
from services import transcribe
import os


# initialize the app router 
router = APIRouter()

# create the socket instance with ASGI support 
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)


# create ASGI app 
socket_app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=router
)


# define the home route 
@router.get('/')
async def Home():
    return "Home route"


# socket io event handlers 
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('connect_response', {'status': 'connected'}, room=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")










# define a mime type var for the audio blobs 
mime_type = ''

# to get the mime/ audio format from the browser
@sio.event 
async def mime_type(sid, type: str):
    print(f"Server recieved the mime type of {type}")
    mime_type = type


# define a audio buffer for the blob data 
audio_buffer = []

# define a fcuntion to compile the audio blobs
def compile_buffer (mime_type: str, audio_buffer: list):
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
    try: 
        subprocess.run(
            ["ffmpeg", "-i", input_file, output_file],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"WAV file saved: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg conversion failed: {e.stderr.decode()}")
    
    return output_file
    

# handle the event of sending audio packets 
@sio.event
async def audio_data(sid, data: bytes):
    print(f"Recieved an audio from client: {len(data)} bytes")

    # append the audio blobs into the buffer 
    audio_buffer.append(data) 

    # compile the audio in the buffer if sixe is morethan 10 
    if len(audio_buffer) > 5:
        audio_wav = compile_buffer(mime_type, audio_buffer)

        # transcribe the data recieved from the client
        transcribed_data = transcribe(audio_wav)

        print(transcribed_data['text'])

    # send a dictionary response to the client that contains the status and message 
    await sio.emit('audio recieved', {'status': 'sucess', 'message': 'Audio data recieved'}, room=sid)

# compile the blobs in the buffer
compiled_audio = b"".join(audio_buffer)


from fastapi import APIRouter
import socketio
from typing import Any
import whisper
from io import BytesIO
import numpy as np 
from pydub import AudioSegment


# initialize the app router 
router = APIRouter()

# create the socket instance with ASGI support 
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# initialize the turbo model 
model = whisper.load_model("turbo")
if model:
    print("Whisper model is loaded")

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
mime_extension = ''

# to get the mime/ audio format from the browser
@sio.event 
async def mime_type(sid, type: str):
    global mime_extension

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
    extension_type = mime_to_extension.get(type, 'bin')

    #print(f"Server recieved the mime type of {extension_type}")
    mime_extension = extension_type


# define a audio buffer for the blob data 
audio_buffer = BytesIO()

# define the sample rate
SAMPLE_RATE = 16000
    
is_processing = False

# handle the event of sending audio packets 
@sio.event
async def audio_data(sid, data: bytes):
    global is_processing, audio_buffer
    #print(f"Recieved an audio from client: {len(data)} bytes")

    if is_processing:
        #print("Process in progress")
        return 

    # append the audio blobs into the buffer 
    audio_buffer.write(data) 

    # check if the buffer is full 
    if audio_buffer.tell() >= SAMPLE_RATE:
        is_processing = True 

        # convert to numpy array 
        audio_buffer.seek(0)
        audio_segment = AudioSegment.from_file(
            audio_buffer,
            codec="opus",  
            format=mime_extension, 
            parameters=["-ar", str(SAMPLE_RATE)]
        )

        # get numpy array 
        samples = np.array(audio_segment.get_array_of_samples(), dtype=np.float32) / 32768.0

        # transcribe from the nunmpy array
        transcription = model.transcribe(samples).get("text", "")
        print(transcription)

        # reset the buffer 
        audio_buffer = BytesIO()